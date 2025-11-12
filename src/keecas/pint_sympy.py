"""Pint-SymPy integration for unit-aware symbolic calculations.

This module bridges Pint unit registry with SymPy symbolic expressions,
providing seamless conversion between physical quantities and symbolic math.

It patches the Pint `Quantity` and `Unit` class to add the `_sympy_` method, which
automatically converts Pint quantities to SymPy expressions with units.
"""

from typing import Any

import pint
import sympy.physics.units as sympy_units
from sympy import nsimplify, sympify
from sympy.physics.units.util import convert_to


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
        from .config.manager import get_config_manager

        config = get_config_manager()
        registry.formatter.default_format = config.options.display.pint_default_format
    except Exception:
        # Fallback if config not available during initialization
        registry.formatter.default_format = ".2f~P"

    return registry


# Initialize the global unit registry
unitregistry = _initialize_unitregistry()


def update_pint_locale(language: str | None = None, verbose: bool = False) -> None:
    r"""Update Pint unit formatter locale for international unit names.

    Changes how units are displayed in Pint quantities, switching between compact
    symbols (kN) and localized full names (kilonewton, chiloNewton, etc.). Useful
    for engineering documentation in different languages. Automatically called when
    config.language changes, but can be invoked manually for custom locale control.

    NOTE: Respects config.language.disable_pint_locale setting. When True (default),
    preserves compact unit symbols. When False, enables locale-specific unit names.

    Args:
        language: Two-letter language code (de, es, fr, it, pt for full support;
            da, nl, no, sv, en for keecas translations only). If None, uses language
            from keecas config. Defaults to None.
        verbose: If True, prints debugging information about locale changes including
            before/after states and configuration status. Useful for troubleshooting
            locale behavior. Defaults to False.

    Examples:
        ```{python}
        from keecas import u
        from keecas.pint_sympy import update_pint_locale

        # Manual locale control with verbose output
        update_pint_locale('it', verbose=True)

        F = 100*u.kN
        print(f"{F}")  # Shows: 100 chiloNewton
        ```

        ```{python}
        # Manual locale control with verbose output
        update_pint_locale('de', verbose=True)

        A = 50*u.cm**2
        print(f"{A}")  # Shows: 50 Zentimeter ** 2
        ```

        ```{python}
        from keecas import config, u

        # Keep compact symbols (default behavior)
        config.language.disable_pint_locale = True  # Default

        F = 100*u.kN
        print(f"{F}")  # Shows: 100 kN (compact symbol preserved)
        ```

        ```{python}
        # Fallback language behavior
        update_pint_locale('sv')  # Swedish - no Pint locale available

        # Unit names stay in English, but keecas terms (VERIFIED, etc.) are Swedish
        F = 100*u.kN
        print(f"{F}")  # Shows: 100 kilonewton (English fallback)
        ```

    Notes:
        - Automatically called when config.language changes
        - Respects config.language.disable_pint_locale (default: True)
        - Full Pint locale support: de, es, fr, it, pt (5 languages)
        - Fallback to English units: da, nl, no, sv, en (5 languages)
        - Conservative behavior: doesn't change locale unnecessarily
        - Manual mode activated if user directly modifies unitregistry.formatter
    """
    from .localization.pint_locale import _update_pint_locale_impl

    _update_pint_locale_impl(unitregistry, language, verbose)


class SymPyUnitCache:
    r"""Cache for dynamically created SymPy units to avoid redundant creation.

    Maintains a registry of SymPy unit objects created from Pint definitions,
    ensuring each unit is only created once and properly configured with scale
    factors for unit conversion. Used internally by pint_to_sympy() for efficient
    Pint-to-SymPy conversion.
    """

    _units: dict[str, Any] = {}

    @classmethod
    def get_or_create(cls, fullname: str, shortname: str, is_prefixed: bool) -> Any:
        r"""Get cached SymPy unit or create new one with conversion scale factors.

        Retrieves cached SymPy unit object or creates new one from Pint definition,
        setting up proper scale factors for unit conversion. Handles both prefixed
        units (kN, cm) using SymPy's prefix system and non-prefixed compound units
        (kgf, lbf) by extracting scale factors from Pint base unit conversion.

        Args:
            fullname: Full unit name from Pint definition (e.g., 'kilonewton',
                'centimeter', 'kilogram_force'). Used as SymPy Quantity name.
            shortname: Short unit abbreviation for display (e.g., 'kN', 'cm', 'kgf').
                Used as SymPy Quantity abbreviation.
            is_prefixed: Whether the unit uses SI prefixes (True for kN, cm; False
                for kgf, lbf). Prefixed units handled by SymPy automatically,
                non-prefixed units require explicit scale factors from Pint.

        Returns:
            SymPy Quantity object configured for unit conversion. Cached for reuse.

        Examples:
            ```{python}
            from keecas.pint_sympy import SymPyUnitCache

            # Get or create prefixed unit (kN)
            kN = SymPyUnitCache.get_or_create('kilonewton', 'kN', is_prefixed=True)

            # Get or create non-prefixed unit (kgf)
            kgf = SymPyUnitCache.get_or_create('kilogram_force', 'kgf', is_prefixed=False)

            # Subsequent calls return cached objects
            kN_cached = SymPyUnitCache.get_or_create('kilonewton', 'kN', is_prefixed=True)
            assert kN is kN_cached
            ```

        Notes:
            - Prefixed units (kN, daN, cm) handled automatically by SymPy prefix system
            - Non-prefixed units (kgf, lbf) get scale factors from Pint base unit conversion
            - Scale factors enable full conversion capabilities via pc.convert_to()
            - Created units added to sympy.physics.units module for backward compatibility
            - Cache prevents redundant unit creation and ensures consistency
        """
        if fullname in cls._units:
            return cls._units[fullname]

        # Create new SymPy unit
        sympy_unit = sympy_units.Quantity(
            fullname,
            abbrev=shortname,
            is_prefixed=is_prefixed,
        )

        # Set scale factor for non-prefixed units (prefixed units handled by SymPy)
        if not is_prefixed:
            try:
                # Get base unit conversion from Pint
                pint_unit = 1 * pint.Unit(fullname)
                base_quantity = pint_unit.to_base_units()
                pint_magnitude, base_units = base_quantity.to_tuple()

                # Build reference from base units and track SymPy scale factors
                reference = sympify(1)
                sympy_scale = sympify(1)

                for unit_name, exponent in base_units:
                    if hasattr(sympy_units, unit_name):
                        unit_obj = getattr(sympy_units, unit_name)
                        reference *= unit_obj ** nsimplify(exponent)

                        # Accumulate SymPy's scale factors
                        if hasattr(unit_obj, "scale_factor"):
                            sympy_scale *= unit_obj.scale_factor**exponent
                    else:
                        # Base unit doesn't exist in SymPy - skip scale factor
                        break
                else:
                    # All base units exist - set scale factor
                    # Adjust magnitude by SymPy's reference scale factors
                    adjusted_magnitude = float(pint_magnitude * sympy_scale)
                    sympy_unit.set_global_relative_scale_factor(adjusted_magnitude, reference)
            except Exception:
                # If scale factor setup fails, unit still works but won't convert
                pass

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
    r"""Convert Pint quantities to SymPy expressions with units.

    Bridges Pint's physical quantities with SymPy's symbolic math, enabling
    symbolic calculations with units. Called automatically via SymPy's _sympy_
    protocol when using sympify() or SymPy operations on Pint quantities.
    Creates SymPy units dynamically as needed and configures them for full
    conversion support.

    NOTE: This function is called automatically by SymPy. Users typically don't
    invoke it directly - just use Pint quantities in SymPy expressions.

    Args:
        quantity: Pint Quantity object with magnitude and units (e.g., 100*u.kN,
            50*u.cm**2). Can also be pint.Unit object (treated as 1*unit).

    Returns:
        SymPy expression combining magnitude and units as symbolic quantities,
        ready for symbolic manipulation and unit conversion.

    Examples:
        ```{python}
        from keecas import symbols, u, pc, show_eqn
        from sympy import sympify

        # Automatic conversion via sympify
        F_pint = 100*u.kN
        F_sympy = sympify(F_pint)  # Calls pint_to_sympy automatically

        print(type(F_pint))   # <class 'pint.Quantity'>
        print(type(F_sympy))  # <class 'sympy.Mul'>
        ```

        ```{python}
        # Use in symbolic expressions
        F, A_load = symbols(r"F, A_{load}")

        _p = {
            F: 100*u.kN,      # Pint quantity
            A_load: 50*u.cm**2
        }

        # Pint quantities automatically converted in SymPy operations
        sigma = symbols(r"\sigma")
        _e = {
            sigma: "F / A_load" | pc.parse_expr
        }

        _v = {
            k: v | pc.subs(_p | _e) | pc.convert_to([u.MPa]) | pc.N
            for k, v in _e.items()
        }

        show_eqn([_p | _e, _v])
        ```

        ```{python}
        # Compound units with exponents
        A = 50*u.cm**2  # Area

        # Automatically handles exponents
        A_sympy = sympify(A)
        print(A_sympy)  # 50*centimeter**2
        ```

        ```{python}
        # Custom Pint units work seamlessly
        pressure = 10*u.MPa
        force = 100*u.kgf  # Non-SI unit

        # Both convert correctly in SymPy
        p_sympy = sympify(pressure)
        f_sympy = sympify(force) | pc.convert_to(u.N)
        ```

    Notes:
        - Automatically creates new SymPy units if they don't exist in sympy.physics.units
        - Uses SymPyUnitCache to avoid redundant unit creation
        - Maintains unit relationships and dimensional analysis capabilities
        - Handles both prefixed units (kN, cm) and non-prefixed units (kgf, lbf)
        - Configured via _sympy_ protocol: Pint objects work directly in SymPy expressions
        - All Pint units convert correctly via pc.convert_to() after conversion
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
                _is_unit_prefixed(fullname),
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
