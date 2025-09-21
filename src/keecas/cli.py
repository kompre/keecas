"""
Command-line interface for Keecas configuration management.

Provides commands for managing global and local configuration files.
"""

import argparse
import sys
import subprocess
import os
from pathlib import Path
import toml
try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version

from .config import get_config_manager


def get_version():
    """Get the current version of keecas."""
    try:
        return version("keecas")
    except Exception:
        return "unknown"


def get_editor():
    """Get the preferred text editor from environment variables."""
    return os.environ.get('EDITOR') or os.environ.get('VISUAL') or 'nano'


def get_system_editor():
    """Get the system default editor command for opening files."""
    import platform
    system = platform.system().lower()

    if system == "linux":
        return "xdg-open"
    elif system == "darwin":  # macOS
        return "open"
    elif system == "windows":
        return "start"
    else:
        # Fallback - try xdg-open first (works on many Unix-like systems)
        return "xdg-open"


def open_with_system_editor(file_path):
    """Open a file with the system default editor."""
    system_editor = get_system_editor()
    try:
        if system_editor == "start":
            # Windows start command has different syntax
            subprocess.run([system_editor, "", str(file_path)], check=True, shell=True)
        else:
            subprocess.run([system_editor, str(file_path)], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error: Could not open file with system editor '{system_editor}': {e}")
        return False


def cmd_init(args):
    """Initialize a new configuration file."""
    config_manager = get_config_manager()
    # Handle mutually exclusive group default
    global_config = getattr(args, 'global_config', False)

    success = config_manager.init_config(
        global_config=global_config,
        force=args.force
    )

    if success:
        config_type = "global" if global_config else "local"
        config_path = config_manager.get_config_path(global_config)
        print(f"Initialized {config_type} configuration file: {config_path}")
    else:
        sys.exit(1)


def cmd_edit(args):
    """Edit configuration file in the user's preferred editor."""
    config_manager = get_config_manager()
    # Handle mutually exclusive group default
    global_config = getattr(args, 'global_config', False)
    config_path = config_manager.get_config_path(global_config)

    # Create file if it doesn't exist
    if not config_path.exists():
        print(f"Configuration file doesn't exist: {config_path}")
        create = input("Create it now? [y/N]: ").lower().strip()
        if create in ('y', 'yes'):
            if not config_manager.init_config(global_config=global_config, force=False):
                sys.exit(1)
        else:
            print("Cancelled.")
            sys.exit(1)

    # Open in editor
    editor = get_editor()
    try:
        subprocess.run([editor, str(config_path)], check=True)

        # Reload configuration after editing
        config_manager.load_configs()
        print(f"Configuration reloaded from: {config_path}")
    except subprocess.CalledProcessError:
        print(f"Error: Could not open editor '{editor}'")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Editor '{editor}' not found")
        print("Set the EDITOR environment variable to your preferred editor")
        sys.exit(1)


def cmd_open(args):
    """Open configuration file with the system default editor."""
    config_manager = get_config_manager()
    # Handle mutually exclusive group default
    global_config = getattr(args, 'global_config', False)
    config_path = config_manager.get_config_path(global_config)

    # Create file if it doesn't exist
    if not config_path.exists():
        print(f"Configuration file doesn't exist: {config_path}")
        create = input("Create it now? [y/N]: ").lower().strip()
        if create in ('y', 'yes'):
            if not config_manager.init_config(global_config=global_config, force=False):
                sys.exit(1)
        else:
            print("Cancelled.")
            sys.exit(1)

    # Open with system editor
    config_type = "global" if global_config else "local"
    print(f"Opening {config_type} configuration file with system editor...")

    if open_with_system_editor(config_path):
        print(f"Opened: {config_path}")
        print("Note: Configuration will be reloaded automatically on next keecas command.")
    else:
        print(f"Failed to open {config_path}")
        print(f"You can manually edit the file at: {config_path}")
        sys.exit(1)


def cmd_show(args):
    """Show current configuration."""
    config_manager = get_config_manager()

    if args.global_config:
        config_dict = config_manager.show_config(global_config=True)
        print("=== Global Configuration ===")
        if config_dict:
            print(toml.dumps(config_dict))
        else:
            print("No global configuration file found.")

    elif args.local:
        config_dict = config_manager.show_config(global_config=False)
        print("=== Local Configuration ===")
        if config_dict:
            print(toml.dumps(config_dict))
        else:
            print("No local configuration file found.")

    else:
        # Show merged configuration
        config_dict = config_manager.show_config(global_config=None)
        print("=== Merged Configuration (Local + Global + Defaults) ===")
        if config_dict:
            print(toml.dumps(config_dict))
        else:
            print("No configuration found (using defaults only).")

    # Show loaded files
    loaded_files = config_manager.get_loaded_files()
    if loaded_files:
        print(f"\nLoaded from: {', '.join(loaded_files)}")


def cmd_path(args):
    """Show path to configuration files."""
    config_manager = get_config_manager()

    if args.global_config:
        path = config_manager.get_config_path(global_config=True)
        exists = "✓" if path.exists() else "✗"
        print(f"Global config: {path} {exists}")

    elif args.local:
        path = config_manager.get_config_path(global_config=False)
        exists = "✓" if path.exists() else "✗"
        print(f"Local config:  {path} {exists}")

    else:
        # Show both
        global_path = config_manager.get_config_path(global_config=True)
        local_path = config_manager.get_config_path(global_config=False)

        global_exists = "✓" if global_path.exists() else "✗"
        local_exists = "✓" if local_path.exists() else "✗"

        print(f"Global config: {global_path} {global_exists}")
        print(f"Local config:  {local_path} {local_exists}")


def cmd_reset(args):
    """Reset configuration to defaults."""
    config_manager = get_config_manager()
    # Handle mutually exclusive group default
    global_config = getattr(args, 'global_config', False)
    config_type = "global" if global_config else "local"

    if not args.force:
        confirm = input(f"Reset {config_type} configuration to defaults? [y/N]: ").lower().strip()
        if confirm not in ('y', 'yes'):
            print("Cancelled.")
            return

    success = config_manager.reset_config(global_config=global_config)
    if not success:
        sys.exit(1)


def create_parser():
    """Create and configure the argument parser."""
    keecas_version = get_version()
    parser = argparse.ArgumentParser(
        description=f"Keecas v{keecas_version} - Command-line interface",
        prog="keecas"
    )

    # Add version argument
    parser.add_argument('--version', action='version', version=f'keecas {keecas_version}')

    # Add main subparsers
    main_subparsers = parser.add_subparsers(dest='main_command', help='Main commands')

    # Config subcommand
    config_parser = main_subparsers.add_parser('config', help='Configuration management')
    config_subparsers = config_parser.add_subparsers(dest='command', help='Configuration commands')

    # Init command
    init_parser = config_subparsers.add_parser('init', help='Initialize a new configuration file')
    init_group = init_parser.add_mutually_exclusive_group()
    init_group.add_argument('--global', dest='global_config', action='store_true',
                          help='Initialize global configuration file')
    init_group.add_argument('--local', dest='local_config', action='store_true',
                          help='Initialize local configuration file (default)')
    init_parser.add_argument('--force', action='store_true',
                           help='Overwrite existing configuration file')
    init_parser.set_defaults(func=cmd_init)

    # Edit command
    edit_parser = config_subparsers.add_parser('edit', help='Edit configuration file with terminal editor')
    edit_group = edit_parser.add_mutually_exclusive_group()
    edit_group.add_argument('--global', dest='global_config', action='store_true',
                          help='Edit global configuration file')
    edit_group.add_argument('--local', dest='local_config', action='store_true',
                          help='Edit local configuration file (default)')
    edit_parser.set_defaults(func=cmd_edit)

    # Open command
    open_parser = config_subparsers.add_parser('open', help='Open configuration file with system default editor')
    open_group = open_parser.add_mutually_exclusive_group()
    open_group.add_argument('--global', dest='global_config', action='store_true',
                          help='Open global configuration file')
    open_group.add_argument('--local', dest='local_config', action='store_true',
                          help='Open local configuration file (default)')
    open_parser.set_defaults(func=cmd_open)

    # Show command
    show_parser = config_subparsers.add_parser('show', help='Show current configuration')
    show_group = show_parser.add_mutually_exclusive_group()
    show_group.add_argument('--global', dest='global_config', action='store_true',
                          help='Show only global configuration')
    show_group.add_argument('--local', action='store_true',
                          help='Show only local configuration')
    show_parser.set_defaults(func=cmd_show)

    # Path command
    path_parser = config_subparsers.add_parser('path', help='Show configuration file paths')
    path_group = path_parser.add_mutually_exclusive_group()
    path_group.add_argument('--global', dest='global_config', action='store_true',
                          help='Show only global configuration path')
    path_group.add_argument('--local', action='store_true',
                          help='Show only local configuration path')
    path_parser.set_defaults(func=cmd_path)

    # Reset command
    reset_parser = config_subparsers.add_parser('reset', help='Reset configuration to defaults')
    reset_group = reset_parser.add_mutually_exclusive_group()
    reset_group.add_argument('--global', dest='global_config', action='store_true',
                           help='Reset global configuration file')
    reset_group.add_argument('--local', dest='local_config', action='store_true',
                           help='Reset local configuration file (default)')
    reset_parser.add_argument('--force', action='store_true',
                            help='Reset without confirmation')
    reset_parser.set_defaults(func=cmd_reset)

    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle main command routing
    if args.main_command == 'config':
        if not hasattr(args, 'func'):
            parser.print_help()
            sys.exit(1)
        try:
            args.func(args)
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # No main command provided
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()