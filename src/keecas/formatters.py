"""Cell and row formatters for LaTeX equation rendering.

This module provides an extensible registry system for formatting cell values
in mathematical equations. Users can register custom formatters for specific
types using decorators or runtime registration.

Formatter Return Values:
    - Return string: Use this formatted output
    - Return None: Skip to next formatter in priority order (conditional formatting)
    - Return "": Use empty string (explicit empty cell)

Example:
    Basic formatter:

    >>> from keecas import cell_formatter
    >>>
    >>> @cell_formatter(int, priority=20)
    >>> def format_int(value, col_index, **kwargs):
    ...     if col_index == 0:
    ...         return str(value)
    ...     return f"= {value}"

    Conditional formatter (returns None to skip):

    >>> @cell_formatter(int, priority=5)  # Higher priority - tried first
    >>> def format_large_int(value, col_index, **kwargs):
    ...     if value > 1000:
    ...         return rf"\\mathbf{{{value}}}"  # Bold large numbers
    ...     return None  # Skip to next formatter for small numbers
"""

from typing import Any, Callable, TypeVar
import inspect

from sympy import latex, Basic, S
from IPython.display import Markdown
import pint

T = TypeVar('T')
FormatterFunc = Callable[[Any, int, dict], str]  # (value, col_index, **kwargs) -> str


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


class CellFormatterRegistry:
    """Extensible registry for type-based cell formatters with priority ordering.

    Formatters are matched using isinstance(), so more specific types should
    have higher priority (lower priority number). First matching type wins.

    Attributes:
        _formatters: Internal dict mapping (type, formatter_id) to (function, priority)
    """

    def __init__(self):
        """Initialize registry and load default formatters."""
        # Use regular dict (Python 3.7+ preserves insertion order)
        self._formatters: dict[tuple[type, int], tuple[FormatterFunc, int]] = {}
        self._load_defaults()

    def register(self, type_class: type[T], formatter: FormatterFunc, priority: int = 50) -> None:
        """Register a formatter for a type with priority (lower = higher priority).

        Args:
            type_class: Type to match with isinstance()
            formatter: Function(value, col_index) -> str
            priority: Lower values = higher priority (0-100, default 50)

        Example:
            >>> registry = CellFormatterRegistry()
            >>> def format_my_type(value, col_index):
            ...     return f"custom: {value}"
            >>> registry.register(MyType, format_my_type, priority=25)
        """
        # Insert maintaining priority order
        key = (type_class, id(formatter))
        self._formatters[key] = (formatter, priority)
        # Re-sort by priority
        self._formatters = dict(
            sorted(self._formatters.items(), key=lambda x: x[1][1])
        )

    def format(self, value: Any, col_index: int, **kwargs) -> str:
        """Format value using first matching type formatter.

        Formatters are tried in priority order. If a formatter returns None,
        it means "I can't handle this value, try the next formatter".
        This allows for conditional formatting based on value properties.

        Args:
            value: Value to format
            col_index: Column index (0 = first column/LHS, 1+ = RHS)
            **kwargs: Additional keyword arguments to pass to latex() function
                (e.g., mul_symbol, mode, etc.)

        Returns:
            LaTeX string representation (never None - fallback ensures this)

        Note:
            - If formatter returns None: Skip to next formatter in priority order
            - If formatter returns "" (empty string): Use empty string (explicit)
            - Ultimate fallback: latex(value, **kwargs)
        """
        for (type_class, _), (formatter, _) in self._formatters.items():
            if isinstance(value, type_class):
                result = formatter(value, col_index, **kwargs)
                # If formatter returns None, continue to next formatter
                if result is not None:
                    return result

        # Ultimate fallback - always return LaTeX-compatible output
        return latex(value, **kwargs)

    def _load_defaults(self):
        """Load built-in formatters."""
        # Priority 10: Specific types first
        self.register(Markdown, self._format_markdown, priority=10)
        self.register(pint.Quantity, self._format_pint, priority=15)

        # Priority 30: SymPy types (broader match)
        self.register(Basic, self._format_sympy, priority=30)

        # Priority 70: Python built-ins (fallback)
        self.register(float, self._format_float, priority=70)
        self.register(int, self._format_int, priority=70)
        self.register(str, self._format_str, priority=70)

    def _format_markdown(self, value: Markdown, col_index: int, **kwargs) -> str:
        """Format Markdown objects.

        Args:
            value: Markdown object
            col_index: Column index
            **kwargs: Ignored for Markdown (passed for consistency)
        """
        if col_index == 0:
            return rf"\text{{{value.data}}}"
        else:
            return rf"\quad\text{{{value.data}}}"

    def _format_pint(self, value: pint.Quantity, col_index: int, **kwargs) -> str:
        """Format Pint quantities.

        Args:
            value: Pint Quantity
            col_index: Column index
            **kwargs: Passed to latex() function for SymPy conversion
        """
        latex_str = latex(S(value), **kwargs)
        if col_index == 0:
            return latex_str
        else:
            return f"= {latex_str}"

    def _format_sympy(self, value: Basic, col_index: int, **kwargs) -> str:
        """Format SymPy expressions.

        Args:
            value: SymPy Basic object
            col_index: Column index
            **kwargs: Passed to latex() function (e.g., mul_symbol, mode)
        """
        latex_str = latex(value, **kwargs)
        if col_index == 0:
            return latex_str
        else:
            return f"= {latex_str}"

    def _format_float(self, value: float, col_index: int, **kwargs) -> str:
        """Format Python floats.

        Args:
            value: Float value
            col_index: Column index
            **kwargs: Ignored for floats (passed for consistency)
        """
        if col_index == 0:
            return str(value)
        else:
            return f"= {value}"

    def _format_int(self, value: int, col_index: int, **kwargs) -> str:
        """Format Python integers.

        Args:
            value: Integer value
            col_index: Column index
            **kwargs: Ignored for integers (passed for consistency)
        """
        if col_index == 0:
            return str(value)
        else:
            return f"= {value}"

    def _format_str(self, value: str, col_index: int, **kwargs) -> str:
        """Format Python strings.

        Args:
            value: String value
            col_index: Column index
            **kwargs: Ignored for strings (passed for consistency)
        """
        if col_index == 0:
            return rf"\text{{{value}}}"
        else:
            return rf"\quad\text{{{value}}}"


# Global default registry
default_cell_formatter_registry = CellFormatterRegistry()


def default_cell_formatter(value: Any, col_index: int, **kwargs) -> str:
    """Default cell formatter using the global registry.

    Args:
        value: Cell value to format
        col_index: Column index (0 = first column/LHS, 1+ = RHS columns)
        **kwargs: Additional keyword arguments passed to latex() function
            (e.g., mul_symbol, mode, etc.)

    Returns:
        LaTeX string representation

    Example:
        >>> from sympy import Symbol
        >>> x = Symbol('x')
        >>> default_cell_formatter(x, 0)
        'x'
        >>> default_cell_formatter(x, 1)
        '= x'
        >>> default_cell_formatter(x, 0, mul_symbol='dot')
        'x'
    """
    return default_cell_formatter_registry.format(value, col_index, **kwargs)


def cell_formatter(type_class: type[T], priority: int = 50):
    """Decorator to register custom cell formatters.

    Args:
        type_class: Type to match with isinstance()
        priority: Lower values = higher priority (0-100, default 50)

    Returns:
        Decorator function

    Example:
        >>> @cell_formatter(MyClass, priority=20)
        ... def format_my_class(value: MyClass, col_index: int) -> str:
        ...     if col_index == 0:
        ...         return f"LHS: {value}"
        ...     return f"RHS: {value}"
    """
    def decorator(func: FormatterFunc) -> FormatterFunc:
        default_cell_formatter_registry.register(type_class, func, priority)
        return func
    return decorator
