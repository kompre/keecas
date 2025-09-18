"""
Spanish translations.

Contains Spanish translations for all LaTeX/SymPy strings used in keecas.
"""

TRANSLATIONS = {
    # SymPy LaTeX words
    "for": "para",
    "otherwise": "de lo contrario",

    # Boolean verification states
    "VERIFIED": "VERIFICADO",
    "NOT_VERIFIED": "NO VERIFICADO",

    # Backward compatibility (deprecated)
    "VERIFICATO": "VERIFICADO",
    "NON VERIFICATO": "NO VERIFICADO",

    # Common mathematical terms
    "True": "Verdadero",
    "False": "Falso",

    # Additional terms that might be useful
    "if": "si",
    "then": "entonces",
    "else": "de lo contrario",
    "and": "y",
    "or": "o",
    "not": "no",
}

# Export for easier access
__all__ = ["TRANSLATIONS"]