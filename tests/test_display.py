import pytest
from sympy import symbols, Eq, Le, StrictLessThan, GreaterThan, Basic
from IPython.display import Markdown
from keecas.display import (
    check,
    show_eqn,
    myprint_latex,
    wrap_floats,
    format_decimal_numbers,
    dict_to_eq,
    eq_to_dict,
    replace_all,
    latex_inline_dict,
)
from keecas import pipe_command as pc

# Test data
x, y = symbols("x y")


def test_check():
    # Test for Le (Less Than or Equal To)
    x = 1
    y = 2
    result = check(x, y, test=Le)
    assert isinstance(result, Markdown)
    assert r"\textcolor{green}" in result.data

    # Test for GreaterThan
    result = check(x, y, test=GreaterThan)
    assert isinstance(result, Markdown)
    assert r"\textcolor{red}" in result.data

    # Test for StrictLessThan
    result = check(x, y, test=StrictLessThan)
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

def test_replace_all():
    from keecas.localization import set_language

    # Set language to Italian for this test
    set_language("it")

    expr = {x: "Piecewise((0, x < 0), (x, x >= 0))" | pc.parse_expr}
    result = show_eqn(expr)
    assert r"\text{for}" not in result.data
    assert r"\text{per}" in result.data
    assert r"\text{otherwise}" not in result.data
    assert r"\text{altrimenti}" in result.data

    # Reset to English
    set_language("en")
    
def test_label():
    expr = {
        x: 1,
        y: 2,
    }
    result = show_eqn(expr, environment='cases',  label="single_label", debug=True)
    assert r"single_label" in result.data


def test_check_template_default():
    """Test default template behavior."""
    result = check(0.5, 1.0, test=Le)
    assert isinstance(result, Markdown)
    assert r"\textcolor{green}" in result.data
    assert r"\left[" in result.data
    assert r"\le" in result.data


def test_check_template_boxed():
    """Test named template set (boxed)."""
    result = check(0.5, 1.0, test=Le, template="boxed")
    assert isinstance(result, Markdown)
    assert r"\colorbox{green}" in result.data
    assert r"\checkmark" in result.data


def test_check_template_minimal():
    """Test named template set (minimal)."""
    result = check(0.5, 1.0, test=Le, template="minimal")
    assert isinstance(result, Markdown)
    assert r"\checkmark" in result.data
    # Should not contain the full bracket structure
    assert r"\left[" not in result.data


def test_check_template_custom():
    """Test custom template override."""
    custom_success = r"✅ {symbol}{rhs} OK"
    custom_failure = r"❌ {symbol}{rhs} FAIL"

    # Test success case
    result = check(0.5, 1.0, test=Le,
                  success_template=custom_success,
                  failure_template=custom_failure)
    assert isinstance(result, Markdown)
    assert "✅" in result.data
    assert "OK" in result.data

    # Test failure case
    result = check(1.5, 1.0, test=Le,
                  success_template=custom_success,
                  failure_template=custom_failure)
    assert isinstance(result, Markdown)
    assert "❌" in result.data
    assert "FAIL" in result.data


def test_check_template_variables():
    """Test that all template variables are available."""
    template = r"{symbol}|{rhs}|{verified_text}|{not_verified_text}|{color}|{test_result}|{result_text}"

    result = check(0.5, 1.0, test=Le,
                  success_template=template,
                  failure_template=template)

    # Check that variables are substituted
    assert r"\le" in result.data  # symbol
    assert "1.0" in result.data   # rhs
    # Check for localized text (might be VERIFIED or VERIFICATO depending on current language)
    assert ("VERIFIED" in result.data or "VERIFICATO" in result.data)  # verified_text
    assert "green" in result.data # color
    assert "True" in result.data  # test_result


def test_check_template_invalid():
    """Test handling of invalid template names."""
    # Invalid template name should fall back to default
    result = check(0.5, 1.0, test=Le, template="nonexistent")
    assert isinstance(result, Markdown)
    # Should use default template
    assert r"\textcolor{green}" in result.data
    assert r"\left[" in result.data


def test_check_different_test_types_with_templates():
    """Test that templates work with different comparison types."""
    template_success = r"{symbol}{rhs} PASS"
    template_failure = r"{symbol}{rhs} FAIL"

    # Test with GreaterThan
    result = check(2.0, 1.0, test=GreaterThan,
                  success_template=template_success,
                  failure_template=template_failure)
    assert r"\ge" in result.data
    assert "PASS" in result.data

    # Test with StrictLessThan
    result = check(0.5, 1.0, test=StrictLessThan,
                  success_template=template_success,
                  failure_template=template_failure)
    assert r"<" in result.data
    assert "PASS" in result.data


def test_check_explicit_parameters():
    """Test new explicit parameters work correctly."""
    # Test explicit template parameter
    result = check(0.5, 1.0, template="minimal")
    assert isinstance(result, Markdown)
    assert r"\textcolor{green}{\checkmark}" in result.data

    # Test explicit success/failure template parameters
    result = check(0.5, 1.0,
                  success_template="GOOD: {symbol}{rhs}",
                  failure_template="BAD: {symbol}{rhs}")
    assert "GOOD:" in result.data
    assert r"\le" in result.data

    # Test failure case with explicit templates
    result = check(1.5, 1.0,
                  success_template="GOOD: {symbol}{rhs}",
                  failure_template="BAD: {symbol}{rhs}")
    assert "BAD:" in result.data
    assert r">" in result.data


def test_check_backward_compatibility_kwargs():
    """Test that kwargs still work for backward compatibility."""
    # Old style with kwargs should still work
    result = check(0.5, 1.0, template="boxed")
    result_kwargs = check(0.5, 1.0, **{"template": "boxed"})

    # Should produce same result
    assert result.data == result_kwargs.data
    assert r"\colorbox{green}" in result.data

    # Test custom templates via kwargs
    result_kwargs = check(0.5, 1.0, **{
        "success_template": "OK: {symbol}{rhs}",
        "failure_template": "FAIL: {symbol}{rhs}"
    })
    assert "OK:" in result_kwargs.data


def test_check_explicit_parameter_precedence():
    """Test that explicit parameters work as intended."""
    # Test that explicit parameters work correctly
    result_minimal = check(0.5, 1.0, template="minimal")
    assert r"\textcolor{green}{\checkmark}" in result_minimal.data
    assert r"\colorbox{green}" not in result_minimal.data

    # Test different template styles
    result_boxed = check(0.5, 1.0, template="boxed")
    assert r"\colorbox{green}" in result_boxed.data
    assert r"\checkmark" in result_boxed.data  # boxed style has different checkmark format

    result_default = check(0.5, 1.0, template="default")
    assert r"\left[" in result_default.data
    assert r"\textcolor{green}" in result_default.data


if __name__ == "__main__":
    pytest.main()
