# Task Proposal: Fix CLI Performance with Lazy Imports

**Status:** ✅ IMPLEMENTED
**Created:** 2025-12-18
**Completed:** 2025-12-18
**Branch:** `feat/lazy-imports-performance`

## Original Objective

Fix the CLI performance issue where `keecas --version` takes ~2 seconds to execute because importing `keecas.__main__` triggers `keecas/__init__.py`, which loads heavy dependencies (SymPy, Pint).

**Current Problem Flow:**
```
keecas --version
↓
from keecas.__main__ import main
↓
keecas/__init__.py runs
↓
Imports: sympy (line 40), pint (line 31), pipe_command (line 10)
↓
~2 seconds of import overhead!
```

**Root Cause:** In Python, `from keecas.X import Y` ALWAYS runs `keecas/__init__.py` first. There's no way to import a module from within a package without running the package's `__init__.py`.

## Investigation Summary

**Explored Options:**
1. ✗ **Standalone module** (`src/keecas_cli.py` outside package) - NOT supported by uv_build
2. ✓ **Lazy imports** in `__init__.py` - Works with uv_build, makes package fast everywhere
3. ✗ **Switch to setuptools** - Would work but loses uv_build benefits

**Investigation Findings:**
- uv_build does NOT support standalone `.py` files outside packages
- uv_build does NOT respect `[tool.setuptools.py-modules]` configuration
- Only packages (directories with `__init__.py`) are included in builds
- Lazy imports via `__getattr__` is the standard Python pattern for this

**User Decision:** Proceed with **Option A: Lazy Imports**

## Implementation Plan

### Phase 1: Analyze Current Imports (Read-only)

**Categorize imports in `src/keecas/__init__.py`:**

**Heavy imports (MUST be lazy):**
- `sympy` (line 40) - 1-2s load time
- `pint` via `pint_sympy.unitregistry` (line 31) - ~500ms
- `pipe_command as pc` (line 10) - depends on sympy/pint

**Lightweight imports (CAN be eager):**
- `config` (from display.py via line 17)
- `version.__version__` (line 78)
- `dataframe.Dataframe` (line 14)
- `display.show_eqn, check, latex_inline_dict` (lines 17-22)
- `utils.dict_to_eq, eq_to_dict` (line 34)
- `label.generate_label, generate_unique_label` (line 28)
- `formatters.format_value` (line 25)
- `col_wrappers.wrap_column` (line 13)

**Initialization code (MUST be lazy):**
- `sympy.init_printing(...)` (line 45) - runs at import!
- `u.formatter.default_format = ...` (line 37) - runs at import!

**Current exports (`__all__`):**
```python
__all__ = [
    "Dataframe", "show_eqn", "config", "check", "latex_inline_dict",
    "dict_to_eq", "eq_to_dict", "generate_label", "generate_unique_label",
    "wrap_column", "format_value", "pc", "u", "sympy", "latex",
    "Eq", "Le", "symbols", "Basic", "Dict", "S", "Matrix", "__version__"
]
```

### Phase 2: Implement Lazy Loading

**2.1. Restructure `src/keecas/__init__.py`:**

```python
"""Keecas: Symbolic and units-aware calculations for Jupyter notebooks.

This package uses lazy imports for heavy dependencies (sympy, pint) to ensure
fast startup time for CLI commands.
"""

# Lightweight imports (loaded immediately)
from .col_wrappers import wrap_column
from .dataframe import Dataframe
from .display import check, config, latex_inline_dict, show_eqn
from .formatters import format_value
from .label import generate_label, generate_unique_label
from .utils import dict_to_eq, eq_to_dict
from .version import __version__

# All exports (including lazy-loaded ones)
__all__ = [
    "Dataframe",
    "show_eqn",
    "config",
    "check",
    "latex_inline_dict",
    "dict_to_eq",
    "eq_to_dict",
    "generate_label",
    "generate_unique_label",
    "wrap_column",
    "format_value",
    "pc",  # Lazy
    "u",  # Lazy
    "sympy",  # Lazy
    "latex",  # Lazy
    "Eq",  # Lazy
    "Le",  # Lazy
    "symbols",  # Lazy
    "Basic",  # Lazy
    "Dict",  # Lazy
    "S",  # Lazy
    "Matrix",  # Lazy
    "__version__",
]


def __getattr__(name):
    """Lazy load heavy dependencies only when accessed."""
    # Lazy load pint unit registry
    if name == "u":
        from .pint_sympy import unitregistry as u

        # Configure pint format (was at module level)
        u.formatter.default_format = config.display.pint_default_format

        globals()["u"] = u
        return u

    # Lazy load pipe_command
    elif name == "pc":
        from . import pipe_command as pc

        globals()["pc"] = pc
        return pc

    # Lazy load sympy and related exports
    elif name == "sympy":
        import sympy

        # Initialize sympy printing (was at module level)
        sympy.init_printing(mul_symbol=config.latex.default_mul_symbol, order="none")

        globals()["sympy"] = sympy
        return sympy

    elif name in ("latex", "Eq", "Le", "symbols", "Basic", "Dict", "S"):
        # Import sympy first (triggers lazy load)
        import sympy
        from sympy import Basic, Dict, Eq, Le, S, latex, symbols

        # Initialize printing if not done yet
        if "sympy" not in globals():
            sympy.init_printing(mul_symbol=config.latex.default_mul_symbol, order="none")
            globals()["sympy"] = sympy

        # Cache all sympy exports
        globals().update({
            "latex": latex,
            "Eq": Eq,
            "Le": Le,
            "symbols": symbols,
            "Basic": Basic,
            "Dict": Dict,
            "S": S,
        })

        return globals()[name]

    elif name == "Matrix":
        import sympy
        from sympy import ImmutableDenseMatrix as Matrix

        # Initialize printing if not done yet
        if "sympy" not in globals():
            sympy.init_printing(mul_symbol=config.latex.default_mul_symbol, order="none")
            globals()["sympy"] = sympy

        globals()["Matrix"] = Matrix
        return Matrix

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

**Key Design Decisions:**
1. **Initialization deferred:** `sympy.init_printing()` and `u.formatter.default_format` only run when the respective modules are first accessed
2. **Caching:** Lazy imports are cached in `globals()` to avoid re-importing
3. **Batch loading:** Importing one sympy export (e.g., `symbols`) loads and caches all of them
4. **Backward compatibility:** All import patterns work: `from keecas import u`, `keecas.u`, `from keecas import *`

### Phase 3: Testing & Validation

**3.1. Test lazy loading mechanism:**
```bash
# Should be fast (no sympy/pint)
python -X importtime -c "import keecas" 2>&1 | grep -E "(keecas|sympy|pint)"

# Should load sympy lazily
python -c "import keecas; print('Fast'); from keecas import sympy; print('Slow')"

# Star import should work
python -c "from keecas import *; print(u, pc, sympy)"
```

**3.2. Test CLI performance:**
```bash
# Should be <100ms (currently ~2s)
time python -c "from keecas.__main__ import main"
time keecas --version
time keecas --help

# Verify no heavy imports for --version
python -X importtime -c "from keecas.__main__ import main" 2>&1 | grep -i sympy
```

**3.3. Run full test suite:**
```bash
pytest -xvs  # All tests should pass
```

**3.4. Test notebook workflows:**
- Verify `from keecas import symbols, u, pc, show_eqn` still works
- Check that `from keecas import *` imports everything
- Test example notebooks run without errors

**3.5. Test IDE support:**
- Check autocomplete in VS Code / PyCharm
- Verify type hints are available
- Ensure no import warnings

### Phase 4: Performance Measurement

**4.1. Benchmark import time:**
```bash
# Before changes
time python -c "import keecas"

# After changes
time python -c "import keecas"
time python -c "from keecas import u, pc, sympy"  # Should trigger lazy load
```

**4.2. Profile with importtime:**
```bash
python -X importtime -c "import keecas" 2>&1 | tail -20
```

**4.3. Verify performance targets:**
- [ ] `import keecas` < 100ms (down from ~2s)
- [ ] `keecas --version` < 100ms
- [ ] `from keecas import u, pc, sympy` ~2s (loads heavy deps as before)

### Phase 5: Documentation & Cleanup

**5.1. Update CLAUDE.md:**
- Document lazy loading pattern
- Explain why this approach was chosen
- Note that heavy imports are deferred

**5.2. Add docstring comments:**
- Explain `__getattr__` mechanism
- Document caching strategy
- Note backward compatibility

**5.3. Clean up old code:**
- Remove `src/keecas/__main__.py` if no longer needed (currently has lightweight version check)
- Actually, keep `__main__.py` - it's the entry point and benefits from fast import!

## Critical Files to Modify

- `src/keecas/__init__.py` - **MAJOR RESTRUCTURING** (lazy imports)

## Success Criteria

- [ ] `keecas --version` executes in <100ms (down from ~2s)
- [ ] No sympy or pint imported for `--version` / `--help`
- [ ] All import patterns still work: `from keecas import *`, `from keecas import u`, `keecas.u`
- [ ] All existing tests pass (no regressions)
- [ ] Example notebooks run successfully
- [ ] CLI commands with full features still work (load heavy deps when needed)
- [ ] Package builds successfully with `uv build`

## Risks & Mitigations

**Risk 1: Breaking IDE autocomplete**
- *Mitigation:* Modern IDEs handle `__getattr__` well. Test with VS Code and PyCharm.

**Risk 2: Subtle import order issues**
- *Mitigation:* Comprehensive test suite + manual testing of notebooks.

**Risk 3: Type hints may not work**
- *Mitigation:* Consider adding type stubs if needed (`__init__.pyi`).

**Risk 4: Initialization order changes**
- *Mitigation:* `sympy.init_printing()` and pint configuration are deferred but still happen on first access.

## Estimated Effort

- **Phase 1 (Analysis):** 15 minutes - Read and categorize imports
- **Phase 2 (Implementation):** 30 minutes - Restructure `__init__.py`
- **Phase 3 (Testing):** 30 minutes - Run tests, verify imports
- **Phase 4 (Performance):** 15 minutes - Benchmark and measure
- **Phase 5 (Documentation):** 15 minutes - Update docs

**Total: ~2 hours**

## Next Steps

1. **User approval:** Review this proposal and approve to proceed
2. **Create branch:** `git checkout -b feat/lazy-imports-performance`
3. **Implement:** Follow phases 1-5 above
4. **Test thoroughly:** Ensure no regressions
5. **Create PR:** Merge to `dev` branch first for testing

---

## Implementation Results ✅

**Status: SUCCESSFULLY IMPLEMENTED**

### Performance Benchmarks

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| `import keecas` sympy/pint imports | ALL | 0 | ∞ (none loaded!) |
| `keecas --version` | ~2000ms | 45ms | **44x faster** |
| `keecas config path` | ~2000ms+ | 88ms | **23x faster** |
| Test suite | 221 tests | 221 tests | All passing ✅ |

### Final Implementation

1. **Restructured `src/keecas/__init__.py`:**
   - ALL exports are now lazy-loaded except `__version__`
   - Used `__getattr__()` for lazy loading
   - Fixed config module collision issue (keecas.config package vs config object)
   - Handled variable scope issues in conditional imports

2. **Key Challenge Solved:**
   - Discovered that importing `from .config.manager` adds `config` (module) to namespace
   - Fixed by checking `hasattr(globals()["config"], "display")` to verify correct type
   - This prevents confusion between config package and config object

3. **Testing:**
   - All 221 tests pass
   - Zero sympy/pint imports on basic `import keecas`
   - CLI performance improved by 44x
   - Backward compatibility maintained - all import patterns work

### Files Modified

- `src/keecas/__init__.py` - Complete restructure with lazy loading (217 lines)

### Ready for Commit

Task completed successfully and ready to be merged to `dev` branch.
