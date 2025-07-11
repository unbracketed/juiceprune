# Prunejuice Project Makefile
# Unified Python project for parallel agentic coding workflow orchestration

.PHONY: help install test lint typecheck format clean dev run status init build docs-install docs-serve docs-build docs-clean docs-deploy

# Default target
help: ## Show this help message
	@echo "Prunejuice - Parallel Agentic Coding Workflow Orchestrator"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Development setup
install: ## Install the project and dependencies
	uv sync

dev-install: ## Install with development dependencies
	uv sync --dev

# Testing
test: ## Run all tests
	uv run pytest

test-verbose: ## Run tests with verbose output
	uv run pytest -v

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=prunejuice --cov-report=html --cov-report=term

test-integration: ## Run only integration tests
	uv run pytest tests/test_integrations.py -v

test-cli: ## Run only CLI tests
	uv run pytest tests/test_cli.py -v

test-failed: ## Rerun only failed tests
	uv run pytest --lf

# Code quality
lint: ## Run linting checks
	uv run ruff check src/ tests/

lint-fix: ## Fix linting issues automatically
	uv run ruff check --fix src/ tests/

format: ## Format code
	uv run ruff format src/ tests/

typecheck: ## Run type checking
	uv run mypy src/

check: lint typecheck ## Run all code quality checks

# Project commands
init: ## Initialize a new prunejuice project
	uv run prj init

status: ## Show project status
	uv run prj status

list-actions: ## List available actions
	uv run prj list-actions

# Development utilities
clean: ## Clean build artifacts and cache
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	uv build

# Git worktree commands (using native implementations)
worktree-create: ## Create a new git worktree (requires BRANCH=<name>)
	@if [ -z "$(BRANCH)" ]; then echo "Usage: make worktree-create BRANCH=<branch-name>"; exit 1; fi
	uv run python -c "import asyncio; from prunejuice.worktree_utils import GitWorktreeManager; asyncio.run(GitWorktreeManager('.').create_worktree('$(BRANCH)'))"

worktree-list: ## List all git worktrees
	uv run python -c "import asyncio; from prunejuice.worktree_utils import GitWorktreeManager; print('\n'.join([str(w) for w in asyncio.run(GitWorktreeManager('.').list_worktrees())]))"

# Tmux session commands (using native implementations)
session-create: ## Create a tmux session (requires TASK=<name>)
	@if [ -z "$(TASK)" ]; then echo "Usage: make session-create TASK=<task-name>"; exit 1; fi
	uv run python -c "import asyncio; from prunejuice.session_utils import SessionLifecycleManager; asyncio.run(SessionLifecycleManager().create_session_for_worktree('.', '$(TASK)'))"

session-list: ## List all tmux sessions
	uv run python -c "import asyncio; from prunejuice.session_utils import TmuxManager; print('\n'.join([s['name'] for s in asyncio.run(TmuxManager().list_sessions())]))"

# Documentation
docs-install: ## Install documentation dependencies
	uv sync --group docs

docs-serve: ## Serve documentation locally (use PORT=<number> to specify port)
	uv run mkdocs serve --dev-addr 127.0.0.1:$${PORT:-8000}

docs-build: ## Build static documentation
	uv run mkdocs build

docs-clean: ## Clean documentation build artifacts
	rm -rf site/

docs-deploy: ## Deploy documentation to GitHub Pages
	uv run mkdocs gh-deploy

# Complete development workflow
dev-setup: dev-install docs-install check test ## Complete development environment setup

# CI/CD workflow
ci: check test ## Run CI checks (linting, type checking, tests)

# Test project management
create-test-project: ## Create a new test project directory with git repo
	@PROJECT_NAME="test-project-$(shell date +%Y%m%d-%H%M%S)"; \
	mkdir -p tmp/$$PROJECT_NAME; \
	cd tmp/$$PROJECT_NAME; \
	git init; \
	echo "# Test Project: $$PROJECT_NAME" > README.md; \
	echo "Created: $(shell date)" >> README.md; \
	git add README.md; \
	git commit -m "Initial commit for test project"; \
	echo "Created test project: tmp/$$PROJECT_NAME"

list-test-projects: ## List all test projects
	@echo "Test projects in tmp/:"
	@ls -la tmp/ 2>/dev/null || echo "No test projects found"

clean-test-projects: ## Remove all test projects
	@rm -rf tmp/*
	@echo "All test projects removed"

# Example commands for development
example-init: ## Example: Initialize project in current directory
	uv run prj init
	@echo "Project initialized. Try 'make example-status' next."

example-status: ## Example: Show detailed project status
	uv run prj status
	@echo "Use 'make list-actions' to see available actions."

example-run: ## Example: Run an action (requires ACTION=<action-name>)
	@if [ -z "$(ACTION)" ]; then echo "Usage: make example-run ACTION=<action-name>"; exit 1; fi
	uv run prj run $(CMD)