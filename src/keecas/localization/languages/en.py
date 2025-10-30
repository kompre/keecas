"""
English translations (default language).

This serves as the base language and defines all available translation keys.
"""

TRANSLATIONS = {
    # SymPy LaTeX words
    "for": "for",
    "otherwise": "otherwise",
    # Domain/Range labels from SymPy LaTeX output
    "Domain: ": "Domain: ",
    "Domain on ": "Domain on ",
    "Range": "Range",
    # Boolean verification states
    "VERIFIED": "VERIFIED",
    "NOT_VERIFIED": "NOT VERIFIED",
    # Common mathematical terms
    "True": "True",
    "False": "False",
    # Additional terms that might be useful
    "if": "if",
    "then": "then",
    "else": "else",
    "and": "and",
    "or": "or",
    "not": "not",
}

# Export for easier access
__all__ = ["TRANSLATIONS"]
