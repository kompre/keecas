"""
Command-line interface for Keecas configuration management.

Provides commands for managing global and local configuration files.
"""

import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

import toml

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version

# Lazy import to avoid loading heavy dependencies (SymPy, Pint) at startup
# from .config.manager import get_config_manager  # Moved to function level


def _get_config_manager():
    """Lazy import of config manager to avoid startup overhead."""
    from .config.manager import get_config_manager

    return get_config_manager()


def get_version() -> str:
    """Get the current version of keecas."""
    try:
        return version("keecas")
    except Exception:
        return "unknown"


def get_editor() -> str:
    """Get the preferred text editor from environment variables."""
    return os.environ.get("EDITOR") or os.environ.get("VISUAL") or "nano"


def get_system_editor() -> str:
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


def open_with_system_editor(file_path: Path | str) -> bool:
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


def find_free_port(start_port: int = 8888, max_attempts: int = 10) -> int | None:
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            continue
    return None


def get_templates_dir() -> Path:
    """Get the templates directory path."""
    # Get the package installation directory
    import keecas

    package_dir = Path(keecas.__file__).parent
    # Look for templates in parent directory (for development)
    templates_dir = package_dir.parent.parent / "templates"
    if templates_dir.exists():
        return templates_dir

    # Look for templates in package directory (for installed package)
    templates_dir = package_dir / "templates"
    if templates_dir.exists():
        return templates_dir

    # Fallback - try relative to current directory
    templates_dir = Path("templates")
    return templates_dir


def generate_untitled_name(work_dir: Path | str) -> str:
    """Generate an available untitled-N.ipynb filename."""
    work_dir = Path(work_dir)
    counter = 1
    while True:
        filename = f"untitled-{counter}.ipynb"
        if not (work_dir / filename).exists():
            return filename
        counter += 1


def copy_template_to_workdir(
    template_name: str,
    work_dir: Path | str,
    target_filename: str | None = None,
) -> Path:
    """Copy a template notebook to the working directory."""
    templates_dir = get_templates_dir()
    template_path = templates_dir / f"{template_name}.ipynb"

    if not template_path.exists():
        raise FileNotFoundError(f"Template '{template_name}' not found at {template_path}")

    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    # Use provided filename or generate one
    if target_filename:
        target_name = target_filename
    else:
        # Copy template with a unique name if file exists
        target_name = f"{template_name}.ipynb"
        counter = 1
        while (work_dir / target_name).exists():
            target_name = f"{template_name}_{counter}.ipynb"
            counter += 1

    target_path = work_dir / target_name
    shutil.copy2(template_path, target_path)
    return target_path


def check_jupyter_available() -> bool:
    """Check if Jupyter is available."""
    try:
        subprocess.run(
            [sys.executable, "-m", "jupyter", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_jupyterlab_available() -> bool:
    """Check if JupyterLab is available."""
    try:
        subprocess.run(
            [sys.executable, "-m", "jupyter", "lab", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize a new configuration file."""
    config_manager = _get_config_manager()
    # Handle mutually exclusive group default
    global_config = getattr(args, "global_config", False)

    success = config_manager.init_config(
        global_config=global_config,
        force=args.force,
        comment_style=getattr(args, "comment_style", "##"),
    )

    if success:
        config_type = "global" if global_config else "local"
        config_path = config_manager.get_config_path(global_config)
        print(f"Initialized {config_type} configuration file: {config_path}")
        if hasattr(args, "comment_style") and args.comment_style != "##":
            print(f"Using comment style: '{args.comment_style}'")
    else:
        sys.exit(1)


def cmd_config_edit(args: argparse.Namespace) -> None:
    """Edit configuration file in the user's preferred editor."""
    config_manager = _get_config_manager()
    # Handle mutually exclusive group default
    global_config = getattr(args, "global_config", False)
    config_path = config_manager.get_config_path(global_config)

    # Create file if it doesn't exist
    if not config_path.exists():
        print(f"Configuration file doesn't exist: {config_path}")
        create = input("Create it now? [y/N]: ").lower().strip()
        if create in ("y", "yes"):
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


def cmd_edit(args: argparse.Namespace) -> None:
    """Launch Jupyter server with keecas notebook templates."""
    # Handle template listing
    if getattr(args, "list_templates", False):
        templates_dir = get_templates_dir()
        if templates_dir.exists():
            templates = [f.stem for f in templates_dir.glob("*.ipynb")]
            if templates:
                print("Available templates:")
                for template in sorted(templates):
                    if template == "minimal":
                        print(f"  {template} (default) - Basic keecas setup")
                    elif template == "quickstart":
                        print(f"  {template} - Comprehensive examples and patterns")
                    else:
                        print(f"  {template}")
            else:
                print("No templates found.")
        else:
            print("Templates directory not found.")
        return

    # Default to JupyterLab unless --no-lab is specified
    use_lab = not getattr(args, "no_lab", False)

    if use_lab:
        if not check_jupyterlab_available():
            print("Error: JupyterLab is not available.")
            print("Please install JupyterLab: pip install jupyterlab")
            print("Falling back to classic Jupyter Notebook...")
            use_lab = False
            if not check_jupyter_available():
                print("Error: Jupyter is not available either.")
                print("Please install Jupyter: pip install jupyter")
                sys.exit(1)
    else:
        if not check_jupyter_available():
            print("Error: Jupyter is not available.")
            print("Please install Jupyter: pip install jupyter")
            sys.exit(1)

    # Find free port
    port = find_free_port(args.port)
    if port is None:
        print(f"Error: Could not find a free port starting from {args.port}")
        sys.exit(1)

    # Set up working directory
    use_temp = getattr(args, "temp", False)
    temp_dir = None

    if use_temp:
        # Create temporary directory for session
        temp_dir = tempfile.mkdtemp(prefix="keecas_session_")
        work_dir = Path(temp_dir)
        print(f"Created temporary session directory: {work_dir}")
    else:
        work_dir = Path(args.dir).resolve()
        work_dir.mkdir(parents=True, exist_ok=True)

    # Handle file argument and template creation
    notebook_path = None
    target_file = getattr(args, "file", None)

    if target_file:
        # File specified - either open existing or create new
        target_path = work_dir / target_file

        if target_path.exists():
            # File exists - open it directly
            notebook_path = target_path
            print(f"Opening existing notebook: {notebook_path}")
        else:
            # File doesn't exist - create from template
            template_name = (
                args.template if hasattr(args, "template") and args.template else "minimal"
            )
            try:
                notebook_path = copy_template_to_workdir(template_name, work_dir, target_file)
                print(f"Created notebook from template '{template_name}': {notebook_path}")
            except FileNotFoundError as e:
                print(f"Error: {e}")
                # List available templates
                templates_dir = get_templates_dir()
                if templates_dir.exists():
                    templates = [f.stem for f in templates_dir.glob("*.ipynb")]
                    if templates:
                        print(f"Available templates: {', '.join(templates)}")
                sys.exit(1)
    else:
        # No file specified - create with untitled name
        template_name = args.template if hasattr(args, "template") and args.template else "minimal"
        untitled_name = generate_untitled_name(work_dir)

        try:
            notebook_path = copy_template_to_workdir(template_name, work_dir, untitled_name)
            if template_name == "minimal":
                print(f"Created keecas notebook: {notebook_path}")
            else:
                print(f"Created notebook from template '{template_name}': {notebook_path}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            # List available templates
            templates_dir = get_templates_dir()
            if templates_dir.exists():
                templates = [f.stem for f in templates_dir.glob("*.ipynb")]
                if templates:
                    print(f"Available templates: {', '.join(templates)}")
            sys.exit(1)

    # Prepare Jupyter command (use sys.executable to ensure same Python environment)
    if use_lab:
        jupyter_cmd = [
            sys.executable,
            "-m",
            "jupyter",
            "lab",
            "--port",
            str(port),
            "--notebook-dir",
            str(work_dir),
        ]
    else:
        jupyter_cmd = [
            sys.executable,
            "-m",
            "jupyter",
            "notebook",
            "--port",
            str(port),
            "--notebook-dir",
            str(work_dir),
        ]

    # Add file to open automatically if specified
    if notebook_path:
        relative_path = notebook_path.relative_to(work_dir)
        jupyter_cmd.extend(["--ServerApp.file_to_run", str(relative_path)])

    if not args.browser:
        jupyter_cmd.append("--no-browser")

    # Add token configuration for security
    if hasattr(args, "token") and args.token:
        jupyter_cmd.extend(["--IdentityProvider.token", args.token])
    else:
        # Disable authentication for local development convenience
        jupyter_cmd.extend(["--IdentityProvider.token="])

    interface_name = "JupyterLab" if use_lab else "Jupyter Notebook"
    print(f"Starting {interface_name} server on port {port}...")
    if use_temp:
        print(f"Temporary session directory: {work_dir}")
        print("Note: Files will be auto-cleaned when server stops")
    else:
        print(f"Working directory: {work_dir}")

    # Start Jupyter server
    try:
        # Start server with output going to terminal to avoid buffer deadlock
        # Using stdout=None, stderr=None allows Jupyter to write directly to terminal
        # This prevents the subprocess from hanging when pipe buffers fill up
        process = subprocess.Popen(
            jupyter_cmd,
            stdout=None,
            stderr=None,
        )

        # Wait a moment for server to start
        time.sleep(2)

        # Check if process is still running
        if process.poll() is not None:
            print("Error: Jupyter server failed to start")
            print("Check the output above for error details")
            sys.exit(1)

        # Construct session URLs
        interface_name = "JupyterLab" if use_lab else "Jupyter Notebook"
        if use_lab:
            session_url = f"http://localhost:{port}/lab"
        else:
            session_url = f"http://localhost:{port}/tree"

        # Build notebook-specific URL if applicable
        notebook_url = None
        if notebook_path:
            relative_path = notebook_path.relative_to(work_dir)
            path_str = str(relative_path).replace("\\", "/")  # Windows compatibility
            if use_lab:
                notebook_url = f"{session_url}/tree/{quote(path_str)}"
            else:
                notebook_url = f"{session_url}/{quote(path_str)}"

        # Display URLs prominently
        print()  # Blank line for readability
        if args.browser:
            print(f"{interface_name} opening in browser...")
            if notebook_path:
                print(f"Notebook: {notebook_path.name}")
            print()
            print(f"Session URL: {session_url}")
            if notebook_url:
                print(f"Direct link: {notebook_url}")
        else:
            print(f"{interface_name} server started (no browser)")
            print()
            print("Copy this URL to your browser:")
            print(f"  {session_url}")
            if notebook_url:
                print()
                print("Direct notebook link:")
                print(f"  {notebook_url}")
            print()

        print(f"Server PID: {process.pid}")
        print("Press Ctrl+C to stop the server")

        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            interface_name = "JupyterLab" if use_lab else "Jupyter Notebook"
            print(f"\nStopping {interface_name} server...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"Force killing {interface_name} server...")
                process.kill()

            # Clean up temporary directory if used
            if temp_dir and Path(temp_dir).exists():
                print(f"Cleaning up temporary session: {temp_dir}")
                shutil.rmtree(temp_dir, ignore_errors=True)

            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Wait for process to complete
        try:
            process.wait()
        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)

    except FileNotFoundError:
        interface_name = "JupyterLab" if use_lab else "Jupyter Notebook"
        print(f"Error: {interface_name} command not found")
        if use_lab:
            print("Please install JupyterLab: pip install jupyterlab")
        else:
            print("Please install Jupyter: pip install jupyter")
        sys.exit(1)
    except Exception as e:
        interface_name = "JupyterLab" if use_lab else "Jupyter Notebook"
        print(f"Error starting {interface_name} server: {e}")
        sys.exit(1)


def cmd_open(args: argparse.Namespace) -> None:
    """Open configuration file with the system default editor."""
    config_manager = _get_config_manager()
    # Handle mutually exclusive group default
    global_config = getattr(args, "global_config", False)
    config_path = config_manager.get_config_path(global_config)

    # Create file if it doesn't exist
    if not config_path.exists():
        print(f"Configuration file doesn't exist: {config_path}")
        create = input("Create it now? [y/N]: ").lower().strip()
        if create in ("y", "yes"):
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


def cmd_show(args: argparse.Namespace) -> None:
    """Show current configuration."""
    config_manager = _get_config_manager()

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


def cmd_path(args: argparse.Namespace) -> None:
    """Show path to configuration files."""
    config_manager = _get_config_manager()

    if args.global_config:
        path = config_manager.get_config_path(global_config=True)
        exists = "[exists]" if path.exists() else "[missing]"
        print(f"Global config: {path} {exists}")

    elif args.local:
        path = config_manager.get_config_path(global_config=False)
        exists = "[exists]" if path.exists() else "[missing]"
        print(f"Local config:  {path} {exists}")

    else:
        # Show both
        global_path = config_manager.get_config_path(global_config=True)
        local_path = config_manager.get_config_path(global_config=False)

        global_exists = "[exists]" if global_path.exists() else "[missing]"
        local_exists = "[exists]" if local_path.exists() else "[missing]"

        print(f"Global config: {global_path} {global_exists}")
        print(f"Local config:  {local_path} {local_exists}")


def cmd_reset(args: argparse.Namespace) -> None:
    """Reset configuration to defaults."""
    config_manager = _get_config_manager()
    # Handle mutually exclusive group default
    global_config = getattr(args, "global_config", False)
    config_type = "global" if global_config else "local"

    if not args.force:
        confirm = input(f"Reset {config_type} configuration to defaults? [y/N]: ").lower().strip()
        if confirm not in ("y", "yes"):
            print("Cancelled.")
            return

    success = config_manager.reset_config(global_config=global_config)
    if not success:
        sys.exit(1)


def cmd_config_version(args: argparse.Namespace) -> None:
    """Show configuration version information."""
    from .config.migration import ConfigMigration
    from .config.schema import get_current_schema_version

    config_manager = _get_config_manager()
    global_config = getattr(args, "global_config", False)

    # Determine which config file to check
    config_path = (
        config_manager._global_config_path if global_config else config_manager._local_config_path
    )

    if not config_path.exists():
        config_type = "global" if global_config else "local"
        print(f"{config_type.capitalize()} config file not found: {config_path}")
        print(f"Create it with: keecas config init {'--global' if global_config else '--local'}")
        sys.exit(1)

    # Extract metadata from header comments
    metadata = config_manager._extract_metadata_from_comments(config_path)

    print(f"Config file: {config_path}")
    print(f"Schema version: {metadata.get('config_version', 'unknown')}")
    print(f"Generated by: keecas v{metadata.get('keecas_version', 'unknown')}")
    if metadata.get("generated_at"):
        print(f"Created: {metadata['generated_at']}")
    if metadata.get("last_modified"):
        print(f"Modified: {metadata['last_modified']}")

    current_schema = get_current_schema_version()
    config_schema = metadata.get("config_version", "0.1.0")

    if ConfigMigration.needs_migration(config_schema, current_schema):
        print(f"\nWARNING: Migration available: {config_schema} -> {current_schema}")
        print("   Run `keecas config migrate` to update")
    else:
        print(f"\nSUCCESS: Config is up to date (latest: {current_schema})")


def cmd_migrate(args: argparse.Namespace) -> None:
    """Manually trigger configuration migration."""
    import shutil

    from .config.migration import ConfigMigration
    from .config.schema import get_current_schema_version

    config_manager = _get_config_manager()
    global_config = getattr(args, "global_config", False)
    dry_run = getattr(args, "dry_run", False)

    # Determine which config file to migrate
    config_path = (
        config_manager._global_config_path if global_config else config_manager._local_config_path
    )

    if not config_path.exists():
        config_type = "global" if global_config else "local"
        print(f"{config_type.capitalize()} config file not found: {config_path}")
        print(f"Create it with: keecas config init {'--global' if global_config else '--local'}")
        sys.exit(1)

    # Extract metadata and check if migration needed
    metadata = config_manager._extract_metadata_from_comments(config_path)
    config_version = metadata.get("config_version", "0.1.0")
    current_version = get_current_schema_version()

    if not ConfigMigration.needs_migration(config_version, current_version):
        print(f"SUCCESS: Config is already up to date (version {config_version})")
        return

    print(f"Config migration: {config_version} -> {current_version}")

    if dry_run:
        print("\nDRY RUN MODE - No changes will be made\n")

        # Load and migrate without saving
        with open(config_path, encoding="utf-8") as f:
            config_data = toml.load(f)

        try:
            migrated_data = ConfigMigration.migrate(config_data, config_version, current_version)
            print("\nSUCCESS: Migration would succeed")
            print("\nMigrated configuration preview:")
            print(toml.dumps(migrated_data))
        except Exception as e:
            print(f"\nERROR: Migration would fail: {e}")
            sys.exit(1)

    else:
        # Actual migration
        # Backup old config
        backup_path = config_path.with_suffix(".toml.backup")
        shutil.copy(config_path, backup_path)
        print(f"Backup created: {backup_path}")

        # Load and migrate
        with open(config_path, encoding="utf-8") as f:
            config_data = toml.load(f)

        try:
            migrated_data = ConfigMigration.migrate(config_data, config_version, current_version)

            # Create a temporary config manager to save the migrated config
            from .config.manager import ConfigManager

            temp_config = ConfigManager.__new__(ConfigManager)
            temp_config._options = config_manager._options
            temp_config._save_config_file(config_path, created_at=metadata.get("generated_at"))

            print(f"SUCCESS: Config migrated successfully to {current_version}")

        except Exception as e:
            print(f"ERROR: Migration failed: {e}")
            print(f"   Restore from backup: {backup_path}")
            sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    keecas_version = get_version()
    parser = argparse.ArgumentParser(
        description=f"Keecas v{keecas_version} - Command-line interface",
        prog="keecas",
    )

    # Add version argument
    parser.add_argument("--version", action="version", version=f"keecas {keecas_version}")

    # Add main subparsers
    main_subparsers = parser.add_subparsers(dest="main_command", help="Main commands")

    # Edit command - Launch Jupyter server with templates
    edit_main_parser = main_subparsers.add_parser(
        "edit",
        help="Launch Jupyter server with keecas templates",
    )
    edit_main_parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Notebook file to open or create (default: untitled-N.ipynb)",
    )
    edit_main_parser.add_argument(
        "--port",
        type=int,
        default=8888,
        help="Port for Jupyter server (default: 8888)",
    )
    edit_main_parser.add_argument(
        "--dir",
        default=".",
        help="Working directory for notebooks (default: current directory)",
    )
    edit_main_parser.add_argument(
        "--template",
        help="Template notebook to create (default: minimal, options: quickstart)",
    )
    edit_main_parser.add_argument(
        "--no-browser",
        dest="browser",
        action="store_false",
        default=True,
        help="Don't open browser automatically",
    )
    edit_main_parser.add_argument(
        "--token",
        help="Security token for Jupyter server (default: disabled for local use)",
    )
    edit_main_parser.add_argument(
        "--no-lab",
        action="store_true",
        default=False,
        help="Use classic Jupyter Notebook instead of JupyterLab (default: JupyterLab)",
    )
    edit_main_parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List available templates and exit",
    )
    edit_main_parser.add_argument(
        "--temp",
        action="store_true",
        default=False,
        help="Create temporary notebook (auto-cleanup when server stops)",
    )
    edit_main_parser.set_defaults(func=cmd_edit)

    # Config subcommand
    config_parser = main_subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(dest="command", help="Configuration commands")

    # Init command
    init_parser = config_subparsers.add_parser("init", help="Initialize a new configuration file")
    init_group = init_parser.add_mutually_exclusive_group()
    init_group.add_argument(
        "--global",
        dest="global_config",
        action="store_true",
        help="Initialize global configuration file",
    )
    init_group.add_argument(
        "--local",
        dest="local_config",
        action="store_true",
        help="Initialize local configuration file (default)",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing configuration file",
    )
    init_parser.add_argument(
        "--comment-style",
        dest="comment_style",
        default="##",
        help='Comment style for values to uncomment (default: "##")',
    )
    init_parser.set_defaults(func=cmd_init)

    # Edit command
    edit_parser = config_subparsers.add_parser(
        "edit",
        help="Edit configuration file with terminal editor",
    )
    edit_group = edit_parser.add_mutually_exclusive_group()
    edit_group.add_argument(
        "--global",
        dest="global_config",
        action="store_true",
        help="Edit global configuration file",
    )
    edit_group.add_argument(
        "--local",
        dest="local_config",
        action="store_true",
        help="Edit local configuration file (default)",
    )
    edit_parser.set_defaults(func=cmd_config_edit)

    # Open command
    open_parser = config_subparsers.add_parser(
        "open",
        help="Open configuration file with system default editor",
    )
    open_group = open_parser.add_mutually_exclusive_group()
    open_group.add_argument(
        "--global",
        dest="global_config",
        action="store_true",
        help="Open global configuration file",
    )
    open_group.add_argument(
        "--local",
        dest="local_config",
        action="store_true",
        help="Open local configuration file (default)",
    )
    open_parser.set_defaults(func=cmd_open)

    # Show command
    show_parser = config_subparsers.add_parser("show", help="Show current configuration")
    show_group = show_parser.add_mutually_exclusive_group()
    show_group.add_argument(
        "--global",
        dest="global_config",
        action="store_true",
        help="Show only global configuration",
    )
    show_group.add_argument("--local", action="store_true", help="Show only local configuration")
    show_parser.set_defaults(func=cmd_show)

    # Path command
    path_parser = config_subparsers.add_parser("path", help="Show configuration file paths")
    path_group = path_parser.add_mutually_exclusive_group()
    path_group.add_argument(
        "--global",
        dest="global_config",
        action="store_true",
        help="Show only global configuration path",
    )
    path_group.add_argument(
        "--local",
        action="store_true",
        help="Show only local configuration path",
    )
    path_parser.set_defaults(func=cmd_path)

    # Reset command
    reset_parser = config_subparsers.add_parser("reset", help="Reset configuration to defaults")
    reset_group = reset_parser.add_mutually_exclusive_group()
    reset_group.add_argument(
        "--global",
        dest="global_config",
        action="store_true",
        help="Reset global configuration file",
    )
    reset_group.add_argument(
        "--local",
        dest="local_config",
        action="store_true",
        help="Reset local configuration file (default)",
    )
    reset_parser.add_argument("--force", action="store_true", help="Reset without confirmation")
    reset_parser.set_defaults(func=cmd_reset)

    # Version command
    version_parser = config_subparsers.add_parser(
        "version",
        help="Show configuration version information",
    )
    version_group = version_parser.add_mutually_exclusive_group()
    version_group.add_argument(
        "--global",
        dest="global_config",
        action="store_true",
        help="Show global configuration version",
    )
    version_group.add_argument(
        "--local",
        dest="local_config",
        action="store_true",
        help="Show local configuration version (default)",
    )
    version_parser.set_defaults(func=cmd_config_version)

    # Migrate command
    migrate_parser = config_subparsers.add_parser(
        "migrate",
        help="Manually trigger configuration migration",
    )
    migrate_group = migrate_parser.add_mutually_exclusive_group()
    migrate_group.add_argument(
        "--global",
        dest="global_config",
        action="store_true",
        help="Migrate global configuration file",
    )
    migrate_group.add_argument(
        "--local",
        dest="local_config",
        action="store_true",
        help="Migrate local configuration file (default)",
    )
    migrate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes",
    )
    migrate_parser.set_defaults(func=cmd_migrate)

    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle main command routing
    if args.main_command in ("config", "edit"):
        if not hasattr(args, "func"):
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


if __name__ == "__main__":
    main()
