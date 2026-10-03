# Minimal notebook skeleton (plain Jupyter)

## Contents

- Setup cell
- Input parameters
- Derived quantities (narrow formulas, description slot kept)
- Wide formulas (description in markdown above)
- Verification
- What this skeleton illustrates

A complete, copyable notebook. Each fenced block is one cell, in order. For a notebook rendered by Quarto, start from the skeleton in the `keecas-quarto` skill instead; it adds the Quarto init cells around the same calculation cells.

The `python` blocks in this file are executed by the keecas test suite, so they are known to run.

## Setup cell

```python
from keecas import *
from IPython.display import display, Markdown

params, eqn = {}, {}
```

## Input parameters

```markdown
## Slab - minimum reinforcement

Inputs for a 1 m strip of slab.
```

```python
h, b, c_nom = symbols(r"h b c_{nom}")
f_ck, f_yk = symbols(r"f_{ck} f_{yk}")

_p = {
    h: 250 * u.mm,
    b: 1000 * u.mm,
    c_nom: 35 * u.mm,
    f_ck: 25 * u.MPa,
    f_yk: 450 * u.MPa,
}
params.update(_p)

_d = {
    h: "spessore soletta",
    b: "larghezza di riferimento",
    c_nom: "copriferro",
    f_ck: "resist. car. cls",
    f_yk: "resist. car. acciaio",
}

show_eqn([_p, _d], label=generate_unique_label(_d))
```

Descriptions are short phrases and do not repeat values: the strip width is the `b` row, not part of a description.

## Derived quantities (narrow formulas, description slot kept)

```markdown
### Concrete tensile strength

Mean tensile strength, EC2 3.1.2 (valid for $f_{ck} \le 50$ MPa).
```

```python
f_ctm, f_ct_eff = symbols(r"f_{ctm} f_{ct,eff}")

_e = {
    f_ctm: "0.30 * (f_ck/u.MPa)^(2/3) * u.MPa" | pc.parse_expr,
    f_ct_eff: f_ctm,
}
eqn.update(_e)

_d = {
    f_ctm: "resist. media a trazione",
    f_ct_eff: "resist. efficace a trazione",
}

_v = {k: v | pc.subs(eqn | params) | pc.N | pc.convert_to([u.MPa]) | pc.N for k, v in _e.items()}

show_eqn(
    [_e, _v, _d],
    label=generate_unique_label(_d),
    float_format=[None, None, "{:.2f}", None],
)
```

The markdown cell gives context; it does not restate the formula as `$$...$$`, because `show_eqn` already renders it from `_e`.

## Wide formulas (description in markdown above)

```markdown
### Minimum flexural reinforcement

Effective depth of the bottom face, and the larger of the strength-based and geometric minimum (EC2 9.2.1.1).
```

```python
A_s_min, d_inf = symbols(r"A_{s,min} d_{inf}")

_e = {
    d_inf: "h - c_nom - 5*u.mm" | pc.parse_expr,
    A_s_min: "Max(0.26*f_ctm/f_yk*b*d_inf, 0.0013*b*d_inf)" | pc.parse_expr,
}
eqn.update(_e)

_d = {
    d_inf: "altezza utile inf.",
    A_s_min: "min. flessionale",
}

_v = {k: v | pc.subs(eqn | params) | pc.N | pc.convert_to([u.mm]) | pc.N for k, v in _e.items()}

show_eqn(
    [_e, _v],
    label=generate_unique_label(_d),
    float_format=[None, None, "{:.2f}"],
)
```

`_d` is not a slot here (the `Max(...)` row is wide), but it still feeds the labels. `pc.convert_to([u.mm])` gives `d_inf` in mm and `A_s_min` in mm**2. The `pc.N` before `pc.convert_to` matters: `5*u.mm` inside the sum would otherwise produce a wrong unit (keecas#118).

## Verification

```markdown
### Check

Provided reinforcement against the minimum.
```

```python
A_s_prov = symbols(r"A_{s,prov}")

_p = {A_s_prov: 524 * u.mm**2}
params.update(_p)

_v = {k: k | pc.subs(eqn | params) | pc.N | pc.convert_to([1]) | pc.N for k in [A_s_min / A_s_prov]}
_c = {k: check(v, 1) for k, v in _v.items()}

show_eqn([_p | _v, _c], float_format=[None, "{:.3f}", None])
```

`check()` takes **demand / capacity**: `A_s_min` is required, `A_s_prov` is provided, and the check passes when the ratio is <= 1.

## What this skeleton illustrates

- One setup cell; `params` and `eqn` are global, `_p/_e/_v/_d/_c` are per cell.
- Each block: symbols -> `_p` or `_e` -> `_d` -> `_v` via `pc.subs | pc.N | pc.convert_to | pc.N` -> `show_eqn`.
- Narrow blocks keep the description slot; wide blocks move the description to the markdown cell above and keep `_d` for labels.
- Markdown cells carry prose, never duplicate formulas.
- Verifications end with `check(demand / capacity, 1)`.
