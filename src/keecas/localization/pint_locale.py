"""Pint locale management and synchronization with keecas language settings.

This module handles locale detection, configuration, and automatic synchronization
between keecas language settings and Pint unit formatting.
"""

import locale
import subprocess
from typing import Any


def _get_available_locales() -> list[str]:
    """Get list of available system locales from the system.

    Returns:
        List of available locale strings, fallback to common locales if command fails
    """
    try:
        # Try to get locales from locale -a command
        result = subprocess.run(["locale", "-a"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return [loc.strip() for loc in result.stdout.split("\n") if loc.strip()]
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: try some common locales
    return ["C", "C.UTF-8", "POSIX"]


def _check_locale_available(locale_str: str) -> bool:
    """Check if a specific locale is available on the system.

    Args:
        locale_str: Locale string to test (e.g., 'en_US.UTF-8')

    Returns:
        True if locale is available and can be set, False otherwise
    """
    if not locale_str:
        return False

    try:
        # Try to set the locale temporarily to test availability
        current = locale.setlocale(locale.LC_NUMERIC)
        locale.setlocale(locale.LC_NUMERIC, locale_str)
        locale.setlocale(locale.LC_NUMERIC, current)  # Restore
        return True
    except locale.Error:
        return False


def _find_best_locale(language_code: str, fallback_to_english: bool = True) -> str | None:
    """Find the best available locale for a given language code.

    Args:
        language_code: Two-letter language code (e.g., 'en', 'it', 'fr')
        fallback_to_english: If True, fallback to English for unsupported languages

    Returns:
        Best matching locale string, or None if no suitable locale found

    Notes:
        Tries multiple locale variants in order of preference for each language
    """
    if not language_code:
        return None

    # Define locale mapping with fallback options
    locale_options = {
        "en": ["en_US.UTF-8", "en_US", "en_GB.UTF-8", "en_GB", "en_AU.UTF-8", "en_CA.UTF-8"],
        "it": ["it_IT.UTF-8", "it_IT", "it_CH.UTF-8"],
        "fr": ["fr_FR.UTF-8", "fr_FR", "fr_CA.UTF-8", "fr_BE.UTF-8", "fr_CH.UTF-8"],
        "de": ["de_DE.UTF-8", "de_DE", "de_AT.UTF-8", "de_CH.UTF-8"],
        "es": ["es_ES.UTF-8", "es_ES", "es_MX.UTF-8", "es_AR.UTF-8"],
        "pt": ["pt_PT.UTF-8", "pt_PT", "pt_BR.UTF-8"],
        "nl": ["nl_NL.UTF-8", "nl_NL", "nl_BE.UTF-8"],
        "da": ["da_DK.UTF-8", "da_DK"],
        "sv": ["sv_SE.UTF-8", "sv_SE"],
        "no": ["nb_NO.UTF-8", "nb_NO", "nn_NO.UTF-8"],
    }

    # Get options for this language
    options = locale_options.get(language_code, [])

    # Try each option in order
    for locale_str in options:
        if _check_locale_available(locale_str):
            return locale_str

    # If language is not supported or no locale found, fallback to English
    if fallback_to_english and language_code != "en":
        return _find_best_locale("en", fallback_to_english=False)

    # Last resort fallbacks (but avoid C.UTF-8 due to Pint case sensitivity issues)
    last_resort = ["en_US.UTF-8", "en_GB.UTF-8", "C.UTF-8", "C", "POSIX"]
    for locale_str in last_resort:
        if _check_locale_available(locale_str):
            return locale_str

    return None


def _get_locale_from_keecas() -> str:
    """Get current locale from keecas localization system.

    Returns:
        Locale identifier based on current keecas language setting

    Notes:
        Maps keecas language codes to standard locale identifiers
    """
    try:
        from . import get_language, get_language_from_config

        # Try to get language from config first, then from current language
        lang = get_language_from_config() or get_language()

        # Map keecas language codes to locale identifiers
        locale_map = {
            "en": "en_US",
            "it": "it_IT",
            "fr": "fr_FR",
            "de": "de_DE",
            "es": "es_ES",
            "pt": "pt_PT",
            "nl": "nl_NL",
            "da": "da_DK",
            "sv": "sv_SE",
            "no": "nb_NO",
        }

        return locale_map.get(lang, "en_US")
    except ImportError:
        # Fallback if localization system not available
        return "en_US"


def _get_safe_init_locale() -> str | None:
    """Get a safe locale for UnitRegistry initialization.

    Returns:
        Locale string if explicitly configured and Pint locale not disabled,
        None to disable locale (preserves compact unit symbols)

    Notes:
        Respects disable_pint_locale config to prevent locale from breaking
        compact unit symbols (kN vs kilonewton)
    """
    try:
        from ..config import ConfigManager
        from . import get_language_from_config

        # Check if Pint locale is disabled
        try:
            cm = ConfigManager()
            if cm._options.disable_pint_locale:
                return None  # Explicitly disable locale
        except Exception:
            pass

        config_lang = get_language_from_config()

        # Only use locale if explicitly configured
        if config_lang:
            return _find_best_locale(config_lang)

        # For default 'en', don't set any locale
        return None
    except ImportError:
        return None


def _get_current_pint_locale(unitregistry: Any) -> str | None:
    """Get the current pint locale setting.

    Args:
        unitregistry: The Pint UnitRegistry instance

    Returns:
        Current locale string set in pint formatter, or None if not set
    """
    try:
        return getattr(unitregistry.formatter, "_locale", None)
    except AttributeError:
        return None


def _detect_pint_mode_on_language_change(unitregistry: Any, new_language: str) -> str:
    """Detect if user has manually changed pint locale.

    Args:
        unitregistry: The Pint UnitRegistry instance
        new_language: New language being set by keecas

    Returns:
        'manual' if user has made manual pint locale changes, 'auto' otherwise

    Notes:
        Compares current pint locale with expected locale for keecas language
    """
    try:
        from ..config import get_config_manager

        config = get_config_manager()
        current_keecas_lang = config.options.language.language or "en"
        current_pint_locale = _get_current_pint_locale(unitregistry)

        if not current_pint_locale:
            return "auto"  # No pint locale set

        # Map expected pint locale for current keecas language
        expected_locale = _find_best_locale(current_keecas_lang)

        # If pint locale doesn't match what keecas would have set, user changed it manually
        if current_pint_locale != expected_locale:
            return "manual"

        return "auto"
    except Exception:
        return "auto"  # Default to auto if detection fails


def _was_pint_imported_before_keecas(unitregistry: Any) -> bool:
    """Check if pint was imported before keecas (indicates manual setup).

    Args:
        unitregistry: The Pint UnitRegistry instance

    Returns:
        True if external pint setup detected, False otherwise
    """
    import sys

    # This is a heuristic - if we detect common manual pint usage patterns
    try:
        # Check if there are external references to pint registries
        pint_module = sys.modules.get("pint")
        if pint_module and hasattr(pint_module, "_APPLICATION_REGISTRY"):
            app_reg = pint_module._APPLICATION_REGISTRY
            if app_reg and app_reg is not unitregistry:
                return True  # Different registry suggests manual setup
        return False
    except Exception:
        return False


def _update_pint_locale_impl(
    unitregistry: Any,
    language: str | None = None,
    verbose: bool = False,
) -> None:
    """Internal implementation of pint locale update with smart mode detection.

    This is the internal implementation. Users should call the public wrapper
    update_pint_locale() from keecas.pint_sympy instead.

    Args:
        unitregistry: The Pint UnitRegistry instance
        language: Two-letter language code. If None, gets from keecas config
        verbose: If True, print debugging information about locale changes

    Notes:
        - Automatically switches to manual mode if user intervention is detected
        - Respects disable_pint_locale configuration setting
        - Handles fallback scenarios for unsupported languages
    """
    from ..config import get_config_manager

    config = get_config_manager()

    # Check if pint locale sync is disabled
    if config.options.language.disable_pint_locale:
        if verbose:
            print("Pint locale sync disabled by configuration")
        return

    # Get or determine the target language
    if language is None:
        from . import get_language, get_language_from_config

        config_lang = get_language_from_config()
        current_lang = get_language()
        language = config_lang or current_lang or "en"

    # Smart mode detection
    if config.options.language.pint_language_mode == "auto":
        # Check if we should switch to manual mode
        if _was_pint_imported_before_keecas(unitregistry):
            config.options.language.pint_language_mode = "manual"
            if verbose:
                print("Detected pint was imported before keecas - switching to manual mode")
        else:
            # Check if user has manually changed pint locale
            detected_mode = _detect_pint_mode_on_language_change(unitregistry, language)
            if detected_mode == "manual":
                config.options.language.pint_language_mode = "manual"
                if verbose:
                    print("Detected manual pint locale change - switching to manual mode")

    # Only proceed if in auto mode
    if config.options.language.pint_language_mode == "manual":
        if verbose:
            print("Pint language mode is 'manual' - skipping automatic locale sync")
        return

    # Handle English locale setting
    if language == "en":
        # Check if we currently have a non-English locale set by inspecting the actual locale
        current_locale = getattr(unitregistry.formatter, "locale", None) or getattr(
            unitregistry.formatter,
            "_locale",
            None,
        )

        # Determine if we have a non-English locale
        has_non_english_locale = current_locale is not None and not current_locale.startswith(
            ("en_", "C", "POSIX"),
        )

        if has_non_english_locale:
            # We have a non-English locale, should reset to English
            if verbose:
                print("Resetting to English locale from non-English locale")
        else:
            # Already English or no locale set
            # Only skip if language was not explicitly requested (i.e., no config set)
            from . import get_language_from_config

            config_lang = get_language_from_config()

            if not config_lang:
                # No explicit config, skip to avoid unnecessary changes
                if verbose:
                    print("Skipping locale setting for unconfigured English (already English)")
                return

    # Find the best available locale for this language
    locale_str = _find_best_locale(language, fallback_to_english=True)

    if not locale_str:
        # No suitable locale found, reset to system default
        if verbose:
            print(f"Warning: No suitable locale found for {language}, resetting to None")
        try:
            unitregistry.formatter.set_locale(None)
        except Exception:
            pass
        return

    # Check if this is a fallback to English for unsupported language
    is_fallback = (
        language not in ["en", "it", "fr", "de", "es", "pt"]
        and locale_str
        and locale_str.startswith(("en_", "C"))
    )

    if verbose and is_fallback:
        print(f"Language '{language}' not supported, falling back to English locale: {locale_str}")

    # Update the locale in the existing registry
    try:
        unitregistry.formatter.set_locale(locale_str)
        if verbose:
            print(f"Set Pint locale to: {locale_str} for language: {language}")
    except Exception as e:
        if verbose:
            print(f"Warning: Could not set Pint locale to {locale_str}: {e}")
        # If setting fails, explicitly try to fallback to English
        try:
            fallback_locale = _find_best_locale("en", fallback_to_english=False)
            if fallback_locale:
                unitregistry.formatter.set_locale(fallback_locale)
                if verbose:
                    print(f"Fallback: Set Pint locale to {fallback_locale}")
        except Exception:
            if verbose:
                print("Failed to set any locale, keeping current")
            pass
