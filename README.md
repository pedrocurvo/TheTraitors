# TheTraitors

A Python framework for simulating multi-agent social deduction games using Large Language Models (LLMs).

## Overview

TheTraitors creates dynamic interactions between AI agents playing a social deduction game inspired by the popular TV show "The Traitors." The framework allows researchers and developers to study emergent behaviors, strategic reasoning, and social dynamics in LLM-based agents.

## Installation

### Setting up a virtual environment

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

### Installing dependencies

Once your virtual environment is activated, install the required dependencies:

```bash
pip install -r requirements.txt
```

For development purposes, you may want to install additional packages:

```bash
pip install pytest coverage
```

## Usage

Basic usage example:

```python
from thetraitors.main import TraitorsGame

# Create a new game with default settings
game = TraitorsGame(
    agent_count=10,
    traitor_count=3,
    model="gpt-3.5-turbo",
    client_type="openai"
)

# Run the game
game.run()

# Analyze the results
game.post_game_analysis()
```

For more detailed usage instructions, see the [documentation](https://thetraitors.readthedocs.io/).

## Running Tests

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

## Documentation

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Pedro Curvo

