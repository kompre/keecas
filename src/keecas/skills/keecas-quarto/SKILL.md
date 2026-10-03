---
name: keecas-quarto
description: Writes and edits keecas calculation notebooks (usually `__*.ipynb`) that Quarto renders into a PDF calculation report (relazione di calcolo). Use when a keecas notebook lives in a Quarto project (`_quarto.yml`), or the user mentions Quarto, `.qmd`, rendering, the PDF, cell options (`#| label`, `fig-cap`, `tbl-cap`, `output`, `eval`), cross-references, `df_to_latex` tables, `%run` of a shared notebook, rows too wide for the page, or a new report section (azione, verifica). Builds on keecas-notebook.
---

# keecas notebooks in Quarto projects

**Load `keecas-notebook` first.** This skill only adds the Quarto layer: notebook structure, cell options, page layout, tables and figures. Symbols, dicts, the values pipeline, `show_eqn` and descriptions are defined there.

Reference files, read when the topic comes up:

- `references/notebook_skeleton.md` - a complete Quarto notebook to copy: `%run`, init cells, KaTeX include, calculation cells.
- `references/tables_and_plots.md` - `df_to_latex`, pint-pandas columns, merged tables, figure and table cell options, cross-references.

## Pre-flight: read an existing notebook as `.qmd`

Before writing a new notebook, read one existing notebook of the same project as its generated `.qmd`, not the `.ipynb` (the `.qmd` has no cell outputs to bloat the context). Pick one close to the task, e.g. in the report template `relazione/Verifiche/_<name>.qmd` or `relazione/Azioni/_<name>.qmd`.

The `_<name>.qmd` files are generated from `__<name>.ipynb` by the project's prerender step (`qbc`, run by `quarto render` or directly via `_scripts/pre_render.py` where the project has it). If the `.qmd` is missing or older than the notebook, run the prerender, or read the `.ipynb` and accept the output noise.

## 1. Cell order

1. **Optional `%run` of a shared base notebook**, always the very first cell (section 2).
2. **Imports and `PATH_PREFIX`**:

   ```python
   #| tags: [inizializzazione]
   #| label: INIZIO CALCOLO <SECTION_NAME>

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

   `PATH_PREFIX` is set by the parent document when the notebook is rendered as part of the report, and defaults to `./` when the notebook runs on its own. Build every file path from it.

3. **keecas config and the section's result dict**:

   ```python
   config.latex.eq_prefix = "eq-<SECTION>-"
   config.display.print_label = True
   config.display.katex = True

   <SECTION> = {
       "parametri": (params := {}),
       "espressioni": (eqn := {}),
       "valori": (vals := {}),  # only if later notebooks consume computed values
       "verifiche": (verifiche := {}),  # only in verification notebooks
   }
   ```

4. **KaTeX include**, a raw Quarto line (not a code cell): `{{< include /_scripts/_KaTeX_compatibility.qmd >}}`

## 2. `%run` of a shared base notebook

```python
#| output: false
#| eval: false
%run ../../shared/__materiali.ipynb
```

- **First cell, before the init cells.** Run later, the base notebook's own `symbols(...)` and `config.*` lines overwrite this notebook's symbols and settings (e.g. `eq_prefix` reverting to the base notebook's prefix, so every later label is wrong). Run first, this notebook's init cells have the last word.
- **`#| eval: false`**: Quarto renders the project in one Jupyter session, where the base notebook has already run. The cell exists only to run the notebook on its own during development.
- **`#| output: false`**: nothing from it reaches the PDF.

## 3. Cell options

| Option | Effect |
|---|---|
| `#\| output: false` | cell runs, output hidden |
| `#\| echo: false` | cell runs, output shown, code hidden (already the project default) |
| `#\| eval: false` | cell does not run at render time |
| `#\| label: fig-...` + `#\| fig-cap: ...` | numbered figure, cite as `@fig-...` |
| `#\| label: tbl-...` + `#\| tbl-cap: ...` | numbered table, cite as `@tbl-...` |

Labels and captions must be in the cell that **produces** the figure or table, not in a setup cell. To silence a value-only cell use `output: false`, never `eval: false` (that skips the computation too).

## 4. Fitting rows to the page width

Apply in this order (the first three are in `keecas-notebook`):

1. Short descriptions, abbreviations welcome, no parameter values in them.
2. Expression blocks without the description slot; context in the markdown cell above.
3. Long formulas split into intermediate symbols.
4. **One term per bullet** when each term needs a sentence of explanation (`.qmd`-style inline cells inside a list):

   ````markdown
   - Minimo per controllo fessurazione:
     ```{python}
     show_eqn({A_s_min: _v[A_s_min]}, label=_l[A_s_min])
     ```
   - Minimo geometrico:
     ```{python}
     show_eqn({A_s_geom: _v[A_s_geom]}, label=_l[A_s_geom])
     ```
   ````

5. **Shrink the block** as a last resort (PDF only, no effect on HTML):

   ````markdown
   ```{=latex}
   {\scriptsize
   ```

   ```{python}
   show_eqn([_e, _v], label=generate_unique_label(_d), float_format=[None, None, "{:.2f}"])
   ```

   ```{=latex}
   }
   ```
   ````

   The first raw block opens a group and leaves the brace open; the second closes it. It shrinks everything in the block, numbers included.

## 5. Markdown cells

- Prose only. Never restate as `$$...$$` a formula that the next code cell renders from `_e`; the copies drift. Inline `$...$` symbol references are fine.
- One paragraph per line; don't hard-wrap at 80 columns.
- Cite equations, figures and tables with `@eq-...`, `@fig-...`, `@tbl-...` (with `config.display.print_label = True`, `show_eqn` prints each equation label to stdout).

## 6. Tables

Use `df_to_latex(df)` for every table, never `df.to_markdown()` or `print(df)`. It is a project helper (`_scripts/table_utils.py`) until it moves into keecas (keecas#120); see `references/tables_and_plots.md` for the import, options and pint-pandas columns. Wrap it in `display(...)` when it is not the last expression of the cell.

## 7. Figures

Plot with matplotlib and end with `plt.show()` in a cell carrying `#| label: fig-...` and `#| fig-cap: ...`. Never `plt.savefig(...)`: Quarto saves the figure and binds the caption and label itself.

## 8. Metadata that may be a list

Fields in `_metadata.yml` (e.g. `altezza_sito`) can be a scalar or a list. Normalise, compute for every value, and pick the governing one explicitly:

```python
_raw = metadata["commessa"]["altezza_sito"]
_altezze_sito = _raw if isinstance(_raw, list) else [_raw]
_as_max = max(_altezze_sito, key=lambda v: u.Quantity(v).to_base_units().magnitude)
```

Then show one table row per value, or state in a markdown line which value governs.

## 9. Naming

- Notebooks are `__<name>.ipynb`; the prerender creates `_<name>.qmd`.
- In `relazione/Azioni/` the folder already says "azione": `__vento.ipynb`, not `__azione_vento.ipynb`.
- `<SECTION>` and `eq-<SECTION>-` use the section name in SCREAMING_SNAKE_CASE.

## Self-check (in addition to the keecas-notebook one)

1. Any `%run` cell is the first cell, with `#| output: false` and `#| eval: false`?
2. Init cells in order: imports + `PATH_PREFIX`, config + section dict, KaTeX include?
3. File paths built from `PATH_PREFIX`?
4. Rows fit the page (section 4)?
5. Markdown cells don't duplicate formulas as `$$...$$`?
6. Figures use `#| label: fig-...` + `#| fig-cap:` in the producing cell, no `savefig`?
7. Tables use `df_to_latex`, wrapped in `display(...)` mid-cell, with `tbl-` options in the producing cell?
8. List-valued metadata normalised, governing value chosen with a `key=` lambda?
