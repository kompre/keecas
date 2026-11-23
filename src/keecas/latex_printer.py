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
            quantity = _split_quantity(expr)
            if quantity is not None:
                return self._print_quantity(*quantity)
            # An unevaluated Mul can carry an explicit 1 factor, e.g.
            # parse_expr("1/(a+b)", evaluate=False) == Mul(1, Pow(a+b, -1)),
            # which stock printing renders as "1 \frac{1}{a + b}". Drop it.
            rest = [arg for arg in expr.args if arg is not S.One]
            if 0 < len(rest) < len(expr.args):
                if len(rest) == 1:
                    return self._print(rest[0])
                expr = Mul(*rest, evaluate=False)
            numer, denom = fraction(expr, exact=True)
            if denom is not S.One and (denom.is_Mul or denom.is_Pow):
                return rf"\frac{{{self._print(numer)}}}{{{self._print(denom)}}}"
            if denom is S.One:
                if self._needs_explicit_dots(expr.args):
                    return self._join_factors(expr.args)
            elif isinstance(numer, Mul) and self._needs_explicit_dots(numer.args):
                return rf"\frac{{{self._print(numer)}}}{{{self._print(denom)}}}"
        return super()._print_Mul(expr)

    def _needs_explicit_dots(self, args) -> bool:
        """True if some pair of factors needs an explicit multiplication sign."""
        if len(args) < 2:
            return False
        return any(_is_quantity(arg) for arg in args) or any(
            self._print(arg)[:1].isdigit() for arg in args[1:]
        )

    def _join_factors(self, args) -> str:
        """Join factors, using \\cdot where juxtaposition could be misread.

        A \\cdot goes between two factors when
        - the next factor starts with a digit (`x \\cdot 2`, `q \\cdot 5\\,m`), or
        - the previous factor is a number with units and the next one is not
          parenthesised (`3\\,\\frac{kN}{m} \\cdot l`: `\\,l` could read as litres).

        Otherwise the configured `mul_symbol` is used, e.g. before
        `\\left(5\\,m\\right)^{2}`, where the parenthesis already separates.
        """
        sep = self._settings["mul_symbol_latex"]
        out, prev = "", None
        for i, arg in enumerate(args):
            tex = self._print(arg)
            if not _is_unit(arg) and self._needs_mul_brackets(
                arg, first=(i == 0), last=(i == len(args) - 1)
            ):
                tex = rf"\left({tex}\right)"
            if prev is not None:
                dot = tex[:1].isdigit() or (_is_quantity(prev) and not tex.startswith(r"\left("))
                out += r" \cdot " if dot else sep
            out += tex
            prev = arg
        return out

    def _print_quantity(self, coeff, units):
        """Print `number * units` with the magnitude outside the unit fraction.

        `2*kN/m**2` -> `2\\,\\frac{kN}{m^{2}}`, not `\\frac{2\\,kN}{m^{2}}`.
        """
        sign = ""
        if coeff.is_extended_negative:
            sign, coeff = "-", -coeff
        unit_part = units[0] if len(units) == 1 else Mul(*units, evaluate=False)
        sep = self._settings["mul_symbol_latex"]
        return f"{sign}{self._print(coeff)}{sep}{self._print(unit_part)}"


def _is_unit(arg) -> bool:
    from sympy.physics.units import Quantity

    # Unwrap nested powers: 1/m**2 under evaluate(False) is Pow(Pow(m, 2), -1)
    while arg.is_Pow:
        arg = arg.base
    return isinstance(arg, Quantity)


def _is_quantity(arg) -> bool:
    """A number times units (bare units do not count)."""
    return isinstance(arg, Mul) and _split_quantity(arg) is not None


def _flat_factors(expr):
    """Factors of a Mul, descending into nested (unevaluated) Muls."""
    for arg in expr.args:
        if isinstance(arg, Mul):
            yield from _flat_factors(arg)
        else:
            yield arg


def _split_quantity(expr):
    """Return `(coeff, units)` if `expr` is one number times units, else None.

    Nested Muls are flattened, so the unevaluated `Mul(Mul(27.06, kN), 1/m)`
    produced by substituting `27.06*kN/m` into an `evaluate=False` tree is
    recognised too. Products of several quantities (two numeric factors), or
    anything with symbols or a power of a quantity, are not.
    """
    from sympy.physics.units import Quantity

    coeffs, units = [], []
    for arg in _flat_factors(expr):
        if arg is S.One:  # e.g. Mul(1, 1/m) from 1/u.m under evaluate(False)
            continue
        if _is_unit(arg):
            units.append(arg)
        elif arg.is_number and not arg.has(Quantity):
            coeffs.append(arg)
        else:
            return None
    if len(coeffs) != 1 or not units or coeffs[0] is S.One:
        return None
    return coeffs[0], units


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
