API Reference
============

This section provides a detailed reference for the key classes and functions in TheTraitors.

TraitorsGame
-----------

The main game engine that manages the simulation.

.. code-block:: python

   class TraitorsGame:
       def __init__(
           self,
           config,
           agent_count=10,
           traitor_count=3,
           model="deepseek-chat",
           seed=None,
           client_type="openai",
           provider=None,
           experiment_name=None
       ):
           """
           Initialize the Traitors Game.

           Args:
               config: Configuration dictionary
               agent_count: Default number of total agents in the game
               traitor_count: Default number of traitors among the agents
               model: Default model name to use
               seed: Random seed for reproducibility
               client_type: Default type of client to use ("openai", "hf", "mlx")
               provider: Default provider for the client
               experiment_name: Optional name for the experiment
           """

Key Methods
^^^^^^^^^^

.. code-block:: python

   def create_agents(self, agent_count, traitor_count):
       """
       Initialize agents with unique roles and traits from configuration.
       Returns a list of Agent instances.
       """

   def introduction_phase(self):
       """
       Run the introduction phase where agents share their background traits.
       """

   def discussion_phase(self):
       """
       Run a discussion phase where agents communicate and discuss who to vote out.
       """

   def voting_phase(self):
       """
       Run a voting phase where agents vote to eliminate a suspected traitor.
       """

   def traitor_discussion_phase(self):
       """
       Run a private discussion among traitor agents to decide who to eliminate.
       """

   def traitor_elimination_phase(self, traitors, active_faithfuls):
       """
       Execute the traitor elimination decision.
       """

   def check_win_conditions(self):
       """
       Check if the game has ended and determine the winner.
       Returns the winner ("Faithfuls", "Traitors") or None if game continues.
       """

   def run(self):
       """
       Execute the main game loop until win conditions are met.
       """

   def post_game_analysis(self):
       """
       Compute and save game metrics after the game has completed.
       """

Agent
----

The Agent class represents a player in the game.

.. code-block:: python

   class Agent:
       def __init__(self, id, role, model, results_dir, traits=None):
           """
           Initialize an Agent.
           
           Args:
               id: Unique identifier for the agent
               role: Either "Traitor" or "Faithful"
               model: The LLM model to use for this agent
               results_dir: Directory to save agent outputs
               traits: Optional dictionary of agent traits (age, profession, etc.)
           """

Key Methods
^^^^^^^^^^

.. code-block:: python

   def set_llm_client(self, client):
       """
       Set the LLM client for this agent.
       """

   def set_fellow_traitors(self, traitor_ids):
       """
       Provide a list of fellow traitor IDs to this agent (only for traitors).
       """

   def set_prompt(self, prompt):
       """
       Set the current prompt for the agent.
       """

   def add_to_memory(self, content, label=None):
       """
       Add content to the agent's memory, optionally with a label.
       """

   def call_llm(self, prompt):
       """
       Call the LLM client to generate a response.
       """

   def is_traitor(self):
       """
       Return True if the agent is a traitor, False otherwise.
       """

   def is_faithful(self):
       """
       Return True if the agent is faithful, False otherwise.
       """

   def is_eliminated(self):
       """
       Return True if the agent has been eliminated, False otherwise.
       """

   def eliminate(self):
       """
       Mark the agent as eliminated.
       """

LLM Clients
----------

The framework includes several LLM client implementations for different providers.

LLMClientFactory
^^^^^^^^^^^^^^^

.. code-block:: python

   class LLMClientFactory:
       @staticmethod
       def create_client(client_type, model, provider=None):
           """
           Create and return an LLM client based on the specified type.
           
           Args:
               client_type: Type of client ("openai", "hf", "mlx")
               model: Model name to use
               provider: Provider name (for compatible APIs)
               
           Returns:
               An instance of an LLMClient implementation
           """

OpenAIClient
^^^^^^^^^^^

.. code-block:: python

   class OpenAIClient:
       def __init__(self, model, provider=None):
           """
           Initialize an OpenAI-compatible client.
           
           Args:
               model: Model name to use
               provider: Provider name ("openai", "deepseek", "together")
           """
           
       def call(self, prompt):
           """
           Call the OpenAI-compatible API with the given prompt.
           
           Args:
               prompt: The prompt to send to the API
               
           Returns:
               The generated text response
           """

HuggingFaceClient
^^^^^^^^^^^^^^^

.. code-block:: python

   class HuggingFaceClient:
       def __init__(self, model):
           """
           Initialize a Hugging Face Inference API client.
           
           Args:
               model: The model name to use on Hugging Face
           """
           
       def call(self, prompt):
           """
           Call the Hugging Face Inference API with the given prompt.
           
           Args:
               prompt: The prompt to send to the API
               
           Returns:
               The generated text response
           """

MLXClient
^^^^^^^^

.. code-block:: python

   class MLXClient:
       def __init__(self, model):
           """
           Initialize an MLX-based client for local model inference.
           
           Args:
               model: The MLX-compatible model name to load
           """
           
       def call(self, prompt):
           """
           Generate a response using a local MLX model.
           
           Args:
               prompt: The prompt to send to the model
               
           Returns:
               The generated text response
           """

Utility Functions
--------------

TheTraitors includes several utility functions for configuration management and metrics computation.

Configuration
^^^^^^^^^^^

.. code-block:: python

   def load_config(config_path):
       """
       Load a YAML configuration file.
       
       Args:
           config_path: Path to the YAML configuration file
           
       Returns:
           A dictionary containing the configuration
       """
       
   def merge_config_with_args(config, args):
       """
       Merge command line arguments with a configuration dictionary.
       
       Args:
           config: The base configuration dictionary
           args: Parsed command line arguments
           
       Returns:
           The merged configuration dictionary
       """

Metrics
^^^^^^

.. code-block:: python

   def compute_traitors_game_metrics(csv_file):
       """
       Compute game metrics from a votes CSV file.
       
       Args:
           csv_file: Path to the votes CSV file
           
       Returns:
           A dictionary of computed metrics
       """
