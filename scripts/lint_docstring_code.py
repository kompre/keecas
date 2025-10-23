#!/usr/bin/env python3
"""
Extract and lint Python code from docstrings.

This script extracts code blocks from ```{python} sections in docstrings
and runs Ruff on them to check for style issues like missing trailing commas.
"""

import re
import sys
import tempfile
import subprocess
from pathlib import Path


def extract_python_blocks(file_path: Path) -> list[tuple[int, str]]:
    """Extract Python code blocks from docstrings.

    Args:
        file_path: Path to Python file to analyze

    Returns:
        List of (line_number, code) tuples for each Python block found
    """
    content = file_path.read_text(encoding='utf-8')

    # Match ```{python} ... ``` blocks, capturing the code
    # Pattern explanation:
    # ```{python}  - Opening fence
    # (.*?)        - Capture group for code (non-greedy)
    # ```          - Closing fence
    pattern = r'```\{python\}\n(.*?)\n\s+```'

    blocks = []
    for match in re.finditer(pattern, content, re.DOTALL | re.MULTILINE):
        code = match.group(1)
        # Calculate approximate line number
        line_num = content[:match.start()].count('\n') + 1
        blocks.append((line_num, code))

    return blocks


def lint_code_block(code: str, original_file: str, line_num: int) -> bool:
    """Lint a code block using Ruff.

    Args:
        code: Python code to lint
        original_file: Original file path for error messages
        line_num: Starting line number in original file

    Returns:
        True if linting passed, False if issues found
    """
    # Create temporary file with the code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        # Dedent the code (docstring examples are indented)
        lines = code.split('\n')
        min_indent = min((len(line) - len(line.lstrip())
                         for line in lines if line.strip()), default=0)
        dedented = '\n'.join(line[min_indent:] if line.strip() else line
                            for line in lines)
        f.write(dedented)
        temp_path = f.name

    try:
        # Run ruff on the temp file
        result = subprocess.run(
            ['uv', 'run', 'ruff', 'check', temp_path, '--select', 'COM,F401,F841'],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # Ruff found issues - reformat output with original file location
            print(f"\n{original_file}:{line_num}: Docstring code block has issues:")
            print(result.stdout)
            return False

        return True

    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)


def main(files: list[str], fix: bool = False) -> int:
    """Main entry point.

    Args:
        files: List of Python files to check
        fix: Whether to auto-fix issues

    Returns:
        Exit code (0 = success, 1 = issues found)
    """
    if fix:
        print("Auto-fix mode is not yet implemented.")
        print("Recommendation: Manually fix docstring code blocks based on Ruff suggestions.")
        print("\nNote: Automated fixing of code inside docstrings is complex due to:")
        print("  - Preserving indentation")
        print("  - Maintaining raw string formatting")
        print("  - Avoiding breaking LaTeX in docstrings")
        return 1

    all_passed = True

    for file_path_str in files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"Warning: {file_path} does not exist")
            continue

        blocks = extract_python_blocks(file_path)

        if not blocks:
            continue

        print(f"\nChecking {len(blocks)} code block(s) in {file_path}...")

        for line_num, code in blocks:
            if not lint_code_block(code, str(file_path), line_num):
                all_passed = False

    return 0 if all_passed else 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: lint_docstring_code.py [--fix] <file1.py> [file2.py ...]")
        print("\nChecks Python code blocks in docstrings for style issues.")
        print("\nOptions:")
        print("  --fix    Auto-fix issues (not yet implemented)")
        sys.exit(1)

    args = sys.argv[1:]
    fix_mode = '--fix' in args
    if fix_mode:
        args.remove('--fix')

    sys.exit(main(args, fix=fix_mode))
