"""
Configuration schema definitions and version registry for keecas.

Manages schema versions, deprecated keys, renamed keys, and migration functions
to handle breaking configuration changes across package versions.
"""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class ConfigSchema:
    """Schema definition for a specific config version."""

    version: str
    created_at: str  # ISO date when schema was introduced
    deprecated_keys: list[str]
    renamed_keys: dict[str, str]  # old_key -> new_key
    removed_keys: list[str]
    migration_fn: Callable[[dict], dict] | None


def migrate_0_1_to_1_0(old_config: dict) -> dict:
    """Migrate config from 0.1.x to 1.0.0

    IMPORTANT: All user-customized values MUST be preserved during migration.
    Only transform structure/location, never lose user data.

    Args:
        old_config: Configuration dict from v0.1.x

    Returns:
        Migrated configuration dict for v1.0.0
    """
    from warnings import warn

    new_config = old_config.copy()  # Preserves ALL user values as starting point

    # RENAME: Move pint_default_format to display section (preserves user value)
    if "pint_default_format" in new_config:
        user_value = new_config.pop("pint_default_format")  # Extract user's value
        if "display" not in new_config:
            new_config["display"] = {}
        new_config["display"]["pint_default_format"] = user_value  # Preserve it
        print(
            f"Migrated 'pint_default_format' -> 'display.pint_default_format' (value: {user_value})",
        )

    # DEPRECATED: Warn but preserve for now (remove in v2.0.0)
    if "sep" in new_config:
        warn(
            "`sep` is deprecated. Use `config.latex.environments.align.separator` instead. "
            "This key will be removed in keecas v2.0.0",
            DeprecationWarning,
            stacklevel=2,
        )
        # Keep the value for now - don't auto-migrate (too complex)

    # REMOVED WITH CONVERSION: float_precision -> display.default_float_format
    if "float_precision" in new_config:
        precision = new_config.pop("float_precision")  # Extract user's precision value
        if "display" not in new_config:
            new_config["display"] = {}
        # Convert numeric precision to format string, preserving user intent
        new_config["display"]["default_float_format"] = f".{precision}f"
        print(
            f"Converted 'float_precision={precision}' -> 'display.default_float_format=\".{precision}f\"'",
        )

    return new_config


# Schema registry: version -> schema definition
SCHEMAS: dict[str, ConfigSchema] = {
    "0.1.0": ConfigSchema(
        version="0.1.0",
        created_at="2024-08-01",
        deprecated_keys=[],
        renamed_keys={},
        removed_keys=[],
        migration_fn=None,  # Base version, no migration needed
    ),
    "1.0.0": ConfigSchema(
        version="1.0.0",
        created_at="2025-10-03",
        deprecated_keys=["sep"],  # Now use environment separator
        renamed_keys={
            "pint_default_format": "display.pint_default_format",
        },
        removed_keys=["float_precision"],  # Converted to default_float_format
        migration_fn=migrate_0_1_to_1_0,
    ),
}


def get_current_schema_version() -> str:
    """Get the current/latest schema version.

    Returns:
        Latest schema version string
    """
    from packaging import version

    return max(SCHEMAS.keys(), key=version.parse)


def get_schema(version_str: str) -> ConfigSchema | None:
    """Get schema definition for a specific version.

    Args:
        version_str: Schema version string

    Returns:
        ConfigSchema if found, None otherwise
    """
    return SCHEMAS.get(version_str)
