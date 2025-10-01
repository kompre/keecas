# LaTeX Environment Templating System

**Status**: ❌ Rejected (PR #4 closed by user)
**Branch**: `feature/latex-environment-templating`
**Started**: 2025-09-30
**Completed**: 2025-10-01
**PR**: #4 (closed)

## Objective

Convert hardcoded environment logic in `show_eqn` to a configurable templating system that allows users to define custom LaTeX environments.

## Implementation Strategy

Extend existing TOML configuration system with environment-specific settings using dictionary-based configuration (no wrapper classes).

### 1. Environment Configuration Structure

Add to [src/keecas/config.py](src/keecas/config.py):

```python
@dataclass
class EnvironmentConfig:
    """LaTeX environment behavior configuration."""
    environments: dict[str, dict[str, Any]] = field(default_factory=lambda: {
        "align": {
            "separator": "&",
            "line_separator": r" \\\n ",
            "supports_multiple_labels": True,
            "outer_environment": "align",
            "inner_environment": None
        },
        "equation": {
            "separator": "",
            "line_separator": "",
            "supports_multiple_labels": False,
            "outer_environment": "equation",
            "inner_environment": None
        },
        "gather": {
            "separator": "",
            "line_separator": r" \\\n ",
            "supports_multiple_labels": True,
            "outer_environment": "gather",
            "inner_environment": None
        },
        "cases": {
            "separator": "&",
            "line_separator": r" \\\n ",
            "supports_multiple_labels": False,
            "outer_environment": "align",
            "inner_environment": "aligned",
            "inner_prefix": r"\left\{",
            "inner_suffix": r"\right.",
            "label_position": "outer"
        },
        "split": {
            "separator": "&",
            "line_separator": r" \\\n ",
            "supports_multiple_labels": False,
            "outer_environment": "align",
            "inner_environment": "aligned",
            "label_position": "outer"
        }
    })
```

**Key Design:**
- **Standard environments**: `outer_environment` only, `inner_environment = None`
- **Nested environments**: Both `outer_environment` and `inner_environment` with optional `inner_prefix`/`inner_suffix`
- **Argument support**: Handled via `env_arg` parameter (e.g., `\begin{alignat}{2}`)

### 2. Configuration Integration

Add to `ConfigOptions` class:
```python
@dataclass
class ConfigOptions:
    # ... existing fields ...
    environments: EnvironmentConfig = field(default_factory=EnvironmentConfig)
```

### 3. TOML User Configuration

**Current Structure** (to be flattened - see Post-Completion Refinements):
```toml
[environments]
environments = {
    custom_align = {
        separator = "&",
        line_separator = " \\\\[0.5em]\n ",
        supports_multiple_labels = true,
        outer_environment = "align"
    },
    boxed_equation = {
        separator = "",
        line_separator = "",
        supports_multiple_labels = false,
        outer_environment = "equation",
        outer_prefix = "\\boxed{",
        outer_suffix = "}"
    }
}
```

**Proposed Structure** (after flattening):
```toml
[environments.custom_align]
separator = "&"
line_separator = " \\\\[0.5em]\n "
supports_multiple_labels = true
outer_environment = "align"

[environments.boxed_equation]
separator = ""
line_separator = ""
supports_multiple_labels = false
outer_environment = "equation"
outer_prefix = "\\boxed{"
outer_suffix = "}"
```

### 4. Template Generation Function

Replace wrap tuple generation with template-based approach:

```python
def _generate_environment_template(environment: str, env_config: dict, label: str | None, env_arg: str | None = None) -> str:
    """Generate complete LaTeX template with ___body___ placeholder.

    Args:
        environment: Environment name (e.g., "align", "align*")
        env_config: Environment configuration dictionary
        label: Optional label for the environment
        env_arg: Optional argument string for environment (e.g., "{2}" for alignat{2})
                 User provides complete argument including braces. Defaults to empty string.
    """
    outer_env = env_config["outer_environment"]
    inner_env = env_config.get("inner_environment")

    # Handle starred environments
    if "*" in environment:
        outer_env += "*"

    # Use env_arg directly (already includes braces) or empty string
    arg_str = env_arg if env_arg else ""

    if inner_env is None:
        # Standard: \begin{env}{arg}___body___\end{env}
        outer_prefix = env_config.get("outer_prefix", "")
        outer_suffix = env_config.get("outer_suffix", "")
        label_str = _attach_label(label) if not env_config['supports_multiple_labels'] else ''

        template = rf"{outer_prefix}\begin{{{outer_env}}}{arg_str}{label_str}" + "\n___body___\n" + rf"\end{{{outer_env}}}{outer_suffix}"
    else:
        # Nested: \begin{outer}\n\t\prefix\begin{inner}{arg}___body___\end{inner}\suffix\n\end{outer}
        inner_prefix = env_config.get("inner_prefix", "")
        inner_suffix = env_config.get("inner_suffix", "")
        outer_prefix = env_config.get("outer_prefix", "")
        outer_suffix = env_config.get("outer_suffix", "")
        label_str = _attach_label(label)

        template = rf"""{outer_prefix}\begin{{{outer_env}}}{label_str}
	{inner_prefix}\begin{{{inner_env}}}{arg_str}
___body___
	\end{{{inner_env}}}{inner_suffix}
\end{{{outer_env}}}{outer_suffix}"""

    return template
```

**Produces:**
```latex
\begin{align}\label{eq-label}
\left\{\begin{aligned}
    x &= 1 \\
    y &= 2
\end{aligned}\right.
\end{align}
```

### 5. show_eqn Integration

Keep existing function signature, use config internally:

```python
def show_eqn(eqns, environment=None, sep="&", label=None, env_arg=None, **kwargs):
    # Get environment configuration
    if not environment:
        environment = config.default_environment

    # Note: After flattening, this will be config.environments[environment]
    env_config = config.environments.environments.get(environment)
    if not env_config:
        warn(f"Unknown environment '{environment}', using 'align'")
        # Note: After flattening, this will be config.environments["align"]
        env_config = config.environments.environments["align"]

    # Use config separator if not explicitly overridden
    if sep == "&":  # Default parameter value
        sep = env_config["separator"]

    # Generate template with optional argument
    template = _generate_environment_template(environment, env_config, label, env_arg)

    # Rest of existing logic...
    template = template.replace("___body___", body)
```

### 6. Environment Validation

At config load time:
- Check required fields: `separator`, `line_separator`, `outer_environment`
- Warn on unknown fields (typos like `seprator`)
- Validate nested environments: `inner_environment` valid when specified
- Ensure prefix/suffix are strings

**No LaTeX syntax validation** - let LaTeX compiler handle that.

### 7. CLI Integration (Optional - Phase 3)

```bash
keecas config environments list              # List available environments
keecas config environments show align        # Show specific definition
keecas config environments validate          # Validate all definitions
```

Implementation in [src/keecas/cli.py](src/keecas/cli.py) using argparse:
```python
def handle_config_environments(args):
    """Handle environment-specific config commands."""
    config_manager = get_config_manager()

    if args.action == "list":
        # Note: After flattening, this will be config_manager.options.environments.keys()
        for name in config_manager.options.environments.environments.keys():
            print(f"  {name}")

    elif args.action == "show":
        # Note: After flattening, this will be config_manager.options.environments.get(args.name)
        env_config = config_manager.options.environments.environments.get(args.name)
        if env_config:
            for key, value in env_config.items():
                print(f"  {key}: {value}")
        else:
            print(f"Unknown environment: {args.name}")
```

## Implementation Plan

### Phase 1: Core Configuration (1 day)
1. Add `EnvironmentConfig` dataclass to [src/keecas/config.py](src/keecas/config.py)
2. Update TOML serialization for environment settings
3. Add built-in environment definitions
4. Add configuration loading tests

### Phase 2: Refactor show_eqn (1 day)
5. Create `_generate_environment_template()` function
6. Replace hardcoded conditionals with config-based logic
7. Update environment lookup in `show_eqn()`
8. Add environment-specific behavior tests

### Phase 3: Custom Environments (0.5 days)
9. Enable user-defined environments via TOML
10. Add configuration validation
11. Update CLI for environment management (optional)
12. Add example configurations

**Total**: ~2.5 days

## Benefits

- Builds on existing TOML configuration system
- Backward compatible (existing code works unchanged)
- Simple dictionary-based implementation
- Enables user customization via `.keecas/config.toml`
- Concentrates environment logic in configuration

**Note**: Post-completion refinements (env_arg, flattening) will add optional parameters but maintain backward compatibility.

## Example Usage

**Before:**
```python
show_eqn(equations, environment="align")  # Limited to built-in environments
```

**After:**
```python
# Built-in environments work the same
show_eqn(equations, environment="align")

# Custom environments from config
show_eqn(equations, environment="spaced_align")
```

**Custom configuration:**
```toml
[environments.spaced_align]
separator = "&"
line_separator = " \\\\[0.5em]\n "
supports_multiple_labels = true
outer_environment = "align"
```

## Implementation Summary

### Completed Changes

**Phase 1: Core Configuration**
- ✅ Added `EnvironmentConfig` dataclass to [src/keecas/config.py](src/keecas/config.py:91-144)
- ✅ Integrated into `ConfigOptions` with backward compatibility
- ✅ Updated TOML serialization (`to_toml_dict()` and `update_from_dict()`)
- ✅ Added validation for custom environments (required fields, typo detection)

**Phase 2: Refactor show_eqn**
- ✅ Created `_attach_label()` helper function [src/keecas/display.py](src/keecas/display.py:43-91)
- ✅ Created `_generate_environment_template()` function [src/keecas/display.py](src/keecas/display.py:94-139)
  - **Note**: Current implementation does not include `env_arg` parameter (planned in Post-Completion Refinements)
- ✅ Replaced hardcoded environment logic with config-based lookup
- ✅ Updated separator and line_separator to use environment config
- ✅ Removed hardcoded `single_label_env`, `join_token` lists

**Phase 3: Testing & Validation**
- ✅ Added 10 comprehensive environment tests in [tests/test_display.py](tests/test_display.py:267-394)
- ✅ All 92 tests pass (30 display tests + 62 other tests)
- ✅ Validated all 5 built-in environments (align, equation, gather, cases, split)
- ✅ Validated starred variants (align*, cases*, etc.)
- ✅ Validated custom environment definitions
- ✅ Validated unknown environment fallback behavior

### Key Achievements

1. **Template-Based System**: Replaced wrap tuple pattern with clean template generation
2. **Configuration-Driven**: All environment behavior now defined in TOML-compatible config
3. **Backward Compatible**: Completed work has no breaking changes - all existing code works unchanged
4. **User Extensible**: Users can define custom environments via `.keecas/config.toml`
5. **Validated**: Environment configs validated on load with helpful error messages
6. **Well-Tested**: 10 new tests covering all environment types and edge cases

### Files Modified

- [src/keecas/config.py](src/keecas/config.py) - Added `EnvironmentConfig`, TOML support, validation
- [src/keecas/display.py](src/keecas/display.py) - Refactored `show_eqn()`, added helper functions
- [tests/test_display.py](tests/test_display.py) - Added 10 comprehensive environment tests

### Performance Impact

- **No performance regression**: Template generation is lightweight
- **Reduced code complexity**: ~80 lines of hardcoded logic replaced with 45 lines of clean template generation
- **Better maintainability**: Environment behavior isolated in configuration

### Future Enhancements (Not in Scope - Original Plan)

- CLI commands for environment management (`keecas config environments list/show`)
- Additional built-in environments (e.g., multline, flalign)

**Note**: Argument support was originally out of scope but is now planned in Post-Completion Refinements.

### Current Implementation vs Planned Refinements

**✅ Completed (Currently in codebase)**:
- Template-based environment system with `_generate_environment_template()`
- Config-driven environment definitions (align, equation, gather, cases, split, alignat)
- TOML configuration support with validation
- Function signature: `show_eqn(eqns, environment=None, sep="&", label=None, ..., env_arg=None, **kwargs)`
- Access pattern: `config.environments[env_name]` (dict-like interface)
- Environment arguments support via `env_arg` parameter
- Dict-like `EnvironmentConfig` class with backward compatibility

**✅ Post-Completion Refinements (Implemented 2025-10-01)**:
1. **Flatten TOML structure**: ✅ Removed double-access pattern via dict-like interface
2. **Environment arguments**: ✅ Added `env_arg` parameter for `\begin{alignat}{2}` style environments

### Post-Completion Refinements

#### Flatten TOML Environments Structure (✅ Completed 2025-10-01)

**Issue**: Double-access pattern `config.environments.environments` is awkward
- First `.environments` returns the config section
- Second `.environments` accesses the dict key within that section

**Current TOML Structure**:
```toml
[environments]
environments = {align = "...", equation = "..."}
```

**Proposed Structure**:
```toml
[environments]
align = "..."
equation = "..."
```

**Changes Required**:
1. Update default config structure in [src/keecas/config.py](src/keecas/config.py)
   - Change `EnvironmentConfig` dataclass to store environments dict directly (not nested under `environments` key)
   - Update `to_toml_dict()` serialization: return environments directly, not `{"environments": {...}}`
   - Update `update_from_dict()` deserialization: read from dict root, not `dict.get("environments", {})`
2. Update all code accessing `config.environments.environments`:
   - [src/keecas/display.py](src/keecas/display.py) - Change `config.environments.environments.get()` to `config.environments.get()`
   - [src/keecas/cli.py](src/keecas/cli.py) (if implemented) - Update environment listing/showing
3. Update tests to match new structure:
   - [tests/test_display.py](tests/test_display.py) - Environment access patterns
   - [tests/test_config.py](tests/test_config.py) - TOML serialization tests
4. Update documentation and example config files

**Benefits**:
- Cleaner API: `config.environments['align']` instead of `config.environments.environments['align']`
- More intuitive TOML structure
- Consistent with standard TOML conventions

**Implementation Summary**:
- Added dict-like interface to `EnvironmentConfig` class (`__getitem__`, `__setitem__`, `get`, `keys`, `values`, `items`, `__contains__`, `__iter__`)
- Renamed internal field from `environments` to `_environments`
- Added `environments` property for backward compatibility
- Updated serialization in `to_toml_dict()` to use `.items()`
- Updated deserialization in `update_from_dict()` to use dict-like assignment
- Updated `display.py` to use `config.environments.get()` and `config.environments["align"]`
- Updated tests to use new dict-like interface
- All 95 tests pass

**Status**: ✅ Completed

#### Environment Arguments Support (✅ Completed 2025-10-01)

**Issue**: Some LaTeX environments require arguments (e.g., `\begin{alignat}{2}`, `\begin{tabular}{lr}`)

**Current Limitation**: No way to specify environment arguments

**Proposed Solution**: Add `env_arg` parameter to `show_eqn()`

**Function Signature**:
```python
def show_eqn(eqns, environment=None, sep="&", label=None, env_arg=None, **kwargs):
    """
    Args:
        env_arg: Optional argument string for environments (e.g., "{2}" for alignat)
                 User provides complete argument including braces.
    """
```

**Template Generation Update**:
```python
def _generate_environment_template(environment: str, env_config: dict, label: str | None, env_arg: str | None = None) -> str:
    """Generate complete LaTeX template with ___body___ placeholder.

    Args:
        env_arg: Optional argument string for environment (e.g., "{2}" for alignat{2})
                 User provides complete argument including braces. Defaults to empty string.
    """
    outer_env = env_config["outer_environment"]
    inner_env = env_config.get("inner_environment")

    # Handle starred environments
    if "*" in environment:
        outer_env += "*"

    # Use env_arg directly (already includes braces) or empty string
    arg_str = env_arg if env_arg else ""

    if inner_env is None:
        # Standard: \begin{env}{arg}___body___\end{env}
        outer_prefix = env_config.get("outer_prefix", "")
        outer_suffix = env_config.get("outer_suffix", "")
        label_str = _attach_label(label) if not env_config['supports_multiple_labels'] else ''

        template = rf"{outer_prefix}\begin{{{outer_env}}}{arg_str}{label_str}" + "\n___body___\n" + rf"\end{{{outer_env}}}{outer_suffix}"
    else:
        # Nested: argument goes on inner environment by default
        inner_prefix = env_config.get("inner_prefix", "")
        inner_suffix = env_config.get("inner_suffix", "")
        outer_prefix = env_config.get("outer_prefix", "")
        outer_suffix = env_config.get("outer_suffix", "")
        label_str = _attach_label(label)

        template = rf"""{outer_prefix}\begin{{{outer_env}}}{label_str}
	{inner_prefix}\begin{{{inner_env}}}{arg_str}
___body___
	\end{{{inner_env}}}{inner_suffix}
\end{{{outer_env}}}{outer_suffix}"""

    return template
```

**Example Usage**:
```python
# alignat requires number of column pairs
show_eqn(equations, environment="alignat", env_arg="{2}")
# Produces: \begin{alignat}{2}...\end{alignat}

# Multiple arguments - user provides complete argument string
show_eqn(equations, environment="custom", env_arg="{2}{l}")
# Produces: \begin{custom}{2}{l}...\end{custom}
```

**Note**: Focus is on amsmath environments. Tabular and other non-math environments are outside scope.

**Configuration Support** (optional):
```toml
[environments.alignat]
separator = "&"
line_separator = " \\\\\n "
supports_multiple_labels = true
outer_environment = "alignat"
```

**Changes Required**:
1. Add `env_arg` parameter to `show_eqn()` in [src/keecas/display.py](src/keecas/display.py)
   - Signature: `def show_eqn(eqns, environment=None, sep="&", label=None, env_arg=None, **kwargs):`
2. Update `_generate_environment_template()` to handle argument insertion
   - Add `env_arg` parameter to function signature
   - User provides complete argument string including braces: `"{2}"` or `"{2}{l}"`
   - Insert `arg_str` after `\begin{env}` but before label in standard environments
   - Insert `arg_str` after `\begin{inner_env}` in nested environments
   - Default to empty string when not specified
3. Pass `env_arg` from `show_eqn()` to `_generate_environment_template()`
4. Add tests for environments with arguments:
   - Test alignat with `env_arg="{2}"`
   - Test custom environment with multiple arguments
   - Test nested environments with arguments
5. Update documentation with examples and docstrings

**Benefits**:
- Enables full amsmath environment support
- Simple string-based interface (no parsing needed)
- User controls exact argument format including braces
- Backward compatible (env_arg defaults to None)

**Edge Cases**:
- Nested environments: argument on inner or outer? (Proposal: inner by default)
- Multiple arguments: user provides complete string `"{2}{l}"` with all braces

**Implementation Summary**:
- Added `env_arg` parameter to `show_eqn()` function signature
- Updated `_generate_environment_template()` to accept and use `env_arg` parameter
- Arguments inserted after `\begin{environment_name}` for standard environments
- Arguments inserted after `\begin{inner_environment}` for nested environments
- Added `alignat` environment definition to default config
- Created 3 comprehensive tests:
  - `test_environment_with_argument`: Tests alignat with `{2}` argument
  - `test_environment_with_multiple_arguments`: Tests custom environment with `{2}{l}` arguments
  - `test_nested_environment_with_argument`: Tests argument placement on inner environment
- All 95 tests pass (33 display tests total)

**Status**: ✅ Completed

## Post-Completion Refinements Summary (2025-10-01)

All planned refinements were successfully implemented, with an additional pivot to a cleaner dataclass architecture:

### 1. Flattened TOML Structure + Dataclass Architecture
**Before**: `config.environments.environments["align"]["separator"]`
**After**: `config.environments.align.separator`

**Key Changes**:
- Created `EnvironmentDefinition` dataclass for type-safe environment definitions
- Simplified `EnvironmentConfig` to use direct attribute access (dot notation)
- TOML structure: `[environments.align]` sections
- Setting environments: `config.environments.set("name", dict)` or direct attribute assignment
- Full IDE autocomplete and type checking support

**API Examples**:
```python
# Access
sep = config.environments.align.separator

# Set via dict
config.environments.set("custom", {
    "separator": "&",
    "line_separator": r" \\\n ",
    "supports_multiple_labels": True,
    "outer_environment": "align"
})

# Set via object
config.environments.custom = EnvironmentDefinition(...)
```

### 2. Environment Arguments
**New Feature**: `show_eqn(eqns, environment="alignat", env_arg="{2}")`
**Output**: `\begin{alignat}{2}...\end{alignat}`

**Key Features**:
- User provides complete argument string including braces
- Arguments placed on outer environment for standard environments
- Arguments placed on inner environment for nested environments
- Added `alignat` to built-in environments

### Updated Test Coverage
- **Before refinements**: 92 tests (30 display tests)
- **After refinements**: 95 tests (33 display tests)
- **New tests added**:
  1. `test_environment_with_argument`
  2. `test_environment_with_multiple_arguments`
  3. `test_nested_environment_with_argument`

### Files Modified in Refinements
- [src/keecas/config.py](src/keecas/config.py) - New `EnvironmentDefinition` dataclass, simplified `EnvironmentConfig`, added alignat
- [src/keecas/display.py](src/keecas/display.py) - Added env_arg parameter, updated to use dot notation for environment access
- [tests/test_display.py](tests/test_display.py) - Added 3 new tests, updated test syntax to use `.set()` method

## Insights & Learnings

1. **R-strings are essential**: Using raw strings (`r"\begin{align}"`) improves LaTeX code readability
2. **Template placeholders work well**: The `___body___` placeholder approach is simple and effective
3. **Config validation is important**: Field validation catches user typos early
4. **Backward compatibility achieved**: All work maintains backward compatibility - existing code works unchanged
5. **Test coverage critical**: 33 tests (including 3 new) ensure all environment types and features work correctly
6. **Dataclasses over magic methods**: Direct attribute access via dataclasses is simpler and more Pythonic than dict-like interfaces
7. **User-controlled formatting**: Letting users provide complete argument strings (with braces) eliminates edge cases
8. **Dot notation superiority**: `config.environments.align.separator` is more intuitive than dict access and provides IDE autocomplete


## Additional Refinements (Pending)

### 1. Inline Environment Definitions
**Goal**: Allow passing environment definitions directly to `show_eqn()`

**Current**:
```python
show_eqn(equations, environment="align")
```

**Proposed (in addition to current)**:
```python
# Pass dict
show_eqn(equations, environment={
    "separator": "&",
    "line_separator": r" \\\n ",
    "supports_multiple_labels": True,
    "outer_environment": "align"
})

# Pass EnvironmentDefinition object
custom_env = EnvironmentDefinition(separator="&", ...)
show_eqn(equations, environment=custom_env)
```

**Implementation**:
- Update `show_eqn()` to detect dict/EnvironmentDefinition in `environment` parameter
- Skip config lookup if inline definition provided
- Validate inline definitions using same logic as config loading

**Benefits**:
- One-off custom environments without config changes
- Quick experimentation
- Cleaner for programmatic environment generation

---

### 2. Relocate Environments to LaTeX Config
**Goal**: Move `environments` under `latex` config section for better organization

**Current**: `config.environments.align`
**Proposed**: `config.latex.environments.align`

**Rationale**: Environments are LaTeX-specific, should be grouped with other LaTeX settings

**Changes Required**:
1. Move `EnvironmentConfig` from `ConfigOptions` to `LatexConfig`
2. Update TOML structure: `[latex.environments.align]`
3. Update all code references: `config.environments` → `config.latex.environments`
4. Update tests and documentation

**TOML Structure**:
```toml
[latex]
eq_prefix = "eq-"
default_environment = "align"
default_mul_symbol = "\\,"

[latex.environments.align]
separator = "&"
line_separator = " \\\\\n "
supports_multiple_labels = true
outer_environment = "align"
```

---

### 3. Move `default_mul_symbol` to LatexConfig
**Goal**: Relocate `default_mul_symbol` from `DisplayConfig` to `LatexConfig`

**Current**: `config.default_mul_symbol` (from DisplayConfig)
**Proposed**: `config.latex.default_mul_symbol`

**Rationale**: Multiplication symbol is LaTeX-specific formatting, not display behavior

**Changes**:
- Move field definition to `LatexConfig` class
- Update references in `show_eqn()` and other code
- Update backward compatibility properties if needed

---

### 4. Document Built-in Environments in Config
**Goal**: Provide template/documentation in default config file

**Proposed TOML Section**:
```toml
# Built-in environments: align, equation, gather, cases, split, alignat
# Uncomment and modify to customize:

# [latex.environments.custom_align]
# separator = "&"
# line_separator = " \\\\[0.5em]\n "
# supports_multiple_labels = true
# outer_environment = "align"

# [latex.environments.boxed_equation]
# separator = ""
# line_separator = ""
# supports_multiple_labels = false
# outer_environment = "equation"
# outer_prefix = "\\boxed{"
# outer_suffix = "}"
```

**Implementation**:
- Add commented example section to default config template
- Document all field meanings
- List built-in environment names

---

## Implementation Plan for Additional Refinements

### Task 1: Inline Environment Definitions
1. Update `show_eqn()` signature type hint: `environment: str | dict | EnvironmentDefinition | None`
2. Add type detection logic at start of function
3. Convert dict to `EnvironmentDefinition` if needed
4. Add validation for inline definitions
5. Add tests for inline dict and object usage

### Task 2: Relocate to LaTeX Config
1. Move `EnvironmentConfig` instantiation from `ConfigOptions` to `LatexConfig`
2. Update TOML serialization/deserialization
3. Update all `config.environments` → `config.latex.environments`
4. Update tests
5. Update documentation (CLAUDE.md, task docs)

### Task 3: Move default_mul_symbol
1. Add field to `LatexConfig`: `default_mul_symbol: str = r"\,"`
2. Remove from `DisplayConfig`
3. Update references: `config.default_mul_symbol` → `config.latex.default_mul_symbol`
4. Add backward compatibility property if needed
5. Update tests

### Task 4: Config Documentation
1. Create example config section with commented examples
2. Add field descriptions
3. List built-in environments
4. Update `keecas config init` to include examples

**Total Effort**: ~1 day

**Status**: ✅ All Completed (v2.0 - Breaking Changes)

---

## Final Implementation Summary (v2.0)

### Completed Features

✅ **Original Task**: LaTeX Environment Templating System
- Template-based environment generation with `_generate_environment_template()`
- Config-driven definitions (align, equation, gather, cases, split, alignat)
- TOML configuration with validation
- All hardcoded environment logic replaced

✅ **Refinement 1**: Inline Environment Definitions
- Pass dict or `EnvironmentDefinition` directly to `show_eqn()`
- Example: `show_eqn(eqns, environment={...})`
- 3 new tests added

✅ **Refinement 2**: Relocate to LaTeX Config
- Moved from `config.environments` → `config.latex.environments`
- TOML: `[latex.environments.align]` sections
- Better organization of LaTeX-specific settings

✅ **Refinement 3**: Move default_mul_symbol
- Relocated from `DisplayConfig` → `LatexConfig`
- Clean grouping of LaTeX formatting options

✅ **Code Cleanup**: Removed All Backward Compatibility
- No legacy properties or migration code
- Clean v2.0 API ready for major release
- -101 lines of compatibility cruft removed

### Breaking Changes (v2.0)

**Migration Guide**:
```python
# Old v1.x API
config.EQ_PREFIX                    # ❌
config.DEBUG                        # ❌
config.katex                        # ❌
config.default_mul_symbol           # ❌
config.default_environment          # ❌
config.environments.align           # ❌

# New v2.0 API
config.latex.eq_prefix              # ✅
config.display.debug                # ✅
config.display.katex                # ✅
config.latex.default_mul_symbol     # ✅
config.latex.default_environment    # ✅
config.latex.environments.align     # ✅
```

### Test Coverage
- **Total Tests**: 98 (all passing)
- **Display Tests**: 36 (including 3 new inline environment tests)
- **New Test Coverage**: Inline dict, inline object, inline with prefixes

### Documentation Updates
- ✅ CLAUDE.md: Updated API examples and access patterns
- ✅ Task docs: Complete implementation history
- ✅ Code comments: Inline environment support documented

### Commits
1. `fefe676` - feat: Implement LaTeX environment templating system
2. `67c6f1e` - docs: Update and cleanup
3. `ee040b0` - refactor: Pivot environment config to dataclass with dot notation
4. `3a6f9a2` - feat: Add inline environments and relocate to latex config
5. `3ffb2ff` - refactor!: Remove backward compatibility for clean v2.0 API

**Branch**: `feature/latex-environment-templating`
**Ready for**: Pull request to `main` branch