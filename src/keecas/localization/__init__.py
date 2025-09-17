"""
Lightweight localization module for keecas.

Provides a simple, hierarchical translation system for LaTeX/SymPy string substitutions.
"""

from .manager import LocalizationManager
from .config import reload_config, get_config

# Global instance - initialized with English defaults
_localization_manager = LocalizationManager()

# Public API
def set_language(language: str) -> None:
    """Set the global language for all translations."""
    _localization_manager.set_language(language)

def translate(key: str, language: str = None, substitutions: dict = None) -> str:
    """
    Translate a key using the hierarchical priority system.

    Priority (highest to lowest):
    1. Direct substitutions parameter
    2. Document-level language setting
    3. Global TOML config language
    4. Default (English)

    Args:
        key: The string to translate
        language: Override language for this translation
        substitutions: Direct substitution dictionary (highest priority)

    Returns:
        Translated string
    """
    return _localization_manager.translate(key, language, substitutions)

def get_language() -> str:
    """Get current global language setting."""
    return _localization_manager.get_language()

def register_language(language_code: str, translations: dict) -> None:
    """Register a new language with translation dictionary."""
    _localization_manager.register_language(language_code, translations)

def get_available_languages() -> list:
    """Get list of available language codes."""
    return _localization_manager.get_available_languages()

def reload_configuration() -> None:
    """Reload TOML configuration and reinitialize localization manager."""
    global _localization_manager
    reload_config()
    _localization_manager = LocalizationManager()

def get_configuration():
    """Get the current configuration object for inspection."""
    return get_config()

__all__ = [
    "set_language",
    "translate",
    "get_language",
    "register_language",
    "get_available_languages",
    "reload_configuration",
    "get_configuration"
]