"""Custom dictionary-like Dataframe class for tabular mathematical data.

This module provides the Dataframe class, which maintains tabular structure
where all rows have consistent column count. It's designed specifically for
LaTeX equation rendering where keys represent row labels and values are lists
that populate columns across each row.
"""

from __future__ import annotations

import copy
from collections.abc import Hashable
from functools import singledispatch
from itertools import chain
from typing import Any


class Dataframe(dict[Hashable, list[Any]]):
    r"""Custom dictionary-like container for tabular equation data.

    Dataframe maintains tabular structure where all rows have consistent column count.
    Used by show_eqn() to create multi-column LaTeX output where keys represent row
    labels in the amsmath block and values are lists that populate columns across
    each row.

    The Dataframe can be initialized from a list of dicts (where each dict represents
    a column of data) or from a single dict (where values are lists representing rows).

    Args:
        *args: If first arg is list of dicts, initializes from column sequences.
            Otherwise, expects at most one dictionary for row-based initialization.
        filler: Value used to fill missing entries when sequences have different
            lengths. Defaults to None.
        **kwargs: Additional key-value pairs for initialization.

    Examples:
        ```{python}
        from keecas import Dataframe, symbols, u

        # Initialize from list of dicts (column-based)
        F, A = symbols(r"F, A")

        _p = {F: 100*u.kN, A: 20*u.cm**2}
        _e = {F: "F_applied", A: "A_load"}

        df = Dataframe([_p, _e])
        df
        ```

        ```{python}
        # Initialize from single dict (row-based)
        df = Dataframe({
            F: [100*u.kN, "F_applied"],
            A: [20*u.cm**2, "A_load"]
        })
        df
        ```

        ```{python}
        # Using filler for missing values
        _p = {F: 100*u.kN, A: 20*u.cm**2}
        _e = {F: "F_applied"}  # Missing A

        df = Dataframe([_p, _e], filler="--")
        df
        ```

    See Also:
        - `~~display.show_eqn`: Main function that uses Dataframe for rendering
        - `~~dataframe.create_dataframe`: Factory function for creating pre-sized Dataframes

    Notes:
        - Keys represent row labels in LaTeX output (LHS symbols)
        - Values are lists where each element becomes a column in the output
        - All rows automatically padded to same width using filler value
        - Supports dict-like operations: update, |, +
        - Order of keys preserved from first dict in list initialization
    """

    def __init__(self, *args: Any, filler: Any = None, **kwargs: Any) -> None:
        super().__init__()
        self._width: int = 0
        self._filler: Any = filler

        if args and isinstance(args[0], list) and all(isinstance(item, dict) for item in args[0]):
            self._init_from_list_of_dicts(args[0])
        else:
            self._update_initial(*args, **kwargs)

    def _init_from_list_of_dicts(self, list_of_dicts: list[dict[Hashable, Any]]) -> None:
        """
        Initialize the Dataframe from a list of dictionaries.

        Each dictionary in the list represents a sequence of values that will
        populate the columns of the LaTeX align block. The keys become row
        labels and their order is preserved from the first dictionary.

        Args:
            list_of_dicts: List of dictionaries where each dict represents a sequence.
                          The first dict determines the row labels/keys.

        Example:
            Input: [{'x': 1, 'y': 'a'}, {'x': 2, 'y': 'b'}, {'x': 3}]
            Result: {'x': [1, 2, 3], 'y': ['a', 'b', filler_value]}
        """
        # Handle empty list case
        if not list_of_dicts:
            self._width = 0
            return

        # the keys are determined by the first dict (order is important!)
        for key in list_of_dicts[0].keys():
            self[key] = [d.get(key, self._filler) for d in list_of_dicts]

        self._width = len(list_of_dicts)

    def _update_initial(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the Dataframe from dictionary arguments.

        Handles initialization when the input is a dictionary or keyword arguments,
        converting single values to lists and ensuring all columns have consistent length.

        Args:
            *args: Positional arguments (expects at most one dictionary)
            **kwargs: Keyword arguments representing column data

        Raises:
            TypeError: If more than one positional argument is provided
        """
        if args:
            if len(args) > 1:
                raise TypeError(
                    f"update expected at most 1 arguments, got {len(args)}",
                )
            other = dict(args[0])
            other.update(kwargs)
        else:
            other = kwargs

        for key, value in other.items():
            if isinstance(value, list):
                self[key] = value
            else:
                self[key] = [value]

        self._width = max(len(value) for value in self.values()) if self else 0
        self._validate_and_fill_data()

    def _validate_and_fill_data(self) -> None:
        """
        Ensure all columns have consistent length by padding with filler values.

        Extends shorter columns to match the maximum width using the filler value.
        This maintains the tabular structure where all rows have the same number of columns.
        """
        for key, value in self.items():
            if len(value) < self._width:
                self[key] = value + [self._filler] * (self._width - len(value))

    def update(self, *args: Any, **kwargs: Any) -> None:
        """
        Update the Dataframe with new data, extending width as needed.

        Similar to dict.update() but maintains tabular structure by ensuring
        all columns have consistent length after the update.

        Args:
            *args: Positional arguments (expects at most one dictionary)
            **kwargs: Keyword arguments representing new column data

        Raises:
            TypeError: If more than one positional argument is provided
        """
        if args:
            if len(args) > 1:
                raise TypeError(
                    f"update expected at most 1 arguments, got {len(args)}",
                )
            other = dict(args[0])
            other.update(kwargs)
        else:
            other = kwargs

        # Convert all values to lists if they aren't already
        for key, value in other.items():
            if not isinstance(value, list):
                other[key] = [value]

        # Find the maximum length of any value in both self and other
        max_length = max(
            [len(value) for value in self.values()]
            + [len(value) for value in other.values()]
            + [self._width],
        )

        # Update existing keys and add new ones
        for key, value in other.items():
            self[key] = value + [self._filler] * (max_length - len(value))

        # Adjust existing keys that weren't in the update data
        for key in self:
            if key not in other:
                if len(self[key]) < max_length:
                    self[key] = self[key] + [self._filler] * (max_length - len(self[key]))
                else:
                    self[key] = self[key][:max_length]

        # Update width
        self._width = max_length

    def append(self, other: Dataframe | dict[Hashable, Any] | Any, strict: bool = True) -> None:
        r"""Append a single column to the Dataframe.

        Adds one new column to the right of existing columns. Each row receives either
        the corresponding value from 'other' or the filler value if not present.

        Args:
            other: Data to append as a new column. Can be:
                - Dataframe: Uses first column of the other Dataframe (index 0)
                - dict: Uses values from the dictionary matching existing row keys
                - Any: Uses the same value for all rows in the new column
            strict: If True, only considers keys that exist in self. When False,
                ignores extra keys in 'other'. Defaults to True.

        Examples:
            ```{python}
            from keecas import Dataframe, symbols, u

            F, A = symbols(r"F, A")

            # Start with parameters
            df = Dataframe({F: [100*u.kN], A: [20*u.cm**2]})

            # Append descriptions as new column
            df.append({F: "applied force", A: "load area"})
            df
            ```

        Notes:
            - Increases width by 1 (adds one column to the right)
            - Rows without matching keys receive filler value
            - Does nothing if Dataframe has no keys yet
        """
        # Only proceed if there are existing keys to append to
        if not self.keys():
            return

        if isinstance(other, Dataframe):
            if strict:
                other = {key: other[key] for key in self.keys() if key in other}

            for key in self.keys():
                self[key].append(
                    other[key][0] if key in other and len(other[key]) > 0 else self._filler,
                )
        elif isinstance(other, dict):
            if strict:
                other = {key: other[key] for key in self.keys() if key in other}

            for key in self.keys():
                self[key].append(other[key] if key in other else self._filler)
        else:
            for key in self.keys():
                self[key].append(other)

        self._width += 1

    def extend(
        self,
        other: Dataframe | dict[Hashable, Any] | list[Any],
        strict: bool = True,
    ) -> None:
        r"""Extend the Dataframe by adding multiple columns from another source.

        Adds all columns from 'other' to the right of existing columns. This is the
        batch version of append(), useful for adding multiple columns at once.

        Args:
            other: Data to extend with. Can be:
                - Dataframe: Adds all columns from the other Dataframe
                - dict: Converts to Dataframe and extends (values as lists for multiple columns)
                - list: Extends each row with the list values (all rows get same list)
            strict: If True, only considers row keys that exist in self. When False,
                new keys from 'other' are added as new rows. Defaults to True.

        Raises:
            ValueError: If other is not a supported type (Dataframe, dict, or list).

        Examples:
            ```{python}
            from keecas import Dataframe, symbols, u, pc

            F, A, sigma = symbols(r"F, A, \sigma")

            # Start with parameters
            _p = Dataframe({F: [100*u.kN], A: [20*u.cm**2]})

            # Extend with expressions and values
            _e = Dataframe({F: ["F"], A: ["A"], sigma: ["F/A"]})
            _v = Dataframe({sigma: [5*u.MPa]}, filler=None)

            _p.extend(_e)
            _p.extend(_v, strict=False)  # Add new row sigma
            _p
            ```

        Notes:
            - Increases width by number of columns in 'other'
            - With strict=True, only existing rows are extended
            - With strict=False, new rows from 'other' are added
            - Use append() to add a single column, extend() for multiple columns
        """
        if isinstance(other, Dataframe):
            # filter keys
            if strict:
                other = Dataframe(
                    {key: other[key] for key in self.keys() if key in other},
                )
                if not other:
                    return

            other_width = other.width

            extra_keys = [k for k in other.keys() if k not in self.keys()]

            for key in chain(self.keys(), extra_keys):
                match (key in self, key in other):
                    case (True, True):
                        self[key].extend(
                            other[key] + [self._filler] * (other_width - len(other[key])),
                        )
                    case (True, False):
                        self[key].extend([self._filler] * other_width)
                    case (False, True):
                        self[key] = (
                            [self._filler] * self._width
                            + other[key]
                            + [self._filler] * (other_width - len(other[key]))
                        )

            self._width += other_width
        elif isinstance(other, dict):
            # filter keys
            if strict:
                other = {key: other[key] for key in self.keys() if key in other}
                if not other:
                    return
            self.extend(Dataframe(other), strict=strict)

            # max_len = max(len(v) if isinstance(v, list) else 1 for v in other.values())

            # for key in self.keys():
            #     if key in other:
            #         v = other[key]
            #         if isinstance(v, list):
            #             self[key].extend(v + [self._filler] * (max_len - len(v)))
            #         else:
            #             self[key].extend([v] * max_len)
            #     else:
            #         self[key].extend([self._filler] * max_len)

            # self._width += max_len
        elif isinstance(other, list):
            for key in self.keys():
                self[key].extend(other)

            self._width += len(other)
        else:
            raise ValueError(
                "Cannot extend Dataframe with this type. Use 'append' for single values.",
            )

    def __add__(self, other: Dataframe | dict[Hashable, Any] | list[Any]) -> Dataframe:
        """
        Create a new Dataframe by extending this one with other data.

        Args:
            other: Data to add (Dataframe, dict, or list)

        Returns:
            New Dataframe containing combined data

        Note:
            Uses strict=False, so new columns from other will be added.
        """
        # if not isinstance(other, Dataframe):
        #     raise ValueError("Can only add Dataframe to Dataframe")
        result = copy.deepcopy(Dataframe(self))
        result.extend(other, strict=False)
        return result

    def __or__(self, other: Dataframe | dict[Hashable, Any]) -> Dataframe:
        """
        Create a new Dataframe by updating this one with other data (| operator).

        Args:
            other: Data to merge (Dataframe or dict)

        Returns:
            New Dataframe with updated data

        Note:
            Similar to dict merge - existing keys are updated, new keys are added.
        """
        # if not isinstance(other, Dataframe):
        #     raise ValueError("Can only perform '|' operation with Dataframe")
        result = copy.deepcopy(Dataframe(self))
        result.update(other)
        return result

    @property
    def width(self) -> int:
        """Number of columns in the Dataframe."""
        return self._width

    @property
    def length(self) -> int:
        """Number of rows in the Dataframe."""
        return len(self)

    @property
    def shape(self) -> tuple[int, int]:
        """Shape of the Dataframe as (columns, rows)."""
        return (self.length, self.width)

    def __repr__(self) -> str:
        return f"Dataframe({self.dict_repr()}, shape={self.shape})"

    def dict_repr(self) -> str:
        """Get string representation as a regular dictionary."""
        return super().__repr__()

    def print_dict(self) -> None:
        """Print the Dataframe as a regular dictionary."""
        print(self.dict_repr())


def _pad_or_repeat(value: Any, width: int, default_value: Any) -> list[Any]:
    """Convert value to list of specified width.

    Args:
        value: Value to convert (list or scalar)
        width: Target list length
        default_value: Value to use for padding

    Returns:
        List of exactly width elements

    Notes:
        - If value is list: pad/truncate to exactly width
        - Otherwise: repeat value exactly width times
    """
    if isinstance(value, list):
        return value[:width] + [default_value] * max(0, width - len(value))
    else:
        return [value] * width


@singledispatch
def create_dataframe(
    seed: Any,
    keys: list[Hashable],
    width: int,
    default_value: Any = None,
) -> Dataframe:
    r"""Create a pre-sized Dataframe with specified shape and initial values.

    Factory function for creating Dataframes with predetermined dimensions. Useful
    when you know the final structure upfront and want to initialize all cells with
    specific patterns or values.

    Args:
        seed: Initial values to populate the Dataframe. Can be:
            - Scalar (Any): Same value repeated across all cells
            - list: Values applied to all rows, padded with default_value if shorter
            - dict: Per-row initialization (supports mixed list/scalar values per key)
            - Dataframe: Copy values from existing Dataframe
            - None: Fill all cells with default_value
        keys: List of keys (row labels) for the Dataframe. These become the symbol
            keys in LaTeX output when used with show_eqn().
        width: Number of columns in the Dataframe (number of cells per row).
        default_value: Value used to fill missing entries when seed doesn't cover
            all cells. Defaults to None.

    Returns:
        New Dataframe with specified shape (len(keys), width) and initialized values.

    Examples:
        ```{python}
        from keecas import symbols
        from keecas.dataframe import create_dataframe

        # Create empty structure
        x, y = symbols(r"x, y")
        df = create_dataframe(None, [x, y], width=3)
        df
        ```

        ```{python}
        # Initialize with scalar seed
        df = create_dataframe(0, [x, y], width=3)
        df
        ```

        ```{python}
        # Initialize with list seed (same for all rows)
        df = create_dataframe([1, 2], [x, y], width=2)
        df
        ```

        ```{python}
        # Per-row initialization with dict
        df = create_dataframe(
            {x: [10, 20], y: 99},  # x gets list, y gets scalar
            [x, y],
            width=2,
            default_value=-1
        )
        df
        ```

    See Also:
        - `~~dataframe.Dataframe`: Main class with initialization options
        - `~~display.show_eqn`: Function that uses Dataframe for rendering

    Notes:
        - All rows guaranteed to have exactly 'width' columns
        - List seed applies same list to all rows
        - Dict seed allows per-row customization
        - Dataframe seed handled automatically (dict subclass)
        - Useful for pre-allocating structure before filling with computed values
        - No filler parameter needed - all data constructed at correct width
    """
    # Scalar case - repeat same value for all cells
    return Dataframe({k: [seed] * width for k in keys})


@create_dataframe.register(list)
def _from_list(
    seed: list[Any],
    keys: list[Hashable],
    width: int,
    default_value: Any = None,
) -> Dataframe:
    """Create Dataframe from list seed - same list for all rows.

    Args:
        seed: List of values to use for all rows
        keys: Row labels
        width: Number of columns
        default_value: Filler for missing values

    Returns:
        New Dataframe with list applied to all rows

    Notes:
        - .copy() is REQUIRED to avoid aliasing - each row gets independent list
        - Without .copy(), all rows would share same list object
    """
    padded_list = seed[:width] + [default_value] * max(0, width - len(seed))
    return Dataframe({k: padded_list.copy() for k in keys})


@create_dataframe.register(dict)
def _from_dict(
    seed: dict[Hashable, Any],
    keys: list[Hashable],
    width: int,
    default_value: Any = None,
) -> Dataframe:
    """Create Dataframe from dict seed - per-row customization.

    Handles three cases per key:
    1. Key missing: Fill with default_value
    2. Dict[key, list]: Use specific list for that row (key-specific list)
    3. Dict[key, scalar]: Repeat scalar across that row

    Args:
        seed: Dict mapping keys to values (scalar or list)
        keys: Row labels
        width: Number of columns
        default_value: Filler for missing keys/values

    Returns:
        New Dataframe with per-row initialization

    Notes:
        - Also handles Dataframe seed (dict subclass) via inheritance
        - No separate Dataframe handler needed
        - _pad_or_repeat ensures all rows have exactly width elements
    """
    data = {key: _pad_or_repeat(seed.get(key, default_value), width, default_value) for key in keys}
    return Dataframe(data)
