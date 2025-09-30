# LaTeX Environment Templating System

**Status**: ✅ Completed
**Branch**: `feature/latex-environment-templating`
**Started**: 2025-09-30
**Completed**: 2025-10-01

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
- **Preamble support**: TODO - handle `\begin{aligned}{2}` style preambles

### 2. Configuration Integration

Add to `ConfigOptions` class:
```python
@dataclass
class ConfigOptions:
    # ... existing fields ...
    environments: EnvironmentConfig = field(default_factory=EnvironmentConfig)
```

### 3. TOML User Configuration

Example `.keecas/config.toml`:
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
def _generate_environment_template(environment: str, env_config: dict, label: str | None) -> str:
    """Generate complete LaTeX template with ___body___ placeholder."""
    outer_env = env_config["outer_environment"]
    inner_env = env_config.get("inner_environment")

    # Handle starred environments
    if "*" in environment:
        outer_env += "*"

    if inner_env is None:
        # Standard: \begin{env}___body___\end{env}
        outer_prefix = env_config.get("outer_prefix", "")
        outer_suffix = env_config.get("outer_suffix", "")
        label_str = _attach_label(label) if not env_config['supports_multiple_labels'] else ''

        template = rf"{outer_prefix}\begin{{{outer_env}}}{label_str}" + "\n___body___\n" + rf"\end{{{outer_env}}}{outer_suffix}"
    else:
        # Nested: \begin{outer}\n\t\prefix\begin{inner}___body___\end{inner}\suffix\n\end{outer}
        inner_prefix = env_config.get("inner_prefix", "")
        inner_suffix = env_config.get("inner_suffix", "")
        outer_prefix = env_config.get("outer_prefix", "")
        outer_suffix = env_config.get("outer_suffix", "")
        label_str = _attach_label(label)

        template = rf"""{outer_prefix}\begin{{{outer_env}}}{label_str}
	{inner_prefix}\begin{{{inner_env}}}
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
def show_eqn(eqns, environment=None, sep="&", label=None, **kwargs):
    # Get environment configuration
    if not environment:
        environment = config.default_environment

    env_config = config.environments.environments.get(environment)
    if not env_config:
        warn(f"Unknown environment '{environment}', using 'align'")
        env_config = config.environments.environments["align"]

    # Use config separator if not explicitly overridden
    if sep == "&":  # Default parameter value
        sep = env_config["separator"]

    # Generate template
    template = _generate_environment_template(environment, env_config, label)

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
        for name in config_manager.options.environments.environments.keys():
            print(f"  {name}")

    elif args.action == "show":
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
- No function signature changes (backward compatible)
- Simple dictionary-based implementation
- Enables user customization via `.keecas/config.toml`
- Concentrates environment logic in configuration

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
3. **Backward Compatible**: No breaking changes - all existing code works unchanged
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

### Future Enhancements (Not in Scope)

- Preamble support for environments like `\begin{aligned}{2}`
- CLI commands for environment management (`keecas config environments list/show`)
- Additional built-in environments (e.g., multline, flalign)

## Insights & Learnings

1. **R-strings are essential**: Using raw strings (`r"\begin{align}"`) improves LaTeX code readability
2. **Template placeholders work well**: The `___body___` placeholder approach is simple and effective
3. **Config validation is important**: Field validation catches user typos early
4. **Backward compatibility achieved**: No changes to function signatures needed
5. **Test coverage critical**: 10 tests ensured all environment types work correctly
