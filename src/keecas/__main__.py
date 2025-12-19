"""
Entry point for running keecas as a module (python -m keecas).

This module defers all functionality to the full CLI implementation to avoid
code duplication. The CLI module (cli.py) implements lazy imports that avoid
loading heavy dependencies (SymPy, Pint) until needed.
"""

from keecas.cli import main

if __name__ == "__main__":
    main()
