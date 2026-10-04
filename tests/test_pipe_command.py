import pytest
from sympy import pi, sin, sqrt, symbols, sympify
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


def test_order_subs_key_before_keys_it_contains():
    """A key is replaced before the other keys it contains (keecas#124)."""
    from sympy import Function, ImmutableMatrix, IndexedBase, MatrixSymbol

    m, n, x = symbols("m n x")
    A = MatrixSymbol("A", n, m)
    f = Function("f")
    b = IndexedBase("b")

    keys = [k for k, _ in order_subs({m: 3, n: 2, A: ImmutableMatrix([[1, 2, 3], [4, 5, 6]])})]
    assert keys.index(A) < keys.index(n)
    assert keys.index(A) < keys.index(m)

    assert [k for k, _ in order_subs({x: 2, f(x): 5})] == [f(x), x]
    assert (f(x) + x) | subs({x: 2, f(x): 5}) == 7

    keys = [k for k, _ in order_subs({b: ImmutableMatrix([1, 2]), x: 1, b[x]: 7})]
    assert keys.index(b[x]) < keys.index(x)
    assert keys.index(b[x]) < keys.index(b)


def test_order_subs_non_expression_keys_and_values():
    """String keys and function classes, as keys or values, contain nothing.

    Display dicts use `""` keys, which do not sympify, and `.has` on a function
    class runs the unbound method on the other key.
    """
    from sympy import Function

    x, y = symbols("x y")
    f = Function("f")

    ordered = order_subs({f: 1, "": 2, x: f, y: x + 1})
    assert [k for k, _ in ordered].index(y) < [k for k, _ in ordered].index(x)
    assert (y + 1) | subs({f: 1, "": 2, x: 3, y: x + 1}) == 5


def test_subs_matrix_symbol_with_symbolic_shape():
    """A MatrixSymbol is substituted when its shape symbols are in the same dict (keecas#124)."""
    from sympy import ImmutableMatrix, MatrixSymbol

    m, n, y = symbols("m n y")
    A = MatrixSymbol("A", n, m)
    M = ImmutableMatrix([[1, 2, 3], [4, 5, 6]])

    eqn = {y: "2*A" | parse_expr(local_dict={"A": A})}
    params = {A: M, n: 2, m: 3}

    result = y | subs(eqn | params)
    assert not result.atoms(MatrixSymbol)
    assert result.doit() == 2 * M


def test_subs_matrix_expression_chain_with_symbolic_shape():
    """Matrix symbols defined through eqn, with their shape in params, are substituted."""
    from sympy import ImmutableMatrix, MatrixSymbol, hadamard_product

    n_file, n_pan, k, A_pan, F_w = symbols("n_file n_pan k A_pan F_w")
    c_p = MatrixSymbol("c_p", n_file, n_pan)
    gamma_N = MatrixSymbol("gamma_N", n_file, n_pan)
    C = ImmutableMatrix([[1, 2], [3, 4]])

    local_dict = {"c_p": c_p, "gamma_N": gamma_N, "hp": hadamard_product, "A_pan": A_pan, "k": k}
    eqn = {
        F_w: "hp(gamma_N, c_p)*A_pan" | parse_expr(local_dict=local_dict),
        gamma_N: "k*c_p" | parse_expr(local_dict=local_dict),
    }
    params = {c_p: C, k: 2, A_pan: 3, n_file: 2, n_pan: 2}

    result = F_w | subs(eqn | params)
    assert not result.atoms(MatrixSymbol)
    assert result.doit() == 6 * C.multiply_elementwise(C)


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


@pytest.fixture
def section_params():
    """Rectangular section with an area formula holding a sum factor (keecas#118)."""
    from keecas.pint_sympy import unitregistry as u

    a, b, A, gamma = symbols("a b A gamma")
    params = {a: 100 * u.mm, b: 50 * u.mm, gamma: 78.5 * u.kN / u.m**3}
    return u, (a, b, A, gamma), params


@pytest.mark.parametrize(
    "formula",
    [
        "a*b - (4 - pi)*b**2/10",  # irrational constant in the sum factor
        "a*b - (4 - 3)*b**2/10",  # unevaluated numeric sum from parse_expr
    ],
)
def test_convert_to_sum_factor_in_product(section_params, formula):
    """A sum that stays a factor of a product gets the right unit (keecas#118)."""
    u, (a, b, A, gamma), params = section_params
    expr = (A * gamma) | subs({A: formula | parse_expr(local_dict={"a": a, "b": b})} | params)
    target = [sympify(u.kN), sympify(u.m)]

    result = expr | convert_to(target) | N
    reference = expr | N | convert_to(target) | N  # evaluating first avoids the bug

    magnitude, unit = result.as_coeff_Mul()
    assert unit == sympify(u.kN / u.m)
    assert magnitude == pytest.approx(float(reference.as_coeff_Mul()[0]))


def test_convert_to_keeps_pi_symbolic(section_params):
    """Converting before pc.N keeps exact constants such as pi."""
    u, (a, b, A, gamma), params = section_params
    area = "a*b - (4 - pi)*b**2/10" | parse_expr(local_dict={"a": a, "b": b}) | subs(params)

    result = area | convert_to([u.mm])

    assert result == (4000 + 250 * pi) * sympify(u.mm) ** 2


def test_convert_to_sum_in_denominator():
    """A sum with units in a denominator, e.g. an inertia with a `(4 - pi)` term, converts correctly."""
    from keecas.pint_sympy import unitregistry as u

    q, L, E, I_y, b, h, r, delta = symbols("q L E I_y b h r delta")
    params = {
        q: 12 * u.kN / u.m,
        L: 6 * u.m,
        E: 210 * u.GPa,
        b: 100 * u.mm,
        h: 200 * u.mm,
        r: 10 * u.mm,
    }
    local_dict = {"q": q, "L": L, "E": E, "I_y": I_y, "b": b, "h": h, "r": r}
    eqn = {
        I_y: "b*h**3/12 - (4 - pi)*r**4/16" | parse_expr(local_dict=local_dict),
        delta: "5*q*L**4/(384*E*I_y)" | parse_expr(local_dict=local_dict),
    }
    expr = delta | subs(eqn | params)

    result = expr | convert_to([u.mm])
    reference = expr | N | convert_to([u.mm]) | N

    assert result.has(pi)
    magnitude, unit = (result | N).as_coeff_Mul()
    assert unit == sympify(u.mm)
    assert magnitude == pytest.approx(float(reference.as_coeff_Mul()[0]))


def test_convert_to_mixed_dimension_sum_term_by_term():
    """A sum whose terms have different dimensions is converted term by term, as in sympy."""
    from sympy.physics.units import millimeter

    x = symbols("x")
    result = (x + 5 * millimeter) | convert_to(meter)
    assert result == x + meter / 200


@pytest.mark.parametrize(
    "expression, target",
    [
        ("850*u.kN / (120*u.cm**2)", "[u.MPa]"),
        ("5000*u.N", "u.kN"),
        ("2*u.kgf", "[u.N]"),
        ("12*u.kN/u.m * (6*u.m)**2 / 8", "[u.kN, u.m]"),
        ("sqrt(3*u.kN*u.m)", "[u.kN, u.m]"),
        ("30*u.deg", "[1]"),
    ],
)
def test_convert_to_matches_sympy_without_sums(expression, target):
    """Without sums carrying units, the result is identical to sympy's convert_to."""
    from sympy.physics.units.util import convert_to as sympy_convert_to

    from keecas.pint_sympy import unitregistry as u

    namespace = {"u": u, "sqrt": sqrt}
    expr = sympify(eval(expression, namespace))
    target_units = eval(target, namespace)

    assert (expr | convert_to(target_units)) == sympy_convert_to(expr, target_units)


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
