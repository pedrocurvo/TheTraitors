# TheTraitors Tests

This directory contains tests for the TheTraitors project.

## Test Structure

- `unit/`: Unit tests for individual components
  - `test_agent.py`: Tests for the Agent class
  - `test_llm_client.py`: Tests for the LLM client classes
  - `test_traitors_game.py`: Tests for the TraitorsGame class
  - `test_utils.py`: Tests for utility functions

## Running Tests

You can run all tests using the test runner:

```bash
python tests/run_tests.py
```

Or you can use Python's unittest discovery:

```bash
python -m unittest discover -s tests
```

To run a specific test file:

```bash
python -m unittest tests/unit/test_agent.py
```

To run a specific test case:

```bash
python -m unittest tests.unit.test_agent.TestAgent.test_initialization
```

## Measuring Code Coverage

To measure code coverage, you can use the `--coverage` flag with the test runner:

```bash
python tests/run_tests.py --coverage
```

This requires the `coverage` package to be installed:

```bash
pip install coverage
```

You can also run coverage directly:

```bash
coverage run tests/run_tests.py
coverage report  # Text report
coverage html    # HTML report
```

The HTML report will be generated in the `htmlcov` directory. Open `htmlcov/index.html` in your browser to view a detailed report.

## Test Coverage

The tests cover:

- Agent initialization, role methods, memory management, and LLM interaction
- LLM client functionality (basic functionality only, external dependencies are mocked)
- TraitorsGame initialization, game flow, and win conditions
- Utility functions for game metrics

## Adding New Tests

When adding new tests:

1. Follow the existing pattern of test organization
2. Use descriptive test method names that explain what is being tested
3. Use appropriate assertions to verify expected behavior
4. Mock external dependencies to avoid actual API calls
5. Clean up any temporary resources in tearDown methods

## Mocking Strategy

The tests use Python's `unittest.mock` module to mock external dependencies:

- LLM API clients (OpenAI, Hugging Face, etc.) are mocked to avoid actual API calls
- File operations are mocked to avoid creating actual files
- Path operations are mocked to avoid creating actual directories

This ensures that tests can run quickly and reliably without external dependencies. 