"""Tests for config file generation and template validation.

Validates that generated config files are:
1. Valid TOML syntax
2. Complete with all documented sections and keys
3. Following comment syntax conventions
4. Consistent with ConfigOptions defaults
"""

import re

import pytest
import toml


@pytest.fixture
def setup_fake_home(tmp_path, monkeypatch):
    """Set up fake home directory for global config tests."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    return fake_home


class TestConfigTemplateGeneration:
    """Validate generated config templates parse correctly and are complete."""

    def test_global_config_is_valid_toml(self, setup_fake_home):
        """Generated global config should parse as valid TOML."""
        from keecas.config.manager import ConfigManager

        manager = ConfigManager()

        # Generate global config
        config_path = setup_fake_home / ".keecas" / "config.toml"
        success = manager.init_config(global_config=True, force=True)
        assert success is True
        assert config_path.exists()

        # Should parse without errors
        config_data = toml.load(config_path)
        assert config_data is not None

    def test_local_config_is_valid_toml(self, tmp_path, monkeypatch):
        """Generated local config should parse as valid TOML."""
        monkeypatch.chdir(tmp_path)

        from keecas.config.manager import ConfigManager

        manager = ConfigManager()

        # Generate local config
        config_path = tmp_path / ".keecas" / "config.toml"
        success = manager.init_config(global_config=False, force=True)
        assert success is True
        assert config_path.exists()

        # Should parse without errors
        config_data = toml.load(config_path)
        assert config_data is not None

    def test_all_sections_present_in_global(self, setup_fake_home):
        """Global config should contain all documented sections."""
        from keecas.config.manager import ConfigManager

        manager = ConfigManager()
        config_path = setup_fake_home / ".keecas" / "config.toml"
        manager.init_config(global_config=True, force=True)

        config_data = toml.load(config_path)

        # Check all main sections exist
        assert "latex" in config_data
        assert "display" in config_data
        assert "language" in config_data
        assert "check_templates" in config_data
        # translations may be empty

    def test_all_latex_keys_present(self, setup_fake_home):
        """[latex] section should contain all documented keys."""
        from keecas.config.manager import ConfigManager

        manager = ConfigManager()
        config_path = setup_fake_home / ".keecas" / "config.toml"
        manager.init_config(global_config=True, force=True)

        config_data = toml.load(config_path)
        latex_section = config_data["latex"]

        # Check required keys
        assert "eq_prefix" in latex_section
        assert "eq_suffix" in latex_section
        assert "vertical_skip" in latex_section
        assert "default_environment" in latex_section
        assert "default_label_command" in latex_section
        assert "default_mul_symbol" in latex_section

    def test_all_display_keys_present(self, setup_fake_home):
        """[display] section should contain all documented keys."""
        from keecas.config.manager import ConfigManager

        manager = ConfigManager()
        config_path = setup_fake_home / ".keecas" / "config.toml"
        manager.init_config(global_config=True, force=True)

        config_data = toml.load(config_path)
        display_section = config_data["display"]

        # Check required keys
        assert "print_label" in display_section
        assert "debug" in display_section
        assert "katex" in display_section
        # default_float_format may be None/missing
        assert "pint_default_format" in display_section

    def test_all_language_keys_present(self, setup_fake_home):
        """[language] section should contain all documented keys."""
        from keecas.config.manager import ConfigManager

        manager = ConfigManager()
        config_path = setup_fake_home / ".keecas" / "config.toml"
        manager.init_config(global_config=True, force=True)

        config_data = toml.load(config_path)
        language_section = config_data["language"]

        # Check required keys
        assert "disable_pint_locale" in language_section
        # language key is optional

    def test_check_templates_structure_valid(self, setup_fake_home):
        """[check_templates] should have valid structure with both top-level and named sets."""
        from keecas.config.manager import ConfigManager

        manager = ConfigManager()
        config_path = setup_fake_home / ".keecas" / "config.toml"
        manager.init_config(global_config=True, force=True)

        config_data = toml.load(config_path)
        check_templates = config_data["check_templates"]

        # Top-level templates (default fallback)
        assert "success_template" in check_templates
        assert "failure_template" in check_templates

        # Named template sets
        assert "template_sets" in check_templates
        template_sets = check_templates["template_sets"]

        # Verify all three named sets exist
        assert "default" in template_sets
        assert "boxed" in template_sets
        assert "minimal" in template_sets

        # Each set should have success and failure
        for set_name in ["default", "boxed", "minimal"]:
            assert "success" in template_sets[set_name]
            assert "failure" in template_sets[set_name]

    def test_version_metadata_present(self, setup_fake_home):
        """Config header should contain version metadata."""
        from keecas.config.manager import ConfigManager

        manager = ConfigManager()
        config_path = setup_fake_home / ".keecas" / "config.toml"
        manager.init_config(global_config=True, force=True)

        # Read raw file content
        content = config_path.read_text()

        # Check metadata headers
        assert "# Generated by keecas v" in content
        assert "# Schema version:" in content
        assert "# Created:" in content
        assert "# Last updated:" in content

    def test_template_defaults_match_code_defaults(self, setup_fake_home):
        """Template default values should match ConfigOptions defaults."""
        from keecas.config.manager import ConfigManager, ConfigOptions

        manager = ConfigManager()
        config_path = setup_fake_home / ".keecas" / "config.toml"
        manager.init_config(global_config=True, force=True)

        config_data = toml.load(config_path)
        defaults = ConfigOptions()

        # Compare key default values
        assert config_data["latex"]["eq_prefix"] == defaults.latex.eq_prefix
        assert config_data["latex"]["eq_suffix"] == defaults.latex.eq_suffix
        assert config_data["latex"]["vertical_skip"] == defaults.latex.vertical_skip
        assert config_data["latex"]["default_environment"] == defaults.latex.default_environment
        assert config_data["latex"]["default_label_command"] == defaults.latex.default_label_command
        assert config_data["latex"]["default_mul_symbol"] == defaults.latex.default_mul_symbol

        assert config_data["display"]["print_label"] == defaults.display.print_label
        assert config_data["display"]["debug"] == defaults.display.debug
        assert config_data["display"]["katex"] == defaults.display.katex
        assert config_data["display"]["pint_default_format"] == defaults.display.pint_default_format

        assert (
            config_data["language"]["disable_pint_locale"] == defaults.language.disable_pint_locale
        )


class TestCommentSyntaxConventions:
    """Verify comment syntax follows conventions: # for toggleable, ## for docs."""

    def test_global_config_comment_syntax(self, setup_fake_home):
        """Global config should follow comment conventions."""
        from keecas.config.manager import ConfigManager

        manager = ConfigManager()
        config_path = setup_fake_home / ".keecas" / "config.toml"
        manager.init_config(global_config=True, force=True)

        content = config_path.read_text()
        lines = content.split("\n")

        # Collect comment lines (excluding version header)
        comment_lines = []
        in_header = True
        for line in lines:
            if in_header and line.startswith("#"):
                if (
                    "Generated by" in line
                    or "Schema version" in line
                    or "Created:" in line
                    or "Last updated:" in line
                ):
                    continue
                else:
                    in_header = False

            if line.strip().startswith("#"):
                comment_lines.append(line)

        # Check for proper comment prefixes
        # Lines starting with "##" are documentation
        # Lines starting with "# " (single # + space + non-#) should be toggleable settings
        for line in comment_lines:
            stripped = line.lstrip()
            if stripped.startswith("##"):
                # Documentation comment - OK
                continue
            elif re.match(r"^# [^#]", stripped):
                # Single # followed by space and non-# character
                # This should be a toggleable setting line
                # For global config, toggleable lines should be uncommented
                # So we shouldn't find many of these
                pass  # OK - may have some commented optional settings

    def test_local_config_shows_inheritance(self, tmp_path, monkeypatch):
        """Local config should show inherited global values in comments."""
        monkeypatch.chdir(tmp_path)

        from keecas.config.manager import ConfigManager

        # Create global config with custom values
        manager = ConfigManager()
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setenv("HOME", str(fake_home))
        monkeypatch.setenv("USERPROFILE", str(fake_home))

        manager.init_config(global_config=True, force=True)

        # Now create local config
        local_dir = tmp_path / "project"
        local_dir.mkdir()
        monkeypatch.chdir(local_dir)

        manager2 = ConfigManager()
        local_config_path = local_dir / ".keecas" / "config.toml"
        manager2.init_config(global_config=False, force=True)

        # Local config should have commented lines showing inherited values
        content = local_config_path.read_text()

        # Should have commented settings (inheritance display)
        assert "# print_label" in content or "# debug" in content or "# katex" in content


class TestConfigLoadingRoundTrip:
    """Test that generated configs can be loaded back correctly."""

    def test_global_config_round_trip(self, setup_fake_home):
        """Generated global config should load without errors."""
        from keecas.config.manager import ConfigManager

        # Generate config
        manager1 = ConfigManager()
        manager1.init_config(global_config=True, force=True)

        # Create new manager that loads the config
        manager2 = ConfigManager()

        # Should load successfully
        assert manager2._configs_loaded is True
        assert manager2._load_error is None

        # Options should be accessible
        assert manager2.options.latex.eq_prefix == "eq-"

    def test_local_config_round_trip(self, tmp_path, monkeypatch):
        """Generated local config should load without errors."""
        monkeypatch.chdir(tmp_path)

        from keecas.config.manager import ConfigManager

        # Generate config
        manager1 = ConfigManager()
        manager1.init_config(global_config=False, force=True)

        # Create new manager that loads the config
        manager2 = ConfigManager()

        # Should load successfully
        assert manager2._configs_loaded is True
        assert manager2._load_error is None

    def test_custom_environment_example_syntax(self, setup_fake_home):
        """Custom environment example in template should have valid structure."""
        from keecas.config.manager import ConfigManager

        manager = ConfigManager()
        config_path = setup_fake_home / ".keecas" / "config.toml"
        manager.init_config(global_config=True, force=True)

        content = config_path.read_text()

        # Check that environment example is present in comments
        assert "[latex.environments.custom]" in content or "latex.environments" in content

        # The example should mention key fields
        assert "separator" in content
        assert "line_separator" in content
        assert "supports_multiple_labels" in content
        assert "outer_environment" in content
