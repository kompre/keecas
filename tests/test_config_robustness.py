"""Tests for robust config handling with broken/invalid configuration files."""

import pytest
import toml


def test_import_with_broken_global_config(tmp_path, monkeypatch):
    """Module import should succeed even with syntax errors in global config."""
    # Create fake home directory with broken config
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    config_file = fake_home / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("language = [broken syntax  # Invalid TOML syntax")

    # Monkeypatch HOME/USERPROFILE to use fake directory (cross-platform)
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))

    # Import should succeed
    from keecas.config.manager import ConfigManager

    manager = ConfigManager()

    # Should have load error stored
    assert manager._load_error is not None
    assert not manager._configs_loaded

    # Path-only operations should still work
    assert manager.get_config_path() is not None
    assert manager.get_config_path(global_config=True) is not None


def test_import_with_broken_local_config(tmp_path, monkeypatch):
    """Module import should succeed even with syntax errors in local config."""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Create broken local config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("katex = True  # Invalid: should be true (no quotes)")

    # Import should succeed
    from keecas.config.manager import ConfigManager

    manager = ConfigManager()

    # Should have load error stored
    assert manager._load_error is not None
    assert not manager._configs_loaded


def test_path_only_operations_work_with_broken_config(tmp_path, monkeypatch):
    """Path-only operations should work even with broken configs."""
    monkeypatch.chdir(tmp_path)

    # Create broken config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("invalid syntax here!")

    from keecas.config.manager import ConfigManager

    manager = ConfigManager()

    # Path-only operations should succeed
    assert manager.get_config_path() is not None
    assert manager.get_config_path(global_config=False) is not None
    assert manager.get_config_path(global_config=True) is not None


def test_init_config_force_works_with_broken_config(tmp_path, monkeypatch):
    """init_config with force should work even with broken configs."""
    monkeypatch.chdir(tmp_path)

    # Create broken config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("broken broken broken")

    from keecas.config.manager import ConfigManager

    manager = ConfigManager()

    # init_config with force should succeed
    assert manager.init_config(global_config=False, force=True) is True

    # New config should be valid
    config_data = toml.load(config_file)
    assert config_data is not None
    assert "latex" in config_data


def test_config_dependent_operation_fails_with_helpful_error(tmp_path, monkeypatch):
    """Config-dependent operations should fail with helpful error message."""
    monkeypatch.chdir(tmp_path)

    # Create broken config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("language = True  # Invalid TOML")

    from keecas.config.manager import ConfigManager

    manager = ConfigManager()

    # Config-dependent operations should raise RuntimeError with recovery hint
    with pytest.raises(RuntimeError) as exc_info:
        manager.show_config()

    error_msg = str(exc_info.value)
    assert "could not be loaded" in error_msg.lower()
    assert "keecas config init --force" in error_msg


def test_show_config_specific_file_works_with_broken_config(tmp_path, monkeypatch):
    """show_config with specific file (not merged) should work with broken configs."""
    monkeypatch.chdir(tmp_path)

    # Create valid local config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)

    valid_config = {
        "latex": {"eq_prefix": "eq-test-"},
        "display": {"katex": True},
    }
    with open(config_file, "w") as f:
        toml.dump(valid_config, f)

    from keecas.config.manager import ConfigManager

    manager = ConfigManager()

    # Should be able to show local config directly (no merge needed)
    local_config = manager.show_config(global_config=False)
    assert local_config is not None
    assert local_config.get("latex", {}).get("eq_prefix") == "eq-test-"


def test_normal_usage_unaffected_by_lazy_loading(tmp_path, monkeypatch):
    """Normal usage without broken configs should work exactly as before."""
    monkeypatch.chdir(tmp_path)

    # Create valid config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)

    valid_config = {
        "latex": {"eq_prefix": "eq-normal-"},
        "display": {"katex": False, "debug": True},
    }
    with open(config_file, "w") as f:
        toml.dump(valid_config, f)

    from keecas.config.manager import ConfigManager

    manager = ConfigManager()

    # Should load successfully
    assert manager._configs_loaded is True
    assert manager._load_error is None

    # All operations should work
    merged_config = manager.show_config()
    assert merged_config["latex"]["eq_prefix"] == "eq-normal-"
    assert merged_config["display"]["debug"] is True

    # Options should be accessible
    assert manager._options.latex.eq_prefix == "eq-normal-"


def test_set_option_fails_with_broken_config(tmp_path, monkeypatch):
    """set_option should fail with helpful error when config is broken."""
    monkeypatch.chdir(tmp_path)

    # Create broken config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("invalid toml content")

    from keecas.config.manager import ConfigManager

    manager = ConfigManager()

    # set_option should fail with helpful error
    with pytest.raises(RuntimeError) as exc_info:
        manager.set_option("katex", True)

    assert "keecas config init --force" in str(exc_info.value)


def test_get_option_fails_with_broken_config(tmp_path, monkeypatch):
    """get_option should fail with helpful error when config is broken."""
    monkeypatch.chdir(tmp_path)

    # Create broken config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text('bad = "syntax')

    from keecas.config.manager import ConfigManager

    manager = ConfigManager()

    # get_option should fail with helpful error
    with pytest.raises(RuntimeError) as exc_info:
        manager.get_option("katex")

    assert "could not be loaded" in str(exc_info.value).lower()


def test_save_config_fails_with_broken_existing_config(tmp_path, monkeypatch):
    """save_config should fail with helpful error when existing config is broken."""
    monkeypatch.chdir(tmp_path)

    # Create broken config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("broken")

    from keecas.config.manager import ConfigManager

    manager = ConfigManager()

    # save_config should fail with helpful error
    with pytest.raises(RuntimeError) as exc_info:
        manager.save_config(global_config=False, force=True)

    assert "keecas config init --force" in str(exc_info.value)


def test_recovery_workflow(tmp_path, monkeypatch):
    """Test complete recovery workflow: broken -> init --force -> fixed."""
    monkeypatch.chdir(tmp_path)

    # 1. Start with broken config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text("completely broken")

    from keecas.config.manager import ConfigManager

    # 2. Manager loads but config is broken
    manager = ConfigManager()
    assert manager._load_error is not None

    # 3. Config-dependent operations fail
    with pytest.raises(RuntimeError):
        manager.show_config()

    # 4. Recovery with init --force
    assert manager.init_config(global_config=False, force=True) is True

    # 5. Need new manager instance to pick up fixed config
    manager2 = ConfigManager()

    # 6. Now everything works
    assert manager2._configs_loaded is True
    assert manager2._load_error is None
    merged_config = manager2.show_config()
    assert "latex" in merged_config
    assert "display" in merged_config


def test_language_runtime_propagation(tmp_path, monkeypatch):
    """Test that setting config.language at runtime propagates to localization system."""
    monkeypatch.chdir(tmp_path)

    # Create minimal valid config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)

    valid_config = {
        "language": {"disable_pint_locale": True},
    }
    with open(config_file, "w") as f:
        toml.dump(valid_config, f)

    from keecas.config.manager import ConfigManager
    from keecas.localization import get_language, translate

    # Create fresh manager
    manager = ConfigManager()
    config = manager.options

    # Initially no language set
    assert config.language is None
    assert get_language() == "en"  # Default

    # Set language at runtime
    config.language = "it"

    # Verify propagation
    assert config.language == "it"
    assert get_language() == "it"
    assert translate("VERIFIED") == "VERIFICATO"
    assert translate("NOT_VERIFIED") == "NON VERIFICATO"

    # Test changing to another language
    config.language = "de"
    assert get_language() == "de"
    assert translate("VERIFIED") == "BESTÄTIGT"
    assert translate("NOT_VERIFIED") == "NICHT BESTÄTIGT"
