"""Keecas: Symbolic and units-aware calculations for Jupyter notebooks.

This package combines SymPy (symbolic math), Pint (units), and Pipe (functional programming)
to provide a streamlined interface for mathematical computations with LaTeX output,
specifically designed for Quarto rendered PDF documents.
"""

# dataframe
# pipe_command
from . import pipe_command as pc

# col_wrappers
from .col_wrappers import wrap_column
from .dataframe import Dataframe

# display
from .display import (
    check,
    config,
    latex_inline_dict,
    show_eqn,
)

# formatters
from .formatters import format_value

# label
from .label import generate_label, generate_unique_label

# initialize pint
from .pint_sympy import unitregistry as u

# utils
from .utils import dict_to_eq, eq_to_dict

# Use configuration for pint format
u.formatter.default_format = config.display.pint_default_format

# initialize sympy
import sympy  # noqa: E402
from sympy import Basic, Dict, Eq, Le, S, latex, symbols  # noqa: E402
from sympy import ImmutableDenseMatrix as Matrix  # noqa: E402

## latex printing settings
sympy.init_printing(mul_symbol=config.latex.default_mul_symbol, order="none")


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
    "pc",
    "u",
    "sympy",
    "latex",
    "Eq",
    "Le",
    "symbols",
    "Basic",
    "Dict",
    "S",
    "Matrix",
    "__version__",
]

# import version
from .version import __version__  # noqa: E402
