"""
Unified Configuration Management for Keecas.

Manages all configuration options with TOML file support, priority handling,
and dynamic propagation to affected subsystems.
"""

import os
import toml
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any, Union
from sympy import Basic
from IPython.display import Markdown


@dataclass
class ConfigOptions:
    """
    Unified configuration options for Keecas.

    Contains all display, localization, and pint settings with defaults.
    """
    # Display options
    EQ_PREFIX: str = "eq-"
    EQ_SUFFIX: str = ""
    VERTICAL_SKIP: str = "8pt"
    PRINT_LABEL: bool = False
    DEBUG: bool = False
    katex: bool = False
    default_mul_symbol: str = r"\,"
    default_environment: str = "align"
    default_label_command: str = r"\label"

    # Localization options
    _language: Optional[str] = field(default=None, init=False)

    @property
    def language(self) -> Optional[str]:
        """Document-level language override (None = use global/config)."""
        return self._language

    @language.setter
    def language(self, value: Optional[str]):
        """Set language and automatically update Pint locale and localization manager."""
        self._language = value
        # Trigger propagation through the config manager
        if hasattr(self, '_config_manager_ref'):
            self._config_manager_ref._propagate_changes('language', value)

    # Pint options
    pint_default_format: str = ".2f~P"
    disable_pint_locale: bool = False

    # Custom translations
    custom_translations: Dict[str, str] = field(default_factory=dict)

    # Complex options (not easily serializable to TOML)
    col_wrap: list = field(default_factory=lambda: [
        None,
        {
            Basic: ("=", ""),
            Markdown: (r"\qquad", ""),
            str: (r"\qquad", ""),
            int: ("=", ""),
            float: ("=", ""),
            object: ("", ""),
        },
    ])

    def to_toml_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for TOML serialization."""
        data = asdict(self)
        # Remove complex options that can't be serialized to TOML
        data.pop('col_wrap', None)
        # Remove private fields and back-references
        data.pop('_language', None)
        data.pop('_config_manager_ref', None)
        # Use the public language property value
        if self.language is not None:
            data['language'] = self.language
        return data

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update configuration from dictionary (loaded from TOML)."""
        for key, value in data.items():
            if key == 'language':
                # Use the property setter to trigger propagation
                self.language = value
            elif hasattr(self, key):
                setattr(self, key, value)


class ConfigManager:
    """
    Manages configuration files, priority loading, and option propagation.

    Priority order: API overrides > Local config > Global config > Defaults
    """

    def __init__(self):
        self._options = ConfigOptions()
        # Set back-reference for language propagation
        self._options._config_manager_ref = self
        self._global_config_path = self._get_global_config_path()
        self._local_config_path = self._get_local_config_path()
        self._loaded_files = []
        self.load_configs()

    def _get_global_config_path(self) -> Path:
        """Get path to global configuration file."""
        if os.name == "nt":  # Windows
            config_dir = Path(os.environ.get("USERPROFILE", "")) / ".keecas"
        else:  # Linux/Mac
            config_dir = Path.home() / ".keecas"

        return config_dir / "config.toml"

    def _get_local_config_path(self) -> Path:
        """Get path to local configuration file."""
        return Path.cwd() / ".keecas" / "config.toml"

    def load_configs(self) -> None:
        """Load configurations from files in priority order."""
        self._loaded_files = []

        # Load global config first (lower priority)
        if self._global_config_path.exists():
            try:
                with open(self._global_config_path, "r", encoding="utf-8") as f:
                    global_config = toml.load(f)
                self._options.update_from_dict(global_config)
                self._loaded_files.append(str(self._global_config_path))
            except (toml.TomlDecodeError, OSError) as e:
                print(f"Warning: Could not load global config from {self._global_config_path}: {e}")

        # Load local config second (higher priority)
        if self._local_config_path.exists():
            try:
                with open(self._local_config_path, "r", encoding="utf-8") as f:
                    local_config = toml.load(f)
                self._options.update_from_dict(local_config)
                self._loaded_files.append(str(self._local_config_path))
            except (toml.TomlDecodeError, OSError) as e:
                print(f"Warning: Could not load local config from {self._local_config_path}: {e}")

    def save_config(self, global_config: bool = False, force: bool = False) -> bool:
        """
        Save current configuration to file.

        Args:
            global_config: If True, save to global config file
            force: If True, overwrite existing file

        Returns:
            True if saved successfully, False otherwise
        """
        config_path = self._global_config_path if global_config else self._local_config_path

        if config_path.exists() and not force:
            print(f"Config file already exists: {config_path}")
            print("Use --force to overwrite or edit the existing file.")
            return False

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            config_dict = self._options.to_toml_dict()
            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(config_dict, f)
            print(f"Configuration saved to: {config_path}")
            return True
        except OSError as e:
            print(f"Error saving config to {config_path}: {e}")
            return False

    def init_config(self, global_config: bool = False, force: bool = False) -> bool:
        """Initialize a new configuration file with current defaults."""
        return self.save_config(global_config=global_config, force=force)

    def get_config_path(self, global_config: bool = False) -> Path:
        """Get path to configuration file."""
        return self._global_config_path if global_config else self._local_config_path

    def show_config(self, global_config: Optional[bool] = None) -> Dict[str, Any]:
        """
        Show current configuration.

        Args:
            global_config: If True, show only global config. If False, only local.
                          If None, show merged configuration.
        """
        if global_config is True:
            # Show only global config
            if self._global_config_path.exists():
                with open(self._global_config_path, "r") as f:
                    return toml.load(f)
            return {}
        elif global_config is False:
            # Show only local config
            if self._local_config_path.exists():
                with open(self._local_config_path, "r") as f:
                    return toml.load(f)
            return {}
        else:
            # Show merged configuration
            return self._options.to_toml_dict()

    def reset_config(self, global_config: bool = False) -> bool:
        """Reset configuration file to defaults."""
        config_path = self._global_config_path if global_config else self._local_config_path

        if not config_path.exists():
            print(f"No config file exists at: {config_path}")
            return False

        try:
            # Create default options and save
            default_options = ConfigOptions()
            config_dict = default_options.to_toml_dict()
            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(config_dict, f)
            print(f"Configuration reset to defaults: {config_path}")
            # Reload configs
            self.load_configs()
            return True
        except OSError as e:
            print(f"Error resetting config at {config_path}: {e}")
            return False

    def get_option(self, key: str, default: Any = None) -> Any:
        """Get configuration option value."""
        return getattr(self._options, key, default)

    def set_option(self, key: str, value: Any, propagate: bool = True) -> None:
        """
        Set configuration option and optionally propagate changes.

        Args:
            key: Option name
            value: Option value
            propagate: Whether to propagate changes to affected subsystems
        """
        if hasattr(self._options, key):
            setattr(self._options, key, value)
            if propagate:
                self._propagate_changes(key, value)
        else:
            raise ValueError(f"Unknown configuration option: {key}")

    def _propagate_changes(self, key: str, value: Any) -> None:
        """Propagate configuration changes to affected subsystems."""
        # Language changes affect both Pint and LocalizationManager
        if key == "language" and value is not None:
            self._update_pint_language(value)
            self._update_localization_language(value)

        # Pint format changes
        elif key == "pint_default_format":
            self._update_pint_format(value)

        # SymPy printing options
        elif key == "default_mul_symbol":
            self._update_sympy_printing()

    def _update_pint_language(self, language: str) -> None:
        """Update Pint locale based on language setting."""
        # Check if Pint locale is disabled
        if self._options.disable_pint_locale:
            return

        try:
            from .pint_sympy import update_pint_locale
            update_pint_locale(language)
        except ImportError:
            pass  # Module not available

    def _update_localization_language(self, language: str) -> None:
        """Update LocalizationManager language."""
        try:
            from .localization import set_language
            set_language(language)
        except ImportError:
            pass  # Module not available

    def _update_pint_format(self, format_str: str) -> None:
        """Update Pint default format."""
        try:
            from .pint_sympy import u
            u.formatter.default_format = format_str
        except ImportError:
            pass  # Module not available

    def _update_sympy_printing(self) -> None:
        """Update SymPy printing settings."""
        try:
            import sympy as sp
            sp.init_printing(mul_symbol=self._options.default_mul_symbol, order="none")
        except ImportError:
            pass  # Module not available

    @property
    def options(self) -> ConfigOptions:
        """Get current configuration options."""
        return self._options

    def get_loaded_files(self) -> list:
        """Get list of successfully loaded configuration files."""
        return self._loaded_files.copy()


# Global configuration manager instance
_config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    return _config_manager


def get_options() -> ConfigOptions:
    """Get current configuration options (backward compatibility)."""
    return _config_manager.options


# Create backward-compatible options instance
options = _config_manager.options