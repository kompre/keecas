# Tables and plots

## Contents

- Tables: `df_to_latex`
  - Import boilerplate
  - Calls and options
  - Mid-cell rendering
  - pint-pandas columns
  - Merged lookup + derived tables
- Plots: Quarto cell options
- Cross-references
- Cell-option placement rules

## Tables: `df_to_latex`

`df_to_latex` is the single entry point for tabular output. Today it is a project helper in `_scripts/table_utils.py`; moving it into keecas is tracked in keecas#120 (when that lands, import it from keecas and drop the `sys.path` line). It handles:

- sympy objects in column headers, rendered as inline math;
- pint `No Unit` headers, stripped;
- locale-aware numbers (Italian default: `0,5`, not `0.5`);
- LaTeX or HTML output depending on `config.display.katex`;
- `longtable` + `booktabs` styling.

Never use `df.to_markdown()`, `print(df)` or a bare DataFrame as output.

### Import boilerplate

Once per notebook, after the init cells:

```python
import sys
sys.path.insert(0, str((PATH_PREFIX / "../..").resolve()))
from _scripts.table_utils import df_to_latex

import pandas as pd
import pint_pandas

pint_pandas.PintType.ureg = u
pint_pandas.PintType.ureg.formatter.default_format = ".2f~P"
```

Set the number of `..` to the notebook's depth below the project root.

### Calls and options

```python
df_to_latex(df)  # defaults: 2 decimals, Italian locale
df_to_latex(df, precision=3)
df_to_latex(df, column_format="lrrr")  # forwarded to the pandas Styler
df_to_latex(df, locale="it")
```

### Mid-cell rendering

Like `show_eqn`, it renders only as the last expression of the cell; otherwise wrap it:

```python
display(df_to_latex(df_main))
display(Markdown("Si osserva che ..."))
```

### pint-pandas columns

Cast quantity columns to `pint[...]` dtypes; their unit goes into the header:

```python
df = (
    pd.DataFrame.from_dict(parametri_zona_vento, orient="index")
    .rename_axis("ZONA")
    .astype({v_b_0: "pint[m/s]", a_0: "pint[m]"})
    .reset_index()
    .drop("regione", axis="columns")
)
```

### Merged lookup + derived tables

When a value is picked from a lookup table (e.g. a wind zone) and further quantities are derived from it, show **one** table: the selected lookup row, its derived columns, and the selector (`ZONA`) as the first column. Derived values still come from the pipeline:

```python
_records = []
for _as_val in _altezze_sito:
    _as_q = u.Quantity(_as_val)
    _subs = _base | params | eqn | {a_s: _as_q}
    _rec = {"ZONA": _zona, v_b_0: _base[v_b_0], a_0: _base[a_0], k_s: _base[k_s], a_s: _as_q}
    for _var in [c_a, c_r, v_b, v_r, q_r]:
        _val = _var | pc.subs(_subs) | pc.N | pc.convert_to([u.m, u.kPa]) | pc.N(4)
        _rec[_var] = u.Quantity(str(_val))
    _records.append(_rec)

_df_merged = pd.DataFrame(_records).astype({...}).pint.dequantify()
display(df_to_latex(_df_merged, column_format="crrrrrrrrrr"))
```

## Plots: Quarto cell options

Label and caption go in the cell that calls `plt.show()`:

```python
#| label: fig-coefficiente-esposizione
#| fig-cap: profilo del coefficiente di esposizione $c_e$ in funzione dell'altezza $z$

plt.plot(profilo_esposizione[c_e(z)], profilo_esposizione[z] / u.m, label="profilo del vento")
plt.legend()
plt.grid(linestyle="--")
plt.show()
```

Wrong:

```python
#| label: fig-setup  # <- option in a cell that does not produce the figure
fig, ax = plt.subplots()

# next cell
ax.plot(...)
plt.savefig("out.png", dpi=150)  # <- Quarto saves figures itself; savefig loses label and caption
plt.show()
```

Numpy is fine for computing plot points; a value that appears in the text must still come from the pipeline.

## Cross-references

In a markdown cell:

```markdown
Il profilo è riportato in @fig-coefficiente-esposizione e i valori in @tbl-pressioni.
```

Tables work the same way with `#| label: tbl-...` and `#| tbl-cap: ...`. Equation labels from `generate_unique_label` are cited as `@eq-...`; with `config.display.print_label = True`, `show_eqn` prints each row's `symbol: eq-...` label to stdout, ready to copy.

## Cell-option placement rules

| Option | Must be in the cell that |
|---|---|
| `#\| label: fig-...`, `#\| fig-cap:` | calls `plt.show()` |
| `#\| label: tbl-...`, `#\| tbl-cap:`, `#\| tbl-colwidths:` | ends with `df_to_latex(df)` |
| `#\| echo: false` | should hide its code |
| `#\| output: false` | should hide its output |

Building the DataFrame in one cell and displaying it in another is fine only if the `tbl-` options are on the displaying cell.
