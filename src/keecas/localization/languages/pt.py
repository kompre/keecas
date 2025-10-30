"""
Portuguese translations.

Contains Portuguese translations for all LaTeX/SymPy strings used in keecas.
"""

TRANSLATIONS = {
    # SymPy LaTeX words
    "for": "para",
    "otherwise": "caso contrário",
    # Domain/Range labels from SymPy LaTeX output
    "Domain: ": "Domínio: ",
    "Domain on ": "Domínio em ",
    "Range": "Intervalo",
    # Boolean verification states
    "VERIFIED": "VERIFICADO",
    "NOT_VERIFIED": "NÃO VERIFICADO",
    # Common mathematical terms
    "True": "Verdadeiro",
    "False": "Falso",
    # Additional terms that might be useful
    "if": "se",
    "then": "então",
    "else": "caso contrário",
    "and": "e",
    "or": "ou",
    "not": "não",
}

# Export for easier access
__all__ = ["TRANSLATIONS"]
