"""Pint-SymPy integration with automatic locale management.

This module bridges Pint unit registry with SymPy symbolic expressions,
providing seamless conversion between physical quantities and symbolic math.
Includes smart locale detection and automatic synchronization with keecas
language settings.
"""

import pint
import sympy.physics.units as sympy_units
from sympy.physics.units.util import convert_to
from sympy import nsimplify, sympify
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
        result = subprocess.run(['locale', '-a'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return [loc.strip() for loc in result.stdout.split('\n') if loc.strip()]
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: try some common locales
    return ['C', 'C.UTF-8', 'POSIX']


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
        'en': ['en_US.UTF-8', 'en_US', 'en_GB.UTF-8', 'en_GB', 'en_AU.UTF-8', 'en_CA.UTF-8'],
        'it': ['it_IT.UTF-8', 'it_IT', 'it_CH.UTF-8'],
        'fr': ['fr_FR.UTF-8', 'fr_FR', 'fr_CA.UTF-8', 'fr_BE.UTF-8', 'fr_CH.UTF-8'],
        'de': ['de_DE.UTF-8', 'de_DE', 'de_AT.UTF-8', 'de_CH.UTF-8'],
        'es': ['es_ES.UTF-8', 'es_ES', 'es_MX.UTF-8', 'es_AR.UTF-8'],
        'pt': ['pt_PT.UTF-8', 'pt_PT', 'pt_BR.UTF-8'],
        'nl': ['nl_NL.UTF-8', 'nl_NL', 'nl_BE.UTF-8'],
        'da': ['da_DK.UTF-8', 'da_DK'],
        'sv': ['sv_SE.UTF-8', 'sv_SE'],
        'no': ['nb_NO.UTF-8', 'nb_NO', 'nn_NO.UTF-8'],
    }

    # Get options for this language
    options = locale_options.get(language_code, [])

    # Try each option in order
    for locale_str in options:
        if _check_locale_available(locale_str):
            return locale_str

    # If language is not supported or no locale found, fallback to English
    if fallback_to_english and language_code != 'en':
        return _find_best_locale('en', fallback_to_english=False)

    # Last resort fallbacks (but avoid C.UTF-8 due to Pint case sensitivity issues)
    last_resort = ['en_US.UTF-8', 'en_GB.UTF-8', 'C.UTF-8', 'C', 'POSIX']
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
        from .localization import get_language_from_config
        from .localization import get_language

        # Try to get language from config first, then from current language
        lang = get_language_from_config() or get_language()

        # Map keecas language codes to locale identifiers
        locale_map = {
            'en': 'en_US',
            'it': 'it_IT',
            'fr': 'fr_FR',
            'de': 'de_DE',
            'es': 'es_ES',
            'pt': 'pt_PT',
            'nl': 'nl_NL',
            'da': 'da_DK',
            'sv': 'sv_SE',
            'no': 'nb_NO',
        }

        return locale_map.get(lang, 'en_US')
    except ImportError:
        # Fallback if localization system not available
        return 'en_US'


# Initialize UnitRegistry with safe locale support
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
        from .config import ConfigManager
        from .localization import get_language_from_config

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

# Initialize UnitRegistry respecting disable_pint_locale config
init_locale = _get_safe_init_locale()
if init_locale:
    unitregistry = pint.UnitRegistry(fmt_locale=init_locale)
else:
    # Explicitly pass None to prevent Pint from auto-detecting system locale
    unitregistry = pint.UnitRegistry(fmt_locale=None)

unitregistry.formatter.default_format = ".2f~P"


def _get_current_pint_locale() -> str | None:
    """Get the current pint locale setting.

    Returns:
        Current locale string set in pint formatter, or None if not set
    """
    try:
        return getattr(unitregistry.formatter, '_locale', None)
    except AttributeError:
        return None


def _detect_pint_mode_on_language_change(new_language: str) -> str:
    """Detect if user has manually changed pint locale.

    Args:
        new_language: New language being set by keecas

    Returns:
        'manual' if user has made manual pint locale changes, 'auto' otherwise

    Notes:
        Compares current pint locale with expected locale for keecas language
    """
    try:
        from .config import get_config_manager
        config = get_config_manager()
        current_keecas_lang = config.options.language_config.language or 'en'
        current_pint_locale = _get_current_pint_locale()

        if not current_pint_locale:
            return 'auto'  # No pint locale set

        # Map expected pint locale for current keecas language
        expected_locale = _find_best_locale(current_keecas_lang)

        # If pint locale doesn't match what keecas would have set, user changed it manually
        if current_pint_locale != expected_locale:
            return 'manual'

        return 'auto'
    except Exception:
        return 'auto'  # Default to auto if detection fails


def _was_pint_imported_before_keecas() -> bool:
    """Check if pint was imported before keecas (indicates manual setup)."""
    import sys
    # This is a heuristic - if we detect common manual pint usage patterns
    try:
        # Check if there are external references to pint registries
        pint_module = sys.modules.get('pint')
        if pint_module and hasattr(pint_module, '_APPLICATION_REGISTRY'):
            app_reg = pint_module._APPLICATION_REGISTRY
            if app_reg and app_reg is not unitregistry:
                return True  # Different registry suggests manual setup
        return False
    except Exception:
        return False


def update_pint_locale(language: str | None = None, verbose: bool = False) -> None:
    """Update pint locale based on keecas language setting with smart mode detection.

    Args:
        language: Two-letter language code. If None, gets from keecas config
        verbose: If True, print debugging information about locale changes

    Notes:
        - Automatically switches to manual mode if user intervention is detected
        - Respects disable_pint_locale configuration setting
        - Handles fallback scenarios for unsupported languages
    """
    from .config import get_config_manager
    config = get_config_manager()

    # Check if pint locale sync is disabled
    if config.options.language_config.disable_pint_locale:
        if verbose:
            print("Pint locale sync disabled by configuration")
        return

    # Get or determine the target language
    if language is None:
        from .localization import get_language_from_config
        from .localization import get_language
        config_lang = get_language_from_config()
        current_lang = get_language()
        language = config_lang or current_lang or 'en'

    # Smart mode detection
    if config.options.language_config.pint_language_mode == 'auto':
        # Check if we should switch to manual mode
        if _was_pint_imported_before_keecas():
            config.options.language_config.pint_language_mode = 'manual'
            if verbose:
                print("Detected pint was imported before keecas - switching to manual mode")
        else:
            # Check if user has manually changed pint locale
            detected_mode = _detect_pint_mode_on_language_change(language)
            if detected_mode == 'manual':
                config.options.language_config.pint_language_mode = 'manual'
                if verbose:
                    print("Detected manual pint locale change - switching to manual mode")

    # Only proceed if in auto mode
    if config.options.language_config.pint_language_mode == 'manual':
        if verbose:
            print("Pint language mode is 'manual' - skipping automatic locale sync")
        return

    # Handle English locale setting
    if language == 'en':
        from .localization import get_language_from_config
        config_lang = get_language_from_config()

        if not config_lang:
            # Check if we currently have a non-English locale set
            # If so, we should reset to English rather than skip
            current_quantity = 1 * unitregistry('cm**2')
            current_result = f'{current_quantity:.3f}'.lower()
            has_non_english_locale = not ('centimeter' in current_result or current_result.count('**') == 0)

            if has_non_english_locale:
                # We have a non-English locale, should reset to English
                if verbose:
                    print("Resetting to English locale from non-English locale")
            else:
                # Already English or no locale set, skip to avoid unnecessary changes
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
    is_fallback = (language not in ['en', 'it', 'fr', 'de', 'es', 'pt'] and
                  locale_str and locale_str.startswith(('en_', 'C')))

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
            fallback_locale = _find_best_locale('en', fallback_to_english=False)
            if fallback_locale:
                unitregistry.formatter.set_locale(fallback_locale)
                if verbose:
                    print(f"Fallback: Set Pint locale to {fallback_locale}")
        except Exception:
            if verbose:
                print("Failed to set any locale, keeping current")
            pass

def pint_to_sympy(quantity: pint.Quantity) -> Any:
    """Convert pint quantity to sympy quantity.

    Args:
        quantity: A Pint Quantity object with magnitude and units

    Returns:
        SymPy expression combining magnitude and units as symbolic quantities

    Notes:
        - Automatically creates new SymPy units if they don't exist
        - Maintains unit relationships and dimensional analysis
        - Handles both prefixed and non-prefixed units
    """
    # divide and extract the magnitude from the units: it will generate a two elements tuple, where the first item will be the magnitude and the second ona a tuple of tuples; each nested tuple is composed by two elements, the unit proper and the exponent to which is elevated; the tuples are supposed to be multiplied together.

    # quantity is multiplied by 1 so that it is converted to pint.Quantity if pint.Unit is passed instead
    magnitude, units = (1 * quantity).to_tuple()

    # for each unit (i.e. tuple), check if it exist in the sympy.physics.units module
    for u in units:
        fullname = u[0]
        shortname = f"{pint.Unit(fullname):~}"
        exponent = sympify(u[1])

        # add a new unit if it doesn't exist
        if not hasattr(sympy_units, fullname):
            if [True for x in unitregistry.parse_unit_name(fullname) if not x[0] == ""]:
                is_prefixed = True
            else:
                is_prefixed = False

            setattr(
                sympy_units,
                fullname,
                sympy_units.Quantity(
                    fullname, abbrev=shortname, is_prefixed=is_prefixed
                ),
            )  # create thwith full namee new sympy unit
            # create the alias with the shortname
            setattr(sympy_units, shortname, getattr(sympy_units, fullname))

            # set the global scale factor relative to base units (base units are assumed to be in sympy)
            # _magnitude, _units = (1 * pint.Unit(fullname)).to_base_units().to_tuple()
            # _reference = sympify(1)
            # for _u in _units:
            #     _reference *= getattr(sympy_units, _u[0])**nsimplify(_u[1])

            # getattr(sympy_units, fullname).set_global_relative_scale_factor(_magnitude, _reference)

        # multiply magnitude for the sympy units (create a sympy.core.Mul object)
        magnitude *= (
            getattr(sympy_units, fullname) ** (exponent)
            if exponent != 1
            else getattr(sympy_units, fullname)
        )

    return sympify(magnitude)


# UnitRegistry = pint.UnitRegistry()
# UnitRegistry.default_format = '.2f~P'
# Q = UnitRegistry.Quantity
# Q._sympy_ = lambda s: sympify(f'{s.m}*{s.u}')

pint.Quantity._sympy_ = lambda x: pint_to_sympy(x)
pint.Unit._sympy_ = lambda x: pint_to_sympy(1 * x)

# REMOVED: Unconditional locale initialization
# Locale is now controlled by config.language_config.disable_pint_locale
# If disable_pint_locale=True (default), no locale is set, preserving compact symbols (kN vs kilonewton)
# If disable_pint_locale=False, locale is set when language config is loaded


if __name__ == "__main__":
    u = unitregistry

    F = 5000 * u.daN  # this unit is not present in sympy.core.physics
    A = 2 * u.m
    B = 300 * u.cm

    # pint unit get converted to sympy units
    print(sympify(F))
    print(sympify(A))
    print(sympify(B))

    # sympy will not automatically simplify different units
    print(sympify(F / (A * B)))  # this is a pressure

    # you need to use convert to

    print(convert_to(sympify(F), u.kN))

    print(convert_to(sympify(F / (A * B)), u.MPa))

    print(convert_to(sympify(F / (A * B)), u.kPa))

    print(f"{F:.4f~P}")
