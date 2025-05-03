# Contributing to TheTraitors

Thank you for your interest in contributing to TheTraitors! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing to the project.

## How to Contribute

There are many ways to contribute to TheTraitors:

1. **Reporting Bugs**: If you find a bug, please open an issue describing the problem, expected behavior, and steps to reproduce.
2. **Suggesting Enhancements**: Feature requests are welcome - please describe what you'd like to see and why it would be valuable.
3. **Contributing Code**: Pull requests for bug fixes, enhancements, or new features are greatly appreciated.
4. **Improving Documentation**: Help with documentation is always welcome, whether it's fixing typos or adding new guides.
5. **Sharing Experimental Results**: If you run experiments using TheTraitors, consider sharing your results and insights.

## Development Workflow

### Setting Up Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/TheTraitors.git
   cd TheTraitors
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install pytest coverage  # For development
   ```
4. Set up API keys as described in the README.md

### Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Add tests for your changes if applicable
4. Run the tests to ensure everything works:
   ```bash
   python tests/run_tests.py
   ```
5. Update documentation if necessary

### Submitting Changes

1. Commit your changes:
   ```bash
   git commit -am "Add a descriptive commit message"
   ```
2. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
3. Create a pull request from your fork to the main repository

### Pull Request Guidelines

1. Describe what your changes do and why they should be included
2. Include any relevant issue numbers in the PR description
3. Make sure all tests pass
4. Update documentation if necessary
5. Keep PRs focused on a single topic to make review easier

## Code Standards

- Follow PEP 8 style guidelines for Python code
- Write clear, descriptive commit messages
- Include docstrings for all functions, classes, and modules
- Add type hints where appropriate
- Write tests for new functionality

## Testing

Run tests using the test runner:

```bash
python tests/run_tests.py
```

For test coverage reports:

```bash
python tests/run_tests.py --coverage
```

## Documentation

If you're adding new features or changing existing ones, please update the relevant documentation:

- Docstrings in the code
- README.md for user-facing changes
- API documentation in the docs/ directory

To build the documentation locally:

```bash
cd docs
make html
```

## Research Extensions

The TheTraitors framework is designed for research on multi-agent systems, LLM capabilities, deception dynamics, and strategic reasoning. If you're extending the project for research purposes, consider:

1. Adding new metrics to measure agent behavior
2. Implementing new agent traits or roles
3. Creating specialized prompting techniques
4. Developing new analysis tools for game data

## Project Structure

- `src/`: Core source code
  - `agent.py`: Agent class definition
  - `llm_client.py`: LLM client classes and factory
  - `prompt_manager.py`: Manages structured prompts for agents
  - `traitors_game.py`: Main game engine
- `utils/`: Utility modules
- `tests/`: Test suite
- `docs/`: Documentation
- `results/`: Game results directory

## Questions?

If you have any questions about contributing, feel free to open an issue for discussion.

Thank you for your contributions!