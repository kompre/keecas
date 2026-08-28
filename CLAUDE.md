# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Unicode Rule (critical)

**Never use Unicode special characters in Python code, comments, or docstrings** (arrows, checkmarks, etc.) — use ASCII only (`->` not the arrow glyph, `[ok]`/`[fail]` not checkmarks). Windows' default `charmap` codec chokes on them, breaking quartodoc builds and CLI output. Unicode is fine inside LaTeX strings (e.g. `r"\sigma"`) since that's expected content, not code.

## Project Overview

`keecas` is a Python module (`src/` layout, Python >=3.12) for symbolic, units-aware engineering calculations in Jupyter notebooks rendered to Quarto documents. It combines `sympy`, `pint`, and `pipe` so equations can be written as dicts (LHS symbol -> RHS expression) and rendered as LaTeX amsmath blocks.

## Architecture

| Module | Responsibility |
|---|---|
| `display.py` | `show_eqn()` (dict -> LaTeX), `config`, `check()` verification, environment system |
| `dataframe.py` | Dict-like container with consistent row length, backs `show_eqn()` |
| `formatters.py` | Singledispatch `format_value()` — type -> LaTeX string (no decoration) |
| `col_wrappers.py` | Singledispatch `wrap_column()` — prefix/suffix decoration (`= `, `\quad`, etc.) |
| `pipe_command.py` | `pc` namespace: `subs`, `N`, `convert_to`, `doit`, `parse_expr` as `@Pipe` steps |
| `pint_sympy.py` | Pint <-> SymPy bridge, unit registry `u`, `update_pint_locale()` |
| `config.py` | Hierarchical TOML config (local > global > defaults) at `.keecas/config.toml` |
| `cli.py` | `keecas` CLI: `edit`, `config init/edit/open/show/path/reset` |
| `localization/` | 10-language support (5 full, 5 fallback), synced with Pint locale |
| `label.py`, `utils.py` | Label/cross-reference generation, shared helpers |

**Lazy imports**: `src/keecas/__init__.py` uses `__getattr__()` to lazy-load sympy/pint (fast CLI startup, ~45ms). Do not add eager imports of heavy modules at top level; verify with `python -X importtime -c "import keecas"` and `time keecas --version` (<100ms).

## Where to Look

- **Writing/editing a keecas notebook or calculation report**: use the `keecas-notebook` skill, or see `_docs/USER_USAGE_CONVENTIONS.md` for dict conventions (`_p`/`_e`/`_v`/`_d`/`_l`/`_c`, `params`/`eqn` globals), symbol naming, and cell patterns.
- **Docstrings**: `_docs/DOCSTRINGS.md` (Google-style, quartodoc, ASCII-only, `{python}` fenced examples).
- **Dev workflow, branching, CI/CD, releases**: `CONTRIBUTING.md` (branch strategy, pre-commit hooks, release-please, PyPI publishing).
- **Linting setup**: `_docs/LINTING.md`.
- **Breaking changes / upgrading**: `_docs/MIGRATION_GUIDE.md`.
- **User-facing quick start**: `README.md`.

## Commands

```bash
pytest                          # run tests
uv build                        # build package
uv sync --group dev             # install dev deps
bash scripts/install-hooks.sh   # install pre-commit hooks
keecas edit [file]               # launch Jupyter with a keecas template
keecas config init|edit|show     # manage .keecas/config.toml
```

Full CLI reference: `docs/cli-reference/`. Full contributor workflow: `CONTRIBUTING.md`.

## Notes

- Backward compatibility is not a constraint pre-1.0 — prefer clean breaks over shims.
- `dev`'s committed `pyproject.toml` version is never read or bumped manually; release-please derives versions from conventional commits on `main`.

## Keeping This File Current

This file must stay accurate and lean. When a session surfaces a new architectural decision, module, convention, or reference doc that would materially help a future session, update the relevant section here (or add a pointer under "Where to Look") before finishing. Prefer linking to a doc over inlining detail — if something belongs in `_docs/`, `CONTRIBUTING.md`, or a skill instead, put it there and reference it here.
