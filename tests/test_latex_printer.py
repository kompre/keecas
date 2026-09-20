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

    mul_symbol=None pins both sides to sympy's own default separator, so
    this isolates the order/fraction-structure behavior from the
    config-driven mul_symbol default (see test_mul_symbol_config_default).
    These particular expressions also happen to already be in canonical
    order, so they're unaffected by the order='none' default (see
    test_unevaluated_argument_order_preserved for a case where it matters).
    """
    exprs = [
        parse_expr(s, evaluate=True)
        for s in ("a/(b/2)", "a/(b/c)", "a/b/c", "2*a/b", "(a+b)/(c)", "-a/b")
    ]
    for expr in exprs:
        assert keecas_latex(expr, mul_symbol=None) == sympy_latex(expr)


def test_unevaluated_argument_order_preserved():
    """Mul/Add factors and terms render in the order the user typed them.

    Stock sympy.latex() re-sorts a Mul/Add into a canonical print order
    (order=None -> as_ordered_factors()/as_ordered_terms()) regardless of
    how the Mul/Add's own .args are stored, silently discarding the
    literal order evaluate=False parsing preserves. mul_symbol=None isolates
    this from the config-driven mul_symbol default tested separately.
    """
    expr = parse_expr("q*l**2/8", evaluate=False)
    assert keecas_latex(expr, mul_symbol=None) == r"\frac{q l^{2}}{8}"

    expr2 = parse_expr("b*a", evaluate=False)
    assert keecas_latex(expr2, mul_symbol=None) == r"b a"


def test_mul_symbol_config_default_applied_without_show_eqn():
    """config.latex.default_mul_symbol applies even to a bare keecas_latex()/
    format_value() call, not just when going through show_eqn().

    Previously the only thing that ever applied it was
    sympy.init_printing(mul_symbol=...), triggered from keecas/__init__.py's
    lazy __getattr__ only when something accessed keecas.sympy/keecas.latex
    (e.g. via `from keecas import *`) - a narrower import never triggered it.
    latex() now reads the config directly, unconditionally.
    """
    from keecas.config.manager import get_config_manager

    cfg = get_config_manager().options
    original = cfg.latex.default_mul_symbol
    try:
        cfg.latex.default_mul_symbol = "dot"
        expr = parse_expr("a*b", evaluate=False)
        assert keecas_latex(expr) == sympy_latex(expr, mul_symbol="dot") == r"a \cdot b"
        # explicit kwarg still overrides the config default
        assert keecas_latex(expr, mul_symbol=None) == sympy_latex(expr)
    finally:
        cfg.latex.default_mul_symbol = original


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


def test_no_reliance_on_init_printing_side_effect(monkeypatch):
    """Regression test for the actual failure mode: both fixes above used to
    only work because sympy.init_printing(order="none", mul_symbol=...) got
    triggered somewhere - from keecas/__init__.py's lazy __getattr__, only
    when something accessed keecas.sympy/keecas.latex/keecas.Eq/etc. (e.g.
    via `from keecas import *`, since those names are in __all__). A
    narrower import, like `from keecas import format_value, pc` (used here
    and in test_format_value_integration_uses_keecas_latex below), never
    triggered it, so order preservation and the mul_symbol config default
    silently depended on unrelated code elsewhere in the session having
    already called init_printing first.

    This monkeypatches sympy.init_printing to fail loudly if called, then
    exercises the exact narrow-import path to prove neither fix depends on
    it anymore.
    """
    import sympy

    def _fail_if_called(*args, **kwargs):
        raise AssertionError(
            "keecas must not rely on sympy.init_printing() for order/mul_symbol defaults"
        )

    monkeypatch.setattr(sympy, "init_printing", _fail_if_called)

    from keecas.config.manager import get_config_manager
    from keecas.formatters import format_value
    from keecas.pipe_command import parse_expr as pc_parse_expr

    cfg = get_config_manager().options
    original = cfg.latex.default_mul_symbol
    try:
        cfg.latex.default_mul_symbol = "dot"
        expr = "q*l**2/8" | pc_parse_expr()
        # order preserved (q before l**2) AND config mul_symbol applied ("dot" -> \cdot),
        # with no call to init_printing anywhere in the path.
        assert format_value(expr) == r"\frac{q \cdot l^{2}}{8}"
    finally:
        cfg.latex.default_mul_symbol = original


def test_format_value_integration_uses_keecas_latex():
    """format_value (the actual keecas rendering entrypoint) picks up the fix."""
    from keecas import pipe_command as pc
    from keecas.formatters import format_value

    expr = "a/(b/2)" | pc.parse_expr()
    assert format_value(expr) == r"\frac{a}{\frac{b}{2}}"

    expr2 = "q*l**2/8" | pc.parse_expr()
    assert format_value(expr2, mul_symbol=None) == r"\frac{q l^{2}}{8}"
