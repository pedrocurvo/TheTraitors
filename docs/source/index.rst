Welcome to TheTraitors documentation!
===================================

**TheTraitors** is a Python framework for simulating multi-agent social deduction games using Large Language Models (LLMs). 
It creates dynamic interactions between AI agents playing a social deduction game inspired by the popular TV show "The Traitors."

The framework allows researchers and developers to study emergent behaviors, strategic reasoning, and social dynamics in LLM-based agents.

Check out the :doc:`usage` section for further information, including how to :ref:`installation` the project.

.. note::

   This project is under active development.

Game Overview
------------

In TheTraitors game:

* A group of AI agents participate in a social deduction game
* Most agents are "Faithfuls" trying to identify and eliminate the "Traitors"
* A small number of agents are secretly "Traitors" working to eliminate the Faithfuls
* The game proceeds in rounds with discussion phases, voting phases, and elimination phases
* Faithfuls win if they eliminate all Traitors
* Traitors win if they equal or outnumber the Faithfuls

Key Features
-----------

* **Agent-based Architecture**: Each agent has its own memory, role, and LLM client
* **Multiple LLM Support**: Compatible with OpenAI, Hugging Face, MLX, and other LLM providers
* **Extensible Design**: Modular architecture makes it easy to customize game rules and agent behaviors
* **Detailed Logging**: Comprehensive logs of discussions, votes, and game outcomes
* **Analysis Tools**: Utilities for analyzing game dynamics and agent performance

Contents
--------

.. toctree::

   usage
   api
   architecture
   game_rules
