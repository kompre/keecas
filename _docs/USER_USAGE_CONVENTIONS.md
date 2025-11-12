# Keecas User Usage Conventions

This guide establishes conventions for writing keecas notebooks to create engineering calculation documents. These patterns ensure consistency, readability, and maintainability across your notebooks.

**Audience**: Users creating engineering calculations with keecas in Jupyter notebooks
**Scope**: Notebook organization, naming patterns, cell structure, and workflows
**Not covered**: Package development, testing, or internal architecture

## Core Philosophy

Keecas represents mathematical equations as Python dictionaries where:
- **Keys** = Left-hand side (LHS) symbols
- **Values** = Right-hand side (RHS) expressions or values

This approach minimizes boilerplate while maximizing expressiveness through:
1. **Dictionary-based containers** for organizing related data
2. **Cell-local vs global patterns** for managing scope
3. **Functional pipe composition** for chaining operations

## Naming Conventions

### Cell-Local Dictionaries (Prefix: `_`)

Cell-local dictionaries live and die within a single cell, used for immediate calculations and display.

| Dict  | Purpose                     | Example                                                          |
|-------|-----------------------------|------------------------------------------------------------------|
| `_p`  | Cell-local parameters       | `_p = {F: 10*u.kN, A: 50*u.cm**2}`                               |
| `_e`  | Cell-local expressions      | `_e = {sigma: "F / A" \| pc.parse_expr}`                         |
| `_v`  | Cell-local evaluated values | `_v = {k: v \| pc.subs(_e\|_p) \| pc.N for k,v in _e.items()}`  |
| `_d`  | Cell-local descriptions     | `_d = {F: "applied force", sigma: "stress"}`                     |
| `_l`  | Cell-local labels           | `_l = generate_unique_label(_d)`                                 |
| `_c`  | Cell-local check results    | `_c = {k: check(v, 1.0) for k,v in _v.items()}`                  |
| `_ff` | Cell-local float formats    | `_ff = {k: [None, "{:.3f}", None] for k in _c.keys()}`           |
| `_expr` | List of expressions       | `_expr = [sigma_Sd / sigma_Rd, tau_Sd / tau_Rd]`                |

### Notebook-Global Dictionaries (No Prefix)

Global dictionaries persist across cells for complex multi-step calculations.

| Dict     | Purpose                  | Example                           |
|----------|--------------------------|-----------------------------------|
| `params` | Global parameters        | `params.update(_p)`               |
| `eqn`    | Global expressions       | `eqn.update(_e)`                  |
| `vals`   | Global evaluated values  | `vals.update(_v)` ⚠️ Use with caution |
| `labels` | Global labels            | `labels = _l`                     |

**Important**: Initialize global dicts once at the start of your notebook:

```python
# Setup cell (run once)
params = {}
eqn = {}
```

## Symbol Definition Conventions

### ✅ Always Use LaTeX Notation

Symbols should **always** be defined with LaTeX notation in raw strings:

```python
# Simple symbols
F, A, sigma = symbols(r"F, A, \sigma")

# Complex engineering symbols with subscripts
sigma_Sd, tau_Rd = symbols(r"\sigma_{Sd}, \tau_{Rd}")

# Greek letters
alpha, beta, gamma = symbols(r"\alpha, \beta, \gamma")

# Symbols with commas - escape with backslash
tau_1_Rd, gamma_M0 = symbols(r"\tau_{1\,Rd}, \gamma_{M0}")
```

### ❌ Avoid Plain String Notation

**Never** use plain string notation - it creates different symbol objects:

```python
# ❌ WRONG: Creates different symbols
sigma_latex = symbols(r"\sigma_{Sd}")   # LaTeX version
sigma_plain = symbols("sigma_Sd")        # Plain version

# These are NOT equal!
sigma_latex == sigma_plain  # False

# Substitutions won't work as expected
_p = {sigma_latex: 100*u.MPa}
expr = sigma_plain / A  # Won't substitute! Different symbol!
```

**Why it matters**: SymPy compares symbols by their string representation. LaTeX and plain notation create distinct objects that won't match during substitutions.

## Standard Cell Patterns

### Pattern 1: Single-Cell Calculation (No Persistence)

Use for standalone calculations that don't need to be referenced later:

```python
# 1. Define symbols with LaTeX notation
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

# 4. Evaluation
_v = {
    k: v | pc.subs(_e | _p) | pc.convert_to([u.MPa]) | pc.N
    for k, v in _e.items()
}

# 5. Display
show_eqn([_p | _e, _v])
```

### Pattern 2: Multi-Cell Calculation (With Persistence)

Use when later cells need access to parameters or expressions:

```python
# === Setup Cell (run once per notebook) ===
params = {}  # Global parameters
eqn = {}     # Global expressions

# === First Calculation Cell ===
F_d, A_load, sigma_d = symbols(r"F_{d}, A_{load}, \sigma_{d}")

_p = {
    F_d: 10 * u.kN,
    A_load: 5 * u.cm**2,
}
params.update(_p)  # Save to global

_e = {
    sigma_d: "F_d / A_load" | pc.parse_expr
}
eqn.update(_e)     # Save to global

_v = {
    k: v | pc.subs(eqn | params) | pc.convert_to([u.MPa]) | pc.N
    for k, v in _e.items()
}
show_eqn([_p | _e, _v])

# === Second Calculation Cell (uses previous results) ===
sigma_Rk, sigma_Rd, gamma_M0 = symbols(r"\sigma_{Rk}, \sigma_{Rd}, \gamma_{M0}")

_p = {
    sigma_Rk: 275 * u.MPa,
    gamma_M0: 1.05,
}
params.update(_p)

_e = {
    sigma_Rd: "sigma_Rk / gamma_M0" | pc.parse_expr
}
eqn.update(_e)

# Note: Uses global eqn|params union
_v = {
    k: v | pc.subs(eqn | params) | pc.convert_to([u.MPa]) | pc.N
    for k, v in _e.items()
}
show_eqn([_p | _e, _v], float_format=":.2f")
```

### Pattern 3: Verification/Check Pattern

Use for design checks and verification:

```python
sigma_Sd, sigma_Rd, tau_Sd, tau_Rd = symbols(
    r"\sigma_{Sd}, \sigma_{Rd}, \tau_{Sd}, \tau_{Rd}"
)

_p = {
    sigma_Sd: 20 * u.MPa,
    tau_Sd: 15 * u.MPa,
    sigma_Rd: 250 * u.MPa,
    tau_Rd: 75 * u.MPa,
}

# List of expressions to verify
_expr = [
    sigma_Sd / sigma_Rd,
    tau_Sd / tau_Rd,
]

# Evaluate expressions (use expression as key!)
_v = {
    k: k | pc.subs(_e | _p) | pc.N
    for k in _expr
}

# Check if expressions are less than 1
_c = {
    k: check(v, 1.0) for k, v in _v.items()
}

show_eqn([_p | _v, _c])
```

### Pattern 4: Complete Documentation (With Descriptions & Labels)

Use for production notebooks with full documentation and cross-references:

```python
F, A_load, sigma_Sd = symbols(r"F, A_{load}, \sigma_{Sd}")

# Parameters
_p = {
    F: 100 * u.kN,
    A_load: 20 * u.cm**2,
}

# Expressions
_e = {
    sigma_Sd: "F / A_load" | pc.parse_expr
}

# Evaluation
_v = {
    k: v | pc.subs(_p | _e) | pc.convert_to([u.MPa]) | pc.N
    for k, v in _e.items()
}

# Descriptions for documentation
_d = {
    F: "applied force",
    A_load: "cross-sectional area",
    sigma_Sd: "normal stress",
}

# Labels for cross-references
_l = {
    k: generate_unique_label([k, v]) for k, v in _d.items()
}

show_eqn([_p | _e, _v, _d], label=_l, float_format="{:.2f}")
```

## Pipe Command Patterns

Keecas uses pipe operators (`|`) for functional composition. This enables clean, readable operation chains.

### Common Pipe Chains

```python
# Parse string to expression
expr = "F / A" | pc.parse_expr

# Standard evaluation chain
result = expr | pc.subs(params) | pc.convert_to([u.MPa]) | pc.N

# Full chain from string
value = "F / A" | pc.parse_expr | pc.subs(eqn | params) | pc.convert_to([u.MPa]) | pc.N

# Symbolic manipulation without numerical evaluation
expr = expression | pc.subs(params) | pc.doit()
```

### Dict Comprehension Pattern (Most Common)

The most common pattern uses dict comprehensions to evaluate multiple expressions:

```python
# Evaluate all expressions in _e
_v = {
    k: v | pc.subs(eqn | params) | pc.convert_to([u.MPa]) | pc.N
    for k, v in _e.items()
}

# Check multiple expressions
_c = {
    k: check(v, 1.0) for k, v in _v.items()
}

# Evaluate list of expressions (expression as key!)
_expr = [sigma_Sd / sigma_Rd, tau_Sd / tau_Rd]
_v = {
    k: k | pc.subs(eqn | params) | pc.N
    for k in _expr
}
```

### Union Pattern for Substitution

Use the union operator (`|`) to combine dictionaries before passing to `pc.subs`:

```python
# Combine cell-local dicts
_v = {k: v | pc.subs(_e | _p) for k, v in _e.items()}

# Use global dicts
_v = {k: v | pc.subs(eqn | params) for k, v in _e.items()}

# Multiple unions (right-to-left precedence)
_v = {k: v | pc.subs(eqn | params | _p) for k, v in _e.items()}
```

## Float Formatting

Control numerical precision with flexible formatting options.

### Global Format (All Cells)

Apply the same format to all numerical values:

```python
show_eqn([_p | _e, _v], float_format="{:.2f}")

# Shorthand without curly braces
show_eqn([_p | _e, _v], float_format=".2f")
```

### Per-Column Format (List)

Different format for each column:

```python
# Column 0: no format, Column 1: .2f, Column 2+: .4f
show_eqn([_p | _e, _v, _d], float_format=['', '.2f', '.4f'])
```

### Per-Row Format (Dict)

Different format for each row (symbol):

```python
_f = {
    F: '{:.1f}',       # Applied to all values in F row
    A_load: '{:.2f}',  # Applied to all values in A_load row
    sigma_Sd: '.3f',   # Applied to all values in sigma_Sd row
}
show_eqn([_p | _e, _v], float_format=_f)
```

### Per-Cell Format (Dict of Lists)

Most granular control - format individual cells:

```python
_ff = {
    sigma_Sd: [None, "{:.3f}", None],  # Only format middle column
    tau_Sd: ['.2f', '.3f', None],      # Format first two columns
}
show_eqn([_p | _v, _c], float_format=_ff)
```

### Configuration Default

Set a global default for all notebooks:

```python
# Set default precision
config.display.default_float_format = ".3f"

# All show_eqn calls use this unless overridden
show_eqn([_p | _e, _v])  # Uses .3f
show_eqn([_p | _e, _v], float_format=".5f")  # Override to .5f
```

## Label Generation

Labels enable cross-referencing equations in your document.

### Method 1: Manual Labels (Full Control)

Manually assign LaTeX-safe label strings:

```python
_l = {
    J: "eq-moment-of-inertia",
    E: "eq-modulus-of-elasticity",
    a: "eq-an-expression",
}

show_eqn(_p, label=_l)
```

Reference in markdown: `\eqref{eq-moment-of-inertia}`

### Method 2: Semi-Automatic with `generate_label`

Provide LaTeX-safe descriptions (no spaces), automatically add `eq-` prefix:

```python
_l = {
    J: "moment-of-inertia",
    E: "modulus-of-elasticity",
    a: "an-expression",
}

# Generate labels with eq- prefix
_l = generate_label(_l)

show_eqn(_p, label=_l)
```

### Method 3: Unique Hashed Labels (Recommended)

Generate unique labels from descriptions with spaces (automatically converted):

```python
_d = {
    J: "moment of inertia",
    E: "modulus of elasticity",
    a: "an expression",
}

# Generate unique hashed labels
_l = generate_unique_label(_d)

# Save for later reference
labels = _l

show_eqn(_p, label=_l)
```

**Advantages**:
- No manual label management
- Handles spaces and special characters
- Unique hashes prevent collisions
- Stable across sessions if input doesn't change

### Method 4: Fully Automatic

Pass the callable directly to generate labels from all row data:

```python
# Labels generated from key + all values in each row
show_eqn([_p, _d], label=generate_unique_label)
```

**Note**: Labels change if any value in the row changes. For stability, use Method 3.

### Referencing Labels

In markdown cells or strings:

```python
# Helper function for easy referencing
from IPython.display import Markdown

def eqref(label):
    return Markdown(rf"\eqref{{{label}}}")

# In inline Python: {python} eqref(labels[J])
# Or directly: \eqref{eq-PREFIX-hash}
```

## Configuration Setup

### Minimal Setup (Quick Start)

For quick notebooks and prototyping:

```python
from keecas import show_eqn, symbols, u, pc, config

# Essential settings
config.display.katex = True              # For Jupyter dev mode
config.display.print_label = True        # Print labels for copy-paste
config.latex.eq_prefix = "eq-PREFIX-"    # Namespace your labels
```

### Complete Setup (Production Notebooks)

For production documents with full features:

```python
from keecas import (
    show_eqn,
    check,
    symbols,
    u,
    pc,
    generate_unique_label,
    config,
)

# Language and localization
config.language.language = 'it'  # 'en', 'de', 'es', 'fr', 'it', 'pt'

# Display settings
config.display.katex = True                   # Disable \label{} for KaTeX
config.display.print_label = True             # Print labels in dev mode
config.display.default_float_format = ".3f"   # Default float precision

# LaTeX settings
config.latex.eq_prefix = "eq-NOTEBOOK_NAME-"  # Unique prefix per notebook
config.latex.default_environment = "align"    # Default environment

# Initialize global dicts
params = {}
eqn = {}
```

### Quarto-Specific Configuration

For Quarto notebooks with equation numbering and cross-references, add to YAML frontmatter:

```yaml
---
title: "Your Document Title"
format:
  html:
    include-in-header:
      # Enable equation numbering
      - text: |
          <script>
          MathJax = { tex: { tags: 'ams' } };
          </script>
      # Prevent horizontal scrollbars
      - text: |
          <style>
          .math.display {
            max-width: 100%;
            padding-right: 3em;
          }
          </style>
  pdf:
    echo: false
---
```

**Important**:
- Set `config.display.katex = False` when rendering with Quarto
- Set `config.display.katex = True` during Jupyter development (VS Code)

## Common Pitfalls

### Pitfall 1: LaTeX vs Plain Symbol Notation

**Problem**: Using plain notation creates different symbol objects.

```python
# ❌ WRONG: Two different symbols
sigma_latex = symbols(r"\sigma_{Sd}")
sigma_plain = symbols("sigma_Sd")

sigma_latex == sigma_plain  # False!

# Substitution fails
_p = {sigma_latex: 100*u.MPa}
expr = sigma_plain / A  # Won't substitute!
```

**Solution**: Always use LaTeX notation.

```python
# ✅ CORRECT: Consistent LaTeX notation
sigma_Sd = symbols(r"\sigma_{Sd}")

_p = {sigma_Sd: 100*u.MPa}
expr = sigma_Sd / A  # Substitutes correctly
```

### Pitfall 2: Using `vals` in `pc.subs()`

**Problem**: Passing evaluated values prevents recalculation when parameters change.

```python
# Initial calculation
params = {x: 2}
eqn = {y: "x + 1" | pc.parse_expr, z: "y^2" | pc.parse_expr}
vals = {k: v | pc.subs(eqn | params) | pc.N for k, v in eqn.items()}

# Update parameter
params.update({x: 3})

# ❌ WRONG: vals has stale values (y=3, z=9 from x=2)
_v_incorrect = {
    k: eqn[k] | pc.subs(eqn | params | vals)
    for k in [y, z]
}
# Result: y=3, z=9 (WRONG! Should be y=4, z=16)
```

**Solution**: Don't pass `vals` to `pc.subs`.

```python
# ✅ CORRECT: Fresh calculation
_v_correct = {
    k: eqn[k] | pc.subs(eqn | params)
    for k in [y, z]
}
# Result: y=4, z=16 (correct with x=3)
```

### Pitfall 3: Comma in Symbol Names

**Problem**: Commas create multiple symbols instead of one.

```python
# ❌ WRONG: Creates two symbols
tau_1_Rd, extra = symbols(r"\tau_{1,Rd}")  # Comma splits into two!
```

**Solution**: Escape commas with `\,` for spacing.

```python
# ✅ CORRECT: Single symbol with spacing
tau_1_Rd = symbols(r"\tau_{1\,Rd}")
```

### Pitfall 4: Forgetting Unit Conversions

**Problem**: Units display in original form, not desired units.

```python
# ❌ LESS IDEAL: Displays as N/mm²
stress = 100 * u.N / u.mm**2
show_eqn({sigma: stress})  # Shows: sigma = 100 N/mm²
```

**Solution**: Explicitly convert to desired units.

```python
# ✅ BETTER: Converts to MPa
stress = 100 * u.N / u.mm**2
_v = {
    sigma: stress | pc.convert_to([u.MPa])
}
show_eqn(_v)  # Shows: sigma = 100 MPa
```

### Pitfall 5: Out-of-Order Dependencies

**Not actually a problem!** Keecas handles dependency ordering automatically.

```python
# ✅ NO PROBLEM: Define in any order
_e = {
    result: "sqrt(a^2 + b^2) / intermediate" | pc.parse_expr,  # Uses intermediate
    intermediate: "a * b" | pc.parse_expr,  # Defined after result
}

# pc.subs automatically sorts topologically
_v = {k: v | pc.subs(_e | _p) for k, v in _e.items()}
```

## Multi-Cell Calculation Workflows

### Sequential Dependency Pattern

Build calculations across multiple cells, with each cell depending on previous results:

```python
# === Setup Cell ===
params = {}
eqn = {}

# === Cell 1: Foundation Parameters ===
F, A = symbols(r"F, A")
_p = {
    F: 100 * u.kN,
    A: 50 * u.cm**2,
}
params.update(_p)
show_eqn(_p)

# === Cell 2: Derived Calculations (uses Cell 1) ===
sigma = symbols(r"\sigma")
_e = {sigma: "F / A" | pc.parse_expr}
eqn.update(_e)

_v = {
    k: v | pc.subs(eqn | params) | pc.convert_to([u.MPa]) | pc.N
    for k, v in _e.items()
}
show_eqn([_e, _v])

# === Cell 3: Further Derivations (uses Cell 1 & 2) ===
sigma_allow = symbols(r"\sigma_{allow}")
_p = {sigma_allow: 200 * u.MPa}
params.update(_p)

# Check utilization
utilization = sigma / sigma_allow

_v = {
    utilization: utilization | pc.subs(eqn | params) | pc.N
}

_c = {
    utilization: check(_v[utilization], 1.0)
}

show_eqn([_p, _v, _c])
```

### Recalculation After Parameter Changes

Update parameters and recalculate specific expressions:

```python
# === Initial Calculation ===
x, y, z = symbols(r"x, y, z")

_p = {x: 2}
params.update(_p)

_e = {
    y: "x + 1" | pc.parse_expr,
    z: "y^2" | pc.parse_expr,
}
eqn.update(_e)

_v = {k: v | pc.subs(eqn | params) | pc.N for k, v in _e.items()}
show_eqn([_p | _e, _v])

# === Later Cell: Update and Recalculate ===
_p = {x: 5}  # New value
params.update(_p)

# Recalculate specific expressions
expr_to_recalc = [y, z]
_v = {
    k: eqn[k] | pc.subs(eqn | params) | pc.N
    for k in expr_to_recalc
}

show_eqn([_p, _v])
```

### When to Use Global vs Cell-Local

**Use cell-local** (`_p`, `_e`) when:
- Calculation is self-contained
- Results won't be referenced later
- Quick prototyping

**Use global** (`params`, `eqn`) when:
- Multi-step calculations
- Parameters used across cells
- Need to update and recalculate
- Building complex documents

## Verification Patterns

### Simple Ratio Check

Check if a single value meets a criterion:

```python
sigma_Sd, sigma_Rd = symbols(r"\sigma_{Sd}, \sigma_{Rd}")

_p = {
    sigma_Sd: 150 * u.MPa,
    sigma_Rd: 200 * u.MPa,
}

# Calculate utilization
utilization = sigma_Sd / sigma_Rd | pc.subs(_p) | pc.N

# Check if less than or equal to 1.0
result = check(utilization, 1.0)  # Default: Le (<=)

show_eqn([_p, {utilization: result}])
```

### Multiple Checks

Check several expressions at once:

```python
sigma_Sd, sigma_Rd, tau_Sd, tau_Rd = symbols(
    r"\sigma_{Sd}, \sigma_{Rd}, \tau_{Sd}, \tau_{Rd}"
)

_p = {
    sigma_Sd: 20 * u.MPa,
    tau_Sd: 15 * u.MPa,
    sigma_Rd: 250 * u.MPa,
    tau_Rd: 75 * u.MPa,
}

# Expressions to verify
_expr = [
    sigma_Sd / sigma_Rd,
    tau_Sd / tau_Rd,
]

# Evaluate (expression as key!)
_v = {
    k: k | pc.subs(_e | _p) | pc.N
    for k in _expr
}

# Check all
_c = {
    k: check(v, 1.0) for k, v in _v.items()
}

show_eqn([_p | _v, _c])
```

### Different Test Types

Use different comparison operators:

```python
from sympy import Le, Ge, Lt, Gt, Eq

a, b, c, d, f = symbols("a, b, c, d, f")

_expr = {
    a: (3, Le, 1),   # Less than or equal: 3 <= 1
    b: (4, Gt, 2),   # Greater than: 4 > 2
    c: (5, Lt, 3),   # Strictly less than: 5 < 3
    d: (6, Ge, 4),   # Greater than or equal: 6 >= 4
    f: (7, Eq, 5),   # Equal: 7 == 5
}

_c = {
    k: check(lhs=v[0], test=v[1], rhs=v[2])
    for k, v in _expr.items()
}

show_eqn(
    [
        {k: v[0] for k, v in _expr.items()},
        _c,
    ],
)
```

### Custom Templates

Control the visual appearance of check results:

```python
# Different visual styles
_c = {
    k: check(v, 1.0, template="boxed")  # or "minimal", "default"
    for k, v in _v.items()
}

# Completely custom templates
custom_success = r"${symbol}{rhs}$ \textbf{PASS}"
custom_failure = r"${symbol}{rhs}$ \textbf{FAIL}"

result = check(
    0.8,
    1.0,
    success_template=custom_success,
    failure_template=custom_failure,
)
```

## Best Practices Checklist

### Symbol Definitions
- ✅ Always use LaTeX notation: `symbols(r"\sigma_{Sd}")`
- ✅ Escape commas in symbol names: `symbols(r"\tau_{1\,Rd}")`
- ❌ Never use plain notation: `symbols("sigma_Sd")`

### Dictionary Conventions
- ✅ Use underscore prefix for cell-local: `_p`, `_e`, `_v`, `_d`, `_l`, `_c`
- ✅ Use no prefix for global: `params`, `eqn`, `vals`
- ✅ Update global dicts after defining: `params.update(_p)`
- ❌ Don't use verbose names: `_parameters`, `_equations`

### Pipe Operations
- ✅ Use dict union operator: `_e | _p`
- ✅ Use dict comprehensions for evaluation
- ✅ Pass union to pc.subs: `pc.subs(eqn | params)`
- ❌ Don't pass `vals` to `pc.subs` (prevents recalculation)

### Organization
- ✅ Initialize global dicts at notebook start
- ✅ Set configuration at notebook start
- ✅ Use cell-local for standalone calculations
- ✅ Use global for multi-step workflows
- ❌ Don't mix patterns unnecessarily

### Display
- ✅ Use `generate_unique_label` for labels
- ✅ Save labels to global dict for referencing
- ✅ Specify float_format when precision matters
- ✅ Use descriptions for documentation

### Dependencies
- ✅ Let keecas handle dependency ordering
- ✅ Define expressions in logical order for readability
- ❌ Don't manually sort dependencies (keecas does this)

## Complete Example

Here's a small but complete example demonstrating all conventions:

```python
# === Imports and Configuration ===
from keecas import (
    show_eqn,
    check,
    symbols,
    u,
    pc,
    generate_unique_label,
    config,
)

# Configuration
config.display.katex = True
config.display.print_label = True
config.latex.eq_prefix = "eq-BEAM-"
config.display.default_float_format = ".2f"

# Initialize global dicts
params = {}
eqn = {}
labels = {}

# === Cell 1: Load Parameters ===
q, L = symbols(r"q, L")

_p = {
    q: 5 * u.kN / u.m,
    L: 8 * u.m,
}
params.update(_p)

_d = {
    q: "distributed load",
    L: "beam span",
}

_l = generate_unique_label(_d)
labels.update(_l)

show_eqn([_p, _d], label=_l)

# === Cell 2: Beam Deflection ===
E, I, delta = symbols(r"E, I, \delta")

_p = {
    E: 200 * u.GPa,
    I: 8360 * u.cm**4,
}
params.update(_p)

_e = {
    delta: "5 * q * L^4 / (384 * E * I)" | pc.parse_expr
}
eqn.update(_e)

_v = {
    k: v | pc.subs(eqn | params) | pc.convert_to([u.mm]) | pc.N
    for k, v in _e.items()
}

_d = {
    E: "elastic modulus",
    I: "moment of inertia",
    delta: "maximum deflection",
}

_l = generate_unique_label(_d)
labels.update(_l)

show_eqn([_p | _e, _v, _d], label=_l)

# === Cell 3: Verification ===
delta_allow = symbols(r"\delta_{allow}")

_p = {delta_allow: 30 * u.mm}
params.update(_p)

# Check utilization
utilization = delta / delta_allow

_v = {
    utilization: utilization | pc.subs(eqn | params) | pc.convert_to([u.dimensionless]) | pc.N
}

_c = {
    utilization: check(_v[utilization], 1.0)
}

_d = {
    delta_allow: "allowable deflection",
}

show_eqn([_p, _v, _c, _d], float_format={utilization: [None, '.3f', None]})
```

This example demonstrates:
- Proper imports and configuration
- Global dict initialization
- Symbol definition with LaTeX notation
- Multi-cell workflow with persistence
- Descriptions and labels
- Pipe command usage
- Verification checks
- Mixed float formatting

---

## Summary

Following these conventions will:
- **Improve readability** - Consistent patterns across notebooks
- **Reduce errors** - Standard workflows prevent common mistakes
- **Enable collaboration** - Others can understand and extend your work
- **Maintain documentation** - Labels and descriptions create self-documenting calculations

**Key Takeaway**: Use cell-local dicts (`_p`, `_e`, `_v`) for immediate calculations, global dicts (`params`, `eqn`) for multi-step workflows, always use LaTeX notation for symbols, and leverage pipe commands for clean operation chains.
