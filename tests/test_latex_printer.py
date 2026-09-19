from sympy import latex as sympy_latex
from sympy import symbols
from sympy.parsing.sympy_parser import parse_expr

from keecas.latex_printer import latex as keecas_latex

a, b, c = symbols("a b c")


def test_nested_unevaluated_division_renders_as_nested_fraction():
    """a/(b/2) parsed with evaluate=False should keep b/2 as its own fraction.

    Stock sympy.latex() flattens the denominator's rational coefficient into
    a leading \\frac{1}{2} (e.g. \\frac{a}{\\frac{1}{2} b}), losing the
    nested-division structure the user typed.
    """
    expr = parse_expr("a/(b/2)", evaluate=False)
    assert keecas_latex(expr) == r"\frac{a}{\frac{b}{2}}"
    assert keecas_latex(expr) != sympy_latex(expr)


def test_nested_symbolic_division_renders_as_nested_fraction():
    expr = parse_expr("a/(b/c)", evaluate=False)
    assert keecas_latex(expr) == r"\frac{a}{\frac{b}{c}}"


def test_evaluated_expressions_match_stock_sympy_latex():
    """Fully evaluated expressions must render identically to sympy.latex()."""
    exprs = [
        parse_expr(s, evaluate=True)
        for s in ("a/(b/2)", "a/(b/c)", "a/b/c", "2*a/b", "(a+b)/(c)", "-a/b")
    ]
    for expr in exprs:
        assert keecas_latex(expr) == sympy_latex(expr)


def test_simple_unevaluated_division_unaffected():
    """Plain (non-nested) unevaluated fractions still render as before."""
    expr = parse_expr("a/b", evaluate=False)
    assert keecas_latex(expr) == sympy_latex(expr) == r"\frac{a}{b}"
