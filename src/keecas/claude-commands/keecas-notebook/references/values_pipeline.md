# The values pipeline — `pc.subs / convert_to / N`

Every numeric value in a keecas notebook is produced by piping a symbolic expression through:

```
expression | pc.subs(eqn | params) | pc.convert_to([base_unit, ...]) | pc.N
```

Each stage has a purpose. Skipping or reordering them produces subtle bugs.

## The stages

### `pc.subs(eqn | params)`

Substitutes both the named expressions (`eqn`) and the numeric parameter values (`params`) into the expression. The order of merge matters when keys overlap — later wins, so `eqn | params` means "use parameter values to override symbolic placeholders".

Most calls use exactly `pc.subs(eqn | params)`. If you need to override a single symbol for a one-off calculation, append:

```python
v | pc.subs(eqn | params | {alpha: alpha_1, mu_i: mu_1(alpha)})
```

### `pc.convert_to([u.X, u.Y, ...])`

Converts the result into the listed **base** units. SymPy raises units to the right power based on the quantity's dimensions, so:

```python
pc.convert_to([u.mm])           # length → mm,   area → mm²,   volume → mm³
pc.convert_to([u.cm])           # area → cm²,   inertia → cm⁴, section modulus → cm³
pc.convert_to([u.MPa])          # stress → MPa
pc.convert_to([u.kN, u.m])      # moment → kN·m, force → kN
```

**Never pass compound units** like `u.mm**2`, `u.kN * u.m`, `u.cm**3`. They confuse sympy's unit machinery.

For per-symbol target units inside a single comprehension, use a `_target_unit` (or `_target`) dict:

```python
_target_unit = {A_ct: [u.mm], A_s_min: [u.mm], sigma_s: [u.MPa]}
_v = {
    k: v | pc.subs(eqn | params) | pc.convert_to(_target_unit[k]) | pc.N
    for k, v in _e.items()
}
```

If some symbols in `_e` should not be converted at all, fall back to a conditional in the comprehension:

```python
_v = {
    k: (v | pc.subs(eqn|params) | pc.N | pc.convert_to([_target_unit[k]]))
       if k in _target_unit
       else (v | pc.subs(eqn|params) | pc.N)
    for k, v in _e.items()
}
```

### `pc.N` and `pc.N(precision)`

Evaluates the expression to a numeric form. `pc.N` uses default precision; `pc.N(4)` evaluates to 4 significant digits — useful when downstream code converts to a pint `Quantity` and you want to control the precision at the symbolic stage.

### `pc.doit`

Forces evaluation of unevaluated structures (e.g. `Piecewise` after substitution). Add it when the pipeline result is still showing a symbolic wrapper instead of a number:

```python
v | pc.subs(eqn | params) | pc.convert_to([u.kN]) | pc.N | pc.doit
```

## When you need a Python float

To branch logically or to feed a Python library (e.g. `math.ceil`, `np.linspace`), extract the float **after** the pipeline:

```python
def _val_mm2(expr):
    return float((expr | pc.subs(eqn | params) | pc.convert_to([u.mm**2]) | pc.N).args[0])

# Note: pc.convert_to here uses mm**2 only because we're extracting .args[0] from a unit-bearing
# quantity; the result is a bare float in mm² regardless. Inside the pipeline itself,
# always use basic units.
```

Or with pint directly:

```python
A_inf = (A_s_inf | pc.subs(eqn | params) | pc.convert_to([u.mm]) | pc.N).magnitude
```

## `solve()` on a symbolic system

For systems of equations, use sympy's `solve` on `pc.parse_expr`-built equations:

```python
from sympy import solve

_sistema = [
    "sigma_theta_m == eqn[sigma_theta]"                          | pc.parse_expr,
    "sigma_theta_m == (T_SLU + T_hold) / 2 / (t * L_drum)"       | pc.parse_expr,
    "r == D_drum / 2"                                            | pc.parse_expr,
]

_s = solve(_sistema, [r, p_n, sigma_theta_m], dict=True)[0]
eqn.update(_s)
```

`_s` is now a dict `{symbol: expression}` that you can treat like any other `_e`:

```python
_v = {k: v | pc.subs(eqn | params) | pc.N | pc.convert_to([u.mm, u.MPa]) for k, v in _s.items()}
show_eqn([_s, _v], float_format="{:.2f}", environment="cases")
```

## Angles and trig functions

SymPy's trig functions (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`) treat their argument as a number in radians, but the argument and return value are both **dimensionless** — not `u.rad`-bearing quantities. Get this wrong and the pipeline silently produces unsimplifiable expressions.

### Stripping units before trig

When a unit-bearing quantity has to feed a trig function, convert it to dimensionless first:

```python
# 30° → its dimensionless radian-equivalent number (= π/6 ≈ 0.5236)
30 * u.deg | pc.convert_to([1])
```

The single-element list `[1]` tells `pc.convert_to` to strip units. `pc.convert_to([u.rad])` would *keep* the rad unit, which trig then can't consume.

### Trig arguments that are ratios of like-unit quantities

In a geometry calculation, an expression like `atan2(y_2 - y_1, x_2 - x_1)` has arguments that are both lengths — mathematically the result depends only on the ratio, so it's "morally" dimensionless. But SymPy doesn't always simplify `atan2(length, length)` automatically.

Force dimensionlessness by writing the trig argument as an explicit ratio of like-unit quantities:

```python
# GOOD — both atan2 arguments are dimensionless ratios after substitution
varphi: "atan2((y_2 - y_1)/d, (x_2 - x_1)/d)" | pc.parse_expr

# RISKY — atan2 receives two length quantities; may not simplify
varphi: "atan2(y_2 - y_1, x_2 - x_1)" | pc.parse_expr
```

This trick (dividing by a reference length `d` that you've already defined) leaves the result unchanged numerically but makes the unit cancellation obvious to SymPy.

### Don't attach `u.rad` to trig results

A trig result is dimensionless by convention. Multiplying by `u.rad` to "give it a unit" makes the downstream computation harder:

```python
# BAD — alpha_e now carries u.rad; combining with other angles needs unit-matched constants
alpha_e: "asin(k_e) * u.rad" | pc.parse_expr,
theta_e2: "varphi - pi*u.rad + alpha_e" | pc.parse_expr,   # need pi*u.rad to balance

# GOOD — keep everything dimensionless; pi is just π
alpha_e:  "asin(k_e)"             | pc.parse_expr,
theta_e2: "varphi - pi + alpha_e" | pc.parse_expr,
```

### Computing the dimensionless value

In the values pipeline, append `pc.convert_to([1])` for trig-derived symbols so any residual unit metadata is stripped:

```python
_v = {
    d:        d        | pc.subs(eqn | params) | pc.convert_to([u.m]) | pc.N,   # length → m
    k_e:      k_e      | pc.subs(eqn | params) | pc.convert_to([1])   | pc.N,   # ratio → dimensionless
    varphi:   varphi   | pc.subs(eqn | params) | pc.convert_to([1])   | pc.N,   # angle (rad) → dimensionless
    alpha_e:  alpha_e  | pc.subs(eqn | params) | pc.convert_to([1])   | pc.N,
    theta_e1: theta_e1 | pc.subs(eqn | params) | pc.convert_to([1])   | pc.N,
}
```

### Displaying an angle in degrees

After computing the dimensionless number (= angle in radians), present it in degrees by re-attaching `u.rad` and converting to `u.deg`:

```python
# v is a dimensionless number representing an angle in radians.
v_deg = (v * u.rad) | pc.convert_to([u.deg]) | pc.N
```

A small helper keeps the rest of the cell tidy:

```python
def _deg(v):
    """Dimensionless angle (radians) → u.deg quantity for display."""
    return (v * u.rad) | pc.convert_to([u.deg]) | pc.N

_v_display = {
    d:        _v[d],
    varphi:   _deg(_v[varphi]),
    alpha_e:  _deg(_v[alpha_e]),
    theta_e1: _deg(_v[theta_e1]),
}
```

Store the dimensionless form in `vals` if downstream notebooks consume the angle in further trig, and the degree-decorated form for display only.

## `sympy.evaluate(False)`

Wrap a `pc.subs` in `with sympy.evaluate(False):` when you want the displayed expression to keep its structure (e.g. show `0.7 * f_tbk * A_res / gamma_M7` literally with the substituted numbers rather than collapsed to a single number). The typical use is for displaying the numeric substitution step in a verification:

```python
with sympy.evaluate(False):
    _uv = {s_min: s_min | pc.subs(eqn | _mag)}
_v = {" ": (_uv[s_min] | pc.N)}
show_eqn([_uv | _v], float_format="{:.2f}")
```

## What NOT to do

```python
# BAD — parallel numpy computation; the displayed formula and the stored number
# are now independently maintained, and they will drift.
_x1 = float(params[x_1].to(u.m).magnitude)
_x2 = float(params[x_2].to(u.m).magnitude)
_d  = np.hypot(_x2 - _x1, ...)
params[d] = _d * u.m

# BAD — assigning a computed quantity directly into params with units re-attached
# breaks the convention that params holds *inputs* and eqn holds *relationships*.
params[d] = (params[x_2] - params[x_1]).to(u.m)
```

If a downstream notebook genuinely needs a precomputed numeric value (e.g. it's expensive or comes from a fit), define it as an entry in `vals` (the third dict in the section's result), not in `params`:

```python
SECTION = {
    "parametri":   (params := {}),
    "espressioni": (eqn    := {}),
    "valori":      (vals   := {}),
}

# ... later ...
vals.update({d: _v[d]})  # downstream notebooks read SECTION["valori"][d]
```
