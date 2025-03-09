Architecture
============

TheTraitors framework is designed with a modular, object-oriented architecture that separates concerns and promotes extensibility.

System Overview
--------------

.. image:: _static/architecture_diagram.png
   :alt: Architecture Diagram
   :width: 600px

*Note: You'll need to create this diagram and place it in the _static directory.*

The system consists of three main components:

1. **Game Engine** (`TraitorsGame` class)
2. **Agents** (`Agent` class)
3. **LLM Clients** (`LLMClient` hierarchy)

Component Relationships
----------------------

- The `TraitorsGame` class manages the overall game flow and contains multiple `Agent` instances
- Each `Agent` has its own `LLMClient` instance for communication with language models
- The `LLMClientFactory` creates appropriate client instances based on configuration

Class Structure
--------------

TraitorsGame
^^^^^^^^^^^

The `TraitorsGame` class is the central component that:

- Initializes the game state and agents
- Manages the game loop and phases (discussion, voting, elimination)
- Handles game logic and win conditions
- Records game history and metrics

Agent
^^^^^

The `Agent` class represents a player in the game and:

- Maintains agent state (role, memory, elimination status)
- Handles agent-specific LLM interactions
- Provides methods for role-specific behaviors
- Manages agent memory and logging

LLM Client Hierarchy
^^^^^^^^^^^^^^^^^^^

The LLM client classes provide a unified interface for different LLM providers:

- `LLMClient`: Abstract base class defining the interface
- `OpenAIClient`: For OpenAI and compatible APIs
- `MLXClient`: For local MLX-based models
- `HuggingFaceClient`: For Hugging Face Inference API

Design Patterns
--------------

The architecture employs several design patterns:

1. **Factory Pattern**: `LLMClientFactory` creates appropriate client instances
2. **Strategy Pattern**: Different LLM clients implement the same interface
3. **Facade Pattern**: `TraitorsGame` provides a simplified interface to the complex system
4. **Observer Pattern**: Agents observe and react to game events

Data Flow
--------

1. The game engine initializes agents with their roles
2. During each round:
   - Agents receive game state information
   - Agents use their LLM clients to generate responses
   - The game engine processes these responses
   - Voting results in eliminations
   - Game state is updated
3. The process continues until a win condition is met

File Structure
-------------

.. code-block:: text

   TheTraitors/
   ├── main.py           # Main game engine
   ├── agent.py          # Agent class definition
   ├── llm_client.py     # LLM client classes
   ├── utils.py          # Utility functions
   ├── requirements.txt  # Dependencies
   ├── results/          # Game results directory
   └── docs/             # Documentation 