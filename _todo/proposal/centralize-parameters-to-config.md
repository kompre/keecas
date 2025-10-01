# Centralize Parameters to Config

**Status**: Updated for v1.0.0 (post LaTeX Environment Templating)
**Original Date**: Pre-v1.0.0
**Updated**: 2025-10-01

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

### Analysis of Current `show_eqn` Signature

```python
def show_eqn(
    eqns: dict[Basic, Any] | list[dict[Basic, Any]] | Dataframe,
    environment: str | dict[str, Any] | None = None,    # ✅ Already configurable
    sep: str | list[str] = "&",                         # ⚠️ Partially configurable (via environment)
    label: str | dict[str, str] | None = None,          # ❌ Not applicable to config
    label_command: str | None = None,                   # ✅ Already configurable
    col_wrap: list[None | tuple[str, str]] | None = None,  # ❌ Needs config
    float_format: str | None = None,                    # ❌ Needs config (user note!)
    debug: bool | None = None,                          # ✅ Already configurable
    env_arg: str | None = None,                         # ❌ Environment-specific, not global
    **kwargs: Any,
) -> Markdown:
```

### 1. **col_wrap** (Priority: HIGH)

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

**Problems:**
- Complex type-based dict makes TOML serialization impossible
- Hardcoded in `ConfigOptions` as a field (not in a config dataclass)
- Not part of any TOML-serializable config section
- Users must either accept this default or specify `col_wrap` on every `show_eqn()` call

<!--  -->



**Proposal:** Simplify to string-based wrapping

```python
@dataclass
class DisplayConfig:
    print_label: bool = False
    debug: bool = False
    katex: bool = False
    default_col_wrap_left: str | None = None   # NEW: First column wrap
    default_col_wrap_right: str = "="          # NEW: Subsequent columns wrap
```

**TOML Configuration:**
```toml
[display]
default_col_wrap_left = ""      # or omit for null
default_col_wrap_right = "="
```

**Implementation in `show_eqn()`:**
```python
# Line 360-361 (current)
if not col_wrap:
    col_wrap = config.col_wrap

# Proposed change
if not col_wrap:
    col_wrap = [
        config.display.default_col_wrap_left,
        (config.display.default_col_wrap_right, "")
    ]
```

**Breaking Change:**
- Remove complex type-based dict
- Users with custom `config.col_wrap` must migrate to new fields
- Simpler, TOML-compatible structure

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
default_float_format = ".3f"  # or omit for null
```

**Implementation in `show_eqn()`:**
```python
# Add after line 330
if float_format is None:
    float_format = config.display.default_float_format
```

**Backward Compatible:** No breaking changes, just adds a default fallback.

### 3. **sep** (Priority: LOW - Already Mostly Handled)

**Current Implementation (lines 370-372):**
```python
# Use config separator if not explicitly overridden (default value check)
if sep == "&":
    sep = env_config.separator
```

**Analysis:**
- Already defers to environment config when user doesn't override
- Fragile: depends on detecting the default value `"&"`
- Works correctly but could be cleaner

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
# Resolve separator
if sep is None:
    sep = env_config.separator
```

**Breaking Change:** Minimal - only affects code that checks `sep == "&"` explicitly.

---

## Revised Implementation Plan

### Phase 1: Config Structure Enhancement (1 day)

**Tasks:**
1. Add to `DisplayConfig`:
   ```python
   default_col_wrap_left: str | None = None
   default_col_wrap_right: str = "="
   default_float_format: str | None = None
   ```

2. Update TOML serialization in `ConfigOptions.to_dict()`:
   - Add `default_col_wrap_left`, `default_col_wrap_right`, `default_float_format` to `display` section

3. Update TOML deserialization in `ConfigOptions.update_from_dict()`:
   - Handle new fields in `display` section

4. Update `_generate_config_template()`:
   - Add commented examples for new fields
   - Document `default_col_wrap_left` and `default_col_wrap_right` usage
   - Document `default_float_format` usage

5. Remove `col_wrap` field from `ConfigOptions`:
   - Delete lines 288-298 in config.py
   - Will be replaced by dynamic generation from new fields

**Files:** `src/keecas/config.py`

### Phase 2: Parameter Resolution in show_eqn (1 day)

**Tasks:**
1. **float_format resolution** (line ~330):
   ```python
   if float_format is None:
       float_format = config.display.default_float_format
   ```

2. **col_wrap resolution** (line ~360):
   ```python
   if not col_wrap:
       col_wrap = [
           config.display.default_col_wrap_left,
           (config.display.default_col_wrap_right, "")
       ]
   ```

3. **sep resolution** (line ~370):
   ```python
   # Change function signature default from "&" to None
   if sep is None:
       sep = env_config.separator
   ```

4. Update function signature:
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

### Phase 3: Simplify col_wrap Structure (1 day)

**Tasks:**
1. **Remove type-based dict complexity:**
   - Current `create_dataframe()` handles `{Basic: ("=", ""), str: (r"\qquad", "")}`
   - Simplify to just handle `(left, right)` tuples

2. **Update `create_dataframe()` helper** (if needed):
   - Review lines 408-410 in display.py
   - Ensure it works with simplified structure

3. **Test with existing notebooks:**
   - Ensure backward compatibility path works
   - Document migration for users with custom `config.col_wrap`

**Files:** `src/keecas/display.py`

### Phase 4: Testing and Documentation (1 day)

**Tasks:**
1. **Tests:**
   - Test `float_format` fallback to config
   - Test `col_wrap` fallback to config
   - Test `sep` environment-based default
   - Test parameter precedence: explicit > config > hardcoded
   - Test TOML config loading for new fields

2. **Documentation:**
   - Update `CLAUDE.md` with new config options
   - Update docstrings in `show_eqn()`
   - Add migration notes for v1.0.0 → v2.0.0

3. **Config template:**
   - Ensure `keecas config init` includes new fields with clear comments

**Files:** `tests/test_display.py`, `CLAUDE.md`, `src/keecas/display.py`

---

## Benefits

### 1. User Experience
- **Consistency:** Set formatting once in config, applies everywhere
- **Less Boilerplate:** No need to repeat `float_format=".3f"` in every cell
- **Project Defaults:** Local config for project-specific preferences

### 2. Code Quality
- **Simplicity:** Remove complex type-based dict from `col_wrap`
- **Clean Config:** All config in TOML-serializable dataclasses
- **Explicit Defaults:** Clear precedence: explicit > config > environment > hardcoded

### 3. Addresses User Feedback
- User note: "float_format should be in the config" → directly implemented
- User preference: "everything" should be configurable → achieves full coverage
- User preference: "clean codebase" → removes type-dict complexity

---

## Breaking Changes (v1.0.0 → v2.0.0)

### col_wrap Structure

**Old (v1.0.0):**
```python
from keecas import config
config.col_wrap = [None, {Basic: ("=", ""), str: (r"\qquad", "")}]
```

**New (v2.0.0):**
```toml
# .keecas/config.toml
[display]
default_col_wrap_left = ""
default_col_wrap_right = "="
```

```python
# Or programmatically
config.display.default_col_wrap_left = None
config.display.default_col_wrap_right = "="
```

### sep Default Value

**Old (v1.0.0):**
```python
show_eqn(eqns, sep="&")  # Explicit default
```

**New (v2.0.0):**
```python
show_eqn(eqns, sep=None)  # Defers to environment config
show_eqn(eqns)            # Same - environment separator used
```

**Impact:** Only affects code that explicitly checks `if sep == "&"` - rare.

---

## Configuration Precedence (Final)

1. **Explicit function parameters** (highest priority)
2. **Environment-specific config** (e.g., `config.latex.environments.align.separator`)
3. **Display config defaults** (e.g., `config.display.default_float_format`)
4. **Hardcoded fallbacks** (lowest priority)

---

## Example Usage

### Before (v1.0.0)
```python
# User must specify repeatedly or accept hardcoded defaults
show_eqn(equations, float_format=".3f", col_wrap=[None, ("=", "")])
show_eqn(more_equations, float_format=".3f", col_wrap=[None, ("=", "")])
show_eqn(final_equations, float_format=".3f", col_wrap=[None, ("=", "")])
```

### After (v2.0.0)
```toml
# .keecas/config.toml (set once per project)
[display]
default_float_format = ".3f"
default_col_wrap_left = ""
default_col_wrap_right = "="
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

- **Phase 1**: 1 day (config structure)
- **Phase 2**: 1 day (parameter resolution)
- **Phase 3**: 1 day (simplify col_wrap)
- **Phase 4**: 1 day (testing and docs)

**Total**: ~4 days of development work

---

## Questions for User Review

1. **col_wrap simplification**: Is removing the type-based dict acceptable? (Assumes yes based on "clean codebase" preference)

<!-- let put aside col_wrap for now. It should also accept as default a list of tuples like so `[None, ("=", "")]` (old implementation). This will be passed to `create_dataframe()` method and return a dataframe, where the first column has no wrapper, the second column wraps with `=` and '', following columns wraps to None again.

Here I want a behavior change: last element of the list becomes the default for following cells (check the create_dataframe() method).

 -->

2. **float_format default**: Should default be `None` or something like `".2f"`?

3. **sep breaking change**: Is changing default from `"&"` to `None` acceptable for cleaner logic?

<!-- Yes, separator should be defined by the environment template applied -->

4. **Version number**: Should this be v2.0.0 (given breaking changes) or v1.1.0?

<!-- check the pyproject file for current version. Until publishing to main, we're on track for 1.0.0 -->

---

**Status**: Awaiting user approval to proceed with implementation.
