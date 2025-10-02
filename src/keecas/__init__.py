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
    default_cell_formatter_registry,
    default_cell_formatter,
    cell_formatter,
    validate_latex_kwargs,
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
    "default_cell_formatter_registry",
    "default_cell_formatter",
    "cell_formatter",
    "validate_latex_kwargs",
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

# Auto-import user custom formatters
import importlib.util
import sys
from pathlib import Path


def _try_import_formatters(formatter_path: Path) -> None:
    """Try to import a formatters.py file if it exists.

    Args:
        formatter_path: Path to formatters.py file to import
    """
    if formatter_path.exists() and formatter_path.is_file():
        try:
            spec = importlib.util.spec_from_file_location(
                f"keecas_user_formatters_{formatter_path.parent.name}",
                formatter_path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
        except Exception:
            # Silently ignore import errors - user formatters are optional
            pass


# Check for user formatter files (in priority order: local > global)
# Global: ~/.keecas/formatters.py
global_formatters = Path.home() / ".keecas" / "formatters.py"
_try_import_formatters(global_formatters)

# Local: <project>/.keecas/formatters.py
# Use current working directory as project root
local_formatters = Path.cwd() / ".keecas" / "formatters.py"
_try_import_formatters(local_formatters)

# Check for custom path in config
if hasattr(config, 'custom_formatters_file') and config.custom_formatters_file:
    custom_path = Path(config.custom_formatters_file)
    _try_import_formatters(custom_path)
