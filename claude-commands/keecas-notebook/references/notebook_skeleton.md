# Minimal notebook skeleton

A complete, copyable skeleton for a new `__<section>.ipynb`. Replace `<SECTION>`, `<eq-prefix>`, and the example calculation with the real content.

The skeleton below is shown as a sequence of cells separated by `--- CELL ---`. Each cell is a `{python}` code block or a Quarto include / markdown cell, in the order it appears in the notebook.

---

## Front matter (raw YAML, top of notebook)

```yaml
---
jupyter: python3
---
```

No `title:` field — the title comes from the first markdown `##` heading.

--- CELL --- *(code, tagged init)*

```python
#| tags:
#|   - inizializzazione
#| label: INIZIO CALCOLO <SECTION>

import matplotlib.pyplot as plt
from keecas import *
from keecas.label import generate_unique_label

from ruamel.yaml import YAML
yaml = YAML()
yaml.preserve_quotes = True

from pathlib import Path
from IPython.display import display, Markdown

try:
    PATH_PREFIX
except NameError:
    PATH_PREFIX = './'

PATH_PREFIX = Path(PATH_PREFIX)
```

--- CELL --- *(code, config)*

```python
config.latex.eq_prefix = "eq-<SECTION>-"
config.display.print_label = True
config.display.katex = True

<SECTION> = {
    "parametri":   (params := {}),
    "espressioni": (eqn    := {}),
    "valori":      (vals   := {}),
}
```

--- CELL --- *(Quarto include — not a code cell)*

```
{{< include /_scripts/_KaTeX_compatibility.qmd >}}
```

--- CELL --- *(optional `%run` of a shared base — only if the notebook depends on one)*

```python
#| output: false
#| eval: false

%run ../../shared/__materiali.ipynb
```

The `%run` cell must come **before** any local symbol definitions.

--- CELL --- *(markdown — first heading and prose intro)*

```markdown
## <Title of the section>

Breve descrizione del calcolo, riferimenti normativi (es. NTC 2018 § X.Y, EC2 § Z.W) e ipotesi di base.
```

--- CELL --- *(code — input parameters)*

```python
h, b, c_nom = symbols(r"h b c_{nom}")
f_ck, f_yk  = symbols(r"f_{ck} f_{yk}")

_p = {
    h:     250 * u.mm,
    b:     1000 * u.mm,
    c_nom: 35 * u.mm,
    f_ck:  25 * u.MPa,
    f_yk:  450 * u.MPa,
}
params.update(_p)

_l = {
    h:     "spessore della platea",
    b:     "larghezza di riferimento (striscia di 1 m)",
    c_nom: "copriferro netto al lembo barra",
    f_ck:  "resistenza caratteristica cilindrica del calcestruzzo",
    f_yk:  "resistenza caratteristica di snervamento dell'acciaio",
}

show_eqn([_p, _l], label=generate_unique_label(_l))
```

--- CELL --- *(markdown — prose introducing the next calculation)*

```markdown
### Caratteristiche meccaniche derivate

La resistenza media a trazione del calcestruzzo è calcolata secondo EC2 § 3.1.6
(per $f_{ck} \le 50\text{ MPa}$).
```

Note: do NOT restate the formula as `$$...$$` here. The next code cell will display it via `show_eqn`.

--- CELL --- *(code — derived expressions)*

```python
f_ctm, f_ct_eff = symbols(r"f_{ctm} f_{ct\,eff}")

_e = {
    f_ctm:    "N(0.30) * (f_ck/u.MPa)^(2/3) * u.MPa" | pc.parse_expr,
    f_ct_eff: f_ctm,
}
eqn.update(_e)

_l = {
    f_ctm:    "resistenza media a trazione del calcestruzzo",
    f_ct_eff: "resistenza efficace a trazione al momento della fessurazione",
}

_v = {k: v | pc.subs(eqn | params) | pc.convert_to([u.MPa]) | pc.N for k, v in _e.items()}

show_eqn(
    [_e, _v, _l],
    label=generate_unique_label(_l),
    float_format=[None, None, "{:.2f}"],
)
```

--- CELL --- *(markdown — verification preamble)*

```markdown
### Verifica del minimo flessionale — NTC § 4.1.6.1.1 / EC2 § 9.2.1.1

Il minimo è il massimo fra il termine proporzionale a $f_{ctm}/f_{yk}$ e il
termine geometrico minimo (0,13%).
```

--- CELL --- *(code — verification)*

```python
A_s_min, d_inf = symbols(r"A_{s\,min} d_{inf}")

_e = {
    d_inf:   "h - c_nom - 5*u.mm"                                  | pc.parse_expr,
    A_s_min: "Max(N(0.26)*f_ctm/f_yk*b*d_inf, N(0.0013)*b*d_inf)"  | pc.parse_expr,
}
eqn.update(_e)

_l = {
    d_inf:   "altezza utile faccia inferiore",
    A_s_min: "minimo flessionale di armatura",
}

_target_unit = {d_inf: [u.mm], A_s_min: [u.mm]}
_v = {k: v | pc.subs(eqn | params) | pc.convert_to(_target_unit[k]) | pc.N for k, v in _e.items()}

show_eqn(
    [_e, _v, _l],
    label=generate_unique_label(_l),
    float_format=[None, None, "{:.2f}"],
)
```

--- CELL --- *(optional code — final esito with `check`)*

```python
A_s_prov = symbols(r"A_{s\,prov}")
_p_prov = {A_s_prov: 524 * u.mm**2}    # esempio: Ø10/150 per striscia di 1 m
params.update(_p_prov)

_ratio = A_s_min / A_s_prov
_v_ratio = _ratio | pc.subs(eqn | params) | pc.N

show_eqn(
    {_ratio: check(_v_ratio, 1)},
    float_format="{:.3f}",
)
```

`check()` argument is **demand / capacity**. Here `A_s_min` is the required minimum (demand) and `A_s_prov` is the disposed armature (capacity). The check passes when the ratio is ≤ 1.

---

## What this skeleton illustrates

- Init cells in fixed order; `generate_unique_label`, `display`, `Markdown` imported once at the top.
- KaTeX include between init and content.
- Each subsequent block follows the same shape: *symbols* → `_p` or `_e` → `_l` → `_v` (computed via the pipeline) → `show_eqn([..., _v, _l], label=generate_unique_label(_l), float_format=[None, None, "{:.2f}"])`.
- Markdown cells carry prose; they do not duplicate formulas as `$$...$$`.
- Verifications end with a `check(demand / capacity, 1)` rendered via `show_eqn`.

## Variant: wide expressions — descriptions in markdown, `_l` for labels only

The skeleton above renders `_l` as a column in every `show_eqn`. That works when descriptions are short and formulas are narrow. For `_e` blocks where the formula column is already wide (e.g. `atan2((y_2 - y_1)/d, (x_2 - x_1)/d)` or anything involving `Max(...)` / `Piecewise(...)`), the description column can push the table past the textwidth.

Alternate pattern for wide-formula blocks: expand the markdown cell above the code, and drop `_l` from the slot list while still using it for label anchors:

```markdown
<!-- markdown cell above the code -->
### Geometria della congiungente

La distanza fra i centri delle pulegge ($d$) e l'angolo della congiungente
rispetto all'orizzontale ($\varphi$) sono calcolati come segue.
```

```python
# code cell — _l is defined for label= but NOT slotted into the show_eqn list
_l = {
    d:      "distanza centri",
    varphi: "angolo congiungente",
}

_v = {k: v | pc.subs(eqn | params) | pc.convert_to(_target_unit[k]) | pc.N for k, v in _e.items()}

show_eqn(
    [_e, _v],
    label=generate_unique_label(_l),
    float_format="{:.4f}",
)
```

Keep `_l` entries short and LaTeX-clean either way — they get wrapped in `\text{...}` whenever they *are* rendered as a column.

When in doubt, copy the main skeleton and adapt rather than improvising a new structure.
