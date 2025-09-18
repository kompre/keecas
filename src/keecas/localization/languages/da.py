"""
Danish translations.

Contains Danish translations for all LaTeX/SymPy strings used in keecas.
"""

TRANSLATIONS = {
    # SymPy LaTeX words
    "for": "for",
    "otherwise": "ellers",

    # Boolean verification states
    "VERIFIED": "VERIFICERET",
    "NOT_VERIFIED": "IKKE VERIFICERET",

    # Backward compatibility (deprecated)
    "VERIFICATO": "VERIFICERET",
    "NON VERIFICATO": "IKKE VERIFICERET",

    # Common mathematical terms
    "True": "Sand",
    "False": "Falsk",

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