"""Cell and row formatters for LaTeX equation rendering.

This module provides a singledispatch-based formatter system for formatting
cell values in mathematical equations. Formatters are dispatched based on
value type, providing a clean and extensible interface.

Formatter Architecture:
    - Main entry point: format_value(value, col_index, **kwargs) -> str
    - Type-based dispatch using @singledispatch decorator
    - Each type has a registered formatter implementation
    - Transformers (Pint, Mul) call other formatters directly
    - Fallback to sympy.latex() for unhandled types

Example:
    ```{python}
    from keecas import format_value, symbols

    # Define symbol with subscript
    sigma_Rd = symbols(r"\\sigma_{Rd}")

    # Format symbol (column 0 - LHS)
    format_value(sigma_Rd, col_index=0)  # Returns: '\\sigma_{Rd}'
    ```

    ```{python}
    # Format float (pure conversion, no decoration)
    format_value(3.14159, col_index=1)  # Returns: '3.14159'
    ```

    ```{python}
    # Format string
    format_value("hello", col_index=0)  # Returns: '\\text{hello}'
    ```

    Custom type registration:

    ```{python}
    #| eval: false
    # Define a custom type
    class MyCustomType:
        def __init__(self, data):
            self.data = data

    # Register a formatter for it
    @format_value.register(MyCustomType)
    def format_custom(value, col_index=0, **kwargs):
        return r"\\text{Custom: " + str(value.data) + "}"
    ```
"""

import inspect
from functools import singledispatch
from typing import Any

from sympy import Basic, Mul, S, latex


def validate_latex_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Validate and filter kwargs for sympy.latex() function.

    Parameters
    ----------
    kwargs : dict[str, Any]
        Dictionary of keyword arguments to validate

    Returns
    -------
    dict[str, Any]
        Filtered dict containing only valid latex() parameters

    Raises
    ------
    ValueError
        If any invalid parameter names are provided
    """
    # Get valid latex() parameters
    latex_sig = inspect.signature(latex)
    valid_params = set(latex_sig.parameters.keys()) - {"expr"}  # Exclude positional 'expr'

    # Check for invalid parameters
    invalid_params = set(kwargs.keys()) - valid_params
    if invalid_params:
        raise ValueError(
            f"Invalid latex() parameters: {', '.join(invalid_params)}. "
            f"Valid parameters are: {', '.join(sorted(valid_params))}",
        )

    return kwargs


@singledispatch
def format_value(value: Any, col_index: int = 0, **kwargs) -> str:
    """Format a value to LaTeX string using type-based dispatch.

    This is the main entry point for formatting values in keecas equations.
    Dispatches to specialized formatters based on value type. For unhandled
    types, falls back to sympy.latex().

    Parameters
    ----------
    value : Any
        Value to format (any type)
    col_index : int, optional
        Column index - 0 for LHS, 1+ for RHS (default: 0)
        Kept for API consistency but not used by default formatters
    **kwargs
        Additional arguments passed to latex() function
        (e.g., mul_symbol, mode, fold_frac_powers)

    Returns
    -------
    str
        LaTeX string representation

    Examples
    --------
    ```{python}
    from keecas import format_value, symbols

    # Define symbol with subscript
    sigma_Rd = symbols(r"\\sigma_{Rd}")

    # Format symbol (LHS)
    format_value(sigma_Rd)  # Returns: '\\sigma_{Rd}'
    ```

    ```{python}
    # Format integer (pure conversion)
    format_value(42, col_index=1)  # Returns: '42'
    ```

    ```{python}
    # Format string
    format_value("text", col_index=0)  # Returns: '\\text{text}'
    ```

    Notes
    -----
    To register custom type formatters:

    ```{python}
    #| eval: false
    # Define your custom type first
    class MyType:
        pass

    # Then register a formatter for it
    @format_value.register(MyType)
    def format_mytype(value, col_index=0, **kwargs):
        return r"\\text{My custom format}"
    ```

    Supported types (built-in registrations):
    - str: Plain text wrapped in \\text{}
    - int: Integer to LaTeX string
    - float: Float to LaTeX string
    - IPython.display.Markdown: Wrapped in \\text{}
    - pint.Quantity: Converted to SymPy, then formatted
    - sympy.Mul: Numeric/unit separation, then formatted as Basic
    - sympy.Basic: LaTeX via sympy.latex()

    See Also
    --------
    format_str : String formatter
    format_int : Integer formatter
    format_float : Float formatter
    format_sympy : SymPy expression formatter
    """
    # Default fallback for unhandled types
    return latex(value, **kwargs)


# Built-in formatters - registered with singledispatch


@format_value.register(str)
def format_str(value: str, col_index: int = 0, **kwargs) -> str:
    """Format Python strings to LaTeX text.

    Pure conversion: wraps string in \\text{} without additional decoration.
    Column wrapping (e.g., \\quad prefix) is handled by wrap_column().

    Parameters
    ----------
    value : str
        String value to format
    col_index : int, optional
        Column index (kept for API consistency, not used)
    **kwargs
        Ignored

    Returns
    -------
    str
        LaTeX string with \\text{} wrapper
    """
    return rf"\text{{{value}}}"


@format_value.register(int)
def format_int(value: int, col_index: int = 0, **kwargs) -> str:
    """Format Python integers to LaTeX.

    Pure conversion: converts int to string without additional decoration.
    Column wrapping (e.g., '= ' prefix) is handled by wrap_column().

    Parameters
    ----------
    value : int
        Integer value to format
    col_index : int, optional
        Column index (kept for API consistency, not used)
    **kwargs
        Ignored

    Returns
    -------
    str
        LaTeX string representation of integer
    """
    return str(value)


@format_value.register(float)
def format_float(value: float, col_index: int = 0, **kwargs) -> str:
    """Format Python floats to LaTeX.

    Pure conversion: converts float to string without additional decoration.
    Column wrapping (e.g., '= ' prefix) is handled by wrap_column().
    Float precision formatting is handled by format_decimal_numbers()
    in display.py after this formatter returns the string.

    Parameters
    ----------
    value : float
        Float value to format
    col_index : int, optional
        Column index (kept for API consistency, not used)
    **kwargs
        Ignored

    Returns
    -------
    str
        LaTeX string representation of float
    """
    return str(value)


# Optional dependency: IPython Markdown
try:
    from IPython.display import Latex, Markdown

    @format_value.register(Markdown)
    def format_markdown(value: Markdown, col_index: int = 0, **kwargs) -> str:
        """Format IPython Markdown objects to LaTeX text.

        Pure conversion: wraps Markdown data in \\text{} without additional decoration.
        Column wrapping (e.g., \\quad prefix) is handled by wrap_column().

        Parameters
        ----------
        value : Markdown
            Markdown object to format
        col_index : int, optional
            Column index (kept for API consistency, not used)
        **kwargs
            Ignored

        Returns
        -------
        str
            LaTeX string with \\text{} wrapper
        """
        return rf"\text{{{value.data}}}"

    @format_value.register(Latex)
    def format_latex(value: Latex, col_index: int = 0, **kwargs) -> str:
        """Format IPython Latex objects to LaTeX text.

        Pure conversion: wraps Latex data in \\text{} without additional decoration.
        Column wrapping (e.g., \\quad prefix) is handled by wrap_column().

        Parameters
        ----------
        value : Latex
            Latex object to format
        col_index : int, optional
            Column index (kept for API consistency, not used)
        **kwargs
            Ignored

        Returns
        -------
        str
            LaTeX string with \\text{} wrapper
        """
        return rf"\text{{{value.data}}}"

except ImportError:
    pass


# Optional dependency: Pint
try:
    import pint

    @format_value.register(pint.Quantity)
    def format_pint(value: pint.Quantity, col_index: int = 0, **kwargs) -> str:
        """Format Pint quantities by converting to SymPy first.

        This is a transformer formatter - it converts Pint Quantity to
        SymPy expression, then calls format_sympy() directly.

        Transformation chain: Quantity -> SymPy -> format_sympy

        Parameters
        ----------
        value : pint.Quantity
            Pint quantity to format
        col_index : int, optional
            Column index (0 = LHS, 1+ = RHS)
        **kwargs
            Passed to format_sympy()

        Returns
        -------
        str
            LaTeX string from SymPy formatting
        """
        sympy_expr = S(value)  # Convert to SymPy
        return format_value(sympy_expr, col_index, **kwargs)

except ImportError:
    pass


@format_value.register(Mul)
def format_mul(value: Mul, col_index: int = 0, **kwargs) -> str:
    """Format Mul expressions with numeric/unit separation.

    For Mul without free symbols (e.g., 5*meter), applies transformation
    to separate numeric and unit parts, then formats as SymPy Basic.

    Transformation: 5*meter -> UnevaluatedExpr(5) * UnevaluatedExpr(meter)
    LaTeX output: "5 \\cdot \\mathrm{meter}" instead of "5meter"

    Parameters
    ----------
    value : Mul
        Multiplication expression to format
    col_index : int, optional
        Column index (0 = LHS, 1+ = RHS)
    **kwargs
        Passed to format_sympy()

    Returns
    -------
    str
        LaTeX string representation
    """
    # Import here to avoid circular dependency
    from keecas import pipe_command as pc

    if not value.free_symbols:
        # Transform to separated form: numeric * unit
        transformed = value | pc.as_two_terms(as_mul=True)
        # Call format_sympy directly (Mul is a Basic subclass)
        return format_sympy(transformed, col_index, **kwargs)

    # Has symbols - format as regular SymPy expression
    return format_sympy(value, col_index, **kwargs)


@format_value.register(Basic)
def format_sympy(value: Basic, col_index: int = 0, **kwargs) -> str:
    """Format SymPy expressions to LaTeX.

    This is the main formatter for all SymPy objects (Basic subclasses).
    Pure conversion: converts SymPy to LaTeX without additional decoration.
    Column wrapping (e.g., '= ' prefix) is handled by wrap_column().

    Parameters
    ----------
    value : Basic
        SymPy expression to format
    col_index : int, optional
        Column index (kept for API consistency, not used)
    **kwargs
        Passed to sympy.latex() function (e.g., mul_symbol, mode)

    Returns
    -------
    str
        LaTeX string representation
    """
    return latex(value, **kwargs)
