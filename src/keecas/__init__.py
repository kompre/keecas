"""Keecas: Symbolic and units-aware calculations for Jupyter notebooks.

This package combines SymPy (symbolic math), Pint (units), and Pipe (functional programming)
to provide a streamlined interface for mathematical computations with LaTeX output,
specifically designed for Quarto rendered PDF documents.

Performance Optimization:
This package uses lazy imports for ALL modules that depend on heavy dependencies (sympy, pint).
This ensures fast startup time for CLI commands like `keecas --version`.
Heavy imports are only loaded when first accessed via __getattr__.
"""

# Only import truly lightweight modules (no sympy/pint dependencies)
from .version import __version__

# All exports (most are lazy-loaded)
__all__ = [
    "Dataframe",
    "show_eqn",
    "config",
    "check",
    "latex_inline_dict",
    "dict_to_eq",
    "eq_to_dict",
    "generate_label",
    "generate_unique_label",
    "wrap_column",
    "format_value",
    # Heavy dependencies (lazy)
    "pc",  # pipe_command
    "u",  # pint unitregistry
    "sympy",  # sympy module
    "latex",  # sympy.latex
    "Eq",  # sympy.Eq
    "Le",  # sympy.Le
    "symbols",  # sympy.symbols
    "Basic",  # sympy.Basic
    "Dict",  # sympy.Dict
    "S",  # sympy.S
    "Matrix",  # sympy.ImmutableDenseMatrix
    "__version__",
]


def _ensure_config_loaded():
    """Ensure the correct config object (ConfigOptions) is loaded.

    Prevents namespace collision with keecas.config package module.

    Keecas exposes two things named "config":
    - keecas.config (package): src/keecas/config/ containing ConfigManager
    - keecas.config (object): ConfigOptions instance from display.py

    This function guarantees that globals()["config"] is the ConfigOptions
    object by checking for the presence of the "display" attribute, which
    only ConfigOptions has, not the package module.

    Returns:
        ConfigOptions: The configuration object from display.py
    """
    if "config" not in globals() or not hasattr(globals()["config"], "display"):
        from .display import config

        globals()["config"] = config
    return globals()["config"]


def __getattr__(name):
    """Lazy load dependencies.

    This function is called when an attribute is not found in the module's global namespace.
    We use it to defer imports of ALL modules that depend on heavy dependencies (sympy, pint)
    until they're actually needed, significantly improving import time for CLI commands.

    The loaded modules are cached in globals() to avoid re-importing on subsequent access.
    """
    # config is needed by other lazy loads, so load it first if requested
    if name == "config":
        return _ensure_config_loaded()

    # Dataframe - actually lightweight, no sympy/pint
    elif name == "Dataframe":
        from .dataframe import Dataframe

        globals()["Dataframe"] = Dataframe
        return Dataframe

    # display module exports (depend on sympy via formatters/col_wrappers)
    elif name == "show_eqn":
        from .display import show_eqn

        globals()["show_eqn"] = show_eqn
        return show_eqn

    elif name == "check":
        from .display import check

        globals()["check"] = check
        return check

    elif name == "latex_inline_dict":
        from .display import latex_inline_dict

        globals()["latex_inline_dict"] = latex_inline_dict
        return latex_inline_dict

    # utils module (depends on sympy)
    elif name == "dict_to_eq":
        from .utils import dict_to_eq

        globals()["dict_to_eq"] = dict_to_eq
        return dict_to_eq

    elif name == "eq_to_dict":
        from .utils import eq_to_dict

        globals()["eq_to_dict"] = eq_to_dict
        return eq_to_dict

    # label module (depends on sympy)
    elif name == "generate_label":
        from .label import generate_label

        globals()["generate_label"] = generate_label
        return generate_label

    elif name == "generate_unique_label":
        from .label import generate_unique_label

        globals()["generate_unique_label"] = generate_unique_label
        return generate_unique_label

    # col_wrappers (depends on sympy)
    elif name == "wrap_column":
        from .col_wrappers import wrap_column

        globals()["wrap_column"] = wrap_column
        return wrap_column

    # formatters (depends on sympy)
    elif name == "format_value":
        from .formatters import format_value

        globals()["format_value"] = format_value
        return format_value

    # Lazy load pint unit registry
    elif name == "u":
        # Need config first
        _ensure_config_loaded()

        from .pint_sympy import unitregistry as u

        # Configure pint format (was at module level in original __init__.py)
        u.formatter.default_format = globals()["config"].display.pint_default_format

        globals()["u"] = u
        return u

    # Lazy load pipe_command
    elif name == "pc":
        from . import pipe_command as pc

        globals()["pc"] = pc
        return pc

    # Lazy load sympy module
    elif name == "sympy":
        # Need config first
        _ensure_config_loaded()

        import sympy

        # Initialize sympy printing (was at module level in original __init__.py)
        sympy.init_printing(mul_symbol=globals()["config"].latex.default_mul_symbol, order="none")

        globals()["sympy"] = sympy
        return sympy

    # Lazy load sympy exports - batch load them all together for efficiency
    elif name in ("latex", "Eq", "Le", "symbols", "Basic", "Dict", "S"):
        # Need config first
        _ensure_config_loaded()

        import sympy
        from sympy import Basic, Dict, Eq, Le, S, latex, symbols

        # Initialize printing if sympy not already loaded
        if "sympy" not in globals():
            sympy.init_printing(
                mul_symbol=globals()["config"].latex.default_mul_symbol, order="none"
            )
            globals()["sympy"] = sympy

        # Cache all sympy exports at once
        globals().update(
            {
                "latex": latex,
                "Eq": Eq,
                "Le": Le,
                "symbols": symbols,
                "Basic": Basic,
                "Dict": Dict,
                "S": S,
            }
        )

        return globals()[name]

    # Lazy load Matrix (separate because it's imported as ImmutableDenseMatrix)
    elif name == "Matrix":
        # Need config first
        _ensure_config_loaded()

        import sympy
        from sympy import ImmutableDenseMatrix as Matrix

        # Initialize printing if sympy not already loaded
        if "sympy" not in globals():
            sympy.init_printing(
                mul_symbol=globals()["config"].latex.default_mul_symbol, order="none"
            )
            globals()["sympy"] = sympy

        globals()["Matrix"] = Matrix
        return Matrix

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
