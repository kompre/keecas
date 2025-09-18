# Keecas Usage Conventions

This document defines the standard conventions for using keecas in Jupyter notebooks and Quarto documents. These conventions are designed to minimize boilerplate code while maximizing expressiveness and maintainability.

## Philosophy

Keecas is built around the principle that **mathematical equations are mappings** between left-hand side (LHS) and right-hand side (RHS) expressions. The simplest Python container for this is a `dict` where the LHS is the key and RHS is the value.

The system uses two levels of organization:
- **Cell-local dicts** (prefixed with `_`): Live and die within a single cell, used for immediate display
- **Notebook-global dicts** (no prefix): Persist across cells for complex multi-step calculations

## Core Dict Conventions

### Standard Cell-Local Dicts

| Dict | Purpose | Example |
|------|---------|---------|
| `_p` | Parameters with units | `_p = {F: 10*u.kN, A: 50*u.cm**2}` |
| `_e` | Symbolic expressions | `_e = {sigma: "F / A" \| pc.parse_expr}` |
| `_v` | Evaluated values | `_v = {k: v \| pc.subs(_e\|_p) \| pc.N for k,v in _e.items()}` |
| `_d` | Descriptions | `_d = {F: "applied force", sigma: "normal stress"}` |
| `_l` | Labels for equations | `_l = {k: str(k) for k in _e.keys()}` |
| `_c` | Check results | `_c = {k: check(v, 1.0) for k,v in _v.items()}` |
| `_ff` | Float formatting | `_ff = {k: "{:.3f}" for k in _v.keys()}` |

### Notebook-Global Dicts

| Dict | Purpose | Usage |
|------|---------|--------|
| `params` | Global parameters | `params.update(_p)` to persist parameters |
| `eqn` | Global expressions | `eqn.update(_e)` to persist expressions |

## Standard Cell Pattern

### Basic Cell Structure

```python
# 1. Define symbols
symbol1, symbol2, result = symbols("symbol1, symbol2, result")

# 2. Parameters (cell-local)
_p = {
    symbol1: value1 * u.unit1,
    symbol2: value2 * u.unit2,
}

# 3. Expressions (cell-local)
_e = {
    result: "symbol1 * symbol2" | pc.parse_expr
}

# 4. Evaluation
_v = {
    k: v | pc.subs(_e | _p) | pc.convert_to([u.target_unit]) | pc.N
    for k, v in _e.items()
}

# 5. Display
show_eqn([_p | _e, _v])
```

### With Persistence (Multi-Cell Calculations)

```python
# Setup cell (run once per notebook)
params = {}  # Global parameters
eqn = {}     # Global expressions

# Calculation cell
_p = {symbol: value}
params.update(_p)  # Save to global

_e = {result: "expression" | pc.parse_expr}
eqn.update(_e)     # Save to global

# For cross-cell dependencies:
_v = {
    k: v | pc.subs(eqn | params) | pc.convert_to([units]) | pc.N
    for k, v in _e.items()
}
```

## Advanced Patterns

### 1. Labels and Cross-References

```python
# Auto-generate labels
_l = {k: str(k) for k in _e.keys()}

show_eqn([_e, _v], label=_l)

# Reference in markdown: \eqref{eq-PREFIX-symbol}
```

### 2. Verification Patterns

**Simple verification:**
```python
_c = {k: check(v, 1.0) for k, v in _v.items()}
```

**Expression-as-key verification:**
```python
_expr = [sigma_Sd / sigma_Rd, tau_Sd / tau_Rd]
_v = {k: k | pc.subs(_e | _p) | pc.N for k in _expr}
_c = {k: check(v, 1.0) for k, v in _v.items()}
```

**Complex verification with test specifications:**
```python
from sympy import Le, Lt, Ge, Gt, Eq

_expr = {
    a: (3, Le, 1),    # 3 ≤ 1
    b: (4, Gt, 2),    # 4 > 2
    c: (5, Lt, 3),    # 5 < 3
}

_c = {k: check(lhs=v[0], test=v[1], rhs=v[2]) for k, v in _expr.items()}
```

### 3. Multi-Column Float Formatting

```python
# Format specific columns differently
_ff = {k: [None, "{:.3f}", None] for k in _c.keys()}  # [col1, col2, col3]
show_eqn([_p | _v, _c], float_format=_ff)

# Or format by dict key
_ff = {
    symbol1: "{:.2f}",
    symbol2: "{:.0f}",
}
```

### 4. Symbol Dependency Ordering

Keecas automatically handles symbol dependencies - you can reference symbols before defining them:

```python
_e = {
    result: "sqrt(a^2 + b^2) / intermediate" | pc.parse_expr,  # Uses 'intermediate'
    intermediate: "a * b" | pc.parse_expr,                     # Defined after 'result'
}

# Keecas will order substitutions correctly
_v = {k: v | pc.subs(eqn | params) | pc.N for k, v in _e.items()}
```

## Configuration Patterns

### Notebook Setup

```python
# Import style (prefer explicit)
from keecas import symbols, u, pc, show_eqn, options, check

# Configuration for Quarto/KaTeX compatibility
options.katex = True              # Disable \label{} for KaTeX
options.PRINT_LABEL = True        # Print labels in dev mode
options.EQ_PREFIX = r"eq-PREFIX-" # Label prefixing

# Initialize global dicts
params = {}
eqn = {}
```

### Engineering Symbol Naming

Use raw strings for LaTeX symbols:

```python
# Good: Raw strings for complex LaTeX
sigma_Sd, tau_Sd = symbols(r"\sigma_{Sd}, \tau_{Sd}")

# Acceptable: Simple symbols
F, A, sigma = symbols("F, A, sigma")
```

## Environment-Specific Patterns

### Cases Environment

```python
_p = {param1: value1, param2: value2}
_d = {param1: "description1", param2: "description2"}

show_eqn([_p, _d],
         environment="cases",
         col_wrap=[None, "=", "&"])
```

### Equation Environment with Labels

```python
_e = {result: "expression" | pc.parse_expr}
_v = {k: v | pc.subs(_e | _p) | pc.N for k, v in _e.items()}
_l = {k: str(k) for k in _e.keys()}

show_eqn([_e, _v],
         environment="equation",
         label=_l)
```

## Best Practices

### Do's

✅ Use underscore-prefixed dicts for cell-local data
✅ Use `params.update(_p)` and `eqn.update(_e)` for persistence
✅ Use dict comprehensions for evaluation
✅ Use pipe operators for functional composition
✅ Use raw strings for complex LaTeX symbols
✅ Let keecas handle symbol dependency ordering

### Don'ts

❌ Don't use verbose variable names like `parameters`, `equations`, `values`
❌ Don't manually manage symbol dependencies
❌ Don't repeat the same parameters across cells without persistence
❌ Don't use individual variables instead of dicts for related data
❌ Don't mix cell-local and global patterns unnecessarily

## Quick Reference

### Minimal Cell Pattern
```python
# Define → Parameters → Expressions → Evaluation → Display
symbols("x, y, z")
_p = {x: value}
_e = {z: "x + y" | pc.parse_expr}
_v = {k: v | pc.subs(_e | _p) | pc.N for k, v in _e.items()}
show_eqn([_p | _e, _v])
```

### Full Featured Cell Pattern
```python
symbols("params, expressions, result")
_p = {param: value * u.unit}
params.update(_p)
_e = {result: "expression" | pc.parse_expr}
eqn.update(_e)
_v = {k: v | pc.subs(eqn | params) | pc.convert_to([units]) | pc.N for k, v in _e.items()}
_d = {param: "description", result: "description"}
_l = {k: str(k) for k in _e.keys()}
_c = {k: check(v, 1.0) for k, v in _v.items()}
show_eqn([_p | _e, _v, _d, _c], label=_l, float_format="{:.3f}")
```

This convention system ensures minimal boilerplate while providing maximum flexibility for engineering calculations in Jupyter notebooks and Quarto documents.