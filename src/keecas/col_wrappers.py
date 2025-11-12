"""Column wrapper for LaTeX equation formatting.

This module provides a singledispatch-based wrapper system for decorating
columns in mathematical equations. Wrappers add prefix/suffix around formatted
values (e.g., "= " before RHS numeric values, "\\quad" before RHS text).

Wrapper Architecture:
    - Main entry point: wrap_column(value, col_index) -> tuple[str, str]
    - Type-based dispatch using @singledispatch decorator
    - Each type has a registered wrapper implementation
    - Returns (prefix, suffix) tuple for wrapping formatted values

Example:
    ```{python}
    from keecas import wrap_column, symbols

    # Define symbol
    sigma = symbols(r"\\sigma")

    # Wrap symbol in LHS (column 0)
    wrap_column(sigma, col_index=0)  # Returns: ('', '')
    ```

    ```{python}
    # Wrap integer in RHS (column 1+)
    wrap_column(42, col_index=1)  # Returns: ('= ', '')
    ```

    ```{python}
    # Wrap string in RHS
    wrap_column("verified", col_index=1)  # Returns: ('\\quad', '')
    ```

    Custom type registration:

    ```{python}
    #| eval: false
    # Define a custom type
    class MyCustomType:
        def __init__(self, data):
            self.data = data

    # Register a wrapper for it
    @wrap_column.register(MyCustomType)
    def wrap_custom(value, col_index=0, **kwargs):
        if col_index == 0:
            return ("", "")
        return (r"\\approx ", "")
    ```
"""

from functools import singledispatch
from typing import Any

from sympy import Basic


@singledispatch
def wrap_column(value: Any, col_index: int = 0, **kwargs) -> tuple[str, str]:
    """Return (prefix, suffix) for column wrapping based on value type.

    This is the main entry point for wrapping columns in keecas equations.
    Dispatches to specialized wrappers based on value type. For unhandled
    types, returns no wrapping (empty strings).

    Parameters
    ----------
    value : Any
        Value to wrap (any type)
    col_index : int, optional
        Column index - 0 for LHS, 1+ for RHS (default: 0)
        LHS columns (0) typically get no wrapping
        RHS columns (1+) get type-specific decoration
    **kwargs
        Additional arguments (reserved for future use)

    Returns
    -------
    tuple[str, str]
        (prefix, suffix) tuple for wrapping the formatted value

    Examples
    --------
    ```{python}
    from keecas import wrap_column, symbols

    # Define symbol
    x = symbols("x")

    # LHS - no wrapping
    wrap_column(x, col_index=0)  # Returns: ('', '')
    ```

    ```{python}
    # RHS integer - equals prefix
    wrap_column(42, col_index=1)  # Returns: ('= ', '')
    ```

    ```{python}
    # RHS string - quad spacing
    wrap_column("text", col_index=1)  # Returns: ('\\quad', '')
    ```

    Notes
    -----
    To register custom type wrappers:

    ```{python}
    #| eval: false
    # Define your custom type first
    class MyType:
        pass

    # Then register a wrapper for it
    @wrap_column.register(MyType)
    def wrap_mytype(value, col_index=0, **kwargs):
        if col_index == 0:
            return ("", "")
        return (r"\\approx ", "")  # Custom prefix for RHS
    ```

    Supported types (built-in registrations):
    - int: '= ' prefix for RHS
    - float: '= ' prefix for RHS
    - str: '\\quad' prefix for RHS
    - sympy.Basic: '= ' prefix for RHS
    - pint.Quantity: '= ' prefix for RHS (optional)
    - IPython.display.Markdown: '\\quad' prefix for RHS (optional)
    - IPython.display.Latex: '\\quad' prefix for RHS (optional)

    See Also
    --------
    formatters.format_value : Cell formatter for type-based LaTeX conversion
    """
    # Default fallback for unhandled types - no wrapping
    return ("", "")


# Built-in wrappers - registered with singledispatch


@wrap_column.register(int)
@wrap_column.register(float)
def wrap_numeric(value: int | float, col_index: int = 0, **kwargs) -> tuple[str, str]:
    """Wrap numeric types with equals prefix in RHS columns.

    Parameters
    ----------
    value : int | float
        Numeric value to wrap
    col_index : int, optional
        Column index (0 = LHS, 1+ = RHS)
    **kwargs
        Ignored

    Returns
    -------
    tuple[str, str]
        ('= ', '') for RHS, ('', '') for LHS
    """
    if col_index == 0:
        return ("", "")
    return ("= ", "")


@wrap_column.register(str)
def wrap_str(value: str, col_index: int = 0, **kwargs) -> tuple[str, str]:
    """Wrap strings with quad spacing in RHS columns.

    Parameters
    ----------
    value : str
        String value to wrap
    col_index : int, optional
        Column index (0 = LHS, 1+ = RHS)
    **kwargs
        Ignored

    Returns
    -------
    tuple[str, str]
        (r'\\quad', '') for RHS, ('', '') for LHS
    """
    if col_index == 0:
        return ("", "")
    return (r"\quad", "")


@wrap_column.register(Basic)
def wrap_sympy(value: Basic, col_index: int = 0, **kwargs) -> tuple[str, str]:
    """Wrap SymPy expressions with equals prefix in RHS columns.

    Parameters
    ----------
    value : Basic
        SymPy expression to wrap
    col_index : int, optional
        Column index (0 = LHS, 1+ = RHS)
    **kwargs
        Ignored

    Returns
    -------
    tuple[str, str]
        ('= ', '') for RHS, ('', '') for LHS
    """
    if col_index == 0:
        return ("", "")
    return ("= ", "")


# Optional dependency: Pint
try:
    import pint

    @wrap_column.register(pint.Quantity)
    def wrap_pint(value: pint.Quantity, col_index: int = 0, **kwargs) -> tuple[str, str]:
        """Wrap Pint quantities with equals prefix in RHS columns.

        Parameters
        ----------
        value : pint.Quantity
            Pint quantity to wrap
        col_index : int, optional
            Column index (0 = LHS, 1+ = RHS)
        **kwargs
            Ignored

        Returns
        -------
        tuple[str, str]
            ('= ', '') for RHS, ('', '') for LHS
        """
        if col_index == 0:
            return ("", "")
        return ("= ", "")

except ImportError:
    pass


# Optional dependency: IPython Markdown/Latex
try:
    from IPython.display import Latex, Markdown

    @wrap_column.register(Markdown)
    @wrap_column.register(Latex)
    def wrap_markdown(value: Markdown | Latex, col_index: int = 0, **kwargs) -> tuple[str, str]:
        """Wrap IPython Markdown/Latex objects with quad spacing in RHS columns.

        Parameters
        ----------
        value : Markdown | Latex
            Markdown or Latex object to wrap
        col_index : int, optional
            Column index (0 = LHS, 1+ = RHS)
        **kwargs
            Ignored

        Returns
        -------
        tuple[str, str]
            (r'\\quad', '') for RHS, ('', '') for LHS
        """
        if col_index == 0:
            return ("", "")
        return (r"\quad", "")

except ImportError:
    pass
