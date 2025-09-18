"""
Swedish translations.

Contains Swedish translations for all LaTeX/SymPy strings used in keecas.
"""

TRANSLATIONS = {
    # SymPy LaTeX words
    "for": "för",
    "otherwise": "annars",

    # Boolean verification states
    "VERIFIED": "VERIFIERAD",
    "NOT_VERIFIED": "INTE VERIFIERAD",

    # Backward compatibility (deprecated)
    "VERIFICATO": "VERIFIERAD",
    "NON VERIFICATO": "INTE VERIFIERAD",

    # Common mathematical terms
    "True": "Sann",
    "False": "Falsk",

    # Additional terms that might be useful
    "if": "om",
    "then": "då",
    "else": "annars",
    "and": "och",
    "or": "eller",
    "not": "inte",
}

# Export for easier access
__all__ = ["TRANSLATIONS"]