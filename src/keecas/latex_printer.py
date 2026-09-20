"""Custom LaTeX printer preserving expression structure and order as typed.

`display.py`/`formatters.py` render expressions parsed with
`evaluate=False` (see `pipe_command.parse_expr`) so the LaTeX output keeps
the symbol order the user typed. SymPy's stock `LatexPrinter` undermines
that goal in two independent ways, both worked around here:

1. Nested division gets flattened. When the denominator of a fraction is
   itself an unevaluated compound expression (e.g. the user wrote
   `a/(b/2)`), the printer's numerator/denominator conversion helper
   prints that sub-expression element-by-element instead of recursing
   through the normal `Mul` printing path, extracting the rational
   coefficient into a leading `\\frac{1}{2}` term:

       a/(b/2), evaluate=False -> \\frac{a}{\\frac{1}{2} b}   (SymPy default)
                                -> \\frac{a}{\\frac{b}{2}}     (here)

   `_print_Mul` intercepts only this one case (a `Mul` whose extracted
   denominator is itself compound, i.e. a `Mul` or `Pow`) and re-prints
   numerator/denominator through `self._print()` so nested fractions
   render as nested `\\frac{}{}` rather than being flattened.

2. Terms/factors get re-sorted. By default `LatexPrinter` prints a `Mul`
   or `Add` in a canonical order (`order=None` -> `as_ordered_factors()`/
   `as_ordered_terms()`) rather than the order the `Mul`/`Add` object's
   own `.args` are stored in - and `evaluate=False` parsing stores `.args`
   in the literal order the user typed (`parse_expr("q*l**2/8",
   evaluate=False).args == (q, l**2, 1/8)`), so the default canonical sort
   silently discards it:

       q*l**2/8, evaluate=False -> \\frac{l^{2} q}{8}   (SymPy default)
                                 -> \\frac{q l^{2}}{8}   (here)

   `_default_settings` overrides `order` to `"none"` so every `Mul`/`Add`
   is printed straight from its stored `.args`, matching what the user
   typed for `evaluate=False` trees. This is a global default for this
   printer, not a per-case check: an explicit `order=...` kwarg passed to
   `latex()` still overrides it, and fully-evaluated expressions are only
   affected when their own canonical `.args` order happens to differ from
   the "pretty" printing order SymPy would otherwise choose (e.g. summed
   polynomial terms may no longer print degree-descending).

3. `config.latex.default_mul_symbol` doesn't reach direct `format_value()`/
   `format_sympy()` calls. Previously the only thing that ever applied it
   was `sympy.init_printing(mul_symbol=..., order="none")`, called from
   `keecas/__init__.py`'s lazy `__getattr__` - but only when something
   accesses `keecas.sympy`/`keecas.latex`/etc. (e.g. via `from keecas
   import *`, since those names are in `__all__`). A narrower import like
   `from keecas import format_value, pc` never triggers it, so the
   configured symbol silently falls back to SymPy's own default depending
   on unrelated import choices elsewhere in the session. `show_eqn()`
   separately injects `mul_symbol` into its kwargs before calling
   `format_value()`, so it was never affected - but `format_value()`/
   `format_sympy()` called directly were.

   `latex()` below reads `config.latex.default_mul_symbol` itself (unless
   the caller already passed `mul_symbol` explicitly) so the setting
   applies unconditionally, the same way the `order` fix does, with no
   dependency on import order or on going through `show_eqn()`.
"""

from typing import Any

from sympy import Mul, S
from sympy.printing.latex import LatexPrinter
from sympy.simplify import fraction


class KeecasLatexPrinter(LatexPrinter):
    """LatexPrinter that preserves nested-division structure in unevaluated Mul trees."""

    _default_settings = {**LatexPrinter._default_settings, "order": "none"}

    def _print_Mul(self, expr):
        if isinstance(expr, Mul):
            numer, denom = fraction(expr, exact=True)
            if denom is not S.One and (denom.is_Mul or denom.is_Pow):
                return rf"\frac{{{self._print(numer)}}}{{{self._print(denom)}}}"
        return super()._print_Mul(expr)


def latex(expr, **settings: Any):
    """Convert `expr` to LaTeX using `KeecasLatexPrinter`.

    Drop-in replacement for `sympy.latex()` accepting the same settings
    (`mul_symbol`, `mode`, `fold_frac_powers`, etc.) - see that function's
    docstring for the full parameter reference.

    Unless the caller passes `mul_symbol` explicitly, it defaults to
    `config.latex.default_mul_symbol` (read fresh on every call, so runtime
    config changes take effect immediately).
    """
    if "mul_symbol" not in settings:
        from keecas.config.manager import get_config_manager

        settings = {**settings, "mul_symbol": get_config_manager().options.latex.default_mul_symbol}
    return KeecasLatexPrinter(settings).doprint(expr)
