import pint
import sympy.physics.units as sympy_units
from sympy.physics.units.util import convert_to

from sympy import nsimplify, sympify


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


# Initialize UnitRegistry with locale support
unitregistry = pint.UnitRegistry(fmt_locale=_get_locale_from_keecas())
unitregistry.formatter.default_format = ".2f~P"


def update_pint_locale(language: str = None):
    """Update pint locale based on keecas language setting.

    Args:
        language: Optional language code. If None, gets from keecas config.
    """
    if language is None:
        locale_str = _get_locale_from_keecas()
    else:
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
        locale_str = locale_map.get(language, 'en_US')

    # Update the locale in the existing registry
    unitregistry.formatter.set_locale(locale_str)

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
