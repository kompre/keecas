# dataframe
from .dataframe import Dataframe

# display
from .display import (
    options,
    show_eqn,
    check,
    verifica,  # backward compatibility alias
    dict_to_eq,
    eq_to_dict,
)

# configuration
from .config import config

# pipe_command
from . import pipe_command as pc

# initialize pint
from .pint_sympy import unitregistry as u, update_pint_locale

# Use configuration for pint format
from .config import get_options
u.formatter.default_format = get_options().pint_default_format

# initialize sympy
import sympy as sp

from sympy import latex, Eq, Le, symbols, Basic, Dict, S, ImmutableDenseMatrix as Matrix

## latex printing settings
sp.init_printing(mul_symbol=options.default_mul_symbol, order="none")
platex = lambda x: latex(x, mode="inline", mul_symbol=options.default_mul_symbol)

## common sympy functions
__all__ = [
    "Dataframe",
    "show_eqn",
    "options",
    "config",  # New configuration interface
    "check",
    "verifica",  # backward compatibility alias
    "dict_to_eq",
    "eq_to_dict",
    "pc",
    "u",
    "update_pint_locale",  # Pint localization control
    "sp",
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
