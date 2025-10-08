"""Tests for CLI robustness with broken configuration files."""

import pytest
import subprocess
import sys
from pathlib import Path
import toml


def test_cli_config_path_works_with_broken_config(tmp_path, monkeypatch):
    """CLI 'config path' should work even with broken configs."""
    monkeypatch.chdir(tmp_path)

    # Create broken config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text('invalid syntax!')

    # Run CLI command
    result = subprocess.run(
        ['keecas', 'config', 'path', '--local'],
        capture_output=True,
        text=True,
        cwd=tmp_path
    )

    assert result.returncode == 0
    assert '.keecas' in result.stdout and 'config.toml' in result.stdout


def test_cli_init_force_overwrites_broken_config(tmp_path, monkeypatch):
    """CLI 'config init --force' should overwrite broken configs."""
    monkeypatch.chdir(tmp_path)

    # Create broken config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text('completely broken content here')

    # Run CLI command to fix
    result = subprocess.run(
        ['keecas', 'config', 'init', '--local', '--force'],
        capture_output=True,
        text=True,
        cwd=tmp_path
    )

    assert result.returncode == 0
    assert 'Configuration template created' in result.stdout

    # Verify config is now valid
    config_data = toml.load(config_file)
    assert config_data is not None
    assert 'latex' in config_data
    assert 'display' in config_data


def test_cli_show_fails_gracefully_with_broken_config(tmp_path, monkeypatch):
    """CLI 'config show' should fail with helpful error for broken configs."""
    monkeypatch.chdir(tmp_path)

    # Create broken config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text('language = True  # Invalid')

    # Run CLI command - should fail but with helpful error
    result = subprocess.run(
        ['keecas', 'config', 'show'],
        capture_output=True,
        text=True,
        cwd=tmp_path
    )

    # Should fail (non-zero exit)
    assert result.returncode != 0

    # Should mention how to fix
    combined_output = result.stdout + result.stderr
    assert 'keecas config init --force' in combined_output or 'could not be loaded' in combined_output.lower()


def test_cli_show_local_works_with_broken_config(tmp_path, monkeypatch):
    """CLI 'config show --local' should work (reads file directly, no merge)."""
    monkeypatch.chdir(tmp_path)

    # Create valid local config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)

    valid_config = {
        'latex': {'eq_prefix': 'test-'},
        'display': {'katex': True}
    }
    with open(config_file, 'w') as f:
        toml.dump(valid_config, f)

    # Run CLI command
    result = subprocess.run(
        ['keecas', 'config', 'show', '--local'],
        capture_output=True,
        text=True,
        cwd=tmp_path
    )

    assert result.returncode == 0
    assert 'eq_prefix' in result.stdout
    assert 'test-' in result.stdout


def test_cli_full_recovery_workflow(tmp_path, monkeypatch):
    """Test complete CLI recovery: path -> init --force -> show works."""
    monkeypatch.chdir(tmp_path)

    # 1. Create broken config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text('broken')

    # 2. Path command still works
    result = subprocess.run(
        ['keecas', 'config', 'path', '--local'],
        capture_output=True,
        text=True,
        cwd=tmp_path
    )
    assert result.returncode == 0

    # 3. Show command fails
    result = subprocess.run(
        ['keecas', 'config', 'show'],
        capture_output=True,
        text=True,
        cwd=tmp_path
    )
    assert result.returncode != 0

    # 4. Fix with init --force
    result = subprocess.run(
        ['keecas', 'config', 'init', '--local', '--force'],
        capture_output=True,
        text=True,
        cwd=tmp_path
    )
    assert result.returncode == 0

    # 5. Now show works
    result = subprocess.run(
        ['keecas', 'config', 'show'],
        capture_output=True,
        text=True,
        cwd=tmp_path
    )
    assert result.returncode == 0
    assert 'latex' in result.stdout
