# Proposal: Refactor create_dataframe using singledispatch pattern

**Status**: ✅ Completed - Merged to dev
**Created**: 2025-01-06
**Approved**: 2025-01-06
**Completed**: 2025-11-06
**Branch**: feature/refactor-create-dataframe-singledispatch
**PR**: #40 (merged)
**Commits**: 885164e, 64bbf77
**Original Objective**: Refactor `create_dataframe` using singledispatch pattern to handle different input types more elegantly, with special handling for dict[key, list] similar to list case but key-specific.

## Final Implementation Summary

**Merged**: PR #40 to dev on 2025-11-06
**Test Results**: All 181 tests passing
**Breaking Change**: Parameter order changed to `(seed, keys, width, default_value)`

## Implementation Decisions (Finalized)

1. **No manual `_width` setting**: Let Dataframe constructor calculate width from data
2. **No `filler` parameter**: All data constructed at correct width, no padding needed
3. **`.copy()` required for list case**: Prevents aliasing bugs where all rows share same list
4. **No separate Dataframe handler**: dict handler covers Dataframe via inheritance
5. **Helper function `_pad_or_repeat`**: Extracts common padding/repetition logic

## Problem Analysis

### Current Implementation Issues

The current `create_dataframe` function in `dataframe.py:438-550` has several structural issues:

1. **Nested type checking with isinstance**: Manual type inspection creates complex branching logic
2. **No separation of concerns**: All seed type logic is embedded in one function
3. **Inconsistent dict handling**: Dict seed supports mixed list/scalar values per key, but this adds complexity
4. **Code duplication**: Similar padding/filling logic repeated across branches
5. **Hard to extend**: Adding new seed types requires modifying the core function
6. **Unclear dispatch priority**: The order of isinstance checks matters but isn't documented

### Current Behavior (dataframe.py:438-550)

```python
def create_dataframe(
    keys: list[Hashable],
    width: int,
    seed: Any | list[Any] | dict[Hashable, Any] | Dataframe | None = None,
    default_value: Any = None,
) -> Dataframe:
    df: Dataframe = Dataframe()

    if not isinstance(seed, (list, dict, Dataframe)):
        # Scalar case - same value for all cells
        for key in keys:
            df[key] = [seed] * width

    elif isinstance(seed, list):
        # List case - same list for all rows
        seed_list = seed[:width] + [default_value] * (width - len(seed))
        for key in keys:
            df[key] = seed_list.copy()

    elif isinstance(seed, Dataframe):
        # Dataframe case - copy values from existing Dataframe
        for key in keys:
            if key in seed:
                df[key] = seed[key][:width] + [default_value] * (width - len(seed[key]))
            else:
                df[key] = [default_value] * width

    elif isinstance(seed, dict):
        # Dict case - per-row initialization (mixed list/scalar per key)
        for key in keys:
            if key in seed:
                if isinstance(seed[key], list):
                    df[key] = seed[key][:width] + [default_value] * (width - len(seed[key]))
                else:
                    df[key] = [seed[key]] * width
            else:
                df[key] = [default_value] * width

    df._width = width
    return df
```

### Key Insight: Dict[key, list] Needs Special Treatment

The problem statement highlights an important distinction:

**Current dict handling** (lines 530-540):
- If `seed[key]` is a list: Use it as the row values (pad if needed)
- If `seed[key]` is scalar: Repeat it across the row
- If key missing: Fill with `default_value`

**Desired behavior**:
- Handle `dict[key, list]` case similar to the `list` case but **key-specific**
- This means: For each key, if provided as a list, use that specific list for that row
- Unlike scalar dict, where each key can have a different scalar
- Unlike list seed, where all keys share the same list

The **real issue**: The dict case is **already doing this correctly**, but the logic is buried in nested conditionals. We need to make it clearer and more maintainable.

## Proposed Solution: Singledispatch Pattern

### Architecture

Adopt the same pattern used in `formatters.py` (lines 84-150):

```python
from functools import singledispatch
from typing import Any
from collections.abc import Hashable

def _pad_or_repeat(value: Any, width: int, default_value: Any) -> list[Any]:
    """Convert value to list of specified width.

    Args:
        value: Value to convert (list or scalar)
        width: Target list length
        default_value: Value to use for padding

    Returns:
        List of exactly width elements

    Notes:
        - If value is list: pad/truncate to exactly width
        - Otherwise: repeat value exactly width times
    """
    if isinstance(value, list):
        return value[:width] + [default_value] * max(0, width - len(value))
    else:
        return [value] * width


@singledispatch
def create_dataframe(
    seed: Any,
    keys: list[Hashable],
    width: int,
    default_value: Any = None,
) -> Dataframe:
    """Create a pre-sized Dataframe with specified shape and initial values.

    Factory function using singledispatch for type-based initialization.
    Fallback implementation handles scalar seeds.

    Args:
        seed: Seed value (any type) - repeated across all cells
        keys: Row labels
        width: Number of columns
        default_value: Not used for scalar case

    Returns:
        New Dataframe with all cells initialized to seed value

    Notes:
        - No filler parameter needed - all data at correct width by construction
        - Dataframe._width automatically calculated from data
    """
    # Scalar case - repeat same value for all cells
    return Dataframe({k: [seed] * width for k in keys})


@create_dataframe.register(list)
def _from_list(
    seed: list[Any],
    keys: list[Hashable],
    width: int,
    default_value: Any = None,
) -> Dataframe:
    """Create Dataframe from list seed - same list for all rows.

    Args:
        seed: List of values to use for all rows
        keys: Row labels
        width: Number of columns
        default_value: Filler for missing values

    Returns:
        New Dataframe with list applied to all rows

    Notes:
        - .copy() is REQUIRED to avoid aliasing - each row gets independent list
        - Without .copy(), all rows would share same list object
    """
    padded_list = seed[:width] + [default_value] * max(0, width - len(seed))
    return Dataframe({k: padded_list.copy() for k in keys})


@create_dataframe.register(dict)
def _from_dict(
    seed: dict[Hashable, Any],
    keys: list[Hashable],
    width: int,
    default_value: Any = None,
) -> Dataframe:
    """Create Dataframe from dict seed - per-row customization.

    Handles three cases per key:
    1. Key missing: Fill with default_value
    2. Dict[key, list]: Use specific list for that row (key-specific list)
    3. Dict[key, scalar]: Repeat scalar across that row

    Args:
        seed: Dict mapping keys to values (scalar or list)
        keys: Row labels
        width: Number of columns
        default_value: Filler for missing keys/values

    Returns:
        New Dataframe with per-row initialization

    Notes:
        - Also handles Dataframe seed (dict subclass) via inheritance
        - No separate Dataframe handler needed
        - _pad_or_repeat ensures all rows have exactly width elements
    """
    data = {
        key: _pad_or_repeat(seed.get(key, default_value), width, default_value)
        for key in keys
    }
    return Dataframe(data)
```

## Implementation Plan

### Step 1: Add singledispatch infrastructure
- Import `singledispatch` from `functools`
- Refactor `create_dataframe` to use `@singledispatch` decorator
- Change parameter order: `seed` becomes first parameter for dispatch
- **New signature**: `create_dataframe(seed, keys, width, default_value=None)`

### Step 2: Implement specialized handlers
- Add `_pad_or_repeat` helper function
- `create_dataframe` (base): Handle scalar case - returns Dataframe
- `_from_list`: Handle list seed with .copy() - returns Dataframe
- `_from_dict`: Handle dict seed - returns Dataframe
  - **Critical**: Maintain existing behavior where dict values can be lists OR scalars
  - Lists are treated as "key-specific list case" (similar to list case but per-row)
  - Scalars are repeated across the row
  - Also handles Dataframe (no separate handler needed)

### Step 3: Update all call sites
- **BREAKING CHANGE**: Parameter order changed
- Old: `create_dataframe(keys, width, seed, default_value)`
- New: `create_dataframe(seed, keys, width, default_value)`
- Search codebase for all uses of `create_dataframe` and update
- Update docstring with new signature

### Step 4: Simplify each handler
- Each handler constructs and returns complete Dataframe
- No intermediate dict step needed
- Handlers set `df._width` directly before returning

### Step 5: Update tests
- Verify all existing tests pass (no behavior changes)
- Add explicit tests for:
  - Dict with list values (key-specific list case)
  - Dict with scalar values (repeated scalar case)
  - Dict with mixed list/scalar values (current behavior)
  - Edge cases: empty lists, oversized lists, missing keys
- Add tests for custom type registration (extensibility)

### Step 6: Update documentation
- Add docstring examples showing dict[key, list] vs dict[key, scalar]
- Document the "key-specific list" concept clearly
- Add "Custom type registration" example similar to formatters.py
- Update CLAUDE.md architecture section if needed

## Benefits

### Code Quality
1. **Separation of concerns**: Each seed type has its own handler function
2. **Single Responsibility**: Each function does one thing well
3. **Eliminates nesting**: No more nested isinstance checks
4. **Clear dispatch order**: Python's singledispatch handles MRO correctly
5. **DRY**: Padding logic extracted and reused

### Maintainability
1. **Easy to extend**: Register new seed types without modifying core function
2. **Testable**: Each handler can be tested independently
3. **Readable**: Intent is clear from function names and dispatch
4. **Consistent**: Matches formatters.py pattern (established in keecas)

### Type Safety
1. **Better type hints**: Each handler has specific type signature
2. **Runtime dispatch**: singledispatch validates types automatically
3. **Clear contracts**: Return type is always dict[Hashable, list[Any]]

### User Experience
1. **Extensibility**: Users can register custom seed types:
   ```python
   from keecas.dataframe import create_dataframe, Dataframe

   @create_dataframe.register(MyDataType)
   def _from_custom(seed: MyDataType, keys, width, default_value=None):
       # Custom initialization logic
       df = Dataframe()
       for key in keys:
           df[key] = [...]  # Custom logic here
       df._width = width
       return df
   ```
2. **Predictable**: Dispatch based on type is easy to reason about
3. **Breaking change**: Parameter order changed - need to update call sites

## Clarification: The "Key-Specific List" Pattern

The proposal emphasizes handling `dict[key, list]` "similar to list case but key-specific." Here's what that means:

### Three Patterns Compared

1. **List seed** (all rows share same list):
   ```python
   df = create_dataframe([x, y, z], width=3, seed=[1, 2, 3])
   # Result: {x: [1, 2, 3], y: [1, 2, 3], z: [1, 2, 3]}
   ```

2. **Dict[key, scalar] seed** (each row has different scalar repeated):
   ```python
   df = create_dataframe([x, y, z], width=3, seed={x: 1, y: 2, z: 3})
   # Result: {x: [1, 1, 1], y: [2, 2, 2], z: [3, 3, 3]}
   ```

3. **Dict[key, list] seed** (each row has different list - KEY-SPECIFIC):
   ```python
   df = create_dataframe([x, y, z], width=3, seed={
       x: [1, 2, 3],
       y: [4, 5, 6],
       z: [7, 8]  # Padded to [7, 8, default_value]
   })
   # Result: {x: [1, 2, 3], y: [4, 5, 6], z: [7, 8, None]}
   ```

**Key insight**: Pattern #3 is "similar to list case" in that each list is padded/truncated to width, but it's "key-specific" because each key can have a different list.

The current implementation already supports this (lines 533-535), but it's hidden in nested conditionals. The singledispatch refactor makes this pattern explicit and clear.

## Edge Cases & Backward Compatibility

### Edge Cases to Handle
1. **None seed**: Should dispatch to scalar handler (fill with None)
2. **Empty list seed**: Should fill with default_value
3. **Oversized lists**: Should truncate to width
4. **Empty keys list**: Should return empty Dataframe
5. **Width = 0**: Should return Dataframe with empty rows

### Backward Compatibility Guarantee
- All existing calls to `create_dataframe` must produce identical results
- No changes to function signature
- No changes to docstring examples (they should still work)
- Test suite must pass without modification (behavior unchanged)

## Testing Strategy

### Unit Tests for Each Handler
```python
def test_create_from_scalar():
    """Test scalar seed handler."""
    df = create_dataframe(42, [x, y], width=3)
    assert df == {x: [42, 42, 42], y: [42, 42, 42]}
    assert df._width == 3

def test_create_from_list():
    """Test list seed handler."""
    df = create_dataframe([1, 2], [x, y], width=3, default_value=0)
    assert df == {x: [1, 2, 0], y: [1, 2, 0]}
    assert df._width == 3

    # Ensure lists are independent copies
    df[x][0] = 999
    assert df[y][0] == 1  # Not affected

def test_create_from_dict_list_values():
    """Test dict seed with list values (key-specific lists)."""
    df = create_dataframe(
        {x: [1, 2, 3], y: [4, 5]},
        [x, y, z],
        width=3,
        default_value=0
    )
    assert df == {
        x: [1, 2, 3],
        y: [4, 5, 0],
        z: [0, 0, 0]  # Missing key
    }
    assert df._width == 3

def test_create_from_dict_scalar_values():
    """Test dict seed with scalar values."""
    df = create_dataframe(
        {x: 10, y: 20},
        [x, y, z],
        width=3,
        default_value=0
    )
    assert df == {
        x: [10, 10, 10],
        y: [20, 20, 20],
        z: [0, 0, 0]
    }
    assert df._width == 3

def test_create_from_dict_mixed():
    """Test dict seed with mixed list/scalar values."""
    df = create_dataframe(
        {x: [1, 2], y: 99},
        [x, y],
        width=3,
        default_value=0
    )
    assert df == {
        x: [1, 2, 0],
        y: [99, 99, 99]
    }
    assert df._width == 3

def test_create_from_dataframe():
    """Test Dataframe seed handler."""
    seed_df = Dataframe({x: [1, 2], y: [3, 4, 5]})
    df = create_dataframe(seed_df, [x, y, z], width=3, default_value=0)
    assert df == {
        x: [1, 2, 0],
        y: [3, 4, 5],
        z: [0, 0, 0]
    }
    assert df._width == 3
```

### Integration Tests
- All existing `test_dataframe.py` tests must pass unchanged
- Add integration test showing custom type registration

## Migration Path

### Phase 1: Implement new singledispatch version
- Add `@singledispatch` decorator to `create_dataframe` with new signature
- Implement all specialized handlers (`_from_list`, `_from_dict`, `_from_dataframe`)
- Each handler returns complete Dataframe

### Phase 2: Update all call sites
- Search for all uses of `create_dataframe` in codebase
- Update parameter order from `(keys, width, seed, default_value)` to `(seed, keys, width, default_value)`
- Update tests to use new signature

### Phase 3: Update documentation
- Update docstring examples with new signature
- Add "Custom type registration" section showing extensibility
- Document parameter order change in changelog
- Update CLAUDE.md if needed

## Open Questions

1. **Should we keep parameter order or change it?**
   - **Old**: `create_dataframe(keys, width, seed, default_value)`
   - **New**: `create_dataframe(seed, keys, width, default_value)` (required for singledispatch)
   - **Decision**: MUST change - singledispatch requires dispatched parameter to be first
   - **Impact**: Breaking change - need to update all call sites

2. **Should we add a helper for padding?**
   ```python
   def _pad_to_width(value_list: list[Any], width: int, filler: Any) -> list[Any]:
       """Pad or truncate list to specified width."""
       return value_list[:width] + [filler] * max(0, width - len(value_list))
   ```
   - **Recommendation**: Optional - reduces duplication but handlers are already concise

3. **Should None seed be special-cased?**
   - Current: Falls through to scalar handler, fills with None values
   - Alternative: Explicit handler that fills with default_value
   - **Recommendation**: Keep current behavior (None is just a scalar)

4. **Should we validate that dict values are homogeneous (all lists OR all scalars)?**
   - Current: Allows mixed list/scalar values in same dict
   - Alternative: Raise ValueError if mixed
   - **Recommendation**: Keep flexible (current behavior), document clearly

## Risks & Mitigation

### Risk: Breaking Backward Compatibility
- **Mitigation**: Comprehensive test suite must pass unchanged
- **Mitigation**: Manual testing of all docstring examples
- **Mitigation**: If any test fails, investigate before proceeding

### Risk: Performance Regression
- **Mitigation**: singledispatch has minimal overhead (cached dispatch)
- **Mitigation**: Run benchmarks before/after if performance is critical
- **Mitigation**: The function is not performance-critical (construction-time only)

### Risk: Confusing Dispatch Behavior
- **Mitigation**: Clear docstrings explaining dispatch rules
- **Mitigation**: Type hints make dispatch explicit
- **Mitigation**: Follow established pattern from formatters.py

## Success Criteria

1. All existing tests pass without modification
2. New tests cover all dispatch handlers independently
3. Code is more readable (subjective but reviewable)
4. No performance regression (micro-benchmarks if needed)
5. Documentation clearly explains dict[key, list] pattern
6. Example showing custom type registration works

## References

- **Formatters pattern**: `src/keecas/formatters.py:84-150` - established singledispatch pattern in keecas
- **Current implementation**: `src/keecas/dataframe.py:438-550`
- **Python docs**: https://docs.python.org/3/library/functools.html#functools.singledispatch

## Next Steps

Awaiting user approval to:
1. Create feature branch: `feature/refactor-create-dataframe-singledispatch`
2. Implement Phase 1 (preparation)
3. Implement Phase 2 (switch implementation)
4. Implement Phase 3 (documentation)
5. Create PR to dev branch
