# dataframe
from .dataframe import Dataframe

# display
from .display import (
    options,
    show_eqn,
    verifica,
    dict_to_eq,
    eq_to_dict,
)

# pipe_command
from . import pipe_command as pc

# initialize pint
from .pint_sympy import unitregistry as u

u.formatter.default_format = ".2f~P"

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
    "verifica",
    "dict_to_eq",
    "eq_to_dict",
    "pc",
    "u",
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
