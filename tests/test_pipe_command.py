import pytest
from sympy import pi, sin, symbols
from sympy.parsing.sympy_parser import parse_expr as sympy_parse_expr
from sympy.physics.units import meter

from keecas.pipe_command import N, convert_to, doit, order_subs, parse_expr, quantity_simplify, subs


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
    symbols("x")
    expression = sin(pi / 2)
    result = expression | doit()
    assert result == 1


def test_parse_expr():
    expr_str = "x**2 + y"
    local_dict = {"x": 2, "y": 3}
    result = expr_str | parse_expr(local_dict=local_dict, evaluate=True)
    expected = sympy_parse_expr(expr_str, local_dict=local_dict)
    assert result == expected


def test_parse_expr_in_dict_comprehension():
    """Test parse_expr works in dict comprehensions (Python 3.13 regression).

    This test verifies that parse_expr can access both comprehension variables
    (k, v) and enclosing scope variables (u, symbols) when used in dict
    comprehensions. Python 3.13 introduced PEP 667 which isolates comprehension
    scope, requiring special handling.
    """
    from keecas.pint_sympy import unitregistry as u

    # Define symbols in function scope
    a, b, c = symbols("a b c")

    # Parameters dict with units
    _p = {
        a: 2 * u.kN,
        b: 3 * u.m,
        c: 5,
    }

    # Dict comprehension using parse_expr (should access both v and u)
    _v = {k: "v/u.kN" | parse_expr for k, v in _p.items()}

    # Verify all expressions parsed correctly
    assert len(_v) == 3
    # Check that u.kN was resolved (not treated as unknown symbol)
    for k, expr in _v.items():
        assert expr is not None
        # Expression should be v / kilonewton (where v is from _p)
        assert "kilonewton" in str(expr) or "kN" in str(expr)


def test_parse_expr_in_module_level_comprehension():
    """Test parse_expr in module-level dict comprehension (Python 3.13).

    Module-level comprehensions in Python 3.13 have isolated scope with no
    parent frame. This requires accessing f_globals instead of f_back.f_locals.
    This test simulates the exact regression case from issue #66.
    """
    import sys
    from io import StringIO
    from pathlib import Path

    # Create test script that mimics module-level usage
    test_script = """
from keecas import u, pc
from sympy import symbols

a, b, c = symbols('a b c')

_p = {
    a: 2*u.kN,
    b: 3*u.m,
    c: 5,
}

_v = {
    k: "v/u.kN" | pc.parse_expr for k,v in _p.items()
}

# Verify expressions parsed correctly
assert len(_v) == 3
for k, expr in _v.items():
    assert expr is not None
    assert "kilonewton" in str(expr) or "kN" in str(expr)

print("SUCCESS")
"""

    # Execute test script in subprocess
    import subprocess

    result = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        timeout=10,
    )

    # Check execution succeeded
    assert result.returncode == 0, f"Script failed:\n{result.stderr}"
    assert "SUCCESS" in result.stdout


def test_quantity_simplify():
    from sympy.physics.units import joule, meter, newton

    expr = 2 * joule + 3 * newton * meter
    result = expr | quantity_simplify()
    assert result == 5 * joule


if __name__ == "__main__":
    pytest.main()
