# LaTeX Environment Templating System - Implementation

**Status**: Active Development
**Branch**: `feature/latex-environment-templating`
**Started**: 2025-09-30

## Original Objective (from show_eqn refactor)

Convert hardcoded environment logic in `show_eqn` to a configurable templating system that allows users to define custom LaTeX environments.

## Current Implementation Analysis

### Existing Patterns in [src/keecas/display.py](src/keecas/display.py)

The current code already uses several template-like patterns:

**1. Wrap Tuple Pattern** (lines 338-362):
```python
# Special environments get wrapped
wrap = (prefix, begin_template, end_template, suffix)

# Standard environments
wrap = ("", f"\\begin{{{environment}}}", f"\\end{{{environment}}}", "")
```

**2. Template Substitution** (line 365):
```python
template = f"{wrap[0]}{wrap[1]}\n___body___{wrap[2]}{wrap[3]}"
template = template.replace("___body___", body)
```

**3. Environment-Specific Logic**:
```python
single_label_env = ["equation", "cases", "split"]           # line 235
if environment.replace("*", "") in ["equation", "gather"]:  # line 242
    sep = ""  # no separator
join_token = "" if "equation" in environment else " \\\\\n " # line 387
```

### Existing Template Infrastructure

Keecas already has sophisticated template support:
- **Configuration System**: TOML-based with hierarchical loading ([src/keecas/config.py](src/keecas/config.py))
- **Check Templates**: Named template sets with overrides ([src/keecas/config.py:70-88](src/keecas/config.py#L70))
- **Dynamic Propagation**: Configuration changes automatically update subsystems

## Revised Proposal: Build on Existing Patterns

### Core Concept: Environment Configuration

Instead of complex template classes, extend the existing configuration system with environment-specific settings.

### 1. Environment Configuration Structure

Add to [src/keecas/config.py](src/keecas/config.py):

<!-- prefer the use of r-string for latex bit of string, so backslashes will be more human readable -->

```python
@dataclass
class EnvironmentConfig:
    """LaTeX environment behavior configuration."""
    # Built-in environments as direct dictionary - no wrapper classes
    environments: dict[str, dict[str, Any]] = field(default_factory=lambda: {
        # Standard align environment
        "align": {
            "separator": "&",
            "line_separator": r" \\\n ",
            "supports_multiple_labels": True,
            "outer_environment": "align",
            "inner_environment": None  # No inner wrapper
        },

        # Standard equation environment
        "equation": {
            "separator": "",
            "line_separator": "",
            "supports_multiple_labels": False,
            "outer_environment": "equation",
            "inner_environment": None
        },

        # Standard gather environment
        "gather": {
            "separator": "",
            "line_separator": r" \\\n ",
            "supports_multiple_labels": True,
            "outer_environment": "gather",
            "inner_environment": None
        },

        # Special cases environment - different from amsmath cases!
        # This creates: \begin{align}\left\{\begin{aligned}...\end{aligned}\right.\end{align}
        "cases": {
            "separator": "&",
            "line_separator": r" \\\n ",
            "supports_multiple_labels": False,
            "outer_environment": "align",  # Can be align or align*
            "inner_environment": "aligned",
            "inner_prefix": r"\left\{",
            "inner_suffix": r"\right.",
            "label_position": "outer"  # Label goes on outer environment
        },

        # Split environment - similar special handling
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

### Environment Configuration Examples

Each environment uses `outer_environment` and `inner_environment` to define structure:

**Standard environments** (align, equation, gather):
```python
"align": {
    "separator": "&",
    "line_separator": r" \\\n ",
    "supports_multiple_labels": True,
    "outer_environment": "align",
    "inner_environment": None  # No inner wrapper - simple \begin{align}...\end{align}
}
```

**Nested environments** (cases, split):
```python
"cases": {
    "separator": "&",
    "line_separator": r" \\\n ",
    "supports_multiple_labels": False,
    "outer_environment": "align",     # \begin{align}
    "inner_environment": "aligned",   # \begin{aligned}
    "inner_prefix": r"\left\{",       # Before inner environment
    "inner_suffix": r"\right.",       # After inner environment
    "outer_prefix": "",               # Before outer environment (optional)
    "outer_suffix": "",               # After outer environment (optional)
    "label_position": "outer"
}
```

This produces LaTeX structure:
```latex
\begin{align}\label{eq-label}
\left\{\begin{aligned}
    x &= 1 \\
    y &= 2
\end{aligned}\right.
\end{align}
```

### 2. Configuration Integration

Add to `ConfigOptions` class:
```python
@dataclass
class ConfigOptions:
    # ... existing fields ...
    environments: EnvironmentConfig = field(default_factory=EnvironmentConfig)
```

### 3. TOML Configuration Support

Enable user configuration in `.keecas/config.toml`:

```toml
[environments]
# Override built-in environment
[environments.align]
separator = "&"
line_separator = " \\\\\n "

# Define custom environment
[environments.custom_align]
separator = "&"
line_separator = " \\\\[0.5em]\n "
supports_multiple_labels = true

# Complex custom environment
[environments.boxed_equation]
separator = ""
line_separator = ""
supports_multiple_labels = false
prefix = "\\boxed{"
suffix = "}"
```

### 4. Simplified Function Signature (Breaking Change)

Since backward compatibility isn't required, we can clean up the function:

**Current signature** (complex with many optional parameters):
```python
def show_eqn(
    eqns: dict[Basic, Any] | list[dict[Basic, Any]] | Dataframe,
    environment: str | None = None,
    sep: str | list[str] = "&",
    label: str | dict[str, str] | None = None,
    label_command: str | None = None,
    col_wrap: list[None | tuple[str, str]] | None = None,
    float_format: str | None = None,
    debug: bool | None = None,
    **kwargs: Any,
) -> Markdown:
```

**Keep current signature** (only minor parameters would move to config):

Since only `sep` and `label_command` would be handled by environment config, it's not worth breaking the signature. Keep the existing function signature and add environment configuration as internal implementation detail.

```python
def show_eqn(
    eqns: dict[Basic, Any] | list[dict[Basic, Any]] | Dataframe,
    environment: str | None = None,
    sep: str | list[str] = "&",
    label: str | dict[str, str] | None = None,
    label_command: str | None = None,
    col_wrap: list[None | tuple[str, str]] | None = None,
    float_format: str | None = None,
    debug: bool | None = None,
    **kwargs: Any,
) -> Markdown:
    """
    Generate LaTeX equations with configurable environments.

    Environment configuration from .keecas/config.toml provides defaults
    for separator and behavior, but can still be overridden by parameters.
    """
```

**Implementation with direct environment dictionary lookup**:

```python
def show_eqn(eqns, environment=None, sep="&", label=None, **kwargs):
    # Get environment configuration - direct dictionary access
    if not environment:
        environment = config.default_environment

    env_config = config.environments.environments.get(environment)
    if not env_config:
        warn(f"Unknown environment '{environment}', using 'align'")
        env_config = config.environments.environments["align"]

    # Use environment config for separator if not explicitly provided
    if sep == "&":  # Default value, use config
        sep = env_config["separator"]

    # Generate wrap based on environment structure
    wrap = _generate_environment_wrap(environment, env_config, label)

    # Rest of existing logic uses wrap tuple...
```

**Simplified wrap generation**:

```python
def _generate_environment_wrap(environment, env_config, label):
    """Generate wrap tuple based on environment configuration."""
    outer_env = env_config["outer_environment"]
    inner_env = env_config.get("inner_environment")

    # Handle starred environments
    if "*" in environment:
        outer_env += "*"

    if inner_env is None:
        # Standard environment: simple \begin{env}...\end{env}
        return (
            env_config.get("outer_prefix", ""),
            f"\\begin{{{outer_env}}}{_attach_label(label) if not env_config['supports_multiple_labels'] else ''}",
            f"\\end{{{outer_env}}}",
            env_config.get("outer_suffix", "")
        )
    else:
        # Nested environment: \begin{outer}\prefix\begin{inner}...\end{inner}\suffix\end{outer}
        inner_prefix = env_config.get("inner_prefix", "")
        inner_suffix = env_config.get("inner_suffix", "")
        outer_prefix = env_config.get("outer_prefix", "")
        outer_suffix = env_config.get("outer_suffix", "")

        return (
            f"{outer_prefix}\\begin{{{outer_env}}}{_attach_label(label)}\\n",
            f"\\t{inner_prefix}\\begin{{{inner_env}}}",
            f"\\t\\n\\end{{{inner_env}}}{inner_suffix}",
            f"\\n\\end{{{outer_env}}}{outer_suffix}"
        )
```

## Implementation Plan

### Phase 1: Core Configuration (1 day)
1. **Add EnvironmentConfig dataclass** to [src/keecas/config.py](src/keecas/config.py)
2. **Update TOML serialization** to include environment settings
3. **Add built-in environment definitions** based on current hardcoded logic
4. **Add tests** for configuration loading and environment definitions

### Phase 2: Refactor show_eqn (1 day)
5. **Extract configuration lookup function** to get environment settings
6. **Replace hardcoded conditionals** with configuration-based logic
7. **Maintain backward compatibility** - all existing behavior unchanged
8. **Add tests** for environment-specific behavior

### Phase 3: Custom Environments (0.5 days)
9. **Enable user-defined environments** via TOML configuration
10. **Add configuration validation** for custom environments
11. **Update CLI** to show available environments
12. **Add examples** for common custom environments

## Benefits of This Approach

### 1. **Builds on Existing Patterns**
- Uses established configuration system
- Follows same patterns as `check` templates
- Maintains current `wrap` tuple approach

### 2. **Minimal Disruption**
- No changes to function signatures
- All existing code continues to work
- No new dependencies required

### 3. **User-Friendly Configuration**
- TOML configuration like existing features
- Hierarchical inheritance (global → local → inline)
- Same CLI commands for management

### 4. **Maintainable Implementation**
- Concentrates environment logic in configuration
- Clear separation between behavior and presentation
- Easy to test and debug

## Example Usage

### Before (current)
```python
# Limited to hardcoded environments
show_eqn(equations, environment="align")
show_eqn(equations, environment="gather")
# No customization possible
```

### After (with configuration)
```python
# Use built-in environments (same as before)
show_eqn(equations, environment="align")

# Use custom environment from config
show_eqn(equations, environment="spaced_align")

# Override inline (new capability)
custom_env = {"separator": "&", "line_separator": " \\\\[1em]\n "}
show_eqn(equations, environment="align", env_override=custom_env)
```

### Configuration Management
```bash
# Edit environment configurations
keecas config edit --local

# Show available environments
keecas config show environments

# Validate environment definitions
keecas config validate
```

## Breaking Changes - Embracing Simplification

Since this is part of a major update, we can make breaking changes that improve the design:

### Configuration Structure Changes
- **Direct dictionary access**: No wrapper classes between config and environment definitions
- **Environment-based logic**: Use `outer_environment`/`inner_environment` instead of `wrap_style`
- **Clear prefix/suffix naming**: `outer_prefix`, `outer_suffix`, `inner_prefix`, `inner_suffix`
- **Maintained function signature**: No breaking changes to `show_eqn` parameters

### Improvements Made:
1. **Consistent environment logic**: All environment-specific behavior in configuration
2. **Better error messages**: Clear feedback when environment doesn't exist
3. **Easier testing**: Each environment type isolated and configurable
4. **User customization**: Custom environments via TOML configuration

## Comparison with Original Proposal

### Original Proposal Issues:
- **Over-engineered**: Complex dataclasses and Jinja2 integration
- **Foreign patterns**: Didn't leverage existing configuration system
- **High complexity**: 6 days estimated implementation time
- **Breaking changes**: Would require significant refactoring

### Revised Proposal Benefits:
- **Leverages existing patterns**: Builds on current configuration system
- **Minimal complexity**: Simple dictionary-based configuration
- **Faster implementation**: 2.5 days estimated vs 6 days
- **Non-breaking**: Zero impact on existing code

## Timeline Estimate

- **Phase 1**: 1 day (configuration structure)
- **Phase 2**: 1 day (show_eqn refactoring)
- **Phase 3**: 0.5 days (custom environments)

**Total**: ~2.5 days vs 6 days in original proposal

## Questions for Review - Answered

### 1. Configuration Complexity ✅
**Answer**: Dictionary-based config is good and simple. We like simple.

### 2. Environment Validation
**How to validate**: Basic structural validation at config load time:
- Check required fields exist (`separator`, `line_separator`, `outer_environment`)
- Warn about unknown fields (catch typos like `seprator`)
- For nested environments: ensure `inner_environment` is valid when specified
- Validate prefix/suffix fields are strings when present

**No LaTeX syntax validation** - LaTeX compiler handles that. If user writes `prefix: "\\invalid{"`, LaTeX will error appropriately.

### 3. CLI Integration - Subtask Proposal

Add environment-specific CLI commands:

```bash
# List available environments
keecas config environments list

# Show specific environment definition
keecas config environments show align

# Create custom environment from template
keecas config environments create my_custom --from align --separator "&"

# Validate all environment definitions
keecas config environments validate
```

<!-- we're not using click for the cli at the moment -->

Implementation in [src/keecas/cli.py](src/keecas/cli.py) (using argparse, not click):
```python
def handle_config_environments(args):
    """Handle environment-specific config commands."""
    config_manager = get_config_manager()

    if args.action == "list":
        environments = config_manager.options.environments.environments
        for name in environments.keys():
            print(f"  {name}")

    elif args.action == "show":
        if not args.name:
            print("Error: environment name required for 'show'")
            return
        env_config = config_manager.options.environments.environments.get(args.name)
        if env_config:
            print(f"Environment '{args.name}':")
            for key, value in env_config.items():
                print(f"  {key}: {value}")
        else:
            print(f"Unknown environment: {args.name}")

    # Additional actions: create, validate...
```

### 4. Migration Path
**Current limitation**: Users can only choose built-in environments (`align`, `equation`, `gather`, `cases`, `split`).

**Migration needed**: Documentation showing how current hardcoded behavior maps to new config:

```python
# Before: hardcoded parameters
show_eqn(eqns, environment="align", sep="&", label_command=r"\label")

# After: environment config handles this
show_eqn(eqns, environment="align", label="my-label")

# Custom behavior that was impossible before
show_eqn(eqns, environment="spaced_align")  # From .keecas/config.toml
```

**No conversion tools needed** - current usage patterns are simple enough to update manually.

This revised approach is more pragmatic, builds on existing patterns, and delivers the same extensibility with significantly less complexity.