import pytest
from sympy import symbols, Basic, sin, cos, pi
from sympy.physics.units import meter, second
from sympy.parsing.sympy_parser import parse_expr as sympy_parse_expr
from keecas.pipe_command import order_subs, subs, N, convert_to, doit, parse_expr, quantity_simplify


def test_order_subs():
    x, y = symbols("x y")
    subs_dict = {x: 2, y: x + 1}
    ordered_subs = order_subs(subs_dict)
    assert ordered_subs == [(y, x + 1), (x, 2)]


def test_subs():
    x, y = symbols("x y")
    expression = x + y
    subs_dict = {x: 2, y: 3}
    result = expression | subs(subs_dict)
    assert result == 5

    expression = None
    result = expression | subs(subs_dict)
    assert result is None

    expression = x + y
    subs_dict = {x: None, y: 3}
    result = expression | subs(subs_dict)
    assert result == x + 3


def test_N():
    x = symbols("x")
    expression = sin(x)
    result = expression.evalf() | N(10)
    assert abs(result - sin(x).evalf(10)) < 1e-10


def test_convert_to():
    x = symbols("x")
    expression = x * meter
    result = expression | convert_to(meter)
    assert result == x * meter


def test_doit():
    x = symbols("x")
    expression = sin(pi/2)
    result = expression | doit()
    assert result == 1


def test_parse_expr():
    expr_str = "x**2 + y"
    local_dict = {'x': 2, 'y': 3}
    result = expr_str | parse_expr(local_dict=local_dict, evaluate=True)
    expected = sympy_parse_expr(expr_str, local_dict=local_dict)
    assert result == expected


def test_quantity_simplify():
    from sympy.physics.units import joule, newton, meter

    expr = 2 * joule + 3 * newton * meter
    result = expr | quantity_simplify()
    assert result == 5 * joule


if __name__ == "__main__":
    pytest.main()
