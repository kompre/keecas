"""Tests for sandbox mode (inline script metadata -> uv run)."""

import argparse
import json

import pytest

from keecas import cli, sandbox

BLOCK = (
    '# /// script\n# requires-python = ">=3.12"\n# dependencies = ["scipy", "pandas>=2,<3"]\n# ///'
)


def write_notebook(path, *sources):
    cells = [
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s}
        for s in sources
    ]
    path.write_text(
        json.dumps({"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5})
    )
    return path


def test_parse_script_metadata():
    metadata = sandbox.parse_script_metadata(BLOCK + "\nimport scipy\n")
    assert metadata == {"requires-python": ">=3.12", "dependencies": ["scipy", "pandas>=2,<3"]}


def test_parse_script_metadata_absent_and_other_types():
    assert sandbox.parse_script_metadata("import os\n") is None
    assert sandbox.parse_script_metadata("# /// other\n# x = 1\n# ///\n") is None


def test_parse_script_metadata_rejects_duplicates():
    with pytest.raises(ValueError):
        sandbox.parse_script_metadata(BLOCK + "\n" + BLOCK + "\n")


def test_read_notebook_metadata_list_source_without_trailing_newline(tmp_path):
    nb = write_notebook(tmp_path / "a.ipynb", "x = 1", BLOCK.splitlines(keepends=True))
    assert sandbox.read_notebook_metadata(nb)["dependencies"] == ["scipy", "pandas>=2,<3"]


def test_read_notebook_metadata_none_and_duplicates(tmp_path):
    assert sandbox.read_notebook_metadata(write_notebook(tmp_path / "a.ipynb", "x = 1")) is None
    with pytest.raises(ValueError):
        sandbox.read_notebook_metadata(write_notebook(tmp_path / "b.ipynb", BLOCK, BLOCK))


def test_build_uv_command_adds_keecas(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox, "_keecas_requirement", lambda: (["keecas==9.9.9"], []))
    metadata = sandbox.parse_script_metadata(BLOCK + "\n")
    req = tmp_path / "req.txt"
    cmd, requirements = sandbox.build_uv_command(metadata, ["edit", "a.ipynb"], req)

    assert requirements == ["keecas==9.9.9", "scipy", "pandas>=2,<3"]
    assert cmd[1:] == [
        "run",
        "--isolated",
        "--no-project",
        "--with-requirements",
        str(req),
        "--python",
        ">=3.12",
        "python",
        "-m",
        "keecas",
        "edit",
        "a.ipynb",
    ]


def test_build_uv_command_respects_user_keecas_pin(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox, "_keecas_requirement", lambda: pytest.fail("should not pin"))
    _, requirements = sandbox.build_uv_command(
        {"dependencies": ["Keecas[extra]==1.0", "scipy"]}, ["edit"], tmp_path / "r.txt"
    )
    assert requirements == ["Keecas[extra]==1.0", "scipy"]


def test_build_uv_command_dev_checkout_is_editable(tmp_path):
    # The test suite runs from the repo checkout, so keecas is layered as editable.
    cmd, requirements = sandbox.build_uv_command(None, ["edit"], tmp_path / "r.txt")
    assert requirements == []
    assert "--with-editable" in cmd


def test_strip_sandbox_args():
    argv = ["edit", "a.ipynb", "--sandbox", "--port", "9000"]
    assert sandbox.strip_sandbox_args(argv) == ["edit", "a.ipynb", "--port", "9000"]


def edit_args(tmp_path, file=None, **kwargs):
    defaults = {"file": file, "dir": str(tmp_path), "sandbox": False, "no_sandbox": False}
    return argparse.Namespace(**{**defaults, **kwargs})


@pytest.fixture
def relaunch(monkeypatch):
    """Record sandbox re-launches instead of running uv."""
    calls = []

    def fake_run(metadata, inner_args):
        calls.append((metadata, inner_args))
        return 0

    monkeypatch.delenv(sandbox.SANDBOX_ENV_VAR, raising=False)
    monkeypatch.setattr(sandbox, "run_in_sandbox", fake_run)
    monkeypatch.setattr(sandbox, "is_uv_available", lambda: True)
    monkeypatch.setattr(cli.sys, "argv", ["keecas", "edit", "a.ipynb", "--sandbox", "--no-browser"])
    return calls


def test_sandbox_flag_relaunches_with_metadata(tmp_path, relaunch):
    write_notebook(tmp_path / "a.ipynb", BLOCK)
    with pytest.raises(SystemExit) as exc:
        cli._maybe_run_in_sandbox(edit_args(tmp_path, "a.ipynb", sandbox=True))
    assert exc.value.code == 0
    metadata, inner_args = relaunch[0]
    assert metadata["dependencies"] == ["scipy", "pandas>=2,<3"]
    assert inner_args == ["edit", "a.ipynb", "--no-browser"]


def test_no_sandbox_and_inside_sandbox_skip(tmp_path, relaunch, monkeypatch):
    write_notebook(tmp_path / "a.ipynb", BLOCK)
    cli._maybe_run_in_sandbox(edit_args(tmp_path, "a.ipynb", no_sandbox=True))
    monkeypatch.setenv(sandbox.SANDBOX_ENV_VAR, "1")
    cli._maybe_run_in_sandbox(edit_args(tmp_path, "a.ipynb", sandbox=True))
    assert relaunch == []


def test_dependencies_without_tty_do_not_relaunch(tmp_path, relaunch, monkeypatch, capsys):
    write_notebook(tmp_path / "a.ipynb", BLOCK)
    monkeypatch.setattr(sandbox.sys.stdin, "isatty", lambda: False, raising=False)
    cli._maybe_run_in_sandbox(edit_args(tmp_path, "a.ipynb"))
    assert relaunch == []
    assert "--sandbox" in capsys.readouterr().out


def test_dependencies_prompt_accepts(tmp_path, relaunch, monkeypatch):
    write_notebook(tmp_path / "a.ipynb", BLOCK)
    monkeypatch.setattr(sandbox.sys.stdin, "isatty", lambda: True, raising=False)
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    with pytest.raises(SystemExit):
        cli._maybe_run_in_sandbox(edit_args(tmp_path, "a.ipynb"))
    assert len(relaunch) == 1


def test_sandbox_without_uv_errors(tmp_path, relaunch, monkeypatch, capsys):
    monkeypatch.setattr(sandbox, "is_uv_available", lambda: False)
    with pytest.raises(SystemExit) as exc:
        cli._maybe_run_in_sandbox(edit_args(tmp_path, "new.ipynb", sandbox=True))
    assert exc.value.code == 1
    assert "uv must be installed" in capsys.readouterr().out
    assert relaunch == []
