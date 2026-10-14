"""
Sandboxed notebook environments built by uv from inline script metadata.

A notebook declares its dependencies with a PEP 723 block placed in a code
cell (a comment-only cell, so executing it is a no-op):

    # /// script
    # requires-python = ">=3.12"
    # dependencies = ["scipy", "pandas>=2"]
    # ///

`keecas edit --sandbox notebook.ipynb` reads the block and re-launches itself
through `uv run` in an isolated, ephemeral environment containing keecas plus
the declared dependencies, so the notebook kernel can import them. uv is not a
keecas dependency: sandbox mode fails with an install hint when uv is missing.

Stdlib-only module, imported lazily by the CLI.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

# Set in the environment of the re-launched process, to prevent re-wrapping.
SANDBOX_ENV_VAR = "KEECAS_SANDBOX"

UV_INSTALL_URL = "https://docs.astral.sh/uv/getting-started/installation/"

# Reference regex from PEP 723 / the inline script metadata specification.
_METADATA_REGEX = re.compile(
    r"(?m)^# /// (?P<type>[a-zA-Z0-9-]+)$\s(?P<content>(^#(| .*)$\s)+)^# ///$"
)


def parse_script_metadata(source: str) -> dict | None:
    """Parse the `script` metadata block from Python source text.

    Args:
        source: Python source (a script or a notebook cell).

    Returns:
        The parsed TOML table, or None when no `script` block is present.

    Raises:
        ValueError: If more than one `script` block is present.
    """
    matches = [m for m in _METADATA_REGEX.finditer(source) if m.group("type") == "script"]
    if len(matches) > 1:
        raise ValueError("Multiple '# /// script' blocks found")
    if not matches:
        return None
    content = "".join(
        line[2:] if line.startswith("# ") else line[1:]
        for line in matches[0].group("content").splitlines(keepends=True)
    )
    return tomllib.loads(content)


def read_notebook_metadata(path: Path | str) -> dict | None:
    """Read the `script` metadata block from a notebook's code cells.

    Args:
        path: Path to an `.ipynb` file.

    Returns:
        The parsed TOML table, or None when no code cell holds a block.

    Raises:
        ValueError: If more than one cell holds a `script` block.
    """
    with open(path, encoding="utf-8") as f:
        notebook = json.load(f)

    found = None
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        metadata = parse_script_metadata(source + "\n")
        if metadata is None:
            continue
        if found is not None:
            raise ValueError(f"Multiple '# /// script' blocks found in {path}")
        found = metadata
    return found


def is_uv_available() -> bool:
    """Return True if the uv executable is on PATH."""
    return shutil.which("uv") is not None


def in_sandbox() -> bool:
    """Return True if this process was launched by sandbox mode."""
    return os.environ.get(SANDBOX_ENV_VAR) == "1"


def _keecas_requirement() -> tuple[list[str], list[str]]:
    """Return (requirement lines, extra uv flags) that provide keecas itself.

    A development checkout (src layout next to a keecas pyproject.toml) is
    layered as editable; otherwise the running keecas version is pinned.
    """
    import keecas

    repo_root = Path(keecas.__file__).resolve().parents[2]
    pyproject = repo_root / "pyproject.toml"
    if pyproject.exists():
        try:
            with open(pyproject, "rb") as f:
                if tomllib.load(f).get("project", {}).get("name") == "keecas":
                    return [], ["--with-editable", str(repo_root)]
        except (OSError, tomllib.TOMLDecodeError):
            pass

    from .cli import get_version

    keecas_version = get_version()
    if keecas_version == "unknown":
        return ["keecas"], []
    return [f"keecas=={keecas_version}"], []


def _is_keecas_requirement(line: str) -> bool:
    name = re.split(r"[\s\[<>=!~;@]", line.strip(), maxsplit=1)[0]
    return name.lower().replace("_", "-") == "keecas"


def build_uv_command(
    metadata: dict | None,
    inner_args: list[str],
    requirements_file: Path | str,
) -> tuple[list[str], list[str]]:
    """Build the `uv run` command that re-launches keecas in a sandbox.

    Args:
        metadata: Parsed `script` table (or None for no dependencies).
        inner_args: keecas CLI arguments for the re-launched process
            (without `--sandbox`).
        requirements_file: Path the requirement lines will be written to.

    Returns:
        (uv command, requirement lines to write to `requirements_file`).
    """
    metadata = metadata or {}
    dependencies = list(metadata.get("dependencies", []))

    uv_flags: list[str] = []
    if not any(_is_keecas_requirement(dep) for dep in dependencies):
        keecas_lines, uv_flags = _keecas_requirement()
        dependencies = keecas_lines + dependencies

    cmd = [
        shutil.which("uv") or "uv",
        "run",
        # Ignore any surrounding project; the notebook declares everything.
        "--isolated",
        "--no-project",
        "--with-requirements",
        str(requirements_file),
        *uv_flags,
    ]
    requires_python = metadata.get("requires-python")
    if requires_python:
        cmd.extend(["--python", requires_python])

    cmd.extend(["python", "-m", "keecas", *inner_args])
    return cmd, dependencies


def strip_sandbox_args(argv: list[str]) -> list[str]:
    """Remove `--sandbox` / `--no-sandbox` from a keecas argv."""
    return [arg for arg in argv if arg not in ("--sandbox", "--no-sandbox")]


def run_in_sandbox(metadata: dict | None, inner_args: list[str]) -> int:
    """Re-launch keecas through `uv run` with the notebook's dependencies.

    Args:
        metadata: Parsed `script` table (or None for no dependencies).
        inner_args: keecas CLI arguments for the re-launched process.

    Returns:
        The exit code of the re-launched process.
    """
    with tempfile.NamedTemporaryFile(
        "w", suffix=".txt", prefix="keecas_sandbox_", delete=False, encoding="utf-8"
    ) as f:
        requirements_file = f.name
    try:
        cmd, requirements = build_uv_command(metadata, inner_args, requirements_file)
        Path(requirements_file).write_text("\n".join(requirements) + "\n", encoding="utf-8")

        env = os.environ.copy()
        env[SANDBOX_ENV_VAR] = "1"

        print("Running in sandbox: " + ", ".join(requirements or ["keecas (dev)"]))
        process = subprocess.Popen(cmd, env=env)
        try:
            return process.wait()
        except KeyboardInterrupt:
            # Ctrl+C already reached the child through the console; let it
            # shut its server down before exiting.
            return process.wait()
    finally:
        try:
            os.unlink(requirements_file)
        except OSError:
            pass


KERNEL_NAME = "python3"


def pin_kernel_to_interpreter(base_env: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """Make the `python3` kernel run on this interpreter, and allow no other.

    Jupyter resolves kernel names through its kernel directories, so a
    `python3` kernel registered by the user (`ipykernel install --user`)
    would shadow the sandbox's own and run the notebook in another
    environment, without the declared dependencies. A temporary kernel
    directory placed first on JUPYTER_PATH pins `python3` to the sandbox
    interpreter; `allowed_kernelspecs` hides every other registered kernel.

    Args:
        base_env: Environment the Jupyter server will inherit.

    Returns:
        (server environment, extra Jupyter server arguments). The temporary
        directory is removed at interpreter exit.
    """
    import atexit

    jupyter_dir = tempfile.mkdtemp(prefix="keecas_kernels_")
    atexit.register(shutil.rmtree, jupyter_dir, ignore_errors=True)

    spec_dir = Path(jupyter_dir) / "kernels" / KERNEL_NAME
    spec_dir.mkdir(parents=True)
    spec = {
        "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "Python 3 (keecas sandbox)",
        "language": "python",
        "metadata": {"debugger": True},
    }
    (spec_dir / "kernel.json").write_text(json.dumps(spec, indent=1), encoding="utf-8")

    env = dict(base_env)
    existing = env.get("JUPYTER_PATH")
    env["JUPYTER_PATH"] = jupyter_dir + (os.pathsep + existing if existing else "")
    return env, [f"--KernelSpecManager.allowed_kernelspecs={KERNEL_NAME}"]


def should_prompt(metadata: dict | None) -> bool:
    """Decide whether to offer sandbox mode for a notebook without `--sandbox`.

    Mirrors marimo: only when the notebook declares dependencies, uv is
    available and stdin is interactive. Prints a hint otherwise.
    """
    if not metadata or not metadata.get("dependencies"):
        return False
    if not is_uv_available():
        print(
            "This notebook declares inline dependencies. Install uv to run it "
            f"in a sandbox with them: {UV_INSTALL_URL}"
        )
        return False
    if not sys.stdin.isatty():
        print(
            "This notebook declares inline dependencies; "
            "pass --sandbox to run it in an environment that has them."
        )
        return False
    answer = (
        input(
            "This notebook declares inline dependencies.\n"
            "Run in a sandboxed environment with them? [Y/n]: "
        )
        .strip()
        .lower()
    )
    return answer in ("", "y", "yes")
