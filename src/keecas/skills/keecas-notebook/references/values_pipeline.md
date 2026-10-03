# The values pipeline - `pc.subs | pc.N | pc.convert_to | pc.N`

## Contents

- The chain and why `pc.N` comes first
- `pc.subs(eqn | params)`
- `pc.convert_to([...])` and per-symbol targets
- `pc.N`, `pc.N(precision)`, `pc.doit`
- Extracting a Python float
- `solve()` on a symbolic system
- Angles and trig functions
- `sympy.evaluate(False)` for substitution steps
- Computed values that downstream cells need

Every reported number is produced by:

```python
expr | pc.subs(eqn | params) | pc.N | pc.convert_to([base_unit, ...]) | pc.N
```

## The chain and why `pc.N` comes first

`pc.parse_expr` keeps expressions unevaluated, so after `pc.subs` a sum can remain a factor inside a product, e.g. `1000*mm*(-1*5*mm + 215*mm)` from `b*(h - c_nom - 5*u.mm)`, or anything with `(4 - pi)`. sympy's `convert_to` mishandles such a factor and can return a wrong unit and a wrong magnitude (`210000000 mm**3` instead of `210000 mm**2`), depending on the target unit (keecas#118). `pc.N` before `pc.convert_to` evaluates the sum and avoids it. The final `pc.N` evaluates the converted result.

`pc.N` works on sympy expressions only; a bare pint quantity (`30 * u.deg`) goes straight to `pc.convert_to`.

## `pc.subs(eqn | params)`

Substitutes expressions (`eqn`) and input values (`params`). Later dicts win on overlapping keys. For a one-off override, append a dict:

```python
v | pc.subs(eqn | params | {alpha: alpha_1})
```

## `pc.convert_to([...])` and per-symbol targets

Pass base units; sympy picks the power from the dimensions:

```python
pc.convert_to([u.mm])        # length -> mm, area -> mm**2, volume -> mm**3
pc.convert_to([u.cm])        # inertia -> cm**4, section modulus -> cm**3
pc.convert_to([u.MPa])       # stress -> MPa
pc.convert_to([u.kN, u.m])   # force -> kN, moment -> kN*m, line load -> kN/m
pc.convert_to([1])           # strip units from a dimensionless result
```

Compound targets (`[u.mm**2]`, `[u.kN * u.m]`) work, but don't use them: the point of base units is that you cannot ask for the wrong power.

Per-symbol targets: a dict of **lists**, indexed directly.

```python
_target_unit = {A_ct: [u.mm], A_s_min: [u.mm], sigma_s: [u.MPa]}
_v = {
    k: v | pc.subs(eqn | params) | pc.N | pc.convert_to(_target_unit[k]) | pc.N
    for k, v in _e.items()
}
```

If some symbols need no conversion, branch on membership:

```python
_v = {
    k: (
        v | pc.subs(eqn | params) | pc.N | pc.convert_to(_target_unit[k]) | pc.N
        if k in _target_unit
        else v | pc.subs(eqn | params) | pc.N
    )
    for k, v in _e.items()
}
```

## `pc.N`, `pc.N(precision)`, `pc.doit`

- `pc.N` evaluates numerically (15 significant digits); `pc.N(4)` uses 4.
- `pc.doit` forces evaluation of wrappers that survive (`Piecewise`, unevaluated `Max`). Append it when the result still shows a symbolic wrapper: `... | pc.N | pc.doit`.

## Extracting a Python float

For branching or feeding a library (`math.ceil`, `np.linspace`), extract after the pipeline. The result is a sympy product `number * unit`, so take its first argument:

```python
_d_m = float((d | pc.subs(eqn | params) | pc.N | pc.convert_to([u.m]) | pc.N).args[0])
```

The result is a sympy object, not a pint quantity: it has no `.magnitude`. A dimensionless result (`pc.convert_to([1])`) is already a number: `float(v)`.

## `solve()` on a symbolic system

`pc.parse_expr` turns `==` into an equation:

```python
from sympy import solve

_sistema = [
    "sigma_m == (T_1 + T_2) / 2 / (t * L)" | pc.parse_expr,
    "r == D / 2" | pc.parse_expr,
]
_s = solve(_sistema, [sigma_m, r], dict=True)[0]
eqn.update(_s)

_v = {k: v | pc.subs(eqn | params) | pc.N | pc.convert_to([u.mm, u.MPa]) | pc.N for k, v in _s.items()}
show_eqn([_s, _v], float_format=[None, None, "{:.2f}"], environment="cases")
```

## Angles and trig functions

sympy's `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2` take a dimensionless number (radians) and return a dimensionless number.

- **Inputs**: convert angle parameters with `[1]`, not `[u.rad]`, which keeps a unit trig cannot consume.

  ```python
  30 * u.deg | pc.convert_to([1])   # -> pi/6
  ```

- **Results**: never multiply by `u.rad`; it forces `pi*u.rad`-style balancing in every later formula.

  ```python
  # BAD
  alpha_e: "asin(k_e) * u.rad" | pc.parse_expr,
  # GOOD
  alpha_e: "asin(k_e)" | pc.parse_expr,
  theta_e: "varphi - pi + alpha_e" | pc.parse_expr,
  ```

- **Values**: end trig-derived symbols with `pc.convert_to([1])`:

  ```python
  _v = {k: v | pc.subs(eqn | params) | pc.N | pc.convert_to([1]) | pc.N for k, v in _e_angles.items()}
  ```

  If a result still carries units (e.g. `atan2` of two lengths), write the arguments as ratios: `"atan2((y_2 - y_1)/d, (x_2 - x_1)/d)"`.

- **Display in degrees**: re-attach `u.rad` only for display.

  ```python
  def _deg(v):
      """Dimensionless angle (radians) -> degrees, for display."""
      return (v * u.rad) | pc.convert_to([u.deg]) | pc.N

  show_eqn([_e_angles, {k: _deg(v) for k, v in _v.items()}], float_format=[None, None, "{:.2f}"])
  ```

  Keep the dimensionless value for any further computation.

## `sympy.evaluate(False)` for substitution steps

To show the formula with numbers substituted but not collapsed (e.g. `0.7 * 500 MPa * 84 mm**2 / 1.25`), substitute inside an `evaluate(False)` block, then evaluate separately:

```python
with sympy.evaluate(False):
    _uv = {F_Rd: F_Rd | pc.subs(eqn | params)}
_v = {F_Rd: _uv[F_Rd] | pc.N | pc.convert_to([u.kN]) | pc.N}
show_eqn([_e, _uv, _v], float_format=[None, None, None, "{:.2f}"])
```

## Computed values that downstream cells need

`params` holds inputs, `eqn` holds relationships. Never write a computed quantity into `params`:

```python
# BAD - number disconnected from any displayed formula
params[d] = (params[x_2] - params[x_1]).to(u.m)

# GOOD
_e = {d: "x_2 - x_1" | pc.parse_expr}
eqn.update(_e)
```

When a later notebook needs a computed number (expensive, or from a fit), store it in a separate `vals` dict (`vals.update({d: _v[d]})`), never in `params`.
