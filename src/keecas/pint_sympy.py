"""Pint-SymPy integration for unit-aware symbolic calculations.

This module bridges Pint unit registry with SymPy symbolic expressions,
providing seamless conversion between physical quantities and symbolic math.
"""

import pint
import sympy.physics.units as sympy_units
from sympy.physics.units.util import convert_to
from sympy import nsimplify, sympify
from typing import Any

def _initialize_unitregistry() -> pint.UnitRegistry:
    """Initialize Pint UnitRegistry with locale and format settings from config.

    Returns:
        Configured Pint UnitRegistry instance
    """
    from .localization.pint_locale import _get_safe_init_locale

    # Get locale based on config
    init_locale = _get_safe_init_locale()

    # Create registry with or without locale
    registry = pint.UnitRegistry(fmt_locale=init_locale)

    # Get default format from config
    try:
        from .config import get_config_manager
        config = get_config_manager()
        registry.formatter.default_format = config.options.display.pint_default_format
    except Exception:
        # Fallback if config not available during initialization
        registry.formatter.default_format = ".2f~P"

    return registry


# Initialize the global unit registry
unitregistry = _initialize_unitregistry()


def update_pint_locale(language: str | None = None, verbose: bool = False) -> None:
    """Update pint locale based on keecas language setting.

    Args:
        language: Two-letter language code. If None, gets from keecas config
        verbose: If True, print debugging information about locale changes

    Notes:
        - Automatically switches to manual mode if user intervention is detected
        - Respects disable_pint_locale configuration setting
        - Handles fallback scenarios for unsupported languages
    """
    from .localization.pint_locale import update_pint_locale as _update_pint_locale
    _update_pint_locale(unitregistry, language, verbose)

class SymPyUnitCache:
    """Cache for dynamically created SymPy units to avoid redundant creation."""

    _units: dict[str, Any] = {}

    @classmethod
    def get_or_create(cls, fullname: str, shortname: str, is_prefixed: bool) -> Any:
        """Get cached unit or create new one if it doesn't exist.

        Args:
            fullname: Full unit name (e.g., 'kilonewton')
            shortname: Short unit abbreviation (e.g., 'kN')
            is_prefixed: Whether the unit uses SI prefixes

        Returns:
            SymPy Quantity object for the unit
        """
        if fullname in cls._units:
            return cls._units[fullname]

        # Create new SymPy unit
        sympy_unit = sympy_units.Quantity(
            fullname,
            abbrev=shortname,
            is_prefixed=is_prefixed
        )

        # Cache the unit
        cls._units[fullname] = sympy_unit

        # Set as module attribute for backward compatibility
        setattr(sympy_units, fullname, sympy_unit)
        setattr(sympy_units, shortname, sympy_unit)

        return sympy_unit


def _is_unit_prefixed(unit_name: str) -> bool:
    """Check if a Pint unit uses SI prefixes.

    Args:
        unit_name: Full unit name to check

    Returns:
        True if unit is prefixed, False otherwise
    """
    return bool([x for x in unitregistry.parse_unit_name(unit_name) if x[0] != ""])


def pint_to_sympy(quantity: pint.Quantity) -> Any:
    """Convert Pint quantity to SymPy expression.

    This function is called automatically via sympy.S(pint_quantity) through
    the _sympy_ protocol defined below.

    Args:
        quantity: A Pint Quantity object with magnitude and units

    Returns:
        SymPy expression combining magnitude and units as symbolic quantities

    Notes:
        - Automatically creates new SymPy units if they don't exist
        - Uses caching to avoid redundant unit creation
        - Maintains unit relationships and dimensional analysis
        - Handles both prefixed and non-prefixed units
    """
    # Convert to Pint Quantity if Unit is passed, then extract magnitude and units
    magnitude, units = (1 * quantity).to_tuple()

    # Process each unit component
    for unit_name, exponent in units:
        fullname = unit_name
        shortname = f"{pint.Unit(fullname):~}"

        # Get or create SymPy unit (with caching)
        if hasattr(sympy_units, fullname):
            sympy_unit = getattr(sympy_units, fullname)
        else:
            sympy_unit = SymPyUnitCache.get_or_create(
                fullname,
                shortname,
                _is_unit_prefixed(fullname)
            )

        # Multiply magnitude by unit raised to exponent
        magnitude *= sympy_unit ** sympify(exponent) if exponent != 1 else sympy_unit

    return sympify(magnitude)


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
