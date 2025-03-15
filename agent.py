from pathlib import Path
import os
import re
from typing import Optional


class Agent:
    """Represents a player in the Traitors Game."""

    def __init__(self, agent_id, role, model, results_dir, llm_client=None, traits=None):
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
        self.memory = ""
        self.current_prompt = ""
        self.eliminated = False
        self.fellow_traitors = []
        self.llm_client = llm_client
        self.traits = traits or {}  # Store traits as an empty dict if None

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
        # Add personality traits to the prompt if available
        traits_prompt = ""
        if self.traits:
            profession = self.traits.get('profession', '')
            nationality = self.traits.get('nationality', '')
            age = self.traits.get('age', '')
            gender = self.traits.get('gender_pronoun', 'they')
            
            if profession and nationality and age:
                traits_prompt = f"As a {age}-year-old {nationality} {profession}, use your background to inform your strategy and interactions. "
                if gender == "he":
                    traits_prompt += "Speak with a voice that reflects your character's personality and life experiences. "
                elif gender == "she":
                    traits_prompt += "Express yourself in a way that reflects your character's unique perspective and background. "
                else:
                    traits_prompt += "Let your character's unique qualities shine through in your interactions. "
        
        if self.is_faithful():
            return (
                f"You are Player {self.id}, a Faithful in The Traitors game.\n"
                f"{traits_prompt}"
                "Your primary objective is to identify and eliminate all Traitors through careful observation and deduction.\n"
                "STRATEGY GUIDELINES:\n"
                "- Pay close attention to inconsistencies in other players' statements\n"
                "- Form alliances cautiously, as you don't know who to trust\n"
                "- Be strategic in your accusations - baseless accusations may damage your credibility\n"
                "- Defend yourself effectively when accused by using logical arguments\n"
                "- Remember that Traitors are trying to blend in and appear trustworthy\n\n"
                "WINNING CONDITION: All Traitors must be eliminated for Faithfuls to win."
            )
        else:
            fellow_traitors_str = ", ".join(map(str, self.fellow_traitors))
            return (
                f"You are Player {self.id}, a Traitor in The Traitors game.\n"
                f"{traits_prompt}"
                f"Your fellow Traitors are Players: {fellow_traitors_str}.\n"
                "Your mission is to eliminate Faithfuls while maintaining your cover.\n"
                "STRATEGY GUIDELINES:\n"
                "- Blend in by mimicking Faithful behavior and concerns\n"
                "- Subtly cast suspicion on Faithful players without being too obvious\n"
                "- Defend fellow Traitors discreetly without revealing your alliance\n"
                "- Create plausible theories that misdirect suspicion away from yourself\n"
                "- Adapt your strategy based on who is being suspected\n\n"
                "WINNING CONDITION: Traitors win when they equal or outnumber the Faithfuls."
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
        agent.memory = data.get("memory", "")

        return agent
