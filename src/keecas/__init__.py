"""Keecas: Symbolic and units-aware calculations for Jupyter notebooks.

This package combines SymPy (symbolic math), Pint (units), and Pipe (functional programming)
to provide a streamlined interface for mathematical computations with LaTeX output,
specifically designed for Quarto rendered PDF documents.
"""

# dataframe
from .dataframe import Dataframe

# display
from .display import (
    config,
    show_eqn,
    check,
    dict_to_eq,
    eq_to_dict,
)

# formatters
from .formatters import (
    EarlyExit,
    FormatterChain,
    default_formatter_chain,
    validate_latex_kwargs,
    format_markdown,
    format_pint,
    format_mul,
    format_sympy,
    format_float,
    format_int,
    format_str,
)

# pipe_command
from . import pipe_command as pc

# initialize pint
from .pint_sympy import unitregistry as u, update_pint_locale

# Use configuration for pint format
u.formatter.default_format = config.pint_default_format

# initialize sympy
import sympy
from sympy import latex, Eq, Le, symbols, Basic, Dict, S, ImmutableDenseMatrix as Matrix

## latex printing settings
sympy.init_printing(mul_symbol=config.latex.default_mul_symbol, order="none")
platex = lambda x: latex(x, mode="inline", mul_symbol=config.latex.default_mul_symbol)

## common sympy functions
__all__ = [
    "Dataframe",
    "show_eqn",
    "config",
    "check",
    "dict_to_eq",
    "eq_to_dict",
    # Formatter exports (chain-based)
    "EarlyExit",
    "FormatterChain",
    "default_formatter_chain",
    "validate_latex_kwargs",
    "format_markdown",
    "format_pint",
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
]

# import version
from .version import __version__
