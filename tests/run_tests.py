#!/usr/bin/env python3
"""
Test runner for TheTraitors project.
Run this script to execute all tests.
"""

import argparse
import os
import sys
import unittest
from unittest import mock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock external dependencies that might not be installed
try:
    pass
except ImportError:
    print("Warning: pandas not found, mocking it for tests")
    sys.modules["pandas"] = mock.MagicMock()

# Mock OpenAI and other external dependencies
for module_name in ["openai", "MLXChatClient", "huggingface_hub"]:
    if module_name not in sys.modules:
        sys.modules[module_name] = mock.MagicMock()
        print(f"Warning: {module_name} not found, mocking it for tests")


def run_tests(with_coverage=False):
    """Run all tests, optionally with coverage measurement."""
    if with_coverage:
        try:
            import coverage
        except ImportError:
            print(
                "Coverage package not installed. Run 'pip install coverage' to install it."
            )
            print("Running tests without coverage measurement...")
            with_coverage = False

    if with_coverage:
        cov = coverage.Coverage(config_file=".coveragerc")
        cov.start()

    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), "unit")
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if with_coverage:
        cov.stop()
        cov.save()
        print("\nCoverage Summary:")
        cov.report()
        print("\nTo generate an HTML report, run: coverage html")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TheTraitors tests")
    parser.add_argument(
        "--coverage", action="store_true", help="Run tests with coverage measurement"
    )
    args = parser.parse_args()

    sys.exit(run_tests(with_coverage=args.coverage))
