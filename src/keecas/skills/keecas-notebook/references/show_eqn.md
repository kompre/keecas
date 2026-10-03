# `show_eqn` - mechanics and patterns

## Contents

- First slot drives the rows
- Slot order
- `float_format`
- `col_wrap`
- `environment`
- Mid-cell rendering
- Labels: `label` and `generate_unique_label`
- Descriptions: content rules and Markdown mode
- Keeping rows narrow
- Common slot patterns

`show_eqn` is the single rendering primitive for symbol / formula / value / description tables. Its sharp edges fail silently, so know them.

## First slot drives the rows

`show_eqn([A, B, C, ...])` renders one row per key of the **first** element. Later elements add columns, and only show a value on rows whose key is in `A`.

```python
_p = {f_ck: 25 * u.MPa, f_yk: 450 * u.MPa}
_e = {f_ctm: "0.30 * (f_ck/u.MPa)^(2/3) * u.MPa" | pc.parse_expr}

# WRONG - only f_ck and f_yk appear; f_ctm is silently dropped
show_eqn([_p, _e, _v])

# RIGHT - merge into the first slot so every key gets a row
show_eqn([_p | _e, _v, _d])
```

A single dict (not a list) renders every key: `show_eqn(_e)`, `show_eqn(_p)`.

## Slot order

| Position | Content | Notes |
|---|---|---|
| 1 | `_p`, `_e` or `_p \| _e` | drives the rows |
| 2 | `_v` | values; pair with `"{:.2f}"` in `float_format` |
| 3 | `_d` | descriptions; drop for wide `_e` blocks |
| (last) | `_c` | `check()` results, in verification tables |

## `float_format`

A single format string applies to every column, **including float literals inside formulas**: with `"{:.2f}"`, a formula term `0.0013*b*d` renders as `0.00 b d`. Whenever a slot holds formulas (`_e`), use a list with one entry per column and `None` to skip:

```python
show_eqn(
    [_p | _e, _v, _d],
    label=generate_unique_label(_d),
    float_format=[None, None, "{:.2f}", None],  # key, first slot, _v, _d
)
```

The list needs **N+1** entries for N slots: index 0 is the key (LHS) column, then one per slot in order. A shorter list is not an error: its last entry is repeated to fill the remaining columns, so an undersized list silently formats the wrong column. Always size it explicitly.

A percent spec is safe: `show_eqn({x: 0.1234}, float_format=".2%")` renders `12.34\%` (the generated `%` is escaped). A raw `%` typed into a description is not escaped and still breaks the render.

## `col_wrap`

Controls the separators around each column. The default (`wrap_column`) already picks `"= "` for numbers, sympy and pint values and `\quad` for strings, so pass `col_wrap` only for a real deviation. It has the same N+1 sizing rule as `float_format`.

```python
show_eqn([_p, _d], col_wrap=[None, "=", "&"])                    # one-column parameter table
show_eqn(_d, col_wrap=[None, r"\qquad"], environment="align*")   # symbol glossary
```

## `environment`

Built-in environments: `"align"` (default), `"equation"`, `"cases"`, `"gather"`, `"split"`, `"alignat"`, `"rcases"`; a trailing `*` removes numbering. Useful cases:

- `"cases"` - a system of equations, e.g. the result of `solve()`.
- `"align*"` - a "where:" glossary of symbol and description, no formula.

```python
display(show_eqn([_e, _v], float_format=[None, None, "{:.2f}"]))
display(Markdown("where:"))
show_eqn(_d, col_wrap=[None, r"\qquad"], environment="align*")
```

## Mid-cell rendering

`show_eqn` returns a display object; Jupyter renders it only when it is the last expression of the cell. Inside `if`/`for`, or when other statements follow, wrap it:

```python
if k_e_val <= 1.0:
    display(show_eqn(_v1))
else:
    display(show_eqn(_v2))
```

## Labels: `label` and `generate_unique_label`

```python
show_eqn([_e, _v, _d], label=generate_unique_label(_d), float_format=[None, None, "{:.2f}", None])
```

- `generate_unique_label(dict)` returns `{key: "eq-<hash>"}`, with the prefix from `config.latex.eq_prefix`. It is exported by `from keecas import *`.
- The hash comes from the dict's text. Editing a description (or expression) changes the label and breaks `@eq-...` references to it.
- An empty string value yields an empty label. To label rows that have no description, use `generate_unique_label(_e)`.
- `config.display.print_label = True` makes `show_eqn` print each row's `symbol: eq-...` label to stdout, ready to copy into a cross-reference. `config.display.katex = True` omits the `\label{...}` commands from the LaTeX itself.
- `label="my-block"` applies one string label to the block.
- Pass `label=` even when the description slot is not rendered.

## Descriptions: content rules and Markdown mode

With the default `config.display.treat_str_as_markdown = False`, each description is spliced raw into `\text{...}`:

1. **Short phrases**, abbreviations welcome. A long description widens the row.
2. **No values that are parameters elsewhere** (sizes, classes, spacings). They go stale; make them `_p` rows.
3. **No inline math**: `$f_{yk}$` inside `\text{}` does not render reliably. Spell symbols in words.
4. **No unescaped `_ ^ % & #`**: `_` is a LaTeX compile error outside math, `%` silently truncates the rest of the line. `"barra x1"`, not `"barra x_1"`.
5. **No em dashes**; use a hyphen.

Setting `config.display.treat_str_as_markdown = True` once (it is a global setting, not a `show_eqn` argument) parses every plain string through a small Markdown subset before escaping:

| Markdown | LaTeX |
|---|---|
| `**bold**` | `\textbf{...}` |
| `*italic*` | `\textit{...}` |
| `` `code` `` | `\texttt{...}` |
| `^[footnote]` | `\footnote{...}` |
| anything else | escaped text (`_ % & # $ ~ ^ \` no longer break) |

It does not produce subscripts (`x_1` stays literal text), and only `*`/`**` emphasis is recognised (not `_italic_`). `Markdown(...)` values always get this treatment.

## Keeping rows narrow

- **Parameter blocks** (`symbol = value`) are narrow: keep the description slot, `show_eqn([_p, _d], ...)`.
- **Expression blocks** (`symbol = formula = value`) are wide: drop the description slot and describe the step in the markdown cell above; still pass `label=generate_unique_label(_d)`.
- **A formula that is itself too wide**: split it into intermediate symbols, each an `_e` entry and a row of its own.
- Rendering-specific remedies for PDF output (one term per bullet, `\scriptsize`) are in the `keecas-quarto` skill.

## Common slot patterns

```python
# Formulas only
show_eqn(_e, label=generate_unique_label(_e))

# Parameters with descriptions
show_eqn([_p, _d], label=generate_unique_label(_d))

# Parameters + expressions + values + descriptions (narrow formulas)
show_eqn([_p | _e, _v, _d], label=generate_unique_label(_d), float_format=[None, None, "{:.2f}", None])

# Wide expressions: no description slot
show_eqn([_e, _v], label=generate_unique_label(_d), float_format=[None, None, "{:.2f}"])

# Verification
show_eqn([_v, _c], float_format="{:.3f}")

# Glossary
show_eqn(_d, col_wrap=[None, r"\qquad"], environment="align*")
```
