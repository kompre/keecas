# `show_eqn` — mechanics and patterns

`show_eqn` is the single rendering primitive for symbol-value-description tables. Its API has a few sharp edges that produce silent failures if you don't know them.

## First-slot drives the rows

When called with a list, `show_eqn([A, B, C, ...], ...)` uses the **keys of the first element** to decide which rows to render. Subsequent elements contribute columns, but each column only shows a value on rows whose key exists in `A`.

```python
_p = {f_ck: 25*u.MPa, f_yk: 450*u.MPa}
_e = {f_ctm: "N(0.30)*(f_ck/u.MPa)^(2/3)*u.MPa" | pc.parse_expr,
      f_ct_eff: f_ctm}

# WRONG — only f_ck and f_yk appear; f_ctm and f_ct_eff are silently dropped
show_eqn([_p, _e, _v], ...)

# RIGHT — merge into the first slot so every key produces a row
show_eqn([_p | _e, _v, _l], ...)
```

When called with a single dict (not a list), every key of that dict becomes a row. The single-dict form is fine when there's nothing to add — `show_eqn(_e)` or `show_eqn(_p)`.

## Slot order convention

For new code, use this slot order:

| Position | Content                                | Notes                                                  |
|----------|----------------------------------------|--------------------------------------------------------|
| 1        | `_p` or `_e` or `_p | _e`              | drives the rows; merge with `|` to include all keys    |
| 2        | `_v`                                   | numeric values; pair with `'{:.2f}'` in `float_format` |
| 3        | `_l`                                   | descriptions                                           |

`label=generate_unique_label(_l)` should still be passed even when `_l` is not rendered as a column — the labels produce LaTeX cross-reference anchors regardless.

## `float_format`

Accepts a single format string (applied to every numeric column) or a list with one entry per column. Use `None` to skip a column:

```python
show_eqn(
    [_p | _e, _v, _l],
    label=generate_unique_label(_l),
    float_format=[None, None, "{:.2f}"],   # skip symbol col, skip formula col, format value col
)
```

The number of `float_format` entries should match the number of slots in the list.

**Do not use a percent spec (`".2%"`) yet.** It's a known bug (keecas#105): the formatted number's literal `%` is spliced unescaped into the LaTeX string, and `%` is LaTeX's comment marker — everything after it on that line silently vanishes from the rendered output, with no error. The same bug applies to a raw, unescaped `%` typed directly into a `_l` description string. For a percentage-like result, format the number as a plain decimal (`".3f"` after multiplying by 100 yourself) and, if you need the `%` sign at all, write it pre-escaped as `\%` in the description or surrounding markdown (`"utilizzo 12.3\\%"`), never as a bare `%`.

## `col_wrap`

Controls the separators between rendered columns. Common forms:

```python
show_eqn([_p, _l], col_wrap=[None, "=", "&"])    # used in older notebooks for param tables
show_eqn(_d, col_wrap=[None, r"\qquad"], environment="align*")  # description-only blocks
```

For a typical formula/value table you usually don't need `col_wrap` — the default is fine.

## `environment`

Switches the underlying LaTeX environment. Useful values:

- `"cases"` / `"cases*"` — for systems of equations or piecewise outputs
- `"align*"` — for symbol-description blocks where each row is `symbol \qquad description`

Example for a description-only "where:" block under a formula:

```python
display(show_eqn([_e, _v], float_format="{:.2f}"))
display(Markdown("Dove:"))
show_eqn(_d, col_wrap=[None, r"\qquad"], environment="align*")
```

## Mid-cell rendering

`show_eqn` only auto-displays when it is the last expression of a cell. Inside conditionals, loops, or before another expression, wrap it:

```python
# WRONG — neither branch renders because show_eqn isn't the cell's last expression
if k_e_val <= 1.0:
    show_eqn(...)
else:
    show_eqn(...)
other_thing()

# RIGHT
if k_e_val <= 1.0:
    display(show_eqn(...))
else:
    display(show_eqn(...))
other_thing()
```

Same applies inside `for` loops, after an `if` block, or any time `show_eqn` is not the trailing expression.

## `_l` content and placement — column vs. label-only

`_l` values are rendered inside LaTeX `\text{...}` when used as a `show_eqn` column. This has four consequences:

1. **No inline math.** `$f_{yk}$` inside `\text{...}` renders as the literal characters `$f_{yk}$` in most contexts, not as math. Keep `_l` entries to plain prose, LaTeX-safe.
2. **Unescaped LaTeX-special characters break the render, not just the look.** `_`, `^`, `%`, `&`, `#` are reserved outside math mode. A description like `"la banana x_1"` throws a LaTeX compile error at render time (`_` is read as a subscript operator with no math mode to apply it in) — it does not just print literally. `%` is LaTeX's comment marker and silently truncates the rest of the line instead of erroring. Never write raw symbol notation in a description; spell it out in words instead (`"minimo per la barra x1"`, not `"minimo per x_1"`).
3. **Avoid em dashes (`—`).** Use a plain hyphen (`-`) or restructure the sentence instead.
4. **Short phrases only.** Long descriptions force the table column to widen, which can push the formula column past the textwidth in expression blocks where the formulas are already wide.

The convention for placement:

- **Parameters (`_p`)** — narrow rows (`symbol = value`), so `_l` as a column fits comfortably. Slot it in: `show_eqn([_p, _l], ...)`.
- **Expressions (`_e` → `_v`)** — wide rows (`symbol = formula = value`). Drop `_l` from the slot list to avoid overflow and put the description in the markdown cell *above* the code cell instead. Still pass `_l` to `label=generate_unique_label(_l)` so the row anchors are generated.

```python
# Parameters — _l column is fine
show_eqn([_p, _l], label=generate_unique_label(_l))

# Expression — describe in markdown above; _l only for label anchors
show_eqn(
    [_e, _v],
    label=generate_unique_label(_l),
    float_format="{:.2f}",
)
```

The pre-cell markdown gets a brief paragraph or definition list — exactly what would have been crammed into the column. Markdown has full LaTeX support, so inline `$...$` works, and the page width is not the formula's problem.

### Alternative: one term per bullet

When several terms each need a real sentence of description (too long for the markdown-above paragraph to stay legible as one blob), skip the `_l` column and interleave a markdown bullet list with one `show_eqn` call per term:

````markdown
- Minimo per controllo fessurazione:
  ```{python}
  show_eqn({A_s_min: _v[A_s_min]}, label=f"eq-{A_s_min}")
  ```
- Minimo geometrico di normativa:
  ```{python}
  show_eqn({A_s_geom: _v[A_s_geom]}, label=f"eq-{A_s_geom}")
  ```
````

This is a different tool from the "where:" `align*` block above — that one is for a compact symbol-glossary (short phrase per symbol, no formula). This one is for when each term's formula is shown individually and the description genuinely needs a sentence, not a phrase.

### Alternative: `\scriptsize`-wrap a formula that's too wide

If the *formula itself* (not just the description) doesn't fit the page width, shrink the whole rendered block by wrapping the code cell in raw LaTeX (PDF/Quarto `{=latex}` output only — no effect on HTML):

````markdown
```{=latex}
{\scriptsize
```

```{python}
show_eqn([_e, _v], label=generate_unique_label(_l))
```

```{=latex}
}
```
````

The first raw block opens a LaTeX group with `\scriptsize` active and deliberately does not close the brace; the second raw block closes it. Reach for this only when shortening the description or dropping `_l` from the slot list still isn't enough — it shrinks the entire block (numbers and symbols included), not just the description column.

## `label` and `generate_unique_label`

```python
from keecas.label import generate_unique_label

show_eqn(
    [_e, _v, _l],
    label=generate_unique_label(_l),
    float_format=[None, None, "{:.2f}"],
)
```

`generate_unique_label(_l)` derives a LaTeX-safe anchor for each row from the description dict's keys. Pass `_l` even when not displaying it as a column — the anchor is what lets later prose reference the formula by number.

If you have no description dict and just want anchors, you can also write `label="my-block-label"` (a single string applied to the block).

## Common slot patterns

For quick reference:

```python
# Just show formulas
show_eqn(_e, label=generate_unique_label(_l))

# Parameters in a one-column table
show_eqn([_p, _l], col_wrap=[None, "=", "&"])

# Parameters + expressions + values + descriptions
show_eqn([_p | _e, _v, _l], label=generate_unique_label(_l),
         float_format=[None, None, "{:.2f}"])

# Only values (e.g. after solving symbolically)
show_eqn([_e, _v], float_format="{:.2f}")

# Where-block (description only)
show_eqn(_d, col_wrap=[None, r"\qquad"], environment="align*")
```
