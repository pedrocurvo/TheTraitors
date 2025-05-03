Welcome to TheTraitors documentation!
===================================

**TheTraitors** is a Python framework for simulating multi-agent social deduction games using Large Language Models (LLMs). 
It creates dynamic interactions between AI agents playing a social deduction game inspired by the popular TV show "The Traitors."

The framework allows researchers and developers to study emergent behaviors, strategic reasoning, social dynamics, and deception in LLM-based agents.

Check out the :doc:`usage` section for further information, including how to :ref:`installation` install the project.

.. note::

   This project is under active development.

Game Overview
------------

In TheTraitors game:

* A group of AI agents participate in a social deduction game
* Most agents are "Faithfuls" trying to identify and eliminate the "Traitors"
* A small number of agents are secretly "Traitors" working to eliminate the Faithfuls
* The game proceeds in rounds with introduction, discussion, voting, and elimination phases
* Faithfuls win if they eliminate all Traitors
* Traitors win if they equal or outnumber the Faithfuls

Key Features
-----------

* **Agent-based Architecture**: Each agent has its own memory, role, and LLM client
* **Multiple LLM Support**: Compatible with various providers:
  * OpenAI API (GPT models)
  * Deepseek's API
  * Together AI's API
  * Hugging Face Inference API
  * Local MLX models for Mac with Apple Silicon
* **Extensible Design**: Modular architecture makes it easy to customize game rules and agent behaviors
* **Detailed Logging**: Comprehensive logs of discussions, votes, and game outcomes
* **Analysis Tools**: Utilities for analyzing game dynamics and agent performance
* **Persona System**: Agents can have rich backgrounds with traits like age, profession, and nationality
* **Configuration-based**: Flexible configuration system using YAML files and command-line arguments
* **Role Enforcement**: Option to enforce specific roles for certain agents in experiments
* **Structured Memory**: Advanced memory system categorizing information for better agent reasoning

Use Cases
--------

TheTraitors can be used for:

* Studying deception and trust formation in AI systems
* Researching theory of mind capabilities in language models
* Evaluating strategic reasoning abilities of different LLMs
* Testing alignment techniques against incentives for deception
* Exploring emergent social dynamics in multi-agent systems

Contents
--------

.. toctree::
   :maxdepth: 2

   usage
   game_rules
   architecture
   api
