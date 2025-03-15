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

   from traitors_game import TraitorsGame
   
   # Create a configuration dictionary
   config = {
       'game': {
           'agent_count': 10,
           'traitor_count': 3,
           'seed': 42,
           'experiment_name': 'my_experiment'
       },
       'llm': {
           'model': 'gpt-3.5-turbo',
           'client_type': 'openai',
           'provider': 'openai'
       }
   }
   
   # Create a game with 10 agents, 3 of which are traitors
   game = TraitorsGame(
       config=config,
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

Agent Traits
^^^^^^^^^^^

You can define personality traits for agents in your configuration file:

.. code-block:: python

   config = {
       # ...other configuration...
       'agent_configs': [
           {
               'model': 'gpt-3.5-turbo',
               'client_type': 'openai',
               'enforce_role': 'Traitor',  # Optional role enforcement
               'traits': {
                   'age': 42,
                   'nationality': 'British',
                   'profession': 'Detective',
                   'ethnicity': 'Caucasian',
                   'civil_status': 'Divorced',
                   'gender_pronoun': 'He',
                   'children': 2
               }
           },
           # More agent configurations...
       ]
   }

The traits will be used during the introduction phase to create a richer game experience.

Command Line Interface
^^^^^^^^^^^^^^^^^^^^^

You can also run the game using the command line interface:

.. code-block:: console

   $ python main.py --config path/to/config.yaml
   
   # Or with direct arguments
   $ python main.py --agents 10 --traitors 3 --model gpt-3.5-turbo --client openai --provider openai --seed 42

Configuration with YAML
---------------------

You can create a YAML configuration file with all game parameters:

.. code-block:: yaml

   game:
     agent_count: 10
     traitor_count: 3
     seed: 42
     experiment_name: experiment_1
   
   llm:
     model: gpt-3.5-turbo
     client_type: openai
     provider: openai
   
   agent_configs:
     - model: gpt-3.5-turbo
       client_type: openai
       enforce_role: Traitor
       traits:
         age: 45
         nationality: American
         profession: Lawyer
         ethnicity: Latino
         civil_status: Married
         gender_pronoun: He
         children: 3

Configuration Options
--------------------

The `TraitorsGame` constructor accepts the following parameters:

* `config`: Configuration dictionary with game parameters
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
* **MLX**: Using local MLX models for Mac with Apple Silicon

Viewing Results
--------------

After running a game, results are saved in the `results` directory:

* `history.txt`: Complete game transcript
* `votes.csv`: Record of all votes and eliminations
* `metrics.txt`: Game metrics and statistics
* `config.yaml`: Game configuration
* Agent-specific logs in subdirectories

The results are organized in a structured way:
`results/{experiment_name}/{model}/run-{number}/`

