---
name: keecas-notebook
description: Writes and edits Jupyter notebooks that use the keecas library (sympy symbols, pint units, show_eqn, pc pipe commands) for engineering calculations. Use when the user mentions keecas, show_eqn, pc.parse_expr, pc.subs, pc.convert_to, check(), params/eqn dicts or a calculation notebook, or asks to add a parameter, formula, derivation or verification to one. For notebooks rendered by Quarto into a report, also use keecas-quarto.
---

# keecas calculation notebooks

**Quarto projects:** if the notebook belongs to a Quarto project (a `_quarto.yml` in the project, `#|` cell options, `.qmd` files, or the user mentions rendering a PDF or report), also load the `keecas-quarto` skill. It adds the Quarto layer on top of this one.

Reference files, read when the topic comes up:

- `references/show_eqn.md` - rows and columns, `float_format`/`col_wrap` sizing, environments, labels, descriptions, wide rows.
- `references/values_pipeline.md` - the `pc.subs | pc.N | pc.convert_to | pc.N` chain, extracting floats, `solve()`, trig and angles, `sympy.evaluate(False)`.
- `references/notebook_skeleton.md` - a complete minimal notebook to copy.

## Core principle

Every number shown must come from the symbolic expression shown next to it. Relationships live in `eqn` as sympy expressions; values are derived from them by the pipe pipeline; `show_eqn` renders symbol, formula, value and description together. If you find yourself doing float arithmetic and assigning results into `params`, stop: define the relationship in `_e` and derive `_v` from it.

## 1. Symbols

```python
q_s, mu_i = symbols(r"q_{s} \mu_{i}")
A_s_min = symbols(r"A_{s,min}")          # comma inside {} is auto-escaped
dc_dev = symbols(r"{\Delta c_{dev}}")    # outer braces keep a spaced name as ONE symbol
mu_1 = symbols(r"\mu_{1}", cls=sympy.Function)
```

Always an r-string, `{}` around multi-character subscripts, `\` for Greek. A space separates symbols, so `r"\Delta c_{dev}"` yields two. `symbols('alpha')` renders as the word "alpha"; `symbols('q_s')` and `symbols(r'q_{s}')` are different symbols.

## 2. Dict names

| Name | Holds |
|---|---|
| `_p` | input parameters with units; then `params.update(_p)` |
| `_e` | sympy expressions, usually via `pc.parse_expr`; then `eqn.update(_e)` |
| `_v` | values derived from `_e` through the pipeline |
| `_d` | descriptions (short text per symbol) |
| `_l` | labels: `_l = generate_unique_label(_d)` |
| `_c` | check results from `check()` |
| `params`, `eqn` | notebook-global inputs and expressions, initialised once: `params, eqn = {}, {}` |

`generate_unique_label` accepts the description dict directly, so a single `_l` dict of descriptions may serve both roles (`label=generate_unique_label(_l)`). To get labels without writing descriptions, label from the expressions: `generate_unique_label(_e)`. An empty description string yields an empty label. Labels are hashes of the description (or expression) text, so editing the text changes the label and breaks any `@eq-...` reference to it. Don't invent other names (`_descr`, `_labels`, ...).

## 3. The canonical cell

```python
A_s_min, k_c, sigma_s = symbols(r"A_{s,min} k_{c} \sigma_{s}")

_e = {
    A_s_min: "k_c * f_ct_eff * A_ct / sigma_s" | pc.parse_expr,
}
eqn.update(_e)

_d = {
    A_s_min: "min. controllo fessurazione",
}

_v = {k: v | pc.subs(eqn | params) | pc.N | pc.convert_to([u.mm]) | pc.N for k, v in _e.items()}

show_eqn(
    [_e, _v, _d],
    label=generate_unique_label(_d),
    float_format=[None, None, "{:.2f}", None],  # key column, then one entry per slot
)
```

- `show_eqn([A, B, C])` makes one row per key of the **first** slot; keys only in later slots are silently dropped. With inputs and expressions in one table, merge them into the first slot: `show_eqn([_p | _e, _v, _d], ...)`.
- `float_format` and `col_wrap` lists need **N+1** entries for N slots (index 0 is the key column). A shorter list is padded with its last entry, which silently formats the wrong columns. A single string (`"{:.2f}"`) also reformats float literals inside formulas (`0.0013` -> `0.00`), so use a list whenever a slot holds `_e`.
- Slot order matches the page: formula, value, description.
- `show_eqn` only renders as the last expression of a cell. Inside `if`/`for`, or before other statements, wrap it: `display(show_eqn(...))` (`from IPython.display import display, Markdown`).

## 4. The values pipeline

Use exactly `pc.subs(eqn | params) | pc.N | pc.convert_to([...]) | pc.N`.

The first `pc.N` is required: `pc.convert_to` on an unevaluated expression can return a wrong unit **and** a wrong magnitude when a sum stays a factor inside a product, e.g. a formula with `(4 - pi)` or a unit literal like `"h - c_nom - 5*u.mm"` (keecas#118). Evaluating first removes the problem. Add `| pc.doit` at the end if a `Piecewise` or other wrapper survives.

## 5. Units in `pc.convert_to`

Pass a list of base units and let sympy raise them to the power the dimensions require:

```python
pc.convert_to([u.mm])        # length -> mm, area -> mm**2, inertia -> mm**4
pc.convert_to([u.kN, u.m])   # force -> kN, moment -> kN*m, line load -> kN/m
pc.convert_to([u.MPa])       # stress -> MPa
```

Don't write `[u.mm**2]` or `[u.kN * u.m]`. They work, but writing the power by hand is exactly the bookkeeping keecas exists to remove: asking for `u.mm**3` when the result is an area is a mistake the base-unit form cannot make. For per-symbol targets use a `_target_unit = {sym: [u.mm], ...}` dict of **lists** and `pc.convert_to(_target_unit[k])`.

## 6. Angles and trig

Trig functions take and return dimensionless numbers, implicitly radians; an argument still carrying `deg` or `rad` is not evaluated (`sin(30*degree)`). Convert angle inputs with `pc.convert_to([1])`, which turns a dimensionless quantity into a plain number, never `[u.rad]`; never multiply a trig result by `u.rad`. To display an angle in degrees: `(v * u.rad) | pc.convert_to([u.deg]) | pc.N`. Details in `references/values_pipeline.md`.

## 7. Descriptions

Description strings are placed inside LaTeX `\text{...}` raw and unescaped (default `config.display.treat_str_as_markdown = False`):

- **Short**: a phrase, abbreviations welcome (`"min. fless. inf."`, `"resist. car. cls"`). Long text widens the row.
- **No data that lives elsewhere**: never put values, sizes or class names that are parameters (`"striscia di 1 m"`, `"C25/30"`, `"phi 10/150"`). They go stale when the parameter changes; show them as `_p` rows instead.
- **LaTeX-safe**: no `$...$`, no raw symbol notation (`x_1`), no `_ ^ % & #`. An unescaped `_` is a LaTeX error; `%` silently truncates the line. Write `"barra x1"`, not `"barra x_1"`. Use a hyphen, not an em dash.
- If a notebook really needs emphasis or footnotes, set `config.display.treat_str_as_markdown = True` once: `**bold**`, `*italic*`, `` `code` `` and `^[footnote]` are converted and everything else is escaped. It still does not make `x_1` a subscript.

## 8. Keeping rows narrow

A row is `symbol = formula = value  description`. When it gets too wide:

1. For `_e` blocks, drop the description slot (`show_eqn([_e, _v], label=generate_unique_label(_d))`) and describe the step in the markdown cell above. Parameter blocks (`show_eqn([_p, _d], ...)`) are narrow and keep the column.
2. Split a long formula into intermediate symbols, each its own `_e` entry and row. This also keeps every partial result traceable.
3. Rendering-specific remedies (shrinking, one term per bullet) are in `keecas-quarto`.

## 9. Expression strings

- Use `^` for powers, so the source reads like the rendered LaTeX.
- Write `Max`, `Min`, `Piecewise` inside the string, not as `sympy.Max(...)`: `"Max(0.26*f_ctm/f_yk*b*d, 0.0013*b*d)" | pc.parse_expr`.
- Units may appear in strings: `"Min(3*h, 400*u.mm)"`.
- Decimal literals already parse as floats; no `N(...)` wrapper is needed.

## 10. No parallel numerics, no `print()`

- Never strip units, compute with numpy/floats and write the result back into `params`. Numpy is fine for plotting or sweeps; any number reported must be re-derived through the pipeline.
- To branch on a value, extract it after the pipeline: `float((d | pc.subs(eqn | params) | pc.N | pc.convert_to([u.m]) | pc.N).args[0])`.
- No `print()`: use `show_eqn({sym: value})`, `display(Markdown(...))`, or a markdown cell.

## 11. Verifications

`check()` defaults to `<=`, so pass **demand / capacity** against 1. Convert the ratio with `[1]`: with mixed units (`kN` over `N`) it otherwise stays `0.000667 kN/N` and `check` raises an error. `[1]` reduces only dimensionless quantities, so a demand/capacity pair with mismatched dimensions keeps its units and still fails loudly.

```python
_v = {k: k | pc.subs(eqn | params) | pc.N | pc.convert_to([1]) | pc.N for k in [N_Ed / N_Rd]}
_c = {k: check(v, 1) for k, v in _v.items()}
show_eqn([_v, _c], float_format="{:.3f}")
```

## 12. Style

No whitespace padding to align dict values or `=` signs; ruff collapses it and it makes diffs noisy.

## Self-check before declaring done

1. Symbols: r-strings, `{}` subscripts, `\` Greek?
2. Every displayed value comes from `pc.subs | pc.N | pc.convert_to | pc.N`; nothing computed with floats is written into `params`?
3. `pc.convert_to` targets are base-unit lists (`[u.mm]`, `[u.kN, u.m]`)?
4. First `show_eqn` slot contains every key that needs a row (`_p | _e`); `float_format`/`col_wrap` are N+1-entry lists whenever a slot holds formulas?
5. `_d` descriptions, `_l` labels; descriptions short, LaTeX-safe, free of parameter values?
6. Wide `_e` blocks render without the description slot?
7. Expression strings use `^`; `Max`/`Min`/`Piecewise` written as strings?
8. Verifications are `check(demand / capacity, 1)` with the ratio converted via `[1]`?
9. Trig: no `* u.rad` on results, angles via `pc.convert_to([1])`?
10. No `print()`, no aligned padding, `display(...)` around non-final `show_eqn`?
