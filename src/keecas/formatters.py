"""Cell and row formatters for LaTeX equation rendering.

This module provides an extensible registry system for formatting cell values
in mathematical equations. Users can register custom formatters for specific
types using decorators or runtime registration.

Example:
    Register a custom formatter for NumPy arrays:

    >>> from keecas import cell_formatter
    >>> import numpy as np
    >>>
    >>> @cell_formatter(np.ndarray, priority=20)
    >>> def format_numpy(arr, col_index):
    ...     if col_index == 0:
    ...         return r"\\mathbf{A}"
    ...     return matrix_to_latex(arr)
"""

from typing import Any, Callable, TypeVar

from sympy import latex, Basic, S
from IPython.display import Markdown
import pint

T = TypeVar('T')
FormatterFunc = Callable[[Any, int], str]  # (value, col_index) -> str


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

    def format(self, value: Any, col_index: int) -> str:
        """Format value using first matching type formatter.

        Args:
            value: Value to format
            col_index: Column index (0 = first column/LHS, 1+ = RHS)

        Returns:
            LaTeX string representation
        """
        for (type_class, _), (formatter, _) in self._formatters.items():
            if isinstance(value, type_class):
                return formatter(value, col_index)

        # Ultimate fallback - always return LaTeX-compatible output
        return latex(value)

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

    def _format_markdown(self, value: Markdown, col_index: int) -> str:
        """Format Markdown objects."""
        if col_index == 0:
            return rf"\text{{{value.data}}}"
        else:
            return rf"\quad\text{{{value.data}}}"

    def _format_pint(self, value: pint.Quantity, col_index: int) -> str:
        """Format Pint quantities."""
        latex_str = latex(S(value))
        if col_index == 0:
            return latex_str
        else:
            return f"= {latex_str}"

    def _format_sympy(self, value: Basic, col_index: int) -> str:
        """Format SymPy expressions."""
        latex_str = latex(value)
        if col_index == 0:
            return latex_str
        else:
            return f"= {latex_str}"

    def _format_float(self, value: float, col_index: int) -> str:
        """Format Python floats."""
        if col_index == 0:
            return str(value)
        else:
            return f"= {value}"

    def _format_int(self, value: int, col_index: int) -> str:
        """Format Python integers."""
        if col_index == 0:
            return str(value)
        else:
            return f"= {value}"

    def _format_str(self, value: str, col_index: int) -> str:
        """Format Python strings."""
        if col_index == 0:
            return rf"\text{{{value}}}"
        else:
            return rf"\quad\text{{{value}}}"


# Global default registry
default_cell_formatter_registry = CellFormatterRegistry()


def default_cell_formatter(value: Any, col_index: int) -> str:
    """Default cell formatter using the global registry.

    Args:
        value: Cell value to format
        col_index: Column index (0 = first column/LHS, 1+ = RHS columns)

    Returns:
        LaTeX string representation

    Example:
        >>> from sympy import Symbol
        >>> x = Symbol('x')
        >>> default_cell_formatter(x, 0)
        'x'
        >>> default_cell_formatter(x, 1)
        '= x'
    """
    return default_cell_formatter_registry.format(value, col_index)


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
