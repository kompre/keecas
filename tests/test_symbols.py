from sympy import Symbol

from keecas import _escape_commas_in_braces, symbols


class TestEscapeCommasInBraces:
    def test_no_braces_unchanged(self):
        assert _escape_commas_in_braces("F, A") == "F, A"

    def test_no_comma_unchanged(self):
        assert _escape_commas_in_braces(r"\sigma_{Rd}") == r"\sigma_{Rd}"

    def test_comma_inside_braces_escaped(self):
        # trailing space after comma inside braces is stripped (prevents sympy space-split)
        assert _escape_commas_in_braces(r"F_{s, b}") == r"F_{s\,b}"

    def test_comma_without_space_inside_braces_escaped(self):
        assert _escape_commas_in_braces(r"F_{s,b}") == r"F_{s\,b}"

    def test_comma_outside_braces_unchanged(self):
        assert _escape_commas_in_braces(r"F_{s, b}, a_{B}") == r"F_{s\,b}, a_{B}"

    def test_already_escaped_space_stripped(self):
        # already escaped \, still strips trailing space
        assert _escape_commas_in_braces(r"\tau_{1\, Rd}") == r"\tau_{1\,Rd}"

    def test_already_escaped_no_space_unchanged(self):
        assert _escape_commas_in_braces(r"\tau_{1\,Rd}") == r"\tau_{1\,Rd}"

    def test_multiple_commas_inside_braces(self):
        assert _escape_commas_in_braces(r"F_{a, b, c}") == r"F_{a\,b\,c}"

    def test_nested_braces(self):
        assert _escape_commas_in_braces(r"F_{{a, b}}") == r"F_{{a\,b}}"

    def test_mixed_multiple_symbols(self):
        result = _escape_commas_in_braces(r"\tau_{1, Rd}, \gamma_{M0}")
        assert result == r"\tau_{1\,Rd}, \gamma_{M0}"

    def test_empty_string(self):
        assert _escape_commas_in_braces("") == ""

    def test_comma_only(self):
        assert _escape_commas_in_braces(",") == ","


class TestSymbolsWrapper:
    def test_single_symbol(self):
        x = symbols("x")
        assert isinstance(x, Symbol)
        assert str(x) == "x"

    def test_multiple_symbols_comma_separated(self):
        F, A = symbols("F, A")
        assert str(F) == "F"
        assert str(A) == "A"

    def test_multiple_symbols_space_separated(self):
        x, y = symbols("x y")
        assert str(x) == "x"
        assert str(y) == "y"

    def test_comma_inside_braces_auto_escaped(self):
        tau_Rd = symbols(r"\tau_{1, Rd}")
        assert isinstance(tau_Rd, Symbol)

    def test_auto_escape_allows_unpacking(self):
        tau_Rd, gamma_M0 = symbols(r"\tau_{1, Rd}, \gamma_{M0}")
        assert isinstance(tau_Rd, Symbol)
        assert isinstance(gamma_M0, Symbol)

    def test_manual_escape_still_works(self):
        tau_Rd, gamma_M0 = symbols(r"\tau_{1\, Rd}, \gamma_{M0}")
        assert isinstance(tau_Rd, Symbol)
        assert isinstance(gamma_M0, Symbol)

    def test_non_string_names_passthrough(self):
        x, y = symbols(["x", "y"])
        assert str(x) == "x"
        assert str(y) == "y"

    def test_kwargs_passthrough(self):
        x = symbols("x", positive=True)
        assert x.is_positive

    def test_latex_symbol_names(self):
        F, A, sigma = symbols(r"F, A, \sigma")
        assert str(F) == "F"
        assert str(A) == "A"

    def test_complex_engineering_symbols(self):
        sigma_Sd, sigma_Rd = symbols(r"\sigma_{Sd}, \sigma_{Rd}")
        assert isinstance(sigma_Sd, Symbol)
        assert isinstance(sigma_Rd, Symbol)

    def test_comma_in_subscript_no_extra_symbols(self):
        result = symbols(r"\tau_{1, Rd}")
        assert isinstance(result, Symbol)

    def test_mixed_escaped_and_unescaped(self):
        tau_Rd, gamma_M0 = symbols(r"\tau_{1\, Rd}, \gamma_{M0}")
        assert isinstance(tau_Rd, Symbol)
        assert isinstance(gamma_M0, Symbol)
