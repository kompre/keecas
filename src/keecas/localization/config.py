"""
Configuration management for localization settings.

Supports loading language settings from TOML configuration files.
"""

import os
import toml
from pathlib import Path
from typing import Optional, Dict, Any


class LocalizationConfig:
    """
    Manages TOML-based configuration for localization settings.

    Searches for config files in multiple locations with standard precedence:
    1. Current working directory: ./keecas.toml
    2. User config directory: ~/.config/keecas/config.toml (Linux/Mac) or AppData (Windows)
    3. System config directory: /etc/keecas/config.toml (Linux/Mac)
    """

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._config_file_path: Optional[Path] = None
        self._load_config()

    def _get_config_search_paths(self) -> list[Path]:
        """
        Get list of paths to search for config files, in order of precedence.

        Returns:
            List of Path objects to check for config files
        """
        paths = []

        # 1. Current working directory
        paths.append(Path.cwd() / "keecas.toml")

        # 2. User config directory
        if os.name == "nt":  # Windows
            user_config = Path(os.environ.get("APPDATA", "")) / "keecas" / "config.toml"
        else:  # Linux/Mac
            user_config = Path.home() / ".config" / "keecas" / "config.toml"
        paths.append(user_config)

        # 3. System config directory (Linux/Mac only)
        if os.name != "nt":
            paths.append(Path("/etc/keecas/config.toml"))

        return paths

    def _load_config(self) -> None:
        """Load configuration from the first available config file."""
        for config_path in self._get_config_search_paths():
            if config_path.exists() and config_path.is_file():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        self._config = toml.load(f)
                    self._config_file_path = config_path
                    break
                except (toml.TomlDecodeError, OSError) as e:
                    # Log error but continue searching
                    print(f"Warning: Could not load config from {config_path}: {e}")
                    continue

    def get_language(self) -> Optional[str]:
        """
        Get language setting from config file.

        Returns:
            Language code (e.g., 'it', 'en') or None if not set
        """
        return self._config.get("language")

    def get_localization_config(self) -> Dict[str, Any]:
        """
        Get the entire localization section from config.

        Returns:
            Dictionary containing localization settings
        """
        return self._config.get("localization", {})

    def get_custom_translations(self) -> Dict[str, str]:
        """
        Get custom translation overrides from config.

        Example TOML:
        [localization.custom_translations]
        "for" = "CUSTOM_FOR"
        "True" = "CUSTOM_TRUE"

        Returns:
            Dictionary of custom translation overrides
        """
        localization = self.get_localization_config()
        return localization.get("custom_translations", {})

    def get_config_file_path(self) -> Optional[Path]:
        """Get the path of the loaded config file, if any."""
        return self._config_file_path

    def has_config(self) -> bool:
        """Check if any config file was loaded."""
        return self._config_file_path is not None

    def reload(self) -> None:
        """Reload configuration from files."""
        self._config = {}
        self._config_file_path = None
        self._load_config()

    def create_example_config(self, path: Path) -> None:
        """
        Create an example configuration file with all options.

        Args:
            path: Path where to create the example config file
        """
        example_config = {
            "language": "it",
            "localization": {
                "custom_translations": {
                    "for": "per",
                    "otherwise": "altrimenti",
                    "True": "Vero",
                    "False": "Falso"
                }
            }
        }

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            toml.dump(example_config, f)


# Global config instance
_config = LocalizationConfig()


def get_config() -> LocalizationConfig:
    """Get the global configuration instance."""
    return _config


def reload_config() -> None:
    """Reload global configuration from files."""
    global _config
    _config.reload()


def get_language_from_config() -> Optional[str]:
    """Get language setting from global config."""
    return _config.get_language()


def get_custom_translations_from_config() -> Dict[str, str]:
    """Get custom translations from global config."""
    return _config.get_custom_translations()