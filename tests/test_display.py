import pytest
from sympy import symbols, Eq, Le, StrictLessThan, GreaterThan, Basic
from IPython.display import Markdown
from keecas.display import (
    verifica,
    show_eqn,
    myprint_latex,
    wrap_floats,
    format_decimal_numbers,
    dict_to_eq,
    eq_to_dict,
    replace_all,
    latex_inline_dict,
)

# Test data
x, y = symbols("x y")


def test_verifica():
    # Test for Le (Less Than or Equal To)
    x = 1
    y = 2
    result = verifica(x, y, test=Le)
    assert isinstance(result, Markdown)
    assert r"\textcolor{green}" in result.data

    # Test for GreaterThan
    result = verifica(x, y, test=GreaterThan)
    assert isinstance(result, Markdown)
    assert r"\textcolor{red}" in result.data

    # Test for StrictLessThan
    result = verifica(x, y, test=StrictLessThan)
    assert isinstance(result, Markdown)
    assert r"\textcolor{green}" in result.data


def test_myprint_latex():
    expr = Eq(x, y)
    result = myprint_latex(expr)
    assert isinstance(result, str)
    assert r"x = y" in result


def test_wrap_floats():
    text = "The value is 3.14159 and -2.71828"
    result = wrap_floats(text, wrapper=("(", ")"))
    assert result == "The value is (3.14159) and (-2.71828)"


def test_format_decimal_numbers():
    text = "The values are 3.14159, -2.71828, and 0.57721."
    result = format_decimal_numbers(text, format_string="{:.2f}")
    assert result == "The values are 3.14, -2.72, and 0.58."


def test_dict_to_eq():
    input_dict = {x: 1, y: 2}
    result = dict_to_eq(input_dict)
    assert result == [Eq(x, 1), Eq(y, 2)]


def test_eq_to_dict():
    input_eqs = [Eq(x, 1), Eq(y, 2)]
    result = eq_to_dict(input_eqs)
    assert result == {x: 1, y: 2}


def test_replace_all():
    body = r"\frac{1}{2}"
    result = replace_all(body)
    assert result == r"\dfrac{1}{2}"


def test_latex_inline_dict():
    mapping = {x: 1, y: 2}
    result = latex_inline_dict(x, mapping)
    assert result == "x = 1"


def test_show_eqn():
    eqns = {x: 1, y: 2}
    result = show_eqn(eqns, debug=True)
    assert isinstance(result, Markdown)
    assert r"x & =1" in result.data
    assert r"y & =2" in result.data


if __name__ == "__main__":
    pytest.main()
