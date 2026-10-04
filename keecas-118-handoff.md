# keecas#118 impact check - brief for a local Claude Code session

## Task

Check whether the keecas calculation project at the path the user gives you produced wrong values because of keecas issue #118, and report which results are affected. Do not edit the project unless the user asks.

## The bug

- In keecas <= 1.5.0, `pc.convert_to` is sympy's `convert_to`. If a sum carrying units is still a factor of a product after `pc.subs`, sympy leaves that sum's units inside the numeric factor. They are then counted twice.
- Typical sources: `(4 - pi)*b**2*gamma`, `b*(h - c - 5*u.mm)` with a unit literal in the formula, an unevaluated `(4 - 3)` from `pc.parse_expr`, or such a sum in a denominator (`5*q*L**4/(384*E*I)` with `I` holding `pi`).
- Symptom: wrong unit (`kN*m` instead of `kN/m`); depending on the target unit, the magnitude can be wrong too (`210000000 mm**3` instead of `210000 mm**2`). A later `pc.N` does not fix it.
- Not affected: pipelines with `pc.N` before `pc.convert_to` (`pc.subs | pc.N | pc.convert_to | pc.N`, the workaround the keecas-notebook skill prescribed); sums whose terms merge after substitution (`a*b - b**2/10` with lengths only).
- Downstream risk: an affected value displayed by `show_eqn`, passed to `check()` (may raise `TypeError` or compare the wrong numbers), reused in later formulas, or extracted as a float (`.args[0]`).

The fix (keecas branch `claude/pc-n-convert-to-order-l82jq1`) converts such sums as a whole, so `pc.N` is no longer needed before `pc.convert_to`.

## How to check

1. Save the script below as `keecas_118_check.py` outside the project (e.g. the keecas repo root; do not commit it).
2. Find the project's Python environment (the one with keecas, sympy, pint and jupyter; `nbclient` and `nbformat` come with jupyter) and the notebooks to run. Run the top-level notebooks; notebooks they pull in with `%run` are covered.
3. Run:

   ```
   <project python> keecas_118_check.py <nb1.ipynb> [<nb2.ipynb> ...] --log keecas_118_findings.jsonl
   ```

   The script runs each notebook unchanged in a fresh kernel, in the notebook's folder. Every `pc.convert_to` call still returns the old (<= 1.5.0) result, so the notebook behaves as it did; each call is also computed with the fixed algorithm, and calls where value or unit differ are logged and summarised. Files are not modified. It works whatever keecas version the project has installed.
   - `.qmd` sources: convert to `.ipynb` in a temp folder (`quarto convert file.qmd --output <tmp>/file.ipynb`) and pass `--cwd <folder of the .qmd>`.
   - Only `pc.convert_to` reached as an attribute (`pc.convert_to`) is checked; a direct `from keecas.pipe_command import convert_to` is not.
   - Notebooks whose cells raise errors are reported; results after the first error may be incomplete.
4. Read the findings. Each gives the notebook, the source line, the target units, `old` (what the report showed) and `fixed` (the correct value). `old/fixed` with units (e.g. `meter**2`) means a wrong unit; a number other than 1 means a wrong magnitude.
5. For each affected line, trace which displayed values, `check()` verifications and later computations used it, and whether a verification outcome would change. If the notebooks hold saved outputs or a rendered PDF exists, confirm the wrong value appears there.

## Report back

- Table: notebook, symbol, value shown, correct value.
- Verifications whose outcome changes (pass -> fail or fail -> pass).
- Notebooks not checked or that errored, and why.
- Fix options for the user to choose: upgrade keecas once the fix is released, or add `| pc.N` before `pc.convert_to` on the affected lines (this evaluates `pi` early).

## If notebooks cannot be executed

Fallback, less reliable: grep for `pc.convert_to(` lines with no `pc.N |` before them, then inspect the formulas feeding them for sums that contain `pi`, `sqrt`, a unit literal (`5*u.mm`) or an unevaluated numeric sum.

## Script: `keecas_118_check.py`

```python
"""Find pc.convert_to calls affected by keecas#118 in existing notebooks.

Runs each notebook unchanged in a fresh kernel in which `pc.convert_to` is
wrapped: every call still returns the result of the installed keecas, and is
also computed with the fixed algorithm (keecas branch
claude/pc-n-convert-to-order-l82jq1). Calls where the two differ in value or
unit are reported. Notebook files are not modified.

Usage (with the Python environment the project's notebooks use):
    python keecas_118_check.py nb1.ipynb [nb2.ipynb ...] [--log findings.jsonl] [--cwd DIR]

The kernel runs in each notebook's own folder, as in Jupyter, unless --cwd is
given (e.g. for a .qmd converted to a temporary .ipynb elsewhere).
"""

import argparse
import inspect
import json
import os
import tempfile
from collections.abc import Iterable
from functools import reduce
from pathlib import Path

LOG_ENV = "KEECAS_118_LOG"
NOTEBOOK_ENV = "KEECAS_118_NOTEBOOK"


# --- fixed algorithm, copied from the keecas fix (pipe_command._convert_to) ---


def _fixed_convert_to(expr, target_units, unit_system="SI"):
    from sympy import Add, Function, Mul, Pow, Tuple, sympify
    from sympy.physics.units import Quantity, UnitSystem
    from sympy.physics.units.dimensions import Dimension
    from sympy.physics.units.util import _get_conversion_matrix_for_expr

    def is_homogeneous(e, us):
        ds = us.get_dimension_system()
        try:
            first, *rest = (
                ds.get_dimensional_dependencies(
                    Dimension(us.get_dimensional_expr(t)), mark_dimensionless=True
                )
                for t in e.args
            )
        except (TypeError, ValueError):
            return False
        return all(d == first for d in rest)

    def scale_factor(e, us):
        if isinstance(e, Quantity):
            return us.get_quantity_scale_factor(e)
        if isinstance(e, Mul):
            return reduce(lambda x, y: x * y, (scale_factor(a, us) for a in e.args))
        if isinstance(e, Pow):
            return scale_factor(e.base, us) ** e.exp
        if isinstance(e, Add) and is_homogeneous(e, us):
            return Add(*(scale_factor(a, us) for a in e.args))
        return e

    def convert(e, tu, us):
        if isinstance(e, Add) and not is_homogeneous(e, us):
            return Add.fromiter(convert(a, tu, us) for a in e.args)
        if isinstance(e, Pow) and isinstance(e.base, Add) and not is_homogeneous(e.base, us):
            return convert(e.base, tu, us) ** e.exp
        if isinstance(e, Function):
            e = e.together()
        if not isinstance(e, Quantity) and e.has(Quantity):
            e = e.replace(lambda x: isinstance(x, Quantity), lambda x: x.convert_to(tu, us))
        depmat = _get_conversion_matrix_for_expr(e, tu, us)
        if depmat is None:
            return e
        coeff, units = Mul.fromiter(
            (1 / scale_factor(u, us) * u) ** p for u, p in zip(tu, depmat)
        ).as_coeff_Mul()
        return (scale_factor(e, us) * coeff) * units

    unit_system = UnitSystem.get_unit_system(unit_system)
    if not isinstance(target_units, Iterable | Tuple):
        target_units = [target_units]
    return convert(sympify(expr), sympify(target_units), unit_system)


# --- comparison and logging ---


def _difference(old, new):
    """Return why old and new differ, or None when they are the same value and unit."""
    import sympy as sp

    if old == new:
        return None
    try:
        a, b = sp.N(old), sp.N(new)
        if a == b:
            return None
        if b == 0:
            return None if a == 0 else "fixed result is 0"
        ratio = sp.simplify(a / b)
        if ratio.is_number and abs(complex(ratio) - 1) < 1e-9:
            return None
        return f"old/fixed = {ratio}"
    except Exception as exc:  # e.g. matrices: report for a manual look
        return f"could not compare: {exc!r}"


def _caller():
    """First frame outside sympy, pipe, keecas and this file: the notebook line."""
    import pipe
    import sympy

    import keecas

    skip = (
        str(Path(sympy.__file__).parent),
        str(Path(pipe.__file__)),
        str(Path(keecas.__file__).parent),
        str(Path(__file__).resolve()),
    )
    for frame in inspect.stack()[2:]:
        if not frame.filename.startswith(skip):
            line = (frame.code_context or [""])[0].strip()
            return {"file": frame.filename, "line": frame.lineno, "code": line}
    return {}


def _install():
    """Wrap pc.convert_to in this kernel."""
    from pipe import Pipe
    from sympy.physics.units.util import convert_to as sympy_convert_to

    import keecas.pipe_command as pcm

    @Pipe
    def convert_to(expression, units=1):
        old = sympy_convert_to(expression, target_units=units)  # keecas <= 1.5.0
        try:
            new = _fixed_convert_to(expression, units)
            reason = _difference(old, new)
        except Exception as exc:
            new, reason = None, f"fixed algorithm failed: {exc!r}"
        if reason:
            import sympy as sp

            record = {
                "notebook": os.environ.get(NOTEBOOK_ENV, ""),
                **_caller(),
                "input": str(expression)[:500],
                "target": str(units),
                "old": str(sp.N(old))[:300],
                "fixed": str(sp.N(new))[:300] if new is not None else None,
                "reason": reason,
            }
            with open(os.environ[LOG_ENV], "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        return old

    pcm.convert_to = convert_to


# --- runner ---


def _run(notebooks, log_path, cwd=None):
    import nbformat
    from nbclient import NotebookClient

    ipython_dir = Path(tempfile.mkdtemp(prefix="keecas118_ipython_"))
    startup = ipython_dir / "profile_default" / "startup"
    startup.mkdir(parents=True)
    (startup / "00-keecas-118.py").write_text(
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('keecas_118_check', {str(Path(__file__).resolve())!r})\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "sys.modules['keecas_118_check'] = mod\n"
        "spec.loader.exec_module(mod)\n"
        "mod._install()\n",
        encoding="utf-8",
    )
    os.environ["IPYTHONDIR"] = str(ipython_dir)
    os.environ[LOG_ENV] = str(log_path)
    log_path.write_text("", encoding="utf-8")

    for nb_path in notebooks:
        nb_path = Path(nb_path).resolve()
        os.environ[NOTEBOOK_ENV] = str(nb_path)
        nb = nbformat.read(nb_path, as_version=4)
        client = NotebookClient(
            nb,
            timeout=1200,
            kernel_name="python3",
            allow_errors=True,
            resources={"metadata": {"path": str(Path(cwd).resolve() if cwd else nb_path.parent)}},
        )
        print(f"[run] {nb_path}", flush=True)
        try:
            client.execute()
        except Exception as exc:
            print(f"  [fail] {exc!r}", flush=True)
            continue
        errors = [
            c for c in nb.cells
            if c.cell_type == "code" and any(o.get("output_type") == "error" for o in c.get("outputs", []))
        ]
        if errors:
            print(f"  [warn] {len(errors)} cell(s) raised errors; later results may be incomplete")
            for c in errors[:3]:
                err = next(o for o in c.outputs if o.get("output_type") == "error")
                print(f"    {err.get('ename')}: {err.get('evalue', '')[:150]}")

    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line]
    print(f"\n{len(records)} affected pc.convert_to call(s). Details: {log_path}")
    seen = set()
    for r in records:
        key = (r["notebook"], r.get("code"), r["old"], r["fixed"])
        if key in seen:
            continue
        seen.add(key)
        print(f"\n{Path(r['notebook']).name}: {r.get('code', '?')}")
        print(f"  target {r['target']}")
        print(f"  old:   {r['old']}")
        print(f"  fixed: {r['fixed']}   ({r['reason']})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("notebooks", nargs="+")
    parser.add_argument("--log", default="keecas_118_findings.jsonl")
    parser.add_argument(
        "--cwd", help="working folder for the kernels (default: each notebook's own folder)"
    )
    args = parser.parse_args()
    _run(args.notebooks, Path(args.log).resolve(), args.cwd)
```
