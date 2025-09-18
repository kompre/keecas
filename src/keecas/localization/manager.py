"""
LocalizationManager - Core translation engine for keecas.
"""

from typing import Dict, Optional, Any
import os
from pathlib import Path
from .config import get_language_from_config, get_custom_translations_from_config


class LocalizationManager:
    """
    Manages hierarchical translation system with priority-based lookups.

    Priority order (highest to lowest):
    1. Direct substitutions (function parameter)
    2. Document-level language setting
    3. Global TOML config language
    4. Default language (English)
    """

    def __init__(self):
        self._languages: Dict[str, Dict[str, str]] = {}
        self._current_language = "en"
        self._load_builtin_languages()

        # Load language from config file if available
        config_lang = get_language_from_config()
        if config_lang and config_lang in self._languages:
            self._current_language = config_lang

    def _load_builtin_languages(self) -> None:
        """Load built-in language definitions."""
        import importlib
        import pkgutil
        from . import languages

        # Discover all language modules dynamically
        for importer, modname, ispkg in pkgutil.iter_modules(languages.__path__):
            if modname != '__init__':  # Skip __init__.py
                try:
                    lang_module = importlib.import_module(f'.languages.{modname}', __package__)
                    if hasattr(lang_module, 'TRANSLATIONS'):
                        self._languages[modname] = lang_module.TRANSLATIONS
                except ImportError:
                    # Skip modules that can't be imported
                    pass

    def set_language(self, language: str) -> None:
        """Set the global language."""
        if language not in self._languages:
            raise ValueError(f"Language '{language}' not available. Use: {list(self._languages.keys())}")
        self._current_language = language

    def get_language(self) -> str:
        """Get current global language."""
        return self._current_language


    def register_language(self, language_code: str, translations: Dict[str, str]) -> None:
        """Register a new language with its translation dictionary."""
        self._languages[language_code] = translations.copy()

    def get_available_languages(self) -> list:
        """Get list of available language codes."""
        return list(self._languages.keys())

    def translate(
        self,
        key: str,
        document_language: Optional[str] = None,
        substitutions: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Translate a key using hierarchical priority system.

        Priority (highest to lowest):
        1. Direct substitutions parameter
        2. Custom translations from config file
        3. Document-level language setting
        4. Current global language setting
        5. Config file language setting
        6. Default (English)

        Args:
            key: String to translate
            document_language: Document-level language override
            substitutions: Direct substitution dict (highest priority)

        Returns:
            Translated string, or original key if no translation found
        """
        # Priority 1: Direct substitutions (highest)
        if substitutions and key in substitutions:
            return substitutions[key]

        # Priority 2: Custom translations from config file
        config_custom = get_custom_translations_from_config()
        if config_custom and key in config_custom:
            return config_custom[key]

        # Priority 3: Document-level language
        if document_language and document_language in self._languages:
            if key in self._languages[document_language]:
                return self._languages[document_language][key]

        # Priority 4: Current global language
        if self._current_language in self._languages:
            if key in self._languages[self._current_language]:
                return self._languages[self._current_language][key]

        # Priority 5: Config file language setting
        config_lang = get_language_from_config()
        if config_lang and config_lang in self._languages:
            if key in self._languages[config_lang]:
                return self._languages[config_lang][key]

        # Priority 6: Default English fallback
        if "en" in self._languages and key in self._languages["en"]:
            return self._languages["en"][key]

        # No translation found - return original key
        return key

    def get_translations(self, language: str) -> Dict[str, str]:
        """Get all translations for a specific language."""
        return self._languages.get(language, {}).copy()

    def translate_dict(
        self,
        replacements: Dict[str, str],
        document_language: Optional[str] = None,
        substitutions: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Translate a dictionary of replacements using the priority system.

        This is particularly useful for regex replacement dictionaries.

        Args:
            replacements: Dictionary where values need translation
            document_language: Document-level language override
            substitutions: Direct substitution dict (highest priority)

        Returns:
            New dictionary with translated values
        """
        return {
            pattern: self.translate(replacement, document_language, substitutions)
            for pattern, replacement in replacements.items()
        }