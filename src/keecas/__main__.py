"""
Entry point for running keecas as a module (python -m keecas).

This module defers all functionality to the CLI to avoid code duplication.
The lazy import pattern ensures heavy dependencies (SymPy, Pint) are only
loaded when actually needed.
"""

from .cli import main

if __name__ == "__main__":
    main()
