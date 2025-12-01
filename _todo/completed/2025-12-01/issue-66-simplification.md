# Issue #66: Python 3.13 parse_expr Fix - Simplification

**Date:** 2025-12-01
**Branch:** claude/issue-66-20251128-1827
**Status:** Completed

## Objective

Simplify and improve the initial fix for Python 3.13 dict comprehension regression in `pc.parse_expr`.

## Background

The initial fix (commit f31ec0a) worked but had several weaknesses:
- Fragile heuristic: `len(f_locals) <= 3` to detect module-level comprehensions
- Could break with nested loops (4+ variables) or walrus operators
- Complex branching logic (~40 lines)
- Didn't properly consider cross-module isolation

## Deep Analysis Performed

Created comprehensive analysis documents in `.test/` (temporary):

1. **FIX_ANALYSIS.md** - Evaluated 6 alternative approaches:
   - Always merge globals (chosen approach)
   - Smart filtering
   - ChainMap lazy access
   - Require explicit local_dict
   - Bytecode detection
   - Hybrid with deprecation

2. **OPTION_B_ANALYSIS.md** - Impact on function scope isolation

3. **DESIRED_BEHAVIOR_ANALYSIS.md** - What Python's normal scoping does

4. **CROSS_MODULE_ISOLATION_ANALYSIS.md** - Critical discovery about f_globals vs f_back

5. **test_desired_behavior.py** - Verified Python's scoping behavior

6. **cross_module_test.py** - Tested cross-module variable isolation

## Key Discovery: f_globals vs f_back

**Critical insight:** When module_b imports module_a and calls module_a.func():
- `frame.f_back` → Points to module_b (calling context) ⚠️
- `frame.f_back.f_locals` → Contains module_b's variables (DANGEROUS!)
- `frame.f_globals` → Contains module_a's variables (SAFE!) ✅

**Why this matters:**
- `f_globals` is bound at **definition time** (where function was defined)
- `f_back` is determined at **call time** (where function was called from)
- For cross-module isolation, must use `f_globals`, NOT `f_back.f_locals`

## Solution Implemented

Replaced complex heuristic-based detection with simple, robust approach:

```python
# Before (40 lines of complex logic):
if is_comprehension:
    if frame3.f_back:
        local_dict = {**dict(enclosing.f_locals), **dict(frame3.f_locals)}
    else:
        local_dict = {**dict(frame3.f_globals), **dict(frame3.f_locals)}
else:
    local_dict = dict(frame3.f_locals)

# After (1 line):
local_dict = {**dict(frame3.f_globals), **dict(frame3.f_locals)}
```

## Benefits

1. **Cross-module isolation** - Uses f_globals (bound to defining module)
2. **Matches Python scoping** - Functions can access module variables
3. **Simpler code** - Reduced from ~40 lines to ~10 lines
4. **More robust** - No heuristics, no version-specific logic
5. **Correct precedence** - f_locals override f_globals

## Known Limitation

Comprehensions inside functions can't access parent function locals:

```python
def func():
    F_total = 100
    # Won't see F_total:
    {k: "F_total + k" | pc.parse_expr for k in [1,2,3]}
```

**Why acceptable:**
- Direct result of Python 3.13 PEP 667 scope isolation
- Rare in notebook usage
- Workaround: pass explicit `local_dict`
- Matches Python's own behavior

## Testing

- ✅ All 221 tests pass
- ✅ Regression test (.test/regression.py) passes
- ✅ Module-level comprehensions work
- ✅ Functions access module globals correctly
- ✅ Cross-module isolation verified

## Commits

1. `f31ec0a` - Initial fix with heuristic detection
2. `a0b47a2` - Simplified fix (final)

## Impact

- **Lines changed:** -36 lines (net reduction)
- **Complexity:** Significantly reduced
- **Robustness:** Improved (no heuristics)
- **Maintainability:** Much better (simpler logic)

## User Requirements Met

✅ Functions see module-level variables
✅ Locals shadow globals (Python precedence)
✅ Cross-module isolation (no variable leakage)
✅ Module-level comprehensions work
⚠️ Comprehensions in functions (documented limitation)

## Insights

The key to solving this was understanding Python's scoping mechanisms:
- Use `f_globals` for cross-module isolation (bound at definition time)
- Never use `f_back.f_locals` (could leak importing module's variables)
- Accept Python 3.13 PEP 667 limitations (comprehension scope isolation)

Simpler solutions are often more robust than complex heuristics.
