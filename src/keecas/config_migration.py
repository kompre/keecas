"""
Configuration migration engine for keecas.

Handles automatic migration of configuration files between schema versions,
preserving user values while transforming structure and deprecating/removing keys.
"""

from typing import Dict, List
from warnings import warn
from packaging import version

from .config_schema import SCHEMAS


class ConfigMigration:
    """Configuration migration engine."""

    @staticmethod
    def needs_migration(config_version: str, current_version: str) -> bool:
        """Check if config needs migration.

        Args:
            config_version: Version of the config file
            current_version: Current schema version

        Returns:
            True if migration is needed, False otherwise
        """
        return version.parse(config_version) < version.parse(current_version)

    @staticmethod
    def get_migration_path(from_version: str, to_version: str) -> List[str]:
        """Get ordered list of schema versions to migrate through.

        Args:
            from_version: Starting schema version
            to_version: Target schema version

        Returns:
            List of intermediate versions to migrate through
        """
        all_versions = sorted(SCHEMAS.keys(), key=version.parse)
        start_idx = all_versions.index(from_version)
        end_idx = all_versions.index(to_version)
        return all_versions[start_idx + 1 : end_idx + 1]

    @staticmethod
    def migrate(config_data: Dict, from_version: str, to_version: str) -> Dict:
        """Migrate config through all intermediate versions.

        Preserves all user-customized values while transforming structure
        and handling deprecated/removed keys according to migration functions.

        Args:
            config_data: Configuration dictionary to migrate
            from_version: Starting schema version
            to_version: Target schema version

        Returns:
            Migrated configuration dictionary
        """
        migration_path = ConfigMigration.get_migration_path(from_version, to_version)

        current_config = config_data.copy()  # Start with full user config
        for target_version in migration_path:
            schema = SCHEMAS[target_version]

            # Warn about deprecated keys (don't remove yet)
            for key in schema.deprecated_keys:
                if key in current_config:
                    warn(
                        f"Config key '{key}' is deprecated as of keecas {target_version}. "
                        f"See migration guide for alternatives.",
                        DeprecationWarning,
                        stacklevel=2
                    )

            # Handle removed keys
            # NOTE: Custom migration_fn should handle value conversion BEFORE removal
            # This section only removes keys that truly have no migration path
            for key in schema.removed_keys:
                if key in current_config:
                    # Only warn if the custom migration didn't already handle it
                    warn(
                        f"Config key '{key}' was removed in keecas {target_version}. "
                        f"Check migration guide for replacement options.",
                        UserWarning,
                        stacklevel=2
                    )
                    current_config.pop(key)

            # Apply renaming (preserves user values)
            for old_key, new_key in schema.renamed_keys.items():
                if old_key in current_config:
                    user_value = current_config.pop(old_key)

                    # Handle nested keys (e.g., "display.pint_default_format")
                    parts = new_key.split('.')
                    if len(parts) > 1:
                        # Create nested structure
                        current_level = current_config
                        for part in parts[:-1]:
                            if part not in current_level:
                                current_level[part] = {}
                            current_level = current_level[part]
                        current_level[parts[-1]] = user_value
                    else:
                        current_config[new_key] = user_value

                    print(f"Migrated '{old_key}' -> '{new_key}' (value: {user_value})")

            # Run custom migration function (handles complex transformations)
            if schema.migration_fn:
                current_config = schema.migration_fn(current_config)

            # Metadata will be updated in header comments during save
            # No need to modify config_data structure

        return current_config
