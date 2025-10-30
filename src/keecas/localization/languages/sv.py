"""
Swedish translations.

Contains Swedish translations for all LaTeX/SymPy strings used in keecas.
"""

TRANSLATIONS = {
    # SymPy LaTeX words
    "for": "för",
    "otherwise": "annars",
    # Domain/Range labels from SymPy LaTeX output
    "Domain: ": "Definitionsmängd: ",
    "Domain on ": "Definitionsmängd på ",
    "Range": "Område",
    # Boolean verification states
    "VERIFIED": "VERIFIERAD",
    "NOT_VERIFIED": "INTE VERIFIERAD",
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
