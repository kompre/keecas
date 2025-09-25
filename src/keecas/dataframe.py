"""Custom dictionary-like Dataframe class for tabular mathematical data.

This module provides the Dataframe class, which maintains tabular structure
where all rows have consistent column count. It's designed specifically for
LaTeX equation rendering where keys represent row labels and values are lists
that populate columns across each row.
"""

from __future__ import annotations

import copy
from itertools import chain
from typing import Any, Hashable
from sympy import Dict as sympy_dict


class Dataframe(dict[Hashable, list[Any]]):
    def __init__(self, *args: Any, filler: Any = None, **kwargs: Any) -> None:
        """
        Initialize a Dataframe.

        If the first argument is a list of dictionaries, each dictionary represents
        a sequence of values that will populate columns in the LaTeX align block.
        The keys become row labels and values are collected into lists.
        Otherwise, the Dataframe is initialized from a single dictionary or keyword
        arguments, where keys become row labels and values are converted to lists
        of equal length using filler for missing values 
        (single values become single-item lists).

        Args:
            *args: If first arg is list of dicts, initializes from sequences.
                   Otherwise, expects at most one dictionary.
            filler: Value used to fill missing entries when sequences have different lengths
            **kwargs: Additional key-value pairs for initialization
        """
        super().__init__()
        self._width: int = 0
        self._filler: Any = filler

        if (
            args
            and isinstance(args[0], list)
            and all(isinstance(item, dict) for item in args[0])
        ):
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
                    "update expected at most 1 arguments, got %d" % len(args)
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
                    "update expected at most 1 arguments, got %d" % len(args)
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
            + [self._width]
        )

        # Update existing keys and add new ones
        for key, value in other.items():
            self[key] = value + [self._filler] * (max_length - len(value))

        # Adjust existing keys that weren't in the update data
        for key in self:
            if key not in other:
                if len(self[key]) < max_length:
                    self[key] = self[key] + [self._filler] * (
                        max_length - len(self[key])
                    )
                else:
                    self[key] = self[key][:max_length]

        # Update width
        self._width = max_length

    def append(self, other: 'Dataframe' | dict[Hashable, Any] | Any, strict: bool = True) -> None:
        """
        Append a single row to the Dataframe.

        Args:
            other: Data to append as a new row. Can be:
                  - Dataframe: Uses first row of the other Dataframe
                  - Dict: Uses values from the dictionary
                  - Any: Uses the same value for all columns
            strict: If True, only considers keys that exist in self

        Note:
            This adds exactly one row, increasing width by 1 only if there are keys to append to.
        """
        # Only proceed if there are existing keys to append to
        if not self.keys():
            return

        if isinstance(other, Dataframe):
            if strict:
                other = {key: other[key] for key in self.keys() if key in other}

            for key in self.keys():
                self[key].append(
                    other[key][0]
                    if key in other and len(other[key]) > 0
                    else self._filler
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

    def extend(self, other: 'Dataframe' | dict[Hashable, Any] | list[Any], strict: bool = True) -> None:
        """
        Extend the Dataframe by adding multiple rows from another source.

        Args:
            other: Data to extend with. Can be:
                  - Dataframe: Adds all rows from the other Dataframe
                  - Dict: Converts to Dataframe and extends
                  - List: Extends each column with the list values
            strict: If True, only considers keys that exist in self

        Raises:
            ValueError: If other is not a supported type for extension
        """
        if isinstance(other, Dataframe):
            # filter keys
            if strict:
                other = Dataframe(
                    {key: other[key] for key in self.keys() if key in other}
                )
                if not other:
                    return

            other_width = other.width

            extra_keys = [k for k in other.keys() if k not in self.keys()]

            for key in chain(self.keys(), extra_keys):
                match (key in self, key in other):
                    case (True, True):
                        self[key].extend(
                            other[key]
                            + [self._filler] * (other_width - len(other[key]))
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
                "Cannot extend Dataframe with this type. Use 'append' for single values."
            )

    def __add__(self, other: 'Dataframe' | dict[Hashable, Any] | list[Any]) -> 'Dataframe':
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

    def __or__(self, other: 'Dataframe' | dict[Hashable, Any]) -> 'Dataframe':
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


def create_dataframe(
    keys: list[Hashable],
    width: int,
    seed: Any | list[Any] | dict[Hashable, Any] | Dataframe | None = None,
    default_value: Any = None,
) -> Dataframe:
    """
    Create a Dataframe with specified keys and width, initialized with seed values.

    Args:
        keys: List of keys (row labels) for the dataframe
        width: Number of columns (width) for the dataframe
        seed: Initial values to populate the dataframe. Can be:
            - Scalar: Same value repeated across all cells
            - List: Values applied to all rows, padded with default_value
            - Dict: Per-key initialization (supports mixed list/scalar values)
            - Dataframe: Copy values from existing dataframe
            - None: Fill all cells with default_value
        default_value: Value used to fill missing entries

    Returns:
        New Dataframe with specified shape and initial values

    Example:
        >>> create_dataframe(['x', 'y'], 3, seed=0)
        Dataframe({'x': [0, 0, 0], 'y': [0, 0, 0]}, shape=(2, 3))

        >>> create_dataframe(['a', 'b'], 2, seed=[1, 2], default_value=-1)
        Dataframe({'a': [1, 2], 'b': [1, 2]}, shape=(2, 2))
    """
    df: Dataframe = Dataframe()

    if not isinstance(seed, (list, dict, Dataframe)):
        # Single value seed (can be of any type)
        for key in keys:
            df[key] = [seed] * width

    elif isinstance(seed, list):
        # List seed (applies to all rows)
        seed_list = seed[:width] + [default_value] * (width - len(seed))
        for key in keys:
            df[key] = seed_list.copy()

    elif isinstance(seed, Dataframe):
        for key in keys:
            if key in seed:
                df[key] = seed[key][:width] + [default_value] * (width - len(seed[key]))
            else:
                df[key] = [default_value] * width

    elif isinstance(seed, dict):
        for key in keys:
            if key in seed:
                if isinstance(seed[key], list):
                    # List value for this row
                    df[key] = seed[key][:width] + [default_value] * (
                        width - len(seed[key])
                    )
                else:
                    # Single value for this row
                    df[key] = [seed[key]] * width
            else:
                df[key] = [default_value] * width

    # Fill any missing rows with default_value
    for key in keys:
        if key not in df:
            df[key] = [default_value] * width

    # Set the width correctly
    df._width = width

    return df
