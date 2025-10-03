"""Demonstration: Creating custom formatters with the @cell_formatter decorator.

This script walks through the process of creating and using custom formatters
at runtime for the keecas equation rendering system.
"""

# Step 1: Import necessary components
from keecas import (
    cell_formatter,              # Decorator for registering formatters
    show_eqn,                    # Main equation display function
    symbols,                     # SymPy symbols
    default_cell_formatter_registry,  # Access to the global registry
)
from fractions import Fraction

print("=" * 70)
print("DEMONSTRATION: Creating Custom Formatters with @cell_formatter")
print("=" * 70)

# Step 2: Define symbols for our equations
print("\n[Step 1] Define symbols:")
x, y, z = symbols("x, y, z")
print(f"Created symbols: x, y, z")

# Step 3: Create a basic equation WITHOUT custom formatter
print("\n[Step 2] Basic equation without custom formatter:")
print("Code: show_eqn({x: 5, y: 10})")
result = show_eqn({x: 5, y: 10}, debug=True)
print("Output:")
print(result.data)

# Step 4: Register a custom formatter for fractions
print("\n" + "=" * 70)
print("[Step 3] Register a custom formatter for Python's Fraction type")
print("=" * 70)

@cell_formatter(Fraction, priority=25)
def format_fraction(frac, col_index, **kwargs):
    """Format fractions as LaTeX fractions.

    Args:
        frac: Fraction object
        col_index: 0 for LHS, 1+ for RHS
        **kwargs: latex parameters (passed but ignored for Fraction)
    """
    latex_frac = rf"\frac{{{frac.numerator}}}{{{frac.denominator}}}"
    if col_index == 0:
        return latex_frac
    else:
        return f"= {latex_frac}"

print("[OK] Registered formatter for Fraction with priority=25")
print("\nFormatter function signature:")
print("  format_fraction(frac, col_index, **kwargs)")
print("\nLogic:")
print("  - col_index == 0 (LHS): Show \\frac{num}{den}")
print("  - col_index > 0 (RHS): Show = \\frac{num}{den}")

# Step 5: Use the custom formatter
print("\n" + "=" * 70)
print("[Step 4] Use the custom formatter")
print("=" * 70)

a, b = symbols("a, b")
frac_value = Fraction(3, 4)

print("\nCode:")
print("  a = symbols('a')")
print("  frac_value = Fraction(3, 4)")
print("  show_eqn({a: frac_value})")

result_frac = show_eqn({a: frac_value}, debug=True)
print("\nOutput:")
print(result_frac.data)

# Step 6: Register formatter for custom class
print("\n" + "=" * 70)
print("[Step 5] Register formatter for a custom class")
print("=" * 70)

class ComplexNumber:
    """Simple complex number class for demonstration."""
    def __init__(self, real, imag):
        self.real = real
        self.imag = imag

    def __repr__(self):
        return f"ComplexNumber({self.real}, {self.imag})"

@cell_formatter(ComplexNumber, priority=20)
def format_complex(num, col_index, **kwargs):
    """Format custom complex numbers.

    Args:
        num: ComplexNumber object
        col_index: 0 for LHS, 1+ for RHS
        **kwargs: latex parameters (ignored)
    """
    # Format as a + bi
    if num.imag >= 0:
        complex_str = f"{num.real} + {num.imag}i"
    else:
        complex_str = f"{num.real} - {abs(num.imag)}i"

    if col_index == 0:
        return complex_str
    else:
        return f"= {complex_str}"

print("[OK] Registered formatter for ComplexNumber with priority=20")

c = symbols("c")
complex_val = ComplexNumber(3, 4)

print("\nCode:")
print("  class ComplexNumber:")
print("      def __init__(self, real, imag): ...")
print("  ")
print("  @cell_formatter(ComplexNumber, priority=20)")
print("  def format_complex(num, col_index, **kwargs):")
print("      # Format as a + bi")
print("      ...")
print("  ")
print("  c = symbols('c')")
print("  complex_val = ComplexNumber(3, 4)")
print("  show_eqn({c: complex_val})")

result_complex = show_eqn({c: complex_val}, debug=True)
print("\nOutput:")
print(result_complex.data)

# Step 7: Use multiple custom formatters together
print("\n" + "=" * 70)
print("[Step 6] Use multiple custom formatters together")
print("=" * 70)

d, e = symbols("d, e")
frac_value2 = Fraction(5, 6)
complex_val2 = ComplexNumber(2, -3)

print("\nCode:")
print("  d, e = symbols('d, e')")
print("  show_eqn({d: Fraction(5, 6), e: ComplexNumber(2, -3)})")

result_mixed = show_eqn({d: frac_value2, e: complex_val2}, debug=True)
print("\nOutput:")
print(result_mixed.data)

# Step 8: Inspect the registry
print("\n" + "=" * 70)
print("[Step 7] Inspect the formatter registry")
print("=" * 70)

print("\nRegistered formatters (in priority order):")
for (type_class, func_id), (formatter, priority) in default_cell_formatter_registry._formatters.items():
    print(f"  Priority {priority:3d}: {type_class.__name__:20s} -> {formatter.__name__}")

# Step 9: Override formatter at function call
print("\n" + "=" * 70)
print("[Step 8] Override formatter for a specific call")
print("=" * 70)

def custom_boxed_formatter(value, col_index, **kwargs):
    """Custom formatter that boxes everything."""
    from sympy import latex
    if hasattr(value, '__class__') and hasattr(value, '__sympy__'):
        latex_str = latex(value, **kwargs)
    else:
        latex_str = str(value)

    if col_index == 0:
        return rf"\boxed{{{latex_str}}}"  # Box LHS
    else:
        return rf"= \boxed{{{latex_str}}}"  # Box RHS too

print("\nCode:")
print("  def custom_boxed_formatter(value, col_index, **kwargs):")
print("      # Box both LHS and RHS")
print("      ...")
print("  show_eqn({x: 100}, cell_formatter=custom_boxed_formatter)")

result_override = show_eqn({x: 100}, cell_formatter=custom_boxed_formatter, debug=True)
print("\nOutput:")
print(result_override.data)

# Step 10: Using kwargs with formatters
print("\n" + "=" * 70)
print("[Step 9] Pass kwargs to formatters (mul_symbol)")
print("=" * 70)

expr = x * y * z

print("\nDefault mul_symbol (thin space):")
print("  show_eqn({expr: x * y})")
result_default = show_eqn({expr: x * y}, debug=True)
print("Output:", result_default.data)

print("\nCustom mul_symbol (cdot):")
print("  show_eqn({expr: x * y}, mul_symbol=r'\\cdot')")
result_kwargs = show_eqn({expr: x * y}, mul_symbol=r'\cdot', debug=True)
print("Output:", result_kwargs.data)

# Summary
print("\n" + "=" * 70)
print("SUMMARY: Key Points")
print("=" * 70)
print("""
1. Use @cell_formatter(Type, priority=N) to register custom formatters
   - Lower priority number = higher precedence
   - First matching type wins (isinstance check)

2. Formatter signature: (value, col_index, **kwargs) -> str
   - value: The cell value to format
   - col_index: 0 for LHS, 1+ for RHS columns
   - **kwargs: Parameters passed to latex() (e.g., mul_symbol, mode)

3. Built-in priorities:
   - Priority 10: Markdown
   - Priority 15: Pint quantities
   - Priority 30: SymPy expressions (Basic)
   - Priority 70: Python built-ins (float, int, str)

4. Registration methods:
   - @cell_formatter decorator (global, persistent in current session)
   - cell_formatter parameter in show_eqn() (per-call override)

5. Formatters are called for EVERY cell value
   - Use col_index to differentiate LHS vs RHS formatting
   - LHS (col_index=0): typically just the value
   - RHS (col_index>0): typically "= value"

6. Custom formatters in config files:
   - Create ~/.keecas/formatters.py for global formatters
   - Create <project>/.keecas/formatters.py for project formatters
   - These are auto-imported on keecas startup

Example ~/.keecas/formatters.py:
    from keecas import cell_formatter
    from fractions import Fraction

    @cell_formatter(Fraction, priority=25)
    def my_fraction_formatter(frac, col_index, **kwargs):
        latex_frac = rf"\\frac{{{frac.numerator}}}{{{frac.denominator}}}"
        return latex_frac if col_index == 0 else f"= {latex_frac}"
""")

print("\n[OK] Demonstration complete!")
print("\nNext steps:")
print("  - Try creating your own custom formatter")
print("  - Create ~/.keecas/formatters.py for persistent formatters")
print("  - Experiment with different priorities and types")
