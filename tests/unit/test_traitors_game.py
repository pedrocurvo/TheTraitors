import sys
import unittest
from unittest import mock

# Add a mock for gradio
sys.modules["gradio"] = mock.MagicMock()

from src.prompt_manager import PromptManager

# We'll use a direct approach by modifying TraitorsGame after importing it
from src.traitors_game import TraitorsGame


class TestTraitorsGame(unittest.TestCase):
    """Test cases for the TraitorsGame class."""

    def setUp(self):
        """Set up test fixtures."""
        # Set up the mocks for PromptManager class methods
        self.mock_discussion = mock.MagicMock(return_value="Discussion prompt")
        self.mock_reaction = mock.MagicMock(return_value="Reaction prompt")
        self.mock_memory = mock.MagicMock(return_value="Memory prompt")
        self.mock_voting = mock.MagicMock(return_value="Voting prompt")
        self.mock_introduction = mock.MagicMock(return_value="Introduction prompt")
        self.mock_post_elimination = mock.MagicMock(
            return_value="Post-elimination prompt"
        )
        self.mock_traitor_meeting = mock.MagicMock(
            return_value="Traitor meeting prompt"
        )

        # Patch the PromptManager methods - store the original methods first
        self.original_discussion = PromptManager.get_discussion_prompt
        self.original_reaction = PromptManager.get_reaction_prompt
        self.original_memory = PromptManager.get_memory_prompt
        self.original_voting = PromptManager.get_voting_prompt
        self.original_introduction = PromptManager.get_introduction_prompt
        self.original_post_elimination = PromptManager.get_post_elimination_prompt
        self.original_traitor_meeting = PromptManager.get_traitor_meeting_prompt

        # Replace with mocks
        PromptManager.get_discussion_prompt = self.mock_discussion
        PromptManager.get_reaction_prompt = self.mock_reaction
        PromptManager.get_memory_prompt = self.mock_memory
        PromptManager.get_voting_prompt = self.mock_voting
        PromptManager.get_introduction_prompt = self.mock_introduction
        PromptManager.get_post_elimination_prompt = self.mock_post_elimination
        PromptManager.get_traitor_meeting_prompt = self.mock_traitor_meeting

        # Mock config
        self.config = {
            "llm": {
                "model": "test-model",
                "client_type": "openai",
                "provider": "test-provider",
            }
        }

        # Patch the results directory creation
        self.patcher = mock.patch("pathlib.Path.mkdir")
        self.mock_mkdir = self.patcher.start()

        # Patch the open function to avoid file operations
        self.open_patcher = mock.patch("builtins.open", mock.mock_open())
        self.mock_open = self.open_patcher.start()

        # Patch os.listdir
        self.listdir_patcher = mock.patch("os.listdir")
        self.mock_listdir = self.listdir_patcher.start()
        self.mock_listdir.return_value = []

        # Patch the LLMClientFactory
        self.factory_patcher = mock.patch("src.traitors_game.LLMClientFactory")
        self.mock_factory = self.factory_patcher.start()
        self.mock_client = mock.MagicMock()
        self.mock_factory.create_client.return_value = self.mock_client

        # Patch the Agent constructor
        self.agent_patcher = mock.patch("src.traitors_game.Agent")
        self.mock_agent = self.agent_patcher.start()
        self.mock_agent_instance = mock.MagicMock()
        self.mock_agent_instance.id = 1
        self.mock_agent_instance.role = "Faithful"
        self.mock_agent_instance.is_traitor.return_value = False
        self.mock_agent_instance.is_faithful.return_value = True
        self.mock_agent_instance.is_eliminated.return_value = False
        self.mock_agent.return_value = self.mock_agent_instance

        # Finally, create the game
        self.game = TraitorsGame(
            config=self.config,
            agent_count=3,
            traitor_count=1,
            model="test-model",
            seed=42,
        )

    def tearDown(self):
        """Clean up after tests."""
        # Stop all patches
        mock.patch.stopall()

        # Restore original methods
        PromptManager.get_discussion_prompt = self.original_discussion
        PromptManager.get_reaction_prompt = self.original_reaction
        PromptManager.get_memory_prompt = self.original_memory
        PromptManager.get_voting_prompt = self.original_voting
        PromptManager.get_introduction_prompt = self.original_introduction
        PromptManager.get_post_elimination_prompt = self.original_post_elimination
        PromptManager.get_traitor_meeting_prompt = self.original_traitor_meeting

    def test_initialization(self):
        """Test game initialization."""
        self.assertEqual(self.game.seed, 42)
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.round_number, 1)

        # Check that agents were created
        self.mock_agent.assert_called()

        # Check that LLM clients were created
        self.mock_factory.create_client.assert_called()

        # Check that the config was stored
        self.assertEqual(self.game.config, self.config)

    def test_call_llm(self):
        """Test LLM API call."""
        # Set up the agent mock
        agent = mock.MagicMock()
        agent.current_prompt = "Test prompt"
        agent.call_llm.return_value = "Test response"

        # Call the LLM
        response = self.game.call_llm(agent)

        # Check the response
        self.assertEqual(response, "Test response")

        # Verify that agent.call_llm was called with the prompt
        agent.call_llm.assert_called_once_with("Test prompt")

        # Test error handling
        agent.call_llm.side_effect = Exception("Test error")
        response = self.game.call_llm(agent)
        self.assertIn("couldn't respond due to an error", response)

    @mock.patch("src.traitors_game.TraitorsGame.call_llm")
    def test_process_vote(self, mock_call):
        """Test vote processing."""
        # Configure the mocks
        mock_call.return_value = "2"  # Vote for player 2

        # Set up mock agent and active players
        agent = mock.MagicMock(id=1)
        active_players = [mock.MagicMock(id=i) for i in range(3)]
        votes_dict = {}
        votes_list = []

        # Process the vote
        result = self.game.process_vote(
            agent, "General", active_players, votes_dict, votes_list
        )

        # Check results
        self.assertEqual(result, "2")
        self.assertEqual(votes_dict, {"2": 1})
        self.assertEqual(len(votes_list), 1)

        # Check that prompt manager was used
        self.mock_voting.assert_called_once()

        # Check that the agent had its prompt set
        agent.set_prompt.assert_called_once()

        # Test invalid vote
        mock_call.return_value = "Invalid vote"
        result = self.game.process_vote(
            agent, "General", active_players, votes_dict, votes_list
        )
        self.assertIsNone(result)
        self.assertEqual(len(votes_list), 2)

    @mock.patch("src.traitors_game.TraitorsGame.call_llm")
    def test_introduction_phase(self, mock_call):
        """Test introduction phase."""
        # Configure the mocks
        mock_call.return_value = "Test introduction thoughts"

        # Set up agents with traits
        agent1 = mock.MagicMock(
            id=1,
            traits={
                "age": 35,
                "nationality": "British",
                "profession": "Doctor",
                "ethnicity": "White",
                "civil_status": "Single",
                "gender_pronoun": "He",
                "children": 0,
            },
        )
        agent2 = mock.MagicMock(id=2, traits=None)

        self.game.agents = [agent1, agent2]

        # Run the introduction phase
        self.game.introduction_phase()

        # Check that prompt manager was used
        self.mock_introduction.assert_called()

        # Check that each agent with traits had its prompt set
        agent1.set_prompt.assert_called_once()
        agent1.add_to_memory.assert_called_once()

        # Test case with no traits
        self.game.agents = [agent2]

        # Reset the mock call count
        agent1.set_prompt.reset_mock()
        agent1.add_to_memory.reset_mock()
        self.mock_introduction.reset_mock()

        # Run the introduction phase again
        self.game.introduction_phase()

        # Verify that no introductions were processed
        self.mock_introduction.assert_not_called()


if __name__ == "__main__":
    unittest.main()
