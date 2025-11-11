"""Utility functions for YAML processing, symbol handling, and image insertion.

This module provides helper functions for working with configuration files,
SymPy symbol manipulation, and Markdown image display in Jupyter notebooks.
"""

import os
from pathlib import Path
from typing import Any

import flatten_dict as fd
from IPython.display import Markdown, display
from ruamel.yaml import YAML
from sympy import Basic, Eq, symbols
from sympy.core.function import FunctionClass

yaml = YAML()
yaml.preserve_quotes = True


def load_data(main: str, updated_value: str) -> dict[str, Any]:
    """Load and merge YAML configuration files with hierarchical priority.

    Merges two YAML files where updated_value has priority over main.
    Creates main file if it doesn't exist. Uses flatten_dict to merge
    nested structures.

    Parameters
    ----------
    main : str
        Path to main YAML file (created if missing, lower priority)
    updated_value : str
        Path to update YAML file (higher priority, overrides main)

    Returns
    -------
    dict[str, Any]
        Merged configuration dictionary (updated_value takes precedence)

    Notes
    -----
    - Creates empty main file if it doesn't exist
    - Flattens both dicts before merging to handle nested structures
    - Unflattens result to restore original structure
    - Empty or invalid main file results in empty dict
    """
    # Check if main file exists
    if not os.path.exists(main):
        # Create an empty file and return an empty dict
        with open(main, "w"):
            pass

    # caricamento dati esistenti (generati automaticamente)
    with open(main) as m:
        try:
            _main = fd.flatten(yaml.load(m))
        except ValueError:
            _main = {}

    # caricamento dei metadata (inseriti manualmente)
    with open(updated_value) as m:
        _updated_value = fd.flatten(yaml.load(m))

    return fd.unflatten(_main | _updated_value)


# %% SYMPY
def escape_name(symbol_name: Any, dict_of_subs: dict[str, str] | None = None) -> str:
    r"""Transform symbol name by applying character substitutions.

    Converts a symbol name (typically LaTeX notation) to a valid Python identifier
    by replacing specified characters according to a substitution dictionary.

    Parameters
    ----------
    symbol_name : Any
        Symbol name to transform (converted to string).
        Can be SymPy symbol, string, or any object with __str__.
    dict_of_subs : dict[str, str] | None, optional
        Dictionary of string substitutions. Keys are characters to replace,
        values are replacement strings (default: None, returns unchanged name).

    Returns
    -------
    str
        Transformed symbol name with substitutions applied.

    Examples
    --------
    ```{python}
    from keecas.utils import escape_name

    # Transform LaTeX symbol name to valid Python identifier
    name = escape_name(r"\sigma_{Rd}", {"\\": "", "{": "_", "}": ""})
    print(name)  # Returns: 'sigma_Rd'
    ```

    ```{python}
    # Remove special characters
    name = escape_name("alpha-beta", {"-": "_"})
    print(name)  # Returns: 'alpha_beta'
    ```

    Notes
    -----
    - Only performs string transformation, does not inject into namespace
    - Use escape_var() if you need both transformation and namespace injection
    - Substitutions applied in dictionary iteration order
    - Returns original name (as string) if dict_of_subs is None

    See Also
    --------
    escape_var : Create and inject symbols with escaped names
    """
    name = str(symbol_name)
    if dict_of_subs is not None:
        for old, new in dict_of_subs.items():
            name = name.replace(old, new)
    return name


def escape_var(names: str | Any, dict_of_subs: dict[str, str] | None = None, **args: Any) -> Any:
    r"""Create and inject SymPy symbols into global namespace with escaped names.

    Extension of sympy.var() that allows symbol name substitutions for escaping
    special characters. Useful when symbol names contain characters that are not
    valid Python identifiers.

    Parameters
    ----------
    names : str | Any
        Symbol names as string (comma-separated) or existing SymPy objects.
        String format follows sympy.symbols() conventions (e.g., "x, y, z").
    dict_of_subs : dict[str, str] | None, optional
        Dictionary of string substitutions to escape symbol names.
        Keys are characters to replace, values are replacement strings.
        Applied to generate valid Python variable names (default: None).
    **args : Any
        Additional keyword arguments passed to sympy.symbols()
        (e.g., real=True, positive=True).

    Returns
    -------
    Any
        SymPy symbol(s) created. Returns single symbol for single input,
        tuple of symbols for multiple inputs.

    Examples
    --------
    ```{python}
    from keecas.utils import escape_var

    # Create symbols with special characters in LaTeX names
    # but valid Python variable names
    escape_var(r"\sigma_{Rd}, \tau_{Rd}", {"\\": "", "{": "_", "}": ""})

    # Now sigma_Rd and tau_Rd are available as Python variables
    print(sigma_Rd)  # Displays: \\sigma_{Rd}
    ```

    Notes
    -----
    - Symbols are injected into the calling scope's global namespace
    - Use escape_name() if you only need name transformation without injection
    - Useful for creating variables from LaTeX symbol names
    - Frame reference properly cleaned up to avoid cyclic dependencies

    See Also
    --------
    escape_name : Transform symbol name without namespace injection
    sympy.symbols : Create SymPy symbols (without injection)
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
    """Insert Markdown image links for all images in a directory tree.

    Walks through directory structure and displays Markdown image links
    for JPG, JPEG, and PNG files. Useful for bulk image insertion in
    Jupyter notebooks.

    Parameters
    ----------
    source_path : str | Path
        Directory to search for images (recursive)
    dest_path : str | Path, optional
        Base path for computing relative image paths (default: ".")
    fig_opt : str, optional
        Quarto figure options to append (e.g., "#fig-label" or "width=50%")

    Notes
    -----
    - Searches recursively for .jpg, .jpeg, .png files (case-insensitive)
    - Uses image stem (filename without extension) as alt text
    - Displays images immediately in Jupyter via IPython.display.Markdown
    - Computes relative paths from dest_path for portability

    Examples
    --------
    ```{python}
    #| eval: false
    from keecas.utils import insert_images

    # Insert all images from figures/ directory
    insert_images("figures/")
    ```

    ```{python}
    #| eval: false
    # With Quarto figure options
    insert_images("figures/", fig_opt="#fig-diagram width=80%")
    ```
    """
    # filtra lista di immagini -> path object
    for root, _, files in os.walk(source_path):
        for f in files:
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                image = Path(root) / f
                display(
                    Markdown(
                        f"![{image.stem}](<{image.relative_to(dest_path)}>){{{fig_opt}}}",
                    ),
                )


def dict_to_eq(result: dict[Basic, Any]) -> Eq | list[Eq]:
    """Convert a dictionary to SymPy Eq object(s).

    Converts a dictionary of symbol-value pairs to SymPy equality objects.
    Returns a single Eq if the dictionary has one item, or a list of Eq
    objects if multiple items.

    Args:
        result: Dictionary mapping SymPy symbols to values

    Returns:
        Single Eq object if one item, list of Eq objects if multiple items

    Examples:
        ```{python}
        from keecas import symbols
        from keecas.utils import dict_to_eq

        # Define symbols with subscripts
        sigma_Sd, tau_Sd = symbols(r"\\sigma_{Sd}, \tau_{Sd}")

        # Single equation
        dict_to_eq({sigma_Sd: 5})  # Returns: Eq(\\sigma_{Sd}, 5)
        ```

        ```{python}
        # Multiple equations
        dict_to_eq({sigma_Sd: 5, tau_Sd: 10})  # Returns: [Eq(\\sigma_{Sd}, 5), Eq(\tau_{Sd}, 10)]
        ```

    See Also:
        - `~~utils.eq_to_dict`: Convert SymPy Eq objects to dictionary
        - `~~display.show_eqn`: Display mathematical equations (uses dicts internally)
    """
    eq = [Eq(k, v) for k, v in result.items()]
    return eq if len(eq) > 1 else eq[0]


def eq_to_dict(result: Eq | list[Eq] | tuple[Eq, ...]) -> dict[Basic, Any]:
    """Convert SymPy Eq object(s) to dictionary.

    Converts SymPy equality objects to a dictionary mapping left-hand side
    symbols to right-hand side values. Handles single Eq objects, lists,
    or tuples of Eq objects.

    Args:
        result: Single Eq object, or list/tuple of Eq objects

    Returns:
        Dictionary mapping LHS symbols to RHS values

    Examples:
        ```{python}
        from keecas import symbols
        from keecas.utils import eq_to_dict
        from sympy import Eq

        # Define symbols with subscripts
        sigma_Sd, tau_Sd = symbols(r"\\sigma_{Sd}, \tau_{Sd}")

        # Single equation
        eq_to_dict(Eq(sigma_Sd, 5))  # Returns: {\\sigma_{Sd}: 5}
        ```

        ```{python}
        # Multiple equations
        eq_to_dict([Eq(sigma_Sd, 5), Eq(tau_Sd, 10)])  # Returns: {\\sigma_{Sd}: 5, \tau_{Sd}: 10}
        ```

    See Also:
        - `~~utils.dict_to_eq`: Convert dictionary to SymPy Eq objects
        - `~~display.show_eqn`: Display mathematical equations (uses dicts internally)
    """
    if hasattr(result, "__iter__"):
        return {x.lhs: x.rhs for x in result}
    else:
        return {result.lhs: result.rhs}
