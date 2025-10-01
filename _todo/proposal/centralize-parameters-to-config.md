# Centralize Parameters to Config

## Original Objective (from show_eqn refactor)

Analyze the `show_eqn` function for parameters that could be set in the config file.

## Analysis of Current `show_eqn` Function

### Current Function Signature
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

### Parameters That Could Be Moved to Config

#### 1. **Environment Defaults**
- **Current**: `environment: str | None = None` (defaults to `config.default_environment`)
- **Config opportunity**: Already handled correctly

#### 2. **Separator Defaults**
- **Current**: `sep: str | list[str] = "&"`
- **Config opportunity**: `default_separator = "&"` - different equation environments might benefit from different default separators

#### 3. **Label Command Defaults**
- **Current**: `label_command: str | None = None` (defaults to `config.default_label_command`)
- **Config opportunity**: Already handled correctly

#### 4. **Column Wrapping Defaults**
- **Current**: `col_wrap: list[None | tuple[str, str]] | None = None`
- **Config opportunity**: `default_col_wrap = [None, ('=', '')]` - users often want consistent column wrapping

#### 5. **Float Formatting Defaults**
- **Current**: `float_format: str | None = None`
- **Config opportunity**: `default_float_format = None` - users might want consistent float formatting across documents

#### 6. **Debug Mode Defaults**
- **Current**: `debug: bool | None = None` (defaults to `config.debug`)
- **Config opportunity**: Already handled correctly

#### 7. **Hidden Parameters in Code**
Looking at the implementation, there are several hardcoded values that could be configurable:

```python
# Line ~310 in show_eqn implementation
if col_wrap is None:
    col_wrap = [None, ("=", "")]  # Hardcoded default

# Various environment-specific separators
environments_no_sep = ["equation", "gather", "multline"]  # Hardcoded list
```

## Proposed Configuration Additions

### New Config Structure

```python
@dataclass
class DisplayDefaults:
    """Default values for show_eqn function parameters."""
    separator: str = "&"
    column_wrapping: list[None | tuple[str, str]] = field(default_factory=lambda: [None, ("=", "")])
    float_format: str | None = None
    environments_without_separator: list[str] = field(default_factory=lambda: ["equation", "gather", "multline"])

    # Environment-specific separator overrides
    separator_overrides: dict[str, str] = field(default_factory=dict)

    # Default column wrapping for different contexts
    col_wrap_presets: dict[str, list[None | tuple[str, str]]] = field(default_factory=lambda: {
        "default": [None, ("=", "")],
        "no_equals": [None, None],
        "explicit": [("=", ""), ("=", "")]
    })
```

### TOML Configuration Example

```toml
# .keecas/config.toml
[display_defaults]
separator = "&"
float_format = ".3f"
environments_without_separator = ["equation", "gather", "multline"]

[display_defaults.separator_overrides]
align = "&"
alignat = "&"
gather = ""

[display_defaults.col_wrap_presets]
default = [[null, ["=", ""]]]
no_equals = [[null, null]]
explicit = [["=", ""], ["=", ""]]
```

## Implementation Plan

### Phase 1: Config Structure Enhancement
1. **Extend configuration dataclass**
   - Add `DisplayDefaults` dataclass to config system
   - Implement proper field factories for mutable defaults
   - Add validation for separator overrides

2. **Update config loading**
   - Extend TOML parsing for new display_defaults section
   - Add validation for list and dict fields
   - Implement proper default value handling

### Phase 2: Function Parameter Refactoring
3. **Update show_eqn signature**
   - Keep existing parameters for backward compatibility
   - Add parameter precedence: explicit args > config > hardcoded defaults

4. **Implement parameter resolution logic**
   ```python
   def _resolve_show_eqn_params(
       environment: str | None,
       sep: str | list[str] | None,
       col_wrap: list[None | tuple[str, str]] | None,
       float_format: str | None,
       **kwargs
   ) -> ResolvedParams:
       """Resolve parameters using config defaults and explicit overrides."""
   ```

### Phase 3: Environment-Specific Logic
5. **Implement separator logic**
   - Use config for environment-specific separator rules
   - Allow per-environment separator overrides
   - Maintain backward compatibility

6. **Column wrapping presets**
   - Implement named column wrapping presets
   - Allow users to define custom presets in config
   - Add preset parameter to function signature

### Phase 4: Testing and Documentation
7. **Comprehensive testing**
   - Test parameter precedence (explicit > config > default)
   - Test all new configuration options
   - Ensure backward compatibility

8. **Update documentation**
   - Document new configuration options
   - Provide examples of common configurations
   - Update function docstrings

## Benefits

### 1. **User Experience**
- Consistent formatting across documents without repetitive parameters
- Easy global changes via config file updates
- Reduced boilerplate in notebook cells

### 2. **Flexibility**
- Environment-specific defaults for different LaTeX contexts
- Named presets for common formatting patterns
- Per-project configuration customization

### 3. **Maintainability**
- Centralized default values instead of scattered hardcoded constants
- Clear separation between user preferences and function logic
- Easier testing with configurable defaults

## Backward Compatibility

**Guarantee**: All existing code will continue to work without changes
- Function signature remains the same
- Default behavior preserved when no config is set
- Explicit parameters always override config values

## Configuration Precedence

1. **Explicit function parameters** (highest priority)
2. **Local project config** (`.keecas/config.toml`)
3. **Global user config** (`~/.keecas/config.toml`)
4. **Hardcoded defaults** (lowest priority)

## Example Usage

### Before (current)
```python
# User needs to specify col_wrap in every cell
show_eqn(equations, col_wrap=[None, ("=", "")])
show_eqn(more_equations, col_wrap=[None, ("=", "")])
```

### After (with config)
```toml
# .keecas/config.toml
[display_defaults]
col_wrap_preset = "default"
separator = "&"
```

```python
# Clean notebook cells
show_eqn(equations)  # Uses config defaults
show_eqn(more_equations, col_wrap=[None, None])  # Override when needed
```

## Timeline Estimate

- **Phase 1**: 1 day (config structure)
- **Phase 2**: 1 day (parameter refactoring)
- **Phase 3**: 1 day (environment logic)
- **Phase 4**: 1 day (testing and docs)

**Total**: ~4 days of development work

## Questions for User Review

1. **Scope**: Which parameters are most important to make configurable?
2. **Presets**: Should we include more built-in column wrapping presets?
3. **Environment logic**: Any specific environment-separator combinations to prioritize?
4. **Migration**: Should we provide tools to help users migrate from explicit parameters to config?

Awaiting user approval to proceed with implementation.