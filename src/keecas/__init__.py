"""Keecas: Symbolic and units-aware calculations for Jupyter notebooks.

This package combines SymPy (symbolic math), Pint (units), and Pipe (functional programming)
to provide a streamlined interface for mathematical computations with LaTeX output,
specifically designed for Quarto rendered PDF documents.
"""

# dataframe
# pipe_command
from . import pipe_command as pc

# col_wrapper
from .col_wrapper import wrap_column
from .dataframe import Dataframe

# display
from .display import (
    check,
    config,
    latex_inline_dict,
    show_eqn,
)

# formatters
from .formatters import (
    format_float,
    format_int,
    format_mul,
    format_str,
    format_sympy,
    format_value,
    validate_latex_kwargs,
)

# utils
from .utils import dict_to_eq, eq_to_dict

# Import optional formatters if available (for type registration)
try:
    from .formatters import format_latex  # noqa: F401
except ImportError:
    pass

try:
    from .formatters import format_markdown  # noqa: F401
except ImportError:
    pass

try:
    from .formatters import format_pint  # noqa: F401
except ImportError:
    pass

# label
from .label import generate_label, generate_unique_label

# initialize pint
from .pint_sympy import unitregistry as u
from .pint_sympy import update_pint_locale

# Use configuration for pint format
u.formatter.default_format = config.display.pint_default_format

# initialize sympy
import sympy  # noqa: E402
from sympy import Basic, Dict, Eq, Le, S, latex, symbols  # noqa: E402
from sympy import ImmutableDenseMatrix as Matrix  # noqa: E402

## latex printing settings
sympy.init_printing(mul_symbol=config.latex.default_mul_symbol, order="none")


def platex(x):
    """Print LaTeX in inline mode with configured multiplication symbol."""
    return latex(x, mode="inline", mul_symbol=config.latex.default_mul_symbol)


## common sympy functions
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
    # Column wrapper (singledispatch-based)
    "wrap_column",
    # Formatter exports (singledispatch-based)
    "format_value",
    "validate_latex_kwargs",
    "format_mul",
    "format_sympy",
    "format_float",
    "format_int",
    "format_str",
    "pc",
    "u",
    "update_pint_locale",  # Pint localization control
    "sympy",
    "latex",
    "Eq",
    "Le",
    "symbols",
    "Basic",
    "Dict",
    "S",
    "Matrix",
    "platex",
    "__version__",
]

# import version
from .version import __version__  # noqa: E402
