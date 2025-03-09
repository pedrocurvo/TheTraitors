import os
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, model: str):
        """Initialize the LLM client.

        Args:
            model: The model name to use for API calls
        """
        self.model = model

    @abstractmethod
    def call(self, system_message: str, user_message: str) -> str:
        """Call the LLM API with the given messages.

        Args:
            system_message: The system message to send
            user_message: The user message to send

        Returns:
            The LLM's response text
        """
        pass

    def extract_dialogue(self, full_response: str) -> str:
        """Extract dialogue from between triple dashes in the response.

        Args:
            full_response: The full response from the LLM

        Returns:
            The extracted dialogue, or the full response if no markers found
        """
        pattern = r"---\s*([\s\S]*?)\s*---"
        match = re.search(pattern, full_response)

        if match:
            return match.group(1).strip()
        else:
            # If no markers found, use the whole response
            return full_response


class OpenAIClient(LLMClient):
    """Client for OpenAI-compatible APIs."""

    def __init__(self, model: str, api_key: str, base_url: Optional[str] = None):
        """Initialize the OpenAI client.

        Args:
            model: The model name to use
            api_key: The API key for authentication
            base_url: Optional base URL for the API (for compatible providers)
        """
        super().__init__(model)
        from openai import OpenAI

        client_args = {"api_key": api_key}
        if base_url:
            client_args["base_url"] = base_url

        self.client = OpenAI(**client_args)

    def call(self, system_message: str, user_message: str) -> str:
        """Call the OpenAI API with the given messages."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return f"Error: {str(e)}"


class MLXClient(LLMClient):
    """Client for MLX-based local models."""

    def __init__(self, model: str):
        """Initialize the MLX client."""
        super().__init__(model)
        try:
            from MLXChatClient import MLXChatClient

            self.client = MLXChatClient()
        except ImportError:
            raise ImportError("Please install the MLX package to use MLX client")

    def call(self, system_message: str, user_message: str) -> str:
        """Call the MLX model with the given messages."""
        try:
            response = self.client.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                stream=False,
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error calling MLX model: {e}")
            return f"Error: {str(e)}"


class HuggingFaceClient(LLMClient):
    """Client for Hugging Face Inference API."""

    def __init__(
        self, model: str, provider: Optional[str] = None, api_key: Optional[str] = None
    ):
        """Initialize the Hugging Face client.

        Args:
            model: The model name to use
            provider: Optional provider name (e.g., 'together')
            api_key: API key for authentication
        """
        super().__init__(model)
        try:
            from huggingface_hub import InferenceClient

            if provider == "together":
                self.client = InferenceClient(provider="together", api_key=api_key)
                self.provider = "together"
            else:
                self.client = InferenceClient(token=api_key)
                self.provider = None
        except ImportError:
            raise ImportError("Please install huggingface_hub package to use HF client")

    def call(self, system_message: str, user_message: str) -> str:
        """Call the Hugging Face API with the given messages."""
        try:
            if self.provider == "together":
                # Use chat_completion for Together AI provider
                response = self.client.chat_completion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.7,
                    max_tokens=500,
                )
                return response.choices[0].message.content
            else:
                # Standard HF text generation
                return self.client.text_generation(
                    prompt=f"<s>[INST] <<SYS>>\n{system_message}\n<</SYS>>\n\n{user_message} [/INST]",
                    model=self.model,
                    max_new_tokens=500,
                    temperature=0.7,
                    top_p=0.9,
                )
        except Exception as e:
            print(f"Error calling Hugging Face API: {e}")
            return f"Error: {str(e)}"


class LLMClientFactory:
    """Factory for creating LLM clients based on configuration."""

    @staticmethod
    def create_client(
        client_type: str, model: str, provider: Optional[str] = None
    ) -> LLMClient:
        """Create an LLM client based on the specified type.

        Args:
            client_type: Type of client to create ('openai', 'mlx', 'hf')
            model: Model name to use
            provider: Optional provider name for certain client types

        Returns:
            An instance of the appropriate LLMClient subclass
        """
        # Provider-specific settings
        provider_settings = {
            "deepseek": {
                "api_key": os.getenv("DEEPSEEK_API_KEY"),
                "base_url": "https://api.deepseek.com",
            },
            "openai": {"api_key": os.getenv("OPENAI_API_KEY")},
            "together": {
                "api_key": os.getenv("TOGETHER_API_KEY"),
                "base_url": "https://api.together.xyz/v1",
            },
        }

        if client_type == "openai":
            if provider == "openai":
                return OpenAIClient(
                    model=model, api_key=provider_settings["openai"]["api_key"]
                )
            elif provider in ["deepseek", "together"]:
                return OpenAIClient(
                    model=model,
                    api_key=provider_settings[provider]["api_key"],
                    base_url=provider_settings[provider]["base_url"],
                )
            else:
                raise ValueError(
                    f"Unsupported provider: {provider} for client type: {client_type}"
                )

        elif client_type == "mlx":
            return MLXClient(model=model)

        elif client_type == "hf":
            if provider == "together":
                return HuggingFaceClient(
                    model=model,
                    provider="together",
                    api_key=provider_settings["together"]["api_key"],
                )
            else:
                return HuggingFaceClient(model=model, api_key=os.getenv("HF_API_TOKEN"))

        else:
            raise ValueError(f"Unsupported client type: {client_type}")
