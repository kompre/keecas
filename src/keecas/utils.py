"""Utility functions for YAML processing, symbol handling, and image insertion.

This module provides helper functions for working with configuration files,
SymPy symbol manipulation, and Markdown image display in Jupyter notebooks.
"""

import os
from pathlib import Path
from typing import Any
from IPython.display import Markdown, display
import flatten_dict as fd
from ruamel.yaml import YAML
from sympy import Basic, symbols
from sympy.core.function import FunctionClass

yaml = YAML()
yaml.preserve_quotes = True


def load_data(main: str, updated_value: str) -> dict[str, Any]:
    # Check if main file exists
    if not os.path.exists(main):
        # Create an empty file and return an empty dict
        with open(main, "w") as f:
            pass

    # caricamento dati esistenti (generati automaticamente)
    with open(main, "r") as m:
        try:
            _main = fd.flatten(yaml.load(m))
        except ValueError:
            _main = {}

    # caricamento dei metadata (inseriti manualmente)
    with open(updated_value, "r") as m:
        _updated_value = fd.flatten(yaml.load(m))

    return fd.unflatten(_main | _updated_value)


# %% SYMPY
def escape_name(symbol_name: Any, dict_of_subs: dict[str, str] | None = None) -> str:
    name = str(symbol_name)
    for old, new in dict_of_subs.items():
        name = name.replace(old, new)
    return name


def escape_var(names: str | Any, dict_of_subs: dict[str, str] | None = None, **args: Any) -> Any:
    """estensione di sympy:var() con l'introduzione di una lista di sostituzioni per escapare i nomi dei simboli

    Args:
        names (_type_): _description_
        dict_of_subs (_type_, optional): _description_. Defaults to None.
    """

    def traverse(symbols, frame):
        """Recursively inject symbols to the global namespace."""
        for symbol in symbols:
            if isinstance(symbol, Basic):
                frame.f_globals[escape_name(symbol.name, dict_of_subs)] = symbol
            elif isinstance(symbol, FunctionClass):
                frame.f_globals[escape_name(symbol.__name__, dict_of_subs)] = symbol
            else:
                traverse(symbol, frame)

    from inspect import currentframe

    frame = currentframe().f_back

    try:
        if isinstance(names, str):
            syms = symbols(names, **args)
        else:
            syms = names

        if syms is not None:
            if isinstance(syms, Basic):
                frame.f_globals[escape_name(syms.name, dict_of_subs)] = syms
            elif isinstance(syms, FunctionClass):
                frame.f_globals[escape_name(syms.__name__, dict_of_subs)] = syms
            else:
                traverse(syms, frame)
    finally:
        del frame  # break cyclic dependencies as stated in inspect docs

    return syms


def insert_images(source_path: str | Path, dest_path: str | Path = ".", fig_opt: str = "") -> None:
    images = []

    # filtra lista di immagini -> path object
    for root, _, files in os.walk(source_path):
        for f in files:
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                image = Path(root) / f
                display(
                    Markdown(
                        f"![{image.stem}](<{image.relative_to(dest_path)}>){{{fig_opt}}}"
                    )
                )
