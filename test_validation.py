"""Test file for docstring validation - missing docstring."""


def public_function_missing_docstring(x, y):
    return x + y


def public_function_with_docstring(x, y):
    """Add two numbers together."""
    return x + y


class PublicClassMissingDocstring:
    def method(self):
        return "test"


class PublicClassWithDocstring:
    """A test class with proper docstring."""

    def method(self):
        """A method with docstring."""
        return "test"


def _private_function_no_docstring():
    return "private"
