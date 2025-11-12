"""Tests for col_wrapper module."""

import pytest
from sympy import symbols

from keecas import wrap_column


class TestWrapColumnDispatch:
    """Test singledispatch behavior of wrap_column."""

    def test_integer_lhs(self):
        """Integer in LHS column (col_index=0) gets no wrapping."""
        result = wrap_column(42, col_index=0)
        assert result == ("", "")

    def test_integer_rhs(self):
        """Integer in RHS column (col_index=1+) gets equals prefix."""
        result = wrap_column(42, col_index=1)
        assert result == ("= ", "")

        result = wrap_column(100, col_index=2)
        assert result == ("= ", "")

    def test_float_lhs(self):
        """Float in LHS column gets no wrapping."""
        result = wrap_column(3.14, col_index=0)
        assert result == ("", "")

    def test_float_rhs(self):
        """Float in RHS column gets equals prefix."""
        result = wrap_column(3.14159, col_index=1)
        assert result == ("= ", "")

    def test_string_lhs(self):
        """String in LHS column gets no wrapping."""
        result = wrap_column("text", col_index=0)
        assert result == ("", "")

    def test_string_rhs(self):
        """String in RHS column gets quad spacing."""
        result = wrap_column("verified", col_index=1)
        assert result == (r"\quad", "")

    def test_sympy_symbol_lhs(self):
        """SymPy symbol in LHS column gets no wrapping."""
        x = symbols("x")
        result = wrap_column(x, col_index=0)
        assert result == ("", "")

    def test_sympy_symbol_rhs(self):
        """SymPy symbol in RHS column gets equals prefix."""
        sigma = symbols(r"\sigma")
        result = wrap_column(sigma, col_index=1)
        assert result == ("= ", "")

    def test_sympy_expression_rhs(self):
        """SymPy expression in RHS column gets equals prefix."""
        x, y = symbols("x y")
        expr = x + y
        result = wrap_column(expr, col_index=1)
        assert result == ("= ", "")

    def test_unknown_type_fallback(self):
        """Unknown types fall back to no wrapping."""

        class CustomType:
            pass

        custom = CustomType()
        result = wrap_column(custom, col_index=0)
        assert result == ("", "")

        result = wrap_column(custom, col_index=1)
        assert result == ("", "")


class TestWrapColumnOptionalTypes:
    """Test wrap_column with optional dependency types."""

    def test_pint_quantity_lhs(self):
        """Pint Quantity in LHS column gets no wrapping."""
        try:
            import pint

            u = pint.UnitRegistry()
            qty = 10 * u.meter
            result = wrap_column(qty, col_index=0)
            assert result == ("", "")
        except ImportError:
            pytest.skip("Pint not installed")

    def test_pint_quantity_rhs(self):
        """Pint Quantity in RHS column gets equals prefix."""
        try:
            import pint

            u = pint.UnitRegistry()
            qty = 50 * u.kilonewton
            result = wrap_column(qty, col_index=1)
            assert result == ("= ", "")
        except ImportError:
            pytest.skip("Pint not installed")

    def test_markdown_lhs(self):
        """IPython Markdown in LHS column gets no wrapping."""
        try:
            from IPython.display import Markdown

            md = Markdown("text")
            result = wrap_column(md, col_index=0)
            assert result == ("", "")
        except ImportError:
            pytest.skip("IPython not installed")

    def test_markdown_rhs(self):
        """IPython Markdown in RHS column gets quad spacing."""
        try:
            from IPython.display import Markdown

            md = Markdown("verified")
            result = wrap_column(md, col_index=1)
            assert result == (r"\quad", "")
        except ImportError:
            pytest.skip("IPython not installed")

    def test_latex_lhs(self):
        """IPython Latex in LHS column gets no wrapping."""
        try:
            from IPython.display import Latex

            ltx = Latex(r"\alpha")
            result = wrap_column(ltx, col_index=0)
            assert result == ("", "")
        except ImportError:
            pytest.skip("IPython not installed")

    def test_latex_rhs(self):
        """IPython Latex in RHS column gets quad spacing."""
        try:
            from IPython.display import Latex

            ltx = Latex(r"\beta")
            result = wrap_column(ltx, col_index=1)
            assert result == (r"\quad", "")
        except ImportError:
            pytest.skip("IPython not installed")


class TestWrapColumnCustomRegistration:
    """Test user registration of custom type wrappers."""

    def test_register_custom_type(self):
        """User can register wrapper for custom type."""

        class MyCustomType:
            def __init__(self, value):
                self.value = value

        @wrap_column.register(MyCustomType)
        def wrap_custom(value, col_index=0, **kwargs):
            if col_index == 0:
                return ("", "")
            return (r"\approx ", "")

        custom = MyCustomType(42)

        # LHS - no wrapping
        result = wrap_column(custom, col_index=0)
        assert result == ("", "")

        # RHS - custom prefix
        result = wrap_column(custom, col_index=1)
        assert result == (r"\approx ", "")


class TestWrapColumnEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_col_index_zero_default(self):
        """col_index defaults to 0 (LHS behavior)."""
        result = wrap_column(42)  # No col_index argument
        assert result == ("", "")

    def test_col_index_higher_values(self):
        """col_index > 1 still treated as RHS."""
        result = wrap_column(42, col_index=5)
        assert result == ("= ", "")

        result = wrap_column("text", col_index=10)
        assert result == (r"\quad", "")

    def test_kwargs_ignored(self):
        """Extra kwargs are accepted and ignored."""
        result = wrap_column(42, col_index=1, extra_param="ignored")
        assert result == ("= ", "")

    def test_none_value(self):
        """None value falls back to default (no wrapping)."""
        result = wrap_column(None, col_index=0)
        assert result == ("", "")

        result = wrap_column(None, col_index=1)
        assert result == ("", "")

    def test_zero_value(self):
        """Zero values work correctly."""
        result = wrap_column(0, col_index=1)
        assert result == ("= ", "")

        result = wrap_column(0.0, col_index=1)
        assert result == ("= ", "")

    def test_negative_values(self):
        """Negative values work correctly."""
        result = wrap_column(-42, col_index=1)
        assert result == ("= ", "")

        result = wrap_column(-3.14, col_index=1)
        assert result == ("= ", "")

    def test_empty_string(self):
        """Empty string works correctly."""
        result = wrap_column("", col_index=0)
        assert result == ("", "")

        result = wrap_column("", col_index=1)
        assert result == (r"\quad", "")
