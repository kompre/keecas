"""
Tests for language file structure and consistency.

Ensures all language files have consistent structure and no deprecated entries.
"""

import pytest
import importlib
import pkgutil
from pathlib import Path
from keecas.localization import languages


def get_all_language_modules():
    """Get all language modules from the languages package."""
    language_modules = []
    for importer, modname, ispkg in pkgutil.iter_modules(languages.__path__):
        if modname != '__init__':
            module = importlib.import_module(f'keecas.localization.languages.{modname}')
            language_modules.append((modname, module))
    return language_modules


def test_all_language_files_exist():
    """Test that all expected language files exist."""
    expected_languages = {'en', 'it', 'fr', 'de', 'es', 'pt', 'da', 'nl', 'no', 'sv'}
    language_modules = get_all_language_modules()
    actual_languages = {modname for modname, _ in language_modules}

    assert actual_languages == expected_languages, f"Expected {expected_languages}, got {actual_languages}"


def test_all_language_files_have_translations():
    """Test that all language files have a TRANSLATIONS dictionary."""
    language_modules = get_all_language_modules()

    for modname, module in language_modules:
        assert hasattr(module, 'TRANSLATIONS'), f"Language {modname} missing TRANSLATIONS dictionary"
        assert isinstance(module.TRANSLATIONS, dict), f"Language {modname} TRANSLATIONS is not a dict"
        assert len(module.TRANSLATIONS) > 0, f"Language {modname} TRANSLATIONS is empty"


def test_all_language_files_have_same_keys():
    """Test that all language files have identical keys."""
    language_modules = get_all_language_modules()

    # Get reference keys from English
    en_module = next(module for modname, module in language_modules if modname == 'en')
    reference_keys = set(en_module.TRANSLATIONS.keys())

    for modname, module in language_modules:
        actual_keys = set(module.TRANSLATIONS.keys())
        missing_keys = reference_keys - actual_keys
        extra_keys = actual_keys - reference_keys

        assert not missing_keys, f"Language {modname} missing keys: {missing_keys}"
        assert not extra_keys, f"Language {modname} has extra keys: {extra_keys}"
        assert actual_keys == reference_keys, f"Language {modname} keys don't match reference"


def test_no_deprecated_entries():
    """Test that no language files contain deprecated VERIFICATO entries."""
    language_modules = get_all_language_modules()
    deprecated_keys = {'VERIFICATO', 'NON VERIFICATO'}

    for modname, module in language_modules:
        actual_keys = set(module.TRANSLATIONS.keys())
        found_deprecated = actual_keys & deprecated_keys

        assert not found_deprecated, f"Language {modname} contains deprecated keys: {found_deprecated}"


def test_required_sections_present():
    """Test that all required sections are present in all language files."""
    language_modules = get_all_language_modules()

    # Required keys from each section
    required_sympy_keys = {'for', 'otherwise'}
    required_domain_keys = {'Domain: ', 'Domain on ', 'Range'}
    required_verification_keys = {'VERIFIED', 'NOT_VERIFIED'}
    required_boolean_keys = {'True', 'False'}
    required_additional_keys = {'if', 'then', 'else', 'and', 'or', 'not'}

    all_required_keys = (required_sympy_keys | required_domain_keys |
                        required_verification_keys | required_boolean_keys |
                        required_additional_keys)

    for modname, module in language_modules:
        actual_keys = set(module.TRANSLATIONS.keys())
        missing_keys = all_required_keys - actual_keys

        assert not missing_keys, f"Language {modname} missing required keys: {missing_keys}"


def test_all_translation_values_are_strings():
    """Test that all translation values are non-empty strings."""
    language_modules = get_all_language_modules()

    for modname, module in language_modules:
        for key, value in module.TRANSLATIONS.items():
            assert isinstance(value, str), f"Language {modname} key '{key}' has non-string value: {type(value)}"
            assert value.strip(), f"Language {modname} key '{key}' has empty or whitespace-only value"


def test_language_files_have_proper_structure():
    """Test that language files have proper Python module structure."""
    language_modules = get_all_language_modules()

    for modname, module in language_modules:
        # Check for proper docstring
        assert module.__doc__, f"Language {modname} missing module docstring"
        assert 'translations' in module.__doc__.lower(), f"Language {modname} docstring doesn't mention translations"

        # Check for __all__ export
        assert hasattr(module, '__all__'), f"Language {modname} missing __all__ export"
        assert 'TRANSLATIONS' in module.__all__, f"Language {modname} __all__ doesn't include TRANSLATIONS"


def test_verification_states_consistency():
    """Test that verification state translations are consistent across languages."""
    language_modules = get_all_language_modules()

    for modname, module in language_modules:
        verified = module.TRANSLATIONS['VERIFIED']
        not_verified = module.TRANSLATIONS['NOT_VERIFIED']

        # Check that they're different
        assert verified != not_verified, f"Language {modname} has same translation for VERIFIED and NOT_VERIFIED"

        # Check that they're not just the English defaults (except for English)
        if modname != 'en':
            assert verified != 'VERIFIED', f"Language {modname} VERIFIED not translated"
            assert not_verified != 'NOT VERIFIED', f"Language {modname} NOT_VERIFIED not translated"


def test_language_file_imports():
    """Test that all language files can be imported without errors."""
    language_modules = get_all_language_modules()

    # Just getting the modules above already tests import, but let's be explicit
    for modname, module in language_modules:
        assert module is not None, f"Failed to import language module {modname}"


def test_no_duplicate_values_within_language():
    """Test that each language doesn't have duplicate translations (except where appropriate)."""
    language_modules = get_all_language_modules()

    # Some keys legitimately have the same translation
    allowed_duplicates = {
        ('for', 'for'),  # Some languages use same word for both meanings
        ('otherwise', 'else'),  # These can be the same in some languages
        ('else', 'otherwise'),
    }

    for modname, module in language_modules:
        value_to_keys = {}
        for key, value in module.TRANSLATIONS.items():
            if value in value_to_keys:
                # Check if this is an allowed duplicate
                existing_key = value_to_keys[value]
                if (key, existing_key) not in allowed_duplicates and (existing_key, key) not in allowed_duplicates:
                    pytest.fail(f"Language {modname} has duplicate translation '{value}' for keys '{key}' and '{existing_key}'")
            else:
                value_to_keys[value] = key