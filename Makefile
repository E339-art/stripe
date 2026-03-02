.PHONY: help install dev lint format typecheck test test-cov clean build

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in editable mode
	pip install -e .

dev: ## Install with all development dependencies
	pip install -e ".[dev]"
	pre-commit install || true

lint: ## Run linting checks
	ruff check src/ tests/ examples/

format: ## Format code with ruff
	ruff format src/ tests/ examples/
	ruff check --fix src/ tests/ examples/

typecheck: ## Run mypy type checking
	mypy src/

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage report
	pytest tests/ -v --cov=stripewrap --cov-report=term-missing --cov-report=html

check: lint typecheck test ## Run all checks (lint + typecheck + test)

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	rm -rf .mypy_cache .ruff_cache .pytest_cache
	rm -rf htmlcov/ .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

build: clean ## Build distribution packages
	python -m build
