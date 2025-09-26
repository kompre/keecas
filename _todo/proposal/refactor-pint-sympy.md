# Refactor of pint_sympy

## Original Objective

`pint_sympy.py` and in particular `pint_to_sympy` function is in need of a refactor. The function will [needs completion - objective was cut off in todo.md].

## Analysis of Current Implementation

### Current `pint_to_sympy` Function Issues

After analyzing the current implementation in `src/keecas/pint_sympy.py:354-411`, several issues are apparent:

1. **Poor Code Quality**
   - Extremely long comment on line 368 that spans the entire line
   - Commented-out dead code (lines 397-402)
   - Complex nested logic that's hard to follow
   - Mixed concerns (unit creation, magnitude handling, exponent processing)

2. **Inefficient Unit Creation**
   - Creates new SymPy units dynamically using `setattr(sympy_units, ...)`
   - No caching mechanism for created units
   - Redundant unit lookup operations
   - Creates both full name and short name attributes separately

3. **Unclear Logic Flow**
   - Unit existence checking is buried in complex conditionals
   - Prefix detection logic is hard to understand
   - No clear separation between unit discovery and conversion

4. **Missing Functionality**
   - Commented-out scale factor setting (lines 397-402)
   - No proper base unit conversion support
   - Limited error handling

5. **Type Safety Issues**
   - Dynamic attribute creation bypasses type checking
   - No validation of unit creation success
   - Unclear return type behavior

## Proposed Refactor

### Goals
1. **Improve code readability and maintainability**
2. **Add proper error handling and validation**
3. **Implement efficient unit caching**
4. **Separate concerns into logical functions**
5. **Add comprehensive type annotations**
6. **Enable proper base unit conversion**

### New Architecture

#### 1. Unit Cache Management
```python
class SymPyUnitCache:
    """Manages created SymPy units to avoid redundant creation."""
    _created_units: dict[str, Any] = {}

    @classmethod
    def get_or_create_unit(cls, fullname: str, shortname: str, is_prefixed: bool) -> Any:
        """Get existing unit or create new one."""

    @classmethod
    def clear_cache(cls) -> None:
        """Clear unit cache (useful for testing)."""
```

#### 2. Unit Analysis Functions
```python
def _analyze_pint_unit(unit_name: str) -> UnitInfo:
    """Analyze a Pint unit and extract metadata."""

def _is_unit_prefixed(unit_name: str) -> bool:
    """Determine if a unit uses prefixes."""

def _get_base_unit_conversion(unit_name: str) -> tuple[float, list[tuple[str, float]]]:
    """Get conversion factor and base units for a given unit."""
```

#### 3. SymPy Unit Creation
```python
def _create_sympy_unit(fullname: str, shortname: str, is_prefixed: bool) -> Any:
    """Create a new SymPy unit with proper attributes."""

def _ensure_sympy_unit_exists(unit_name: str) -> Any:
    """Ensure SymPy unit exists, creating if necessary."""
```

#### 4. Refactored Main Function
```python
def pint_to_sympy(quantity: pint.Quantity) -> Any:
    """Convert Pint quantity to SymPy expression.

    Streamlined implementation with clear error handling and
    efficient unit caching.
    """
```

### Implementation Steps

#### Phase 1: Core Infrastructure
1. **Create unit cache system**
   - Implement `SymPyUnitCache` class
   - Add unit metadata analysis functions
   - Create comprehensive tests

2. **Implement unit analysis helpers**
   - Extract prefix detection logic
   - Add base unit conversion support
   - Implement proper error handling

#### Phase 2: SymPy Unit Management
3. **Refactor unit creation**
   - Centralize SymPy unit creation logic
   - Add proper type annotations
   - Implement caching mechanism

4. **Add validation and error handling**
   - Validate Pint quantities before conversion
   - Handle edge cases (dimensionless quantities, complex units)
   - Add comprehensive error messages

#### Phase 3: Main Function Refactor
5. **Rewrite `pint_to_sympy` function**
   - Use new helper functions
   - Clear, linear logic flow
   - Proper error handling and type safety

6. **Optimize performance**
   - Leverage unit caching
   - Minimize redundant operations
   - Profile performance improvements

#### Phase 4: Testing and Documentation
7. **Comprehensive testing**
   - Unit tests for all helper functions
   - Integration tests with complex quantities
   - Performance benchmarks

8. **Documentation and cleanup**
   - Add detailed docstrings
   - Remove commented-out code
   - Update module-level documentation

### Expected Benefits

1. **Improved Code Quality**
   - Clear, readable function structure
   - Proper separation of concerns
   - Comprehensive type annotations

2. **Better Performance**
   - Unit caching reduces redundant creation
   - Optimized lookup operations
   - Reduced memory footprint

3. **Enhanced Reliability**
   - Proper error handling
   - Validation of inputs and outputs
   - Robust edge case handling

4. **Easier Maintenance**
   - Modular design enables easier testing
   - Clear interfaces between components
   - Better documentation and examples

### Backward Compatibility

The refactor will maintain complete backward compatibility:
- Same function signature for `pint_to_sympy`
- Same behavior for valid inputs
- Enhanced error messages for invalid inputs
- No changes to module exports

### Testing Strategy

1. **Preserve existing behavior**: All current tests must pass
2. **Add edge case coverage**: Handle corner cases better
3. **Performance testing**: Ensure no regression
4. **Integration testing**: Test with complex real-world examples

### Timeline Estimate

- **Phase 1**: 1-2 days (infrastructure)
- **Phase 2**: 1-2 days (unit management)
- **Phase 3**: 1 day (main function)
- **Phase 4**: 1 day (testing and docs)

**Total**: ~4-6 days of development work

### Questions for User Review

1. **Scope**: Should we also refactor other functions in the module (like locale management)?
2. **Performance**: Are there specific performance requirements or bottlenecks to address?
3. **Features**: Should we implement the commented-out scale factor functionality?
4. **Breaking changes**: Any tolerance for minor API improvements that might require small changes to user code?

Awaiting user approval to proceed with implementation.