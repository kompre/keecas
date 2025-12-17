"""
Lightweight CLI entry point for Keecas that avoids loading heavy dependencies.

This module serves as a fast entry point that only imports the main keecas package
when actually needed, avoiding the overhead of loading SymPy and Pint for simple
commands like --version.
"""

import sys


def get_version() -> str:
    """Get keecas version without loading the package."""
    try:
        from importlib.metadata import version
    except ImportError:
        from importlib_metadata import version

    try:
        return version("keecas")
    except Exception:
        return "unknown"


def show_quick_help() -> None:
    """Show basic help without loading heavy dependencies."""
    keecas_version = get_version()
    print(f"""usage: keecas [-h] [--version] {{edit,config}} ...

Keecas v{keecas_version} - Command-line interface

positional arguments:
  {{edit,config}}  Main commands
    edit         Launch Jupyter server with keecas templates
    config       Configuration management

options:
  -h, --help     show this help message and exit
  --version      show program's version number and exit

For detailed help on subcommands, use: keecas <command> --help
""")


def main() -> None:
    """Main CLI entry point with lazy imports."""
    # Fast path for version check
    if len(sys.argv) == 2 and sys.argv[1] in ("--version", "-V"):
        print(f"keecas {get_version()}")
        sys.exit(0)

    # Fast path for help (no arguments or -h/--help)
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help")):
        show_quick_help()
        sys.exit(0 if len(sys.argv) == 2 else 1)

    # For all other commands, import and delegate to the full CLI
    # This will load the keecas package with SymPy/Pint for actual work
    from keecas.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
