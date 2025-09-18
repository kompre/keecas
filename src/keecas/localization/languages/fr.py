"""
French translations.

Contains French translations for all LaTeX/SymPy strings used in keecas.
"""

TRANSLATIONS = {
    # SymPy LaTeX words
    "for": "pour",
    "otherwise": "sinon",

    # Boolean verification states
    "VERIFIED": "VÉRIFIÉ",
    "NOT_VERIFIED": "NON VÉRIFIÉ",

    # Backward compatibility (deprecated)
    "VERIFICATO": "VÉRIFIÉ",
    "NON VERIFICATO": "NON VÉRIFIÉ",

    # Common mathematical terms
    "True": "Vrai",
    "False": "Faux",

    # Additional terms that might be useful
    "if": "si",
    "then": "alors",
    "else": "sinon",
    "and": "et",
    "or": "ou",
    "not": "non",
}

# Export for easier access
__all__ = ["TRANSLATIONS"]