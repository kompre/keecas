# Examples

This section provides practical examples demonstrating Keecas usage patterns for common engineering calculations.

## Basic Stress Calculation

Simple stress calculation from force and area.

```python
from keecas import symbols, u, pc, show_eqn, config

# Configure for engineering output
config.katex = True
config.eq_prefix = "eq-stress-"

# Define symbols
F, A, sigma = symbols(r"F, A, \sigma")

# Parameters
_p = {
    F: 150 * u.kN,     # Applied force
    A: 25 * u.cm**2,   # Cross-sectional area
}

# Expression
_e = {
    sigma: "F / A" | pc.parse_expr
}

# Evaluate
_v = {
    k: v | pc.subs(_e | _p) | pc.convert_to([u.MPa]) | pc.N
    for k, v in _e.items()
}

# Display
show_eqn([_p | _e, _v])
```

## Beam Deflection Calculation

Multi-step calculation with global parameters.

```python
# Setup global containers
params = {}
eqn = {}

# Material and geometric properties
E, I, L, q = symbols(r"E, I, L, q")

_p = {
    E: 210 * u.GPa,        # Young's modulus
    I: 8196 * u.cm**4,     # Second moment of area
    L: 6 * u.m,            # Beam length
    q: 25 * u.kN/u.m,      # Distributed load
}
params.update(_p)

# Maximum deflection for simply supported beam
delta_max = symbols(r"\delta_{max}")

_e = {
    delta_max: "5 * q * L^4 / (384 * E * I)" | pc.parse_expr
}
eqn.update(_e)

_v = {
    k: v | pc.subs(eqn | params) | pc.convert_to([u.mm]) | pc.N
    for k, v in _e.items()
}

show_eqn([_p | _e, _v])
```

## Verification with Safety Factors

Engineering verification with limit checks.

```python
from keecas import check

# Define resistances and loads
N_Ed, N_Rd, gamma_f = symbols(r"N_{Ed}, N_{Rd}, \gamma_f")

# Load case
_p = {
    N_Ed: 450 * u.kN,     # Design load
    N_Rd: 750 * u.kN,     # Design resistance
    gamma_f: 1.5,         # Safety factor
}

# Utilization ratio
eta = symbols(r"\eta")
_e = {
    eta: "N_Ed / N_Rd" | pc.parse_expr
}

_v = {
    k: v | pc.subs(_e | _p) | pc.N
    for k, v in _e.items()
}

show_eqn([_p | _e, _v])

# Verification check
verification = check(eta | pc.subs(_e | _p), 1.0)
```

## Complex Symbol Notation

Working with complex engineering symbols.

```python
# Complex symbols with subscripts and special characters
sigma_x, sigma_y, tau_xy = symbols(r"\sigma_x, \sigma_y, \tau_{xy}")
sigma_1, sigma_2, sigma_v = symbols(r"\sigma_1, \sigma_2, \sigma_v")

# Principal stress calculation
_p = {
    sigma_x: 100 * u.MPa,
    sigma_y: 60 * u.MPa,
    tau_xy: 40 * u.MPa,
}

# Principal stresses
_e = {
    sigma_1: "(sigma_x + sigma_y)/2 + sqrt(((sigma_x - sigma_y)/2)^2 + tau_xy^2)" | pc.parse_expr,
    sigma_2: "(sigma_x + sigma_y)/2 - sqrt(((sigma_x - sigma_y)/2)^2 + tau_xy^2)" | pc.parse_expr,
}

# Von Mises stress
_e.update({
    sigma_v: "sqrt(sigma_1^2 - sigma_1*sigma_2 + sigma_2^2)" | pc.parse_expr
})

_v = {
    k: v | pc.subs(_e | _p) | pc.N
    for k, v in _e.items()
}

show_eqn([_p | _e, _v])
```

## Unit Conversion Examples

Working with different unit systems.

```python
# Pressure conversion
P, F, A = symbols(r"P, F, A")

_p = {
    F: 500 * u.lbf,        # Force in pounds
    A: 2.5 * u.inch**2,    # Area in square inches
}

_e = {
    P: "F / A" | pc.parse_expr
}

# Convert to different units
_v_psi = {
    k: v | pc.subs(_e | _p) | pc.convert_to([u.psi]) | pc.N
    for k, v in _e.items()
}

_v_mpa = {
    k: v | pc.subs(_e | _p) | pc.convert_to([u.MPa]) | pc.N
    for k, v in _e.items()
}

show_eqn([_p | _e, _v_psi])
show_eqn([{"Pressure in MPa": ""}, _v_mpa])
```

## Temperature-Dependent Properties

Calculations with temperature effects.

```python
# Temperature-dependent material properties
E_0, alpha, T, T_0 = symbols(r"E_0, \alpha, T, T_0")
E_T = symbols(r"E(T)")

_p = {
    E_0: 200 * u.GPa,              # Reference modulus at T_0
    alpha: -0.0004 / u.degC,       # Temperature coefficient
    T: 80 * u.degC,                # Operating temperature
    T_0: 20 * u.degC,              # Reference temperature
}

_e = {
    E_T: "E_0 * (1 + alpha * (T - T_0))" | pc.parse_expr
}

_v = {
    k: v | pc.subs(_e | _p) | pc.N
    for k, v in _e.items()
}

show_eqn([_p | _e, _v])
```

## Multi-Language Support

Using different languages for output.

```python
# Italian configuration
config.language = 'it'

# Steel verification (in Italian)
f_y, gamma_M0, sigma_Ed = symbols(r"f_y, \gamma_{M0}, \sigma_{Ed}")

_p = {
    f_y: 355 * u.MPa,
    gamma_M0: 1.0,
    sigma_Ed: 280 * u.MPa,
}

# Resistance calculation
f_d = symbols(r"f_d")
_e = {
    f_d: "f_y / gamma_M0" | pc.parse_expr
}

_v = {
    k: v | pc.subs(_e | _p) | pc.N
    for k, v in _e.items()
}

show_eqn([_p | _e, _v])

# Verification (will show in Italian)
verification = check(sigma_Ed, f_d | pc.subs(_e | _p))
```

## Matrix Operations

Working with matrices and vectors.

```python
import numpy as np
from keecas import Matrix

# Stress transformation matrix
theta = symbols(r"\theta")
T = symbols(r"T")

_p = {
    theta: 30 * u.deg,  # Rotation angle
}

# Transformation matrix (using SymPy Matrix)
_e = {
    T: Matrix([
        ["cos(theta)^2", "sin(theta)^2", "2*sin(theta)*cos(theta)"],
        ["sin(theta)^2", "cos(theta)^2", "-2*sin(theta)*cos(theta)"],
        ["-sin(theta)*cos(theta)", "sin(theta)*cos(theta)", "cos(theta)^2 - sin(theta)^2"]
    ]) | pc.parse_expr
}

# Convert angle to radians and evaluate
_v = {
    k: v | pc.subs(_p | {theta: _p[theta].to(u.rad).magnitude}) | pc.N
    for k, v in _e.items()
}

show_eqn([_p | _e, _v])
```

## Dynamic Loading

Time-dependent analysis with harmonic loading.

```python
import math

# Harmonic loading
F_0, omega, t, F_t = symbols(r"F_0, \omega, t, F(t)")

_p = {
    F_0: 100 * u.kN,        # Amplitude
    omega: 2 * math.pi * u.Hz,  # Frequency
    t: 0.25 * u.s,          # Time
}

_e = {
    F_t: "F_0 * sin(omega * t)" | pc.parse_expr
}

_v = {
    k: v | pc.subs(_e | _p) | pc.N
    for k, v in _e.items()
}

show_eqn([_p | _e, _v])
```

## Label Management

Working with equation labels and references.

```python
# Generate labels for cross-referencing
config.eq_prefix = "eq-example-"

F, A, sigma = symbols(r"F, A, \sigma")

_p = {F: 100 * u.kN, A: 20 * u.cm**2}
_e = {sigma: "F / A" | pc.parse_expr}
_v = {k: v | pc.subs(_e | _p) | pc.convert_to([u.MPa]) | pc.N for k, v in _e.items()}

# Generate labels
_l = {k: str(k).replace("\\", "").replace("{", "").replace("}", "") for k in _e.keys()}

show_eqn([_p | _e, _v], label=_l)

# Now you can reference this equation in text as: \eqref{eq-example-sigma}
```

## Error Handling

Dealing with common calculation errors.

```python
# Safe division with error handling
try:
    F, A = symbols(r"F, A")
    sigma = symbols(r"\sigma")

    _p = {
        F: 100 * u.kN,
        A: 0 * u.cm**2,  # This will cause division by zero
    }

    _e = {sigma: "F / A" | pc.parse_expr}

    _v = {
        k: v | pc.subs(_e | _p) | pc.N
        for k, v in _e.items()
    }

    show_eqn([_p | _e, _v])

except Exception as e:
    print(f"Calculation error: {e}")
    print("Check input parameters for physical validity")
```

## Tips for Effective Use

### Organizing Complex Calculations

1. **Use descriptive comments** for each calculation section
2. **Group related parameters** in logical dictionaries
3. **Use consistent naming** across related calculations
4. **Document assumptions** clearly

### Performance Optimization

1. **Reuse global dictionaries** for repeated calculations
2. **Cache expensive computations** in global variables
3. **Use appropriate precision** for your application

### Debugging Strategies

1. **Enable debug mode**: `config.debug = True`
2. **Print intermediate results** for verification
3. **Use simple test cases** to validate complex expressions
4. **Check units** at each step of calculation

These examples demonstrate the flexibility and power of Keecas for engineering calculations. Start with simple patterns and gradually incorporate more advanced features as needed.