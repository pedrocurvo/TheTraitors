import unittest
from unittest import mock
import os
import tempfile
from pathlib import Path

from agent import Agent


class TestAgent(unittest.TestCase):
    """Test cases for the Agent class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.llm_client = mock.MagicMock()
        self.llm_client.call.return_value = "Test response"
        
        # Create a test agent
        self.agent = Agent(
            agent_id=1,
            role="Faithful",
            model="test-model",
            results_dir=self.temp_dir,
            llm_client=self.llm_client
        )
        
        # Create a test traitor agent
        self.traitor = Agent(
            agent_id=2,
            role="Traitor",
            model="test-model",
            results_dir=self.temp_dir,
            llm_client=self.llm_client
        )
        self.traitor.set_fellow_traitors([3, 4])

    def tearDown(self):
        """Clean up after tests."""
        # Remove temp directory
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.id, 1)
        self.assertEqual(self.agent.role, "Faithful")
        self.assertEqual(self.agent.model, "test-model")
        self.assertEqual(self.agent.memory, "")
        self.assertEqual(self.agent.current_prompt, "")
        self.assertFalse(self.agent.eliminated)
        self.assertEqual(self.agent.fellow_traitors, [])
        self.assertEqual(self.agent.llm_client, self.llm_client)
        
        # Check that the agent directory was created
        agent_dir = Path(f"{self.temp_dir}/agent-1")
        self.assertTrue(agent_dir.exists())
        self.assertTrue(agent_dir.is_dir())

    def test_role_methods(self):
        """Test role-related methods."""
        # Test faithful agent
        self.assertTrue(self.agent.is_faithful())
        self.assertFalse(self.agent.is_traitor())
        
        # Test traitor agent
        self.assertTrue(self.traitor.is_traitor())
        self.assertFalse(self.traitor.is_faithful())

    def test_elimination(self):
        """Test elimination functionality."""
        self.assertFalse(self.agent.is_eliminated())
        self.assertTrue(self.agent.is_active())
        
        # Eliminate the agent
        self.agent.eliminate()
        
        self.assertTrue(self.agent.is_eliminated())
        self.assertFalse(self.agent.is_active())

    def test_memory_management(self):
        """Test memory management."""
        # Add to memory without section
        self.agent.add_to_memory("Test memory")
        self.assertIn("Test memory", self.agent.memory)
        
        # Add to memory with section
        self.agent.add_to_memory("Section memory", "TEST SECTION")
        self.assertIn("--- TEST SECTION ---", self.agent.memory)
        self.assertIn("Section memory", self.agent.memory)

    def test_prompt_setting(self):
        """Test setting the prompt."""
        test_prompt = "This is a test prompt"
        self.agent.set_prompt(test_prompt)
        self.assertEqual(self.agent.current_prompt, test_prompt)

    def test_get_role_prompt(self):
        """Test role-specific prompts."""
        # Test faithful prompt
        faithful_prompt = self.agent.get_role_prompt()
        self.assertIn("You are a Faithful in The Traitors game", faithful_prompt)
        self.assertIn("find and eliminate all Traitors", faithful_prompt)
        
        # Test traitor prompt
        traitor_prompt = self.traitor.get_role_prompt()
        self.assertIn("You are a Traitor in The Traitors game", traitor_prompt)
        self.assertIn("fellow Traitors are agents: 3, 4", traitor_prompt)

    def test_extract_dialogue(self):
        """Test dialogue extraction."""
        # Test with valid markers
        response = "Thinking...\n---\nThis is the dialogue\n---\nMore thinking..."
        dialogue = self.agent.extract_dialogue(response)
        self.assertEqual(dialogue, "This is the dialogue")
        
        # Test without markers
        response = "This is a response without markers"
        dialogue = self.agent.extract_dialogue(response)
        self.assertEqual(dialogue, response)

    @mock.patch('agent.Agent.log_inner_thoughts')
    def test_call_llm(self, mock_log):
        """Test LLM calling."""
        # Set up the mock
        self.llm_client.call.return_value = "Thinking...\n---\nHello world\n---\nMore thinking..."
        
        # Call the LLM
        response = self.agent.call_llm("Test prompt")
        
        # Check that the client was called with the right arguments
        self.llm_client.call.assert_called_once()
        system_message = self.llm_client.call.call_args[0][0]
        user_message = self.llm_client.call.call_args[0][1]
        
        self.assertIn(f"You are Player {self.agent.id}", system_message)
        self.assertEqual(user_message, "Test prompt")
        
        # Check that the response was processed correctly
        self.assertEqual(response, "Hello world")
        
        # Check that log_inner_thoughts was called
        mock_log.assert_called_once_with("Thinking...\n---\nHello world\n---\nMore thinking...")

    def test_to_dict(self):
        """Test conversion to dictionary."""
        agent_dict = self.agent.to_dict()
        
        self.assertEqual(agent_dict["id"], 1)
        self.assertEqual(agent_dict["role"], "Faithful")
        self.assertEqual(agent_dict["model"], "test-model")
        self.assertFalse(agent_dict["eliminated"])
        self.assertEqual(agent_dict["fellow_traitors"], [])

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "id": 5,
            "role": "Traitor",
            "model": "test-model",
            "eliminated": True,
            "fellow_traitors": [6, 7],
            "memory": "Test memory"
        }
        
        agent = Agent.from_dict(data, self.temp_dir, self.llm_client)
        
        self.assertEqual(agent.id, 5)
        self.assertEqual(agent.role, "Traitor")
        self.assertEqual(agent.model, "test-model")
        self.assertTrue(agent.eliminated)
        self.assertEqual(agent.fellow_traitors, [6, 7])
        self.assertEqual(agent.memory, "Test memory")
        self.assertEqual(agent.llm_client, self.llm_client)


if __name__ == '__main__':
    unittest.main() 