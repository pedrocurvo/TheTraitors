from pathlib import Path
import os
import re
from typing import Optional


class Agent:
    """Represents a player in the Traitors Game."""

    def __init__(self, agent_id, role, model, results_dir, llm_client=None):
        """Initialize an agent with basic attributes.

        Args:
            agent_id (int): The unique identifier for this agent
            role (str): Either "Faithful" or "Traitor"
            model (str): The LLM model to use for this agent
            results_dir (str): Directory to store agent-specific files
            llm_client: The LLM client to use for this agent
        """
        self.id = agent_id
        self.role = role
        self.model = model
        self.memory = ""
        self.current_prompt = ""
        self.eliminated = False
        self.fellow_traitors = []
        self.llm_client = llm_client

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

        # Create system message with role and memory
        system_message = f"You are Player {self.id}. {self.get_role_prompt()}\n\nYour memory: {self.memory}"

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
        """Add content to the agent's memory with optional section formatting.

        Args:
            content (str): The content to add to memory
            section (str, optional): Section header for the memory entry
        """
        if section:
            self.memory += f"\n--- {section} ---\n{content}\n"
        else:
            self.memory += f"\n{content}\n"

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
        """Generate the role-specific prompt for this agent.

        Returns:
            str: A role-specific prompt describing the agent's goals
        """
        if self.is_faithful():
            return (
                "You are a Faithful in The Traitors game.\n"
                "Your goal is to find and eliminate all Traitors before they take over.\n"
                "Engage in discussions, observe behavior, and vote wisely.\n"
                "You do not know who the other Faithfuls are. Be cautious in your accusations.\n"
                "Convince others to eliminate real Traitors and defend yourself if accused.\n"
                "Faithfuls win if all Traitors are eliminated."
            )
        else:
            fellow_traitors_str = ", ".join(map(str, self.fellow_traitors))
            return (
                "You are a Traitor in The Traitors game.\n"
                f"Your fellow Traitors are agents: {fellow_traitors_str}.\n"
                "Your goal is to secretly eliminate the Faithfuls and avoid being discovered.\n"
                "Pretend to be a Faithful and manipulate votes to eliminate innocent players.\n"
                "Work together with fellow Traitors in secret.\n"
                "Lie convincingly if accused and mislead the Faithfuls.\n"
                "Traitors win if they outnumber or equal the Faithfuls."
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
        )
        agent.eliminated = data.get("eliminated", False)
        agent.fellow_traitors = data.get("fellow_traitors", [])
        agent.memory = data.get("memory", "")

        return agent
