import os
import random
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
from pathlib import Path

from utils import compute_traitors_game_metrics

# TODO: Keep metrics and overall conversation
# TODO: For each agent, keep all information in a folder/file, because their toughts are not shared with others
# TODO: Include an introduction phase, like: Player 1. [PROFESSION] [ETHNICITY] [COUNTRY] [AGE] [CIVIL STATUS] [CHILDREN]
# TODO: Decide on which models to run + number of times + temperature + top_p
# TODO: Write Paper
# TODO: README.md + Documentation
# TODO: MULTIAGENTS (?)


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
        run_number = len(
            [
                name
                for name in os.listdir(self.RESULTS_DIR)
                if os.path.isdir(os.path.join(self.RESULTS_DIR, name))
            ]
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

        # Initialize client based on type
        self.client_type = client_type
        self.model = model
        self.provider = provider

        # Provider-specific settings
        self.provider_settings = {
            "deepseek": {
                "api_key": os.getenv("DEEPSEEK_API_KEY"),
                "base_url": "https://api.deepseek.com",
            },
            "openai": {"api_key": os.getenv("OPENAI_API_KEY")},
            "together": {
                "api_key": os.getenv("TOGETHER_API_KEY"),
                "base_url": "https://api.together.xyz/v1",
            },
        }

        if client_type == "openai":
            if self.provider == "openai":
                self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            elif self.provider in ["deepseek", "together"]:
                self.client = OpenAI(
                    api_key=self.provider_settings[self.provider]["api_key"],
                    base_url=self.provider_settings[self.provider]["base_url"],
                )
            else:
                raise ValueError(
                    f"Unsupported provider: {provider} for client type: {client_type}"
                )
        elif client_type == "mlx":
            try:
                from MLXChatClient import MLXChatClient

                self.client = MLXChatClient()
                print("Using MLX client")
            except ImportError:
                raise ImportError("Please install the MLX package to use MLX client")
        elif client_type == "hf":
            try:
                from huggingface_hub import InferenceClient

                # Initialize with provider-specific settings
                if provider == "together":
                    self.client = InferenceClient(
                        provider="together", api_key=os.getenv("TOGETHER_API_KEY")
                    )
                    print("Using Together AI provider with Hugging Face client")
                else:
                    # Default HF client
                    self.client = InferenceClient(token=os.getenv("HF_API_TOKEN"))
                    print("Using standard Hugging Face Inference API")
            except ImportError:
                raise ImportError(
                    "Please install huggingface_hub package to use HF client"
                )
        else:
            raise ValueError(f"Unsupported client type: {client_type}")

        self.agents = self.create_agents(agent_count, traitor_count)
        self.game_over = False
        self.history = []  # Stores past discussions
        self.round_number = 1
        self.traitors_last_eliminated = None

        # Write a .yaml file with the configurations for the experiment
        with open(f"{self.RESULTS_DIR}/config.yaml", "w") as f:
            f.write(f"agent_count: {agent_count}\n")
            f.write(f"traitor_count: {traitor_count}\n")
            f.write(f"model: {model}\n")
            f.write(f"seed: {seed}\n")
            f.write(f"client_type: {client_type}\n")
            f.write(f"provider: {provider}\n")
            # Write if agent is Traitor or Faithful
            for agent in self.agents:
                f.write(f"agent_{agent['id']}: {agent['role']}\n")

            f.write("\n")

        # Create a .txt file to keep the game history
        self.HISTORY_FILE = f"{self.RESULTS_DIR}/history.txt"

        # Write a .csv file to keep votes and eliminations
        self.VOTING_FILE = f"{self.RESULTS_DIR}/votes.csv"
        with open(self.VOTING_FILE, "w") as f:
            f.write("Round,Vote_Type,Player_ID,Role,Vote_Target,Eliminated\n")

    def create_agents(self, agent_count, traitor_count):
        """Initialize agents with unique roles."""
        if traitor_count >= agent_count:
            raise ValueError("Traitor count must be less than agent count")

        agents = [
            {"id": i, "role": "Faithful", "memory": "", "model": self.model, "path": None}
            for i in range(agent_count)
        ]

        # Create a path for each agent
        for agent in agents:
            agent["path"] = f"{self.RESULTS_DIR}/agent-{agent['id']}"
            Path(agent["path"]).mkdir(parents=True, exist_ok=True)

        # Assign traitor roles
        traitors = random.sample(agents, traitor_count)
        for agent in traitors:
            agent["role"] = "Traitor"

        # Give each agent knowledge of other traitors if they are a traitor
        for agent in agents:
            if agent["role"] == "Traitor":
                traitor_ids = [
                    t["id"]
                    for t in agents
                    if t["role"] == "Traitor" and t["id"] != agent["id"]
                ]
                agent["fellow_traitors"] = traitor_ids

        return agents

    def get_role_prompt(self, agent):
        """Generate the initial role-specific prompt for each agent."""
        if agent["role"] == "Faithful":
            return (
                "You are a Faithful in The Traitors game.\n"
                "Your goal is to find and eliminate all Traitors before they take over.\n"
                "Engage in discussions, observe behavior, and vote wisely.\n"
                "You do not know who the other Faithfuls are. Be cautious in your accusations.\n"
                "Convince others to eliminate real Traitors and defend yourself if accused.\n"
                "Faithfuls win if all Traitors are eliminated."
            )
        else:
            fellow_traitors = agent.get("fellow_traitors", [])
            return (
                "You are a Traitor in The Traitors game.\n"
                f"Your fellow Traitors are agents: {', '.join(map(str, fellow_traitors))}.\n"
                "Your goal is to secretly eliminate the Faithfuls and avoid being discovered.\n"
                "Pretend to be a Faithful and manipulate votes to eliminate innocent players.\n"
                "Work together with fellow Traitors in secret.\n"
                "Lie convincingly if accused and mislead the Faithfuls.\n"
                "Traitors win if they outnumber or equal the Faithfuls."
            )

    def call_llm(self, agent):
        """Call the LLM API to generate agent responses."""
        role_description = self.get_role_prompt(agent)
        agent_memory = agent.get("memory", "")
        prompt = agent.get("current_prompt", "")

        # Add formatting instructions with delimiters
        formatted_prompt = (
            f"{prompt}\n\n"
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
            # Use appropriate client for API call
            if self.client_type == "openai":
                response = self.client.chat.completions.create(
                    model=agent["model"],
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are Player {agent['id']}. {role_description}\n\nYour memory: {agent_memory}",
                        },
                        {"role": "user", "content": formatted_prompt},
                    ],
                    stream=False,
                )
                full_response = response.choices[0].message.content
            
            elif self.client_type == "mlx":
                response = self.client.create(
                    model=agent["model"],
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are Player {agent['id']}. {role_description}\n\nYour memory: {agent_memory}",
                        },
                        {"role": "user", "content": formatted_prompt},
                    ],
                    stream=False,
                )
                full_response = response["choices"][0]["message"]["content"]

            elif self.client_type == "hf":
                # Hugging Face client implementation
                system_message = f"You are Player {agent['id']}. {role_description}\n\nYour memory: {agent_memory}"

                if self.provider == "together":
                    # Use chat_completion for Together AI provider
                    response = self.client.chat_completion(
                        model=agent["model"],
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": formatted_prompt},
                        ],
                        temperature=0.7,
                        max_tokens=500,
                    )
                    full_response = response.choices[0].message.content
                else:
                    # Standard HF text generation
                    full_response = self.client.text_generation(
                        prompt=f"<s>[INST] <<SYS>>\n{system_message}\n<</SYS>>\n\n{formatted_prompt} [/INST]",
                        model=agent["model"],
                        max_new_tokens=500,
                        temperature=0.7,
                        top_p=0.9,
                    )

            # Extract only the content between --- markers
            import re

            # Put the full response in a file under agent's path
            file = f"{agent['path']}/inner-toughts.txt"
            if os.path.exists(file):
                with open(file, "a") as f:
                    print(full_response, file=f)
            else:
                with open(file, "w") as f:
                    print(full_response, file=f)

            pattern = r"---\s*([\s\S]*?)\s*---"
            match = re.search(pattern, full_response)


            if match:
                return match.group(1).strip()
            else:
                # If no markers found, use the whole response but add a note
                print(f"Warning: Agent {agent['id']} didn't use the requested format")
                with open(self.HISTORY_FILE, "a") as f:
                    print(f"Warning: Agent {agent['id']} didn't use the requested format", file=f)
                return full_response

        except Exception as e:
            print(f"Error calling the LLM API: {e}")
            with open(self.HISTORY_FILE, "a") as f:
                print(f"Error calling the LLM API: {e}", file=f)
            return f"Agent {agent['id']} couldn't respond due to an error."

    def get_game_status(self):
        """Return the current game status for prompts."""
        active_agents = [a for a in self.agents if "eliminated" not in a]
        eliminated_agents = [a for a in self.agents if "eliminated" in a]

        status = f"Round {self.round_number}: "
        status += f"Active players: {', '.join(str(a['id']) for a in active_agents)}. "

        if eliminated_agents:
            status += f"Eliminated players: {', '.join(str(a['id']) for a in eliminated_agents)}. "

        status += f"Game history: {' '.join(self.history)}"
        return status

    def discussion_phase(self):
        """Agents communicate and discuss who to vote out."""
        print(f"\n--- DISCUSSION PHASE (ROUND {self.round_number}) ---")
        with open(self.HISTORY_FILE, "a") as f:
            print(f"\n--- DISCUSSION PHASE (ROUND {self.round_number}) ---", file=f)
        new_discussions = []

        # Add info about last elimination by traitors if any
        if self.traitors_last_eliminated:
            new_discussions.append(self.traitors_last_eliminated)

        active_agents = [a for a in self.agents if "eliminated" not in a]

        # First round of comments - each agent shares suspicions
        for i, agent in enumerate(active_agents):
            game_status = self.get_game_status()
            agent["current_prompt"] = (
                f"{game_status}\n\n"
                "You are in a room with other players to discuss who might be a traitor. "
                "Who do you suspect and why? Be strategic based on your role. "
                "Consider past eliminations and discussions."
            )

            if self.round_number == 1:
                agent[
                    "current_prompt"
                ] += "\n\nThis is the first round of discussions, therefore you still don't have"
                "any information about players who haven't spoken yet."

            if new_discussions:
                agent[
                    "current_prompt"
                ] += f"\n\nCurrent discussion: {' '.join(new_discussions)}"

            response = self.call_llm(agent)
            new_discussions.append(f"Player {agent['id']}: {response}")
            print(new_discussions[-1])
            with open(self.HISTORY_FILE, "a") as f:
                print(new_discussions[-1], file=f)

        # Second round - reactions to other agents' comments
        reaction_discussions = []
        for agent in active_agents:
            agent["current_prompt"] = (
                "After hearing everyone's suspicions, what is your response? "
                f"\n\nDiscussion so far: {' '.join(new_discussions)}"
            )

            response = self.call_llm(agent)
            reaction_discussions.append(f"Player {agent['id']} responds: {response}")
            print(reaction_discussions[-1])
            with open(self.HISTORY_FILE, "a") as f:
                print(reaction_discussions[-1], file=f)

        # Combine all discussions
        all_discussions = new_discussions + reaction_discussions

        # Update memory for each agent
        for agent in active_agents:
            agent["current_prompt"] = (
                "Summarize the most important points from this discussion that you want to remember. "
                f"Focus on who you believe are traitors and why: {' '.join(all_discussions)}"
            )
            memory_response = self.call_llm(agent)

            # Add timestamp to memory
            agent[
                "memory"
            ] += f"\n--- ROUND {self.round_number} MEMORY ---\n{memory_response}\n"

    def voting_phase(self):
        """Agents vote to eliminate a player."""
        print(f"\n--- VOTING PHASE (ROUND {self.round_number}) ---")
        with open(self.HISTORY_FILE, "a") as f:
            print(f"\n--- VOTING PHASE (ROUND {self.round_number}) ---", file=f)
        votes = {}
        active_agents = [a for a in self.agents if "eliminated" not in a]

        # a list with dictionaries with the votes
        votes_list = []

        for agent in active_agents:
            agent["current_prompt"] = (
                f"Based on all discussions and your memory:\n{agent['memory']}\n\n"
                f"It's time to vote. The active players are: {', '.join(str(a['id']) for a in active_agents)}.\n"
                "Who are you voting to eliminate? Respond with ONLY the player number."
            )

            vote_response = self.call_llm(agent)

            # Extract just the number from the response
            import re

            vote_match = re.search(r"\d+", vote_response)
            if vote_match:
                vote = vote_match.group()
                votes[vote] = votes.get(vote, 0) + 1
                print(f"Player {agent['id']} votes for Player {vote}")
                with open(self.HISTORY_FILE, "a") as f:
                    print(f"Player {agent['id']} votes for Player {vote}", file=f)

                # Add the vote to the list
                votes_list.append(
                    {
                        "Round": self.round_number,
                        "Vote_Type": "General",
                        "Player_ID": agent["id"],
                        "Role": agent["role"],
                        "Vote_Target": vote,
                        "Eliminated": False,
                    }
                )
            else:
                print(f"Player {agent['id']} cast an invalid vote: {vote_response}")
                with open(self.HISTORY_FILE, "a") as f:
                    print(f"Player {agent['id']} cast an invalid vote: {vote_response}", file=f)

                # Add the invalid vote to the list
                votes_list.append(
                    {
                        "Round": self.round_number,
                        "Vote_Type": "General",
                        "Player_ID": agent["id"],
                        "Role": agent["role"],
                        "Vote_Target": None,
                        "Eliminated": False,
                    }
                )

        if not votes:
            print("No valid votes were cast!")
            with open(self.HISTORY_FILE, "a") as f:
                print("No valid votes were cast!", file=f)
            return

        # Find the agent with the most votes
        eliminated = max(votes, key=votes.get)
        eliminated_agent = next(
            (a for a in self.agents if str(a["id"]) == eliminated), None
        )

        # Loop through the list and replace the eliminated in each dictionary
        for vote in votes_list:
            vote["Eliminated"] = eliminated

        # Write the votes to the .csv file
        with open(self.VOTING_FILE, "a") as f:
            for vote in votes_list:
                f.write(
                    f"{vote['Round']},{vote['Vote_Type']},{vote['Player_ID']},{vote['Role']},{vote['Vote_Target']},{vote['Eliminated']}\n"
                )

        if eliminated_agent:
            eliminated_agent["eliminated"] = True
            elimination_message = f"Player {eliminated} was eliminated. Player {eliminated} was a {eliminated_agent['role']}."
            print(elimination_message)
            with open(self.HISTORY_FILE, "a") as f:
                print(elimination_message, file=f)
            self.history.append(elimination_message)

            # Add to each agent's memory
            for agent in active_agents:
                if "eliminated" not in agent:
                    agent["memory"] += f"\n{elimination_message}\n"

            self.post_elimination_discussion(eliminated)

    def post_elimination_discussion(self, eliminated):
        """Allow agents to discuss after elimination is revealed."""
        print("\n--- POST-ELIMINATION DISCUSSION ---")
        with open(self.HISTORY_FILE, "a") as f:
            print("\n--- POST-ELIMINATION DISCUSSION ---", file=f)
        eliminated_agent = next(
            (a for a in self.agents if str(a["id"]) == eliminated), None
        )

        if not eliminated_agent:
            return

        discussion_prompts = []
        active_agents = [a for a in self.agents if "eliminated" not in a]

        for agent in active_agents:
            agent["current_prompt"] = (
                f"Player {eliminated} was eliminated and was a {eliminated_agent['role']}. "
                "What are your thoughts on this elimination? Has this changed your suspicions? "
                "Be strategic based on your role."
            )

            if discussion_prompts:
                agent[
                    "current_prompt"
                ] += f"\n\nOngoing discussion: {' '.join(discussion_prompts)}"

            response = self.call_llm(agent)
            discussion_prompts.append(f"Player {agent['id']}: {response}")
            print(discussion_prompts[-1])
            with open(self.HISTORY_FILE, "a") as f:
                print(discussion_prompts[-1], file=f)

        # Update memory for each agent
        for agent in active_agents:
            agent["current_prompt"] = (
                f"Summarize key insights from this post-elimination discussion: {' '.join(discussion_prompts)}"
            )
            memory_response = self.call_llm(agent)
            agent[
                "memory"
            ] += f"\n--- POST-ELIMINATION INSIGHTS ---\n{memory_response}\n"

    def traitor_discussion_phase(self):
        """Traitors secretly discuss who to eliminate."""
        print("\n--- TRAITOR DISCUSSION PHASE ---")
        traitors = [
            agent
            for agent in self.agents
            if agent["role"] == "Traitor" and "eliminated" not in agent
        ]

        if not traitors:
            return

        active_faithfuls = [
            a for a in self.agents if a["role"] == "Faithful" and "eliminated" not in a
        ]

        traitor_discussion = []
        for traitor in traitors:
            traitor["current_prompt"] = (
                f"SECRET TRAITOR MEETING: You are with your fellow traitors: {', '.join(str(t['id']) for t in traitors)}.\n"
                f"The Faithfuls still in the game are: {', '.join(str(a['id']) for a in active_faithfuls)}.\n"
                "Who do you suggest eliminating next and why? Be strategic to avoid detection."
            )

            if traitor_discussion:
                traitor[
                    "current_prompt"
                ] += f"\n\nTraitor discussion so far: {' '.join(traitor_discussion)}"

            response = self.call_llm(traitor)
            traitor_discussion.append(f"Traitor {traitor['id']}: {response}")
            print(traitor_discussion[-1])
            with open(self.HISTORY_FILE, "a") as f:
                print(traitor_discussion[-1], file=f)

        # Second round for traitors to reach consensus
        consensus_discussion = []
        for traitor in traitors:
            traitor["current_prompt"] = (
                "Based on the traitor discussion, who do you now think we should eliminate? "
                f"Discussion: {' '.join(traitor_discussion)}"
            )

            response = self.call_llm(traitor)
            consensus_discussion.append(
                f"Traitor {traitor['id']} concludes: {response}"
            )
            print(consensus_discussion[-1])
            with open(self.HISTORY_FILE, "a") as f:
                print(consensus_discussion[-1], file=f)

        # Update traitor memories
        traitor_memory = f"--- SECRET TRAITOR MEETING (ROUND {self.round_number}) ---\n"
        traitor_memory += " ".join(traitor_discussion + consensus_discussion)

        for traitor in traitors:
            traitor["memory"] += f"\n{traitor_memory}\n"

        self.traitor_elimination_phase(traitors, active_faithfuls)

    def traitor_elimination_phase(self, traitors, active_faithfuls):
        """Traitors vote to eliminate a Faithful."""
        print("\n--- TRAITOR ELIMINATION PHASE ---")
        with open(self.HISTORY_FILE, "a") as f:
            print("\n--- TRAITOR ELIMINATION PHASE ---", file=f)

        if not traitors or not active_faithfuls:
            return

        # a list with dictionaries with the votes
        votes_list = []

        votes = {}
        for traitor in traitors:
            traitor["current_prompt"] = (
                "Based on the traitor discussion, which Faithful do you vote to eliminate tonight? "
                f"The Faithfuls are: {', '.join(str(a['id']) for a in active_faithfuls)}. "
                "Respond with ONLY the player number."
            )

            vote_response = self.call_llm(traitor)

            # Extract just the number
            import re

            vote_match = re.search(r"\d+", vote_response)
            if vote_match:
                vote = vote_match.group()
                votes[vote] = votes.get(vote, 0) + 1
                print(f"Traitor {traitor['id']} votes to eliminate Player {vote}")
                with open(self.HISTORY_FILE, "a") as f:
                    print(f"Traitor {traitor['id']} votes to eliminate Player {vote}", file=f)

                # Add the vote to the list
                votes_list.append(
                    {
                        "Round": self.round_number,
                        "Vote_Type": "Traitor",
                        "Player_ID": traitor["id"],
                        "Role": traitor["role"],
                        "Vote_Target": vote,
                        "Eliminated": False,
                    }
                )
            else:
                print(f"Traitor {traitor['id']} cast an invalid vote: {vote_response}")
                with open(self.HISTORY_FILE, "a") as f:
                    print(f"Traitor {traitor['id']} cast an invalid vote: {vote_response}", file=f)

                # Add the invalid vote to the list
                votes_list.append(
                    {
                        "Round": self.round_number,
                        "Vote_Type": "Traitor",
                        "Player_ID": traitor["id"],
                        "Role": traitor["role"],
                        "Vote_Target": None,
                        "Eliminated": False,
                    }
                )

        if not votes:
            print("No valid traitor votes were cast!")
            with open(self.HISTORY_FILE, "a") as f:
                print("No valid traitor votes were cast!", file=f)
            return

        # Find the agent with the most votes
        eliminated = max(votes, key=votes.get)
        eliminated_agent = next(
            (a for a in active_faithfuls if str(a["id"]) == eliminated), None
        )

        # Loop through the list and replace the eliminated in each dictionary
        for vote in votes_list:
            vote["Eliminated"] = eliminated

        # Write the votes to the .csv file
        with open(self.VOTING_FILE, "a") as f:
            for vote in votes_list:
                f.write(
                    f"{vote['Round']},{vote['Vote_Type']},{vote['Player_ID']},{vote['Role']},{vote['Vote_Target']},{vote['Eliminated']}\n"
                )

        if eliminated_agent:
            eliminated_agent["eliminated"] = True
            elimination_message = (
                f"Player {eliminated} was eliminated by the traitors in the night."
            )
            print(elimination_message)
            with open(self.HISTORY_FILE, "a") as f:
                print(elimination_message, file=f)
            self.history.append(elimination_message)
            self.traitors_last_eliminated = f"Moderator: Player {eliminated} was eliminated last night by the traitors."

            # Update all active agents' memory
            for agent in self.agents:
                if "eliminated" not in agent:
                    agent["memory"] += f"\n{elimination_message}\n"

    def check_win_conditions(self):
        """Determine if the game has ended."""
        faithfuls = sum(
            1 for a in self.agents if a["role"] == "Faithful" and "eliminated" not in a
        )
        traitors = sum(
            1 for a in self.agents if a["role"] == "Traitor" and "eliminated" not in a
        )

        print(f"\n--- GAME STATUS: {faithfuls} Faithfuls, {traitors} Traitors ---")
        with open(self.HISTORY_FILE, "a") as f:
            print(f"\n--- GAME STATUS: {faithfuls} Faithfuls, {traitors} Traitors ---", file=f)

        if traitors == 0:
            print("\n🎉 FAITHFULS WIN! All traitors have been eliminated.")
            with open(self.HISTORY_FILE, "a") as f:
                print("\n🎉 FAITHFULS WIN! All traitors have been eliminated.", file=f)
            self.game_over = True
            return "Faithfuls"
        elif traitors >= faithfuls:
            print("\n💀 TRAITORS WIN! They now equal or outnumber the Faithfuls.")
            with open(self.HISTORY_FILE, "a") as f:
                print("\n💀 TRAITORS WIN! They now equal or outnumber the Faithfuls.", file=f)
            self.game_over = True
            return "Traitors"
        return None

    def run(self):
        """Main game loop."""
        # Start a timer
        start_time = time.time()
        print("\n===== THE TRAITORS GAME =====")
        print(
            f"Starting with {len(self.agents)} players, including {sum(1 for a in self.agents if a['role'] == 'Traitor')} traitors"
        )
        with open(self.HISTORY_FILE, "w") as f:
            f.write("===== THE TRAITORS GAME =====\n\n")
            f.write(
                f"Starting with {len(self.agents)} players, including {sum(1 for a in self.agents if a['role'] == 'Traitor')} traitors\n\n"
            )

        if self.seed is not None:
            print(f"Game seed: {self.seed}")
            with open(self.HISTORY_FILE, "a") as f:
                print(f"Game seed: {self.seed}", file=f)
        print(
            f"Using client: {self.client_type}"
            + (f" with provider: {self.provider}" if self.provider else "")
        )
        with open(self.HISTORY_FILE, "a") as f:
            print(
                f"Using client: {self.client_type}"
                + (f" with provider: {self.provider}" if self.provider else ""), file=f
            )
        print(f"Model: {self.model}")
        with open(self.HISTORY_FILE, "a") as f:
            print(f"Model: {self.model}", file=f)

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
            print("\n===== GAME SUMMARY =====")
            with open(self.HISTORY_FILE, "a") as f:
                print("\n===== GAME SUMMARY =====", file=f)
            print(f"The game simulation took {end_time - start_time:.2f} seconds")
            with open(self.HISTORY_FILE, "a") as f:
                print(f"The game simulation took {end_time - start_time:.2f} seconds", file=f)    
            print(f"The game lasted {self.round_number} rounds")
            with open(self.HISTORY_FILE, "a") as f:
                print(f"The game lasted {self.round_number} rounds", file=f)
            print(
                "Traitors were:",
                ", ".join(
                    f"Player {a['id']}" for a in self.agents if a["role"] == "Traitor"
                ),
            )
            print(
                "Eliminated agents:",
                ", ".join(
                    f"Player {a['id']} ({a['role']})"
                    for a in self.agents
                    if "eliminated" in a
                ),
            )
            print(
                "Survivors:",
                ", ".join(
                    f"Player {a['id']} ({a['role']})"
                    for a in self.agents
                    if "eliminated" not in a
                ),
            )
            with open(self.HISTORY_FILE, "a") as f:
                print(
                    "Traitors were:",
                    ", ".join(
                        f"Player {a['id']}" for a in self.agents if a["role"] == "Traitor"
                    ),
                    file=f,
                )
                print(
                    "Eliminated agents:",
                    ", ".join(
                        f"Player {a['id']} ({a['role']})"
                        for a in self.agents
                        if "eliminated" in a
                    ),
                    file=f,
                )
                print(
                    "Survivors:",
                    ", ".join(
                        f"Player {a['id']} ({a['role']})"
                        for a in self.agents
                        if "eliminated" not in a
                    ),
                    file=f,
                )

        except KeyboardInterrupt:
            print("\nGame interrupted by user.")
            with open(self.HISTORY_FILE, "a") as f:
                print("\nGame interrupted by user.", file=f)
        except Exception as e:
            print(f"Game error: {e}")
            with open(self.HISTORY_FILE, "a") as f:
                print(f"Game error: {e}", file=f)

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
