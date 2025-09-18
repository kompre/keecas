"""
Dutch translations.

Contains Dutch translations for all LaTeX/SymPy strings used in keecas.
"""

TRANSLATIONS = {
    # SymPy LaTeX words
    "for": "voor",
    "otherwise": "anders",

    # Boolean verification states
    "VERIFIED": "GEVERIFIEERD",
    "NOT_VERIFIED": "NIET GEVERIFIEERD",

    # Backward compatibility (deprecated)
    "VERIFICATO": "GEVERIFIEERD",
    "NON VERIFICATO": "NIET GEVERIFIEERD",

    # Common mathematical terms
    "True": "Waar",
    "False": "Onwaar",

    # Additional terms that might be useful
    "if": "als",
    "then": "dan",
    "else": "anders",
    "and": "en",
    "or": "of",
    "not": "niet",
}

# Export for easier access
__all__ = ["TRANSLATIONS"]