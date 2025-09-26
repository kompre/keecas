# Conventions

Keecas follows strict conventions to minimize boilerplate while maximizing expressiveness. **Always follow these patterns when working with keecas code.**

## Core Philosophy

Mathematical equations are mappings between LHS and RHS expressions. Use Python `dict` containers where:

- **Cell-local dicts** (prefixed with `_`): Live and die within a single cell for immediate display
- **Notebook-global dicts** (no prefix): Persist across cells for complex multi-step calculations

## Standard Dict Conventions

| Dict     | Purpose                     | Example                                                        |
| -------- | --------------------------- | -------------------------------------------------------------- |
| `_p`     | Cell-local parameters       | `_p = {F: 10*u.kN, A: 50*u.cm**2}`                             |
| `_e`     | Cell-local expressions      | `_e = {sigma: "F / A" \| pc.parse_expr}`                       |
| `_v`     | Cell-local evaluated values | `_v = {k: v \| pc.subs(_e\|_p) \| pc.N for k,v in _e.items()}` |
| `_d`     | Cell-local descriptions     | `_d = {F: "applied force", sigma: "stress"}`                   |
| `_l`     | Cell-local labels           | `_l = {k: str(k) for k in _e.keys()}`                          |
| `_c`     | Cell-local checks           | `_c = {k: check(v, 1.0) for k,v in _v.items()}`                |
| `params` | Global parameters           | `params.update(_p)` for persistence                            |
| `eqn`    | Global expressions          | `eqn.update(_e)` for persistence                               |

## Standard Cell Pattern

```python
# 1. Define symbols (prefer LaTeX notation)
F, A, sigma = symbols(r"F, A, \sigma")

# 2. Cell-local parameters
_p = {
    F: 10 * u.kN,
    A: 50 * u.cm**2,
}

# 3. Cell-local expressions
_e = {
    sigma: "F / A" | pc.parse_expr
}

# 4. Evaluation using cell-local dicts
_v = {
    k: v | pc.subs(_e | _p) | pc.convert_to([u.MPa]) | pc.N
    for k, v in _e.items()
}

# 5. Display
show_eqn([_p | _e, _v])
```

## Multi-Cell Persistence

For calculations spanning multiple cells:

```python
# Setup cell (run once per notebook)
params = {}  # Global parameters
eqn = {}     # Global expressions

# Calculation cell with LaTeX symbols
q, L, delta = symbols(r"q, L, \delta")

_p = {q: 5 * u.kN/u.m, L: 8 * u.m}
params.update(_p)  # Save to global

_e = {delta: "5 * q * L^4 / (384 * E * I)" | pc.parse_expr}
eqn.update(_e)     # Save to global

# For cross-cell dependencies
_v = {
    k: v | pc.subs(eqn | params) | pc.convert_to([u.mm]) | pc.N
    for k, v in _e.items()
}
```

## Symbol Naming Conventions

### ✅ PREFERRED: LaTeX notation with raw strings

```python
# Simple symbols
F, A, sigma = symbols(r"F, A, \sigma")

# Complex engineering symbols
sigma_Sd, tau_Rd = symbols(r"\sigma_{Sd}, \tau_{Rd}")

# Symbols with commas - escape with backslash
tau_1_Rd, gamma_M0 = symbols(r"\tau_{1\,Rd}, \gamma_{M0}")

# Greek letters
alpha, beta, gamma = symbols(r"\alpha, \beta, \gamma")
```

### ❌ AVOID: Plain string notation

```python
# Avoid - no LaTeX rendering
sigma, tau, gamma = symbols("sigma, tau, gamma")
```

## Advanced Patterns

### Verification

```python
# Use LaTeX notation for engineering symbols
sigma_Sd, sigma_Rd, tau_Sd, tau_Rd = symbols(r"\sigma_{Sd}, \sigma_{Rd}, \tau_{Sd}, \tau_{Rd}")

_expr = [sigma_Sd / sigma_Rd, tau_Sd / tau_Rd]  # List of expressions to check
_v = {k: k | pc.subs(_e | _p) | pc.N for k in _expr}  # Expression as key
_c = {k: check(v, 1.0) for k, v in _v.items()}
```

### Labels and Cross-References

```python
_l = {k: str(k) for k in _e.keys()}  # Auto-generate labels
show_eqn([_e, _v], label=_l)
# Reference in text: \eqref{eq-PREFIX-symbol}
```

### Symbol Dependency Ordering (Automatic)

```python
# Complex symbols with LaTeX notation - escape commas with backslash
tau_1_Rd, gamma_M0 = symbols(r"\tau_{1\,Rd}, \gamma_{M0}")

_e = {
    result: "sqrt(a^2 + b^2) / intermediate" | pc.parse_expr,  # Uses 'intermediate'
    intermediate: "a * b" | pc.parse_expr,                     # Defined after 'result'
}
# Keecas handles dependency ordering automatically
```

## Configuration Setup

```python
# Preferred import style
from keecas import symbols, u, pc, show_eqn, config, check

# Configuration for Quarto/KaTeX
config.katex = True              # Disable \label{} for KaTeX compatibility
config.print_label = True        # Print labels in dev mode
config.eq_prefix = r"eq-PREFIX-" # Label prefixing

# Language and localization (automatic Pint sync)
config.language = 'it'           # Sets both keecas and Pint locales
# Supported: 'de', 'es', 'fr', 'it', 'pt' (full)
# Fallback: 'da', 'nl', 'no', 'sv', 'en' (English units)

# Initialize global dicts
params = {}
eqn = {}
```

## Pipe Operations

Keecas uses pipe operators for functional composition:

### Common Pipe Commands

```python
# Parse string expressions
expr = "F / A" | pc.parse_expr

# Substitute values
result = expr | pc.subs(parameters)

# Convert units
result = expr | pc.convert_to([u.MPa])

# Numerical evaluation
result = expr | pc.N

# Chain operations
result = "F / A" | pc.parse_expr | pc.subs(_p) | pc.convert_to([u.MPa]) | pc.N
```

### Advanced Pipe Operations

```python
# Simplify expressions
simplified = expr | pc.simplify

# Apply assumptions
result = expr | pc.subs(assumptions) | pc.doit

# Quantity operations
quantity = expr | pc.quantity_simplify
```

## Do's and Don'ts

### ✅ DO:

- Use LaTeX notation with raw strings for symbol definitions
- Use underscore-prefixed dicts for cell-local data (`_p`, `_e`, `_v`, `_d`)
- Use `params.update(_p)` and `eqn.update(_e)` for persistence
- Use dict comprehensions for evaluation
- Use pipe operators for functional composition
- Escape commas in symbol names with `\,`
- Let keecas handle symbol dependency ordering

### ❌ DON'T:

- Use plain string notation for symbols - always prefer LaTeX
- Use verbose variable names like `parameters`, `equations`, `values`
- Manually manage symbol dependencies
- Use individual variables instead of dicts for related data
- Mix cell-local and global patterns unnecessarily

## Engineering-Specific Patterns

### Material Properties

```python
# Steel properties
E, f_y, gamma_M0 = symbols(r"E, f_y, \gamma_{M0}")

_p = {
    E: 210 * u.GPa,        # Young's modulus
    f_y: 355 * u.MPa,      # Yield strength
    gamma_M0: 1.0,         # Partial factor
}
```

### Section Properties

```python
# Beam section
A, I_y, W_y = symbols(r"A, I_y, W_y")

_p = {
    A: 129.7 * u.cm**2,           # Cross-sectional area
    I_y: 8196 * u.cm**4,          # Second moment of area
    W_y: 641.3 * u.cm**3,         # Section modulus
}
```

### Load Calculations

```python
# Distributed load on beam
q, L, M_max = symbols(r"q, L, M_{max}")

_p = {q: 25 * u.kN/u.m, L: 6 * u.m}
_e = {M_max: "q * L^2 / 8" | pc.parse_expr}
```

### Verification Checks

```python
# Resistance verification
N_Ed, N_Rd = symbols(r"N_{Ed}, N_{Rd}")

_p = {
    N_Ed: 500 * u.kN,     # Applied force
    N_Rd: 750 * u.kN,     # Resistance
}

# Check utilization ratio
utilization = check(N_Ed / N_Rd, 1.0)
```

## Common Mistakes to Avoid

### Symbol Definition Issues

```python
# ❌ Wrong - plain strings
force, area = symbols("force, area")

# ✅ Correct - LaTeX notation
F, A = symbols(r"F, A")
```

### Unit Handling Issues

```python
# ❌ Wrong - mixing unit systems
pressure = 1000 * u.Pa + 1 * u.psi  # Don't mix units

# ✅ Correct - consistent units
pressure = 1000 * u.Pa + (1 * u.psi).to(u.Pa)
```

### Dictionary Pattern Issues

```python
# ❌ Wrong - verbose names and individual variables
parameters = {force: 100}
expressions = {stress: force/area}
force_value = 100

# ✅ Correct - follow conventions
_p = {F: 100 * u.N}
_e = {sigma: "F / A" | pc.parse_expr}
```

## Best Practices Summary

1. **Consistency**: Always follow the established patterns
2. **LaTeX symbols**: Use raw strings with LaTeX notation
3. **Dict organization**: Use prefixed dicts for organization
4. **Pipe operations**: Chain operations with pipe operators
5. **Units**: Always include units for physical quantities
6. **Documentation**: Use meaningful variable names and comments
7. **Verification**: Include checks for engineering calculations