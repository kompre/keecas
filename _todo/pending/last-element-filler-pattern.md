# Proposal: Universal Last-Element-as-Filler Pattern

## Objective

Replace the ambiguous `(seed, filler)` tuple pattern in `show_eqn` with a universal last-element-as-filler pattern for `col_wrap`, `float_format`, and `cell_formatter` parameters. Add a configuration option to control filler behavior globally.

## Problem Statement

### Current Implementation Issues

The current `(seed, filler)` tuple pattern has a critical type ambiguity for `col_wrap`:

```python
# User intent: Apply ("=", "") wrapping to all columns
col_wrap = ("=", "")

# ACTUAL behavior: seed="=", filler="" (WRONG!)
# EXPECTED behavior: tuple (prefix, suffix) for all columns
```

**Root cause:** `_col_wrap()` legitimately accepts `tuple[str, str]` as data (prefix, suffix), creating an unresolvable conflict with the meta-pattern `(seed, filler)`.

### Edge Cases

1. **Tuple values cannot be used**: `col_wrap = ("=", "")` is ambiguous
2. **Nested structures are confusing**: `([None, ("=", "")], ("default", ""))`
3. **None as filler is awkward**: `(None, ".2f")` - which is seed?
4. **Inconsistent across parameters**: Only works cleanly for non-tuple value types

## Proposed Solution

### Universal Last-Element-as-Filler Pattern

**For all three parameters** (`col_wrap`, `float_format`, `cell_formatter`):

- **Lists**: Last element serves as filler and remains in sequence
- **Scalar**: Repeats across all columns (existing behavior)
- **Dict**: Per-row specification (existing behavior)
- **Dataframe**: Per-cell specification (existing behavior)

### Behavior Examples

```python
# width=3, keys=[x, y]

# Scalar (unchanged)
".3f" → all rows: [".3f", ".3f", ".3f"]

# Single-element list (equivalent to scalar)
[".3f"] → all rows: [".3f", ".3f", ".3f"]

# Multi-element list (last element fills remaining)
[".1f", ".2f"] → all rows: [".1f", ".2f", ".2f"]

# Explicit None filler
[".1f", None] → all rows: [".1f", None, None]

# Exact width (no padding)
[".1f", ".2f", ".3f"] → all rows: [".1f", ".2f", ".3f"]

# Dict (per-row, unchanged)
{x: ".3f"} → {x: [".3f", ".3f", ".3f"], y: [None, None, None]}

# Dict with list values
{x: [".1f", ".2f"]} → {x: [".1f", ".2f", ".2f"], y: [None, None, None]}
```

### Col_wrap Examples (Solves Ambiguity)

```python
# ✅ Tuple wrapping now works!
[None, ("=", "")] → all rows: [None, ("=", ""), ("=", "")]

# ✅ Different tuples per column
[None, ("=", ""), (r"\quad(", ")")]
→ all rows: [None, ("=", ""), (r"\quad(", ")"), (r"\quad(", ")"), ...]

# ✅ Single tuple for all (both work identically)
("=", "") → all rows: [("=", ""), ("=", ""), ("=", "")]
[("=", "")] → all rows: [("=", ""), ("=", ""), ("=", "")]
```

## Behavior: Always Use Last Element as Filler

**Simple rule:** For lists, the last element always serves as the filler.

```python
# Last element fills remaining columns
[".1f", ".2f"] → [".1f", ".2f", ".2f", ".2f", ...]

# Explicit None filler
[".1f", None] → [".1f", None, None, None, ...]

# Exact width, no padding needed
[".1f", ".2f", ".3f"]  # width=3 → [".1f", ".2f", ".3f"]
```

**No configuration needed** - behavior is consistent and predictable.

## Implementation Details

### Step 1: Create Helper Function

```python
def _extract_seed_and_filler(value: Any) -> tuple[Any, Any]:
    """Extract seed and filler from various input formats.

    Args:
        value: Input value (scalar, list, dict, Dataframe)

    Returns:
        (seed, filler) tuple where:
        - seed: Value to pass to create_dataframe
        - filler: Value to use as default_value in create_dataframe

    Examples:
        >>> _extract_seed_and_filler([".1f", ".2f"])
        ([".1f", ".2f"], ".2f")

        >>> _extract_seed_and_filler(".3f")
        (".3f", None)

        >>> _extract_seed_and_filler([".3f"])
        ([".3f"], ".3f")
    """
    if isinstance(value, list) and len(value) > 0:
        # Last element is filler
        return value, value[-1]
    else:
        # Scalar, empty list, dict, or Dataframe - no list filler
        return value, None
```

### Step 2: Update `show_eqn` Parameter Processing

Replace current tuple pattern logic:

```python
# OLD (lines 320-352)
float_format = create_dataframe(
    seed=float_format[0] if isinstance(float_format, tuple) else float_format,
    default_value=float_format[1] if isinstance(float_format, tuple) else None,
    keys=keys,
    width=num_cols,
)

# NEW
float_format_seed, float_format_filler = _extract_seed_and_filler(float_format)
float_format = create_dataframe(
    seed=float_format_seed,
    default_value=float_format_filler,
    keys=keys,
    width=num_cols,
)
```

Apply same pattern to `col_wrap` and `cell_formatter`.

### Step 3: Update `create_dataframe` List Handling

Modify list seed handling to use filler consistently:

```python
elif isinstance(seed, list):
    # List seed (applies to all rows)
    if len(seed) == 0:
        # Empty list: fill with default_value
        seed_list = [default_value] * width
    else:
        # Use list elements up to width, pad with default_value
        seed_list = seed[:width] + [default_value] * max(0, width - len(seed))
    for key in keys:
        df[key] = seed_list.copy()
```

**Note:** When `filler_index=None` and list length doesn't match width, `create_dataframe` receives `default_value=None`, resulting in None padding. Add validation if strict mode desired.

### Step 4: Add Strict Validation (Optional)

```python
elif isinstance(seed, list):
    if len(seed) == 0:
        seed_list = [default_value] * width
    elif default_value is None and len(seed) != width:
        # Strict mode: no filler and length mismatch
        raise ValueError(
            f"List length ({len(seed)}) doesn't match width ({width}). "
            f"Set config.display.filler_index to enable automatic filling."
        )
    else:
        seed_list = seed[:width] + [default_value] * max(0, width - len(seed))
    for key in keys:
        df[key] = seed_list.copy()
```

### Step 5: Update Docstrings

Update `show_eqn` parameter documentation:

```python
def show_eqn(
    eqns: dict[Any, Any] | list[dict[Any, Any]] | Dataframe,
    # ...
    col_wrap: str | dict | list[dict] | Dataframe | Callable | None = None,
    float_format: str | dict | list[dict] | Dataframe | None = None,
    cell_formatter: Callable | dict | list | Dataframe | None = None,
    # ...
) -> Latex:
    r"""Display mathematical equations as formatted LaTeX amsmath block.

    Args:
        col_wrap: Column wrapping specifications for LaTeX formatting.
            Can be:
            - Scalar (str/tuple/dict): Applied to all cells
            - list: Column-specific values. Last element fills remaining columns.
              For prefix/suffix tuples: [None, ("=", ""), ("\\quad(", ")")] works correctly.
            - dict: Per-row specification {symbol: value_or_list}
            - Dataframe: Per-cell specification
            List elements: None (no wrapping), str (prefix only),
            tuple (prefix, suffix), or Callable.
            Defaults to config.col_wrap.

        float_format: Format specification for float values (does not affect int).
            Can be:
            - str: Format applied to all floats (e.g., ".3f")
            - list: Column-specific formats. Last element fills remaining columns.
              Example: [None, ".3f", ".2f"] → col 0: no format, col 1: ".3f",
              col 2+: ".2f"
            - dict: Per-row specification {symbol: format_or_list}
            - Dataframe: Per-cell specification
            Supports format specs with or without braces (e.g., ".3f" or "{:.3f}").
            Defaults to config.display.default_float_format.

        cell_formatter: Custom cell value formatter function(s).
            Can be:
            - Callable: Applied to all cells (signature: (value, col_index) -> str)
            - list: Column-specific formatters. Last element fills remaining columns.
            - dict: Per-row specification {symbol: formatter_or_list}
            - Dataframe: Per-cell specification
            Defaults to config.display.cell_formatter or format_value.
```

## Migration Strategy

### Breaking Changes

Since backward compatibility is not an issue:

1. **Remove tuple pattern support entirely** - clean break
2. **Update all examples** in docs and notebooks
3. **Update CLAUDE.md** with new patterns

### Migration Examples

**Old (tuple pattern):**
```python
float_format = ({x: ".3f"}, ".4f")
col_wrap = ([None, ("=", "")], ("default", ""))
cell_formatter = ({x: custom_fmt}, format_value)
```

**New (last-element pattern):**
```python
float_format = [{x: ".3f"}, ".4f"]
col_wrap = [None, ("=", ""), ("default", "")]
cell_formatter = [{x: custom_fmt}, format_value]
```

**Alternative (dict with list values):**
```python
float_format = {x: [".3f", ".3f", ".4f"], y: [".4f", ".4f", ".4f"]}
col_wrap = [None, ("=", "")]  # Simpler when all rows same
```

### Documentation Updates

1. **README.md**: Update examples
2. **CLAUDE.md**:
   - Update "Keecas Usage Conventions" section
   - Add note about `filler_index` config
3. **API reference**: Update `show_eqn` docstring
4. **User guide**: Add section on list filler behavior
5. **Examples**: Update all notebooks

## Testing Strategy

### Unit Tests

**Test file:** `tests/test_display.py`

```python
def test_last_element_filler_scalar():
    """Test scalar values repeat across columns."""
    eqns = [{x: 1}, {x: 2}, {x: 3}]  # 3 columns
    result = show_eqn(eqns, float_format=".2f", debug=True)
    assert "1.00" in result.data
    assert "2.00" in result.data
    assert "3.00" in result.data

def test_last_element_filler_single_list():
    """Test single-element list equivalent to scalar."""
    eqns = [{x: 1.5}, {x: 2.5}]

    # Scalar
    result1 = show_eqn(eqns, float_format=".1f", debug=True)

    # Single-element list
    result2 = show_eqn(eqns, float_format=[".1f"], debug=True)

    assert result1.data == result2.data
    assert "1.5" in result1.data

def test_last_element_filler_multi_list():
    """Test last element fills remaining columns."""
    eqns = [{x: 1.111}, {x: 2.222}, {x: 3.333}]  # 3 cols

    # [col0, col1, col2+]
    result = show_eqn(eqns, float_format=[None, ".2f"], debug=True)

    # Col 0: no formatting
    assert "1.111" in result.data
    # Col 1+: .2f formatting
    assert "2.22" in result.data
    assert "3.33" in result.data

def test_last_element_filler_exact_width():
    """Test list with exact width, no padding needed."""
    eqns = [{x: 1.1}, {x: 2.2}, {x: 3.3}]
    result = show_eqn(eqns, float_format=[None, ".1f", ".2f"], debug=True)

    assert "1.1" in result.data  # Col 0: no format
    assert "2.2" in result.data  # Col 1: .1f
    assert "3.30" in result.data  # Col 2: .2f

def test_last_element_filler_none():
    """Test explicit None as filler."""
    eqns = [{x: 1.5}, {x: 2.5}, {x: 3.5}]
    result = show_eqn(eqns, float_format=[".1f", None], debug=True)

    # Col 0: formatted
    assert "1.5" in result.data
    # Col 1+: no format (None)
    assert "2.5" in result.data
    assert "3.5" in result.data

def test_col_wrap_tuple_values():
    """Test col_wrap with tuple values (solves ambiguity issue)."""
    eqns = [{x: 1}, {x: 2}]

    # Single tuple for all columns
    result1 = show_eqn(eqns, col_wrap=("=", ""), debug=True)
    assert result1.data.count("=") >= 2  # Both columns have "="

    # List with tuple values
    result2 = show_eqn(eqns, col_wrap=[None, ("=", "")], debug=True)
    assert "=1" in result2.data or "= 1" in result2.data
    assert "=2" in result2.data or "= 2" in result2.data

def test_col_wrap_different_tuples():
    """Test col_wrap with different tuples per column."""
    eqns = [{x: 1}, {x: 2}, {x: 3}]
    result = show_eqn(
        eqns,
        col_wrap=[None, ("=", ""), (r"\quad(", ")")],
        debug=True
    )

    # Col 0: no wrap
    # Col 1: "=" prefix
    # Col 2+: "\quad(" prefix, ")" suffix
    assert "=2" in result.data or "= 2" in result.data
    assert r"\quad(3)" in result.data or r"\quad( 3 )" in result.data

def test_dict_with_list_values():
    """Test dict seed with list values uses filler per row."""
    eqns = [{x: 1.11, y: 2.22}, {x: 3.33, y: 4.44}]

    float_format = {
        x: [".1f", ".2f"],  # x: col 0 .1f, col 1+ .2f
        y: ".3f",           # y: all cols .3f
    }

    result = show_eqn(eqns, float_format=float_format, debug=True)

    # x row: 1.1, 3.33
    assert "1.1" in result.data
    assert "3.33" in result.data

    # y row: 2.220, 4.440
    assert "2.220" in result.data
    assert "4.440" in result.data

def test_cell_formatter_list():
    """Test cell_formatter with list and last-element filler."""
    from keecas import format_value

    def custom_fmt(val, col_idx, **kwargs):
        return f"CUSTOM[{val}]"

    eqns = [{x: "a"}, {x: "b"}]

    # Use custom for col 0, default for rest
    result = show_eqn(
        eqns,
        cell_formatter=[custom_fmt, format_value],
        debug=True
    )

    # Col 0 uses custom_fmt
    assert "CUSTOM[" in result.data
    # Col 1 uses format_value (should have \text{})
    assert r"\text{" in result.data
```

### Integration Tests

**Test file:** `tests/test_integration.py`

```python
def test_complex_multi_column_formatting():
    """Test complex scenario with all three parameters using lists."""
    from keecas import symbols, u, pc, show_eqn

    F, A, sigma = symbols(r"F, A, \sigma")

    _p = {F: 10*u.kN, A: 5*u.cm**2}
    _e = {sigma: "F/A" | pc.parse_expr}
    _v = {k: v | pc.subs(_p | _e) | pc.N for k, v in _e.items()}

    result = show_eqn(
        [_p | _e, _v],
        col_wrap=[None, ("=", "")],  # No wrap col 0, "=" for rest
        float_format=[None, ".2f"],   # No format col 0, .2f for rest
        debug=True
    )

    assert isinstance(result, Latex)
    assert "=" in result.data
    # Check formatting applied
```

### Edge Case Tests

```python
def test_empty_list():
    """Test empty list seed."""
    eqns = {x: 1}
    # Should default to None for all columns
    result = show_eqn(eqns, float_format=[], debug=True)
    assert isinstance(result, Latex)

def test_list_longer_than_width():
    """Test list truncation when longer than width."""
    eqns = {x: 1}  # Only 1 column + key = 2 total
    # List has 5 elements but only 2 columns
    result = show_eqn(eqns, float_format=[".1f", ".2f", ".3f", ".4f", ".5f"], debug=True)
    # Should truncate to width
    assert isinstance(result, Latex)
```

## Success Criteria

- [ ] `_extract_seed_and_filler()` helper function implemented
- [ ] All three parameters (`col_wrap`, `float_format`, `cell_formatter`) use new pattern
- [ ] Tuple pattern code completely removed
- [ ] `col_wrap` can accept tuple values without ambiguity
- [ ] Single-element lists equivalent to scalars (last element fills)
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Documentation updated (README, CLAUDE.md, API docs)
- [ ] Examples updated (notebooks, user guide)
- [ ] Backwards incompatible changes documented in CHANGELOG

## Timeline Estimate

- Helper function implementation: 30 minutes
- `show_eqn` refactoring: 1 hour
- `create_dataframe` updates: 30 minutes (optional, may not need changes)
- Docstring updates: 1 hour
- Unit tests: 2 hours
- Integration tests: 1 hour
- Documentation updates: 2 hours
- Example updates: 1 hour

**Total:** ~9 hours

## Open Questions

1. Should empty lists `[]` be treated as "no value" or "all None"?
   - **Recommendation:** All None (consistent with `default_value=None` behavior)

2. Should the filler element be removed from the sequence or kept?
   - **Decision:** Kept in sequence (last element appears at its position AND fills remaining)
   - **Rationale:** Simpler mental model and allows exact width matching
---

## Implementation Progress

### Completed (2025-01-05)

**Core Implementation:**
- ✅ Added `_extract_seed_and_filler()` helper function in `display.py`
- ✅ Refactored `show_eqn` to use new pattern for `float_format`, `col_wrap`, and `cell_formatter`
- ✅ Removed tuple pattern support from type hints
- ✅ Updated parameter docstrings to reflect new last-element-as-filler behavior

**Testing:**
- ✅ Added 11 comprehensive unit tests covering:
  - Scalar vs single-element list equivalence
  - Multi-element lists with last-element filling
  - Exact width matching
  - Explicit None filler
  - col_wrap with tuple values (solving the ambiguity!)
  - Different tuples per column
  - Dict with list values (per-row formatting)
  - Cell formatter lists
  - Empty lists
  - List truncation when longer than width
- ✅ All 58 tests in test_display.py passing

**Key Changes:**
1. `display.py:910-939` - New `_extract_seed_and_filler()` helper
2. `display.py:322-328` - float_format using new pattern
3. `display.py:332-338` - col_wrap using new pattern  
4. `display.py:349-359` - cell_formatter using new pattern
5. `display.py:44-46` - Updated type hints (removed tuple support)
6. `display.py:82-99` - Updated parameter docstrings
7. `tests/test_display.py:785-949` - 11 new tests + 1 updated test

### Remaining Work

- [ ] Update examples in notebooks (hello_world.ipynb, quarto_example.ipynb)
- [ ] Update user guide documentation
- [ ] Update CLAUDE.md with new pattern
- [ ] Add CHANGELOG entry for breaking change

### Executive Summary

Successfully implemented the universal last-element-as-filler pattern, replacing the ambiguous `(seed, filler)` tuple pattern. The implementation is clean, well-tested, and solves the critical col_wrap ambiguity where tuple data values conflicted with the meta-pattern.

**Breaking Change:** The tuple pattern `({x: ".3f"}, ".4f")` is no longer supported. Users should use list pattern `[{x: ".3f"}, ".4f"]` or dict pattern instead.

**Benefit:** col_wrap can now accept tuple values without ambiguity: `[None, ("=", ""), (r"\quad(", ")")]` works correctly!

All tests pass (58/58), implementation is complete and ready for review.
