import pytest
from IPython.display import Latex
from sympy import Eq, GreaterThan, Le, StrictLessThan, symbols

from keecas import pipe_command as pc
from keecas.display import (
    _replace_all,
    check,
    format_decimal_numbers,
    latex_inline_dict,
    show_eqn,
)
from keecas.formatters import validate_latex_kwargs
from keecas.utils import dict_to_eq, eq_to_dict

# Test data
x, y = symbols("x y")


def test_import_star():
    """Test that 'from keecas import *' works without AttributeError."""
    # This test ensures __all__ is properly updated with main exports

    # Create a fresh namespace
    namespace = {}

    # Execute import *
    exec("from keecas import *", namespace)

    # Verify main singledispatch export is available
    assert "format_value" in namespace

    # Individual formatter functions are not exported (use format_value singledispatch)
    assert "format_mul" not in namespace
    assert "format_sympy" not in namespace
    assert "format_int" not in namespace
    assert "format_float" not in namespace
    assert "format_str" not in namespace

    # Verify old chain-based exports are NOT present
    assert "EarlyExit" not in namespace
    assert "FormatterChain" not in namespace
    assert "default_formatter_chain" not in namespace
    assert "default_cell_formatter_registry" not in namespace
    assert "cell_formatter" not in namespace
    assert "default_cell_formatter" not in namespace

    # Verify format_value is actually usable
    format_value = namespace["format_value"]

    # Test basic functionality - formatters now do pure conversion (no decoration)
    result = format_value(42, col_index=0)
    assert result == "42"

    result = format_value(42, col_index=1)
    assert result == "42"  # No "= " prefix (handled by wrap_column now)

    # Verify wrap_column is available
    assert "wrap_column" in namespace
    wrap_column = namespace["wrap_column"]

    # Test wrap_column functionality
    prefix, suffix = wrap_column(42, col_index=0)
    assert prefix == "" and suffix == ""

    prefix, suffix = wrap_column(42, col_index=1)
    assert prefix == "= " and suffix == ""


def test_check():
    # Test for Le (Less Than or Equal To)
    x = 1
    y = 2
    result = check(x, y, test=Le)
    assert isinstance(result, Latex)
    assert r"\textcolor{green}" in result.data

    # Test for GreaterThan
    result = check(x, y, test=GreaterThan)
    assert isinstance(result, Latex)
    assert r"\textcolor{red}" in result.data

    # Test for StrictLessThan
    result = check(x, y, test=StrictLessThan)
    assert isinstance(result, Latex)
    assert r"\textcolor{green}" in result.data


def test_default_cell_formatter():
    """Test format_value function with singledispatch."""
    from keecas import format_value

    expr = Eq(x, y)
    # Test column 0 (LHS)
    result_col0 = format_value(expr, 0)
    assert isinstance(result_col0, str)
    assert r"x = y" in result_col0

    # Test column 1 (RHS)
    result_col1 = format_value(expr, 1)
    assert isinstance(result_col1, str)
    assert "=" in result_col1  # Should have = prefix

    # Test with kwargs (mul_symbol)
    expr_mul = x * y
    result_default = format_value(expr_mul, 0)
    result_dot = format_value(expr_mul, 0, mul_symbol="dot")
    assert result_default != result_dot  # Should be different with different mul_symbol


def test_validate_latex_kwargs():
    """Test validate_latex_kwargs function."""
    # Valid kwargs
    valid_kwargs = {"mul_symbol": "dot", "mode": "inline"}
    result = validate_latex_kwargs(valid_kwargs)
    assert result == valid_kwargs

    # Invalid kwargs should raise ValueError
    invalid_kwargs = {"invalid_param": "value", "mul_symbol": "dot"}
    with pytest.raises(ValueError, match="Invalid latex\\(\\) parameters"):
        validate_latex_kwargs(invalid_kwargs)


def test_formatter_custom_registration():
    """Test that custom formatters can be registered with singledispatch."""
    from keecas import format_value

    # Define a custom type
    class LargeInt:
        def __init__(self, value):
            self.value = value

    # Register a custom formatter for LargeInt
    @format_value.register(LargeInt)
    def format_large_int(value, col_index=0, **kwargs):
        # Custom formatting for LargeInt type
        return f"LARGE: {value.value}" if col_index == 0 else f"= LARGE: {value.value}"

    # Test with value > 100 - should use our formatter
    result_large = show_eqn({x: LargeInt(150)})
    assert "LARGE: 150" in result_large.data

    # Test with regular int - should use built-in int formatter
    result_small = show_eqn({y: 50})
    assert "LARGE" not in result_small.data
    assert "50" in result_small.data  # Uses default int formatter


def test_formatter_empty_string():
    """Test that formatters can explicitly return empty string."""
    from keecas import format_value

    # Define custom type
    class EmptyType:
        pass

    # Register formatter that explicitly returns empty string
    @format_value.register(EmptyType)
    def format_empty(value, col_index=0, **kwargs):
        return ""  # Explicit empty string

    result = show_eqn({x: EmptyType()})

    # Should have empty content between separator and line end
    assert "& " in result.data or "& \\" in result.data
    # Should NOT have "None"
    assert "None" not in result.data


def test_formatter_pint_transformation():
    """Test Pint → SymPy transformation with format_pint."""
    from keecas import format_value, u

    # Test with Pint quantity - should be transformed to SymPy and formatted
    # format_pint converts Quantity → SymPy, then calls format_sympy
    result = show_eqn({x: 5 * u.meter})

    # Should have the value
    assert "5" in result.data
    # Should have meter units (abbreviated as 'm' or full 'meter')
    assert "\\text{m}" in result.data or "meter" in result.data or "mathrm" in result.data

    # Test direct formatting of Pint quantity
    result_direct = format_value(5 * u.meter, col_index=0)
    assert isinstance(result_direct, str)
    assert "5" in result_direct


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
    result = _replace_all(body)
    assert result == r"\dfrac{1}{2}"


def test_latex_inline_dict():
    mapping = {x: 1, y: 2}
    result = latex_inline_dict(x, mapping)
    assert result == "x = 1"


def test_show_eqn():
    eqns = {x: 1, y: 2}
    result = show_eqn(eqns, debug=True)
    assert isinstance(result, Latex)
    # New formatter adds "= " prefix for RHS values
    assert r"x & == 1" in result.data or r"x & = 1" in result.data
    assert r"y & == 2" in result.data or r"y & = 2" in result.data


def test_replace_all_with_localization():
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
    result = show_eqn(expr, environment="cases", label="single_label", debug=True)
    assert r"single_label" in result.data


def test_check_template_default():
    """Test default template behavior."""
    result = check(0.5, 1.0, test=Le)
    assert isinstance(result, Latex)
    assert r"\textcolor{green}" in result.data
    assert r"\left[" in result.data
    assert r"\le" in result.data


def test_check_template_boxed():
    """Test named template set (boxed)."""
    result = check(0.5, 1.0, test=Le, template="boxed")
    assert isinstance(result, Latex)
    assert r"\colorbox{green}" in result.data
    assert r"\checkmark" in result.data


def test_check_template_minimal():
    """Test named template set (minimal)."""
    result = check(0.5, 1.0, test=Le, template="minimal")
    assert isinstance(result, Latex)
    assert r"\checkmark" in result.data
    # Should not contain the full bracket structure
    assert r"\left[" not in result.data


def test_check_template_custom():
    """Test custom template override."""
    custom_success = r"✅ {symbol}{rhs} OK"
    custom_failure = r"❌ {symbol}{rhs} FAIL"

    # Test success case
    result = check(
        0.5,
        1.0,
        test=Le,
        success_template=custom_success,
        failure_template=custom_failure,
    )
    assert isinstance(result, Latex)
    assert "✅" in result.data
    assert "OK" in result.data

    # Test failure case
    result = check(
        1.5,
        1.0,
        test=Le,
        success_template=custom_success,
        failure_template=custom_failure,
    )
    assert isinstance(result, Latex)
    assert "❌" in result.data
    assert "FAIL" in result.data


def test_check_template_variables():
    """Test that all template variables are available."""
    template = (
        r"{symbol}|{rhs}|{verified_text}|{not_verified_text}|{color}|{test_result}|{result_text}"
    )

    result = check(0.5, 1.0, test=Le, success_template=template, failure_template=template)

    # Check that variables are substituted
    assert r"\le" in result.data  # symbol
    assert "1.0" in result.data  # rhs
    # Check for localized text (might be VERIFIED or VERIFICATO depending on current language)
    assert "VERIFIED" in result.data or "VERIFICATO" in result.data  # verified_text
    assert "green" in result.data  # color
    assert "True" in result.data  # test_result


def test_check_template_invalid():
    """Test handling of invalid template names."""
    # Invalid template name should fall back to default
    result = check(0.5, 1.0, test=Le, template="nonexistent")
    assert isinstance(result, Latex)
    # Should use default template
    assert r"\textcolor{green}" in result.data
    assert r"\left[" in result.data


def test_check_different_test_types_with_templates():
    """Test that templates work with different comparison types."""
    template_success = r"{symbol}{rhs} PASS"
    template_failure = r"{symbol}{rhs} FAIL"

    # Test with GreaterThan
    result = check(
        2.0,
        1.0,
        test=GreaterThan,
        success_template=template_success,
        failure_template=template_failure,
    )
    assert r"\ge" in result.data
    assert "PASS" in result.data

    # Test with StrictLessThan
    result = check(
        0.5,
        1.0,
        test=StrictLessThan,
        success_template=template_success,
        failure_template=template_failure,
    )
    assert r"<" in result.data
    assert "PASS" in result.data


def test_check_explicit_parameters():
    """Test new explicit parameters work correctly."""
    # Test explicit template parameter
    result = check(0.5, 1.0, template="minimal")
    assert isinstance(result, Latex)
    assert r"\textcolor{green}{\checkmark}" in result.data

    # Test explicit success/failure template parameters
    result = check(
        0.5,
        1.0,
        success_template="GOOD: {symbol}{rhs}",
        failure_template="BAD: {symbol}{rhs}",
    )
    assert "GOOD:" in result.data
    assert r"\le" in result.data

    # Test failure case with explicit templates
    result = check(
        1.5,
        1.0,
        success_template="GOOD: {symbol}{rhs}",
        failure_template="BAD: {symbol}{rhs}",
    )
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
    result_kwargs = check(
        0.5,
        1.0,
        **{
            "success_template": "OK: {symbol}{rhs}",
            "failure_template": "FAIL: {symbol}{rhs}",
        },
    )
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


def test_environment_align():
    """Test standard align environment."""
    eqns = {x: 1, y: 2}
    result = show_eqn(eqns, environment="align", debug=True)
    assert isinstance(result, Latex)
    assert r"\begin{align}" in result.data
    assert r"\end{align}" in result.data
    assert "&" in result.data  # separator
    assert r"\\" in result.data  # line separator


def test_environment_align_starred():
    """Test starred align* environment."""
    eqns = {x: 1, y: 2}
    result = show_eqn(eqns, environment="align*", debug=True)
    assert isinstance(result, Latex)
    assert r"\begin{align*}" in result.data
    assert r"\end{align*}" in result.data


def test_environment_equation():
    """Test equation environment (no separator, single label)."""
    eqns = {x: 1}
    result = show_eqn(eqns, environment="equation", debug=True)
    assert isinstance(result, Latex)
    assert r"\begin{equation}" in result.data
    assert r"\end{equation}" in result.data
    assert "&" not in result.data  # no separator
    assert r"\\" not in result.data  # no line separator for single equation


def test_environment_gather():
    """Test gather environment (no separator, multiple labels)."""
    eqns = {x: 1, y: 2}
    result = show_eqn(eqns, environment="gather", debug=True)
    assert isinstance(result, Latex)
    assert r"\begin{gather}" in result.data
    assert r"\end{gather}" in result.data
    assert "&" not in result.data  # no separator


def test_environment_cases():
    """Test nested cases environment."""
    eqns = {x: 1, y: 2}
    result = show_eqn(eqns, environment="cases", label="test-label", debug=True)
    assert isinstance(result, Latex)
    assert r"\begin{align}" in result.data
    assert r"\end{align}" in result.data
    assert r"\begin{aligned}" in result.data
    assert r"\end{aligned}" in result.data
    assert r"\left\{" in result.data
    assert r"\right." in result.data


def test_environment_cases_starred():
    """Test nested cases* environment (starred outer)."""
    eqns = {x: 1, y: 2}
    result = show_eqn(eqns, environment="cases*", debug=True)
    assert isinstance(result, Latex)
    assert r"\begin{align*}" in result.data
    assert r"\end{align*}" in result.data
    assert r"\begin{aligned}" in result.data
    assert r"\left\{" in result.data


def test_environment_split():
    """Test nested split environment."""
    eqns = {x: 1, y: 2}
    result = show_eqn(eqns, environment="split", label="test-label", debug=True)
    assert isinstance(result, Latex)
    assert r"\begin{align}" in result.data
    assert r"\begin{aligned}" in result.data


def test_environment_unknown_fallback():
    """Test unknown environment falls back to align."""
    import warnings

    eqns = {x: 1, y: 2}

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = show_eqn(eqns, environment="nonexistent", debug=True)

        # Check warning was issued
        assert len(w) == 1
        assert "Unknown environment" in str(w[0].message)

        # Should fall back to align
        assert r"\begin{align}" in result.data


def test_environment_config_separator():
    """Test environment configuration controls separator."""
    from keecas.config import get_config_manager

    get_config_manager()

    # Test that align uses & separator from config
    eqns = {x: 1, y: 2}
    result = show_eqn(eqns, environment="align")
    assert "&" in result.data

    # Test that equation uses empty separator from config
    result = show_eqn(eqns, environment="equation")
    assert "&" not in result.data


def test_environment_custom_from_config():
    """Test custom environment definition from config."""
    from keecas.config import get_config_manager

    config_manager = get_config_manager()

    # Add custom environment
    config_manager.options.latex.environments.set(
        "custom_test",
        {
            "separator": "&",
            "line_separator": r" \\" + "\n ",
            "supports_multiple_labels": True,
            "outer_environment": "align",
            "inner_environment": None,
        },
    )

    eqns = {x: 1, y: 2}
    result = show_eqn(eqns, environment="custom_test", debug=True)

    assert r"\begin{align}" in result.data
    assert "&" in result.data


def test_environment_with_argument():
    """Test environment with argument (alignat)."""
    eqns = {x: 1, y: 2}
    result = show_eqn(eqns, environment="alignat", env_arg="{2}", debug=True)

    assert r"\begin{alignat}{2}" in result.data
    assert r"\end{alignat}" in result.data


def test_environment_with_multiple_arguments():
    """Test custom environment with multiple arguments."""
    from keecas.config import get_config_manager

    config_manager = get_config_manager()

    # Add custom environment for testing
    config_manager.options.latex.environments.set(
        "test_multi_arg",
        {
            "separator": "&",
            "line_separator": r" \\" + "\n ",
            "supports_multiple_labels": False,
            "outer_environment": "customenv",
            "inner_environment": None,
        },
    )

    eqns = {x: 1}
    result = show_eqn(eqns, environment="test_multi_arg", env_arg="{2}{l}", debug=True)

    assert r"\begin{customenv}{2}{l}" in result.data
    assert r"\end{customenv}" in result.data


def test_nested_environment_with_argument():
    """Test nested environment with argument (argument on inner environment)."""
    from keecas.config import get_config_manager

    config_manager = get_config_manager()

    # Add custom nested environment for testing
    config_manager.options.latex.environments.set(
        "test_nested_arg",
        {
            "separator": "&",
            "line_separator": r" \\" + "\n ",
            "supports_multiple_labels": False,
            "outer_environment": "equation",
            "inner_environment": "aligned",
            "inner_prefix": "",
            "inner_suffix": "",
        },
    )

    eqns = {x: 1, y: 2}
    result = show_eqn(eqns, environment="test_nested_arg", env_arg="{2}", debug=True)

    # Argument should be on inner environment
    assert r"\begin{equation}" in result.data
    assert r"\begin{aligned}{2}" in result.data
    assert r"\end{aligned}" in result.data
    assert r"\end{equation}" in result.data


def test_inline_environment_dict():
    """Test passing environment definition as dict."""
    eqns = {x: 1, y: 2}

    inline_env = {
        "separator": "&",
        "line_separator": r" \\" + "\n ",
        "supports_multiple_labels": True,
        "outer_environment": "align",
    }

    result = show_eqn(eqns, environment=inline_env, debug=True)

    assert r"\begin{align}" in result.data
    assert "&" in result.data
    assert r"\end{align}" in result.data


def test_inline_environment_object():
    """Test passing EnvironmentDefinition object."""
    from keecas.config import EnvironmentDefinition

    eqns = {x: 1}

    inline_env = EnvironmentDefinition(
        separator="",
        line_separator="",
        supports_multiple_labels=False,
        outer_environment="equation",
    )

    result = show_eqn(eqns, environment=inline_env, debug=True)

    assert r"\begin{equation}" in result.data
    assert r"\end{equation}" in result.data


def test_inline_environment_with_prefixes():
    """Test inline environment with outer prefix/suffix."""
    eqns = {x: 1}

    inline_env = {
        "separator": "",
        "line_separator": "",
        "supports_multiple_labels": False,
        "outer_environment": "equation",
        "outer_prefix": r"\boxed{",
        "outer_suffix": "}",
    }

    result = show_eqn(eqns, environment=inline_env, debug=True)

    assert r"\boxed{" in result.data
    assert r"\begin{equation}" in result.data
    assert r"\end{equation}}" in result.data


def test_float_format_config_fallback():
    """Test that float_format falls back to config.display.default_float_format."""
    from keecas.display import config

    # Save original value
    original_format = config.display.default_float_format

    try:
        # Set config default
        config.display.default_float_format = ".3f"

        # Use show_eqn without explicit float_format
        eqns = {x: 3.14159265}
        result = show_eqn(eqns, debug=True)

        # Should use config format (.3f)
        assert "3.142" in result.data

        # Explicit float_format should override config
        result = show_eqn(eqns, float_format=".1f", debug=True)
        assert "3.1" in result.data

    finally:
        # Restore original value
        config.display.default_float_format = original_format


def test_float_format_none_uses_config():
    """Test that float_format=None explicitly uses config default."""
    from keecas.display import config

    original_format = config.display.default_float_format

    try:
        config.display.default_float_format = ".2f"

        eqns = {x: 2.71828}
        result = show_eqn(eqns, float_format=None, debug=True)

        assert "2.72" in result.data

    finally:
        config.display.default_float_format = original_format


def test_sep_none_uses_environment_separator():
    """Test that sep=None uses environment-specific separator."""
    # Test with align (separator = "&")
    eqns = {x: 1, y: 2}
    result = show_eqn(eqns, environment="align", sep=None, debug=True)
    assert "x & == 1" in result.data or "x & = 1" in result.data

    # Test with equation (separator = "")
    eqns = {x: 1}
    result = show_eqn(eqns, environment="equation", sep=None, debug=True)
    assert "x  == 1" in result.data or "x  = 1" in result.data  # Two spaces, no separator

    # Test explicit override still works
    eqns = {x: 1, y: 2}
    result = show_eqn(eqns, environment="align", sep="&&", debug=True)
    assert "x && == 1" in result.data or "x && = 1" in result.data


def test_sep_default_is_environment_based():
    """Test that omitting sep parameter uses environment separator."""
    # Don't specify sep - should use environment default
    eqns = {x: 1, y: 2}

    # align environment - should use "&"
    result = show_eqn(eqns, environment="align", debug=True)
    assert "x & == 1" in result.data or "x & = 1" in result.data

    # equation environment - should use ""
    eqns_single = {x: 1}
    result = show_eqn(eqns_single, environment="equation", debug=True)
    assert "x  == 1" in result.data or "x  = 1" in result.data


def test_float_format_validation():
    """Test that invalid float formats raise clear errors."""
    eqns = {x: 3.14159}

    # Valid formats should work
    valid_formats = [".3f", "{:.3f}", ":.3f", ".2e", "g", "<10.2f", "^8.1f"]
    for fmt in valid_formats:
        result = show_eqn(eqns, float_format=fmt, debug=True)
        assert isinstance(result.data, str)

    # Invalid formats should raise ValueError
    invalid_formats = ["invalid", ".3x", "not_a_format"]
    for fmt in invalid_formats:
        with pytest.raises(ValueError, match="Invalid float_format"):
            show_eqn(eqns, float_format=fmt, debug=True)


def test_float_format_structure():
    """Test that float_format supports same structures as eqns (dict, list, Dataframe)."""
    # Test with dict structure - different format per key
    eqns = {x: 3.14159, y: 2.71828}
    float_format = {x: ".3f", y: ".2f"}
    result = show_eqn(eqns, float_format=float_format, debug=True)
    assert "3.142" in result.data  # x formatted with .3f
    assert "2.72" in result.data  # y formatted with .2f

    # Test with dict containing list - cell-by-cell formatting for multiple columns
    eqns_list = [{x: 3.14159}, {x: 2.71828}]  # Creates: x & =3.14159 & =2.71828
    # Format list must include key column (None for key, then formats for values)
    float_format_with_list = {x: [None, ".3f", ".1f"]}  # None for key, then value formats
    result = show_eqn(eqns_list, float_format=float_format_with_list, debug=True)
    assert "3.142" in result.data  # First value column with .3f
    assert "2.7" in result.data  # Second value column with .1f

    # Test with dict pattern - key uses one format, other keys use None
    eqns = {x: 1.5, y: 2.5}
    float_format = {x: ".1f"}  # x uses .1f, y uses None (no formatting)
    result = show_eqn(eqns, float_format=float_format, debug=True)
    assert "1.5" in result.data  # x with .1f
    assert "2.5" in result.data  # y with no formatting


def test_last_element_filler_scalar():
    """Test scalar values repeat across columns."""
    eqns = [{x: 1.0}, {x: 2.0}, {x: 3.0}]  # 3 value columns with floats
    result = show_eqn(eqns, float_format=".2f", debug=True)
    assert "1.00" in result.data
    assert "2.00" in result.data
    assert "3.00" in result.data


def test_last_element_filler_single_list():
    """Test single-element list equivalent to scalar."""
    eqns = [{x: 1.5}, {x: 2.5}]

    # Scalar
    result1 = show_eqn(eqns, float_format=".1f", debug=True)

    # Single-element list
    result2 = show_eqn(eqns, float_format=[".1f"], debug=True)

    # Both should format consistently (last element fills)
    assert "1.5" in result1.data
    assert "1.5" in result2.data
    assert "2.5" in result1.data
    assert "2.5" in result2.data


def test_last_element_filler_multi_list():
    """Test last element fills remaining columns."""
    eqns = [{x: 1.111}, {x: 2.222}, {x: 3.333}]  # 3 value columns + 1 key column = 4 total

    # [col0, col1, col2+]
    result = show_eqn(eqns, float_format=[None, ".2f"], debug=True)

    # Col 0 (key): no formatting
    assert "x" in result.data
    # Col 1+: .2f formatting (last element fills)
    assert "1.11" in result.data
    assert "2.22" in result.data
    assert "3.33" in result.data


def test_last_element_filler_exact_width():
    """Test list with exact width, no padding needed."""
    eqns = [{x: 1.1}, {x: 2.2}, {x: 3.3}]
    # 3 value columns + 1 key = 4 total, so provide 4 format specs
    result = show_eqn(eqns, float_format=[None, ".1f", ".1f", ".2f"], debug=True)

    assert "1.1" in result.data  # Col 1: .1f
    assert "2.2" in result.data  # Col 2: .1f
    assert "3.30" in result.data  # Col 3: .2f


def test_last_element_filler_none():
    """Test explicit None as filler."""
    eqns = [{x: 1.5}, {x: 2.5}, {x: 3.5}]
    result = show_eqn(eqns, float_format=[".1f", None], debug=True)

    # Col 0 (key): should have "x"
    # Col 1: formatted with .1f
    assert "1.5" in result.data
    # Col 2+: no format (None fills)
    assert "2.5" in result.data
    assert "3.5" in result.data


def test_col_wrap_tuple_values():
    """Test col_wrap with tuple values (solves ambiguity issue)."""
    eqns = [{x: 1}, {x: 2}]

    # Single tuple for all columns
    result1 = show_eqn(eqns, col_wrap=("=", ""), debug=True)
    assert result1.data.count("=") >= 2  # Both value columns should have "="

    # List with tuple values - last tuple fills
    result2 = show_eqn(eqns, col_wrap=[None, ("=", "")], debug=True)
    # Column 0 (key): no wrap
    # Column 1+: "=" prefix (last element fills)
    assert "=1" in result2.data or "= 1" in result2.data
    assert "=2" in result2.data or "= 2" in result2.data


def test_col_wrap_different_tuples():
    """Test col_wrap with different tuples per column."""
    eqns = [{x: 1}, {x: 2}, {x: 3}]
    result = show_eqn(eqns, col_wrap=[None, ("=", ""), (r"\quad(", ")")], debug=True)

    # Col 0 (key): no wrap → "x"
    # Col 1 (value 1): "=" prefix → "=1" or "= 1"
    # Col 2 (value 2): "\quad(" prefix, ")" suffix → "\quad(...2...)"
    # Col 3 (value 3): "\quad(" prefix, ")" suffix (last element fills) → "\quad(...3...)"
    assert "x" in result.data
    assert "=1" in result.data or "= 1" in result.data
    assert r"\quad(" in result.data and "2" in result.data and ")" in result.data
    assert r"\quad(" in result.data and "3" in result.data and ")" in result.data


def test_dict_with_list_values():
    """Test dict seed with list values uses filler per row."""
    eqns = [{x: 1.11, y: 2.22}, {x: 3.33, y: 4.44}]

    float_format = {
        x: [".1f", ".2f"],  # x: col 0 .1f, col 1 .2f, col 2+ .2f (last fills)
        y: ".3f",  # y: all cols .3f
    }

    result = show_eqn(eqns, float_format=float_format, debug=True)

    # x row: 1.1, 3.33 (col 0: .1f, col 1+: .2f fills)
    assert "1.1" in result.data
    assert "3.33" in result.data

    # y row: 2.220, 4.440 (all .3f)
    assert "2.220" in result.data
    assert "4.440" in result.data


def test_cell_formatter_list():
    """Test cell_formatter with list and last-element filler."""
    from keecas import format_value

    def custom_fmt(val, col_idx, **kwargs):
        return f"CUSTOM[{val}]"

    eqns = [{x: "a"}, {x: "b"}]

    # Use custom for col 0 (key), default for rest (last element fills)
    result = show_eqn(eqns, cell_formatter=[custom_fmt, format_value], debug=True)

    # Col 0 uses custom_fmt (but might not apply to key)
    # Col 1+ uses format_value (should have \text{})
    assert r"\text{" in result.data


def test_empty_list():
    """Test empty list seed."""
    eqns = {x: 1}
    # Empty list should default to None for all columns
    result = show_eqn(eqns, float_format=[], debug=True)
    assert isinstance(result, Latex)
    # No formatting should be applied (None filler)
    assert "1" in result.data


def test_list_longer_than_width():
    """Test list truncation when longer than width."""
    eqns = {x: 1.5}  # Only 1 value column + 1 key column = 2 total
    # List has 5 elements but only 2 columns needed
    result = show_eqn(eqns, float_format=[".1f", ".2f", ".3f", ".4f", ".5f"], debug=True)
    # Should use first 2 elements, truncate the rest
    assert isinstance(result, Latex)
    # First value column should use .2f (index 1)
    assert "1.50" in result.data


if __name__ == "__main__":
    pytest.main()
