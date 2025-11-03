#!/usr/bin/env python3
"""Validate that changed files have docstrings for public API.

This script performs lightweight validation suitable for pre-commit hooks:
- Checks that public functions and classes have docstrings
- Only validates presence, not quality
- Runs quickly enough for pre-commit workflow

For comprehensive docstring guidelines, see DOCSTRINGS.md.
"""

import ast
import subprocess
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows (fixes emoji encoding issues)
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def get_changed_files() -> list[str]:
    """Get staged Python files from git.

    Returns:
        List of file paths for staged Python files in src/
    """
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return []

    files = result.stdout.strip().split("\n")
    return [f for f in files if f.startswith("src/") and f.endswith(".py")]


def check_file_docstrings(filepath: Path) -> list[str]:
    """Check that public functions/classes in file have docstrings.

    Args:
        filepath: Path to Python file to check

    Returns:
        List of names for public API items missing docstrings
    """
    missing = []

    try:
        with open(filepath, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"⚠️  {filepath}: Failed to parse ({e})")
        return []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            # Skip private/internal API (starts with _)
            if not node.name.startswith("_"):
                if not ast.get_docstring(node):
                    missing.append(node.name)

    return missing


def main() -> int:
    """Validate docstrings in changed files.

    Returns:
        Exit code: 0 if all files valid, 1 if missing docstrings
    """
    changed_files = get_changed_files()

    if not changed_files:
        # No Python files changed
        return 0

    has_errors = False
    for filepath in changed_files:
        path = Path(filepath)
        if not path.exists():
            continue

        missing = check_file_docstrings(path)
        if missing:
            print(f"⚠️  {filepath}: Missing docstrings for: {', '.join(missing)}")
            has_errors = True

    if has_errors:
        print("\n💡 Tip: Add Google-style docstrings to public functions/classes")
        print("📖 See DOCSTRINGS.md for comprehensive guidelines")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
