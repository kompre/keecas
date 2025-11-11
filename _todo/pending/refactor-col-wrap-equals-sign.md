# Task Proposal: Refactor `=` Sign Handling to col_wrap

## Original Objective
Move the `=` sign insertion from cell formatters to `col_wrap` system for better separation of concerns and user flexibility.

**User Rationale**: Cell formatters should be stable (pure type conversion), while col_wrap is easier to modify on-the-fly for one-off cases. Users can pass simple lists like `[None, "=", None]` instead of defining custom formatter functions.

## Current Implementation

### Cell Formatters (formatters.py)
- Type-based dispatch using `@singledispatch`
- Numeric types (int, float, Basic) add `"= "` prefix when `col_index > 0`
- Text types (str, Markdown) add `r"\quad"` prefix when `col_index > 0`
- Example:
  ```python
  @format_value.register(int)
  def format_int(value: int, col_index: int = 0, **kwargs) -> str:
      if col_index == 0:
          return str(value)
      else:
          return f"= {value}"
  ```

### Col Wrap (display.py:952)
- Currently handles wrapping with prefix/suffix tuples
- Supports: None, str, tuple, dict[type, tuple]
- Called in show_eqn:404: `f"{_col_wrap(cw, v)[0]}{formatted_value}{_col_wrap(cw, v)[-1]}"`
- No type-based dispatch, no column index awareness

## Proposed Architecture

### 1. Cell Formatters → Pure Type Converters
Remove all `=` and `\quad` prefix logic from formatters:

```python
@format_value.register(int)
def format_int(value: int, col_index: int = 0, **kwargs) -> str:
    """Pure conversion: int → LaTeX string (no decoration)."""
    return str(value)

@format_value.register(float)
def format_float(value: float, col_index: int = 0, **kwargs) -> str:
    """Pure conversion: float → LaTeX string (no decoration)."""
    return str(value)

@format_value.register(str)
def format_str(value: str, col_index: int = 0, **kwargs) -> str:
    """Pure conversion: str → LaTeX text (no decoration)."""
    return rf"\text{{{value}}}"

@format_value.register(Basic)
def format_sympy(value: Basic, col_index: int = 0, **kwargs) -> str:
    """Pure conversion: SymPy → LaTeX string (no decoration)."""
    return latex(value, **kwargs)
```

**Note**: `col_index` parameter remains for potential use by custom formatters. Keeps API consistent.

### 2. Col Wrap → Singledispatch-Based Decoration
Create new module `col_wrapper.py` with singledispatch pattern:

```python
from functools import singledispatch
from typing import Any
from sympy import Basic

@singledispatch
def wrap_column(value: Any, col_index: int = 0, **kwargs) -> tuple[str, str]:
    """Return (prefix, suffix) for column wrapping based on value type.

    Default fallback: no wrapping for unknown types.
    """
    return ("", "")

@wrap_column.register(int)
@wrap_column.register(float)
def wrap_numeric(value: int | float, col_index: int = 0, **kwargs) -> tuple[str, str]:
    """Numeric types get '= ' prefix in RHS columns."""
    if col_index == 0:
        return ("", "")
    return ("= ", "")

@wrap_column.register(Basic)
def wrap_sympy(value: Basic, col_index: int = 0, **kwargs) -> tuple[str, str]:
    """SymPy expressions get '= ' prefix in RHS columns."""
    if col_index == 0:
        return ("", "")
    return ("= ", "")

@wrap_column.register(str)
def wrap_str(value: str, col_index: int = 0, **kwargs) -> tuple[str, str]:
    """Strings get '\quad' prefix in RHS columns."""
    if col_index == 0:
        return ("", "")
    return (r"\quad", "")

# Optional: Pint and IPython types (if available)
try:
    import pint
    @wrap_column.register(pint.Quantity)
    def wrap_pint(value: pint.Quantity, col_index: int = 0, **kwargs) -> tuple[str, str]:
        if col_index == 0:
            return ("", "")
        return ("= ", "")
except ImportError:
    pass

try:
    from IPython.display import Markdown, Latex
    @wrap_column.register(Markdown)
    @wrap_column.register(Latex)
    def wrap_markdown(value: Markdown | Latex, col_index: int = 0, **kwargs) -> tuple[str, str]:
        if col_index == 0:
            return ("", "")
        return (r"\quad", "")
except ImportError:
    pass
```

### 3. Integration in display.py
Update `show_eqn()` to use new default:

```python
# Import new default wrapper
from keecas.col_wrap_formatter import wrap_column

def show_eqn(
    eqns: dict[Any, Any] | list[dict[Any, Any]] | Dataframe,
    # ... other params ...
    col_wrap: str | dict | list | Dataframe | Callable | None = None,
    # ...
):
    # Set default to singledispatch-based wrapper
    if not col_wrap:
        col_wrap = config.col_wrap if config.col_wrap is not None else wrap_column

    # ... rest of function ...
```

Update `_col_wrap()` helper to handle Callable:

```python
def _col_wrap(
    cw: None | str | tuple[str, str] | dict[type, tuple[str, str]] | Callable,
    value: Any,
    col_index: int = 0,  # Add col_index parameter
) -> tuple[str, str]:
    if not cw:
        return ("", "")

    if callable(cw):
        return cw(value, col_index)  # Call with value and col_index

    if isinstance(cw, str):
        return cw, ""

    if isinstance(cw, tuple):
        return cw

    if isinstance(cw, dict):
        for type_, col_wraps in cw.items():
            if isinstance(value, type_):
                return col_wraps

    return ("", "")
```

Update call site in show_eqn (line 404):

```python
# Before:
cell_content = f"{_col_wrap(cw, v)[0]}{formatted_value}{_col_wrap(cw, v)[-1]}"

# After:
cell_content = f"{_col_wrap(cw, v, col_idx)[0]}{formatted_value}{_col_wrap(cw, v, col_idx)[-1]}"
```

### 4. Configuration Update

No TOML configuration needed (col_wrap is a callable, same as cell_formatters). Default is handled programmatically in show_eqn().

## Implementation Steps

1. **Create col_wrapper.py module**
   - Implement singledispatch `wrap_column()` function
   - Register handlers for: int, float, str, Basic
   - Register optional handlers for: pint.Quantity, Markdown, Latex
   - Add comprehensive docstrings with examples

2. **Refactor formatters.py**
   - Remove all `= ` and `\quad` prefix logic from formatters
   - Simplify each formatter to pure type conversion
   - Update docstrings to reflect "no decoration" behavior
   - Keep `col_index` parameter for API consistency (backwards compatibility)

3. **Update display.py**
   - Import `wrap_column` from new col_wrapper module
   - Update `_col_wrap()` signature to accept `col_index`
   - Add Callable branch to `_col_wrap()` for singledispatch support
   - Update default `col_wrap` in `show_eqn()` to use `wrap_column`
   - Update call site (line 404) to pass `col_idx` to `_col_wrap()`

4. **Update __init__.py exports**
   - Export `wrap_column` from main module for user extensibility
   - Add to public API documentation

5. **Update tests**
   - Test formatters return pure LaTeX (no prefixes)
   - Test `wrap_column()` dispatches correctly by type
   - Test `col_index` behavior (0 vs 1+)
   - Test user override scenarios:
     - List form: `[None, "=", r"\approx"]`
     - Callable form: custom wrapper function
     - Dict form: type-based wrapping
   - Test edge cases: None values, mixed types, custom types

6. **Update documentation**
   - CLAUDE.md: Update architecture section for col_wrap system
   - Docstrings: Update `show_eqn()` col_wrap parameter description
   - Examples: Add cookbook for custom col_wrap scenarios
   - Migration guide: Note for users with custom formatters

## Benefits

### Separation of Concerns
- **Formatters**: Pure type conversion (Python → LaTeX string)
- **Col Wrap**: Column decoration (LHS/RHS syntax)
- Clear boundary: formatters handle "what", col_wrap handles "how presented"

### User Flexibility
```python
# Simple list override (no function definition needed)
show_eqn(data, col_wrap=[None, "= ", r"\leq "])

# Callable for advanced logic
def custom_wrap(value, col_index):
    if col_index == 0:
        return ("", "")
    return (r"\approx ", "") if isinstance(value, float) else ("= ", "")

show_eqn(data, col_wrap=custom_wrap)

# Register custom type
@wrap_column.register(MyCustomType)
def wrap_custom(value, col_index=0, **kwargs):
    return (">>> ", "") if col_index > 0 else ("", "")
```

### Extensibility
- All comparison operators naturally fit: `=`, `\leq`, `\geq`, `\approx`
- Future enhancements (units display, approximations) fit in col_wrap
- User registration via `@wrap_column.register()` pattern

### Consistency
- Same singledispatch pattern as cell formatters
- Formatters are pure type converters (stable, less customization needed)
- All "between LHS and RHS" syntax lives in one place

## Breaking Changes

### User Impact
- **Custom formatters** that rely on `= ` prefix behavior will need updates
- **Expected**: Minimal impact (most users don't customize formatters)
- **Default behavior**: Unchanged for typical use cases

### Migration Path
1. Users with custom formatters should remove prefix logic:
   ```python
   # Before (custom formatter):
   @format_value.register(MyType)
   def format_mytype(value, col_index=0):
       prefix = "= " if col_index > 0 else ""
       return f"{prefix}{value.to_latex()}"

   # After (custom formatter):
   @format_value.register(MyType)
   def format_mytype(value, col_index=0):
       return value.to_latex()  # Pure conversion

   # If custom prefix needed, use col_wrap instead:
   @wrap_column.register(MyType)
   def wrap_mytype(value, col_index=0):
       return ("= ", "") if col_index > 0 else ("", "")
   ```

2. Document in CHANGELOG with migration examples

### Version Bump
- This is a **breaking change** → v1.0.0 (major version per pyproject.toml)
- Current version: 1.0.0b3 → 1.0.0 release candidate

## Testing Strategy

### Unit Tests
- `tests/test_col_wrap_formatter.py`: Test singledispatch behavior
- `tests/test_formatters.py`: Verify pure conversion (no prefixes)
- `tests/test_display.py`: Integration testing with show_eqn

### Integration Tests
- Test default behavior matches current output (for non-custom cases)
- Test list override: `[None, "=", r"\approx"]`
- Test callable override with custom logic
- Test user registration of custom types

### Regression Tests
- Ensure existing notebooks render identically (default behavior)
- Verify engineering verification (`check()` function) still works

## Documentation Updates

### CLAUDE.md
- Update "Core Components" → "Display Module" section
- Add "Col Wrap System" subsection with singledispatch explanation
- Update "Formatters Module" to emphasize pure conversion

### Docstrings
- Update `show_eqn()` col_wrap parameter with new examples
- Add comprehensive docstring to `wrap_column()`
- Update formatter docstrings to remove prefix references

### Examples
- Add cookbook section: "Custom Column Decorations"
- Show list form, callable form, and registration examples
- Engineering-focused examples: verification checks with `\leq`

## Risks and Mitigations

### Risk: Implementation Complexity
- **Mitigation**: Follow existing singledispatch pattern from formatters.py
- **Mitigation**: Comprehensive unit tests before integration

### Risk: Performance Overhead
- **Concern**: Extra function call per column
- **Mitigation**: Python singledispatch is highly optimized (C implementation)
- **Impact**: Negligible (one dispatch per cell, not per equation)

### Risk: User Confusion
- **Concern**: Users may not know where to look for `= ` behavior
- **Mitigation**: Clear docstrings pointing to col_wrap_formatter.py
- **Mitigation**: Migration guide in CHANGELOG
- **Mitigation**: Examples showing both formatters and col_wrap

## Success Criteria

1. ✅ All formatters are pure type converters (no prefix logic)
2. ✅ Default behavior unchanged for typical users
3. ✅ `wrap_column()` singledispatch handles all built-in types
4. ✅ List override works: `col_wrap=[None, "=", r"\leq"]`
5. ✅ Callable override works with custom logic
6. ✅ User registration works: `@wrap_column.register(MyType)`
7. ✅ All existing tests pass
8. ✅ Documentation updated (CLAUDE.md, docstrings, examples)
9. ✅ No regression in existing notebook rendering

## Timeline Estimate

- **Module creation** (col_wrap_formatter.py): 1-2 hours
- **Formatter refactoring**: 30 minutes
- **display.py integration**: 1 hour
- **Configuration updates**: 30 minutes
- **Testing**: 2-3 hours
- **Documentation**: 1-2 hours

**Total**: ~6-9 hours of focused development time

---

## Approval Checkpoint

**Status**: ⏸️ Awaiting user review and approval

**Decisions (from annotations)**:
1. ✅ `col_index` stays in formatter signatures (for custom formatter flexibility)
2. ✅ Export `wrap_column` in `__init__.py` (user extensibility)
3. ✅ Module name: `col_wrapper.py` (not col_wrap_formatter.py)
4. ✅ No TOML config (callable, same pattern as cell_formatters)

**Status**: ✅ Approved - Ready to implement
