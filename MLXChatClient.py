from mlx_lm import generate, load


class MLXChatClient:
    def __init__(self):
        """Initialize the client with an empty model cache."""
        self.models = {}

    def _load_model(self, model_name):
        """Load and cache the model if not already loaded."""
        if model_name not in self.models:
            self.models[model_name] = load(model_name)
        return self.models[model_name]

    def create(self, model, messages, stream=False):
        """Mimics OpenAI's API behavior for chat completion."""
        model_instance, tokenizer = self._load_model(model)

        # Ensure the messages follow the required structure
        if messages[0]["role"] == "system":
            # Merge the system message into the first user message
            if len(messages) > 1 and messages[1]["role"] == "user":
                messages[1]["content"] = (
                    messages[0]["content"] + "\n\n" + messages[1]["content"]
                )
                messages.pop(0)  # Remove the system message

        # Ensure alternation of roles: user -> assistant -> user -> assistant
        expected_roles = ["user", "assistant"]
        for i, message in enumerate(messages):
            if message["role"] != expected_roles[i % 2]:
                raise ValueError(
                    "Messages must alternate between user and assistant roles."
                )

        # Apply chat template
        prompt = tokenizer.apply_chat_template(
            conversation=messages, add_generation_prompt=True
        )

        # Generate response
        if stream:
            return generate(
                model=model_instance,
                tokenizer=tokenizer,
                prompt=prompt,
                max_tokens=1000,
                verbose=False,
            )
        else:
            tokens = [
                token
                for token in generate(
                    model=model_instance,
                    tokenizer=tokenizer,
                    prompt=prompt,
                    max_tokens=1000,
                    verbose=False,
                )
            ]
            full_response = "".join(tokens)
            return {
                "choices": [
                    {"message": {"role": "assistant", "content": full_response}}
                ]
            }


# Example usage
client = MLXChatClient()
name_of_model = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
agent = {"id": 1}
role_description = "You are a strategic player in the game."
agent_memory = "Previously, you allied with Player 3."
formatted_prompt = "What is your next move?"

response = client.create(
    model=name_of_model,
    messages=[
        {
            "role": "system",
            "content": f"You are Player {agent['id']}. {role_description}\n\nYour memory: {agent_memory}",
        },
        {"role": "user", "content": formatted_prompt},
    ],
    stream=False,
)

print(response["choices"][0]["message"]["content"])
