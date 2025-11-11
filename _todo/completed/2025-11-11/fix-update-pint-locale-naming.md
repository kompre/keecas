# Task: Fix `update_pint_locale` Function Naming Conflict

**Status**: Completed
**Created**: 2025-11-11
**Completed**: 2025-11-11
**Priority**: High (Fixes incorrect test implementation)
**Branch**: `fix/update-pint-locale-naming` (merged to dev via PR #46)
**Additional PR**: #47 (test fixes after merge conflict)

## Original Objective

Fix the naming conflict where two functions share the same name `update_pint_locale`, causing confusion between the public API wrapper and internal implementation. Tests were incorrectly modified to call the internal function directly instead of using the public wrapper.

## Problem Analysis

### Current Situation

Two functions named `update_pint_locale` exist:

1. **Public Wrapper** (`src/keecas/pint_sympy.py:49-117`)
   - Signature: `update_pint_locale(language: str | None = None, verbose: bool = False)`
   - Purpose: User-facing API for updating Pint locale
   - Does NOT require `unitregistry` parameter (uses global instance)
   - Documented in CLAUDE.md and docstrings
   - Intended for direct user consumption

2. **Internal Implementation** (`src/keecas/localization/pint_locale.py:247`)
   - Signature: `update_pint_locale(unitregistry: Any, language: str | None = None, verbose: bool = False)`
   - Purpose: Actual implementation with complex locale logic
   - Requires explicit `unitregistry` parameter
   - Called by wrapper and previously by tests

### The Mistake

When `update_pint_locale` was removed from `__init__.py` exports, tests started failing. The "fix" incorrectly:
- Changed all test imports to use the **internal implementation** from `localization.pint_locale`
- Modified all test calls to pass `unitregistry` as first parameter
- Made tests use a different API than what users would use

### Correct Behavior

Tests should:
- Import the **public wrapper** from `pint_sympy` (same as users)
- Call without `unitregistry` parameter (simple API)
- Test the same interface that's documented and exposed to users

## Proposed Solution

### 1. Rename Internal Function

**File**: `src/keecas/localization/pint_locale.py:247`

Rename the internal implementation to clearly mark it as internal:

```python
# FROM:
def update_pint_locale(
    unitregistry: Any,
    language: str | None = None,
    verbose: bool = False,
) -> None:

# TO:
def _update_pint_locale_impl(
    unitregistry: Any,
    language: str | None = None,
    verbose: bool = False,
) -> None:
```

**Rationale**:
- `_impl` suffix follows Python convention for implementation details
- Leading underscore signals "internal, do not use directly"
- Prevents namespace collision with public API
- Makes IDE autocomplete suggest public API, not internal

Update docstring to indicate internal status:
```python
"""Internal implementation of pint locale update with smart mode detection.

This is the internal implementation. Users should call the public wrapper
update_pint_locale() from keecas.pint_sympy instead.

Args:
    unitregistry: The Pint UnitRegistry instance
    language: Two-letter language code. If None, gets from keecas config
    verbose: If True, print debugging information about locale changes

Notes:
    - Automatically switches to manual mode if user intervention is detected
    - Respects disable_pint_locale configuration setting
    - Handles fallback scenarios for unsupported languages
"""
```

### 2. Update Wrapper Import and Call

**File**: `src/keecas/pint_sympy.py`

Update the wrapper to call the renamed internal function:

```python
# Line 115 - Update import:
# FROM:
from .localization.pint_locale import update_pint_locale as _update_pint_locale

# TO:
from .localization.pint_locale import _update_pint_locale_impl

# Line 117 - Update call:
# FROM:
_update_pint_locale(unitregistry, language, verbose)

# TO:
_update_pint_locale_impl(unitregistry, language, verbose)
```

Fix docstring example (line 71):
```python
# FROM:
from keecas.localization.pint_locale import update_pint_locale

# TO:
from keecas.pint_sympy import update_pint_locale
```

### 3. Revert Test Changes

**File**: `tests/test_localization.py`

Revert all test modifications to use the public wrapper:

1. **Change all imports** (lines 613, 655, 754, 787, 808, 855, 881, 915):
   ```python
   # FROM:
   from keecas.localization.pint_locale import update_pint_locale

   # TO:
   from keecas.pint_sympy import update_pint_locale
   ```

2. **Remove `unitregistry` parameter from all calls**:
   - Line 632: `update_pint_locale("en")` instead of `update_pint_locale(unitregistry, "en")`
   - Line 640: `update_pint_locale("it")` instead of `update_pint_locale(unitregistry, "it")`
   - Line 671: `update_pint_locale(lang_code)` instead of `update_pint_locale(u, lang_code)`
   - Line 679: `update_pint_locale("en")` instead of `update_pint_locale(u, "en")`
   - Line 684: `update_pint_locale(None)` instead of `update_pint_locale(u, None)`
   - And all other occurrences...

### 4. Optional: Re-export in Main API

**File**: `src/keecas/__init__.py`

Consider re-adding `update_pint_locale` to public exports:

```python
# After line 30:
from .pint_sympy import unitregistry as u, update_pint_locale

# In __all__ (around line 64):
"u",
"update_pint_locale",
```

This allows users to import as `from keecas import update_pint_locale`.

**Discussion point**: Should this function be in the main API? It's documented in CLAUDE.md as available from `pint_sympy`, and it's a more advanced/specialized feature. Could keep it as `from keecas.pint_sympy import update_pint_locale` for clarity.

## Implementation Steps

1. **Rename internal function**:
   - Change function name in `localization/pint_locale.py`
   - Update docstring to indicate internal status

2. **Update wrapper**:
   - Fix import in `pint_sympy.py`
   - Fix function call in wrapper
   - Fix docstring example

3. **Revert test changes**:
   - Change all imports to use `pint_sympy`
   - Remove `unitregistry` parameter from all calls
   - Verify tests pass with public API

4. **Run full test suite**:
   - `uv run pytest tests/test_localization.py -v`
   - Ensure all 27 tests pass
   - Verify no regressions

5. **Update documentation if needed**:
   - Check CLAUDE.md for any references
   - Ensure examples use public API

6. **Commit changes**:
   - Descriptive commit message
   - Push to current branch

## Benefits

1. **Clear API boundaries**: Public wrapper vs internal implementation
2. **Better testing**: Tests use same API as users
3. **Prevents misuse**: Internal function name discourages direct use
4. **IDE support**: Autocomplete suggests public API
5. **Maintainability**: Single entry point for users
6. **Documentation clarity**: Examples reference correct function
7. **Pythonic**: Follows Python naming conventions

## Breaking Changes

**None** - The public API signature remains unchanged. Only internal naming changes.

## Risks

**Low risk**:
- Internal function only called from 2 places (wrapper + tests after revert)
- All changes are internal refactoring
- Tests will verify correct behavior

## Open Questions

1. Should `update_pint_locale` be re-exported in main `__init__.py`?
   - Pro: Convenient for users (`from keecas import update_pint_locale`)
   - Con: It's a specialized function, keeping it in `pint_sympy` makes namespace cleaner
   - Current: Available as `from keecas.pint_sympy import update_pint_locale`

<!-- no -->

2. Any other files importing the internal function directly that we missed?

<!-- no -->

---

## Implementation Progress

### Completed (2025-11-11)

✅ **All implementation steps completed successfully**

1. **Renamed internal function** (`src/keecas/localization/pint_locale.py`)
   - Function renamed: `update_pint_locale` → `_update_pint_locale_impl`
   - Updated docstring to indicate internal implementation status
   - Added note to use public wrapper from `keecas.pint_sympy`

2. **Updated wrapper** (`src/keecas/pint_sympy.py`)
   - Fixed import: `from .localization.pint_locale import _update_pint_locale_impl`
   - Updated function call: `_update_pint_locale_impl(unitregistry, language, verbose)`
   - Docstring examples already correct (no changes needed)

3. **Fixed all test imports** (`tests/test_localization.py`)
   - Changed all imports from `from keecas import update_pint_locale` to `from keecas.pint_sympy import update_pint_locale`
   - Tests now use the public API wrapper as intended
   - Function calls already correct (no unitregistry parameter)

4. **Test Results**
   - ✅ All 27 tests in `test_localization.py` passing
   - No breaking changes to public API
   - Tests now verify the same interface users will use

### Executive Summary

Successfully resolved the `update_pint_locale` naming conflict by renaming the internal implementation to `_update_pint_locale_impl`. This change:

- **Clarifies API boundaries**: Public wrapper in `pint_sympy.py` vs internal implementation in `localization/pint_locale.py`
- **Fixes test issues**: Tests now correctly import and use the public API wrapper
- **Prevents future confusion**: Internal function name makes its purpose obvious
- **Maintains backward compatibility**: Public API signature unchanged

The fix addresses the root cause of the earlier test failures where tests were incorrectly modified to call the internal function directly. Now both users and tests use the same clean API: `update_pint_locale(language, verbose)` without needing to pass the `unitregistry` parameter.

All tests passing, ready for commit.
