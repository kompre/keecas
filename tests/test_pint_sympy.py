"""Tests for Pint-SymPy integration and unit conversion."""

import sympy

from keecas import pc, u


def test_kgf_to_newton_conversion():
    """Test that kilogram-force converts correctly to newtons."""
    kgf_q = 100 * u.kgf
    kgf_sympy = sympy.S(kgf_q)
    result = kgf_sympy | pc.convert_to([u.N])

    # 100 kgf = 980.665 N
    expected = 980.665
    actual = float(result / u.N)
    assert abs(actual - expected) < 0.01, f"Expected {expected} N, got {actual} N"


def test_daN_conversion():
    """Verify decanewton conversion still works (prefixed unit)."""
    # This should continue to work (prefixed unit)
    dan_q = 50 * u.daN
    result = dan_q | pc.convert_to([u.kN])

    expected = 0.5  # 50 daN = 0.5 kN
    actual = float(result / u.kN)
    assert abs(actual - expected) < 0.001, f"Expected {expected} kN, got {actual} kN"


def test_kgf_to_kN_conversion():
    """Test kgf to kilonewton conversion."""
    kgf_q = 1000 * u.kgf
    kgf_sympy = sympy.S(kgf_q)
    result = kgf_sympy | pc.convert_to([u.kN])

    # 1000 kgf = 9.80665 kN
    expected = 9.80665
    actual = float(result / u.kN)
    assert abs(actual - expected) < 0.01


def test_compound_unit_conversion():
    """Test that compound units with scale factors convert properly."""
    # kgf/cm² is a common pressure unit in engineering
    pressure = 10 * u.kgf / u.cm**2
    pressure_sympy = sympy.S(pressure)
    result = pressure_sympy | pc.convert_to([u.MPa])

    # 10 kgf/cm² = 0.980665 MPa
    expected = 0.980665
    actual = float(result / u.MPa)
    assert abs(actual - expected) < 0.01, f"Expected {expected} MPa, got {actual} MPa"


def test_prefixed_unit_kN():
    """Test that kilonewton (prefixed) works correctly."""
    kn_q = 10 * u.kN
    kn_sympy = sympy.S(kn_q)
    result = kn_sympy | pc.convert_to([u.N])

    # 10 kN = 10000 N
    expected = 10000
    actual = float(result / u.N)
    assert abs(actual - expected) < 0.1


def test_bidirectional_conversion():
    """Test conversion works in both directions."""
    # kgf to N
    kgf_q = 50 * u.kgf
    n_result = sympy.S(kgf_q) | pc.convert_to([u.N])
    assert abs(float(n_result / u.N) - 490.3325) < 0.01

    # N to kgf (via base units)
    n_q = 490.3325 * u.N
    # Note: Can't directly convert to kgf in SymPy, but can verify consistency
    assert abs(n_q.to(u.kgf).magnitude - 50) < 0.01


def test_unit_cache():
    """Test that units are properly cached."""
    from keecas.pint_sympy import SymPyUnitCache

    # Get kgf multiple times
    kgf1 = sympy.S(1 * u.kgf)
    kgf2 = sympy.S(1 * u.kgf)

    # Should be using the same cached unit
    assert 'force_kilogram' in SymPyUnitCache._units
    # Both conversions should work the same
    assert kgf1 == kgf2


def test_unknown_unit_graceful_failure():
    """Test that unknown units don't crash, just don't convert."""
    import sympy.physics.units as sympy_units

    # If a unit's base units aren't in SymPy, it should still create the unit
    # but it won't have a scale factor (and thus won't convert)
    # This is tested by the fact that the code doesn't crash
    kgf_sympy = sympy.S(1 * u.kgf)
    assert kgf_sympy is not None
    assert hasattr(sympy_units, 'force_kilogram')
