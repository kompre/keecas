# Task Proposal: Eliminate Configuration Property Shortcuts

## Original Objective

Fix inconsistent configuration access patterns by eliminating all property shortcuts and enforcing a single, predictable dot-notation access pattern that matches the TOML structure.

## Problem Statement

The current configuration system has three inconsistent patterns:

**1. Settings with Python shortcuts (3 total)**:
- `config.language` → `config.language_config.language`
- `config.pint_default_format` → `config.display.pint_default_format`
- `config.disable_pint_locale` → `config.language_config.disable_pint_locale`

**2. Settings without shortcuts (majority)**:
- Must use full path: `config.display.katex`, `config.latex.eq_prefix`, etc.

**3. TOML structure (always nested)**:
- No top-level shortcuts in TOML files
- All settings under `[latex]`, `[display]`, `[language]`, etc.

This creates confusion:
- Users must memorize which settings have shortcuts
- Documentation must explain two access patterns
- TOML structure doesn't match Python API for shortcuts
- Inconsistent mental model

## Proposed Solution

**Eliminate all property shortcuts** and enforce consistent dot-notation access matching TOML structure.

### Access Pattern Changes

| Current (Mixed) | New (Consistent) |
|-----------------|------------------|
| `config.language` | `config.language.language` |
| `config.pint_default_format` | `config.display.pint_default_format` |
| `config.disable_pint_locale` | `config.language.disable_pint_locale` |
| `config.display.katex` | `config.display.katex` (unchanged) |
| `config.latex.eq_prefix` | `config.latex.eq_prefix` (unchanged) |

**Rationale**: Python access now mirrors TOML structure exactly.

### Benefits

1. **Single mental model**: TOML structure = Python structure
2. **Predictable**: If you know TOML path, you know Python path
3. **Self-documenting**: `config.display.katex` tells you it's in `[display]` section
4. **Easier maintenance**: No duplicate property definitions
5. **Cleaner code**: Remove ~30 lines of property boilerplate

## Implementation Plan

### Step 1: Remove Property Shortcuts from ConfigOptions

**File**: `src/keecas/config/manager.py`

Remove these property definitions (lines 328-360):

```python
# DELETE: Backward compatibility property for options.language
@property
def language(self) -> str | None:
    return self.language_setting

@language.setter
def language(self, value: str | None):
    self.language_setting = value

# DELETE: Backward compatibility shortcuts
@property
def pint_default_format(self) -> str:
    return self.display.pint_default_format

@pint_default_format.setter
def pint_default_format(self, value: str):
    self.display.pint_default_format = value

@property
def disable_pint_locale(self) -> bool:
    return self.language_config.disable_pint_locale

@disable_pint_locale.setter
def disable_pint_locale(self, value: bool):
    self.language_config.disable_pint_locale = value
```

### Step 2: Rename language_config to language

**File**: `src/keecas/config/manager.py` (line 304)

```python
# OLD
language_config: LanguageConfig = field(default_factory=LanguageConfig)

# NEW
language: LanguageConfig = field(default_factory=LanguageConfig)
```

Update all references:
- `self.language_config` → `self.language` throughout ConfigOptions class
- Update `__post_init__` method (line 311)
- Update `to_toml_dict` method (line 391-403)
- Update `update_from_dict` method (line 427-440)

### Step 3: Update Propagation Mechanism

**File**: `src/keecas/config/manager.py`

The language setter needs to trigger propagation. Move this into LanguageConfig:

```python
@dataclass
class LanguageConfig:
    """Language and localization configuration."""

    _language: str | None = field(default=None, init=False)
    disable_pint_locale: bool = True
    pint_language_mode: str = "auto"
    _config_manager_ref: Any = field(default=None, init=False, repr=False)

    @property
    def language(self) -> str | None:
        """Document-level language override."""
        return self._language

    @language.setter
    def language(self, value: str | None):
        """Set language and trigger propagation."""
        self._language = value
        if self._config_manager_ref:
            self._config_manager_ref._propagate_changes("language", value)
```

### Step 4: Update Tests

**Files**: `tests/test_config*.py`

Search and replace all test assertions:
- `config.language` → `config.language.language`
- `config.pint_default_format` → `config.display.pint_default_format`
- `config.disable_pint_locale` → `config.language.disable_pint_locale`

### Step 5: Update Documentation

**Files**: All documentation files already reviewed in Phase 1

Update all code examples:
- `docs/getting-started/configuration.qmd` (just fixed this!)
- `docs/getting-started/quickstart.qmd`
- `docs/index.qmd`
- Any other docs with config examples

**Note**: Most docs are already correct since we just fixed them to use full paths!

### Step 6: Update Examples

**Files**: `examples/**/*.ipynb`

Update any config usage in example notebooks.

### Step 7: Update CLAUDE.md

Document the single access pattern:

```markdown
## Configuration Access Pattern

All configuration uses dot notation matching TOML structure:

```python
# Language settings
config.language.language = 'it'
config.language.disable_pint_locale = True

# Display settings
config.display.katex = True
config.display.print_label = False
config.display.default_float_format = '.3f'
config.display.pint_default_format = '.2f~P'

# LaTeX settings
config.latex.eq_prefix = 'eq-'
config.latex.eq_suffix = ''
config.latex.default_environment = 'align'
```

**Rule**: Python path always matches TOML section path.


## Breaking Changes

**For Beta Users** (if any):

| Old Code | New Code | Fix |
|----------|----------|-----|
| `config.language = 'it'` | `config.language.language = 'it'` | Add extra `.language` |
| `config.pint_default_format = '.3f~P'` | `config.display.pint_default_format = '.3f~P'` | Use full path |
| `config.disable_pint_locale = True` | `config.language.disable_pint_locale = True` | Use full path |

**Migration**: Since v1.0.0 hasn't been officially released, no migration needed. Just fix and document.

## Testing Strategy

1. **Unit Tests**:
   - Test all configuration access paths
   - Test propagation still works (language changes update Pint)
   - Test TOML serialization/deserialization
   - Test config file loading

2. **Integration Tests**:
   - Test actual usage in notebooks
   - Test `keecas config init` generates correct structure
   - Test `keecas config show` displays correctly

3. **Documentation Tests**:
   - Run all code examples from docs
   - Verify no shortcuts remain in examples

## Files to Modify

1. **Core Config Module** (3 files):
   - `src/keecas/config/manager.py` - Remove properties, rename language_config
   - `src/keecas/config/__init__.py` - Update exports if needed
   - `src/keecas/config/schema.py` - No changes needed

2. **Tests** (estimate 5-8 files):
   - `tests/test_config*.py` - Update all assertions
   - `tests/test_display*.py` - Update config usage
   - `tests/test_localization*.py` - Update config usage

3. **Documentation** (5 files - already mostly fixed):
   - `docs/getting-started/configuration.qmd` - Update remaining `config.language` refs
   - `docs/getting-started/quickstart.qmd` - Already fixed
   - `docs/index.qmd` - Check for any shortcuts
   - `CLAUDE.md` - Update configuration section
   - `README.md` - Check for any shortcuts

4. **Examples** (check all .ipynb files):
   - `examples/hello_world.ipynb`
   - `examples/quarto_example/quarto_example.ipynb`
   - Any other examples

## Risk Assessment

**Low Risk**:
- Clear, mechanical changes
- Pattern is consistent throughout
- Easy to search and replace
- Tests will catch any missed instances

**Benefits Far Outweigh Risks**:
- Eliminates ongoing confusion
- Makes system more maintainable
- Reduces code complexity
- Better user experience long-term

## Timeline Estimate

- **Step 1-3** (Core changes): 30-45 minutes
- **Step 4** (Tests): 30-60 minutes
- **Step 5** (Documentation): 15-30 minutes (mostly done)
- **Step 6** (Examples): 15-30 minutes
- **Step 7** (CLAUDE.md): 15 minutes
- **Testing**: 30-45 minutes
- **Total**: 2-4 hours

## Success Criteria

- [ ] All property shortcuts removed from ConfigOptions
- [ ] `language_config` renamed to `language` throughout codebase
- [ ] All tests passing with new access patterns
- [ ] All documentation examples use consistent pattern
- [ ] All example notebooks use consistent pattern
- [ ] CLAUDE.md documents single access pattern
- [ ] No `config.language` (shortcut) references remain
- [ ] No `config.pint_default_format` (shortcut) references remain
- [ ] No `config.disable_pint_locale` (shortcut) references remain
- [ ] Propagation mechanism still works correctly

## Open Questions

None - approach is straightforward.

## Additional Notes

- This is a **polish task** before v1.0.0 release
- Simplifies the configuration system significantly
- Makes onboarding easier for new users
- Aligns with "explicit is better than implicit" principle
- Since config files haven't been published, perfect time to fix this
