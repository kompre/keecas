"""Tests for configuration migration system."""

import pytest
from packaging import version as pkg_version

from keecas.config.migration import ConfigMigration
from keecas.config.schema import SCHEMAS, get_current_schema_version, migrate_0_1_to_1_0


class TestConfigSchema:
    """Test configuration schema definitions."""

    def test_schema_registry_exists(self):
        """Schema registry should contain version definitions."""
        assert len(SCHEMAS) > 0
        assert "0.1.0" in SCHEMAS
        assert "1.0.0" in SCHEMAS

    def test_schema_versions_are_valid(self):
        """All schema versions should be valid semantic versions."""
        for ver_str in SCHEMAS.keys():
            # Should not raise exception
            pkg_version.parse(ver_str)

    def test_get_current_schema_version(self):
        """Should return the latest schema version."""
        current = get_current_schema_version()
        assert current == "1.0.0"  # Update when adding new versions

        # Current version should be in registry
        assert current in SCHEMAS

    def test_schema_has_migration_fn_when_needed(self):
        """Schemas with breaking changes should have migration functions."""
        schema_1_0 = SCHEMAS["1.0.0"]
        # Has breaking changes (renamed/removed keys)
        assert schema_1_0.migration_fn is not None


class TestMigrationEngine:
    """Test migration engine logic."""

    def test_needs_migration_true(self):
        """Should detect when migration is needed."""
        assert ConfigMigration.needs_migration("0.1.0", "1.0.0") is True

    def test_needs_migration_false(self):
        """Should detect when migration is not needed."""
        assert ConfigMigration.needs_migration("1.0.0", "1.0.0") is False

    def test_get_migration_path(self):
        """Should calculate correct migration path."""
        path = ConfigMigration.get_migration_path("0.1.0", "1.0.0")
        assert path == ["1.0.0"]

    def test_get_migration_path_empty(self):
        """Migration path should be empty for same version."""
        path = ConfigMigration.get_migration_path("1.0.0", "1.0.0")
        assert path == []


class TestMigration_0_1_to_1_0:
    """Test specific migration from 0.1.0 to 1.0.0."""

    def test_preserves_all_user_values(self):
        """Migration should preserve all user-set values."""
        old_config = {
            "language": "it",
            "katex": True,
            "custom_key": "user_value",
        }

        new_config = migrate_0_1_to_1_0(old_config)

        assert new_config["language"] == "it"
        assert new_config["katex"] is True
        assert new_config["custom_key"] == "user_value"

    def test_moves_pint_default_format(self):
        """Should move pint_default_format to display section."""
        old_config = {
            "pint_default_format": ".4f~P",
        }

        new_config = migrate_0_1_to_1_0(old_config)

        assert "pint_default_format" not in new_config
        assert "display" in new_config
        assert new_config["display"]["pint_default_format"] == ".4f~P"

    def test_converts_float_precision(self):
        """Should convert float_precision to default_float_format."""
        old_config = {
            "float_precision": 4,
        }

        new_config = migrate_0_1_to_1_0(old_config)

        assert "float_precision" not in new_config
        assert "display" in new_config
        assert new_config["display"]["default_float_format"] == ".4f"

    def test_preserves_deprecated_sep(self):
        """Should preserve deprecated 'sep' key with warning."""
        old_config = {
            "sep": "&",
        }

        with pytest.warns(DeprecationWarning, match="sep.*deprecated"):
            new_config = migrate_0_1_to_1_0(old_config)

        # Should still be in config (removed in v2.0.0)
        assert new_config["sep"] == "&"

    def test_handles_complex_migration(self):
        """Should handle multiple transformations correctly."""
        old_config = {
            "language": "de",
            "pint_default_format": ".3f~P",
            "float_precision": 2,
            "sep": "|",
            "unknown_key": "preserved",
        }

        with pytest.warns(DeprecationWarning):
            new_config = migrate_0_1_to_1_0(old_config)

        # Check all transformations
        assert new_config["language"] == "de"
        assert new_config["display"]["pint_default_format"] == ".3f~P"
        assert new_config["display"]["default_float_format"] == ".2f"
        assert new_config["sep"] == "|"  # Deprecated but preserved
        assert new_config["unknown_key"] == "preserved"


class TestMigrationIntegration:
    """Integration tests for full migration process."""

    def test_migrate_preserves_user_values(self):
        """Full migration should preserve all user values."""
        old_config = {
            "language": "fr",
            "katex": False,
            "pint_default_format": ".5f~P",
            "custom_setting": "value",
        }

        new_config = ConfigMigration.migrate(old_config, "0.1.0", "1.0.0")

        # User values preserved
        assert new_config["language"] == "fr"
        assert new_config["katex"] is False
        assert new_config["custom_setting"] == "value"

        # Transformed correctly
        assert new_config["display"]["pint_default_format"] == ".5f~P"

    def test_migrate_handles_renamed_keys(self):
        """Migration should handle key renaming automatically."""
        old_config = {
            "pint_default_format": ".2f~P",
        }

        new_config = ConfigMigration.migrate(old_config, "0.1.0", "1.0.0")

        assert "pint_default_format" not in new_config
        assert new_config["display"]["pint_default_format"] == ".2f~P"

    def test_migrate_handles_removed_keys_with_conversion(self):
        """Removed keys should be converted if migration function handles it."""
        old_config = {
            "float_precision": 3,
        }

        new_config = ConfigMigration.migrate(old_config, "0.1.0", "1.0.0")

        assert "float_precision" not in new_config
        assert new_config["display"]["default_float_format"] == ".3f"

    def test_migrate_empty_config(self):
        """Should handle empty config without errors."""
        old_config = {}

        new_config = ConfigMigration.migrate(old_config, "0.1.0", "1.0.0")

        # Should return valid config (may have defaults added)
        assert isinstance(new_config, dict)

    def test_migrate_no_changes_needed(self):
        """Config without deprecated keys should pass through unchanged."""
        old_config = {
            "language": "en",
            "katex": True,
        }

        new_config = ConfigMigration.migrate(old_config, "0.1.0", "1.0.0")

        assert new_config["language"] == "en"
        assert new_config["katex"] is True


class TestMetadataExtraction:
    """Test metadata extraction from config file headers."""

    def test_extract_all_metadata(self, tmp_path):
        """Should extract all metadata from header comments."""
        from keecas.config import ConfigManager

        config_file = tmp_path / "config.toml"
        config_file.write_text(
            "# Generated by keecas v1.0.0\n"
            "# Schema version: 1.0.0\n"
            "# Created: 2025-10-03T10:00:00\n"
            "# Last updated: 2025-10-03T15:00:00\n\n"
            "language = 'en'\n",
        )

        metadata = ConfigManager._extract_metadata_from_comments(config_file)

        assert metadata["config_version"] == "1.0.0"
        assert metadata["keecas_version"] == "1.0.0"
        assert metadata["generated_at"] == "2025-10-03T10:00:00"
        assert metadata["last_modified"] == "2025-10-03T15:00:00"

    def test_extract_partial_metadata(self, tmp_path):
        """Should handle missing metadata fields."""
        from keecas.config import ConfigManager

        config_file = tmp_path / "config.toml"
        config_file.write_text(
            "# Generated by keecas v0.9.0\n# Schema version: 0.1.0\n\nlanguage = 'en'\n",
        )

        metadata = ConfigManager._extract_metadata_from_comments(config_file)

        assert metadata["config_version"] == "0.1.0"
        assert metadata["keecas_version"] == "0.9.0"
        assert metadata["generated_at"] is None
        assert metadata["last_modified"] is None

    def test_extract_no_metadata(self, tmp_path):
        """Should return defaults for config without headers."""
        from keecas.config import ConfigManager

        config_file = tmp_path / "config.toml"
        config_file.write_text("language = 'en'\n")

        metadata = ConfigManager._extract_metadata_from_comments(config_file)

        assert metadata["config_version"] == "0.1.0"  # Default
        assert metadata["keecas_version"] == "unknown"
        assert metadata["generated_at"] is None
        assert metadata["last_modified"] is None


class TestConfigSaveWithMetadata:
    """Test saving config with version metadata."""

    def test_save_new_config_creates_metadata(self, tmp_path):
        """Saving new config should add version metadata header."""
        from keecas.config import ConfigManager

        config_manager = ConfigManager()
        config_path = tmp_path / "config.toml"

        # Save config
        config_manager._save_config_file(config_path)

        # Read and check header
        content = config_path.read_text()
        assert "# Generated by keecas v" in content
        assert "# Schema version: 1.0.0" in content
        assert "# Created:" in content
        assert "# Last updated:" in content

    def test_save_preserves_creation_timestamp(self, tmp_path):
        """Re-saving should preserve original creation timestamp."""
        from keecas.config import ConfigManager

        config_manager = ConfigManager()
        config_path = tmp_path / "config.toml"

        # First save
        config_manager._save_config_file(config_path, created_at="2025-01-01T00:00:00")

        # Second save (simulating user modification)
        config_manager._save_config_file(config_path)

        # Check creation time preserved
        metadata = ConfigManager._extract_metadata_from_comments(config_path)
        assert metadata["generated_at"] == "2025-01-01T00:00:00"

    def test_save_updates_last_modified(self, tmp_path):
        """Re-saving should update last modified timestamp."""
        import time

        from keecas.config import ConfigManager

        config_manager = ConfigManager()
        config_path = tmp_path / "config.toml"

        # First save
        config_manager._save_config_file(config_path)
        first_metadata = ConfigManager._extract_metadata_from_comments(config_path)

        time.sleep(0.1)  # Ensure timestamp difference

        # Second save
        config_manager._save_config_file(config_path)
        second_metadata = ConfigManager._extract_metadata_from_comments(config_path)

        # Last modified should be different
        assert first_metadata["last_modified"] != second_metadata["last_modified"]
        # But created should be same
        assert first_metadata["generated_at"] == second_metadata["generated_at"]
