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
    """Simple fully evaluated expressions render identically to sympy.latex().

    These particular expressions happen to already be in canonical order,
    so they're unaffected by the order='none' default (see
    test_unevaluated_argument_order_preserved for a case where it matters).
    """
    exprs = [
        parse_expr(s, evaluate=True)
        for s in ("a/(b/2)", "a/(b/c)", "a/b/c", "2*a/b", "(a+b)/(c)", "-a/b")
    ]
    for expr in exprs:
        assert keecas_latex(expr) == sympy_latex(expr)


def test_unevaluated_argument_order_preserved():
    """Mul/Add factors and terms render in the order the user typed them.

    Stock sympy.latex() re-sorts a Mul/Add into a canonical print order
    (order=None -> as_ordered_factors()/as_ordered_terms()) regardless of
    how the Mul/Add's own .args are stored, silently discarding the
    literal order evaluate=False parsing preserves.
    """
    expr = parse_expr("q*l**2/8", evaluate=False)
    assert keecas_latex(expr) == r"\frac{q l^{2}}{8}"

    expr2 = parse_expr("b*a", evaluate=False)
    assert keecas_latex(expr2) == r"b a"


def test_simple_unevaluated_division_unaffected():
    """Plain (non-nested) unevaluated fractions still render as before."""
    expr = parse_expr("a/b", evaluate=False)
    assert keecas_latex(expr) == sympy_latex(expr) == r"\frac{a}{b}"


def test_negative_nested_division_renders_as_nested_fraction():
    expr = parse_expr("a/(-(b/2))", evaluate=False)
    assert keecas_latex(expr) == r"\frac{a}{- \frac{b}{2}}"


def test_function_in_nested_division_renders_as_nested_fraction():
    expr = parse_expr("a/(sqrt(b)/2)", evaluate=False)
    assert keecas_latex(expr) == r"\frac{a}{\frac{\sqrt{b}}{2}}"


def test_format_value_integration_uses_keecas_latex():
    """format_value (the actual keecas rendering entrypoint) picks up the fix."""
    from keecas import pipe_command as pc
    from keecas.formatters import format_value

    expr = "a/(b/2)" | pc.parse_expr()
    assert format_value(expr) == r"\frac{a}{\frac{b}{2}}"

    expr2 = "q*l**2/8" | pc.parse_expr()
    assert format_value(expr2) == r"\frac{q l^{2}}{8}"
