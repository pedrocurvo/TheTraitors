import unittest
from unittest import mock

# Update the import to use the module from src
from src.traitors_game import TraitorsGame


@mock.patch("src.traitors_game.PromptManager")
class TestTraitorsGame(unittest.TestCase):
    """Test cases for the TraitorsGame class."""

    def setUp(self):
        """Set up test fixtures."""
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
        self.factory_patcher = mock.patch("traitors_game.LLMClientFactory")
        self.mock_factory = self.factory_patcher.start()
        self.mock_client = mock.MagicMock()
        self.mock_factory.create_client.return_value = self.mock_client

        # Patch the Agent constructor
        self.agent_patcher = mock.patch("traitors_game.Agent")
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
        self.patcher.stop()
        self.open_patcher.stop()
        self.listdir_patcher.stop()
        self.factory_patcher.stop()
        self.agent_patcher.stop()

    def test_initialization(self, mock_pm):
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

    def test_call_llm(self, mock_pm):
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

    @mock.patch("traitors_game.TraitorsGame.call_llm")
    def test_discussion_phase(self, mock_call, mock_pm):
        """Test discussion phase."""
        # Configure the mocks
        mock_call.return_value = "Test response"

        # Set up mock agents
        self.game.agents = [mock.MagicMock(id=i, eliminated=False) for i in range(3)]

        # Configure mock_pm - Fix by attaching methods to the PromptManager class mock
        mock_pm.get_discussion_prompt.return_value = "Discussion prompt"
        mock_pm.get_reaction_prompt.return_value = "Reaction prompt"
        mock_pm.get_memory_prompt.return_value = "Memory prompt"

        # Run the discussion phase
        self.game.discussion_phase()

        # Check that the prompt manager was used - fix assertion to check all calls
        self.assertGreater(mock_pm.get_discussion_prompt.call_count, 0)
        self.assertGreater(mock_pm.get_reaction_prompt.call_count, 0)
        self.assertGreater(mock_pm.get_memory_prompt.call_count, 0)

        # Verify that call_llm was called for each agent multiple times
        # (initial discussion, reaction, memory)
        self.assertEqual(mock_call.call_count, 9)  # 3 agents * 3 calls each

        # Check that each agent had its prompt set
        for agent in self.game.agents:
            agent.set_prompt.assert_called()
            agent.add_to_memory.assert_called_once()

    @mock.patch("traitors_game.TraitorsGame.call_llm")
    def test_process_vote(self, mock_call, mock_pm):
        """Test vote processing."""
        # Configure the mocks
        mock_call.return_value = "2"  # Vote for player 2

        # Set up mock agent and active players
        agent = mock.MagicMock(id=1)
        active_players = [mock.MagicMock(id=i) for i in range(3)]
        votes_dict = {}
        votes_list = []

        # Configure mock_pm
        mock_pm.get_voting_prompt.return_value = "Voting prompt"

        # Process the vote
        result = self.game.process_vote(
            agent, "General", active_players, votes_dict, votes_list
        )

        # Check results
        self.assertEqual(result, "2")
        self.assertEqual(votes_dict, {"2": 1})
        self.assertEqual(len(votes_list), 1)

        # Check that prompt manager was used
        mock_pm.get_voting_prompt.assert_called_once()

        # Check that the agent had its prompt set
        agent.set_prompt.assert_called_once()

        # Test invalid vote
        mock_call.return_value = "Invalid vote"
        result = self.game.process_vote(
            agent, "General", active_players, votes_dict, votes_list
        )
        self.assertIsNone(result)
        self.assertEqual(len(votes_list), 2)

    @mock.patch("traitors_game.TraitorsGame.call_llm")
    def test_introduction_phase(self, mock_call, mock_pm):
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

        # Configure mock_pm
        mock_pm.get_introduction_prompt.return_value = "Introduction prompt"

        # Run the introduction phase
        self.game.introduction_phase()

        # Check that prompt manager was used
        mock_pm.get_introduction_prompt.assert_called()

        # Check that each agent with traits had its prompt set
        agent1.set_prompt.assert_called_once()
        agent1.add_to_memory.assert_called_once()

        # Test case with no traits
        self.game.agents = [agent2]

        # Reset the mock call count
        agent1.set_prompt.reset_mock()
        agent1.add_to_memory.reset_mock()
        mock_pm.get_introduction_prompt.reset_mock()

        # Run the introduction phase again
        self.game.introduction_phase()

        # Verify that no introductions were processed
        mock_pm.get_introduction_prompt.assert_not_called()

    @mock.patch("traitors_game.TraitorsGame.call_llm")
    def test_post_elimination_discussion(self, mock_call, mock_pm):
        """Test post-elimination discussion."""
        # Configure the mocks
        mock_call.return_value = "Test elimination thoughts"

        # Set up agents
        agent1 = mock.MagicMock(id=1, eliminated=False, role="Faithful")
        agent2 = mock.MagicMock(id=2, eliminated=False, role="Traitor")
        agent3 = mock.MagicMock(id=3, eliminated=True, role="Faithful")

        self.game.agents = [agent1, agent2, agent3]

        # Configure mock_pm
        mock_pm.get_post_elimination_prompt.return_value = "Post-elimination prompt"

        # Run the post-elimination discussion
        self.game.post_elimination_discussion("3")

        # Check that prompt manager was used - fix the assertion
        self.assertGreater(mock_pm.get_post_elimination_prompt.call_count, 0)

        # Check that active agents had their prompts set
        agent1.set_prompt.assert_called()
        agent2.set_prompt.assert_called()
        agent3.set_prompt.assert_not_called()  # Eliminated agent


if __name__ == "__main__":
    unittest.main()
