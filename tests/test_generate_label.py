"""Tests for generate_label function with callable support."""

import pytest
from sympy import symbols

from keecas import Dataframe, generate_label, generate_unique_label, show_eqn
from keecas.config.manager import get_config_manager


@pytest.fixture
def config():
    """Provide access to config for testing."""
    return get_config_manager().options


def test_generate_label_string(config):
    """Test generate_label with string input."""
    label = generate_label("my-label")
    expected = f"{config.latex.eq_prefix}my-label{config.latex.eq_suffix}"
    assert label == expected


def test_generate_label_dict(config):
    """Test generate_label with dict input."""
    F, A = symbols("F, A")
    labels = {F: "force", A: "area"}
    result = generate_label(labels)

    assert result[F] == f"{config.latex.eq_prefix}force{config.latex.eq_suffix}"
    assert result[A] == f"{config.latex.eq_prefix}area{config.latex.eq_suffix}"


def test_generate_label_dict_with_empty_values(config):
    """Test generate_label with dict containing None/empty values."""
    F, A = symbols("F, A")
    labels = {F: "force", A: None}
    result = generate_label(labels)

    assert result[F] == f"{config.latex.eq_prefix}force{config.latex.eq_suffix}"
    assert result[A] == ""


def test_generate_label_unique_id_string(config):
    """Test generate_label with unique_id=True for string."""
    label = generate_label("my-key", unique_id=True)

    # Should start with prefix and be deterministic
    assert label.startswith(config.latex.eq_prefix)

    # Same input should give same output
    label2 = generate_label("my-key", unique_id=True)
    assert label == label2


def test_generate_label_unique_id_dict(config):
    """Test generate_label with unique_id=True for dict."""
    F, A = symbols("F, A")
    labels = {F: "force", A: "area"}
    result = generate_label(labels, unique_id=True)

    # Should generate hash-based IDs
    assert result[F].startswith(config.latex.eq_prefix)
    assert result[A].startswith(config.latex.eq_prefix)

    # Should be deterministic
    result2 = generate_label(labels, unique_id=True)
    assert result[F] == result2[F]
    assert result[A] == result2[A]




def test_generate_unique_label_string(config):
    """Test generate_unique_label convenience function with string."""
    label = generate_unique_label("test-key")

    assert label.startswith(config.latex.eq_prefix)

    # Should be deterministic
    label2 = generate_unique_label("test-key")
    assert label == label2


def test_generate_unique_label_dict(config):
    """Test generate_unique_label convenience function with dict."""
    F, A = symbols("F, A")
    labels = {F: "force", A: "area"}
    result = generate_unique_label(labels)

    assert result[F].startswith(config.latex.eq_prefix)
    assert result[A].startswith(config.latex.eq_prefix)


def test_show_eqn_with_callable_label(config):
    """Test show_eqn with callable label."""
    F, A = symbols("F, A")

    def my_labeler(key, values):
        # Generate label based on key and number of values
        return f"{config.latex.eq_prefix}{key}-{len(values)}{config.latex.eq_suffix}"

    eqns = Dataframe({F: [100, 200], A: [20, 30]})

    # Should not raise error
    result = show_eqn(eqns, label=my_labeler)
    assert result is not None


def test_show_eqn_with_dict_callable_label(config):
    """Test show_eqn with dict containing callable labels."""
    F, A = symbols("F, A")

    def force_labeler(key, values):
        return f"{config.latex.eq_prefix}force-custom{config.latex.eq_suffix}"

    labels = {
        F: force_labeler,
        A: f"{config.latex.eq_prefix}area-fixed{config.latex.eq_suffix}",
    }

    eqns = Dataframe({F: [100], A: [20]})

    # Should not raise error
    result = show_eqn(eqns, label=labels)
    assert result is not None


def test_callable_label_receives_correct_arguments():
    """Test that callable labels receive key and value list."""
    F, A = symbols("F, A")

    received_args = []

    def capture_labeler(key, values):
        received_args.append((key, values))
        return "eq-test"

    eqns = Dataframe({F: [100, 200], A: [20]})
    show_eqn(eqns, label=capture_labeler)

    # Should have been called for each key
    assert len(received_args) == 2

    # Check F's call
    f_call = [call for call in received_args if call[0] == F][0]
    assert f_call[1] == [100, 200]

    # Check A's call - Dataframe pads shorter rows with None
    a_call = [call for call in received_args if call[0] == A][0]
    assert a_call[1] == [20, None]  # Dataframe auto-pads to equal length


def test_generate_label_unsupported_type():
    """Test that unsupported types raise TypeError."""
    with pytest.raises(TypeError, match="Unsupported type"):
        generate_label(123)  # int is not supported


def test_integration_with_partial():
    """Test using functools.partial with generate_label."""
    from functools import partial

    F, A = symbols("F, A")

    # Create a partial function with unique_id=True
    auto_labeler = partial(generate_label, unique_id=True)

    # Use it to generate labels
    label_str = auto_labeler("test")
    assert label_str.startswith("eq-")

    label_dict = auto_labeler({F: "force", A: "area"})
    assert all(v.startswith("eq-") for v in label_dict.values())


