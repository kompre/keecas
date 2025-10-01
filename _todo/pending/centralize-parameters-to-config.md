# Centralize Parameters to Config

**Status**: Updated for v1.0.0 (post LaTeX Environment Templating)
**Original Date**: Pre-v1.0.0
**Updated**: 2025-10-01
**Current Version**: 0.1.2 → Target: 1.0.0

## Original Objective

Analyze the `show_eqn` function for parameters that could be set in the config file.

---

## What Changed: LaTeX Environment Templating (PR #5)

The LaTeX environment templating system (merged in v1.0.0) already addressed several items from the original proposal:

### ✅ Completed via Environment Templating

1. **Environment-specific separators** → Now in `config.latex.environments.{name}.separator`
   - Each environment (align, equation, gather, cases, split, alignat, rcases) has its own separator
   - User-extensible via TOML: `[latex.environments.custom]`
   - Inline definitions supported: `show_eqn(eqns, environment={...})`

2. **`environments_without_separator` list** → Eliminated
   - Handled naturally by `separator: ""` in environment definitions
   - No hardcoded list needed

3. **`default_mul_symbol`** → Moved to `config.latex.default_mul_symbol`
   - Grouped with other LaTeX formatting options
   - TOML: `[latex] default_mul_symbol = "\\,"`

4. **Line separators** → Now in `config.latex.environments.{name}.line_separator`
   - Configurable per environment
   - Example: `line_separator = " \\\\\\n "`

### Current Architecture (v1.0.0)

```python
# Config structure
config.latex.environments.align.separator           # "&"
config.latex.environments.align.line_separator      # " \\\\\n "
config.latex.environments.equation.separator        # ""
config.latex.default_environment                    # "align"
config.latex.default_mul_symbol                     # r"\,"
```

**Result**: Environment-specific behavior is now fully configurable and extensible.

---

## Remaining Parameters to Centralize

### User Feedback from Original Proposal

From HTML comments in original proposal:
- **Scope**: "everything" - make all remaining parameters configurable
- **Presets**: "no" - skip preset system complexity
- **Environment logic**: "defer to environment template config" - ✅ done
- **Migration tools**: "no" - breaking changes acceptable
- **Backward compatibility**: "Prefer a clean codebase rather than having non breaking patches all over"
- **col_wrap**: "let put aside for now" - defer simplification
- **sep**: "Yes, separator should be defined by the environment template applied"
- **Version**: "check the pyproject file for current version. Until publishing to main, we're on track for 1.0.0"

### Analysis of Current `show_eqn` Signature

```python
def show_eqn(
    eqns: dict[Basic, Any] | list[dict[Basic, Any]] | Dataframe,
    environment: str | dict[str, Any] | None = None,    # ✅ Already configurable
    sep: str | list[str] = "&",                         # ⚠️ Should defer to environment
    label: str | dict[str, str] | None = None,          # ❌ Not applicable to config
    label_command: str | None = None,                   # ✅ Already configurable
    col_wrap: list[None | tuple[str, str]] | None = None,  # ⏸️ Deferred
    float_format: str | None = None,                    # ❌ Needs config
    debug: bool | None = None,                          # ✅ Already configurable
    env_arg: str | None = None,                         # ❌ Environment-specific, not global
    **kwargs: Any,
) -> Markdown:
```

### 1. **col_wrap** (Priority: DEFERRED)

**User Decision:** "Let put aside for now" - keep current implementation

**Current State:**
```python
# ConfigOptions line 288-298
col_wrap: list = field(default_factory=lambda: [
    None,
    {
        Basic: ("=", ""),
        Markdown: (r"\qquad", ""),
        str: (r"\qquad", ""),
        int: ("=", ""),
        float: ("=", ""),
        object: ("", ""),
    },
])
```

**Current Behavior (line 410 in display.py):**
```python
col_wrap = create_dataframe(seed=col_wrap, keys=keys, width=num_cols, default_value=col_wrap[-1])
```

**User Requirements Met:**
- ✅ Accepts list of tuples: `[None, ("=", "")]`
- ✅ Last element becomes default for following columns via `default_value=col_wrap[-1]`
- ✅ Passed to `create_dataframe()` which handles per-row dataframe creation

**No Changes for v1.0.0:**
- Current implementation already meets user requirements
- Type-based dict complexity can be addressed in future iteration
- Focus on `float_format` and `sep` instead

### 2. **float_format** (Priority: HIGH)

**User Note:** `<!-- float_format should be in the config -->`

**Current State:**
- `float_format: str | None = None` in function signature
- No config default - always `None` unless explicitly passed
- Users must repeat format spec in every call

**Proposal:**
```python
@dataclass
class DisplayConfig:
    # ... existing fields ...
    default_float_format: str | None = None   # NEW
```

**TOML Configuration:**
```toml
[display]
# default_float_format = ".3f"  # Uncomment to set default
```

**Implementation in `show_eqn()`:**
```python
# Add after line 330
if float_format is None:
    float_format = config.display.default_float_format
```

**Impact:** Backward compatible - no breaking changes, just adds a default fallback.

### 3. **sep** (Priority: HIGH)

**User Approval:** "Yes, separator should be defined by the environment template applied"

**Current Implementation (lines 370-372):**
```python
# Use config separator if not explicitly overridden (default value check)
if sep == "&":
    sep = env_config.separator
```

**Problems:**
- Fragile: depends on detecting the default value `"&"`
- Not explicit that environment config is the source of truth

**Proposal:** Make environment separator the explicit default

Change function signature:
```python
def show_eqn(
    eqns: dict[Basic, Any] | list[dict[Basic, Any]] | Dataframe,
    environment: str | dict[str, Any] | None = None,
    sep: str | list[str] | None = None,  # Changed from = "&"
    ...
):
```

Then:
```python
# Resolve separator (cleaner logic)
if sep is None:
    sep = env_config.separator
```

**Breaking Change:** Minimal - only affects code that explicitly checks `if sep == "&"` - rare.

---

## Revised Implementation Plan

### Phase 1: Config Structure for float_format (0.5 day)

**Tasks:**
1. Add to `DisplayConfig`:
   ```python
   default_float_format: str | None = None
   ```

2. Update TOML serialization in `ConfigOptions.to_dict()`:
   - Add `default_float_format` to `display` section

3. Update TOML deserialization in `ConfigOptions.update_from_dict()`:
   - Handle new field in `display` section

4. Update `_generate_config_template()`:
   - Add commented example for `default_float_format`
   - Document usage and format spec examples

**Files:** `src/keecas/config.py`

### Phase 2: Parameter Resolution (0.5 day)

**Tasks:**
1. **float_format resolution** (line ~330 in display.py):
   ```python
   if float_format is None:
       float_format = config.display.default_float_format
   ```

2. **sep resolution** (line ~370):
   ```python
   # Change function signature default from "&" to None
   if sep is None:
       sep = env_config.separator
   ```

3. Update function signature:
   ```python
   def show_eqn(
       eqns: dict[Basic, Any] | list[dict[Basic, Any]] | Dataframe,
       environment: str | dict[str, Any] | None = None,
       sep: str | list[str] | None = None,  # Changed!
       label: str | dict[str, str] | None = None,
       label_command: str | None = None,
       col_wrap: list[None | tuple[str, str]] | None = None,
       float_format: str | None = None,
       debug: bool | None = None,
       env_arg: str | None = None,
       **kwargs: Any,
   ) -> Markdown:
   ```

**Files:** `src/keecas/display.py`

### Phase 3: Testing and Documentation (1 day)

**Tasks:**
1. **Tests:**
   - Test `float_format` fallback to config
   - Test `float_format=None` uses config value
   - Test explicit `float_format` overrides config
   - Test `sep=None` uses environment separator
   - Test parameter precedence: explicit > environment > config > hardcoded
   - Test TOML config loading for `default_float_format`

2. **Documentation:**
   - Update `CLAUDE.md` with `default_float_format` option
   - Update `show_eqn()` docstring
   - Document `sep=None` behavior change
   - Add migration notes for v0.1.x → v1.0.0

3. **Config template:**
   - Ensure `keecas config init` includes `default_float_format` with examples
   - Add comments explaining format spec syntax (e.g., `.3f`, `.2e`)

**Files:** `tests/test_display.py`, `CLAUDE.md`, `src/keecas/display.py`

---

## Benefits

### 1. User Experience
- **Consistency:** Set `float_format` once in config, applies everywhere
- **Less Boilerplate:** No need to repeat `float_format=".3f"` in every cell
- **Project Defaults:** Local config for project-specific formatting preferences
- **Clean Separator Logic:** Explicit environment-based defaults

### 2. Code Quality
- **Simpler Logic:** `if sep is None` is clearer than `if sep == "&"`
- **Explicit Defaults:** Clear precedence: explicit > environment > config > hardcoded
- **Maintainable:** Environment config is single source of truth for separators

### 3. Addresses User Feedback
- ✅ User note: "float_format should be in the config"
- ✅ User approval: "separator should be defined by the environment template applied"
- ✅ User preference: "clean codebase" - simpler sep logic
- ⏸️ col_wrap deferred per user request

---

## Breaking Changes (v0.1.x → v1.0.0)

### sep Default Value

**Old (v0.1.x):**
```python
show_eqn(eqns, sep="&")  # Explicit default
```

**New (v1.0.0):**
```python
show_eqn(eqns, sep=None)  # Defers to environment config
show_eqn(eqns)            # Same - environment separator used
```

**Migration:**
- Code relying on `sep="&"` default: No change needed (align environment uses "&")
- Code checking `if sep == "&"`: Update to `if sep is None` or `if sep == env_config.separator`

**Impact:** Minimal - very rare edge case

---

## Configuration Precedence (Final)

1. **Explicit function parameters** (highest priority)
2. **Environment-specific config** (e.g., `config.latex.environments.align.separator`)
3. **Display config defaults** (e.g., `config.display.default_float_format`)
4. **Hardcoded fallbacks** (lowest priority)

---

## Example Usage

### Before (v0.1.x)
```python
# User must specify repeatedly
show_eqn(equations, float_format=".3f")
show_eqn(more_equations, float_format=".3f")
show_eqn(final_equations, float_format=".3f")
```

### After (v1.0.0)
```toml
# .keecas/config.toml (set once per project)
[display]
default_float_format = ".3f"
```

```python
# Clean notebook cells - config applied automatically
show_eqn(equations)
show_eqn(more_equations)
show_eqn(final_equations)

# Override when needed
show_eqn(special_equations, float_format=".5f")
```

---

## Timeline Estimate

- **Phase 1**: 0.5 day (config structure)
- **Phase 2**: 0.5 day (parameter resolution)
- **Phase 3**: 1 day (testing and docs)

**Total**: ~2 days of development work

---

## Scope Summary

### In Scope for v1.0.0
- ✅ Add `config.display.default_float_format`
- ✅ Change `sep` default from `"&"` to `None`
- ✅ Update documentation and tests

### Out of Scope (Deferred)
- ⏸️ col_wrap simplification (user request: "put aside for now")
- ⏸️ Type-based dict removal (can be addressed in future iteration)

---

## Implementation Progress

### Session 2025-10-01: Complete Implementation

**Completed Tasks:**

1. ✅ **Added `default_float_format` to DisplayConfig**
   - New optional field with `str | None = None` default
   - Config serialization/deserialization updated
   - Template generation updated with format_value() helper

2. ✅ **Changed `sep` default to `None`**
   - Function signature: `sep: str | list[str] | None = None`
   - Resolution logic: uses environment separator when None
   - Breaking change documented for v1.0.0

3. ✅ **Implemented float_format validation (Option 3)**
   - Smart wrapping: `.3f` → `{:.3f}`, `:0.3f` → `{:0.3f}`
   - Validation by testing format with 1.0
   - Clear error messages for invalid formats
   - Supports all Python format specs

4. ✅ **Refactored `format_decimal_numbers`**
   - Removed hardcoded default `"{:.2f}"`
   - Changed to `format_string: str | None = None`
   - Returns unformatted when None

5. ✅ **Fixed config template None handling**
   - format_value() now handles None values specially
   - Generates commented examples: `# default_float_format = ".3f"`
   - Works for both global and local configs

6. ✅ **Test Coverage**
   - Added 5 new tests for float_format and sep behavior
   - All 103 tests passing
   - Tests cover validation, fallback, and environment resolution

**Files Modified:**
- `src/keecas/config.py` - DisplayConfig, serialization, template generation
- `src/keecas/display.py` - show_eqn(), format_decimal_numbers()
- `tests/test_display.py` - 5 new tests
- `CLAUDE.md` - Updated examples and breaking changes documentation

**Technical Details:**

**Float Format Validation:**
```python
# Handles multiple input formats
".3f" → "{:.3f}"      # Common shorthand
":0.3f" → "{:0.3f}"   # With colon prefix
"{:.3f}" → "{:.3f}"   # Already wrapped

# Validates by testing
float_format.format(1.0)  # Raises ValueError if invalid
```

**Sep Resolution Logic:**
```python
if sep is None:
    sep = env_config.separator  # Defer to environment config
```

**Config Template Fix:**
```python
# Before: toml.dumps({'default_float_format': None}) → ''
# After: Special case returns: '# default_float_format = ".3f"'
```

**Breaking Changes:**
- `sep` parameter default: `"&"` → `None` (minimal impact)
- Backward compatible for align environment (still uses "&")

---

**Status**: ✅ Implementation complete. All tests passing (103/103). Ready for commit and PR.
