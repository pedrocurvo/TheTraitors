import unittest

# Update the import to use the module from src
from src.prompt_manager import PromptManager


class MockAgent:
    """Mock Agent class for testing purposes."""

    def __init__(self, agent_id, role, traits=None, fellow_traitors=None):
        self.id = agent_id
        self.role = role
        self.traits = traits or {}
        self.fellow_traitors = fellow_traitors or []

    def is_traitor(self):
        return self.role == "Traitor"

    def is_faithful(self):
        return self.role == "Faithful"


class TestPromptManager(unittest.TestCase):
    """Test cases for the PromptManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock agents for testing
        self.faithful_agent = MockAgent(1, "Faithful")
        self.traitor_agent = MockAgent(2, "Traitor", fellow_traitors=[3, 4])
        self.agent_with_traits = MockAgent(
            3,
            "Faithful",
            traits={
                "age": 45,
                "nationality": "American",
                "profession": "Lawyer",
                "ethnicity": "Latino",
                "civil_status": "Married",
                "gender_pronoun": "He",
                "children": 2,
            },
        )

    def test_system_prompt_faithful(self):
        """Test system prompt generation for Faithful agents."""
        system_prompt = PromptManager.get_system_prompt(self.faithful_agent)

        # Check that it contains key faithful-specific phrases
        self.assertIn("playing as a Faithful player", system_prompt)
        self.assertIn("identify and eliminate all Traitors", system_prompt)
        self.assertIn("YOUR IDENTITY: You are Player 1", system_prompt)

        # Should NOT contain traitor-specific information
        self.assertNotIn("YOUR FELLOW TRAITORS", system_prompt)

    def test_system_prompt_traitor(self):
        """Test system prompt generation for Traitor agents."""
        system_prompt = PromptManager.get_system_prompt(self.traitor_agent)

        # Check that it contains key traitor-specific phrases
        self.assertIn("playing as a Traitor player", system_prompt)
        self.assertIn(
            "eliminate Faithfuls", system_prompt
        )  # Changed from "maintain your cover"
        self.assertIn("YOUR FELLOW TRAITORS: Players 3, 4", system_prompt)

    def test_system_prompt_with_traits(self):
        """Test system prompt generation with traits."""
        system_prompt = PromptManager.get_system_prompt(self.agent_with_traits)

        # Check that traits are included
        self.assertIn("45-year-old American Lawyer", system_prompt)
        self.assertIn("You are Latino", system_prompt)
        self.assertIn("You are Married", system_prompt)
        self.assertIn("You have 2 children", system_prompt)
        self.assertIn("male perspective", system_prompt)

    def test_format_traits(self):
        """Test formatting of traits."""
        traits = {
            "age": 30,
            "nationality": "British",
            "profession": "Doctor",
            "gender_pronoun": "she",
        }

        formatted = PromptManager._format_traits(traits)
        self.assertIn("30-year-old British Doctor", formatted)
        self.assertIn("female perspective", formatted)

        # Test with empty traits
        self.assertEqual("", PromptManager._format_traits({}))

    def test_discussion_prompt(self):
        """Test discussion prompt generation."""
        prompt = PromptManager.get_discussion_prompt(
            "Round 1: Active players: 1, 2, 3.",
            1,
            self.faithful_agent,
            "Who do you suspect?",
            discussions=None,
            is_first_speaker=True,
        )

        # Check content
        self.assertIn("Round 1: Active players: 1, 2, 3.", prompt)
        self.assertIn("first round of discussions", prompt)
        self.assertIn("Who do you suspect?", prompt)
        self.assertIn("first to speak", prompt)

        # Test without first speaker flag
        prompt2 = PromptManager.get_discussion_prompt(
            "Round 2: Active players: 1, 2, 3.",
            2,
            self.traitor_agent,
            "What patterns have you noticed?",
            discussions="Previous discussion content",
            is_first_speaker=False,
        )

        self.assertIn("Round 2: Active players: 1, 2, 3.", prompt2)
        self.assertIn("Round 2 of discussions", prompt2)
        self.assertIn("blend in while subtly casting", prompt2)
        self.assertIn("Previous discussion content", prompt2)
        self.assertNotIn("first to speak", prompt2)

    def test_voting_prompt(self):
        """Test voting prompt generation."""
        # Test for faithful
        faithful_prompt = PromptManager.get_voting_prompt(
            1, self.faithful_agent, ["1", "2", "3", "4"]
        )

        self.assertIn("time to vote for elimination in Round 1", faithful_prompt)
        self.assertIn("As a Faithful", faithful_prompt)
        self.assertIn("The active players are: 1, 2, 3, 4", faithful_prompt)

        # Test for traitor with active fellow traitors
        traitor_prompt = PromptManager.get_voting_prompt(
            2, self.traitor_agent, ["1", "2", "3", "4"]
        )

        self.assertIn("time to vote for elimination in Round 2", traitor_prompt)
        self.assertIn("As a Traitor", traitor_prompt)
        self.assertIn("Remember your fellow Traitors (Players 3, 4)", traitor_prompt)

    def test_traitor_meeting_prompt(self):
        """Test traitor meeting prompt generation."""
        # Test first speaker
        first_prompt = PromptManager.get_traitor_meeting_prompt(
            2, ["2", "3", "4"], ["1", "5", "6"], 1, is_first_speaker=True
        )

        self.assertIn("SECRET TRAITOR MEETING", first_prompt)
        self.assertIn("fellow traitors: 2, 3, 4", first_prompt)
        self.assertIn("Faithfuls still in the game are: 1, 5, 6", first_prompt)
        self.assertIn("first to speak in this secret meeting", first_prompt)

        # Test with existing discussion
        second_prompt = PromptManager.get_traitor_meeting_prompt(
            3,
            ["2", "3", "4"],
            ["1", "5", "6"],
            2,
            is_first_speaker=False,
            discussion="Previous traitor discussion",
        )

        self.assertIn("Consider what your fellow traitors have said", second_prompt)
        self.assertIn("Previous traitor discussion", second_prompt)

    def test_other_prompts(self):
        """Test other prompt generation methods."""
        # Test reaction prompt
        reaction = PromptManager.get_reaction_prompt(
            "What's your response?", "Previous discussion"
        )
        self.assertIn("What's your response?", reaction)
        self.assertIn("Discussion so far: Previous discussion", reaction)

        # Test memory prompt
        memory = PromptManager.get_memory_prompt(
            "Summarize key points", "Full discussion"
        )
        self.assertIn("Summarize key points", memory)
        self.assertIn("Focus on information that will help your strategy", memory)
        self.assertIn("Full discussion", memory)

        # Test post-elimination prompt
        post_elim = PromptManager.get_post_elimination_prompt("3", "Traitor")
        self.assertIn("Player 3 was eliminated and was a Traitor", post_elim)
        self.assertIn("Has this changed your suspicions?", post_elim)

        # Test introduction prompt
        intro = PromptManager.get_introduction_prompt(
            "Player 1 is a doctor. Player 2 is a lawyer."
        )
        self.assertIn("introductions of all players", intro)
        self.assertIn("Player 1 is a doctor. Player 2 is a lawyer.", intro)
        self.assertIn("what do you find most interesting", intro)


if __name__ == "__main__":
    unittest.main()
