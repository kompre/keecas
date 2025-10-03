# Improving myprint_latex

## Original Objective (from show_eqn refactor)

I want to implement a function that will apply a formatting function based on type. User should be able to provide their own printer function, or rather their own `Dataframe` of function, similar as the `col_wrap` works right now.

The current `myprint_latex` supports only Markdown objects and sympy objects, with the cases being hardcoded.

Ideally the printer function will have an ordered sequence like a dict, where to a type is associated a formatting function. First type to match will return so order is important for priority. Using `isinstance` will let user provide fallback (for example every sympy object is instance of `Basic` while a `Mul` object will not match a `Symbol` object).

Have a look at the col_wrap functionality for inspiration.

I'm wondering if this could become a decorator function so a user can define its own function definition, without writing too much code.

## Analysis of Current `myprint_latex` Function

### Current Implementation Issues

Looking at the current implementation, `myprint_latex` has several limitations:

1. **Hardcoded type handling**: Only supports Markdown and SymPy Basic objects
2. **No extensibility**: Users cannot add custom type formatters
3. **Limited type detection**: Simple if/else logic instead of flexible type matching
4. **Inflexible priority**: No way to control formatter precedence
5. **No configuration**: Cannot be customized via config files

### Current Function Structure
```python
def myprint_latex(obj) -> str:
    """Convert object to LaTeX string representation."""
    if isinstance(obj, Markdown):
        return obj.data
    elif isinstance(obj, Basic):
        return latex(obj, mul_symbol=config.default_mul_symbol)
    else:
        return str(obj)  # Fallback
```

## Proposed Type-Based Formatter System

### Core Concept: Ordered Type Formatters

Replace hardcoded type checking with a flexible, ordered dictionary of type formatters where:

1. **Types are matched in order** (first match wins)
2. **Users can register custom formatters**
3. **Inheritance-based matching** using `isinstance`
4. **Configurable via config files and runtime**
5. **Decorator-based registration** for easy user-defined formatters

### Architecture Design

#### 1. Formatter Registry System

<!-- why use OrderedDict? -->

```python
from typing import TypeVar, Callable, Any, OrderedDict, Type
from collections import OrderedDict

T = TypeVar('T')
FormatterFunction = Callable[[Any], str]

class TypeFormatterRegistry:
    """Registry for type-based formatting functions with ordered priority."""

    def __init__(self):
        self._formatters: OrderedDict[Type, FormatterFunction] = OrderedDict()
        self._load_default_formatters()

    def register_formatter(self, type_class: Type[T], formatter: FormatterFunction, priority: int | None = None) -> None:
        """Register a formatter for a specific type with optional priority."""

    def format_object(self, obj: Any) -> str:
        """Format object using first matching type formatter."""

    def remove_formatter(self, type_class: Type) -> None:
        """Remove formatter for a type."""

    def list_formatters(self) -> list[tuple[Type, str]]:
        """List all registered formatters with their type names."""
```

#### 2. Default Formatter Implementation

```python
def _load_default_formatters(self):
    """Load built-in formatters in priority order."""
    # Order matters! More specific types first
    self._formatters[Markdown] = self._format_markdown
    self._formatters[pint.Quantity] = self._format_pint_quantity
    self._formatters[sympy.Basic] = self._format_sympy  # Broader catch-all
    self._formatters[float] = self._format_float
    self._formatters[int] = self._format_int
    self._formatters[str] = self._format_string
    self._formatters[object] = self._format_fallback  # Ultimate fallback

def _format_markdown(self, obj: Markdown) -> str:
    return obj.data

def _format_sympy(self, obj: sympy.Basic) -> str:
    return latex(obj, mul_symbol=config.default_mul_symbol)

def _format_pint_quantity(self, obj: pint.Quantity) -> str:
    return f"{obj:~L}"  # LaTeX format

def _format_float(self, obj: float) -> str:
    if config.float_format:
        return f"{obj:{config.float_format}}"
    return str(obj)
```

#### 3. Decorator-Based Registration

```python
# Global registry instance
formatter_registry = TypeFormatterRegistry()

def formatter_for(type_class: Type[T], priority: int | None = None):
    """Decorator to register a custom formatter function."""
    def decorator(func: FormatterFunction) -> FormatterFunction:
        formatter_registry.register_formatter(type_class, func, priority)
        return func
    return decorator

# User-friendly decorator
latex_formatter = formatter_for  # Alias for clarity
```

#### 4. Enhanced myprint_latex Function

```python
def myprint_latex(obj: Any, formatters: TypeFormatterRegistry | None = None) -> str:
    """Convert object to LaTeX string using type-based formatters.

    Args:
        obj: Object to format
        formatters: Optional custom formatter registry (defaults to global)

    Returns:
        LaTeX string representation of the object
    """
    registry = formatters or formatter_registry
    return registry.format_object(obj)
```

### User Interface Design

#### 1. Decorator-Based Custom Formatters

```python
from keecas import latex_formatter
import numpy as np

# Register custom formatter for numpy arrays
@latex_formatter(np.ndarray)
def format_numpy_array(arr: np.ndarray) -> str:
    if arr.ndim == 1:
        return r"\begin{bmatrix}" + r" & ".join(map(str, arr)) + r"\end{bmatrix}"
    elif arr.ndim == 2:
        rows = [r" & ".join(map(str, row)) for row in arr]
        return r"\begin{bmatrix}" + r" \\ ".join(rows) + r"\end{bmatrix}"
    else:
        return str(arr)

# Register formatter for custom classes
@latex_formatter(MyCustomClass, priority=1)  # High priority
def format_my_class(obj: MyCustomClass) -> str:
    return rf"\text{{{obj.name}}}: {latex(obj.value)}"
```

#### 2. Configuration File Integration

```toml
# .keecas/config.toml
[formatters]
# Built-in formatter configuration
float_precision = 3
int_format = "d"
string_escape_latex = true

# Enable/disable specific formatters
enable_pint_formatting = true
enable_numpy_formatting = false

[formatters.custom]
# Define simple string-based formatters
"MyClass" = "\\text{Custom: {obj}}"
"decimal.Decimal" = "{obj:.3f}"
```

#### 3. Runtime Formatter Management

```python
from keecas import formatter_registry

# Add custom formatter at runtime
def format_datetime(dt: datetime) -> str:
    return rf"\text{{{dt.strftime('%Y-%m-%d %H:%M')}}}"

formatter_registry.register_formatter(datetime, format_datetime)

# Create custom registry for specific context
custom_registry = TypeFormatterRegistry()
custom_registry.register_formatter(float, lambda x: f"{x:.6f}")

# Use custom registry in specific call
result = myprint_latex(my_object, formatters=custom_registry)
```

### Integration with col_wrap Pattern

#### Inspiration from col_wrap Design

The current `col_wrap` parameter works as:
```python
col_wrap: list[None | tuple[str, str]] | None = None
# Example: [None, ("=", "")] means no wrap for first column, "=" prefix for second
```

#### Formatter Specification Pattern

Similarly, we can allow formatter specification as data structures:

```python
# Type-formatter mapping specification
formatter_spec = [
    (Markdown, lambda obj: obj.data),
    (pint.Quantity, lambda obj: f"{obj:~L}"),
    (sympy.Basic, lambda obj: latex(obj)),
    (float, lambda obj: f"{obj:.3f}"),
    (object, str)  # Fallback
]

# Use in show_eqn
show_eqn(equations, formatters=formatter_spec)
```

#### Enhanced Dataframe Integration

```python
# Formatter specification as Dataframe-like structure
FormattersDataframe = dict[Type, FormatterFunction]

formatters_df = FormattersDataframe({
    Markdown: lambda obj: obj.data,
    sympy.Basic: lambda obj: latex(obj, mode="inline"),
    float: lambda obj: f"{obj:.2f}",
    str: lambda obj: rf"\text{{{obj}}}"
})

show_eqn(equations, formatters=formatters_df)
```

### Implementation Plan

#### Phase 1: Core Registry System
1. **Implement TypeFormatterRegistry**
   - Ordered type matching with isinstance
   - Priority-based insertion
   - Default formatter loading

2. **Create decorator interface**
   - `@latex_formatter` decorator
   - Priority specification
   - Type validation

#### Phase 2: Integration with show_eqn
3. **Update myprint_latex function**
   - Use registry-based formatting
   - Maintain backward compatibility
   - Add optional custom registry parameter

4. **Integrate with show_eqn**
   - Add `formatters` parameter to show_eqn
   - Support both registry and specification formats
   - Test with existing code

#### Phase 3: Configuration and Advanced Features
5. **Configuration file support**
   - TOML-based formatter configuration
   - Built-in formatter customization
   - Runtime configuration updates

6. **Advanced features**
   - Conditional formatting based on object properties
   - Context-aware formatting
   - Formatter composition and chaining

#### Phase 4: Documentation and Examples
7. **Comprehensive documentation**
   - Formatter creation tutorials
   - Common use case examples
   - Best practices guide

8. **Example formatters library**
   - NumPy array formatters
   - Pandas DataFrame formatters
   - Scientific notation formatters

### Benefits

#### 1. **Extensibility**
- Users can add formatters for any type
- Third-party package integration (NumPy, Pandas, etc.)
- Custom class formatting support

#### 2. **Flexibility**
- Per-project formatter customization
- Context-specific formatting registries
- Priority-based type matching

#### 3. **Maintainability**
- Clear separation of type handling logic
- Declarative formatter definitions
- Easy to test and debug

#### 4. **User Experience**
- Simple decorator-based registration
- Consistent formatting across documents
- No need to manually handle type checking

### Example Usage Scenarios

#### Scientific Computing
```python
@latex_formatter(np.ndarray)
def format_matrix(arr):
    return matrix_to_latex(arr)

@latex_formatter(scipy.stats.norm)
def format_distribution(dist):
    return rf"N(\mu={dist.mean()}, \sigma^2={dist.var()})"
```

#### Engineering Calculations
```python
@latex_formatter(Steel)  # Custom material class
def format_steel(steel):
    return rf"\text{{{steel.grade}}} (f_y = {steel.yield_strength:~L})"

@latex_formatter(BeamSection)
def format_beam(beam):
    return rf"HEB {beam.height} \times {beam.width}"
```

#### Financial Calculations
```python
@latex_formatter(decimal.Decimal, priority=1)
def format_currency(amount):
    return rf"\${amount:,.2f}"

@latex_formatter(datetime.date)
def format_date(date):
    return rf"\text{{{date.strftime('%B %d, %Y')}}}"
```

### Backward Compatibility

**Guarantee**: All existing code will continue to work without changes
- Default formatters preserve current behavior
- myprint_latex signature unchanged (optional parameter added)
- Built-in type formatting remains identical

### Timeline Estimate

- **Phase 1**: 2 days (core registry)
- **Phase 2**: 1 day (integration)
- **Phase 3**: 2 days (configuration)
- **Phase 4**: 1 day (documentation)

**Total**: ~6 days of development work

### Questions for User Review

1. **Decorator style**: Is the `@latex_formatter(Type)` decorator approach intuitive?
2. **Configuration**: Should formatters be configurable via TOML or just runtime registration?
3. **Built-in formatters**: Any specific types that should have built-in formatters (NumPy, Pandas, etc.)?
4. **Priority system**: Should priority be numeric or enum-based ("high", "medium", "low")?

Awaiting user approval to proceed with implementation.