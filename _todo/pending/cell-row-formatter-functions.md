# Cell and Row Formatter Functions for show_eqn()

## Original Objective (from todo.md)

Add two new arguments to `show_eqn()`:

- `apply_to_cell`: Apply func formatter to each cell
- `apply_to_row`: Apply func formatter to each row, after the row has been formed

This feature replaces the current hardcoded `myprint_latex` function with a flexible, user-configurable cell formatting system. Users will be able to pass custom formatting functions that control how each cell or entire row is rendered.

**Key Requirement**: This task supersedes `_todo/proposal/improving-myprint-latex.md`.

## Problem Analysis

### Current Limitations

The current implementation at `display.py:463-489` has these issues:

1. **Hardcoded cell formatting**: `myprint_latex()` is directly called with no user control
2. **Type handling inflexibility**: Only Markdown and SymPy Basic types supported
3. **No column-specific formatting**: Same formatter applied to all columns
4. **No row-level transformations**: Cannot apply formatting to complete generated rows
5. **Limited extensibility**: Users must modify keecas source to add custom formatters

### Current Code Structure (display.py:463-489)

```python
body_lines = {}
for key, list_values in eqns.items():
    body_lines[key] = " ".join(
        [
            format_decimal_numbers(
                f'{ f"{_col_wrap(cw,v)[0]}{myprint_latex(v, **latex_kwargs)}{_col_wrap(cw, v)[-1]}" if v is not None else " " } {s}',
                ff,
            )
            for v, s, cw, ff in zip_longest(
                ([key] + list_values),
                sep,
                col_wrap[key],
                float_format[key],
                fillvalue="",
            )
        ]
    ) + _attach_label(label, key, label_command)
```

**Critical insight**: Each cell goes through: `col_wrap` → `myprint_latex` → `format_decimal_numbers`

## Proposed Solution: Two-Level Formatter System

### Architecture Overview

```
Input Data → apply_to_cell (per-cell) → Row Assembly → apply_to_row (per-row) → LaTeX Output
```

### 1. Cell-Level Formatting (`apply_to_cell`)

**Purpose**: Transform individual cell values before row assembly

**Type Signature**:
```python
apply_to_cell: Callable | dict[Hashable, Callable] | list[dict[Hashable, Callable]] | Dataframe | tuple | None
```

**Processing Logic**:
- Converted to `Dataframe` using `create_dataframe()` utility
- Applied during cell generation loop (replaces `myprint_latex`)
- Receives raw cell value, returns LaTeX string
- Tuple form `(formatters, default)` provides default formatter

**Application Point**: Within the `zip_longest` loop at `display.py:471-477`

### 2. Row-Level Formatting (`apply_to_row`)

**Purpose**: Transform complete assembled rows before final output

**Type Signature**:
```python
apply_to_row: Callable | dict[Hashable, Callable] | None
```

**Processing Logic**:
- Applied to `body_lines[key]` after row assembly
- Cannot use Dataframe (operates on complete rows)
- Dict form allows key-specific row transformations
- Callable form applies same transformation to all rows

**Application Point**: After row assembly at `display.py:479`, before joining

## Detailed Implementation Plan

### Phase 1: Extensible Default Formatter with Registry

Create a **unified default formatter** that:
- Takes both `value` and `col_index` as parameters
- Uses an extensible registry system with priority-based type matching
- First matching type wins
- Users can extend via decorators or runtime registration

#### 1.1 Formatter Registry Implementation

**Location**: Create new file `src/keecas/formatters.py` for all formatter-related code.

```python
from typing import Callable, Any, TypeVar

T = TypeVar('T')
FormatterFunc = Callable[[Any, int], str]  # (value, col_index) -> str

class CellFormatterRegistry:
    """Extensible registry for type-based cell formatters with priority ordering."""

    def __init__(self):
        # Use regular dict (Python 3.7+ preserves insertion order)
        self._formatters: dict[tuple[type, int], tuple[FormatterFunc, int]] = {}
        self._load_defaults()

    def register(self, type_class: type[T], formatter: FormatterFunc, priority: int = 50) -> None:
        """Register a formatter for a type with priority (lower = higher priority).

        Args:
            type_class: Type to match with isinstance()
            formatter: Function(value, col_index) -> str
            priority: Lower values = higher priority (0-100, default 50)
        """
        # Insert maintaining priority order
        key = (type_class, id(formatter))
        self._formatters[key] = (formatter, priority)
        # Re-sort by priority
        self._formatters = dict(
            sorted(self._formatters.items(), key=lambda x: x[1][1])
        )

    def format(self, value: Any, col_index: int) -> str:
        """Format value using first matching type formatter."""
        for (type_class, _), (formatter, _) in self._formatters.items():
            if isinstance(value, type_class):
                return formatter(value, col_index)

        # Ultimate fallback - always return LaTeX-compatible output
        return latex(value)

    def _load_defaults(self):
        """Load built-in formatters."""
        # Priority 10: Specific types first
        self.register(Markdown, self._format_markdown, priority=10)
        self.register(pint.Quantity, self._format_pint, priority=15)

        # Priority 30: SymPy types (broader match)
        self.register(sympy.Basic, self._format_sympy, priority=30)

        # Priority 70: Python built-ins (fallback)
        self.register(float, self._format_float, priority=70)
        self.register(int, self._format_int, priority=70)
        self.register(str, self._format_str, priority=70)

    def _format_markdown(self, value: Markdown, col_index: int) -> str:
        """Format Markdown objects."""
        if col_index == 0:
            return rf"\text{{{value.data}}}"
        else:
            return rf"\quad\text{{{value.data}}}"

    def _format_pint(self, value: pint.Quantity, col_index: int) -> str:
        """Format Pint quantities."""
        latex_str = latex(S(value))
        if col_index == 0:
            return latex_str
        else:
            return f"= {latex_str}"

    def _format_sympy(self, value: sympy.Basic, col_index: int) -> str:
        """Format SymPy expressions."""
        latex_str = latex(value)
        if col_index == 0:
            return latex_str
        else:
            return f"= {latex_str}"

    def _format_float(self, value: float, col_index: int) -> str:
        """Format Python floats."""
        if col_index == 0:
            return str(value)
        else:
            return f"= {value}"

    def _format_int(self, value: int, col_index: int) -> str:
        """Format Python integers."""
        if col_index == 0:
            return str(value)
        else:
            return f"= {value}"

    def _format_str(self, value: str, col_index: int) -> str:
        """Format Python strings."""
        if col_index == 0:
            return rf"\text{{{value}}}"
        else:
            return rf"\quad\text{{{value}}}"


# Global default registry
default_cell_formatter_registry = CellFormatterRegistry()
```

#### 1.2 Decorator for User Extensions

```python
def cell_formatter(type_class: type[T], priority: int = 50):
    """Decorator to register custom cell formatters.

    Usage:
        @cell_formatter(MyClass, priority=20)
        def format_my_class(value: MyClass, col_index: int) -> str:
            return f"custom: {value}"
    """
    def decorator(func: FormatterFunc) -> FormatterFunc:
        default_cell_formatter_registry.register(type_class, func, priority)
        return func
    return decorator
```

#### 1.3 Default Formatter Function

```python
def default_cell_formatter(value: Any, col_index: int) -> str:
    """Default cell formatter using the global registry.

    Args:
        value: Cell value to format
        col_index: Column index (0 = first column/LHS, 1+ = RHS columns)

    Returns:
        LaTeX string representation
    """
    return default_cell_formatter_registry.format(value, col_index)
```

**Key advantages**:
- Single formatter function with column-aware behavior
- Extensible via decorator or runtime registration
- Priority-based type matching (first to match wins)
- Users can override at function call or extend globally

### Phase 2: Configuration Integration

Add to `config.py`:

```python
class DisplayConfig:
    # Existing fields...
    cell_formatter: Callable[[Any, int], str] | None = None  # Override default formatter
    row_formatter: Callable[[str], str] | None = None  # Default row transformer
```

**Runtime API for extending the default registry**:

```python
# Users extend the global registry with custom types
from keecas import cell_formatter, default_cell_formatter_registry

# Option 1: Decorator
@cell_formatter(np.ndarray, priority=20)
def format_numpy(arr: np.ndarray, col_index: int) -> str:
    return matrix_to_latex(arr)

# Option 2: Direct registration
def format_my_type(value: MyType, col_index: int) -> str:
    return f"custom: {value}"

default_cell_formatter_registry.register(MyType, format_my_type, priority=25)

# Option 3: Override global default in config
config.display.cell_formatter = my_custom_formatter
```

**Note**: TOML configuration for formatters is not feasible (can't serialize functions). Users extend via Python runtime API.

**User Config File Support**:
Users can create custom formatter files in config directories:
- **Global**: `~/.keecas/formatters.py`
- **Local**: `<project>/.keecas/formatters.py`

These files are automatically imported at startup if they exist. Users can define custom formatters:

```python
# ~/.keecas/formatters.py
from keecas import cell_formatter
import numpy as np

@cell_formatter(np.ndarray, priority=20)
def my_numpy_formatter(arr, col_index):
    return matrix_to_latex(arr)
```

Add to `config.py`:
```python
class KeecasConfig:
    # Existing fields...
    custom_formatters_file: str | None = None  # Override default formatter file path
```

This follows best practice for user extensions:
- **Convention over configuration**: Standard file locations
- **Explicit imports**: No magic, clear what's happening
- **Override capability**: Config option for custom paths

### Phase 3: Modified show_eqn() Signature

```python
def show_eqn(
    eqn: InputTypes = None,
    *,
    # ... existing parameters ...
    cell_formatter: Callable | dict[Hashable, Callable] | list[dict[Hashable, Callable]] | Dataframe | tuple | None = None,
    row_formatter: Callable | dict[Hashable, Callable] | None = None,
    # ... remaining parameters ...
) -> Markdown:
```

**Parameter semantics**:
- `cell_formatter`: Applied to each cell value. Signature: `(value, col_index) -> str`
- `row_formatter`: Applied to complete assembled rows. Signature: `(row_latex_str) -> str`

### Phase 4: Implementation Logic

#### Step 4.1: Process `cell_formatter` into Dataframe

```python
# After determining keys and num_cols...

# Step 1: Determine default if not provided
if cell_formatter is None:
    cell_formatter = config.display.cell_formatter or default_cell_formatter

# Step 2: Create Dataframe (single line, matching float_format pattern)
cell_formatters = create_dataframe(
    seed=cell_formatter if not isinstance(cell_formatter, tuple) else cell_formatter[0],
    default_value=default_cell_formatter if not isinstance(cell_formatter, tuple) else cell_formatter[1],
    keys=keys,
    width=num_cols,
)
```

**Key insight**:
- Two-step process like other parameters: determine default, then convert
- Single `Callable` → used for all cells
- Tuple `(formatters, default)` → custom default fallback
- Dataframe/dict/list → per-column/per-row-key customization

#### Step 4.2: Apply Cell Formatters in Loop

```python
body_lines = {}
for key, list_values in eqns.items():
    # Generate cells with custom formatters
    cells = []
    for col_idx, (v, s, cw, ff, cf) in enumerate(zip_longest(
        ([key] + list_values),
        sep,
        col_wrap[key],
        float_format[key],
        cell_formatters[key],  # Add to zip_longest
        fillvalue="",
    )):
        # Apply formatter with column index
        if v is not None:
            formatted_value = cf(v, col_idx)  # cf = cell formatter from zip_longest
            cell_content = f"{_col_wrap(cw,v)[0]}{formatted_value}{_col_wrap(cw, v)[-1]}"
        else:
            cell_content = " "

        # Apply float formatting
        cell_content = format_decimal_numbers(f"{cell_content} {s}", ff)
        cells.append(cell_content)

    # Join cells to form row
    body_lines[key] = " ".join(cells) + _attach_label(label, key, label_command)
```

**Critical changes**:
- Add `cell_formatters[key]` to `zip_longest` (parallel to other parameters)
- Remove unnecessary length checking (Dataframe already correct size)
- Formatters receive `(value, col_idx)` instead of just `(value)`

#### Step 4.3: Apply Row Formatters

```python
# After assembling all rows, apply row-level transformations
if row_formatter is not None:
    if callable(row_formatter):
        # Single function for all rows
        body_lines = {k: row_formatter(v) for k, v in body_lines.items()}
    elif isinstance(row_formatter, dict):
        # Key-specific row formatters (dict keys = symbol keys)
        body_lines = {
            k: row_formatter.get(k, lambda x: x)(v)
            for k, v in body_lines.items()
        }
elif config.display.row_formatter is not None:
    # Use config default if available
    row_func = config.display.row_formatter
    body_lines = {k: row_func(v) for k, v in body_lines.items()}
```

**Note**: Dict keys use symbols (matches Dataframe pattern per user request).

### Phase 5: Remove myprint_latex

**Breaking change**: `myprint_latex` is removed entirely. Users should:
- Use `default_cell_formatter` as direct replacement
- Or implement custom formatters

```python
# Before (old code):
myprint_latex(expr)

# After (new code):
default_cell_formatter(expr, col_index=0)

# Or create custom formatter
@cell_formatter(MyType, priority=20)
def format_my_type(value: MyType, col_index: int) -> str:
    return latex(value)
```

## Usage Examples

### Example 1: Default Behavior (Uses Registry)

```python
from keecas import show_eqn

# Use built-in default formatter (registry-based)
show_eqn([_p | _e, _v])  # Automatically handles all types
```

### Example 2: Extend Global Registry

```python
from keecas import cell_formatter
import numpy as np

# Add custom type support globally
@cell_formatter(np.ndarray, priority=20)
def format_numpy(arr: np.ndarray, col_index: int) -> str:
    if col_index == 0:
        return rf"\mathbf{{A}}"  # Bold matrix symbol in LHS
    else:
        rows = [" & ".join(map(str, row)) for row in arr]
        return rf"= \begin{{bmatrix}} {' \\\\ '.join(rows)} \end{{bmatrix}}"

# Now numpy arrays work automatically
A = symbols("A")
_p = {A: np.array([[1, 2], [3, 4]])}
show_eqn(_p)  # Formats numpy array with custom formatter
```

### Example 3: Custom Cell Formatter with Column Logic

```python
def custom_cell_formatter(value, col_index: int) -> str:
    """Add custom styling based on value and column."""
    if isinstance(value, pint.Quantity) and value.magnitude > 1000:
        latex_str = latex(S(value))
        if col_index == 0:
            return rf"\mathbf{{{latex_str}}}"  # Bold large values in LHS
        else:
            return rf"= \mathbf{{{latex_str}}}"  # Bold with equals

    # Fallback to default
    return default_cell_formatter(value, col_index)

show_eqn([_p | _e, _v], cell_formatter=custom_cell_formatter)
```

### Example 4: Per-Column Formatters with Dataframe

```python
def lhs_formatter(value, col_index: int) -> str:
    """Custom formatter for LHS column."""
    return rf"\boxed{{{latex(value)}}}"  # Boxed symbols

def rhs_formatter(value, col_index: int) -> str:
    """Custom formatter for RHS column."""
    return rf"\Rightarrow {latex(value)}"  # Custom arrow

# Different formatters per column using list
# List creates Dataframe where:
#   lhs_formatter → column 0
#   rhs_formatter → column 1
show_eqn(
    [_p | _e, _v],
    cell_formatter=[lhs_formatter, rhs_formatter]
)
```

### Example 5: Row-Level Transformations

```python
def highlight_row(row_latex: str) -> str:
    """Add highlighting to specific rows."""
    return rf"\colorbox{{yellow}}{{{row_latex}}}"

# Apply to specific rows by symbol key
sigma = symbols(r"\sigma")
show_eqn(
    [_p | _e, _v],
    row_formatter={sigma: highlight_row}  # Highlight sigma row only
)
```

### Example 6: Configuration-Based Global Defaults

```python
# Set project-wide default via config
def project_formatter(value, col_index: int) -> str:
    """Project-specific formatting."""
    if col_index == 0:
        return rf"\underline{{{latex(value)}}}"  # Underline LHS
    else:
        return rf"\Rightarrow {latex(value)}"  # Custom arrow

config.display.cell_formatter = project_formatter

# All subsequent show_eqn() calls use this default
show_eqn([_p | _e, _v])  # Uses project_formatter
```

### Example 7: Engineering-Specific Type Handling

```python
# Add engineering unit preferences to global registry
@cell_formatter(pint.Quantity, priority=15)
def engineering_quantity_formatter(value: pint.Quantity, col_index: int) -> str:
    """Convert to preferred engineering units."""
    if value.dimensionality == "[length]":
        value = value.to("mm")
    elif value.dimensionality == "[force]":
        value = value.to("kN")

    latex_str = latex(S(value))
    if col_index == 0:
        return latex_str
    else:
        return f"= {latex_str}"

# Now all Pint quantities use engineering units
show_eqn([_p | _e, _v])  # Automatic unit conversion
```

## Benefits of This Design

### 1. Extensibility via Registry
- **Global type registration**: Add custom types once, use everywhere
- **Priority-based matching**: Control formatter precedence (first match wins)
- **Decorator pattern**: Simple `@cell_formatter(Type)` syntax
- **No source modification**: Extend keecas without touching internals

### 2. Column-Aware Formatting
- **Single formatter function**: Receives both value and `col_index`
- **LHS/RHS logic**: Different rendering based on column position
- **Context-sensitive**: Format decisions use column information

### 3. Flexible Per-Call Overrides
- **Function-level**: Pass custom formatter per `show_eqn()` call
- **Column-specific**: Different formatters per column via Dataframe
- **Row-specific**: Transform complete rows with `row_formatter`
- **Symbol-keyed dicts**: Precise control using symbol keys

### 4. Configuration Hierarchy
- **Runtime config**: `config.display.cell_formatter` for project defaults
- **Global registry**: Extend default formatter for all future calls
- **Per-call override**: Explicit formatter parameter takes precedence

### 5. Clean Breaking Change
- **No backward compatibility burden**: Major version allows clean slate
- **Simpler implementation**: No legacy code paths
- **Clear migration**: `myprint_latex` → `default_cell_formatter`

## Implementation Checklist

### Phase 0: User Config File Auto-Import
- [ ] Create `src/keecas/formatters.py` module
- [ ] Implement auto-import logic in `__init__.py`:
  - [ ] Check for `~/.keecas/formatters.py`
  - [ ] Check for `<project>/.keecas/formatters.py`
  - [ ] Import if exists (use `importlib`)
  - [ ] Handle import errors gracefully
- [ ] Add `custom_formatters_file` to `KeecasConfig`
- [ ] Support explicit path override via config

### Core Implementation
- [ ] Implement `CellFormatterRegistry` class with priority-based type matching in `formatters.py`
- [ ] Create `default_cell_formatter_registry` global instance
- [ ] Implement built-in formatters for: Markdown, pint.Quantity, sympy.Basic, float, int, str
- [ ] Create `default_cell_formatter(value, col_index)` function
- [ ] Implement `@cell_formatter` decorator for user extensions
- [ ] Add `cell_formatter` parameter to `show_eqn()`
- [ ] Add `row_formatter` parameter to `show_eqn()`
- [ ] Implement Dataframe conversion for `cell_formatter` parameter (two-step: default, then convert)
- [ ] Modify cell generation loop: add `cell_formatters[key]` to `zip_longest`
- [ ] Modify cell generation loop: pass `(value, col_idx)` to formatters
- [ ] Implement row-level formatter application
- [ ] Remove `myprint_latex` function entirely

### Configuration
- [ ] Add `cell_formatter: Callable[[Any, int], str] | None` to `DisplayConfig`
- [ ] Add `row_formatter: Callable[[str], str] | None` to `DisplayConfig`
- [ ] Add `custom_formatters_file: str | None` to `KeecasConfig`
- [ ] Implement config → formatter resolution hierarchy
- [ ] Document runtime API for registry extension

### Testing
- [ ] Test registry type matching (isinstance behavior)
- [ ] Test priority-based formatter selection
- [ ] Test default formatter with all built-in types
- [ ] Test decorator-based registration
- [ ] Test `col_index` parameter passing
- [ ] Test custom cell formatters (Callable, dict, list, Dataframe, tuple)
- [ ] Test row formatters (callable, dict with symbol keys)
- [ ] Test tuple form with default values
- [ ] Test configuration-based defaults (`config.display.cell_formatter`)
- [ ] Test edge cases (empty rows, None values, mixed types)
- [ ] Test Dataframe conversion edge cases

### Documentation
- [ ] Update `show_eqn()` docstring
- [ ] Add formatter function examples
- [ ] Update CONVENTIONS.md with formatter patterns
- [ ] Add to CLAUDE.md under "Key Design Patterns"
- [ ] Create example notebook: `examples/custom_formatters.ipynb`
- [ ] Update README with formatter feature

### Examples
- [ ] Basic column-specific formatting
- [ ] Custom type handling
- [ ] Engineering calculations with unit conversion
- [ ] Row highlighting and conditional formatting
- [ ] Configuration-based project defaults

## Migration Path from improving-myprint-latex Proposal

The previous proposal focused on a **type-based registry system** with decorators. This revised proposal **keeps the registry system** but adds **column-awareness** and **flexible overrides**.

**Core Approach (Registry + Column Index)**:
```python
# Global extension via decorator
@cell_formatter(np.ndarray, priority=20)
def format_numpy(arr, col_index):
    if col_index == 0:
        return rf"\mathbf{{A}}"
    else:
        return matrix_to_latex(arr)

# All future calls automatically use this formatter
show_eqn([_p | _e, _v])  # numpy arrays formatted automatically
```

**Per-Call Override**:
```python
# Custom formatter for specific call
def my_formatter(value, col_index):
    if isinstance(value, np.ndarray):
        return matrix_to_latex(arr)
    return default_cell_formatter(value, col_index)

show_eqn(..., cell_formatter=my_formatter)
```

### Key Improvements from Original Proposal

1. **Column-aware formatters**: `(value, col_index)` signature enables LHS/RHS logic
2. **Both global and local**: Registry for project-wide, parameter for per-call
3. **Simpler registration**: Just `dict` (not OrderedDict), Python 3.7+ ordering
4. **Fallback to latex()**: Always produce LaTeX-compatible output
5. **User config files**: `~/.keecas/formatters.py` for persistent custom formatters
6. **Clean implementation split**: New `formatters.py` module

## Design Decisions (User Feedback Incorporated)

### ✅ Confirmed Design Choices

1. **Extensible Registry with col_index**
   - Default formatter takes `(value, col_index)` parameters
   - Priority-based type matching (first to match wins)
   - Users extend via decorator or runtime registration
   - **Status**: Implemented in Phase 1

2. **TOML Configuration**
   - Not feasible for function serialization
   - Use runtime API only (`@cell_formatter`, direct registration)
   - **Status**: Documented in Phase 2

3. **Parameter Naming**
   - `cell_formatter` (not `apply_to_cell`)
   - `row_formatter` (not `apply_to_row`)
   - **Status**: Updated throughout proposal

4. **Always Convert to Dataframe**
   - Performance negligible for document rendering
   - Consistency more important than micro-optimization
   - **Status**: Implemented in Phase 4.1

5. **Row Formatter Dict Uses Symbol Keys**
   - Matches Dataframe pattern
   - More intuitive for keecas users
   - **Status**: Implemented in Phase 4.3

## Estimated Timeline

- **Phase 0** (User Config File Auto-Import): 0.5 days
  - Create `formatters.py` module
  - Auto-import logic in `__init__.py`
  - Config file path support
- **Phase 1** (Registry + Default Formatters): 1 day
  - CellFormatterRegistry class
  - Built-in type formatters
  - Decorator implementation
- **Phase 2** (Configuration): 0.5 days
  - DisplayConfig updates
  - Runtime API documentation
  - KeecasConfig updates
- **Phase 3** (show_eqn Signature): 0.25 days
  - Parameter additions
- **Phase 4** (Implementation Logic): 1.5 days
  - Dataframe conversion (two-step)
  - Cell generation loop modifications (add to zip_longest)
  - Row formatter application
- **Phase 5** (Remove myprint_latex): 0.25 days
  - Code removal
  - Migration guide
- **Testing**: 1.5 days
  - Registry testing
  - Priority system testing
  - Auto-import testing
  - Integration testing
- **Documentation & Examples**: 1 day
  - Docstrings
  - Example notebooks
  - CLAUDE.md updates
  - User config file examples

**Total**: ~6.5 days

---

## Summary of Key Changes from User Feedback

1. **Unified default formatter with registry** instead of separate `first_column_formatter`/`second_column_formatter`
2. **Column index parameter** added to all formatter functions: `(value, col_index) -> str`
3. **Extensible via decorator** using `@cell_formatter(Type, priority=N)`
4. **Parameter renamed** from `apply_to_cell`/`apply_to_row` to `cell_formatter`/`row_formatter`
5. **Always convert to Dataframe** for consistency (performance non-issue)
6. **Symbol keys for row_formatter** dict (matches keecas philosophy)
7. **User config files** for persistent formatters: `~/.keecas/formatters.py` (auto-imported)
8. **New formatters.py module** - separate file for all formatter code
9. **Regular dict** instead of OrderedDict (Python 3.7+ preserves order)
10. **Simplified cell loop** - add `cell_formatters[key]` to `zip_longest`
11. **Two-step parameter processing** - determine default, then convert to Dataframe
12. **Clean breaking change** - remove `myprint_latex` entirely (no backward compatibility)

---

**Status**: ✅ APPROVED - Implementation in progress

**Supersedes**: `_todo/proposal/improving-myprint-latex.md`

**Estimated Effort**: ~6.5 days

---

## Implementation Progress

### Session 1: 2025-10-02

**Proposal Phase**:
- ✅ Created detailed proposal with user feedback
- ✅ Revised proposal based on inline comments:
  - Added `formatters.py` module
  - Changed OrderedDict → dict
  - Added user config file auto-import
  - Simplified parameter processing
  - Fixed example code
- ✅ Proposal approved by user
- ✅ Moved to pending/

**Implementation Phase**:
- ✅ Created feature branch: `feature/cell-row-formatters`
- ✅ **Phase 0**: Created `src/keecas/formatters.py` module
  - Implemented `CellFormatterRegistry` with priority-based type matching
  - Created `default_cell_formatter_registry` global instance
  - Implemented built-in formatters for: Markdown, Pint, SymPy, float, int, str
  - Created `default_cell_formatter(value, col_index)` function
  - Implemented `@cell_formatter` decorator for user extensions
  - Added auto-import logic in `__init__.py` for user config files:
    - `~/.keecas/formatters.py` (global)
    - `<project>/.keecas/formatters.py` (local)
    - Custom path via `config.custom_formatters_file`
- ✅ **Phase 2**: Updated configuration
  - Added `cell_formatter` to `DisplayConfig`
  - Added `row_formatter` to `DisplayConfig`
  - Added `custom_formatters_file` to `ConfigOptions`
- ✅ **Phase 3-4**: Updated `show_eqn()` function
  - Added `cell_formatter` and `row_formatter` parameters
  - Implemented Dataframe conversion for `cell_formatter` (two-step pattern)
  - Modified cell generation loop to use `zip_longest` with `cell_formatters[key]`
  - Formatters now receive `(value, col_idx)` parameters
  - Implemented row-level formatter application with dict support
- ✅ **Phase 5**: Removed `myprint_latex` function (breaking change)
  - Removed function from `display.py`
  - Updated docstring references
  - Removed unused `latex_kwargs` variable
- ✅ **Testing**: Updated all tests
  - Changed `test_myprint_latex` to `test_default_cell_formatter`
  - Updated test assertions to match new formatter output (adds `= ` prefix for RHS)
  - All 104 tests passing

**Next Steps**:
- Create example notebook demonstrating new formatter features
- Update CLAUDE.md documentation
- Test with actual notebook examples
