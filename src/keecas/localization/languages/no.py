"""
Norwegian translations.

Contains Norwegian translations for all LaTeX/SymPy strings used in keecas.
"""

TRANSLATIONS = {
    # SymPy LaTeX words
    "for": "for",
    "otherwise": "ellers",

    # Boolean verification states
    "VERIFIED": "VERIFISERT",
    "NOT_VERIFIED": "IKKE VERIFISERT",

    # Backward compatibility (deprecated)
    "VERIFICATO": "VERIFISERT",
    "NON VERIFICATO": "IKKE VERIFISERT",

    # Common mathematical terms
    "True": "Sann",
    "False": "Usann",

    # Additional terms that might be useful
    "if": "hvis",
    "then": "så",
    "else": "ellers",
    "and": "og",
    "or": "eller",
    "not": "ikke",
}

# Export for easier access
__all__ = ["TRANSLATIONS"]