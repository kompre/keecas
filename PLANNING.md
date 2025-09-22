# Planning Notes - Keecas Development

**Date**: 2025-09-22
**Session**: Planning and execution workflow setup

## Workflow
1. **Planning**: Add brief notes below
2. **Expansion**: Claude expands selected items into detailed plans; ask question for clarifications
3. **Approval**: Review and approve/modify plans
4. **Execution**: Claude implements approved plans with TodoWrite tracking

---

## Ideas/Tasks to Tackle

This section is written by the user.

### refactor localization module

I feel the localization module is overblown and overcomplicated, even if it is working. I can't follow what is going on. 

Our localization consist in a simple dict that maps terms to be replaced. Those terms needs to be set at import, or when a different language is set in the notebook. Even the pint formatter should be set only when we change the language, because if the user decide to set directly the pint formatter during usage, then it would be jarring if the the language does not respect the user setting. For example this SHOULD NOT HAPPEN:

- user set `u.formatter.set_locale = 'fr_FR'` -> pint print in French
- user set `keecas.config.language = 'en'` -> pint print in English

In the above example the user has made a distinct decision on what pint language should be, we should not override to avoid side effect.

#### Automatically detect of pint language

We should try to automatically detect when pint language is changed by the user:

- add config for pint_language_mode (auto|manual)
- if pint is already imported, then set pint_language mode to manual and not keep in sync with keecas language
- if pint is not imported, then set pint_language mode to auto and keep in sync with keecas language; now when user set language in the document manually, we determine if pint is in sync with the previous language and:
  - if not, then set pint_language mode to manual, do not sync anymore
  - if yes then change pint_language in sync with keecas
  
(UNLESS you have a better idea on how to detect manual input by the user for a different package.)

### templating the check function

The user should be able to provide a latex template for the check function, in substitution of the default one. Maybe I want a green box with a checkmark and a red box with an X.

### launch jupyter server with keecas templates

If possible I would like to launch the jupyter server with an already opened notebook, but without creating a saved file. I would prefer a temporary file, that the user should decide if it want to be saved or not. Many times a user need something on the fly, without tha hassle of dealing with file management. If it decide to actually save the work, it can always save it as a new file.

As a side, lower priority we should look on providing intellisense/autocomplete, otherwise it will be a bit of a chore to use. This feature is to implement only if it does not bloat our package. Having the ability to launch a jupyter server is a nice to have, not a must.

The templates should be shipped with the package (we're using uv_build).

---

## Expanded Plans (Ready for Execution)

This section is written by Claude.

User comments and and answers will be added here inside comment blocks <!-- comment by user -->


### 1. Localization Module Refactor - DETAILED PLAN

**Problem Analysis:**
Current localization system is overly complex with:
- Multiple managers and config layers
- Complex pint locale synchronization
- Hard to follow hierarchical priority system
- Automatic pint override that conflicts with user intent

**Proposed Simplified Architecture:**

#### Core Simplification
1. **Single Translation Dict**: Replace manager hierarchy with simple `Dict[str, str]`
2. **Import-time Setup**: Set translations once at import or language change
3. **Pint Mode Detection**: Smart detection of user vs automatic pint changes

#### Implementation Plan

**Phase 1: Simplify Translation System**
- Replace `LocalizationManager` with simple translation functions
- Create `get_translations(language: str) -> Dict[str, str]` that loads from separate language files
- Keep language files as separate modules, load on-demand when language changes
- Preserve hierarchy: config.toml → runtime overrides → reset capability
- Add reset function to revert user modifications back to config defaults
- Rename "custom_translations" to "custom_replacements" (pattern → replacement pairs)

**Phase 2: Smart Pint Synchronization**
- Add `pint_language_mode` config option: `'auto' | 'manual'`
- Detect if pint was imported before keecas: set mode to `'manual'`
- Before changing keecas language: check pint locale vs current keecas language
- If discrepancy found: user made manual change → set mode to `'manual'`
- Only sync pint when mode is `'auto'` and language change came from keecas

**Phase 3: Clean Integration Points**
- Update `config.language` setter (migrate from `options.language`)
- Support breaking changes for major version upgrade
- Update `display.py` to use simple dict lookups
- Remove complex manager hierarchy while preserving functionality

#### Files to Modify
- `src/keecas/localization/__init__.py` - simple functions, keep separate language files
- `src/keecas/localization/manager.py` - delete or drastically simplify
- `src/keecas/pint_sympy.py` - add pint mode detection logic
- `src/keecas/config.py` - add `pint_language_mode`, migrate from options
- `src/keecas/display.py` - update to simple dict lookups

#### Clarifications Resolved
1. ✅ Keep custom replacements (pattern → replacement pairs) from config files
2. ✅ Keep language files as separate modules, load on-demand
3. ✅ Detect pint manual changes by comparing locales before keecas language change

**Estimated Complexity:** Medium - affects core localization but architecture is straightforward

---

## Completed This Session

### ✅ Localization Module Refactor - COMPLETED

**All phases successfully implemented:**

✅ **Phase 1: Simplified Translation System**
- Replaced `LocalizationManager` with simple functions in `__init__.py`
- Created `get_translations()` for complete dictionary access
- Maintained separate language files, load on-demand
- Implemented config hierarchy: runtime → config → language file
- Added `set_runtime_override()` and `reset_to_config()` for user control
- Renamed "custom_translations" to "custom_replacements" with backward compatibility

✅ **Phase 2: Smart Pint Synchronization**
- Added `pint_language_mode` config option: `'auto' | 'manual'`
- Implemented detection of pint imported before keecas → set to 'manual'
- Added locale comparison logic to detect user manual changes
- Only sync pint locale when mode is 'auto' and change comes from keecas
- Prevents jarring override of user's explicit pint settings

✅ **Phase 3: Clean Integration Points**
- Migrated primary interface from `options` to `config` (major version upgrade)
- Updated `display.py` to use new localization functions
- Maintained backward compatibility with `options` alias
- Updated `__init__.py` to export `config` as primary interface

✅ **Tests Updated and Passing**
- All 27 localization tests pass
- All 62 total tests pass
- Added backward compatibility functions for test compatibility
- Verified functionality: translations, runtime overrides, config hierarchy, pint detection

**Key Benefits Achieved:**
- ❌ **Eliminated complex manager hierarchy** - much simpler to understand
- ✅ **Smart pint behavior** - respects user's manual locale changes
- ✅ **Runtime control** - users can override/reset translations in notebooks
- ✅ **Backward compatibility** - existing code continues to work
- ✅ **Config hierarchy preserved** - still supports TOML custom replacements
- ✅ **On-demand loading** - language files loaded only when needed

The localization system is now much simpler and more predictable!

### ✅ Localization Cleanup - COMPLETED

**Removed all unnecessary backward compatibility code:**

✅ **Deleted manager.py** - Entire 56-line backward compatibility wrapper file
✅ **Cleaned __init__.py** - Removed 3 compatibility functions and unused variables
✅ **Cleaned config.py** - Removed support for 5 legacy config section names
✅ **Unified interface** - Removed `options` alias, only `config` remains
✅ **Removed verifica alias** - Only `check` function remains
✅ **Updated tests** - All 62 tests pass with cleaned imports

**Code Reduction:**
- **~200 lines removed** across multiple files
- **1 entire file deleted** (manager.py)
- **Single interface** - no more confusion between options/config or check/verifica
- **Cleaner imports** - direct usage of current API

**Final API:**
```python
# Configuration
keecas.config  # Only interface (no options)

# Functions
keecas.check()  # Only function (no verifica)

# Localization
keecas.localization.translate()
keecas.localization.get_translations()
keecas.localization.set_language()
# etc.
```

The codebase is now much cleaner and focused on the current API!

### ✅ Configuration System Unification - COMPLETED

**Eliminated duplicate configuration systems:**

✅ **Removed LocalizationConfig wrapper** - Deleted separate config system in localization module
✅ **Updated localization to use main ConfigManager** - Direct delegation instead of wrapper
✅ **Fixed config file paths** - LocalizationConfig was using wrong paths (%APPDATA% vs %USERPROFILE%)
✅ **Cleaned up test mocking** - Removed `_MockConfig` class and updated test helpers
✅ **Updated all imports** - Tests now import directly from main config or localization module

**Results:**
- **Single config system** - Localization now properly integrates with main ConfigManager
- **Correct file paths** - Uses proper `%USERPROFILE%/.keecas` path hierarchy
- **All 62 tests passing** - No regressions after config unification
- **Cleaner architecture** - No more orphaned config systems using wrong paths

### ✅ Project Metadata & Dynamic URLs - COMPLETED

**Added proper project metadata and dynamic GitHub URL handling:**

✅ **Added Project URLs to pyproject.toml**:
```toml
[project.urls]
Homepage = "https://github.com/kompre/keecas"
Repository = "https://github.com/kompre/keecas"
Issues = "https://github.com/kompre/keecas/issues"
```

✅ **Made GitHub URL dynamic** - Warning messages now read from project metadata instead of hardcoded strings
✅ **Added robust fallbacks** - Multiple fallback strategies ensure users always get working URLs
✅ **Verified functionality** - Dynamic URL retrieval works correctly in warnings

**Benefits:**
- **Centralized URL management** - All URLs managed in pyproject.toml
- **Standards compliance** - Follows Python packaging best practices
- **Automatic updates** - Warning messages update when repository URLs change

### ✅ Language Files Cleanup & Testing - COMPLETED

**Comprehensive cleanup and validation of all language translation files:**

✅ **Removed deprecated entries** - Eliminated unused `VERIFICATO` and `NON VERIFICATO` backward compatibility entries from 9 language files
✅ **Standardized structure** - All 10 language files now have identical 15-key structure
✅ **Added missing sections** - Added "Additional terms" section to English file for consistency
✅ **Comprehensive testing** - Created `test_language_structure.py` with 10 automated tests:
- All language files exist and can be imported
- All files have identical key structure
- No deprecated entries remain
- All required sections present
- All translation values are valid strings
- Proper Python module structure
- Verification states consistency
- No inappropriate duplicate values

✅ **Updated existing tests** - Fixed `test_verification_terms()` to remove dependency on deprecated keys
✅ **Full validation** - All 72 tests pass (added 10 new structure validation tests)

**Results:**
- **Clean, consistent language files** - No deprecated content, standardized structure
- **Automated validation** - Prevents future inconsistencies with comprehensive test suite
- **Verified integrity** - All 10 languages have identical 15-key structure
- **Future-proof** - Tests ensure structural consistency for new language additions

**Final Language File Structure:**
```python
TRANSLATIONS = {
    # SymPy LaTeX words (2 keys)
    "for": "...", "otherwise": "...",

    # Domain/Range labels (3 keys)
    "Domain: ": "...", "Domain on ": "...", "Range": "...",

    # Boolean verification states (2 keys)
    "VERIFIED": "...", "NOT_VERIFIED": "...",

    # Common mathematical terms (2 keys)
    "True": "...", "False": "...",

    # Additional terms (6 keys)
    "if": "...", "then": "...", "else": "...",
    "and": "...", "or": "...", "not": "..."
}
```

The localization system is now fully integrated, clean, and properly tested!
