# Proposal: Refactor Formatters to Singledispatch

## Original Objective

Refactor the current formatters implementation to use a singledispatch approach:
- No need for `EarlyExit` class
- Preserve each formatter function signature (they may be used directly)
- Update docs and docstrings

## Current State Analysis

### Architecture Overview

The formatter system (in `src/keecas/formatters.py`) currently uses a **chain-of-responsibility pattern** with three key components:

1. **`EarlyExit` Sentinel Class** (lines 90-114)
   - Wraps formatted result strings
   - Signals the chain to stop processing and return immediately
   - Enables both transformer and terminal formatters

2. **`FormatterChain` Class** (lines 117-286)
   - Orchestrates execution of formatters in sequence
   - Handles three return semantics:
     - `EarlyExit(result)` → Stop and return result (terminal)
     - `Transformed value` → Pass to next formatter (transformer)
     - `None` → Skip to next formatter
   - Falls back to `sympy.latex()` if no formatter handles the value

3. **Seven Built-in Formatters** (lines 289-493)

| Formatter | Type | Input Type | Output |
|-----------|------|------------|--------|
| `format_markdown` | Terminal | `IPython.display.Markdown` | `EarlyExit(r"\text{...}")` |
| `format_pint` | Transformer | `pint.Quantity` | SymPy expression |
| `format_mul` | Transformer | SymPy `Mul` | Transformed `Mul` |
| `format_sympy` | Terminal | SymPy `Basic` | `EarlyExit(LaTeX)` |
| `format_float` | Terminal | `float` | `EarlyExit(formatted)` |
| `format_int` | Terminal | `int` | `EarlyExit(formatted)` |
| `format_str` | Terminal | `str` | `EarlyExit(r"\text{...}")` |

### Function Signatures

All formatters follow the same pattern:

```python
def formatter_name(
    value: Any,                    # The value to format
    col_index: int = 0,           # 0=LHS, 1+=RHS (affects formatting)
    **kwargs                       # Passed to latex() function
) -> EarlyExit | str | None:
```

### Current Usage

```python
# Static default chain
default_formatter_chain = FormatterChain([
    format_markdown,
    format_pint,      # Transformer: Pint → SymPy
    format_mul,       # Transformer: Numeric * Unit separation
    format_sympy,     # Terminal: SymPy → LaTeX
    format_float,     # Terminal fallback
    format_int,       # Terminal fallback
    format_str,       # Terminal fallback
])

# In show_eqn() (display.py)
formatted_value = cell_formatter(value, col_idx, **latex_kwargs)
```

## Proposed Refactoring: Singledispatch Approach

### Core Concept

Replace the chain-of-responsibility pattern with Python's `@singledispatch` decorator:
- **Type-based dispatch** replaces explicit ordering
- **No `EarlyExit` needed** - dispatches directly to the right formatter
- **Simpler mental model** - "what type do I have?" vs "what order should formatters run?"
- **Preserve function signatures** - formatters can still be called directly

### New Architecture

```python
from functools import singledispatch
from typing import Any
from sympy import Basic, latex

@singledispatch
def format_value(
    value: Any,
    col_index: int = 0,
    **kwargs
) -> str:
    """Format a value to LaTeX string.

    Dispatches based on value type to specialized formatters.
    Falls back to sympy.latex() for unhandled types.

    Args:
        value: Value to format (any type)
        col_index: Column index (0=LHS, 1+=RHS)
        **kwargs: Arguments passed to latex()

    Returns:
        LaTeX string representation

    Examples:
        >>> from keecas import symbols
        >>> x = symbols('x')
        >>> format_value(x)  # Dispatches to format_sympy
        'x'
        >>> format_value(3.14159, col_index=1, float_format=".2f")
        '= 3.14'
    """
    # Default fallback for unhandled types
    return latex(value, **kwargs)


@format_value.register(str)
def format_str(value: str, col_index: int = 0, **kwargs) -> str:
    """Format string values to LaTeX text."""
    return r"\text{" + value + "}"


@format_value.register(int)
def format_int(value: int, col_index: int = 0, **kwargs) -> str:
    """Format integer values."""
    if col_index == 0:
        return str(value)
    else:
        return f"= {value}"


@format_value.register(float)
def format_float(value: float, col_index: int = 0, **kwargs) -> str:
    """Format float values with optional precision."""
    float_format = kwargs.pop('float_format', None)
    if float_format:
        formatted = format(value, float_format.strip('{}:'))
    else:
        formatted = str(value)

    if col_index == 0:
        return formatted
    else:
        return f"= {formatted}"


# IPython Markdown
try:
    from IPython.display import Markdown

    @format_value.register(Markdown)
    def format_markdown(value: Markdown, col_index: int = 0, **kwargs) -> str:
        """Format Markdown objects to LaTeX text."""
        return r"\text{" + value.data + "}"
except ImportError:
    pass


# Pint Quantity (with transformation)
try:
    import pint
    from sympy import S

    @format_value.register(pint.Quantity)
    def format_pint(value: pint.Quantity, col_index: int = 0, **kwargs) -> str:
        """Format Pint quantities by converting to SymPy first."""
        sympy_expr = S(value)  # Transform to SymPy
        return format_value(sympy_expr, col_index, **kwargs)  # Recurse
except ImportError:
    pass


# SymPy Basic
@format_value.register(Basic)
def format_sympy(value: Basic, col_index: int = 0, **kwargs) -> str:
    """Format SymPy expressions to LaTeX."""
    latex_str = latex(value, **kwargs)
    if col_index == 0:
        return latex_str
    else:
        return f"= {latex_str}"
```

### Handling Transformers (Pint, Mul)

**Challenge**: Current system has "transformer" formatters that modify values before passing to the next formatter (e.g., `format_pint` converts Quantity → SymPy → dispatch to `format_sympy`).

**Solution**: Recursive dispatch within registered implementations:

```python
@format_value.register(pint.Quantity)
def format_pint(value: pint.Quantity, col_index: int = 0, **kwargs) -> str:
    """Format Pint quantities by converting to SymPy first."""
    sympy_expr = S(value)  # Transform
    return format_value(sympy_expr, col_index, **kwargs)  # Re-dispatch
```

This pattern replaces the chain's "return non-EarlyExit value" with explicit re-dispatch.

**For `format_mul`** (numeric * unit separation):

```python
from sympy import Mul

@format_value.register(Mul)
def format_mul(value: Mul, col_index: int = 0, **kwargs) -> str:
    """Format multiplication expressions with numeric/unit separation."""
    # Apply transformation logic (lines 414-447 in current implementation)
    transformed_value = _apply_mul_transformation(value)

    # Continue formatting the transformed expression
    latex_str = latex(transformed_value, **kwargs)

    if col_index == 0:
        return latex_str
    else:
        return f"= {latex_str}"
```

### Benefits

1. **Simpler Mental Model**
   - "What type is this?" vs "In what order should formatters run?"
   - Type-based dispatch is more intuitive than chain execution

2. **No Sentinel Class Needed**
   - `EarlyExit` eliminated entirely
   - Direct return of LaTeX strings from each formatter

3. **Better Type Safety**
   - Return type is always `str` (not `EarlyExit | str | None`)
   - Type checkers can verify correctness more easily

4. **Preserve Direct Callable Signatures**
   - Formatters remain individually callable: `format_float(3.14, col_index=1)`
   - Useful for testing and custom formatting pipelines

5. **Extensibility**
   - Users can register custom types: `@format_value.register(MyClass)`
   - No need to subclass or modify `FormatterChain`

6. **Standard Library Pattern**
   - Uses Python's built-in `singledispatch` (no custom classes)
   - Well-documented, widely understood pattern

### Trade-offs

#### Loss of Explicit Ordering

**Current System**:
```python
# Explicit order visible in definition
FormatterChain([format_pint, format_mul, format_sympy, ...])
```

**Singledispatch**:
```python
# Dispatch order determined by type hierarchy
# Pint → format_pint → (transforms to SymPy) → format_sympy
```

**Mitigation**: Document transformation chains clearly in docstrings:
```python
@format_value.register(pint.Quantity)
def format_pint(value, col_index=0, **kwargs):
    """Format Pint quantities.

    Transformation chain: Quantity → SymPy → format_sympy
    """
```

#### Loss of Runtime Chain Modification

**Current System**:
```python
# Users can modify chains in notebooks
chain = default_formatter_chain.copy()
chain.insert(0, my_formatter)
chain.move_down(format_sympy, 2)
```

**Singledispatch**:
- Cannot easily reorder dispatch at runtime
- Can register new types: `format_value.register(MyType)(my_formatter)`

**Mitigation**: This is acceptable since:
1. Type-based dispatch makes ordering less critical
2. Most users won't need runtime reordering
3. Custom types are still extensible via registration

## Implementation Plan

### Phase 1: Core Refactoring

1. **Create new singledispatch-based implementation** in `formatters.py`:
   ```python
   @singledispatch
   def format_value(value: Any, col_index: int = 0, **kwargs) -> str:
       """Main formatter with type-based dispatch."""
       return latex(value, **kwargs)

   # Register all built-in formatters as implementations
   @format_value.register(str)
   def format_str(...): ...

   @format_value.register(int)
   def format_int(...): ...
   # ... etc
   ```

2. **Preserve individual formatter functions**:
   - Keep `format_str`, `format_int`, `format_float`, etc. as named functions
   - They remain directly callable: `format_float(3.14, col_index=1)`
   - Update signatures to return `str` instead of `EarlyExit | str | None`

3. **Handle transformers via recursive dispatch**:
   - `format_pint`: Convert to SymPy, then call `format_value()` again
   - `format_mul`: Apply transformation, then format result

4. **Update `display.py`**:
   ```python
   # Old
   cell_formatter = config.display.cell_formatter or default_formatter_chain
   formatted_value = cell_formatter(value, col_idx, **latex_kwargs)

   # New
   cell_formatter = config.display.cell_formatter or format_value
   formatted_value = cell_formatter(value, col_idx, **latex_kwargs)
   ```

### Phase 2: Deprecation (Optional)

If we want to maintain backward compatibility for one release cycle:

1. **Keep `EarlyExit` and `FormatterChain` with deprecation warnings**:
   ```python
   import warnings

   class EarlyExit:
       def __init__(self, result):
           warnings.warn(
               "EarlyExit is deprecated. Use singledispatch formatters instead.",
               DeprecationWarning,
               stacklevel=2
           )
           self.result = result
   ```

2. **Add migration guide** to documentation

3. **Remove in next major version** (v2.0.0)

**However**: Since we're targeting v1.0.0 (breaking changes acceptable), we can skip deprecation and do a clean break.

### Phase 3: Documentation Updates

1. **Update `CLAUDE.md`**:
   - Remove `EarlyExit` and `FormatterChain` architecture description
   - Document singledispatch pattern
   - Show how to register custom formatters

2. **Update docstrings**:
   - `format_value`: Comprehensive main docstring with all supported types
   - Individual formatters: Minimal docstrings (per singledispatch best practice)
   - Document transformation chains (e.g., "Pint → SymPy → format_sympy")

3. **Update API reference** (`docs/api-reference/formatters.qmd`):
   - Remove `EarlyExit` from public API (if documented)
   - Add `format_value` as main entry point
   - Keep individual formatters documented (they're still directly callable)

4. **Add examples**:
   ```python
   # Basic usage
   from keecas import format_value
   format_value(3.14159, float_format=".2f")  # "3.14"

   # Custom type registration
   @format_value.register(MyCustomType)
   def format_custom(value, col_index=0, **kwargs):
       return r"\text{Custom: " + str(value) + "}"
   ```

### Phase 4: Testing

1. **Update existing tests** in `tests/test_formatters.py`:
   - Replace `EarlyExit` checks with direct string comparisons
   - Update `FormatterChain` tests to use `format_value` directly
   - Verify all formatters work via dispatch

2. **Add singledispatch-specific tests**:
   - Test custom type registration
   - Test transformation chains (Pint → SymPy)
   - Test col_index behavior across all types
   - Test kwargs propagation

3. **Integration tests**:
   - Verify `show_eqn()` works with new formatters
   - Test with Dataframe values (multiple types in one call)
   - Verify LaTeX output matches previous behavior

## Migration Path for Users

### Breaking Changes

1. **`EarlyExit` removed**: If users wrote custom formatters returning `EarlyExit`, they need to:
   ```python
   # Old
   def my_formatter(value, col_index=0, **kwargs):
       if isinstance(value, MyType):
           return EarlyExit(r"\text{...}")
       return None

   # New
   @format_value.register(MyType)
   def format_mytype(value, col_index=0, **kwargs):
       return r"\text{...}"
   ```

2. **`FormatterChain` removed**: If users created custom chains:
   ```python
   # Old
   custom_chain = FormatterChain([my_formatter, format_sympy, ...])
   show_eqn(eqns, cell_formatter=custom_chain)

   # New
   @format_value.register(MyType)
   def format_mytype(value, col_index=0, **kwargs):
       return r"\text{...}"

   show_eqn(eqns)  # Uses global dispatch registry
   ```

3. **Runtime chain modification not supported**:
   - Can no longer do `chain.insert(0, my_formatter)`
   - Must register types at module level

### Non-Breaking Changes

- Individual formatters (`format_float`, `format_int`, etc.) remain callable
- Signature stays the same: `format_float(value, col_index=0, **kwargs)`
- `show_eqn()` usage unchanged (default formatter "just works")

## Open Questions

1. **Should we keep `FormatterChain` for advanced users who need runtime chain modification?**
   - **Recommendation**: No - accept the trade-off for simpler codebase
   - Users needing custom logic can still create wrapper functions

2. **How do we handle `format_mul` transformer logic?**
   - **Option A**: Keep as `@format_value.register(Mul)` with inline transformation
   - **Option B**: Extract transformation to helper, then dispatch result
   - **Recommendation**: Option A (cleaner, fewer indirections)

3. **Should we export `format_value` or keep it internal?**
   - **Recommendation**: Export it - useful for testing and custom pipelines
   - Users can do: `from keecas import format_value; format_value(my_val)`

4. **Config integration - should `config.display.cell_formatter` change?**
   - **Current**: Accepts `Callable` or `FormatterChain`
   - **New**: Accepts `Callable` (which `format_value` is)
   - **Recommendation**: No schema change needed, just update default value

## Success Criteria

1. ✅ `EarlyExit` class removed from codebase
2. ✅ All formatters use `@singledispatch` pattern
3. ✅ Individual formatter functions remain directly callable
4. ✅ All existing tests pass (or updated to reflect new pattern)
5. ✅ Documentation updated (CLAUDE.md, docstrings, API reference)
6. ✅ `show_eqn()` behavior unchanged from user perspective
7. ✅ Custom type registration works and is documented

## Estimated Effort

- **Core refactoring**: 2-3 hours
- **Testing updates**: 1-2 hours
- **Documentation**: 1-2 hours
- **Total**: ~5-7 hours of development time

## Recommendation

**Proceed with refactoring** - the singledispatch pattern is:
- More Pythonic (standard library pattern)
- Simpler (no custom sentinel class)
- Better typed (direct `str` returns)
- Sufficient for current needs (type-based dispatch handles all use cases)

The loss of runtime chain modification is acceptable given:
- Not commonly needed by users
- Type registration still allows extensibility
- Simpler mental model outweighs flexibility loss

---

**Awaiting user approval to proceed with implementation.**
