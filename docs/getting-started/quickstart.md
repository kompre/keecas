# Quick Start

This guide will get you up and running with Keecas in just a few minutes.

## Your First Calculation

Let's start with a simple engineering calculation - computing stress from force and area.

### 1. Import Keecas

```python
from keecas import symbols, u, pc, show_eqn, config
```

### 2. Define Symbols

Use LaTeX notation for beautiful symbol display:

```python
# Define symbols with LaTeX notation
F, A, sigma = symbols(r"F, A, \sigma")
```

### 3. Set Up Parameters

Define your parameters with units:

```python
# Cell-local parameters
_p = {
    F: 10 * u.kN,      # Force in kilonewtons
    A: 50 * u.cm**2,   # Area in square centimeters
}
```

### 4. Define Expressions

Create symbolic expressions:

```python
# Cell-local expressions
_e = {
    sigma: "F / A" | pc.parse_expr
}
```

### 5. Evaluate and Display

Compute values and display the results:

```python
# Evaluate expressions
_v = {
    k: v | pc.subs(_e | _p) | pc.convert_to([u.MPa]) | pc.N
    for k, v in _e.items()
}

# Display equations
show_eqn([_p | _e, _v])
```

This will produce beautiful LaTeX output showing both the symbolic equation and numerical result.

## Understanding the Pattern

Keecas follows a consistent pattern:

### Dictionary Conventions

| Dict | Purpose | Example |
|------|---------|---------|
| `_p` | Cell-local parameters | `_p = {F: 10*u.kN}` |
| `_e` | Cell-local expressions | `_e = {sigma: "F/A" \| pc.parse_expr}` |
| `_v` | Cell-local values | Evaluated results |

### Pipe Operations

Keecas uses pipe operators (`|`) for functional composition:

```python
# Chain operations together
result = expression | pc.subs(parameters) | pc.convert_to(units) | pc.N
```

Common pipe commands:
- `pc.parse_expr` - Parse string expressions
- `pc.subs(dict)` - Substitute values
- `pc.convert_to(units)` - Convert units
- `pc.N` - Numerical evaluation

## Configuration

Set up basic configuration for your document:

```python
# Configuration for LaTeX output
config.katex = True              # KaTeX compatibility
config.eq_prefix = "eq-"         # Equation label prefix
config.language = 'en'           # Language/locale
```

## Multi-Step Calculations

For complex calculations spanning multiple cells:

```python
# Setup cell (run once)
params = {}  # Global parameters
eqn = {}     # Global expressions

# First calculation cell
F, A, sigma = symbols(r"F, A, \sigma")

_p = {F: 10 * u.kN, A: 50 * u.cm**2}
params.update(_p)  # Save to global

_e = {sigma: "F / A" | pc.parse_expr}
eqn.update(_e)     # Save to global

_v = {k: v | pc.subs(eqn | params) | pc.convert_to([u.MPa]) | pc.N for k, v in _e.items()}
show_eqn([_p | _e, _v])

# Second calculation cell (uses previous results)
tau, gamma = symbols(r"\tau, \gamma")

_p = {gamma: 1.5}  # Safety factor
params.update(_p)

_e = {tau: "sigma / gamma" | pc.parse_expr}
eqn.update(_e)

_v = {k: v | pc.subs(eqn | params) | pc.N for k, v in _e.items()}
show_eqn([_p | _e, _v])
```

## Verification and Checks

Check if calculated values meet criteria:

```python
from keecas import check

# Check if stress is within allowable limits
sigma_max = 250 * u.MPa
result = check(sigma, sigma_max)  # Will show verification result
```

## CLI Quick Start

Use the Keecas CLI for quick setup:

```bash
# Create a new notebook with template
keecas edit my_calculation.ipynb --template quickstart

# Launch JupyterLab in current directory
keecas edit --dir .

# Show available templates
keecas edit --list-templates
```

## Next Steps

- Learn more about [Configuration](configuration.md)
- Explore [Conventions](../user-guide/conventions.md) for advanced patterns
- Check out [Examples](../user-guide/examples.md) for real-world use cases
- Review the [API Reference](../api-reference/display.md) for complete function documentation