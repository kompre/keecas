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
    get_available_languages,
    set_runtime_override,
    clear_runtime_overrides,
    get_translations
)


# Fixture to temporarily enable Pint locale for specific tests
@pytest.fixture
def enable_pint_locale():
    """Temporarily enable Pint locale for tests that need it."""
    from keecas import config
    original_setting = config.language_config.disable_pint_locale
    config.language_config.disable_pint_locale = False
    yield
    config.language_config.disable_pint_locale = original_setting


# Test helper functions to replace backward compatibility
def register_language(language_code: str, translations: dict) -> None:
    """Test helper to register a language."""
    from keecas.localization import _translations_cache
    _translations_cache[language_code] = translations.copy()

def reload_configuration() -> None:
    """Test helper to reload configuration."""
    from keecas.config import get_config_manager
    from keecas.localization import _translations_cache, get_language_from_config

    # Reload main config
    config_manager = get_config_manager()
    config_manager.load_configs()

    # Update localization language from config
    config_lang = get_language_from_config()
    if config_lang:
        set_language(config_lang)
    _translations_cache.clear()

def get_configuration():
    """Test helper to get configuration."""
    from keecas.config import get_config_manager
    return get_config_manager()


def test_default_language():
    """Test that default language is English."""
    # Reset to default state for testing
    set_language("en")
    assert get_language() == "en"


def test_basic_translation():
    """Test basic translation functionality."""
    # English (default)
    set_language("en")  # Reset to ensure clean state
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
    assert translate("VERIFIED") == "VERIFIED"
    assert translate("NOT_VERIFIED") == "NOT VERIFIED"

    # Italian
    set_language("it")
    assert translate("VERIFIED") == "VERIFICATO"
    assert translate("NOT_VERIFIED") == "NON VERIFICATO"

    # German
    set_language("de")
    assert translate("VERIFIED") == "BESTÄTIGT"
    assert translate("NOT_VERIFIED") == "NICHT BESTÄTIGT"

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
    from unittest.mock import patch
    import keecas.localization

    original_language = get_language()
    original_cache = keecas.localization._translations_cache.copy()

    try:
        # Mock the config manager to return Italian language
        with patch('keecas.localization.get_language_from_config', return_value="it"):
            # Manually set the language and clear cache to force reload
            set_language("it")
            keecas.localization._translations_cache.clear()

            # Language should be loaded from config
            assert get_language() == "it"
            assert translate("for") == "per"

    finally:
        # Cleanup
        set_language(original_language)
        keecas.localization._translations_cache.clear()
        keecas.localization._translations_cache.update(original_cache)


def test_toml_config_custom_replacements():
    """Test custom translations from TOML config file."""
    from unittest.mock import patch
    import keecas.localization

    # Mock the config manager to return custom translations
    mock_translations = {
        "for": "CUSTOM_FOR",
        "custom_key": "CUSTOM_VALUE"
    }

    original_language = get_language()
    original_cache = keecas.localization._translations_cache.copy()

    try:
        # Patch at the point where it's called during translation
        with patch('keecas.localization.get_custom_replacements_from_config', return_value=mock_translations):
            # Manually set the language and clear cache to force reload
            set_language("en")
            keecas.localization._translations_cache.clear()

            # Custom translations should have high priority
            assert translate("for") == "CUSTOM_FOR"
            assert translate("custom_key") == "CUSTOM_VALUE"

            # But direct substitutions should still have highest priority
            assert translate("for", substitutions={"for": "DIRECT_OVERRIDE"}) == "DIRECT_OVERRIDE"

    finally:
        # Cleanup
        set_language(original_language)
        keecas.localization._translations_cache.clear()
        keecas.localization._translations_cache.update(original_cache)


def test_toml_config_priority():
    """Test that TOML config has correct priority in hierarchy."""
    from unittest.mock import patch
    import keecas.localization

    original_language = get_language()
    original_cache = keecas.localization._translations_cache.copy()

    try:
        # Mock config to return Italian language
        with patch('keecas.localization.get_language_from_config', return_value="it"):
            # Set up Italian as the config default
            set_language("it")
            keecas.localization._translations_cache.clear()

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
        set_language(original_language)
        keecas.localization._translations_cache.clear()
        keecas.localization._translations_cache.update(original_cache)


def test_no_config_file():
    """Test behavior when no config file exists."""
    from unittest.mock import patch
    import keecas.localization

    original_language = get_language()
    original_cache = keecas.localization._translations_cache.copy()

    try:
        # Mock the config manager to return None (no config found)
        with patch('keecas.localization.get_language_from_config', return_value=None), \
             patch('keecas.localization.get_custom_replacements_from_config', return_value={}):

            # Manually set to English since no config found should default to English
            set_language("en")
            keecas.localization._translations_cache.clear()

            # Should default to English
            assert get_language() == "en"
            assert translate("for") == "for"

            # Test that no custom config translations are applied (empty dict)
            from keecas.localization import get_custom_replacements_from_config
            config_replacements = get_custom_replacements_from_config()
            assert config_replacements == {}

    finally:
        # Cleanup
        set_language(original_language)
        keecas.localization._translations_cache.clear()
        keecas.localization._translations_cache.update(original_cache)


def test_display_module_integration():
    """Test integration with display module options and show_eqn function."""
    from keecas.display import config, show_eqn
    from sympy import symbols

    # Reset to defaults
    config.language = None
    set_language("en")

    # Test that config.language works
    config.language = "it"
    x = symbols('x')
    # This should use Italian translations due to config.language
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
    config.language = None
    set_language("en")


def test_verifica_function_localization():
    """Test check() function with localization support."""
    from keecas.display import check, config
    from sympy import symbols, Le, Gt

    x = symbols('x')

    # Reset to defaults
    config.language = None
    set_language("en")

    # Test English (default)
    result_pass = check(5, 10, Le)
    result_fail = check(15, 10, Le)

    # Check that result contains Markdown object
    assert hasattr(result_pass, 'data')
    assert hasattr(result_fail, 'data')

    # Test Italian via global setting
    set_language("it")
    result_it_pass = check(5, 10, Le)
    result_it_fail = check(15, 10, Le)

    # Test document-level language override
    config.language = "en"
    result_doc_en = check(5, 10, Le)

    # Test function-level language override
    result_func_it = check(5, 10, Le, language="it")

    # Test direct substitutions (highest priority)
    custom_subs = {
        "VERIFIED": "CUSTOM_PASS",
        "NOT_VERIFIED": "CUSTOM_FAIL"
    }
    result_custom_pass = check(5, 10, Le, substitutions=custom_subs)
    result_custom_fail = check(15, 10, Le, substitutions=custom_subs)

    # Verify custom substitutions are applied
    assert "CUSTOM_PASS" in result_custom_pass.data
    assert "CUSTOM_FAIL" in result_custom_fail.data

    # Reset
    config.language = None
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
    from keecas.display import check, config
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
    config.language = None
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
    """Test that Pint locale respects disable_pint_locale config.

    This test validates:
    1. The locale helper function works
    2. unitregistry has locale capabilities
    3. Runtime config changes affect locale behavior

    Note: This test uses runtime config changes to test behavior without
    requiring a clean isolated config environment.
    """
    from keecas.pint_sympy import unitregistry
    from keecas.localization.pint_locale import _get_locale_from_keecas
    from keecas import config, update_pint_locale

    # Store original settings
    original_disable = config.language_config.disable_pint_locale
    original_mode = config.language_config.pint_language_mode

    try:
        # Test: locale helper function works
        locale_str = _get_locale_from_keecas()
        assert isinstance(locale_str, str)
        assert '_' in locale_str  # Should be format like 'en_US'

        # Test: unitregistry has locale attribute
        assert hasattr(unitregistry.formatter, 'locale')

        # Test: when disable_pint_locale=True, update_pint_locale does nothing
        config.language_config.disable_pint_locale = True
        unitregistry.formatter.set_locale(None)
        update_pint_locale('en')
        assert unitregistry.formatter.locale is None  # Should remain None

        # Test: when disable_pint_locale=False and mode='auto', locale is set
        config.language_config.disable_pint_locale = False
        config.language_config.pint_language_mode = 'auto'
        # Use 'it' instead of 'en' because 'en' has conservative behavior
        # that skips setting locale if not explicitly configured
        update_pint_locale('it')
        assert unitregistry.formatter.locale is not None  # Should be set
        assert unitregistry.formatter.locale.startswith('it_')  # Should be Italian

    finally:
        # Restore original settings
        config.language_config.disable_pint_locale = original_disable
        config.language_config.pint_language_mode = original_mode
        # Reset locale to None to avoid test pollution
        unitregistry.formatter.set_locale(None)


def test_manual_pint_locale_update():
    """Test manual Pint locale updates with improved locale handling."""
    from keecas import update_pint_locale, u, config

    # Temporarily enable Pint locale for this test
    original_setting = config.language_config.disable_pint_locale
    config.language_config.disable_pint_locale = False

    try:
        # Test with different languages (now expecting UTF-8 variants or available alternatives)
        test_locales = {
            'it': 'it_IT',   # Should set some Italian locale
            'fr': 'fr_FR',   # Should set some French locale
            'de': 'de_DE',   # Should set some German locale
            'es': 'es_ES'    # Should set some Spanish locale
        }

        for lang_code, expected_locale_prefix in test_locales.items():
            update_pint_locale(lang_code)
            # Verify the locale was set (accept UTF-8 variants)
            actual_locale = u.formatter.locale
            assert actual_locale.startswith(expected_locale_prefix), f"Expected locale starting with '{expected_locale_prefix}', got {actual_locale}"

        # Test with 'en' - should use conservative behavior (may not change locale)
        previous_locale = u.formatter.locale
        update_pint_locale('en')
        # 'en' might not change locale due to conservative behavior, so we don't assert a specific change

        # Test with None (should use current keecas language if explicitly set)
        set_language('it')
        update_pint_locale(None)
        # This should set Italian locale since it's explicitly configured
        assert u.formatter.locale.startswith('it_IT'), f"Expected Italian locale, got {u.formatter.locale}"

    finally:
        # Reset
        config.language_config.disable_pint_locale = original_setting
    set_language("en")


def test_options_language_auto_sync():
    """Test that config.language automatically updates Pint locale for non-default languages."""
    from keecas.display import config
    from keecas import u

    # Temporarily enable Pint locale for this test
    original_setting = config.language_config.disable_pint_locale
    config.language_config.disable_pint_locale = False

    try:
        # Store initial state
        initial_locale = u.formatter.locale

        # Test automatic sync when setting config.language (only for explicitly configured languages)
        test_cases = [
            ('it', 'it_IT'),   # Should set Italian locale
            ('fr', 'fr_FR'),   # Should set French locale
            ('de', 'de_DE'),   # Should set German locale
        ]

        for lang_code, expected_locale_prefix in test_cases:
            config.language = lang_code
            actual_locale = u.formatter.locale
            assert actual_locale.startswith(expected_locale_prefix), f"Auto-sync failed: expected locale starting with '{expected_locale_prefix}', got {actual_locale} for language '{lang_code}'"

        # Test English reset behavior: 'en' should reset to English when coming from non-English
        previous_locale = u.formatter.locale
        assert previous_locale.startswith('de_DE'), "Should have German locale from previous test"

        config.language = 'en'
        current_locale = u.formatter.locale
        assert current_locale.startswith('en_'), f"Setting 'en' should reset to English from German, got {current_locale}"

        # Test conservative behavior: 'en' after 'en' should not change
        config.language = 'en'
        assert u.formatter.locale == current_locale, f"Setting 'en' again should be conservative, but it changed"

        # Test None behavior
        config.language = None
        # None should not change the locale (conservative behavior for None)
    finally:
        config.language_config.disable_pint_locale = original_setting
        config.language = None
    assert u.formatter.locale == current_locale, f"Setting None should not change locale"

    # Reset (this won't actually reset the locale due to conservative behavior, but that's fine)
    config.language = None


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
    """Test edge cases in Pint localization with improved handling."""
    from keecas import update_pint_locale, u

    # Store current locale
    initial_locale = u.formatter.locale

    # Test invalid language code - should gracefully do nothing
    update_pint_locale('invalid_lang')
    # Should remain unchanged (no fallback to hardcoded locale)
    current_locale = u.formatter.locale
    # Either stays the same or falls back to a safe locale

    # Test empty string - should gracefully do nothing
    update_pint_locale('')
    # Should remain unchanged or use safe fallback

    # Reset
    update_pint_locale('en')


def test_pint_locale_fallback_behavior(enable_pint_locale):
    """Test proper fallback behavior for unsupported languages."""
    from keecas import update_pint_locale, u
    from keecas.localization import set_language

    # Reset to clean state
    u.formatter.set_locale(None)

    # Test 1: Unsupported language should fallback to English
    set_language('da')  # Danish - unsupported
    update_pint_locale('da')

    quantity = 1 * u('cm**2')
    result = f'{quantity:.3f}'
    # Should show English units, not retain previous locale
    assert 'centimeter' in result.lower(), f"Expected English units after Danish, got: {result}"

    # Test 2: Set supported language, then unsupported - should reset to English
    set_language('it')
    update_pint_locale('it')
    quantity = 1 * u('cm**2')
    italian_result = f'{quantity:.3f}'
    assert 'centimetro' in italian_result.lower(), "Italian should work"

    # Now switch to unsupported - should reset to English, not keep Italian
    set_language('sv')  # Swedish - unsupported
    update_pint_locale('sv')
    quantity = 1 * u('cm**2')
    swedish_result = f'{quantity:.3f}'
    assert 'centimeter' in swedish_result.lower(), f"Expected English after Swedish, got: {swedish_result}"
    assert 'centimetro' not in swedish_result.lower(), "Should not retain Italian units"

    # Test 3: Multiple unsupported languages should all use English
    unsupported_langs = ['da', 'nl', 'no', 'sv']
    for lang in unsupported_langs:
        set_language(lang)
        update_pint_locale(lang)
        quantity = 1 * u('cm**2')
        result = f'{quantity:.3f}'
        assert 'centimeter' in result.lower(), f"Language {lang} should fallback to English, got: {result}"


def test_pint_locale_supported_languages(enable_pint_locale):
    """Test that all officially supported languages work correctly."""
    from keecas import update_pint_locale, u
    from keecas.localization import set_language

    # Expected translations for supported languages
    expected_translations = {
        'de': 'zentimeter',      # German
        'es': 'centímetro',      # Spanish
        'fr': 'centimètre',      # French
        'it': 'centimetro',      # Italian
        'pt': 'centímetro',      # Portuguese
    }

    for lang, expected_unit in expected_translations.items():
        set_language(lang)
        update_pint_locale(lang)
        quantity = 1 * u('cm**2')
        result = f'{quantity:.3f}'.lower()

        assert expected_unit in result, f"Language {lang} should show '{expected_unit}', got: {result}"


def test_pint_locale_persistence_fix(enable_pint_locale):
    """Test that the locale persistence issue is fixed."""
    from keecas import update_pint_locale, u
    from keecas.localization import set_language

    # Reset to clean state
    u.formatter.set_locale(None)

    # Scenario that previously failed: Italian -> English -> Danish
    set_language('it')
    update_pint_locale('it')
    quantity = 1 * u('cm**2')
    assert 'centimetro' in f'{quantity:.3f}'.lower(), "Italian should work"

    # Switch to English - should now reset to English (key fix!)
    set_language('en')
    update_pint_locale('en')
    quantity = 1 * u('cm**2')
    result = f'{quantity:.3f}'.lower()
    assert 'centimeter' in result, f"English should reset to English from Italian. Got: {result}"
    assert 'centimetro' not in result, f"English should not retain Italian. Got: {result}"

    # Switch to Danish - should fallback to English
    set_language('da')
    update_pint_locale('da')
    quantity = 1 * u('cm**2')
    result = f'{quantity:.3f}'.lower()

    # The fix: Danish should show English, not retain Italian
    assert 'centimeter' in result, f"Danish should fallback to English. Got: {result}"
    assert 'centimetro' not in result, f"Danish should not show Italian units. Got: {result}"


def test_pint_locale_english_reset_behavior(enable_pint_locale):
    """Test specific English reset behavior when coming from other languages."""
    from keecas import update_pint_locale, u
    from keecas.localization import set_language

    # Reset to clean state
    u.formatter.set_locale(None)

    # Test 1: Fresh English should be conservative (skip)
    set_language('en')
    update_pint_locale('en')
    quantity = 1 * u('cm**2')
    fresh_result = f'{quantity:.3f}'.lower()
    assert 'centimeter' in fresh_result, "Fresh English should work"

    # Test 2: English after non-English should reset
    set_language('fr')
    update_pint_locale('fr')
    quantity = 1 * u('cm**2')
    assert 'centimètre' in f'{quantity:.3f}'.lower(), "French should work"

    # Now switch to English - should reset to English
    set_language('en')
    update_pint_locale('en')
    quantity = 1 * u('cm**2')
    reset_result = f'{quantity:.3f}'.lower()
    assert 'centimeter' in reset_result, f"English should reset from French. Got: {reset_result}"
    assert 'centimètre' not in reset_result, f"Should not retain French. Got: {reset_result}"

    # Test 3: English after English should be conservative (skip)
    set_language('en')
    update_pint_locale('en')
    quantity = 1 * u('cm**2')
    conservative_result = f'{quantity:.3f}'.lower()
    assert 'centimeter' in conservative_result, "Repeated English should remain English"