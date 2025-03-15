import os
import random
import time
import sys
import yaml
import re
from pathlib import Path

from utils import compute_traitors_game_metrics
from agent import Agent  # Import the Agent class
from llm_client import LLMClientFactory  # Import the LLM client factory


class TraitorsGame:
    def __init__(
        self,
        config,
        agent_count=10,
        traitor_count=3,
        model="deepseek-chat",
        seed=None,
        client_type="openai",
        provider=None,
        experiment_name=None,
    ):
        """
        Initialize the Traitors Game.

        Args:
            config: Configuration dictionary
            agent_count: Default number of total agents in the game
            traitor_count: Default number of traitors among the agents
            model: Default model name to use
            seed: Random seed for reproducibility
            client_type: Default type of client to use ("openai", "hf")
            provider: Default provider for HF client
            experiment_name: Optional name for the experiment
        """
        # Store the configuration
        self.config = config

        # Create the results folder
        Path("results").mkdir(parents=True, exist_ok=True)
        self.RESULTS_DIR = "results"

        if experiment_name:
            Path(f"results/{experiment_name}/{model}").mkdir(
                parents=True, exist_ok=True
            )
            self.RESULTS_DIR = Path(f"results/{experiment_name}/{model}")
        else:
            Path(f"results/{model}").mkdir(parents=True, exist_ok=True)
            self.RESULTS_DIR = Path(f"results/{model}")

        # Now append a dir with run-number based on the number of directories in the model folder
        run_number = (
            sum(
                [
                    1
                    for name in os.listdir(self.RESULTS_DIR)
                    if os.path.isdir(os.path.join(self.RESULTS_DIR, name))
                ]
            )
            + 1
        )
        # Create a new directory for the run
        Path(f"{self.RESULTS_DIR}/run-{run_number}").mkdir(parents=True, exist_ok=True)
        self.RESULTS_DIR = Path(f"{self.RESULTS_DIR}/run-{run_number}")
        print(f"Results will be saved in: {self.RESULTS_DIR}")

        # Set random seed if provided
        self.seed = seed
        if seed is not None:
            random.seed(seed)
            print(f"Game initialized with seed: {seed}")

        # Create a .txt file to keep the game history
        self.HISTORY_FILE = f"{self.RESULTS_DIR}/history.txt"
        # Create agents with their own LLM clients
        self.agents = self.create_agents(agent_count, traitor_count)
        self.game_over = False
        self.history = []  # Stores past discussions
        self.round_number = 1
        self.traitors_last_eliminated = None

        # Write configuration files
        self.write_config_file(
            agent_count, traitor_count, model, seed, client_type, provider
        )

        # Write a .csv file to keep votes and eliminations
        self.VOTING_FILE = f"{self.RESULTS_DIR}/votes.csv"
        with open(self.VOTING_FILE, "w") as f:
            f.write("Round,Vote_Type,Player_ID,Role,Vote_Target,Eliminated\n")

    def write_config_file(
        self, agent_count, traitor_count, model, seed, client_type, provider
    ):
        """Write game configuration to a YAML file.

        Args:
            agent_count (int): Number of agents in the game
            traitor_count (int): Number of traitors among the agents
            model (str): Model name used for LLM calls
            seed (int): Random seed for reproducibility
            client_type (str): Type of client used (openai, hf, mlx)
            provider (str): Provider for the client
        """
        config_file = f"{self.RESULTS_DIR}/config.yaml"
        with open(config_file, "w") as f:
            f.write(f"agent_count: {agent_count}\n")
            f.write(f"traitor_count: {traitor_count}\n")
            f.write(f"model: {model}\n")
            f.write(f"seed: {seed}\n")
            f.write(f"client_type: {client_type}\n")
            f.write(f"provider: {provider}\n")

            # Write agent roles
            f.write("\n# Agent roles\n")
            for agent in self.agents:
                f.write(f"agent_{agent.id}: {agent.role}\n")

            f.write("\n")

        self.write_to_history(f"Configuration written to {config_file}")

    def create_agents(self, agent_count, traitor_count):
        """Initialize agents with unique roles."""
        if traitor_count >= agent_count:
            raise ValueError("Traitor count must be less than agent count")

        agents = []
        enforced_traitors = 0
        enforced_faithfuls = 0
        flexible_agents = []

        # Phase 1: Create agents with specific configurations from config file
        specific_configs = []
        if 'agent_configs' in self.config:
            # Get all specific agent configurations
            specific_configs = self.config['agent_configs']
            # Shuffle the configurations to randomize assignment
            random.shuffle(specific_configs)

        # Create all agents
        for i in range(agent_count):
            # Determine if this agent gets a specific configuration
            agent_config = specific_configs[i] if i < len(specific_configs) else self.config['llm']
            
            # Get traits if they exist in the configuration
            traits = agent_config.get('traits', None)
            
            agent = Agent(
                i,
                "Faithful",  # Default role, may be changed later
                agent_config.get('model', self.config['llm']['model']),
                self.RESULTS_DIR,
                traits=traits  # Pass traits to the Agent constructor
            )

            # Handle role enforcement if specified
            if 'enforce_role' in agent_config:
                if agent_config['enforce_role'] == "Traitor":
                    agent.role = "Traitor"
                    enforced_traitors += 1
                elif agent_config['enforce_role'] == "Faithful":
                    agent.role = "Faithful"
                    enforced_faithfuls += 1
                else:
                    raise ValueError(f"Invalid enforced role: {agent_config['enforce_role']}")
            else:
                flexible_agents.append(agent)

            # Create and assign LLM client
            agent_client = LLMClientFactory.create_client(
                agent_config.get('client_type', self.config['llm']['client_type']),
                agent_config.get('model', self.config['llm']['model']),
                agent_config.get('provider', self.config['llm'].get('provider'))
            )
            agent.set_llm_client(agent_client)
            agents.append(agent)

        # Validate role counts
        remaining_traitors = traitor_count - enforced_traitors
        if remaining_traitors < 0:
            raise ValueError("More enforced traitors than total traitor count")
        if len(flexible_agents) < remaining_traitors:
            raise ValueError("Not enough flexible agents to assign remaining traitor roles")
        if enforced_faithfuls > agent_count - traitor_count:
            raise ValueError("More enforced faithfuls than total faithful count")

        # Assign remaining traitor roles to flexible agents
        new_traitors = random.sample(flexible_agents, remaining_traitors)
        for agent in new_traitors:
            agent.role = "Traitor"

        # Give each traitor knowledge of other traitors
        for agent in agents:
            if agent.is_traitor():
                traitor_ids = [
                    t.id for t in agents if t.is_traitor() and t.id != agent.id
                ]
                agent.set_fellow_traitors(traitor_ids)

        # Log the final agent-model assignments and roles
        self.write_to_history("\nAgent-Model Assignments:", new_section=True)
        for agent in agents:
            # Find the configuration that was used for this agent
            if i < len(specific_configs):
                config = specific_configs[i]
                role_info = "(Enforced)" if 'enforce_role' in config else "(Random)"
            else:
                config = self.config['llm']
                role_info = "(Random)"
            
            self.write_to_history(
                f"Agent {agent.id} - {agent.role} {role_info}: "
                f"Model={config.get('model', self.config['llm']['model'])}, "
                f"Provider={config.get('provider', self.config['llm'].get('provider'))}"
            )

        return agents

    def call_llm(self, agent):
        """Call the LLM API to generate agent responses."""
        # Add formatting instructions with delimiters
        formatted_prompt = (
            f"{agent.current_prompt}\n\n"
            "Important: First, decide what your character would say in this situation. "
            "Then provide ONLY your character's actual dialogue between triple dashes like this:\n"
            "---\n"
            "Your in-game dialogue here\n"
            "---\n"
            "Keep the thoughts outside the triple dashes.\n\n"
            "Keep your response brief (50-100 words). Only the text between the triple dashes will be shown to other players."
            "Main Task: What would you say next in the group chat? "
            "Ensure the conversation flows naturally and AVOIDS REPETITION.\n\n"
        )

        try:
            # Use the agent's own LLM client to generate a response
            return agent.call_llm(formatted_prompt)
        except Exception as e:
            print(f"Error calling the LLM API: {e}")
            with open(self.HISTORY_FILE, "a") as f:
                print(f"Error calling the LLM API: {e}", file=f)
            return f"Agent {agent.id} couldn't respond due to an error."

    def get_game_status(self):
        """Return the current game status for prompts."""
        active_agents = [a for a in self.agents if not a.is_eliminated()]
        eliminated_agents = [a for a in self.agents if a.is_eliminated()]

        status = f"Round {self.round_number}: "
        status += f"Active players: {', '.join(str(a.id) for a in active_agents)}. "

        if eliminated_agents:
            status += f"Eliminated players: {', '.join(str(a.id) for a in eliminated_agents)}. "

        status += f"Game history: {' '.join(self.history)}"
        return status

    def write_to_history(self, message, new_section=False):
        """Write a message to the history file with optional section formatting."""
        if new_section:
            message = f"\n--- {message} ---"

        print(message)
        with open(self.HISTORY_FILE, "a") as f:
            print(message, file=f)

    def discussion_phase(self):
        """Agents communicate and discuss who to vote out."""
        self.write_to_history(
            f"DISCUSSION PHASE (ROUND {self.round_number})", new_section=True
        )
        new_discussions = []

        # Add info about last elimination by traitors if any
        if self.traitors_last_eliminated:
            new_discussions.append(self.traitors_last_eliminated)

        active_agents = [a for a in self.agents if not a.is_eliminated()]
        eliminated_agents = [a for a in self.agents if a.is_eliminated()]
        
        # Create round-specific discussion topics
        round_topics = [
            "Who do you suspect might be a Traitor and why?",
            "What patterns of behavior have you noticed that seem suspicious?",
            "Which player's arguments or defenses seem inconsistent or weak?",
            "Who do you trust the most and why?",
            "What strategy do you think the Traitors are using in this game?",
            "Who has been flying under the radar and not contributing much to discussions?"
        ]
        
        # Select topic based on round number (cycling through topics)
        topic_index = (self.round_number - 1) % len(round_topics)
        current_topic = round_topics[topic_index]
        
        # Add context about eliminated players if any
        elimination_context = ""
        if eliminated_agents:
            last_eliminated = [a for a in eliminated_agents if a.id == max(e.id for e in eliminated_agents)]
            if last_eliminated:
                elimination_context = f"Player {last_eliminated[0].id} was just eliminated. "
                if self.round_number > 1:
                    elimination_context += "How does this change your assessment of who the Traitors might be? "

        # First round of comments - each agent shares thoughts on the current topic
        for i, agent in enumerate(active_agents):
            game_status = self.get_game_status()
            
            # Create a personalized prompt based on the agent's role and the round
            if agent.is_traitor():
                strategy_hint = "Remember to blend in while subtly casting suspicion on Faithfuls."
            else:
                strategy_hint = "Try to identify inconsistencies in others' statements that might reveal Traitors."
            
            # Vary the prompt based on round number
            if self.round_number == 1:
                prompt = (
                    f"{game_status}\n\n"
                    "This is the first round of discussions. Share your initial thoughts and observations. "
                    f"{current_topic} {strategy_hint}"
                )
            else:
                prompt = (
                    f"{game_status}\n\n"
                    f"Round {self.round_number} of discussions. {elimination_context}"
                    f"{current_topic} Consider what you've learned from previous rounds. {strategy_hint}"
                )
            
            agent.set_prompt(prompt)

            if i == 0 and self.round_number == 1:
                agent.current_prompt += "\n\nYou are the first to speak in this game. Set the tone for the discussion."
            
            if new_discussions:
                agent.current_prompt += (
                    f"\n\nCurrent discussion: {' '.join(new_discussions)}"
                )

            response = self.call_llm(agent)
            message = f"Player {agent.id}: {response}"
            new_discussions.append(message)
            self.write_to_history(message)

        # Second round - reactions to other agents' comments with varied prompts
        reaction_discussions = []
        for i, agent in enumerate(active_agents):
            # Vary the reaction prompts to avoid repetition
            reaction_prompts = [
                "Now that you've heard everyone's thoughts, what's your response?",
                "Do you agree or disagree with any particular accusations? Explain why.",
                "Has anyone said something that changed your perspective?",
                "Would you like to defend yourself or challenge someone else's statement?",
                "What important points do you think are being overlooked in this discussion?"
            ]
            
            # Select a reaction prompt based on agent ID and round number to ensure variety
            reaction_index = (i + self.round_number) % len(reaction_prompts)
            reaction_prompt = reaction_prompts[reaction_index]
            
            agent.set_prompt(
                f"{reaction_prompt} "
                f"\n\nDiscussion so far: {' '.join(new_discussions)}"
            )

            response = self.call_llm(agent)
            message = f"Player {agent.id} responds: {response}"
            reaction_discussions.append(message)
            self.write_to_history(message)

        # Combine all discussions
        all_discussions = new_discussions + reaction_discussions

        # Update memory for each agent with varied memory prompts
        for agent in active_agents:
            memory_prompts = [
                "Summarize the key points from this discussion that you want to remember.",
                "What were the most revealing statements in this discussion?",
                "Update your assessment of who might be Traitors based on this discussion.",
                "What important clues or patterns emerged in this round?"
            ]
            
            # Select memory prompt based on agent ID and round
            memory_index = (agent.id + self.round_number) % len(memory_prompts)
            memory_prompt = memory_prompts[memory_index]
            
            agent.set_prompt(
                f"{memory_prompt} "
                f"Focus on information that will help your strategy: {' '.join(all_discussions)}"
            )
            memory_response = self.call_llm(agent)
            agent.add_to_memory(memory_response, f"ROUND {self.round_number} MEMORY")

    def process_vote(self, agent, vote_type, active_players, votes_dict, votes_list):
        """Process a vote from an agent and update tracking structures."""
        # Create more strategic voting prompts based on the agent's role and game state
        active_player_ids = [str(a.id) for a in active_players]
        
        # Create different voting prompts based on the agent's role
        if agent.is_traitor():
            # For traitors, emphasize strategic voting
            strategic_hint = (
                "As a Traitor, your vote is crucial. Consider voting strategically to eliminate Faithfuls "
                "or to deflect suspicion from yourself or fellow Traitors."
            )
            
            # Add info about fellow traitors for strategic coordination
            fellow_traitors_ids = [str(id) for id in agent.fellow_traitors]
            active_fellow_traitors = [id for id in fellow_traitors_ids if id in active_player_ids]
            if active_fellow_traitors:
                strategic_hint += f" Remember that your fellow Traitors (Players {', '.join(active_fellow_traitors)}) are still active."
        else:
            # For faithfuls, emphasize deduction
            strategic_hint = (
                "As a Faithful, your goal is to identify and eliminate Traitors. "
                "Review the discussions carefully and vote based on your suspicions."
            )
        
        # Add round-specific context
        if self.round_number == 1:
            round_context = "This is the first elimination. You have limited information to go on, but must make a choice."
        elif self.round_number < 3:
            round_context = "The game is still in early stages. Consider both current discussions and past eliminations."
        else:
            round_context = "The game is progressing. Patterns may be emerging that could reveal who the Traitors are."
        
        # Create the final voting prompt
        agent.set_prompt(
            f"Based on all discussions and your memory:\n{agent.memory}\n\n"
            f"It's time to vote for elimination. Round {self.round_number}.\n"
            f"{round_context}\n"
            f"{strategic_hint}\n\n"
            f"The active players are: {', '.join(active_player_ids)}.\n"
            "Who are you voting to eliminate? Respond with ONLY the player number."
        )

        vote_response = self.call_llm(agent)

        # Extract just the number from the response
        vote_match = re.search(r"\d+", vote_response)

        if vote_match:
            vote = vote_match.group()
            votes_dict[vote] = votes_dict.get(vote, 0) + 1
            self.write_to_history(f"Player {agent.id} votes for Player {vote}")

            # Add the vote to the list
            votes_list.append(
                {
                    "Round": self.round_number,
                    "Vote_Type": vote_type,
                    "Player_ID": agent.id,
                    "Role": agent.role,
                    "Vote_Target": vote,
                    "Eliminated": False,
                }
            )
            return vote
        else:
            self.write_to_history(
                f"Player {agent.id} cast an invalid vote: {vote_response}"
            )

            # Add the invalid vote to the list
            votes_list.append(
                {
                    "Round": self.round_number,
                    "Vote_Type": vote_type,
                    "Player_ID": agent.id,
                    "Role": agent.role,
                    "Vote_Target": None,
                    "Eliminated": False,
                }
            )
            return None

    def process_elimination(
        self, eliminated_id, eliminated_agent, votes_list, elimination_type="vote"
    ):
        """Process the elimination of an agent."""
        if not eliminated_agent:
            return False

        eliminated_agent.eliminate()

        if elimination_type == "vote":
            elimination_message = f"Player {eliminated_id} was eliminated. Player {eliminated_id} was a {eliminated_agent.role}."
        else:  # traitor elimination
            elimination_message = (
                f"Player {eliminated_id} was eliminated by the traitors in the night."
            )
            self.traitors_last_eliminated = f"Moderator: Player {eliminated_id} was eliminated last night by the traitors."

        self.write_to_history(elimination_message)
        self.history.append(elimination_message)

        # Update all active agents' memory
        for agent in self.agents:
            if not agent.is_eliminated():
                agent.add_to_memory(elimination_message)

        # Update votes_list with the eliminated player
        for vote in votes_list:
            vote["Eliminated"] = eliminated_id

        # Write the votes to the .csv file
        with open(self.VOTING_FILE, "a") as f:
            for vote in votes_list:
                f.write(
                    f"{vote['Round']},{vote['Vote_Type']},{vote['Player_ID']},{vote['Role']},{vote['Vote_Target']},{vote['Eliminated']}\n"
                )

        return True

    def voting_phase(self):
        """Agents vote to eliminate a player."""
        self.write_to_history(
            f"VOTING PHASE (ROUND {self.round_number})", new_section=True
        )
        votes = {}
        active_agents = [a for a in self.agents if not a.is_eliminated()]
        votes_list = []

        for agent in active_agents:
            self.process_vote(agent, "General", active_agents, votes, votes_list)

        if not votes:
            self.write_to_history("No valid votes were cast!")
            return

        # Find the agent with the most votes
        eliminated_id = max(votes, key=votes.get)
        eliminated_agent = next(
            (a for a in self.agents if str(a.id) == eliminated_id), None
        )

        if self.process_elimination(eliminated_id, eliminated_agent, votes_list):
            self.post_elimination_discussion(eliminated_id)

    def post_elimination_discussion(self, eliminated):
        """Allow agents to discuss after elimination is revealed."""
        self.write_to_history("POST-ELIMINATION DISCUSSION", new_section=True)
        eliminated_agent = next(
            (a for a in self.agents if str(a.id) == eliminated), None
        )

        if not eliminated_agent:
            return

        discussion_prompts = []
        active_agents = [a for a in self.agents if not a.is_eliminated()]

        for agent in active_agents:
            agent.set_prompt(
                f"Player {eliminated} was eliminated and was a {eliminated_agent.role}. "
                "What are your thoughts on this elimination? Has this changed your suspicions? "
                "Be strategic based on your role. "
                "Consider past eliminations and discussions."
            )

            if discussion_prompts:
                agent.current_prompt += (
                    f"\n\nOngoing discussion: {' '.join(discussion_prompts)}"
                )

            response = self.call_llm(agent)
            message = f"Player {agent.id}: {response}"
            discussion_prompts.append(message)
            self.write_to_history(message)

        # Update memory for each agent
        for agent in active_agents:
            agent.set_prompt(
                f"Summarize key insights from this post-elimination discussion: {' '.join(discussion_prompts)}"
            )
            memory_response = self.call_llm(agent)
            agent.add_to_memory(memory_response, "POST-ELIMINATION INSIGHTS")

    def traitor_discussion_phase(self):
        """Traitors secretly discuss who to eliminate."""
        self.write_to_history("TRAITOR DISCUSSION PHASE", new_section=True)
        traitors = [
            agent
            for agent in self.agents
            if agent.is_traitor() and not agent.is_eliminated()
        ]

        if not traitors:
            return

        active_faithfuls = [
            a for a in self.agents if a.is_faithful() and not a.is_eliminated()
        ]

        # Create more strategic and varied prompts for traitor discussions
        traitor_discussion = []
        
        # Create round-specific strategic questions for traitors
        strategic_questions = [
            "Who is the most dangerous Faithful that could expose us?",
            "Which Faithful seems most trusted by others?",
            "Who would be least suspicious for us to eliminate?",
            "Is there a Faithful who's close to figuring out our identities?",
            "Should we eliminate someone who's been quiet, or someone vocal?"
        ]
        
        # Select a strategic question based on the round
        question_index = (self.round_number - 1) % len(strategic_questions)
        strategic_question = strategic_questions[question_index]
        
        # Add game state analysis for traitors
        game_state = ""
        if self.round_number > 1:
            traitor_count = len(traitors)
            faithful_count = len(active_faithfuls)
            game_state = (
                f"Current game state: {traitor_count} Traitors vs {faithful_count} Faithfuls. "
                f"You need {faithful_count - traitor_count} more eliminations to win. "
            )
        
        for i, traitor in enumerate(traitors):
            # Create a personalized prompt for each traitor
            if i == 0:
                # First traitor sets the tone
                traitor.set_prompt(
                    f"SECRET TRAITOR MEETING: You are with your fellow traitors: {', '.join(str(t.id) for t in traitors)}.\n"
                    f"{game_state}"
                    f"The Faithfuls still in the game are: {', '.join(str(a.id) for a in active_faithfuls)}.\n\n"
                    f"As the first to speak in this secret meeting, assess the current situation. {strategic_question} "
                    "Suggest a target and explain your reasoning strategically."
                )
            else:
                # Other traitors respond to the ongoing discussion
                traitor.set_prompt(
                    f"SECRET TRAITOR MEETING: You are with your fellow traitors: {', '.join(str(t.id) for t in traitors)}.\n"
                    f"{game_state}"
                    f"The Faithfuls still in the game are: {', '.join(str(a.id) for a in active_faithfuls)}.\n\n"
                    f"Consider what your fellow traitors have said. Do you agree with their target selection? {strategic_question} "
                    "Share your thoughts on who to eliminate and why."
                )

            if traitor_discussion:
                traitor.current_prompt += (
                    f"\n\nTraitor discussion so far: {' '.join(traitor_discussion)}"
                )

            response = self.call_llm(traitor)
            message = f"Traitor {traitor.id}: {response}"
            traitor_discussion.append(message)
            self.write_to_history(message)

        # Second round for traitors to reach consensus with more strategic depth
        consensus_discussion = []
        
        # Create consensus-building prompts that vary by round
        if self.round_number == 1:
            consensus_prompt = (
                "This is our first elimination. Based on our discussion, who should we target? "
                "Consider both immediate benefit and long-term strategy."
            )
        elif self.round_number < 3:
            consensus_prompt = (
                "The game is still developing. Which elimination would best position us for the mid-game? "
                "Consider both eliminating threats and maintaining our cover."
            )
        else:
            consensus_prompt = (
                "We're getting closer to our goal. Which strategic elimination would bring us closest to victory? "
                "Consider both the numbers and which Faithfuls pose the greatest threat to our identities."
            )
        
        for traitor in traitors:
            traitor.set_prompt(
                f"{consensus_prompt} "
                f"Discussion: {' '.join(traitor_discussion)}"
            )

            response = self.call_llm(traitor)
            message = f"Traitor {traitor.id} concludes: {response}"
            consensus_discussion.append(message)
            self.write_to_history(message)

        # Update traitor memories with more strategic framing
        traitor_memory = " ".join(traitor_discussion + consensus_discussion)
        for traitor in traitors:
            traitor.add_to_memory(
                f"SECRET TRAITOR MEETING SUMMARY (ROUND {self.round_number}):\n{traitor_memory}\n\n"
                f"STRATEGIC NOTES: Remember who we discussed eliminating and why. "
                f"In public discussions, be careful not to reveal information only Traitors would know.",
                f"SECRET TRAITOR MEETING (ROUND {self.round_number})"
            )

        self.traitor_elimination_phase(traitors, active_faithfuls)

    def traitor_elimination_phase(self, traitors, active_faithfuls):
        """Traitors vote to eliminate a Faithful."""
        self.write_to_history("TRAITOR ELIMINATION PHASE", new_section=True)

        if not traitors or not active_faithfuls:
            return

        # Add strategic context for the elimination
        if self.round_number == 1:
            elimination_context = "This is your first night elimination. Choose wisely to set up your long-term strategy."
        elif self.round_number < 3:
            elimination_context = "The game is developing. Consider eliminating someone who poses a threat to your secrecy."
        else:
            elimination_context = "The end game approaches. Each elimination brings you closer to victory."
            
        # Get the consensus from the previous discussion
        consensus_targets = []
        for traitor in traitors:
            # Extract the most recent traitor meeting memory
            traitor_memories = [m for m in traitor.memory.split("\n--- SECRET TRAITOR MEETING") if "ROUND" in m]
            if traitor_memories:
                most_recent = traitor_memories[-1]
                consensus_targets.append(most_recent)
        
        consensus_summary = ""
        if consensus_targets:
            consensus_summary = "Based on your secret meeting, you discussed potential targets. "
            consensus_summary += "Now you must make the final decision on who to eliminate."

        votes = {}
        votes_list = []
        
        # Create a more strategic prompt for the final vote
        for traitor in traitors:
            # Create a personalized prompt for each traitor's vote
            traitor_prompt = (
                f"{elimination_context}\n\n"
                f"{consensus_summary}\n\n"
                "This is the moment to act. Your vote will determine which Faithful is eliminated tonight. "
                "Choose strategically to advance the Traitors' position in the game."
            )
            
            # Override the standard process_vote with our custom prompt
            traitor.set_prompt(
                f"Based on all discussions and your memory:\n{traitor.memory}\n\n"
                f"{traitor_prompt}\n\n"
                f"The active Faithfuls are: {', '.join(str(a.id) for a in active_faithfuls)}.\n"
                "Who are you voting to eliminate? Respond with ONLY the player number."
            )
            
            vote_response = self.call_llm(traitor)
            
            # Extract just the number from the response
            vote_match = re.search(r"\d+", vote_response)
            
            if vote_match:
                vote = vote_match.group()
                votes[vote] = votes.get(vote, 0) + 1
                self.write_to_history(f"Traitor {traitor.id} votes to eliminate Player {vote}")
                
                # Add the vote to the list
                votes_list.append(
                    {
                        "Round": self.round_number,
                        "Vote_Type": "Traitor",
                        "Player_ID": traitor.id,
                        "Role": traitor.role,
                        "Vote_Target": vote,
                        "Eliminated": False,
                    }
                )
            else:
                self.write_to_history(
                    f"Traitor {traitor.id} cast an invalid vote: {vote_response}"
                )
                
                # Add the invalid vote to the list
                votes_list.append(
                    {
                        "Round": self.round_number,
                        "Vote_Type": "Traitor",
                        "Player_ID": traitor.id,
                        "Role": traitor.role,
                        "Vote_Target": None,
                        "Eliminated": False,
                    }
                )

        if not votes:
            self.write_to_history("No valid traitor votes were cast!")
            return

        # Find the agent with the most votes
        eliminated_id = max(votes, key=votes.get)
        eliminated_agent = next(
            (a for a in active_faithfuls if str(a.id) == eliminated_id), None
        )
        
        # Add a strategic reflection for traitors after the elimination
        if eliminated_agent:
            for traitor in traitors:
                strategic_note = (
                    f"You have eliminated Player {eliminated_id} in the night. "
                    "Remember to act surprised when this is announced to all players. "
                    "Consider how you might use this elimination to your advantage in discussions."
                )
                traitor.add_to_memory(strategic_note, f"TRAITOR ELIMINATION (ROUND {self.round_number})")

        self.process_elimination(eliminated_id, eliminated_agent, votes_list, "traitor")

    def check_win_conditions(self):
        """Determine if the game has ended."""
        faithfuls = sum(
            1 for a in self.agents if a.is_faithful() and not a.is_eliminated()
        )
        traitors = sum(
            1 for a in self.agents if a.is_traitor() and not a.is_eliminated()
        )

        self.write_to_history(
            f"GAME STATUS: {faithfuls} Faithfuls, {traitors} Traitors", new_section=True
        )

        if traitors == 0:
            self.write_to_history(
                "🎉 FAITHFULS WIN! All traitors have been eliminated."
            )
            self.game_over = True
            return "Faithfuls"
        elif traitors >= faithfuls:
            self.write_to_history(
                "💀 TRAITORS WIN! They now equal or outnumber the Faithfuls."
            )
            self.game_over = True
            return "Traitors"
        return None

    def introduction_phase(self):
        """Introduce agents with their traits to the game."""
        self.write_to_history("INTRODUCTION PHASE", new_section=True)
        self.write_to_history("Let's meet our players!")

        # Build complete introduction text
        introductions = []
        for agent in self.agents:
            if agent.traits:
                # Determine how to refer to the agent
                gender_pronoun = agent.traits.get('gender_pronoun', '').lower()
                if gender_pronoun in ['he', 'she']:
                    subject = gender_pronoun.capitalize()
                    possessive = "his" if gender_pronoun == "he" else "her"
                else:
                    subject = f"Player {agent.id}"
                    possessive = "their"

                # Build the introduction
                intro = f"Player {agent.id} is a {agent.traits.get('age')}-year-old "
                intro += f"{agent.traits.get('nationality')} {agent.traits.get('profession')}. "
                intro += f"{subject} is {agent.traits.get('ethnicity')} and {agent.traits.get('civil_status')}. "
                
                children = agent.traits.get('children', 0)
                if children == 0:
                    intro += f"{subject} has no children."
                elif children == 1:
                    intro += f"{subject} has one child."
                else:
                    intro += f"{subject} has {children} children."
                    
                self.write_to_history(intro)
                introductions.append(intro)

        # If there are no introductions, write a message to the history and return
        if not introductions:
            self.write_to_history("No introductions were provided. Skipping introduction phase.")
            return
        
        # Add a note about players without introductions
        players_without_traits = [str(a.id) for a in self.agents if not a.traits]
        if players_without_traits:
            no_info_msg = f"I do not have background information about Player(s): {', '.join(players_without_traits)}."
            self.write_to_history("\n" + no_info_msg)
            introductions.append(no_info_msg)

        # Have each agent process and remember the introductions
        all_introductions = "\n".join(introductions)
        for agent in self.agents:
            agent.set_prompt(
                f"These are the introductions of all players:\n{all_introductions}\n\n"
                "As your character, what do you find most interesting or noteworthy about the other players? "
                "What information might be useful to remember? "
                "Consider their professions, backgrounds, and any potential connections or suspicions."
            )
            memory_response = self.call_llm(agent)
            agent.add_to_memory(
                f"MY THOUGHTS ON PLAYERS BACKGROUNDS:\n{memory_response}",
            )
        
        # Add a small break before starting the game
        self.write_to_history("\nNow that we know each other, let the game begin!", new_section=True)

    def run(self):
        """Main game loop."""
        # Start a timer
        start_time = time.time()
        self.write_to_history("THE TRAITORS GAME", new_section=True)
        self.write_to_history(
            f"Starting with {len(self.agents)} players, including {sum(1 for a in self.agents if a.is_traitor())} traitors"
        )

        if self.seed is not None:
            self.write_to_history(f"Game seed: {self.seed}")

        self.write_to_history(
            f"Using client: {self.config['llm']['client_type']}"
            + (f" with provider: {self.config['llm'].get('provider')}" if self.config['llm'].get('provider') else "")
        )
        self.write_to_history(f"Model: {self.config['llm']['model']}")

        try:
            # Add introduction phase before the main game loop
            self.introduction_phase()
            
            while not self.game_over:
                self.discussion_phase()
                self.voting_phase()
                self.traitor_discussion_phase()
                winner = self.check_win_conditions()

                if winner:
                    break

                self.round_number += 1

            # End timer
            end_time = time.time()

            # Game summary
            self.write_to_history("GAME SUMMARY", new_section=True)
            self.write_to_history(
                f"The game simulation took {end_time - start_time:.2f} seconds"
            )
            self.write_to_history(f"The game lasted {self.round_number} rounds")
            self.write_to_history(
                "Traitors were: "
                + ", ".join(f"Player {a.id}" for a in self.agents if a.is_traitor())
            )
            self.write_to_history(
                "Eliminated agents: "
                + ", ".join(
                    f"Player {a.id} ({a.role})"
                    for a in self.agents
                    if a.is_eliminated()
                )
            )
            self.write_to_history(
                "Survivors: "
                + ", ".join(
                    f"Player {a.id} ({a.role})"
                    for a in self.agents
                    if not a.is_eliminated()
                )
            )

        except KeyboardInterrupt:
            self.write_to_history("Game interrupted by user.")
        except Exception as e:
            self.write_to_history(f"Game error: {e}")

    def post_game_analysis(self):
        """Compute game metrics and write to a file."""
        metrics = compute_traitors_game_metrics(csv_file=self.VOTING_FILE)
        with open(f"{self.RESULTS_DIR}/metrics.txt", "w") as f:
            for key, value in metrics.items():
                f.write(f"{key}: {value}\n")
