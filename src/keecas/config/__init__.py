"""
Configuration management for keecas.

This package handles configuration versioning, migration, and management.
"""

from .manager import ConfigManager, get_config_manager
from .schema import SCHEMAS, get_current_schema_version, get_schema
from .migration import ConfigMigration

__all__ = [
    'ConfigManager',
    'get_config_manager',
    'ConfigMigration',
    'SCHEMAS',
    'get_current_schema_version',
    'get_schema',
]
