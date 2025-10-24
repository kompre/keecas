# Linting Quick Start Guide

## TL;DR - The 3 Commands You Need

```bash
# 1. Auto-fix code style (adds trailing commas automatically)
uv run ruff check --fix src/ tests/

# 2. Check docstring examples
uv run python scripts/lint_docstring_code.py src/keecas/*.py

# 3. Run tests
uv run pytest tests/
```

---

## What Does Each Command Do?

### 1. Auto-fix code style
```bash
uv run ruff check --fix src/ tests/
```

**What it does:**
- Automatically adds missing trailing commas
- Fixes import order
- Removes unused imports
- Fixes whitespace
- And more...

**Example:**
```python
# Before:
my_list = [
    1,
    2,
    3  # ❌ Missing comma
]

# After running the command:
my_list = [
    1,
    2,
    3,  # ✅ Comma added automatically
]
```

---

### 2. Check docstring examples
```bash
uv run python scripts/lint_docstring_code.py src/keecas/*.py
```

**What it does:**
- Checks code inside your docstrings (the `{python}` blocks)
- Reports missing trailing commas
- Reports unused imports/variables

**Output example:**
```
src\keecas\pipe_command.py:87: Docstring code block has issues:
COM812 Trailing comma missing
  --> line 8
  |
8 |     A_load: 20*u.cm**2
  |                       ^
```

**How to fix:**
- Open the file at the line number shown
- Add the missing comma manually
- **Note:** This doesn't auto-fix because docstrings are complex

---

### 3. Run tests
```bash
uv run pytest tests/
```

**What it does:**
- Runs all 158 tests
- Makes sure your changes didn't break anything

---

## VS Code Users (EASIEST METHOD)

**Step 1:** Install the Ruff extension in VS Code
- Open VS Code
- Go to Extensions (Ctrl+Shift+X)
- Search for "Ruff"
- Click Install

**Step 2:** It's already configured!
- The `.vscode/settings.json` file is already set up
- Now when you save a file (Ctrl+S), it automatically:
  - Adds trailing commas
  - Fixes imports
  - Formats code

**You don't need to run any commands manually!**

---

## Optional: Makefile Shortcuts

If you have `make` installed, you can use short commands:

| Short Command | Full Command |
|---------------|--------------|
| `make fix` | `uv run ruff check --fix src/ tests/` |
| `make lint-docs` | `uv run python scripts/lint_docstring_code.py src/keecas/*.py` |
| `make test` | `uv run pytest tests/` |
| `make check` | Runs all three above |

**Don't have `make`?** Just use the full commands - they work the same!

---

## Common Questions

### Q: Do I need to run these every time?

**For regular code:** Use VS Code auto-format on save (easiest)
**For docstrings:** Run the check before committing changes

### Q: What if I don't use VS Code?

Use the commands directly:
```bash
# Before committing:
uv run ruff check --fix src/ tests/
uv run python scripts/lint_docstring_code.py src/keecas/*.py
uv run pytest tests/
```

### Q: Can I auto-fix docstring code?

No - it's too complex to automate safely. Fix manually based on the reported line numbers.

### Q: What are trailing commas and why do we need them?

**With trailing comma:**
```python
my_list = [
    1,
    2,
    3,  # ← This comma
]
```

**Benefits:**
- Cleaner git diffs (only one line changes when you add items)
- No syntax errors when reordering
- Consistent code style

---

## Quick Workflow

```bash
# 1. Write your code
# ...

# 2. Fix style automatically
uv run ruff check --fix src/ tests/

# 3. Check docstrings
uv run python scripts/lint_docstring_code.py src/keecas/*.py

# 4. Fix any docstring issues manually

# 5. Run tests
uv run pytest tests/

# 6. Commit!
git add .
git commit -m "Your message"
```

**Or if using VS Code with Ruff extension:**
```bash
# 1. Write your code and save (auto-fixes on save!)
# 2. Check docstrings
uv run python scripts/lint_docstring_code.py src/keecas/*.py
# 3. Fix docstring issues manually
# 4. Run tests
uv run pytest tests/
# 5. Commit!
```
