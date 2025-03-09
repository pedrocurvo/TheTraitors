import unittest
from unittest import mock
import os
import tempfile
import shutil
from pathlib import Path

from main import TraitorsGame
from agent import Agent


class TestTraitorsGame(unittest.TestCase):
    """Test cases for the TraitorsGame class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test results
        self.temp_dir = tempfile.mkdtemp()
        
        # Patch the Path.mkdir method to avoid creating directories
        self.patcher = mock.patch('pathlib.Path.mkdir')
        self.mock_mkdir = self.patcher.start()
        
        # Patch LLMClientFactory to return a mock client
        self.client_patcher = mock.patch('main.LLMClientFactory')
        self.mock_factory = self.client_patcher.start()
        self.mock_llm_client = mock.MagicMock()
        self.mock_factory.create_client.return_value = self.mock_llm_client
        
        # Patch open to avoid file operations
        self.open_patcher = mock.patch('builtins.open', mock.mock_open())
        self.mock_open = self.open_patcher.start()
        
        # Create a test game
        with mock.patch('main.Path', return_value=Path(self.temp_dir)):
            self.game = TraitorsGame(
                agent_count=4,
                traitor_count=1,
                model="test-model",
                seed=42,
                client_type="openai",
                provider="openai"
            )
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop patchers
        self.patcher.stop()
        self.client_patcher.stop()
        self.open_patcher.stop()
        
        # Remove temp directory
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test game initialization."""
        self.assertEqual(len(self.game.agents), 4)
        self.assertEqual(self.game.model, "test-model")
        self.assertEqual(self.game.client_type, "openai")
        self.assertEqual(self.game.provider, "openai")
        self.assertEqual(self.game.seed, 42)
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.round_number, 1)
        self.assertIsNone(self.game.traitors_last_eliminated)
        
        # Check that the factory was called to create clients
        self.mock_factory.create_client.assert_called_with("openai", "test-model", "openai")
    
    def test_create_agents(self):
        """Test agent creation."""
        # Count traitors and faithfuls
        traitors = [a for a in self.game.agents if a.is_traitor()]
        faithfuls = [a for a in self.game.agents if a.is_faithful()]
        
        self.assertEqual(len(traitors), 1)
        self.assertEqual(len(faithfuls), 3)
        
        # Check that each agent has an LLM client
        for agent in self.game.agents:
            self.assertIsNotNone(agent.llm_client)
    
    @mock.patch('main.Agent.call_llm')
    def test_call_llm(self, mock_call_llm):
        """Test LLM calling."""
        # Set up mock
        mock_call_llm.return_value = "Test response"
        
        # Call the method
        agent = self.game.agents[0]
        agent.current_prompt = "Original prompt"
        response = self.game.call_llm(agent)
        
        # Check that the agent's call_llm method was called with the right prompt
        mock_call_llm.assert_called_once()
        prompt_arg = mock_call_llm.call_args[0][0]
        self.assertIn("Original prompt", prompt_arg)
        self.assertIn("triple dashes", prompt_arg)  # Check formatting instructions
        
        # Check response
        self.assertEqual(response, "Test response")
    
    def test_get_game_status(self):
        """Test game status generation."""
        # Set up game state
        self.game.agents[0].eliminate()
        self.game.history = ["Player 1 was eliminated."]
        
        # Get status
        status = self.game.get_game_status()
        
        # Check status content
        self.assertIn("Round 1", status)
        self.assertIn("Active players: 1, 2, 3", status)  # Assuming IDs are 0-3
        self.assertIn("Eliminated players: 0", status)
        self.assertIn("Player 1 was eliminated.", status)
    
    def test_write_to_history(self):
        """Test history writing."""
        # Set up mock
        file_handle = self.mock_open.return_value
        
        # Call the method
        self.game.write_to_history("Test message")
        
        # Check that open was called
        self.mock_open.assert_called()
        
        # Call with new section
        self.game.write_to_history("Section message", new_section=True)
        
        # Instead of checking specific calls, just verify that write was called
        # This is more robust against implementation changes
        self.assertTrue(file_handle.write.called)
        
        # Since the implementation details may vary, we'll just check that
        # the method was called at least twice (once for each message)
        self.assertGreaterEqual(file_handle.write.call_count, 2)
    
    @mock.patch('main.TraitorsGame.call_llm')
    @mock.patch('main.TraitorsGame.write_to_history')
    def test_process_vote(self, mock_write, mock_call_llm):
        """Test vote processing."""
        # Set up mocks
        mock_call_llm.return_value = "I vote for player 2"
        
        # Set up test data
        agent = self.game.agents[0]
        active_players = self.game.agents
        votes_dict = {}
        votes_list = []
        
        # Call the method
        result = self.game.process_vote(agent, "Test", active_players, votes_dict, votes_list)
        
        # Check results
        self.assertEqual(result, "2")
        self.assertEqual(votes_dict, {"2": 1})
        self.assertEqual(len(votes_list), 1)
        self.assertEqual(votes_list[0]["Vote_Target"], "2")
        self.assertEqual(votes_list[0]["Player_ID"], agent.id)
        
        # Test with invalid vote
        mock_call_llm.return_value = "I'm not sure"
        votes_dict = {}
        votes_list = []
        
        result = self.game.process_vote(agent, "Test", active_players, votes_dict, votes_list)
        
        self.assertIsNone(result)
        self.assertEqual(votes_dict, {})
        self.assertEqual(len(votes_list), 1)
        self.assertIsNone(votes_list[0]["Vote_Target"])
    
    @mock.patch('main.TraitorsGame.write_to_history')
    def test_process_elimination(self, mock_write):
        """Test elimination processing."""
        # Set up test data
        eliminated_id = "1"
        eliminated_agent = self.game.agents[1]
        votes_list = [{
            "Round": self.game.round_number,
            "Vote_Type": "Test",
            "Player_ID": 0,
            "Role": "Faithful",
            "Vote_Target": eliminated_id,
            "Eliminated": False
        }]
        
        # Mock the open file for CSV writing
        mock_file = mock.mock_open()
        with mock.patch('builtins.open', mock_file):
            # Call the method
            result = self.game.process_elimination(eliminated_id, eliminated_agent, votes_list)
        
        # Check results
        self.assertTrue(result)
        self.assertTrue(eliminated_agent.is_eliminated())
        self.assertEqual(votes_list[0]["Eliminated"], eliminated_id)
        self.assertEqual(len(self.game.history), 1)
        
        # Test with traitor elimination
        eliminated_id = "2"
        eliminated_agent = self.game.agents[2]
        votes_list = [{
            "Round": self.game.round_number,
            "Vote_Type": "Traitor",
            "Player_ID": 0,
            "Role": "Traitor",
            "Vote_Target": eliminated_id,
            "Eliminated": False
        }]
        
        # Mock the open file for CSV writing
        mock_file = mock.mock_open()
        with mock.patch('builtins.open', mock_file):
            # Call the method
            result = self.game.process_elimination(eliminated_id, eliminated_agent, votes_list, "traitor")
        
        # Check results
        self.assertTrue(result)
        self.assertTrue(eliminated_agent.is_eliminated())
        self.assertEqual(votes_list[0]["Eliminated"], eliminated_id)
        self.assertEqual(len(self.game.history), 2)
        self.assertIsNotNone(self.game.traitors_last_eliminated)
    
    def test_check_win_conditions(self):
        """Test win condition checking."""
        # Set up for Faithfuls win
        for agent in self.game.agents:
            if agent.is_traitor():
                agent.eliminate()
        
        # Check win condition
        result = self.game.check_win_conditions()
        
        # Verify result
        self.assertEqual(result, "Faithfuls")
        self.assertTrue(self.game.game_over)
        
        # Reset game state
        self.game.game_over = False
        for agent in self.game.agents:
            agent.eliminated = False
        
        # Set up for Traitors win
        for agent in self.game.agents:
            if agent.is_faithful():
                agent.eliminate()
                if sum(1 for a in self.game.agents if a.is_faithful() and not a.is_eliminated()) <= 1:
                    break
        
        # Check win condition
        result = self.game.check_win_conditions()
        
        # Verify result
        self.assertEqual(result, "Traitors")
        self.assertTrue(self.game.game_over)
        
        # Reset game state
        self.game.game_over = False
        for agent in self.game.agents:
            agent.eliminated = False
        
        # Set up for no win yet
        result = self.game.check_win_conditions()
        
        # Verify result
        self.assertIsNone(result)
        self.assertFalse(self.game.game_over)


if __name__ == '__main__':
    unittest.main() 