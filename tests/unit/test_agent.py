import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Update the import to use the module from src
from src.agent import Agent


@mock.patch("src.agent.PromptManager")
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
            llm_client=self.llm_client,
        )

        # Create a test traitor agent
        self.traitor = Agent(
            agent_id=2,
            role="Traitor",
            model="test-model",
            results_dir=self.temp_dir,
            llm_client=self.llm_client,
        )
        self.traitor.set_fellow_traitors([3, 4])

        # Create a test agent with traits
        self.agent_with_traits = Agent(
            agent_id=3,
            role="Faithful",
            model="test-model",
            results_dir=self.temp_dir,
            llm_client=self.llm_client,
            traits={
                "age": 45,
                "nationality": "American",
                "profession": "Lawyer",
                "gender_pronoun": "He",
            },
        )

    def tearDown(self):
        """Clean up after tests."""
        # Remove temp directory
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_initialization(self, mock_pm):
        """Test agent initialization."""
        self.assertEqual(self.agent.id, 1)
        self.assertEqual(self.agent.role, "Faithful")
        self.assertEqual(self.agent.model, "test-model")
        self.assertEqual(self.agent.current_prompt, "")
        self.assertFalse(self.agent.eliminated)
        self.assertEqual(self.agent.fellow_traitors, [])
        self.assertEqual(self.agent.llm_client, self.llm_client)

        # Check that the agent directory was created
        agent_dir = Path(f"{self.temp_dir}/agent-1")
        self.assertTrue(agent_dir.exists())
        self.assertTrue(agent_dir.is_dir())

        # Check that the structured memory is initialized
        self.assertIsInstance(self.agent.memory, dict)
        self.assertIn("player_info", self.agent.memory)
        self.assertIn("game_events", self.agent.memory)
        self.assertIn("suspicions", self.agent.memory)
        self.assertIn("strategies", self.agent.memory)
        self.assertIn("round_summaries", self.agent.memory)

    def test_role_methods(self, mock_pm):
        """Test role-related methods."""
        # Test faithful agent
        self.assertTrue(self.agent.is_faithful())
        self.assertFalse(self.agent.is_traitor())

        # Test traitor agent
        self.assertTrue(self.traitor.is_traitor())
        self.assertFalse(self.traitor.is_faithful())

    def test_elimination(self, mock_pm):
        """Test elimination functionality."""
        self.assertFalse(self.agent.is_eliminated())
        self.assertTrue(self.agent.is_active())

        # Eliminate the agent
        self.agent.eliminate()

        self.assertTrue(self.agent.is_eliminated())
        self.assertFalse(self.agent.is_active())

    def test_memory_management(self, mock_pm):
        """Test structured memory management."""
        # Add to memory with section - round memory
        self.agent.add_to_memory("Player 4 seems suspicious", "ROUND 1 MEMORY")

        # Check that it was categorized correctly
        self.assertIn("summary", self.agent.memory["round_summaries"][1])

        # Add a suspicion
        self.agent.add_to_memory(
            "I suspect Player 5 might be a traitor", "ROUND 2 MEMORY"
        )

        # Check it was added to suspicions
        self.assertIn("5", self.agent.memory["suspicions"])

        # Add player information
        self.agent.add_to_memory(
            "Player 3 is very logical. Player 4 is emotional.",
            "THOUGHTS ON PLAYERS BACKGROUNDS",
        )

        # Check player info was extracted
        self.assertIn("3", self.agent.memory["player_info"])
        self.assertIn("4", self.agent.memory["player_info"])

        # Test elimination event
        self.agent.add_to_memory("Player 5 was eliminated", "ELIMINATION EVENT")

        # Check it was added to game events
        self.assertEqual(1, len(self.agent.memory["game_events"]))
        self.assertEqual("elimination", self.agent.memory["game_events"][0]["type"])

        # Test memory retrieval
        player_info = self.agent.get_player_info("3")
        self.assertTrue(len(player_info) > 0)
        self.assertIn("logical", player_info[0])

        suspicions = self.agent.get_suspicions("5")
        self.assertTrue(len(suspicions) > 0)
        self.assertIn("suspect", suspicions[0]["content"].lower())

        # Test get_round_summary
        round_summary = self.agent.get_round_summary(1)
        self.assertIn("summary", round_summary)

        # Test get_memory_by_category
        strategies = self.agent.get_memory_by_category("strategies")
        self.assertEqual(strategies, [])  # Empty since we didn't add any

    def test_prompt_setting(self, mock_pm):
        """Test setting the prompt."""
        test_prompt = "This is a test prompt"
        self.agent.set_prompt(test_prompt)
        self.assertEqual(self.agent.current_prompt, test_prompt)

    def test_get_formatted_memory(self, mock_pm):
        """Test formatted memory output."""
        # Add some test data to memory
        self.agent.memory["player_info"] = {"2": ["is suspicious", "talks a lot"]}
        self.agent.memory["suspicions"] = {
            "3": [{"content": "I think Player 3 is a traitor", "round": 1}]
        }
        self.agent.memory["game_events"] = [
            {"type": "elimination", "details": "Player 4 was eliminated", "round": 2}
        ]
        self.agent.memory["strategies"] = [
            {"content": "I should build trust with Player 2", "round": 1}
        ]
        self.agent.memory["personal_notes"] = ["Important observation"]

        formatted = self.agent.get_formatted_memory()

        # Check that sections are properly formatted
        self.assertIn("--- PLAYER INFORMATION ---", formatted)
        self.assertIn("Player 2: is suspicious talks a lot", formatted)
        self.assertIn("--- SUSPICIONS ---", formatted)
        self.assertIn("Suspicions about Player 3:", formatted)
        self.assertIn("--- GAME EVENTS ---", formatted)
        self.assertIn("Round 2: Player 4 was eliminated", formatted)
        self.assertIn("--- MY STRATEGIES ---", formatted)
        self.assertIn("I should build trust with Player 2", formatted)
        self.assertIn("--- PERSONAL NOTES ---", formatted)
        self.assertIn("Important observation", formatted)

    @mock.patch("src.agent.Agent.log_inner_thoughts")
    def test_call_llm(self, mock_log, mock_pm):
        """Test LLM calling with structured prompts."""
        # Mock the get_system_prompt method
        mock_pm.get_system_prompt.return_value = "You are Player 1"

        # Mock the LLM client call
        self.llm_client.call.return_value = (
            "Thinking...\n---\nHello everyone\n---\nMore thoughts..."
        )

        # Call the LLM
        response = self.agent.call_llm("What would you say?")

        # Check that PromptManager was called correctly
        mock_pm.get_system_prompt.assert_called_once()

        # Check that the LLM client was called with the right parameters
        self.llm_client.call.assert_called_once()
        system_prompt_arg = self.llm_client.call.call_args[0][0]
        user_prompt_arg = self.llm_client.call.call_args[0][1]
        self.assertEqual(system_prompt_arg, "You are Player 1")
        self.assertEqual(user_prompt_arg, "What would you say?")

        # Check that log_inner_thoughts was called
        mock_log.assert_called_once()

        # Check that the response was extracted correctly
        self.assertEqual(response, "Hello everyone")

    def test_extract_dialogue(self, mock_pm):
        """Test dialogue extraction."""
        # Test with valid markers
        response = "Thinking...\n---\nThis is the dialogue\n---\nMore thinking..."
        dialogue = self.agent.extract_dialogue(response)
        self.assertEqual(dialogue, "This is the dialogue")

        # Test without markers
        response = "This is a response without markers"
        dialogue = self.agent.extract_dialogue(response)
        self.assertEqual(dialogue, response)

    def test_to_dict(self, mock_pm):
        """Test conversion to dictionary."""
        # Add some test data
        self.agent.memory["player_info"] = {"2": ["is suspicious"]}

        data = self.agent.to_dict()

        self.assertEqual(data["id"], 1)
        self.assertEqual(data["role"], "Faithful")
        self.assertEqual(data["model"], "test-model")
        self.assertFalse(data["eliminated"])
        self.assertEqual(data["memory"]["player_info"], {"2": ["is suspicious"]})

    def test_from_dict(self, mock_pm):
        """Test creation from dictionary."""
        data = {
            "id": 5,
            "role": "Traitor",
            "model": "test-model",
            "eliminated": True,
            "fellow_traitors": [6, 7],
            "memory": {
                "player_info": {"2": ["is suspicious"]},
                "game_events": [
                    {
                        "type": "elimination",
                        "details": "Player 4 was eliminated",
                        "round": 2,
                    }
                ],
                "suspicions": {},
                "strategies": [],
                "round_summaries": {},
                "alliances": [],
                "personal_notes": [],
            },
        }

        agent = Agent.from_dict(data, self.temp_dir, self.llm_client)

        self.assertEqual(agent.id, 5)
        self.assertEqual(agent.role, "Traitor")
        self.assertEqual(agent.model, "test-model")
        self.assertTrue(agent.eliminated)
        self.assertEqual(agent.fellow_traitors, [6, 7])
        self.assertEqual(agent.memory["player_info"], {"2": ["is suspicious"]})
        self.assertEqual(agent.llm_client, self.llm_client)

        # Test with old string-based memory format
        data = {
            "id": 6,
            "role": "Faithful",
            "model": "test-model",
            "memory": "Old memory format",
        }

        agent = Agent.from_dict(data, self.temp_dir)

        self.assertEqual(agent.id, 6)
        self.assertEqual(agent.memory["personal_notes"], ["Old memory format"])


if __name__ == "__main__":
    unittest.main()
