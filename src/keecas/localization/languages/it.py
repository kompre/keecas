"""
Italian translations.

Contains Italian translations for all LaTeX/SymPy strings used in keecas.
"""

TRANSLATIONS = {
    # SymPy LaTeX words (currently hardcoded in display.py)
    "for": "per",
    "otherwise": "altrimenti",

    # Boolean verification states (currently hardcoded in verifica function)
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