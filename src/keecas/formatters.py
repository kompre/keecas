"""Cell and row formatters for LaTeX equation rendering.

This module provides a chain-based formatter system for formatting cell values
in mathematical equations. Formatters are executed in explicit order, allowing
easy modification and prototyping in Jupyter notebooks.

Formatter Return Values:
    - Return EarlyExit(result): Stop chain, use this result
    - Return transformed value: Pass to next formatter in chain
    - Return None: Skip to next formatter (no transformation)

Example:
    Basic chain with transformers and terminals:

    >>> from keecas import FormatterChain, EarlyExit
    >>> from sympy import Basic, latex, S
    >>> import pint
    >>>
    >>> def format_pint(value, col_index=None, **kwargs):
    ...     '''Transform Pint to SymPy.'''
    ...     if isinstance(value, pint.Quantity):
    ...         return S(value)  # Transform, continue chain
    ...     return None  # Skip
    ...
    >>> def format_sympy(value, col_index=None, **kwargs):
    ...     '''Render SymPy to LaTeX.'''
    ...     if isinstance(value, Basic):
    ...         latex_str = latex(value, **kwargs)
    ...         return EarlyExit(latex_str)  # Done!
    ...     return None
    ...
    >>> chain = FormatterChain([format_pint, format_sympy])
    >>> print(chain)  # See order
    FormatterChain([format_pint, format_sympy])

    Modifying chain in notebook (no kernel restart needed):

    >>> # Add debug formatter
    >>> def debug_fmt(value, col_index=None, **kwargs):
    ...     print(f"Debug: {type(value)=}")
    ...     return None
    ...
    >>> chain.insert(0, debug_fmt)  # Add at beginning
    >>> chain.remove(debug_fmt)     # Remove it
    >>> chain.move_up(format_sympy)  # Reorder
"""

from typing import Any, Callable
import inspect

from sympy import latex, Basic, S, Mul
from IPython.display import Markdown
import pint


def validate_latex_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Validate and filter kwargs for sympy.latex() function.

    Args:
        kwargs: Dictionary of keyword arguments to validate

    Returns:
        Filtered dict containing only valid latex() parameters

    Raises:
        ValueError: If any invalid parameter names are provided
    """
    # Get valid latex() parameters
    latex_sig = inspect.signature(latex)
    valid_params = set(latex_sig.parameters.keys()) - {'expr'}  # Exclude positional 'expr'

    # Check for invalid parameters
    invalid_params = set(kwargs.keys()) - valid_params
    if invalid_params:
        raise ValueError(
            f"Invalid latex() parameters: {', '.join(invalid_params)}. "
            f"Valid parameters are: {', '.join(sorted(valid_params))}"
        )

    return kwargs


class EarlyExit:
    """Sentinel to signal chain should stop and return result.

    When a formatter returns EarlyExit(result), the chain stops executing
    and returns the wrapped result string immediately.

    Example:
        >>> def format_int(value, col_index=None, **kwargs):
        ...     if isinstance(value, int):
        ...         return EarlyExit(str(value))  # Stop chain
        ...     return None  # Continue to next formatter
    """

    def __init__(self, result: str):
        """Initialize EarlyExit with result string.

        Args:
            result: The formatted string to return from chain
        """
        self.result = result

    def __repr__(self):
        return f"EarlyExit({self.result!r})"


class FormatterChain:
    """Chain of formatters executed in explicit order.

    Formatters are regular functions stored in a list, making it easy to
    inspect, modify, and reorder them without kernel restart.

    Attributes:
        formatters: List of formatter functions (publicly accessible)

    Example:
        >>> chain = FormatterChain([format_pint, format_sympy])
        >>> print(chain)  # See current order
        >>> chain.insert(0, my_formatter)  # Add at beginning
        >>> chain.move_up(format_sympy)    # Reorder
    """

    def __init__(self, formatters: list[Callable] | None = None):
        """Initialize formatter chain.

        Args:
            formatters: List of formatter functions. Each should have signature:
                (value, col_index, **kwargs) -> str | EarlyExit | None
        """
        self.formatters = formatters or []

    def __call__(self, value: Any, col_index: int, **kwargs) -> str:
        """Execute formatter chain on value.

        Formatters are executed in order until one returns EarlyExit or
        all formatters complete.

        Args:
            value: Value to format
            col_index: Column index (0 = LHS, 1+ = RHS)
            **kwargs: Additional arguments passed to latex() and formatters

        Returns:
            Formatted LaTeX string

        Chain Semantics:
            - Formatter returns EarlyExit(result): Stop, return result
            - Formatter returns transformed value: Pass to next formatter
            - Formatter returns None: Skip to next formatter
            - No formatter handles: Fall back to latex(value, **kwargs)
        """
        current_value = value

        for formatter in self.formatters:
            result = formatter(current_value, col_index, **kwargs)

            if isinstance(result, EarlyExit):
                return result.result  # Stop chain
            elif result is not None:
                current_value = result  # Transform, continue
            # None = skip to next

        # Fallback: no formatter returned EarlyExit
        return latex(current_value, **kwargs)

    def __repr__(self):
        """Show formatter names for easy inspection."""
        names = [f.__name__ for f in self.formatters]
        return f"FormatterChain({names})"

    # Helper methods for chain manipulation

    def insert(self, index: int, formatter: Callable) -> None:
        """Insert formatter at specific position.

        Args:
            index: Position to insert at
            formatter: Formatter function to insert
        """
        self.formatters.insert(index, formatter)

    def remove(self, formatter: Callable) -> None:
        """Remove formatter from chain.

        Args:
            formatter: Formatter function to remove
        """
        self.formatters.remove(formatter)

    def append(self, formatter: Callable) -> None:
        """Append formatter to end of chain.

        Args:
            formatter: Formatter function to append
        """
        self.formatters.append(formatter)

    def clear(self) -> None:
        """Remove all formatters from chain."""
        self.formatters.clear()

    def move(self, formatter: Callable, new_index: int) -> None:
        """Move formatter to new position in chain.

        Args:
            formatter: The formatter function to move
            new_index: Target index position

        Example:
            >>> chain.move(format_pint, 0)  # Move to beginning
            >>> chain.move(format_sympy, -1)  # Move to end
        """
        current_index = self.formatters.index(formatter)
        self.formatters.pop(current_index)
        self.formatters.insert(new_index, formatter)

    def move_up(self, formatter: Callable, steps: int = 1) -> None:
        """Move formatter toward beginning of chain (lower index).

        Args:
            formatter: The formatter function to move
            steps: Number of positions to move up (default 1)

        Example:
            >>> chain.move_up(format_pint)      # Move up by 1
            >>> chain.move_up(format_sympy, 2)  # Move up by 2
        """
        current_index = self.formatters.index(formatter)
        new_index = max(0, current_index - steps)
        self.formatters.pop(current_index)
        self.formatters.insert(new_index, formatter)

    def move_down(self, formatter: Callable, steps: int = 1) -> None:
        """Move formatter toward end of chain (higher index).

        Args:
            formatter: The formatter function to move
            steps: Number of positions to move down (default 1)

        Example:
            >>> chain.move_down(format_pint)      # Move down by 1
            >>> chain.move_down(format_sympy, 2)  # Move down by 2
        """
        current_index = self.formatters.index(formatter)
        new_index = min(len(self.formatters) - 1, current_index + steps)
        self.formatters.pop(current_index)
        self.formatters.insert(new_index, formatter)


# Built-in formatters

def format_markdown(value, col_index: int = 0, **kwargs) -> EarlyExit | None:
    """Format Markdown objects.

    Args:
        value: Value to check
        col_index: Column index (0 = LHS, 1+ = RHS)
        **kwargs: Ignored

    Returns:
        EarlyExit with LaTeX text if Markdown, None otherwise
    """
    if isinstance(value, Markdown):
        if col_index == 0:
            return EarlyExit(rf"\text{{{value.data}}}")
        else:
            return EarlyExit(rf"\quad\text{{{value.data}}}")
    return None


def format_pint(value, col_index: int = 0, **kwargs) -> Basic | None:
    """Convert Pint quantities to SymPy.

    This is a transformer - it returns the converted value for the next
    formatter (likely format_sympy) to handle.

    Args:
        value: Value to check
        col_index: Column index (not used)
        **kwargs: Passed through

    Returns:
        SymPy expression if Pint Quantity, None otherwise
    """
    if isinstance(value, pint.Quantity):
        return S(value)  # Transform to SymPy, continue chain
    return None


def format_mul(value, col_index: int = 0, **kwargs) -> Mul | None:
    """Transform Mul without symbols to separated numeric+unit form.

    If the object is a Mul without any symbols (e.g., 5*meter), it represents
    a numeric value multiplied by a unit. Transform it using as_two_terms for
    better formatting where numeric and unit parts are visually separated.

    Args:
        value: Value to check and potentially transform
        col_index: Column index (not used)
        **kwargs: Passed through

    Returns:
        Transformed Mul as UnevaluatedExpr if applicable, None otherwise

    Example:
        Input:  5*meter (Mul with no free symbols)
        Output: UnevaluatedExpr(5) * UnevaluatedExpr(meter)
        LaTeX: "5 \\cdot \\mathrm{meter}" instead of "5meter"
    """
    # Import here to avoid circular dependency
    from keecas import pipe_command as pc

    if isinstance(value, Mul) and not value.free_symbols:
        # Transform to separated form: numeric * unit
        transformed = value | pc.as_two_terms(as_mul=True)
        return transformed  # Continue to next formatter (likely format_sympy)

    return None  # Not a Mul or has symbols, skip


def format_sympy(value, col_index: int = 0, **kwargs) -> EarlyExit | None:
    """Format SymPy expressions to LaTeX.

    Args:
        value: Value to check
        col_index: Column index (0 = LHS, 1+ = RHS)
        **kwargs: Passed to latex() function (e.g., mul_symbol, mode)

    Returns:
        EarlyExit with LaTeX string if SymPy Basic, None otherwise
    """
    if isinstance(value, Basic):
        latex_str = latex(value, **kwargs)
        if col_index == 0:
            return EarlyExit(latex_str)
        else:
            return EarlyExit(f"= {latex_str}")
    return None


def format_float(value, col_index: int = 0, **kwargs) -> EarlyExit | None:
    """Format Python floats.

    Args:
        value: Value to check
        col_index: Column index (0 = LHS, 1+ = RHS)
        **kwargs: Ignored

    Returns:
        EarlyExit with string if float, None otherwise
    """
    if isinstance(value, float):
        if col_index == 0:
            return EarlyExit(str(value))
        else:
            return EarlyExit(f"= {value}")
    return None


def format_int(value, col_index: int = 0, **kwargs) -> EarlyExit | None:
    """Format Python integers.

    Args:
        value: Value to check
        col_index: Column index (0 = LHS, 1+ = RHS)
        **kwargs: Ignored

    Returns:
        EarlyExit with string if int, None otherwise
    """
    if isinstance(value, int):
        if col_index == 0:
            return EarlyExit(str(value))
        else:
            return EarlyExit(f"= {value}")
    return None


def format_str(value, col_index: int = 0, **kwargs) -> EarlyExit | None:
    """Format Python strings.

    Args:
        value: Value to check
        col_index: Column index (0 = LHS, 1+ = RHS)
        **kwargs: Ignored

    Returns:
        EarlyExit with LaTeX text if string, None otherwise
    """
    if isinstance(value, str):
        if col_index == 0:
            return EarlyExit(rf"\text{{{value}}}")
        else:
            return EarlyExit(rf"\quad\text{{{value}}}")
    return None


# Default formatter chain with built-in formatters
default_formatter_chain = FormatterChain([
    format_markdown,  # Terminal: Markdown objects
    format_pint,      # Transformer: Pint → SymPy
    format_mul,       # Transformer: numeric Mul → separated form
    format_sympy,     # Terminal: SymPy expressions
    format_float,     # Terminal fallback: float
    format_int,       # Terminal fallback: int
    format_str,       # Terminal fallback: str
])
