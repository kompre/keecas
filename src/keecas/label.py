"""
Stable, repeatable unique ID generator for Python objects.

This module provides a deterministic hash function that generates short alphanumeric
lowercase IDs suitable for use as automatic reference labels.
"""

import hashlib
from typing import Any


def generate_id(obj: Any, length: int = 8) -> str:
    """
    Generate a stable, unique ID for any Python object.

    Args:
        obj: Any Python object (sympy symbols, str, dict, list, etc.)
        length: Desired length of the ID (default: 8)

    Returns:
        A lowercase alphanumeric string of specified length

    Examples:
        >>> from sympy import symbols
        >>> x = symbols('x')
        >>> generate_id(x)  # Will always return same ID for symbol 'x'
        >>> generate_id("test_string", length=6)
    """
    # Create a stable string representation
    obj_str = _serialize_object(obj)

    # Generate SHA-256 hash
    hash_obj = hashlib.sha256(obj_str.encode("utf-8"))
    hash_hex = hash_obj.hexdigest()

    # Convert to base36 (0-9, a-z), or numeric (0-9) for more compact representation
    # Take first 20 hex chars (80 bits) for conversion
    hash_int = int(hash_hex[:20], 16)
    match type:
        case "alphanumeric":
            out_str = _to_base36(hash_int)
        case "numeric":
            out_str = str(hash_int)

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
