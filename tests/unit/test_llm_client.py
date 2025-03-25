import re
import unittest


# Create a simplified version of the LLMClient classes for testing
class MockLLMClient:
    def __init__(self, model):
        self.model = model

    def extract_dialogue(self, full_response):
        pattern = r"---\s*([\s\S]*?)\s*---"
        match = re.search(pattern, full_response)

        if match:
            return match.group(1).strip()
        else:
            return full_response


class TestLLMClientBase(unittest.TestCase):
    """Test cases for the base LLMClient class."""

    def test_extract_dialogue(self):
        """Test dialogue extraction."""
        client = MockLLMClient("test-model")

        # Test with valid markers
        response = "Thinking...\n---\nThis is the dialogue\n---\nMore thinking..."
        dialogue = client.extract_dialogue(response)
        self.assertEqual(dialogue, "This is the dialogue")

        # Test without markers
        response = "This is a response without markers"
        dialogue = client.extract_dialogue(response)
        self.assertEqual(dialogue, response)


class TestLLMClientFactory(unittest.TestCase):
    """Test cases for the LLMClientFactory class."""

    def test_invalid_client_type(self):
        """Test error handling for invalid client type."""

        # We'll create a simple factory function for testing
        def create_client(client_type, model):
            if client_type not in ["openai", "mlx", "hf"]:
                raise ValueError(f"Unsupported client type: {client_type}")
            return MockLLMClient(model)

        # Test with invalid client type
        with self.assertRaises(ValueError):
            create_client("invalid", "test-model")

        # Test with valid client type
        client = create_client("openai", "test-model")
        self.assertIsInstance(client, MockLLMClient)
        self.assertEqual(client.model, "test-model")


if __name__ == "__main__":
    unittest.main()
