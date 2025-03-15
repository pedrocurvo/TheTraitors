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

- Initializes the game state and agents with their roles
- Manages the game loop with multiple phases (discussion, voting, traitor elimination)
- Handles game logic and win conditions
- Records game history, votes, and metrics
- Supports agent customization through traits and role assignments
- Implements introduction, discussion and post-elimination phases

Agent
^^^^^

The `Agent` class represents a player in the game and:

- Maintains agent state (role, memory, elimination status)
- Handles agent-specific LLM interactions
- Manages persona traits (age, profession, nationality, etc.)
- Provides methods for role-specific behaviors
- Maintains awareness of fellow traitors (for traitor agents)
- Records private memories and reflections

LLM Client Hierarchy
^^^^^^^^^^^^^^^^^^^

The LLM client classes provide a unified interface for different LLM providers:

- `LLMClient`: Abstract base class defining the interface
- `OpenAIClient`: For OpenAI and compatible APIs (including Deepseek and Together AI)
- `MLXClient`: For local MLX-based models (optimized for Mac with Apple Silicon)
- `HuggingFaceClient`: For Hugging Face Inference API

Configuration System
------------------

TheTraitors includes a flexible configuration system:

- YAML-based configuration files for game parameters
- Command-line arguments that can override configuration
- Support for agent-specific configurations, including traits and enforced roles
- Dynamic result directory creation based on experiment name and model

Design Patterns
--------------

The architecture employs several design patterns:

1. **Factory Pattern**: `LLMClientFactory` creates appropriate client instances
2. **Strategy Pattern**: Different LLM clients implement the same interface
3. **Facade Pattern**: `TraitorsGame` provides a simplified interface to the complex system
4. **Observer Pattern**: Agents observe and react to game events
5. **Configuration Pattern**: External configuration options control game behavior

Game Flow
--------

1. **Initialization**: Game engine sets up agents with roles and traits
2. **Introduction Phase**: Agents learn about each other's backgrounds
3. **Main Game Loop**:
   - **Discussion Phase**: All surviving agents discuss and share suspicions
   - **Voting Phase**: Agents vote to eliminate a suspected traitor
   - **Traitor Discussion Phase**: Traitors privately discuss strategy
   - **Traitor Elimination Phase**: Traitors eliminate a faithful player
   - **Win Condition Check**: Game checks if either side has met victory conditions
4. **Post-Game Analysis**: Computation of game metrics and statistics

File Structure
-------------

.. code-block:: text

   TheTraitors/
   ├── main.py               # Main entry point and CLI
   ├── traitors_game.py      # Main game engine
   ├── agent.py              # Agent class definition
   ├── llm_client.py         # LLM client interface and factory
   ├── MLXChatClient.py      # MLX-specific client for local models
   ├── utils/
   │   ├── __init__.py       # Common utilities
   │   ├── config.py         # Configuration handling
   │   └── metrics.py        # Game metrics computation
   ├── requirements.txt      # Dependencies
   ├── docs/                 # Documentation
   └── results/              # Game results directory