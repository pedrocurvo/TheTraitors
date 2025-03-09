API
===

This page details the API for TheTraitors framework.

TraitorsGame
------------

.. py:class:: TraitorsGame

   The main class that manages the game simulation.

   .. py:method:: __init__(agent_count=10, traitor_count=3, model="deepseek-chat", seed=None, client_type="openai", provider=None, experiment_name=None)

      Initialize a new Traitors game.

      :param agent_count: Number of agents in the game
      :param traitor_count: Number of traitors among the agents
      :param model: Model name to use for LLM calls
      :param seed: Random seed for reproducibility
      :param client_type: Type of client to use ("openai", "hf", "mlx")
      :param provider: Provider for the client
      :param experiment_name: Optional name for the experiment

   .. py:method:: create_agents(agent_count, traitor_count)

      Initialize agents with unique roles.

      :param agent_count: Number of agents to create
      :param traitor_count: Number of traitors to assign
      :return: List of Agent objects

   .. py:method:: call_llm(agent)

      Call the LLM API to generate agent responses.

      :param agent: The agent to generate a response for
      :return: The agent's response text

   .. py:method:: run()

      Run the game simulation until a winner is determined.

   .. py:method:: post_game_analysis()

      Compute game metrics and write to a file.

Agent
-----

.. py:class:: Agent

   Represents a player in the Traitors Game.

   .. py:method:: __init__(agent_id, role, model, results_dir, llm_client=None)

      Initialize an agent with basic attributes.

      :param agent_id: The unique identifier for this agent
      :param role: Either "Faithful" or "Traitor"
      :param model: The LLM model to use for this agent
      :param results_dir: Directory to store agent-specific files
      :param llm_client: The LLM client to use for this agent

   .. py:method:: set_llm_client(llm_client)

      Set the LLM client for this agent.

      :param llm_client: The LLM client to use

   .. py:method:: call_llm(user_prompt)

      Call the LLM API to generate a response.

      :param user_prompt: The prompt to send to the LLM
      :return: The LLM's response

   .. py:method:: is_traitor()

      Check if the agent is a traitor.

      :return: True if the agent is a traitor, False otherwise

   .. py:method:: is_faithful()

      Check if the agent is faithful.

      :return: True if the agent is faithful, False otherwise

   .. py:method:: is_eliminated()

      Check if the agent has been eliminated.

      :return: True if the agent has been eliminated, False otherwise

LLMClient
---------

.. py:class:: LLMClient

   Abstract base class for LLM clients.

   .. py:method:: __init__(model)

      Initialize the LLM client.

      :param model: The model name to use for API calls

   .. py:method:: call(system_message, user_message)

      Call the LLM API with the given messages.

      :param system_message: The system message to send
      :param user_message: The user message to send
      :return: The LLM's response text

LLMClientFactory
---------------

.. py:class:: LLMClientFactory

   Factory for creating LLM clients based on configuration.

   .. py:staticmethod:: create_client(client_type, model, provider=None)

      Create an LLM client based on the specified type.

      :param client_type: Type of client to create ('openai', 'mlx', 'hf')
      :param model: Model name to use
      :param provider: Optional provider name for certain client types
      :return: An instance of the appropriate LLMClient subclass
