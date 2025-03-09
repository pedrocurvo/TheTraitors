.PHONY: test test-coverage test-html clean

# Run all tests
test:
	python tests/run_tests.py

# Run tests with coverage
test-coverage:
	python tests/run_tests.py --coverage

# Run tests and generate HTML coverage report
test-html:
	coverage run tests/run_tests.py
	coverage html
	@echo "Open htmlcov/index.html in your browser to view the report"

# Clean up coverage data and reports
clean:
	rm -rf .coverage htmlcov
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete 