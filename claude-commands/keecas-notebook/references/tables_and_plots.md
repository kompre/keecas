# Tables and plots

## Tables: `df_to_latex`

The helper at `_scripts/table_utils.df_to_latex` is the single entry point for all tabular output. It handles:

- SymPy objects in column headers (rendered as inline math)
- pint `No Unit` headers (stripped)
- Italian locale for numbers (`0,5` not `0.5`)
- LaTeX vs HTML output depending on whether `config.display.katex` is on
- `longtable` + `booktabs` styling

### Import boilerplate (run once per notebook)

```python
import sys
sys.path.insert(0, str((PATH_PREFIX / '../..').resolve()))
from _scripts.table_utils import df_to_latex

import pandas as pd
import pint_pandas

pint_pandas.PintType.ureg = u
pint_pandas.PintType.ureg.formatter.default_format = '.2f~P'
```

Adjust the `..` count in the path-insertion line to match the notebook's depth relative to the project root (e.g. `'../../..'` if the notebook is nested deeper).

### Basic call

```python
df_to_latex(df)                          # default
df_to_latex(df, precision=3)             # more decimals
df_to_latex(df, column_format="lrrr")    # forwarded to Styler — explicit alignment
df_to_latex(df, locale="it")             # explicit; already the default
```

### Mid-cell rendering

If the DataFrame is the **last expression** of the cell, plain `df_to_latex(df)` works. If it's not, wrap in `display(...)`:

```python
display(df_to_latex(df_main))
display(Markdown("Si osserva che ..."))
```

### pint-pandas dtypes

Mix pint and bare numeric columns in one DataFrame by casting:

```python
df = (
    pd.DataFrame.from_dict(parametri_zona_vento, orient="index")
      .rename_axis("ZONA")
      .astype({v_b_0: "pint[m/s]", a_0: "pint[m]"})
      .reset_index()
      .drop("regione", axis="columns")
)
```

The columns with `pint[...]` dtypes will render with their units in the table header (under SymPy column-name handling).

### Merged zone+derived tables

When a calculation selects a zone from a lookup and then derives further quantities, **do not** show two separate tables. Filter the lookup to the selected zone, append derived columns, and put `ZONA` as the first column for context:

```python
_records = []
for _as_val in _altezze_sito:
    _as_q = u.Quantity(_as_val)
    _subs = _base | params | eqn | {a_s: _as_q}
    _rec = {"ZONA": _zona, v_b_0: _base[v_b_0], a_0: _base[a_0], k_s: _base[k_s], a_s: _as_q}
    for _var in [c_a, c_r, v_b, v_r, q_r]:
        _rec[_var] = u.Quantity(str(
            _var | pc.subs(_subs) | pc.convert_to([u.m, u.kPa]) | pc.N(4)
        ))
    _records.append(_rec)

_df_merged = pd.DataFrame(_records).astype({...}).pint.dequantify()
display(df_to_latex(_df_merged, column_format="crrrrrrrrrr"))
```

## Plots: Quarto cell options

Cell options for figures **must** live in the same cell that calls `plt.show()`:

```python
#| label: fig-coefficiente-esposizione
#| fig-cap: profilo del coefficiente di esposizione $c_e$ in funzione dell'altezza $z$

plt.plot(profilo_esposizione[c_e(z)], profilo_esposizione[z] / u.m, label="profilo del vento")
# ... more plotting ...
plt.legend()
plt.grid(linestyle="--")
plt.show()
```

### What NOT to do

```python
#| label: setup-cell    ← option in the wrong cell
fig, ax = plt.subplots()

# next cell:
ax.plot(...)
ax.legend()
plt.savefig('out.png', dpi=150)   ← Quarto handles saving; manual savefig loses the binding
plt.show()
```

Quarto produces a properly-numbered figure with a caption you can cross-reference via `@fig-...` when the label and cap are on the producing cell.

### Cross-referencing in prose

In a markdown cell elsewhere in the notebook:

```markdown
Il valore atteso è visibile in @fig-coefficiente-esposizione.
```

Same mechanism for tables: `#| label: tbl-...` and `#| tbl-cap: ...` → reference via `@tbl-...`.

## Cell-option layout rules

| Option              | Must be in cell with                          |
|---------------------|-----------------------------------------------|
| `#| label: fig-...` | the `plt.show()` call                         |
| `#| fig-cap: ...`   | the `plt.show()` call                         |
| `#| label: tbl-...` | the `df_to_latex(df)` call                    |
| `#| tbl-cap: ...`   | the `df_to_latex(df)` call                    |
| `#| tbl-colwidths:` | the `df_to_latex(df)` call                    |
| `#| echo: false`    | the cell whose code should be hidden          |
| `#| output: false`  | the cell whose output should be hidden        |

Splitting "build the DataFrame here, display it there" loses the label binding. If you need to build silently and display later, keep both in the same cell, or use a helper variable and call `df_to_latex(...)` on the trailing line of the display cell.
