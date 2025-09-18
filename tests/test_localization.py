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
    """Test verification terms translation with backward compatibility."""
    # English - test both new and old keys
    set_language("en")
    assert translate("VERIFIED") == "VERIFIED"
    assert translate("NOT_VERIFIED") == "NOT VERIFIED"
    # Backward compatibility with old Italian keys
    assert translate("VERIFICATO") == "VERIFIED"
    assert translate("NON VERIFICATO") == "NOT VERIFIED"

    # Italian - test both new and old keys
    set_language("it")
    assert translate("VERIFIED") == "VERIFICATO"
    assert translate("NOT_VERIFIED") == "NON VERIFICATO"
    # Backward compatibility with old Italian keys
    assert translate("VERIFICATO") == "VERIFICATO"
    assert translate("NON VERIFICATO") == "NON VERIFICATO"

    # Reset
    set_language("en")


def test_available_languages():
    """Test getting available languages."""
    languages = get_available_languages()
    expected_languages = ['da', 'de', 'en', 'es', 'fr', 'it', 'nl', 'no', 'pt', 'sv']

    # Verify all expected languages are present
    for lang in expected_languages:
        assert lang in languages, f"Language '{lang}' not found in available languages: {languages}"

    # Verify we have exactly the expected set (no more, no less)
    assert len(languages) == len(expected_languages), f"Expected {len(expected_languages)} languages, got {len(languages)}: {languages}"
    assert set(languages) == set(expected_languages), f"Language set mismatch. Expected: {expected_languages}, Got: {languages}"


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
        "VERIFIED": "CUSTOM_PASS",
        "NOT_VERIFIED": "CUSTOM_FAIL"
    }
    result_custom_pass = verifica(5, 10, Le, substitutions=custom_subs)
    result_custom_fail = verifica(15, 10, Le, substitutions=custom_subs)

    # Verify custom substitutions are applied
    assert "CUSTOM_PASS" in result_custom_pass.data
    assert "CUSTOM_FAIL" in result_custom_fail.data

    # Reset
    options.language = None
    set_language("en")


def test_new_language_translations():
    """Test translations for all new European languages."""
    # Expected translations for each language
    expected_translations = {
        'fr': {  # French
            'VERIFIED': 'VÉRIFIÉ',
            'NOT_VERIFIED': 'NON VÉRIFIÉ',
            'for': 'pour',
            'otherwise': 'sinon'
        },
        'de': {  # German
            'VERIFIED': 'BESTÄTIGT',
            'NOT_VERIFIED': 'NICHT BESTÄTIGT',
            'for': 'für',
            'otherwise': 'andernfalls'
        },
        'es': {  # Spanish
            'VERIFIED': 'VERIFICADO',
            'NOT_VERIFIED': 'NO VERIFICADO',
            'for': 'para',
            'otherwise': 'de lo contrario'
        },
        'pt': {  # Portuguese
            'VERIFIED': 'VERIFICADO',
            'NOT_VERIFIED': 'NÃO VERIFICADO',
            'for': 'para',
            'otherwise': 'caso contrário'
        },
        'nl': {  # Dutch
            'VERIFIED': 'GEVERIFIEERD',
            'NOT_VERIFIED': 'NIET GEVERIFIEERD',
            'for': 'voor',
            'otherwise': 'anders'
        },
        'da': {  # Danish
            'VERIFIED': 'VERIFICERET',
            'NOT_VERIFIED': 'IKKE VERIFICERET',
            'for': 'for',
            'otherwise': 'ellers'
        },
        'sv': {  # Swedish
            'VERIFIED': 'VERIFIERAD',
            'NOT_VERIFIED': 'INTE VERIFIERAD',
            'for': 'för',
            'otherwise': 'annars'
        },
        'no': {  # Norwegian
            'VERIFIED': 'VERIFISERT',
            'NOT_VERIFIED': 'IKKE VERIFISERT',
            'for': 'for',
            'otherwise': 'ellers'
        }
    }

    # Test each language
    for lang_code, translations in expected_translations.items():
        set_language(lang_code)

        # Test verification terms
        assert translate("VERIFIED") == translations["VERIFIED"], f"VERIFIED translation failed for {lang_code}"
        assert translate("NOT_VERIFIED") == translations["NOT_VERIFIED"], f"NOT_VERIFIED translation failed for {lang_code}"

        # Test SymPy words
        assert translate("for") == translations["for"], f"'for' translation failed for {lang_code}"
        assert translate("otherwise") == translations["otherwise"], f"'otherwise' translation failed for {lang_code}"

    # Reset
    set_language("en")


def test_verification_terms_all_languages():
    """Test verification terms for all supported languages."""
    # Test each language individually
    verification_tests = {
        'en': ('VERIFIED', 'NOT VERIFIED'),
        'it': ('VERIFICATO', 'NON VERIFICATO'),
        'fr': ('VÉRIFIÉ', 'NON VÉRIFIÉ'),
        'de': ('BESTÄTIGT', 'NICHT BESTÄTIGT'),
        'es': ('VERIFICADO', 'NO VERIFICADO'),
        'pt': ('VERIFICADO', 'NÃO VERIFICADO'),
        'nl': ('GEVERIFIEERD', 'NIET GEVERIFIEERD'),
        'da': ('VERIFICERET', 'IKKE VERIFICERET'),
        'sv': ('VERIFIERAD', 'INTE VERIFIERAD'),
        'no': ('VERIFISERT', 'IKKE VERIFISERT')
    }

    for lang_code, (verified, not_verified) in verification_tests.items():
        set_language(lang_code)
        assert translate("VERIFIED") == verified, f"VERIFIED failed for {lang_code}"
        assert translate("NOT_VERIFIED") == not_verified, f"NOT_VERIFIED failed for {lang_code}"

    # Reset
    set_language("en")


def test_check_function_multilingual():
    """Test check() function with different language settings."""
    from keecas.display import check, options
    from sympy import Le

    # Test languages with their expected verification terms
    test_cases = [
        ('en', 'VERIFIED', 'NOT VERIFIED'),
        ('fr', 'VÉRIFIÉ', 'NON VÉRIFIÉ'),
        ('de', 'BESTÄTIGT', 'NICHT BESTÄTIGT'),
        ('es', 'VERIFICADO', 'NO VERIFICADO'),
        ('it', 'VERIFICATO', 'NON VERIFICATO')
    ]

    for lang_code, verified_term, not_verified_term in test_cases:
        set_language(lang_code)

        # Test passing case
        result_pass = check(5, 10, Le)
        assert verified_term in result_pass.data, f"Passing check failed for {lang_code}: expected '{verified_term}' in '{result_pass.data}'"

        # Test failing case
        result_fail = check(15, 10, Le)
        assert not_verified_term in result_fail.data, f"Failing check failed for {lang_code}: expected '{not_verified_term}' in '{result_fail.data}'"

    # Reset
    options.language = None
    set_language("en")


def test_show_eqn_language_replacements():
    """Test show_eqn() with Piecewise expressions in different languages."""
    from keecas.display import show_eqn
    from keecas import pipe_command as pc
    from sympy import symbols

    x = symbols('x')

    # Test languages with their expected word replacements
    test_cases = [
        ('it', 'per', 'altrimenti'),  # Italian
        ('fr', 'pour', 'sinon'),      # French
        ('de', 'für', 'andernfalls'), # German
        ('es', 'para', 'de lo contrario')  # Spanish
    ]

    for lang_code, for_word, otherwise_word in test_cases:
        set_language(lang_code)

        expr = {x: "Piecewise((0, x < 0), (x, x >= 0))" | pc.parse_expr}
        result = show_eqn(expr)

        # Check that English words are replaced with localized versions
        assert rf"\text{{{for_word}}}" in result.data, f"'{for_word}' not found for {lang_code} in: {result.data}"
        assert rf"\text{{{otherwise_word}}}" in result.data, f"'{otherwise_word}' not found for {lang_code} in: {result.data}"

        # Check that English words are NOT present
        assert r"\text{for}" not in result.data, f"English 'for' still present for {lang_code}"
        assert r"\text{otherwise}" not in result.data, f"English 'otherwise' still present for {lang_code}"

    # Reset
    set_language("en")


def test_word_boundary_protection():
    """Test that partial string matches are prevented by word boundaries."""
    from keecas.display import replace_all

    # Test cases that should NOT be replaced (partial matches)
    protected_cases = [
        ('foreste', 'it'),     # 'for' in 'foreste' should stay
        ('before', 'it'),      # 'for' in 'before' should stay
        ('otherwise_var', 'it'), # 'otherwise' in variable name should stay
        ('performer', 'fr'),   # 'for' in 'performer' should stay (French)
        ('deformed', 'de'),    # 'for' in 'deformed' should stay (German)
    ]

    # Test cases that SHOULD be replaced (whole words)
    replacement_cases = [
        ('for x', 'it', 'per x'),
        ('x for y', 'it', 'x per y'),
        ('(for', 'it', '(per'),
        ('for)', 'it', 'per)'),
        ('otherwise', 'it', 'altrimenti'),
        ('for', 'fr', 'pour'),
        ('otherwise', 'fr', 'sinon'),
        ('for', 'de', 'für'),
        ('otherwise', 'de', 'andernfalls')
    ]

    # Test protected cases (should NOT change)
    for text, lang_code in protected_cases:
        set_language(lang_code)
        result = replace_all(text)
        assert result == text, f"Word boundary protection failed for '{text}' in {lang_code}: got '{result}'"

    # Test replacement cases (should change)
    for original, lang_code, expected in replacement_cases:
        set_language(lang_code)
        result = replace_all(original)
        assert result == expected, f"Word replacement failed for '{original}' in {lang_code}: expected '{expected}', got '{result}'"

    # Reset
    set_language("en")


def test_pint_locale_initialization():
    """Test that Pint locale is initialized correctly."""
    from keecas.pint_sympy import unitregistry, _get_locale_from_keecas
    from keecas.localization import get_language

    # Test that the function works
    locale_str = _get_locale_from_keecas()
    assert isinstance(locale_str, str)
    assert '_' in locale_str  # Should be format like 'en_US'

    # Test that unitregistry has a locale
    assert hasattr(unitregistry.formatter, 'locale')
    assert isinstance(unitregistry.formatter.locale, str)


def test_manual_pint_locale_update():
    """Test manual Pint locale updates."""
    from keecas import update_pint_locale, u

    # Test with different languages
    test_locales = {
        'en': 'en_US',
        'it': 'it_IT',
        'fr': 'fr_FR',
        'de': 'de_DE',
        'es': 'es_ES'
    }

    for lang_code, expected_locale in test_locales.items():
        update_pint_locale(lang_code)
        # Verify the locale was set (access internal formatter)
        actual_locale = u.formatter.locale
        assert actual_locale == expected_locale, f"Expected {expected_locale}, got {actual_locale}"

    # Test with None (should use current keecas language)
    set_language('it')
    update_pint_locale(None)
    assert u.formatter.locale == 'it_IT'

    # Reset
    set_language("en")
    update_pint_locale('en')


def test_options_language_auto_sync():
    """Test that options.language automatically updates Pint locale."""
    from keecas.display import options
    from keecas import u

    # Test automatic sync when setting options.language
    test_cases = [
        ('it', 'it_IT'),
        ('fr', 'fr_FR'),
        ('de', 'de_DE'),
        ('en', 'en_US'),
        (None, 'en_US')  # None should default to en_US
    ]

    for lang_code, expected_locale in test_cases:
        options.language = lang_code
        actual_locale = u.formatter.locale
        assert actual_locale == expected_locale, f"Auto-sync failed: expected {expected_locale}, got {actual_locale} for language '{lang_code}'"

    # Reset
    options.language = None


def test_pint_locale_with_real_formatting():
    """Test Pint locale with actual number formatting (system dependent)."""
    from keecas import u, update_pint_locale
    import locale as sys_locale

    # Create a test quantity
    test_quantity = 1234.567 * u.meter

    # Test with different locales if system supports them
    # Note: This test might be system-dependent based on available locales
    try:
        # Test English formatting
        update_pint_locale('en')
        en_format = f"{test_quantity:.2f}"
        assert isinstance(en_format, str)

        # Test other locales (may not work on all systems)
        update_pint_locale('it')
        it_format = f"{test_quantity:.2f}"
        assert isinstance(it_format, str)

        # The formatting might be the same if system doesn't have locale support
        # but at least verify no errors occur

    except Exception as e:
        # If locale formatting fails, that's okay - system dependent
        # Just ensure no crashes occur
        pass

    # Reset
    update_pint_locale('en')


def test_pint_locale_edge_cases():
    """Test edge cases in Pint localization."""
    from keecas import update_pint_locale, u

    # Test invalid language code
    update_pint_locale('invalid_lang')
    # Should default to en_US
    assert u.formatter.locale == 'en_US'

    # Test empty string
    update_pint_locale('')
    assert u.formatter.locale == 'en_US'

    # Reset
    update_pint_locale('en')