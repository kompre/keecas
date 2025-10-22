# Linting and Code Quality

This project uses **Ruff** for fast, comprehensive Python linting and formatting.

## Quick Start

```bash
# Check code for issues
make lint

# Auto-fix issues (including trailing commas)
make fix

# Format code
make format

# Check docstring code blocks
make lint-docs

# Run all checks
make check
```

## Ruff Configuration

Configured in `pyproject.toml`:

- **COM (flake8-commas)**: Enforces trailing commas in multi-line collections
- **I (isort)**: Auto-sorts imports
- **E/W (pycodestyle)**: Style checks
- **F (pyflakes)**: Error detection
- **UP (pyupgrade)**: Modern Python syntax

## Trailing Comma Enforcement

### Regular Python Code

Ruff automatically enforces trailing commas in multi-line collections:

```python
# ❌ Missing trailing comma
my_list = [
    1,
    2,
    3  # Ruff will flag this
]

# ✅ With trailing comma
my_list = [
    1,
    2,
    3,  # Good!
]
```

**Auto-fix:**
```bash
make fix
```

### Docstring Code Blocks

Code inside docstrings (like `{python}` blocks in API docs) requires separate checking:

```bash
# Check all docstring code blocks
make lint-docs

# Or manually:
uv run python scripts/lint_docstring_code.py src/keecas/pipe_command.py
```

This will report:
- Missing trailing commas
- Unused imports
- Unused variables

**Note:** Auto-fix for docstring code is not yet implemented due to complexity with indentation and LaTeX formatting. Fix these manually based on the reported issues.

## Why Trailing Commas?

1. **Cleaner git diffs** - Adding a new item only changes one line
2. **No syntax errors** - Can't forget comma when reordering
3. **Consistent style** - Looks better and more maintainable

### Example Git Diff

**Without trailing comma:**
```diff
  my_list = [
      1,
      2,
-     3
+     3,
+     4
  ]
```

**With trailing comma:**
```diff
  my_list = [
      1,
      2,
      3,
+     4,
  ]
```

## Commands Reference

| Command | Description |
|---------|-------------|
| `make lint` | Check for linting issues |
| `make fix` | Auto-fix linting issues |
| `make format` | Format code with Ruff |
| `make lint-docs` | Check code in docstrings |
| `make check` | Run all checks + tests |
| `make test` | Run pytest |

## Manual Ruff Usage

```bash
# Check specific files
uv run ruff check src/keecas/pipe_command.py

# Auto-fix specific files
uv run ruff check --fix src/keecas/pipe_command.py

# Check only trailing commas
uv run ruff check --select COM src/

# Format files
uv run ruff format src/keecas/

# Show what would be formatted (dry-run)
uv run ruff format --check src/
```

## IDE Integration

### VS Code

Install the Ruff extension and add to `.vscode/settings.json`:

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    }
  }
}
```

### PyCharm

1. Install Ruff plugin
2. Enable "Ruff" in Settings → Tools → Ruff
3. Enable "Format on save"

## Pre-commit Hook (Optional)

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Then install: `pre-commit install`
