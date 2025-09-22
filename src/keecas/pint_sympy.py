import pint
import sympy.physics.units as sympy_units
from sympy.physics.units.util import convert_to

from sympy import nsimplify, sympify
import locale
import subprocess


def _get_available_locales():
    """Get list of available system locales."""
    try:
        # Try to get locales from locale -a command
        result = subprocess.run(['locale', '-a'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return [loc.strip() for loc in result.stdout.split('\n') if loc.strip()]
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: try some common locales
    return ['C', 'C.UTF-8', 'POSIX']


def _check_locale_available(locale_str):
    """Check if a specific locale is available on the system."""
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


def _find_best_locale(language_code, fallback_to_english=True):
    """Find the best available locale for a given language code.

    Args:
        language_code: The language code to find a locale for
        fallback_to_english: If True, fallback to English for unsupported languages
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


def _get_locale_from_keecas():
    """Get current locale from keecas localization system."""
    try:
        from .localization.config import get_language_from_config
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
def _get_safe_init_locale():
    """Get a safe locale for UnitRegistry initialization."""
    try:
        from .localization.config import get_language_from_config
        from .localization import get_language

        config_lang = get_language_from_config()

        # Only use locale if explicitly configured
        if config_lang:
            return _find_best_locale(config_lang)

        # For default 'en', don't set any locale (use system default)
        return None
    except ImportError:
        return None

# Initialize UnitRegistry without problematic locale by default
init_locale = _get_safe_init_locale()
if init_locale:
    unitregistry = pint.UnitRegistry(fmt_locale=init_locale)
else:
    unitregistry = pint.UnitRegistry()  # Use system default

unitregistry.formatter.default_format = ".2f~P"


def update_pint_locale(language: str = None, verbose: bool = False):
    """Update pint locale based on keecas language setting.

    Args:
        language: Optional language code. If None, gets from keecas config.
        verbose: If True, print debugging information about locale changes.
    """
    # Don't set locale for default English or None
    if language is None:
        from .localization.config import get_language_from_config
        from .localization import get_language

        # Get language from config system
        config_lang = get_language_from_config()
        current_lang = get_language()

        # Only set locale if explicitly configured (not default)
        if not config_lang and current_lang == 'en':
            if verbose:
                print("Skipping locale setting for default English")
            return  # Don't set locale for default English

        language = config_lang or current_lang

    # Handle English locale setting
    from .localization.config import get_language_from_config
    if language == 'en' and not get_language_from_config():
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

def pint_to_sympy(quantity: unitregistry.Quantity):
    """convert pint quantity to sympy quantity

    Args:
        quantity (UnitRegistry.Quantity): a quantity defined with the pint module

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

# Initialize locale on module import
try:
    # Always set a default locale, even for English
    default_locale = _find_best_locale('en', fallback_to_english=False)
    if default_locale:
        unitregistry.formatter.set_locale(default_locale)
except Exception:
    pass  # If initialization fails, continue without locale


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
