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

    # Boolean verification states (proper English keys)
    "VERIFIED": "VERIFIED",
    "NOT_VERIFIED": "NOT VERIFIED",

    # Backward compatibility (deprecated - use VERIFIED/NOT_VERIFIED)
    "VERIFICATO": "VERIFIED",
    "NON VERIFICATO": "NOT VERIFIED",

    # Common mathematical terms that might need translation
    "True": "True",
    "False": "False",
}

# Export for easier access
__all__ = ["TRANSLATIONS"]