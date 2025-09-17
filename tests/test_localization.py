"""
Tests for the localization system.
"""

import pytest
import tempfile
import toml
from pathlib import Path
from keecas.localization import (
    set_language,
    translate,
    get_language,
    register_language,
    get_available_languages,
    reload_configuration,
    get_configuration
)


def test_default_language():
    """Test that default language is English."""
    assert get_language() == "en"


def test_basic_translation():
    """Test basic translation functionality."""
    # English (default)
    assert translate("for") == "for"
    assert translate("otherwise") == "otherwise"

    # Switch to Italian
    set_language("it")
    assert translate("for") == "per"
    assert translate("otherwise") == "altrimenti"

    # Reset to English for other tests
    set_language("en")


def test_priority_hierarchy():
    """Test translation priority hierarchy."""
    set_language("it")

    # Test direct substitution (highest priority)
    custom_subs = {"for": "CUSTOM_FOR"}
    assert translate("for", substitutions=custom_subs) == "CUSTOM_FOR"

    # Test document language (medium priority)
    assert translate("for", language="en") == "for"
    assert translate("for", language="it") == "per"

    # Test fallback to current language
    assert translate("for") == "per"

    # Reset
    set_language("en")


def test_unknown_key():
    """Test that unknown keys return unchanged."""
    assert translate("unknown_key") == "unknown_key"


def test_language_registration():
    """Test registering new languages."""
    # Register Spanish
    spanish = {"for": "para", "otherwise": "de lo contrario"}
    register_language("es", spanish)

    assert "es" in get_available_languages()

    set_language("es")
    assert translate("for") == "para"
    assert translate("otherwise") == "de lo contrario"

    # Reset
    set_language("en")


def test_verification_terms():
    """Test verification terms translation."""
    # English
    set_language("en")
    assert translate("VERIFICATO") == "VERIFIED"
    assert translate("NON VERIFICATO") == "NOT VERIFIED"

    # Italian
    set_language("it")
    assert translate("VERIFICATO") == "VERIFICATO"
    assert translate("NON VERIFICATO") == "NON VERIFICATO"

    # Reset
    set_language("en")


def test_available_languages():
    """Test getting available languages."""
    languages = get_available_languages()
    assert "en" in languages
    assert "it" in languages
    assert len(languages) >= 2


def test_toml_config_language():
    """Test loading language from TOML config file."""
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        config = {"language": "it"}
        toml.dump(config, f)
        config_path = Path(f.name)

    try:
        # Patch the config search paths to use our temp file
        from keecas.localization.config import _config
        original_paths = _config._get_config_search_paths
        _config._get_config_search_paths = lambda: [config_path]

        # Reload configuration
        reload_configuration()

        # Language should be loaded from config
        assert get_language() == "it"
        assert translate("for") == "per"

    finally:
        # Cleanup
        config_path.unlink()
        _config._get_config_search_paths = original_paths
        reload_configuration()  # Reset to default


def test_toml_config_custom_translations():
    """Test custom translations from TOML config file."""
    # Create temporary config file with custom translations
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        config = {
            "language": "en",
            "localization": {
                "custom_translations": {
                    "for": "CUSTOM_FOR",
                    "custom_key": "CUSTOM_VALUE"
                }
            }
        }
        toml.dump(config, f)
        config_path = Path(f.name)

    try:
        # Patch the config search paths
        from keecas.localization.config import _config
        original_paths = _config._get_config_search_paths
        _config._get_config_search_paths = lambda: [config_path]

        # Reload configuration
        reload_configuration()

        # Custom translations should have high priority
        assert translate("for") == "CUSTOM_FOR"
        assert translate("custom_key") == "CUSTOM_VALUE"

        # But direct substitutions should still have highest priority
        assert translate("for", substitutions={"for": "DIRECT_OVERRIDE"}) == "DIRECT_OVERRIDE"

    finally:
        # Cleanup
        config_path.unlink()
        _config._get_config_search_paths = original_paths
        reload_configuration()


def test_toml_config_priority():
    """Test that TOML config has correct priority in hierarchy."""
    # Create config with Italian
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        config = {"language": "it"}
        toml.dump(config, f)
        config_path = Path(f.name)

    try:
        # Patch config
        from keecas.localization.config import _config
        original_paths = _config._get_config_search_paths
        _config._get_config_search_paths = lambda: [config_path]
        reload_configuration()

        # Config sets Italian as default
        assert translate("for") == "per"

        # Document language overrides config
        assert translate("for", language="en") == "for"

        # Global language setting overrides config
        set_language("en")
        assert translate("for") == "for"

        # Direct substitutions override everything
        assert translate("for", substitutions={"for": "OVERRIDE"}) == "OVERRIDE"

    finally:
        # Cleanup
        config_path.unlink()
        _config._get_config_search_paths = original_paths
        reload_configuration()
        set_language("en")  # Reset


def test_no_config_file():
    """Test behavior when no config file exists."""
    # Patch to return non-existent paths
    from keecas.localization.config import _config
    original_paths = _config._get_config_search_paths
    _config._get_config_search_paths = lambda: [Path("/nonexistent/config.toml")]

    try:
        reload_configuration()

        # Should default to English
        assert get_language() == "en"
        assert translate("for") == "for"
        assert not get_configuration().has_config()

    finally:
        # Cleanup
        _config._get_config_search_paths = original_paths
        reload_configuration()


def test_display_module_integration():
    """Test integration with display module options and show_eqn function."""
    from keecas.display import options, show_eqn
    from sympy import symbols

    # Reset to defaults
    options.language = None
    set_language("en")

    # Test that options.language works
    options.language = "it"
    x = symbols('x')
    # This should use Italian translations due to options.language
    result = show_eqn({"x": "for*x"}, debug=True)
    # Note: This test verifies the integration exists;
    # full LaTeX output testing would require more complex setup

    # Test direct language override in show_eqn
    result_en = show_eqn({"x": "for*x"}, language="en", debug=True)
    result_it = show_eqn({"x": "for*x"}, language="it", debug=True)

    # Test direct substitutions (highest priority)
    custom_subs = {"for": "CUSTOM_FOR"}
    result_custom = show_eqn({"x": "for*x"}, substitutions=custom_subs, debug=True)

    # Reset
    options.language = None
    set_language("en")


def test_verifica_function_localization():
    """Test verifica() function with localization support."""
    from keecas.display import verifica, options
    from sympy import symbols, Le, Gt

    x = symbols('x')

    # Reset to defaults
    options.language = None
    set_language("en")

    # Test English (default)
    result_pass = verifica(5, 10, Le)
    result_fail = verifica(15, 10, Le)

    # Check that result contains Markdown object
    assert hasattr(result_pass, 'data')
    assert hasattr(result_fail, 'data')

    # Test Italian via global setting
    set_language("it")
    result_it_pass = verifica(5, 10, Le)
    result_it_fail = verifica(15, 10, Le)

    # Test document-level language override
    options.language = "en"
    result_doc_en = verifica(5, 10, Le)

    # Test function-level language override
    result_func_it = verifica(5, 10, Le, language="it")

    # Test direct substitutions (highest priority)
    custom_subs = {
        "VERIFICATO": "CUSTOM_PASS",
        "NON VERIFICATO": "CUSTOM_FAIL"
    }
    result_custom_pass = verifica(5, 10, Le, substitutions=custom_subs)
    result_custom_fail = verifica(15, 10, Le, substitutions=custom_subs)

    # Verify custom substitutions are applied
    assert "CUSTOM_PASS" in result_custom_pass.data
    assert "CUSTOM_FAIL" in result_custom_fail.data

    # Reset
    options.language = None
    set_language("en")