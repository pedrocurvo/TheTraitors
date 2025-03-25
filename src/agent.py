import os
import re
from pathlib import Path

# Update import to use the module from src
from src.prompt_manager import PromptManager


class Agent:
    """Represents a player in the Traitors Game."""

    def __init__(
        self, agent_id, role, model, results_dir, llm_client=None, traits=None
    ):
        """Initialize an agent with basic attributes.

        Args:
            agent_id (int): The unique identifier for this agent
            role (str): Either "Faithful" or "Traitor"
            model (str): The LLM model to use for this agent
            results_dir (str): Directory to store agent-specific files
            llm_client: The LLM client to use for this agent
            traits (dict, optional): Dictionary of personality traits for this agent
        """
        self.id = agent_id
        self.role = role
        self.model = model
        self.current_prompt = ""
        self.eliminated = False
        self.fellow_traitors = []
        self.llm_client = llm_client
        self.traits = traits or {}  # Store traits as an empty dict if None

        # New structured memory system
        self.memory = {
            "player_info": {},  # Information about other players
            "game_events": [],  # Chronological list of significant events
            "suspicions": {},  # Player-indexed suspicions
            "alliances": [],  # Potential allies identified
            "strategies": [],  # Strategic thoughts about gameplay
            "round_summaries": {},  # Summary of each game round
            "personal_notes": [],  # Miscellaneous observations
        }

        # Create a path for the agent
        self.path = f"{results_dir}/agent-{self.id}"
        Path(self.path).mkdir(parents=True, exist_ok=True)

    def set_llm_client(self, llm_client):
        """Set the LLM client for this agent.

        Args:
            llm_client: The LLM client to use
        """
        self.llm_client = llm_client

    def call_llm(self, user_prompt):
        """Call the LLM API to generate a response.

        Args:
            user_prompt (str): The prompt to send to the LLM

        Returns:
            str: The LLM's response
        """
        if not self.llm_client:
            raise ValueError(f"Agent {self.id} has no LLM client set")

        # Create system message with role and memory using the prompt manager
        system_message = PromptManager.get_system_prompt(
            self, self.get_formatted_memory()
        )

        # Call the LLM client
        full_response = self.llm_client.call(system_message, user_prompt)

        # Log the inner thoughts
        self.log_inner_thoughts(full_response)

        # Extract and return the dialogue
        return self.extract_dialogue(full_response)

    def is_traitor(self):
        """Check if the agent is a traitor."""
        return self.role == "Traitor"

    def is_faithful(self):
        """Check if the agent is faithful."""
        return self.role == "Faithful"

    def is_active(self):
        """Check if the agent is still active in the game."""
        return not self.eliminated

    def is_eliminated(self):
        """Check if the agent has been eliminated."""
        return self.eliminated

    def eliminate(self):
        """Mark the agent as eliminated."""
        self.eliminated = True

    def set_fellow_traitors(self, traitor_ids):
        """Set the IDs of fellow traitors (for traitor agents only).

        Args:
            traitor_ids (list): List of IDs of other traitor agents
        """
        if self.is_traitor():
            self.fellow_traitors = traitor_ids

    def add_to_memory(self, content, section=None):
        """Add content to the agent's memory in the appropriate category.

        Args:
            content (str): The content to add to memory
            section (str, optional): Section/category for the memory entry
        """
        # Extract round number if it's in the section name
        round_match = re.search(r"ROUND (\d+)", section if section else "")
        round_num = int(round_match.group(1)) if round_match else None

        # Choose memory category based on section name or content analysis
        if section and "MEMORY" in section:
            # Process and categorize the memory based on content
            self._categorize_memory(content, round_num)
        elif section and "THOUGHTS ON PLAYERS" in section:
            self._process_player_information(content)
        elif section and "ELIMINATION" in section:
            self.memory["game_events"].append(
                {"type": "elimination", "details": content, "round": round_num}
            )
        elif section and "DISCUSSION" in section:
            if round_num is not None:
                if "discussions" not in self.memory["round_summaries"].setdefault(
                    round_num, {}
                ):
                    self.memory["round_summaries"][round_num]["discussions"] = []
                self.memory["round_summaries"][round_num]["discussions"].append(content)
        else:
            # Default case - add to personal notes
            self.memory["personal_notes"].append(content)

        # Also save to the flat memory format for backward compatibility and logging
        self._save_to_memory_file(content, section)

    def _categorize_memory(self, content, round_num=None):
        """Analyze and categorize memory content into appropriate sections.

        Args:
            content (str): Memory content to categorize
            round_num (int, optional): Round number if available
        """
        # Categorize as suspicion if it mentions suspicion-related keywords
        if any(
            keyword in content.lower()
            for keyword in ["suspect", "suspicious", "traitor might be"]
        ):
            # Look for player IDs mentioned in suspicions
            player_mentions = re.findall(r"Player (\d+)", content)
            for player_id in player_mentions:
                if player_id != str(self.id):  # Don't record suspicions about self
                    if player_id not in self.memory["suspicions"]:
                        self.memory["suspicions"][player_id] = []
                    self.memory["suspicions"][player_id].append(
                        {"content": content, "round": round_num}
                    )

        # Categorize as strategy if it mentions strategy-related keywords
        if any(
            keyword in content.lower()
            for keyword in ["strategy", "plan", "should", "will try"]
        ):
            self.memory["strategies"].append({"content": content, "round": round_num})

        # Add to round summary if round number is available
        if round_num is not None:
            if "summary" not in self.memory["round_summaries"].setdefault(
                round_num, {}
            ):
                self.memory["round_summaries"][round_num]["summary"] = content
            else:
                self.memory["round_summaries"][round_num]["summary"] += f"\n{content}"

    def _process_player_information(self, content):
        """Extract and store information about other players.

        Args:
            content (str): Content containing player information
        """
        # Look for patterns like "Player X: ..." or "Player X is..."
        player_info_patterns = [
            r"Player (\d+)[:\s]+([^\.]+\.)",
            r"Player (\d+) is ([^\.]+\.)",
        ]

        for pattern in player_info_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                player_id, info = match
                if player_id != str(self.id):  # Don't record info about self
                    if player_id not in self.memory["player_info"]:
                        self.memory["player_info"][player_id] = []
                    self.memory["player_info"][player_id].append(info.strip())

    def _save_to_memory_file(self, content, section=None):
        """Save memory to the memory file for persistent storage and logging.

        Args:
            content (str): The content to add to memory file
            section (str, optional): Section header for the memory entry
        """
        memory_file = f"{self.path}/memory.txt"
        mode = "a" if os.path.exists(memory_file) else "w"

        with open(memory_file, mode) as f:
            if section:
                f.write(f"\n--- {section} ---\n{content}\n")
            else:
                f.write(f"\n{content}\n")

    def get_formatted_memory(self):
        """Format the structured memory into a string for the LLM prompt.

        Returns:
            str: A formatted string representation of agent's memory
        """
        sections = []

        # Add player information
        if self.memory["player_info"]:
            player_info_section = "--- PLAYER INFORMATION ---\n"
            for player_id, info_list in self.memory["player_info"].items():
                player_info_section += f"Player {player_id}: {' '.join(info_list)}\n"
            sections.append(player_info_section)

        # Add suspicions
        if self.memory["suspicions"]:
            suspicions_section = "--- SUSPICIONS ---\n"
            for player_id, suspicions_list in self.memory["suspicions"].items():
                suspicions_section += f"Suspicions about Player {player_id}:\n"
                for s in suspicions_list:
                    suspicions_section += f"- {s['content']}\n"
            sections.append(suspicions_section)

        # Add game events
        if self.memory["game_events"]:
            events_section = "--- GAME EVENTS ---\n"
            for event in self.memory["game_events"]:
                events_section += (
                    f"Round {event.get('round', '?')}: {event['details']}\n"
                )
            sections.append(events_section)

        # Add most recent round summaries (last 3 rounds)
        rounds = sorted(self.memory["round_summaries"].keys(), reverse=True)
        if rounds:
            recent_rounds = rounds[: min(3, len(rounds))]
            rounds_section = "--- RECENT ROUNDS ---\n"
            for round_num in sorted(recent_rounds):
                round_data = self.memory["round_summaries"][round_num]
                rounds_section += f"Round {round_num} Summary: {round_data.get('summary', 'No summary')}\n"
            sections.append(rounds_section)

        # Add key strategies
        if self.memory["strategies"]:
            strategies_section = "--- MY STRATEGIES ---\n"
            # Show the most recent 3 strategies
            for strategy in self.memory["strategies"][-3:]:
                strategies_section += f"- {strategy['content']}\n"
            sections.append(strategies_section)

        # Add personal notes
        if self.memory["personal_notes"]:
            notes_section = "--- PERSONAL NOTES ---\n"
            # Only include the most recent 3 notes to avoid cluttering
            for note in self.memory["personal_notes"][-3:]:
                notes_section += f"- {note}\n"
            sections.append(notes_section)

        return "\n\n".join(sections)

    def get_memory_by_category(self, category):
        """Retrieve a specific category of memory.

        Args:
            category (str): The memory category to retrieve

        Returns:
            Any: The requested memory category
        """
        return self.memory.get(category, None)

    def get_player_info(self, player_id=None):
        """Get information about other players.

        Args:
            player_id (str, optional): Specific player ID to get info about

        Returns:
            dict or list: Player information
        """
        if player_id:
            return self.memory["player_info"].get(str(player_id), [])
        return self.memory["player_info"]

    def get_suspicions(self, player_id=None):
        """Get suspicions about other players.

        Args:
            player_id (str, optional): Specific player ID to get suspicions about

        Returns:
            dict or list: Suspicions information
        """
        if player_id:
            return self.memory["suspicions"].get(str(player_id), [])
        return self.memory["suspicions"]

    def get_round_summary(self, round_num):
        """Get summary for a specific round.

        Args:
            round_num (int): Round number to retrieve

        Returns:
            dict: Round summary data
        """
        return self.memory["round_summaries"].get(round_num, {})

    def set_prompt(self, prompt):
        """Set the current prompt for the agent.

        Args:
            prompt (str): The prompt to set
        """
        self.current_prompt = prompt

    def log_inner_thoughts(self, thoughts):
        """Log the agent's inner thoughts to a file.

        Args:
            thoughts (str): The thoughts to log
        """
        file_path = f"{self.path}/inner-thoughts.txt"
        mode = "a" if os.path.exists(file_path) else "w"

        with open(file_path, mode) as f:
            timestamp = self.get_timestamp()
            print(f"\n--- {timestamp} ---\n{thoughts}\n", file=f)

    def get_timestamp(self):
        """Get a timestamp for logging purposes."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_role_prompt(self):
        """This method is deprecated. Use PromptManager.get_system_prompt instead."""
        raise DeprecationWarning(
            "This method is deprecated. Use PromptManager.get_system_prompt instead."
        )

    def extract_dialogue(self, full_response):
        """Extract dialogue from between triple dashes in the response.

        Args:
            full_response (str): The full response from the LLM

        Returns:
            str: The extracted dialogue, or the full response if no markers found
        """
        pattern = r"---\s*([\s\S]*?)\s*---"
        match = re.search(pattern, full_response)

        if match:
            return match.group(1).strip()
        else:
            # If no markers found, use the whole response
            return full_response

    def to_dict(self):
        """Convert the agent to a dictionary representation.

        Returns:
            dict: Dictionary representation of the agent
        """
        return {
            "id": self.id,
            "role": self.role,
            "model": self.model,
            "eliminated": self.eliminated,
            "fellow_traitors": self.fellow_traitors,
            "traits": self.traits,
            "memory": self.memory,  # Store the structured memory
        }

    @classmethod
    def from_dict(cls, data, results_dir, llm_client=None):
        """Create an Agent instance from a dictionary.

        Args:
            data (dict): Dictionary containing agent data
            results_dir (str): Directory to store agent-specific files
            llm_client: Optional LLM client to use

        Returns:
            Agent: A new Agent instance
        """
        agent = cls(
            agent_id=data["id"],
            role=data["role"],
            model=data.get("model", "gpt-3.5-turbo"),
            results_dir=results_dir,
            llm_client=llm_client,
            traits=data.get("traits", None),
        )
        agent.eliminated = data.get("eliminated", False)
        agent.fellow_traitors = data.get("fellow_traitors", [])

        # Handle both old string-based and new structured memory
        if isinstance(data.get("memory", ""), dict):
            agent.memory = data["memory"]
        else:
            # Legacy support for string-based memory
            old_memory = data.get("memory", "")
            agent.memory["personal_notes"].append(old_memory)

        return agent
