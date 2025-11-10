"""Simplified localization module for keecas.

Provides simple translation dictionary lookup with config hierarchy support.
"""

import importlib


def get_language_from_config() -> str | None:
    """Get language setting from main config system."""
    try:
        from ..config import get_config_manager

        config_manager = get_config_manager()
        return config_manager.options.language.language
    except Exception:
        return None


def get_custom_replacements_from_config() -> dict[str, str]:
    """Get custom replacements from main config system."""
    try:
        from ..config import get_config_manager

        config_manager = get_config_manager()
        return config_manager.options.translations.translations.copy()
    except Exception:
        return {}


# Global state
_current_language = "en"
_translations_cache: dict[str, dict[str, str]] = {}
_runtime_overrides: dict[str, str] = {}


def _get_issues_url() -> str:
    """Get the GitHub issues URL from project metadata."""
    try:
        import importlib.metadata

        metadata = importlib.metadata.metadata("keecas")

        # Look for Issues URL in project metadata
        # Format: "Project-URL: Issues, https://github.com/kompre/keecas/issues"
        for key, value in metadata.items():
            if key == "Project-URL" and value.startswith("Issues,"):
                return value.split(",", 1)[1].strip()

        # Fallback: try to get repository URL and append /issues
        for key, value in metadata.items():
            if key == "Project-URL" and (
                value.startswith("Repository,") or value.startswith("Homepage,")
            ):
                repo_url = value.split(",", 1)[1].strip()
                return f"{repo_url}/issues"

    except Exception:
        pass

    # Final fallback
    return "url not found in metadata"


def _load_language_module(language: str) -> dict[str, str]:
    """Load translations from a language module."""
    if language in _translations_cache:
        return _translations_cache[language]

    try:
        module = importlib.import_module(f".languages.{language}", __package__)
        if hasattr(module, "TRANSLATIONS"):
            _translations_cache[language] = module.TRANSLATIONS.copy()
            return _translations_cache[language]
    except ImportError:
        if language != "en":
            import warnings

            issues_url = _get_issues_url()
            warnings.warn(
                f"\nLanguage '{language}' not found. Falling back to English.\n"
                f"You can:\n"
                f"  • Add custom translations to your config.toml file under [translations]\n"
                f"  • Request '{language}' support by opening an issue at: {issues_url}",
                UserWarning,
                stacklevel=3,
            )

    # Fallback to English if language not found
    if language != "en":
        return _load_language_module("en")

    return {}


def get_translations(language: str | None = None) -> dict[str, str]:
    """Get complete translation dictionary for a language.

    Hierarchy: runtime_overrides -> config_replacements -> language_file
    """
    target_lang = language or _current_language

    # Start with base language translations
    translations = _load_language_module(target_lang).copy()

    # Apply config replacements
    config_replacements = get_custom_replacements_from_config()
    translations.update(config_replacements)

    # Apply runtime overrides
    translations.update(_runtime_overrides)

    return translations


def translate(
    key: str,
    language: str | None = None,
    substitutions: dict[str, str] | None = None,
) -> str:
    """Translate a single key.

    Priority: direct substitutions -> runtime -> config -> language file
    """
    # Highest priority: direct substitutions
    if substitutions and key in substitutions:
        return substitutions[key]

    # Get translations for language
    translations = get_translations(language)

    return translations.get(key, key)


def set_language(language: str) -> None:
    """Set the global language."""
    global _current_language
    _current_language = language
    # Clear cache to force reload
    _translations_cache.clear()


def get_language() -> str:
    """Get current global language."""
    return _current_language


def get_available_languages() -> list[str]:
    """Get list of available language codes."""
    import pkgutil

    from . import languages

    available = []
    for importer, modname, ispkg in pkgutil.iter_modules(languages.__path__):
        if modname != "__init__":
            available.append(modname)
    return sorted(available)


def set_runtime_override(key: str, value: str) -> None:
    """Set a runtime translation override."""
    _runtime_overrides[key] = value


def clear_runtime_overrides() -> None:
    """Clear all runtime overrides."""
    _runtime_overrides.clear()


def reset_to_config() -> None:
    """Reset to config defaults, clearing runtime overrides."""
    clear_runtime_overrides()

    # Reload config defaults
    config_lang = get_language_from_config()
    if config_lang:
        set_language(config_lang)


# Initialize from config
config_lang = get_language_from_config()
if config_lang:
    _current_language = config_lang

__all__ = [
    "get_translations",
    "translate",
    "set_language",
    "get_language",
    "get_available_languages",
    "set_runtime_override",
    "clear_runtime_overrides",
    "reset_to_config",
    "get_language_from_config",
    "get_custom_replacements_from_config",
]
