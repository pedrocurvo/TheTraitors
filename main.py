import os
import random
import time

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

from utils import compute_traitors_game_metrics
from agent import Agent  # Import the Agent class
from llm_client import LLMClientFactory  # Import the LLM client factory

# TODO: Keep metrics and overall conversation
# TODO: For each agent, keep all information in a folder/file, because their toughts are not shared with others
# TODO: Include an introduction phase, like: Player 1. [PROFESSION] [ETHNICITY] [COUNTRY] [AGE] [CIVIL STATUS] [CHILDREN]
# TODO: Decide on which models to run + number of times + temperature + top_p
# TODO: Write Paper
# TODO: README.md + Documentation
# TODO: MULTIAGENTS (?)
# TODO: Game through a config file


class TraitorsGame:
    def __init__(
        self,
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
            agent_count: Number of total agents in the game
            traitor_count: Number of traitors among the agents
            model: Model name to use (depends on client_type)
            seed: Random seed for reproducibility
            client_type: Type of client to use ("openai", "hf")
            provider: Provider for HF client (e.g., "together" for Together AI)
        """
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

        # Now append a dir with run-number of run based on the number of directories in the model folder
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

        # Store model and client configuration (for agent creation)
        self.model = model
        self.client_type = client_type
        self.provider = provider

        # Create agents with their own LLM clients
        self.agents = self.create_agents(agent_count, traitor_count)
        self.game_over = False
        self.history = []  # Stores past discussions
        self.round_number = 1
        self.traitors_last_eliminated = None

        # Create a .txt file to keep the game history
        self.HISTORY_FILE = f"{self.RESULTS_DIR}/history.txt"

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

        # Create all agents as Faithful initially
        agents = [
            Agent(i, "Faithful", self.model, self.RESULTS_DIR)
            for i in range(agent_count)
        ]

        # Assign traitor roles
        traitors = random.sample(agents, traitor_count)
        for agent in traitors:
            agent.role = "Traitor"

        # Give each traitor knowledge of other traitors
        for agent in agents:
            if agent.is_traitor():
                traitor_ids = [
                    t.id for t in agents if t.is_traitor() and t.id != agent.id
                ]
                agent.set_fellow_traitors(traitor_ids)

            # Create and assign an LLM client for each agent
            # Currently all agents use the same client type, but this could be customized
            agent_client = LLMClientFactory.create_client(
                self.client_type, agent.model, self.provider
            )
            agent.set_llm_client(agent_client)

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
            "Keep the taughts outside the triple dashes.\n\n"
            "Keep your response brief (50-100 words). Only the text between the triple dashes will be shown to other players."
            "Main Task: What would you say next in the group chat? "
            "Ensure the conversation flows naturally and avoids repetition.\n\n"
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

        # First round of comments - each agent shares suspicions
        for i, agent in enumerate(active_agents):
            game_status = self.get_game_status()
            agent.set_prompt(
                f"{game_status}\n\n"
                "You are in a room with other players to discuss who might be a traitor. "
                "Who do you suspect and why? Be strategic based on your role. "
                "Consider past eliminations and discussions."
            )

            if self.round_number == 1:
                agent.current_prompt += "\n\nThis is the first round of discussions, therefore you still don't have"
                "any information about players who haven't spoken yet."

            if new_discussions:
                agent.current_prompt += (
                    f"\n\nCurrent discussion: {' '.join(new_discussions)}"
                )

            response = self.call_llm(agent)
            message = f"Player {agent.id}: {response}"
            new_discussions.append(message)
            self.write_to_history(message)

        # Second round - reactions to other agents' comments
        reaction_discussions = []
        for agent in active_agents:
            agent.set_prompt(
                "After hearing everyone's suspicions, what is your response? "
                f"\n\nDiscussion so far: {' '.join(new_discussions)}"
            )

            response = self.call_llm(agent)
            message = f"Player {agent.id} responds: {response}"
            reaction_discussions.append(message)
            self.write_to_history(message)

        # Combine all discussions
        all_discussions = new_discussions + reaction_discussions

        # Update memory for each agent
        for agent in active_agents:
            agent.set_prompt(
                "Summarize the most important points from this discussion that you want to remember. "
                f"Focus on who you believe are traitors and why: {' '.join(all_discussions)}"
            )
            memory_response = self.call_llm(agent)
            agent.add_to_memory(memory_response, f"ROUND {self.round_number} MEMORY")

    def process_vote(self, agent, vote_type, active_players, votes_dict, votes_list):
        """Process a vote from an agent and update tracking structures."""
        agent.set_prompt(
            f"Based on all discussions and your memory:\n{agent.memory}\n\n"
            f"It's time to vote. The active players are: {', '.join(str(a.id) for a in active_players)}.\n"
            "Who are you voting to eliminate? Respond with ONLY the player number."
        )

        vote_response = self.call_llm(agent)

        # Extract just the number from the response
        import re

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
                "Be strategic based on your role."
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

        traitor_discussion = []
        for traitor in traitors:
            traitor.set_prompt(
                f"SECRET TRAITOR MEETING: You are with your fellow traitors: {', '.join(str(t.id) for t in traitors)}.\n"
                f"The Faithfuls still in the game are: {', '.join(str(a.id) for a in active_faithfuls)}.\n"
                "Who do you suggest eliminating next and why? Be strategic to avoid detection."
            )

            if traitor_discussion:
                traitor.current_prompt += (
                    f"\n\nTraitor discussion so far: {' '.join(traitor_discussion)}"
                )

            response = self.call_llm(traitor)
            message = f"Traitor {traitor.id}: {response}"
            traitor_discussion.append(message)
            self.write_to_history(message)

        # Second round for traitors to reach consensus
        consensus_discussion = []
        for traitor in traitors:
            traitor.set_prompt(
                "Based on the traitor discussion, who do you now think we should eliminate? "
                f"Discussion: {' '.join(traitor_discussion)}"
            )

            response = self.call_llm(traitor)
            message = f"Traitor {traitor.id} concludes: {response}"
            consensus_discussion.append(message)
            self.write_to_history(message)

        # Update traitor memories
        traitor_memory = " ".join(traitor_discussion + consensus_discussion)
        for traitor in traitors:
            traitor.add_to_memory(
                traitor_memory, f"SECRET TRAITOR MEETING (ROUND {self.round_number})"
            )

        self.traitor_elimination_phase(traitors, active_faithfuls)

    def traitor_elimination_phase(self, traitors, active_faithfuls):
        """Traitors vote to eliminate a Faithful."""
        self.write_to_history("TRAITOR ELIMINATION PHASE", new_section=True)

        if not traitors or not active_faithfuls:
            return

        votes = {}
        votes_list = []

        for traitor in traitors:
            self.process_vote(traitor, "Traitor", active_faithfuls, votes, votes_list)

        if not votes:
            self.write_to_history("No valid traitor votes were cast!")
            return

        # Find the agent with the most votes
        eliminated_id = max(votes, key=votes.get)
        eliminated_agent = next(
            (a for a in active_faithfuls if str(a.id) == eliminated_id), None
        )

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
            f"Using client: {self.client_type}"
            + (f" with provider: {self.provider}" if self.provider else "")
        )
        self.write_to_history(f"Model: {self.model}")

        try:
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


# Example usage
if __name__ == "__main__":
    # Use command line arguments to configure the game
    import argparse

    parser = argparse.ArgumentParser(
        description="Run a Traitors Game simulation with AI agents"
    )
    parser.add_argument(
        "--agents", type=int, default=10, help="Number of agents in the game"
    )
    parser.add_argument(
        "--traitors", type=int, default=3, help="Number of traitor agents"
    )
    parser.add_argument(
        "--model", type=str, default="deepseek-chat", help="Model name to use"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--client",
        type=str,
        choices=["openai", "hf", "mlx"],
        default="openai",
        help="Client type (openai or hf for Hugging Face)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="deepseek",
        choices=["deepseek", "openai", "together"],
        help="Provider for HF client (e.g., 'together' for Together AI)",
    )
    parser.add_argument(
        "--experiment_name",
        type=str,
        default=None,
        help="Name of the experiment to create a subfolder in results",
    )

    args = parser.parse_args()

    # Create and run the game with the specified parameters
    game = TraitorsGame(
        agent_count=args.agents,
        traitor_count=args.traitors,
        model=args.model,
        seed=args.seed,
        client_type=args.client,
        provider=args.provider,
        experiment_name=args.experiment_name,
    )
    game.run()
    game.post_game_analysis()
