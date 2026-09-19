"""Custom LaTeX printer preserving nested-division structure as typed.

`display.py`/`formatters.py` render expressions parsed with
`evaluate=False` (see `pipe_command.parse_expr`) so the LaTeX output keeps
the symbol order the user typed. SymPy's stock `LatexPrinter` handles this
well for most `evaluate=False` trees, but it has a known gap for nested
division: when the denominator of a fraction is itself an unevaluated
compound expression (e.g. the user wrote `a/(b/2)`), the printer's
numerator/denominator conversion helper flattens that sub-expression
instead of recursing through the normal `Mul` printing path, extracting
the rational coefficient into a leading `\\frac{1}{2}` term:

    a/(b/2), evaluate=False -> \\frac{a}{\\frac{1}{2} b}   (SymPy default)
                             -> \\frac{a}{\\frac{b}{2}}     (KeecasLatexPrinter)

`KeecasLatexPrinter` only intercepts this one case (a `Mul` whose
extracted denominator is itself compound, i.e. a `Mul` or `Pow`) and
re-prints numerator/denominator through `self._print()` so nested
fractions render as nested `\\frac{}{}` rather than being flattened. Every
other case (including all fully-evaluated expressions) falls through to
`super()._print_Mul()` unchanged - verified by comparing against stock
`sympy.latex()` output across representative evaluated expressions.
"""

from sympy import Mul, S
from sympy.printing.latex import LatexPrinter
from sympy.simplify import fraction


class KeecasLatexPrinter(LatexPrinter):
    """LatexPrinter that preserves nested-division structure in unevaluated Mul trees."""

    def _print_Mul(self, expr):
        if isinstance(expr, Mul):
            numer, denom = fraction(expr, exact=True)
            if denom is not S.One and (denom.is_Mul or denom.is_Pow):
                return rf"\frac{{{self._print(numer)}}}{{{self._print(denom)}}}"
        return super()._print_Mul(expr)


def latex(expr, **settings):
    """Convert `expr` to LaTeX using `KeecasLatexPrinter`.

    Drop-in replacement for `sympy.latex()` accepting the same settings
    (`mul_symbol`, `mode`, `fold_frac_powers`, etc.) - see that function's
    docstring for the full parameter reference.
    """
    return KeecasLatexPrinter(settings).doprint(expr)
