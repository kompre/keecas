.PHONY: lint format check test lint-docs

# Run linter (check for issues)
lint:
	uv run ruff check src/ tests/

# Auto-fix linting issues
fix:
	uv run ruff check --fix src/ tests/

# Format code
format:
	uv run ruff format src/ tests/

# Check code in docstrings (includes trailing comma check)
lint-docs:
	uv run python scripts/lint_docstring_code.py src/keecas/*.py

# Run all checks
check: lint lint-docs test

# Run tests
test:
	uv run pytest tests/
