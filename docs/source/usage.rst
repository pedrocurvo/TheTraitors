Usage
=====

.. _installation:

Installation
------------

To use TheTraitors, first install it using pip:

.. code-block:: console

   $ pip install -r requirements.txt

You'll need to set up API keys for the LLM providers you want to use. Create a `.env` file in the project root with your API keys:

.. code-block:: console

   OPENAI_API_KEY=your_openai_api_key
   DEEPSEEK_API_KEY=your_deepseek_api_key
   TOGETHER_API_KEY=your_together_api_key
   HF_API_TOKEN=your_huggingface_token

Basic Usage
-----------

Running a Game
^^^^^^^^^^^^^

To run a basic game simulation:

.. code-block:: python

   from main import TraitorsGame
   
   # Create a game with 10 agents, 3 of which are traitors
   game = TraitorsGame(
       agent_count=10,
       traitor_count=3,
       model="gpt-3.5-turbo",
       client_type="openai",
       provider="openai",
       seed=42  # For reproducibility
   )
   
   # Run the game
   game.run()
   
   # Analyze the results
   game.post_game_analysis()

Command Line Interface
^^^^^^^^^^^^^^^^^^^^^

You can also run the game using the command line interface:

.. code-block:: console

   $ python main.py --agents 10 --traitors 3 --model gpt-3.5-turbo --client openai --provider openai --seed 42

Configuration Options
--------------------

The `TraitorsGame` constructor accepts the following parameters:

* `agent_count`: Number of agents in the game (default: 10)
* `traitor_count`: Number of traitors among the agents (default: 3)
* `model`: Model name to use (default: "deepseek-chat")
* `seed`: Random seed for reproducibility (default: None)
* `client_type`: Type of client to use ("openai", "hf", "mlx") (default: "openai")
* `provider`: Provider for the client (default: None)
* `experiment_name`: Optional name for the experiment (default: None)

Supported LLM Providers
----------------------

TheTraitors supports multiple LLM providers:

* **OpenAI**: Using the OpenAI API (GPT models)
* **Deepseek**: Using Deepseek's API
* **Together AI**: Using Together AI's API
* **Hugging Face**: Using Hugging Face's Inference API
* **MLX**: Using local MLX models

Viewing Results
--------------

After running a game, results are saved in the `results` directory:

* `history.txt`: Complete game transcript
* `votes.csv`: Record of all votes and eliminations
* `metrics.txt`: Game metrics and statistics
* `config.yaml`: Game configuration
* Agent-specific logs in subdirectories

