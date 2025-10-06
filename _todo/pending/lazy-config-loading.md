# Task: Lazy Configuration Loading for CLI Robustness

**Status**: In Development
**Branch**: `feature/lazy-config-loading`
**Started**: 2025-10-06

**Original Objective**: Fix CLI commands (`config open`, `config init --force`) that fail when config files have syntax errors, even though these commands don't need to parse the config.

## Implementation Progress

### Session 1: 2025-10-06 - Planning and Design
- ✓ Deep analysis of root cause and impact
- ✓ Revised implementation strategy from lazy-only to defensive initialization
- ✓ Detailed method classification (path-only vs config-dependent)
- ✓ Comprehensive test scenarios defined
- ✓ Error recovery paths documented

### Session 2: 2025-10-06 - Implementation Complete
- ✓ Phase 1: Defensive initialization in `ConfigManager.__init__`
  - Wrapped config loading in try-except block
  - Added `_load_error` tracking for helpful error messages
  - Always initializes `_options` (even with broken configs)
  - Added `_ensure_loaded()` guard method
- ✓ Phase 2: Protected config-dependent methods
  - Added guards to: `save_config()`, `show_config()` (merged only), `get_option()`, `set_option()`, `_propagate_changes()`
  - Path-only operations unguarded: `get_config_path()`, `init_config()`, `_generate_config_template()`
- ✓ Phase 3: CLI robustness verified (no changes needed)
  - `config path` works with broken configs
  - `config init --force` works with broken configs
  - `config show` fails gracefully with helpful error
- ✓ Phase 4: Comprehensive testing
  - 11 new unit tests for config robustness (`test_config_robustness.py`)
  - 5 new CLI integration tests (`test_cli_robustness.py`)
  - All 157 tests pass (including existing tests - no regressions)

**Status**: Implementation complete and verified

## Problem Analysis

### Root Cause
`ConfigManager()` is instantiated at module import time:
```python
# src/keecas/config/manager.py:1022
_config_manager = ConfigManager()
```

The `__init__` method immediately calls `self.load_configs()`, which parses TOML files. If any config has syntax errors (like `True` instead of `true`), the entire module import fails.

### Impact
CLI commands that should be resilient to config errors fail:
- `keecas config open --global` - just opens file in editor, doesn't need parsing
- `keecas config init --force --global` - overwrites file, doesn't need existing content
- Any other keecas command fails even if config is irrelevant to the operation

### Current Behavior
```bash
$ keecas config open --global
# Fails with tomlkit.exceptions.UnexpectedCharError
```

Expected: Opens `~/.keecas/config.toml` in system editor regardless of content.

## Proposed Solution

### Option 1: Defensive Initialization with Lazy Loading (Recommended)
Use a resilient initialization pattern that never fails on import:

```python
class ConfigManager:
    def __init__(self):
        """Initialize manager - always succeeds even with broken configs."""
        # Path setup - always works
        self._global_config_path = self._get_global_config_path()
        self._local_config_path = self._get_local_config_path()

        # State tracking
        self._configs_loaded = False
        self._load_error = None  # Store error for helpful messages
        self._loaded_files = []

        # Try to load configs, but don't fail if broken
        try:
            self._options = ConfigOptions()
            self._options._config_manager_ref = self
            self._options.language_config._config_manager_ref = self
            self.load_configs()
            self._configs_loaded = True
        except Exception as e:
            # Store error but continue - path-only operations still work
            self._load_error = e
            # Create minimal options for path-only operations
            self._options = ConfigOptions()
            self._options._config_manager_ref = self
            self._options.language_config._config_manager_ref = self

    def _ensure_loaded(self):
        """Ensure configs loaded, raise helpful error if broken."""
        if self._load_error:
            raise RuntimeError(
                f"Configuration could not be loaded: {self._load_error}\n"
                f"To fix: keecas config init --force [--global|--local]"
            )
        if not self._configs_loaded:
            self.load_configs()
            self._configs_loaded = True
```

**Pros**:
- Module import never fails - CLI always accessible
- Path-only operations (`init`, `open`, `get_path`) always work
- Clear error messages guide users to recovery commands
- Minimal changes to existing code
- No risk to ConfigSection nested access patterns

**Cons**:
- Need to identify ~15 methods requiring loaded config
- Slightly more complex error handling

### Option 2: Separate CLI Manager
Create a lightweight manager for CLI operations that doesn't load configs:

```python
class ConfigPathManager:
    """Minimal manager for CLI operations that only need paths."""
    def __init__(self):
        self._global_config_path = Path.home() / ".keecas" / "config.toml"
        self._local_config_path = Path.cwd() / ".keecas" / "config.toml"

    def get_path(self, scope='local'):
        return self._global_config_path if scope == 'global' else self._local_config_path

    def init_config(self, scope='local', force=False):
        # Create new config without loading existing
        pass

# Use in CLI
from keecas.config.cli_manager import ConfigPathManager
```

**Pros**:
- Clean separation of concerns
- No risk of breaking existing code
- CLI operations guaranteed to work

**Cons**:
- Code duplication (path logic)
- Two manager classes to maintain

### Option 3: Try-Except at Import (Quick Fix)
Wrap the module-level instantiation:

```python
try:
    _config_manager = ConfigManager()
except Exception:
    # Create manager with defaults, mark as unloaded
    _config_manager = ConfigManager(_skip_load=True)
```

**Pros**:
- Minimal code change
- Quick fix for immediate issue

**Cons**:
- Silently swallows errors that might be legitimate
- Hidden failure mode
- Poor debugging experience

## Recommendation

**Option 1 (Defensive Initialization)** is the best architectural solution:

1. **Resilience**: Module import never fails - CLI always accessible
2. **Recovery**: Path-only commands (`init --force`, `open`) work even with broken configs
3. **Backwards Compatible**: Existing code paths unchanged (with guards added)
4. **Clear Errors**: Helpful error messages guide users to recovery
5. **Minimal Risk**: No changes to ConfigSection or nested access patterns

## Implementation Plan

### Phase 1: Defensive Initialization (Core Fix)
**File**: `src/keecas/config/manager.py`

1. **Modify `ConfigManager.__init__` (lines 436-444)**:
   - Wrap config loading in try-except
   - Store `_load_error` if loading fails
   - Always initialize `_options` (even if loading fails)
   - Set `_configs_loaded = True` only on success

2. **Add `_ensure_loaded()` guard method**:
   - Check `_load_error` - raise with recovery hint
   - Check `_configs_loaded` - load if needed
   - Insert after `__init__` method

### Phase 2: Protect Config-Dependent Methods
Add `self._ensure_loaded()` at start of these methods:

**Need Guards** (require parsed config):
- `show_config()` (line 726) - reads TOML files
- `save_config()` (line 566) - uses `_options.to_toml_dict()`
- `to_dict()` method on options (if exists)
- Any method accessing `self._options` attributes beyond basic path operations
- `_propagate_changes()` (line 803) - accesses language settings

**Don't Need Guards** (path-only operations):
- `get_config_path()` (line 722) - just returns path
- `init_config()` (line 696) - creates new file from defaults
- `_get_global_config_path()` (line 446) - pure calculation
- `_get_local_config_path()` (line 455) - pure calculation
- `_generate_config_template()` (line 863) - uses ConfigOptions() defaults

**Special Case**:
- `reset_config()` (line 756) - calls `_generate_config_template()` then `load_configs()`
  - Add guard AFTER template generation, BEFORE accessing loaded config

### Phase 3: CLI Robustness
**File**: `src/keecas/cli.py`

No changes needed! CLI commands already use correct methods:
- `cmd_open()` uses `get_config_path()` - path-only ✓
- `cmd_init()` uses `init_config()` - path-only ✓
- `cmd_show()` uses `show_config()` - will have guard ✓

### Phase 4: Testing
Add tests for broken config scenarios:

```python
def test_import_with_broken_config(tmp_path):
    """Module import should succeed even with syntax errors."""
    # Create config with invalid TOML
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text('language = True  # Invalid: should be "true"')

    # Import should succeed
    from keecas.config.manager import ConfigManager
    manager = ConfigManager()

    # Path-only operations should work
    assert manager.get_config_path() is not None
    assert manager.init_config(force=True) is True

    # Config-dependent operations should fail with helpful message
    with pytest.raises(RuntimeError, match="keecas config init --force"):
        manager.show_config()

def test_cli_open_with_broken_config(tmp_path, monkeypatch):
    """CLI open command should work even with syntax errors."""
    monkeypatch.chdir(tmp_path)

    # Create broken config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text('katex = True  # Invalid TOML')

    # CLI open should succeed
    result = subprocess.run(['keecas', 'config', 'open', '--local'])
    assert result.returncode == 0

def test_cli_init_force_with_broken_config(tmp_path, monkeypatch):
    """CLI init --force should overwrite broken configs."""
    monkeypatch.chdir(tmp_path)

    # Create broken config
    config_file = tmp_path / ".keecas" / "config.toml"
    config_file.parent.mkdir(parents=True)
    config_file.write_text('invalid syntax here!')

    # Init --force should succeed
    result = subprocess.run(['keecas', 'config', 'init', '--local', '--force'])
    assert result.returncode == 0

    # New config should be valid
    config_data = toml.load(config_file)
    assert config_data is not None
```

## Method Classification

### Path-Only Methods (No Guard Needed)
These work with broken configs:
- `__init__()` - resilient initialization
- `_get_global_config_path()` - pure path calculation
- `_get_local_config_path()` - pure path calculation
- `get_config_path()` - returns path only
- `init_config()` - creates from defaults, doesn't read existing
- `_generate_config_template()` - uses ConfigOptions() fresh defaults

### Config-Dependent Methods (Need Guard)
These require parsed config:
- `show_config()` - reads and parses TOML files
- `save_config()` - calls `_options.to_toml_dict()`
- `_propagate_changes()` - accesses `_options` attributes
- `set_option()` - modifies `_options` attributes
- `get_option()` - reads `_options` attributes
- `_update_pint_language()` - checks `_options.disable_pint_locale`
- `to_dict()` on ConfigOptions - serializes loaded config

### Special Cases
- `reset_config()` - Partially needs guard:
  - Template generation works (uses defaults)
  - `load_configs()` call after write needs no guard (just did reset)
- `load_configs()` itself - No guard needed (it IS the loader)
- `_load_and_migrate_config()` - No guard needed (called by `load_configs`)

## Error Scenarios and Recovery Paths

### Scenario 1: Broken Config + Path-Only Operation
```bash
# Config has syntax error
$ cat ~/.keecas/config.toml
language = True  # Invalid: should be "true"

# Path-only operations still work
$ keecas config open --global
Opening global configuration file with system editor...
Opened: /home/user/.keecas/config.toml
```

**What Happens**:
1. Module import succeeds (defensive `__init__`)
2. `_load_error` is set but hidden
3. `cmd_open()` calls `get_config_path()` - no guard, works fine
4. User can fix config in editor

### Scenario 2: Broken Config + Config-Dependent Operation
```bash
# Config has syntax error
$ cat ~/.keecas/config.toml
katex = True  # Invalid TOML

# Config-dependent operation fails with helpful error
$ keecas config show --global
Error: Configuration could not be loaded: tomlkit.exceptions.UnexpectedCharError
To fix: keecas config init --force [--global|--local]
```

**What Happens**:
1. Module import succeeds
2. `_load_error` is set
3. `cmd_show()` calls `show_config()` which calls `_ensure_loaded()`
4. `_ensure_loaded()` sees `_load_error` and raises with recovery command
5. User knows exactly how to fix

### Scenario 3: Recovery with `init --force`
```bash
# Fix broken config
$ keecas config init --force --global
Configuration template created at: /home/user/.keecas/config.toml (global)

# Now config-dependent operations work
$ keecas config show --global
=== Global Configuration ===
...config content...
```

**What Happens**:
1. `init_config()` has no guard - works even with broken config
2. Overwrites broken config with valid template
3. Subsequent operations succeed

### Scenario 4: Normal Usage (No Broken Config)
```bash
# Everything works as before
$ keecas config show
=== Merged Configuration ===
...config content...
```

**What Happens**:
1. `__init__` successfully loads configs
2. `_configs_loaded = True`, `_load_error = None`
3. `_ensure_loaded()` returns immediately
4. Zero performance impact

## Migration Notes

- No breaking changes to public API
- Internal `_configs_loaded` flag ensures single load
- Error messages improved to suggest `keecas config init --force` for recovery

## Follow-up Tasks

1. Document recovery procedure in README
2. Add `keecas config validate` command for diagnostics
3. Consider schema validation with better error messages
4. Add CI test with intentionally broken configs

---

## Executive Summary

**Problem Solved**: CLI commands (`config open`, `config init --force`) failed when config files had syntax errors, making recovery impossible without manual file deletion.

**Solution Implemented**: Defensive initialization pattern where `ConfigManager.__init__()` never fails on import, even with broken configs. Config loading errors are stored and surfaced only when config-dependent operations are called.

**Key Changes**:
1. `ConfigManager.__init__`: Wrapped `load_configs()` in try-except, stores `_load_error`
2. New `_ensure_loaded()` guard: Checks for errors and provides recovery hint
3. Guards added to 5 config-dependent methods (save, show merged, get_option, set_option, propagate)
4. Path-only operations (get_path, init) remain unguarded and always work

**Testing**: 16 new tests covering broken config scenarios, CLI recovery workflows, and normal usage. All 157 tests pass with no regressions.

**User Impact**:
- **Before**: Broken config → unusable CLI → manual file deletion required
- **After**: Broken config → path-only commands work → `keecas config init --force` fixes → full recovery

**Performance**: Zero overhead for normal usage (immediate return in `_ensure_loaded()` when configs loaded successfully)
