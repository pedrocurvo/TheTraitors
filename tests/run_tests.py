#!/usr/bin/env python3
"""
Test runner for TheTraitors project.
Run this script to execute all tests.
"""

import unittest
from unittest import mock
import sys
import os
import importlib.util
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock external dependencies that might not be installed
try:
    import pandas as pd
except ImportError:
    print("Warning: pandas not found, mocking it for tests")
    sys.modules['pandas'] = mock.MagicMock()

# Mock OpenAI and other external dependencies
for module_name in ['openai', 'MLXChatClient', 'huggingface_hub']:
    if module_name not in sys.modules:
        sys.modules[module_name] = mock.MagicMock()
        print(f"Warning: {module_name} not found, mocking it for tests")


def run_tests(with_coverage=False):
    """Run all tests in the tests directory.
    
    Args:
        with_coverage: Whether to measure code coverage
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    if with_coverage:
        try:
            import coverage
            cov = coverage.Coverage(
                source=['.'],
                omit=['*/tests/*', '*/venv/*', '*/site-packages/*']
            )
            cov.start()
            print("Running tests with coverage measurement...")
        except ImportError:
            print("Warning: coverage package not found. Install with 'pip install coverage'")
            print("Running tests without coverage measurement...")
            with_coverage = False
    
    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    if with_coverage:
        cov.stop()
        cov.save()
        print("\nCoverage Summary:")
        cov.report()
        print("\nGenerating HTML report in 'htmlcov' directory...")
        cov.html_report(directory='htmlcov')
        print("Open 'htmlcov/index.html' in your browser to view the report.")
    
    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run tests for TheTraitors project')
    parser.add_argument('--coverage', action='store_true', help='Measure code coverage')
    args = parser.parse_args()
    
    sys.exit(run_tests(with_coverage=args.coverage)) 