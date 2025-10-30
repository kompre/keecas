# Linting Guide

This project uses **Ruff** for fast, comprehensive Python linting and formatting.

## Quick Reference

### The 3 Essential Commands

```bash
# 1. Auto-fix code style (adds trailing commas, fixes imports, etc.)
uv run ruff check --fix src/ tests/

# 2. Check docstring examples
uv run python scripts/lint_docstring_code.py src/keecas/*.py

# 3. Run tests
uv run pytest tests/
```

---

## VS Code Setup (Recommended)

**Easiest method: Auto-fix on save**

1. Install the Ruff extension in VS Code
   - Open Extensions (Ctrl+Shift+X)
   - Search for "Ruff"
   - Click Install

2. Configuration is already set up
   - The `.vscode/settings.json` file contains all settings
   - Auto-fixes on save (Ctrl+S):
     - Adds trailing commas
     - Fixes imports
     - Formats code

**With VS Code, you only need to run docstring checks and tests manually.**

---

## What Each Command Does

### 1. Auto-fix code style

```bash
uv run ruff check --fix src/ tests/
```

**Automatically fixes:**
- Missing trailing commas
- Import order
- Unused imports
- Whitespace issues
- And more...

**Example:**
```python
# Before:
my_list = [
    1,
    2,
    3  # Missing comma
]

# After:
my_list = [
    1,
    2,
    3,  # Comma added automatically
]
```

### 2. Check docstring examples

```bash
uv run python scripts/lint_docstring_code.py src/keecas/*.py
```

**What it does:**
- Checks code inside docstrings (the `{python}` blocks)
- Reports missing trailing commas
- Reports unused imports/variables

**Example output:**
```
src\keecas\pipe_command.py:87: Docstring code block has issues:
COM812 Trailing comma missing
  --> line 8
  |
8 |     A_load: 20*u.cm**2
  |                       ^
```

**How to fix:**
- Open the file at the reported line number
- Add the missing comma manually
- **Note:** Docstring code is not auto-fixed for safety

### 3. Run tests

```bash
uv run pytest tests/
```

**What it does:**
- Runs all 159 tests
- Validates your changes didn't break anything
- Required before committing

---

## Typical Workflow

### With VS Code (Recommended)

```bash
# 1. Write code and save (auto-fixes on save)

# 2. Check docstrings before committing
uv run python scripts/lint_docstring_code.py src/keecas/*.py

# 3. Fix any docstring issues manually

# 4. Run tests
uv run pytest tests/

# 5. Commit
git add .
git commit -m "Your message"
```

### Without VS Code

```bash
# 1. Write your code

# 2. Fix style automatically
uv run ruff check --fix src/ tests/

# 3. Check docstrings
uv run python scripts/lint_docstring_code.py src/keecas/*.py

# 4. Fix any docstring issues manually

# 5. Run tests
uv run pytest tests/

# 6. Commit
git add .
git commit -m "Your message"
```

---

## Understanding Trailing Commas

### Why trailing commas?

**With trailing comma:**
```python
my_list = [
    1,
    2,
    3,  # This comma
]
```

**Benefits:**
- Cleaner git diffs (only one line changes when adding items)
- No syntax errors when reordering items
- Consistent code style across the project

**Example git diff:**

Without trailing comma:
```diff
  my_list = [
      1,
      2,
-     3
+     3,
+     4
  ]
```

With trailing comma:
```diff
  my_list = [
      1,
      2,
      3,
+     4,
  ]
```

---

## CI/CD Integration

### Pre-commit Hooks

The project uses pre-commit hooks (installed via `bash scripts/install-hooks.sh`):
- Validates docstrings (fast check, < 1s)
- Renders Quarto notebooks (for `examples/quarto_example/`)
- **Note:** Tests run only in CI, not in pre-commit (for speed)

### GitHub Actions

When you create a PR to main, CI automatically runs:
- **Linting:** `uv run ruff check src/ tests/`
- **Tests:** `uv run pytest tests -v`
- **Docstring validation:** `uv run python scripts/validate_docstrings.py`

All checks must pass before merging.

---

## Ruff Configuration

The project uses Ruff for linting and formatting. Configuration is in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "COM"]
ignore = []

[tool.ruff.lint.isort]
known-first-party = ["keecas"]
```

**Key rules:**
- `E`: PEP 8 errors
- `F`: Pyflakes (unused imports, undefined names)
- `W`: PEP 8 warnings
- `I`: Import sorting
- `COM`: Trailing comma enforcement

---

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

---

## IDE Integration

### VS Code

The `.vscode/settings.json` file is already configured:

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

Just install the Ruff extension to enable auto-fix on save.

### PyCharm

1. Install Ruff plugin
2. Enable "Ruff" in Settings → Tools → Ruff
3. Enable "Format on save"

---

## Common Questions

### Q: Do I need to run these every time?

**For regular code:**
- With VS Code Ruff extension: Auto-fixes on save
- Without VS Code: Run `uv run ruff check --fix` before committing

**For docstrings:**
- Run the check before committing changes

**For tests:**
- Run locally before pushing (optional, CI will run them)
- Required to pass in CI before merging

### Q: Can I auto-fix docstring code?

No - docstring code blocks are too complex to automate safely. Fix manually based on the reported line numbers.

### Q: What if the linter and tests pass but CI fails?

This can happen if:
- You're not using the latest dependencies (`uv sync`)
- Local environment differs from CI (Ubuntu 24.04)
- Pre-commit hooks were skipped (`--no-verify`)

Always run `uv sync` after pulling changes.

### Q: How do I skip pre-commit hooks?

```bash
git commit --no-verify
```

Not recommended unless you're committing non-code files or have a specific reason.

---

## Troubleshooting

### Ruff command not found

Make sure you've synced dependencies:
```bash
uv sync
```

### VS Code not auto-fixing

1. Check Ruff extension is installed
2. Verify `.vscode/settings.json` exists
3. Reload VS Code window (Ctrl+Shift+P → "Reload Window")

### Docstring linter fails on Windows

Use forward slashes or escape backslashes in file paths:
```bash
uv run python scripts/lint_docstring_code.py src/keecas/*.py
```

### CI fails but local tests pass

1. Run `uv sync` to update dependencies
2. Check locale installation (for internationalization tests)
3. Verify Python version matches CI (3.13 from `.python-version`)

---

## Additional Resources

- **Ruff documentation:** https://docs.astral.sh/ruff/
- **VS Code Ruff extension:** https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff
- **Project testing guide:** See `tests/` directory
- **Docstring guidelines:** See [docs/DOCSTRINGS.md](docs/DOCSTRINGS.md)
- **Contributing guide:** See [CONTRIBUTING.md](../CONTRIBUTING.md)
