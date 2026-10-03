# Quarto notebook skeleton

## Contents

- Front matter
- Optional `%run` of a shared base
- Init cells
- Section heading and inputs
- Calculation cells
- Figure and table cells
- What this skeleton illustrates

A copyable `__<section>.ipynb` for a Quarto report. Replace `<SECTION>` and the example content. Each fenced block is one cell, in order. The calculation cells follow `keecas-notebook` (its `references/notebook_skeleton.md` has the same calculation as plain, tested Jupyter cells).

## Front matter

Raw cell at the top of the notebook:

```yaml
---
jupyter: python3
---
```

No `title:`; the section title is the first `##` heading.

## Optional `%run` of a shared base

Only if the notebook depends on a base notebook; it must be the very first code cell.

```python
#| output: false
#| eval: false
%run ../../shared/__materiali.ipynb
```

## Init cells

```python
#| tags: [inizializzazione]
#| label: INIZIO CALCOLO <SECTION>

import matplotlib.pyplot as plt
from keecas import *

from ruamel.yaml import YAML
yaml = YAML()
yaml.preserve_quotes = True

from pathlib import Path
from IPython.display import display, Markdown

try:
    PATH_PREFIX
except NameError:
    PATH_PREFIX = "./"

PATH_PREFIX = Path(PATH_PREFIX)
```

```python
config.latex.eq_prefix = "eq-<SECTION>-"
config.display.print_label = True
config.display.katex = True

<SECTION> = {
    "parametri": (params := {}),
    "espressioni": (eqn := {}),
    "valori": (vals := {}),
    "verifiche": (verifiche := {}),  # verification notebooks only
}
```

Raw Quarto line (not a code cell):

```
{{< include /_scripts/_KaTeX_compatibility.qmd >}}
```

## Section heading and inputs

```markdown
## Armatura minima platea

Calcolo dell'armatura minima della platea secondo NTC 2018 e EC2 9.2.1.1, per una striscia di larghezza unitaria.
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
    h: "spessore platea",
    b: "larghezza di riferimento",
    c_nom: "copriferro",
    f_ck: "resist. car. cls",
    f_yk: "resist. car. acciaio",
}

show_eqn([_p, _d], label=generate_unique_label(_d))
```

## Calculation cells

```markdown
### Armatura minima flessionale

Altezza utile della faccia inferiore e massimo fra il minimo di resistenza e il minimo geometrico (EC2 9.2.1.1).
```

```python
f_ctm, d_inf, A_s_min = symbols(r"f_{ctm} d_{inf} A_{s,min}")

_e = {
    f_ctm: "0.30 * (f_ck/u.MPa)^(2/3) * u.MPa" | pc.parse_expr,
    d_inf: "h - c_nom - 5*u.mm" | pc.parse_expr,
    A_s_min: "Max(0.26*f_ctm/f_yk*b*d_inf, 0.0013*b*d_inf)" | pc.parse_expr,
}
eqn.update(_e)

_d = {
    f_ctm: "resist. media a trazione",
    d_inf: "altezza utile inf.",
    A_s_min: "min. flessionale",
}

_target_unit = {f_ctm: [u.MPa], d_inf: [u.mm], A_s_min: [u.mm]}
_v = {k: v | pc.subs(eqn | params) | pc.convert_to(_target_unit[k]) | pc.N for k, v in _e.items()}

show_eqn(
    [_e, _v],
    label=generate_unique_label(_d),
    float_format=[None, None, "{:.2f}"],
)
```

The `Max(...)` row is wide, so the description is in the markdown cell above and `_d` only feeds the labels.

```markdown
### Verifica
```

```python
A_s_prov = symbols(r"A_{s,prov}")

_p = {A_s_prov: 524 * u.mm**2}
params.update(_p)

_v = {k: k | pc.subs(eqn | params) | pc.convert_to([u.mm]) | pc.N for k in [A_s_min / A_s_prov]}
_c = {k: check(v, 1) for k, v in _v.items()}
verifiche.update(_c)

show_eqn([_p | _v, _c], float_format=[None, "{:.3f}", None])
```

## Figure and table cells

```python
#| label: fig-<name>
#| fig-cap: <caption, may use $inline$ math>

plt.plot(...)
plt.grid(linestyle="--")
plt.show()
```

```python
#| label: tbl-<name>
#| tbl-cap: <caption>

df_to_latex(df)
```

See `tables_and_plots.md` for the `df_to_latex` import.

## What this skeleton illustrates

- `%run` (if any) first, then imports + `PATH_PREFIX`, config + section dict, KaTeX include.
- Markdown cells carry the heading and prose; formulas are rendered only by `show_eqn`.
- Narrow parameter blocks keep the description slot; wide expression blocks move it to the markdown above.
- Figure and table options sit in the producing cell.
