"""
Configuration management for keecas.

This package handles configuration versioning, migration, and management.
"""

from .manager import ConfigManager, EnvironmentDefinition, get_config_manager
from .migration import ConfigMigration
from .schema import SCHEMAS, get_current_schema_version, get_schema

__all__ = [
    "ConfigManager",
    "get_config_manager",
    "EnvironmentDefinition",
    "ConfigMigration",
    "SCHEMAS",
    "get_current_schema_version",
    "get_schema",
]
