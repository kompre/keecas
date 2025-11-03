"""
Stable, repeatable unique ID generator for Python objects.

This module provides a deterministic hash function that generates short alphanumeric
lowercase IDs suitable for use as automatic reference labels.
"""

import hashlib
from collections.abc import Hashable
from functools import singledispatch
from typing import Any

from keecas.config.manager import get_config_manager

config = get_config_manager().options


def _generate_id(obj: Any, length: int = 8) -> str:
    r"""
    Generate a stable, unique ID for any Python object.

    Args:
        obj: Any Python object (sympy symbols, str, dict, list, etc.)
        length: Desired length of the ID (default: 8)

    Returns:
        A lowercase alphanumeric string of specified length

    Examples:
        ```{python}
        from keecas import symbols
        from keecas.label import generate_id

        # Define symbol with subscript
        sigma_Sd = symbols(r"\sigma_{Sd}")

        # Generate stable ID for symbol
        generate_id(sigma_Sd)  # Returns: 'a1b2c3d4' (example, always same for this symbol)
        ```

        ```{python}
        # Custom length
        generate_id("test_string", length=6)  # Returns: 'x9y8z7' (example)
        ```
    """
    # Create a stable string representation
    obj_str = _serialize_object(obj)

    # Generate SHA-256 hash
    hash_obj = hashlib.sha256(obj_str.encode("utf-8"))
    hash_hex = hash_obj.hexdigest()

    # Convert to base36 (0-9, a-z) for compact alphanumeric representation
    # Take first 20 hex chars (80 bits) for conversion
    hash_int = int(hash_hex[:20], 16)
    out_str = _to_base36(hash_int)

    # Return first 'length' characters
    return out_str[:length].lower()


def _serialize_object(obj: Any) -> str:
    """Create a stable string representation of an object."""
    # Try to use repr first (works for sympy symbols and most objects)
    try:
        # For sympy objects, repr gives a stable representation
        obj_repr = repr(obj)
        # Verify it's stable by checking if it's a simple repr
        if obj_repr and not obj_repr.startswith("<"):
            return obj_repr
    except Exception:
        pass

    # Handle specific types
    if isinstance(obj, str):
        return f"str:{obj}"
    elif isinstance(obj, (int, float, complex)):
        return f"{type(obj).__name__}:{obj}"
    elif isinstance(obj, (list, tuple)):
        return f"{type(obj).__name__}:[{','.join(_serialize_object(x) for x in obj)}]"
    elif isinstance(obj, dict):
        items = sorted((k, v) for k, v in obj.items())
        return f"dict:{{{','.join(f'{_serialize_object(k)}:{_serialize_object(v)}' for k, v in items)}}}"
    elif isinstance(obj, set):
        return f"set:{{{','.join(sorted(_serialize_object(x) for x in obj))}}}"

    # Fallback to repr
    return repr(obj)


def _to_base36(num: int) -> str:
    """Convert an integer to base36 string (0-9, a-z)."""
    if num == 0:
        return "0"

    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    result = []

    while num > 0:
        result.append(digits[num % 36])
        num //= 36

    return "".join(reversed(result))


@singledispatch
def generate_label(arg: Any, unique_id: bool = False) -> Any:
    """Generate formatted label text for use with show_eqn.

    This function processes label inputs and returns formatted label strings
    that include the configured prefix and suffix. It supports multiple input
    types through singledispatch.

    Args:
        arg: Label input. Can be:
            - str: Single label string
            - dict: Dictionary mapping keys to label strings
            - list: Converted to string representation, then labeled
        unique_id: If True, generate a unique hash-based ID instead of using
            the provided label text. Defaults to False.

    Returns:
        Formatted label(s) with prefix and suffix applied:
        - str input returns formatted str
        - dict input returns dict with formatted values
        - list input returns formatted str (converted via str())

    Examples:
        ```{python}
        from keecas import symbols, generate_label

        # String label
        generate_label("my-label")  # Returns: 'eq-my-label'
        ```

        ```{python}
        # Dict label with subscripted symbols
        F, A_load = symbols(r"F, A_{load}")
        labels = {F: "force", A_load: "area"}
        generate_label(labels)  # Returns: {F: 'eq-force', A_{load}: 'eq-area'}
        ```

        ```{python}
        # List label (converted to string)
        generate_label(["item1", "item2"])  # Returns: "eq-['item1', 'item2']"
        ```

        ```{python}
        # Unique ID generation
        label = generate_label("key", unique_id=True)
        label.startswith("eq-")  # Returns: True
        ```

    See Also:
        - `~~label.generate_unique_label`: Convenience function for unique ID generation
        - `~~display.show_eqn`: Main display function that uses labels

    Notes:
        - Labels are formatted with config.latex.eq_prefix and config.latex.eq_suffix
        - Callable labels should be passed directly to show_eqn, not to generate_label
        - Unique IDs are deterministic hash-based identifiers
    """
    raise TypeError(f"Unsupported type for generate_label: {type(arg)}")


@generate_label.register(str)
def _(arg: str, unique_id: bool = False) -> str:
    """Generate label from string input."""

    if unique_id:
        label_text = _generate_id(arg)
    else:
        label_text = arg

    return f"{config.latex.eq_prefix}{label_text}{config.latex.eq_suffix}"


@generate_label.register(dict)
def _(arg: dict[Hashable, str], unique_id: bool = False) -> dict[Hashable, str]:
    """Generate labels from dict input.

    For each key-value pair in the dict:
    - If value is a string, format it with prefix/suffix
    - If value is None or empty, return empty string
    """

    result = {}
    for key, value in arg.items():
        if value:
            if unique_id:
                label_text = _generate_id((key, value))
            else:
                label_text = value
            result[key] = f"{config.latex.eq_prefix}{label_text}{config.latex.eq_suffix}"
        else:
            result[key] = ""

    return result


@generate_label.register(list)
def _(arg: list, unique_id: bool = False):
    """Generate label from list input by converting to string representation."""
    return generate_label(str(arg), unique_id=unique_id)


def generate_unique_label(arg: str | dict[Hashable, Any]) -> str | dict[Hashable, str]:
    """Generate unique hash-based labels.

    Convenience function that calls generate_label with unique_id=True.
    Useful for automatically generating deterministic labels without
    manual naming.

    Args:
        arg: Label input (str or dict)

    Returns:
        Formatted label(s) with unique hash-based identifiers

    Examples:
        ```{python}
        from keecas import symbols, generate_unique_label

        # String label
        label = generate_unique_label("my-key")
        label.startswith("eq-")  # Returns: True
        ```

        ```{python}
        # Dict label with subscripted symbols
        F, A_load = symbols(r"F, A_{load}")
        labels = generate_unique_label({F: "force", A_load: "area"})
        all(v.startswith("eq-") for v in labels.values())  # Returns: True
        ```

        ```{python}
        # Can be used with partial functions
        from functools import partial
        auto_labeler = partial(generate_unique_label)
        auto_labeler("test")  # Returns: 'eq-...' (hash-based ID)
        ```

    See Also:
        - `~~label.generate_label`: Main label generation function
        - `~~display.show_eqn`: Display function that uses labels

    Notes:
        - Generates deterministic hash-based IDs
        - Same input always produces same ID
        - Useful for automatic label generation in Dataframes
    """
    return generate_label(arg, unique_id=True)
