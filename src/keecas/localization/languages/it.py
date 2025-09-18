"""
Italian translations.

Contains Italian translations for all LaTeX/SymPy strings used in keecas.
"""

TRANSLATIONS = {
    # SymPy LaTeX words
    "for": "per",
    "otherwise": "altrimenti",

    # Boolean verification states (proper English keys)
    "VERIFIED": "VERIFICATO",
    "NOT_VERIFIED": "NON VERIFICATO",

    # Backward compatibility (deprecated)
    "VERIFICATO": "VERIFICATO",
    "NON VERIFICATO": "NON VERIFICATO",

    # Common mathematical terms
    "True": "Vero",
    "False": "Falso",

    # Additional terms that might be useful
    "if": "se",
    "then": "allora",
    "else": "altrimenti",
    "and": "e",
    "or": "o",
    "not": "non",
}

# Export for easier access
__all__ = ["TRANSLATIONS"]