# TheTraitors

<p align="center">
    <img src="docs/source/logo.png" align="center" width="30%">
</p>

<p align="center">
	<em><code>TheTraitors: A multi-agent LLM-based social deduction game framework</code></em>
</p>

<p align="center">
	<img src="https://img.shields.io/github/license/pedrocurvo/TheTraitors" alt="license">
	<img src="https://img.shields.io/badge/python-3.8%2B-blue" alt="python-version">
	<img src="https://img.shields.io/badge/LLM-GPT--4,%20DeepSeek,%20more-blue" alt="supported-models">
</p>

<p align="center">
	<!-- Additional badges can be added here -->
</p>

<br>

## 📋 Table of Contents

- [TheTraitors](#thetraitors)
  - [📋 Table of Contents](#-table-of-contents)
  - [📖 Overview](#-overview)
  - [✨ Features](#-features)
  - [🔍 Project Structure](#-project-structure)
  - [🚀 Getting Started](#-getting-started)
    - [📋 Prerequisites](#-prerequisites)
    - [⚙️ Installation](#️-installation)
      - [Setting up a virtual environment](#setting-up-a-virtual-environment)
      - [Installing dependencies](#installing-dependencies)
      - [Setting up API keys](#setting-up-api-keys)
    - [📊 Usage](#-usage)
      - [Basic Python API](#basic-python-api)
      - [Command Line Interface](#command-line-interface)
      - [Configuration with YAML](#configuration-with-yaml)
    - [🧪 Testing](#-testing)
  - [📚 Documentation](#-documentation)
  - [📜 License](#-license)
  - [👤 Author](#-author)

---

## 📖 Overview

**TheTraitors** is a Python framework for simulating multi-agent social deduction games using Large Language Models (LLMs). It creates dynamic interactions between AI agents playing a social deduction game inspired by the popular TV show "The Traitors."

The framework allows researchers and developers to study:
- Emergent behaviors in multi-agent LLM systems
- Strategic reasoning and deception capabilities
- Social dynamics and coalition formation
- Theory of mind in language models

---

## ✨ Features

- **Agent-based Architecture**: Each agent has its own memory, role, and LLM client
- **Multiple LLM Support**: Compatible with various providers:
  - OpenAI API (GPT models)
  - Deepseek's API
  - Together AI's API
  - Hugging Face Inference API
  - Local MLX models for Mac with Apple Silicon
- **Extensible Design**: Modular architecture makes it easy to customize game rules and agent behaviors
- **Detailed Logging**: Comprehensive logs of discussions, votes, and game outcomes
- **Analysis Tools**: Utilities for analyzing game dynamics and agent performance
- **Persona System**: Agents can have rich backgrounds with traits like age, profession, and nationality
- **Configuration-based**: Flexible configuration system using YAML files and command-line arguments
- **Role Enforcement**: Option to enforce specific roles for certain agents in experiments
- **Structured Memory**: Advanced memory system categorizing information for better agent reasoning

---

## 🔍 Project Structure

```
TheTraitors/
├── config.yaml             # Sample configuration file
├── main.py                 # Main entry point
├── src/                    # Core source code
│   ├── agent.py            # Agent class definition
│   ├── llm_client.py       # LLM client classes and factory
│   ├── prompt_manager.py   # Manages structured prompts for agents
│   └── traitors_game.py    # Main game engine
├── utils/                  # Utility modules
│   ├── config.py           # Configuration handling
│   └── metrics.py          # Game metrics computation
├── tests/                  # Test suite
├── docs/                   # Documentation
└── results/                # Game results directory
```

---

## 🚀 Getting Started

### 📋 Prerequisites

- Python 3.8 or higher
- API keys for the LLM providers you want to use

### ⚙️ Installation

#### Setting up a virtual environment

It's recommended to use a virtual environment to manage dependencies:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Installing dependencies

Once your virtual environment is activated, install the required dependencies:

```bash
pip install -r requirements.txt
```

For development purposes, you may want to install additional packages:

```bash
pip install pytest coverage
```

#### Setting up API keys

Create a `.env` file in the project root with your API keys:

```
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
TOGETHER_API_KEY=your_together_api_key
HF_API_TOKEN=your_huggingface_token
```

### 📊 Usage

#### Basic Python API

```python
from src.traitors_game import TraitorsGame

# Load a configuration from a YAML file
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

# Create and run the game
game = TraitorsGame(config=config)
game.run()
game.post_game_analysis()
```

#### Command Line Interface

You can also run the game using the command line interface:

```bash
# Run with a configuration file
python main.py --config path/to/config.yaml

# Or with direct arguments
python main.py --agents 10 --traitors 3 --model gpt-3.5-turbo --client openai --provider openai --seed 42
```

#### Configuration with YAML

Create a YAML configuration file with all game parameters:

```yaml
game:
  agent_count: 10
  traitor_count: 3
  seed: 42
  experiment_name: experiment_1

llm:
  model: deepseek-chat
  client_type: openai
  provider: deepseek

agent_configs:
  - model: deepseek-chat
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
```

### 🧪 Testing

The project includes a comprehensive test suite. To run the tests:

```bash
# Run all tests
python tests/run_tests.py

# Run tests with coverage
python tests/run_tests.py --coverage

# Generate HTML coverage report
make test-html
```

Alternatively, you can use the provided Makefile:

```bash
# Run all tests
make test

# Run tests with coverage
make test-coverage

# Generate HTML coverage report
make test-html
```

---

## 📚 Documentation

The documentation is built with Sphinx and can be found at [https://thetraitors.readthedocs.io/](https://thetraitors.readthedocs.io/).

To build the documentation locally:

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme

# Build the documentation
cd docs
make html

# View the documentation
open build/html/index.html
```

---

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👤 Author

Pedro Curvo

