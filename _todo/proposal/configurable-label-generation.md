# Configurable Label Generation Strategy

**Status**: Phase 1 (Config Infrastructure) ✅ COMPLETED | Phase 2 (Strategy Implementation) PENDING USER EVALUATION

**Last Updated**: 2025-10-30

## Original Objective

Add config option for the `label` argument in `show_eqn()` to set a default label generation strategy. The current `generate_unique_label` creates hash-based labels that change when any value in the passed list varies, making them unsuitable for manual reference copying. Need to propose stable label generation strategies that balance uniqueness with stability.

## Problem Analysis

### Current State
- `show_eqn(..., label=<callable>)` accepts callable label generators
- `generate_unique_label` exists but generates hash-based labels: `eq-a1b2c3d4`
- Hash changes whenever RHS values change, breaking manual cross-references
- No config-level default for label generation strategy

### Core Tensions
1. **Stability vs. Uniqueness**: Stable labels (based on LHS key only) may collide; unique labels (based on content) are unstable
2. **Manual vs. Programmatic**: Manual referencing needs human-readable stable labels; programmatic needs guaranteed uniqueness
3. **Scope**: Same symbol may appear multiple times in a document (different cells, sections, recalculations)

## Proposed Solutions

### Strategy 1: Key-Based Stable Labels (Recommended Default)
Generate labels from LHS key only, ignoring RHS values.

**Implementation:**
```python
def generate_stable_label(data: list[Any]) -> str:
    """Generate label from key only (first element of data list).

    Args:
        data: [key, value1, value2, ...] from show_eqn

    Returns:
        Label string like "eq-sigma" or "eq-F"
    """
    key = data[0]
    # Convert SymPy symbol to LaTeX string, sanitize for label
    key_str = str(key).replace("\\", "").replace("{", "").replace("}", "").replace("_", "-")
    return f"{config.latex.eq_prefix}{key_str}{config.latex.eq_suffix}"
```

**Pros:**
- Stable: Changing RHS values doesn't break references
- Human-readable: `eq-sigma`, `eq-F-load`
- Simple mental model for users

**Cons:**
- **Collision risk**: Same key in different cells generates identical labels
- LaTeX will use last definition, breaking earlier references
- Not suitable for multi-cell documents with repeated symbols

### Strategy 2: Cell-Scoped Stable Labels
Append cell execution counter or user-provided scope identifier.

**Implementation:**
```python
def generate_cell_scoped_label(data: list[Any], scope: str | None = None) -> str:
    """Generate label with optional scope prefix.

    Args:
        data: [key, value1, value2, ...] from show_eqn
        scope: Optional scope identifier (e.g., "section1", "calc-beam-1")

    Returns:
        Label string like "eq-section1-sigma" or "eq-sigma-1"
    """
    key = data[0]
    key_str = str(key).replace("\\", "").replace("{", "").replace("}", "").replace("_", "-")

    if scope:
        label_text = f"{scope}-{key_str}"
    else:
        # Auto-increment counter per key
        counter = _get_or_increment_counter(key)
        label_text = f"{key_str}-{counter}"

    return f"{config.latex.eq_prefix}{label_text}{config.latex.eq_suffix}"
```

**Pros:**
- Solves collision problem with counter/scope
- Still human-readable: `eq-sigma-1`, `eq-section-A-sigma`
- Stable within scope (changing values doesn't affect label)

**Cons:**
- Counter state management complexity (global mutable state)
- Counter resets between notebook sessions unless persisted
- Scope parameter adds API surface complexity
- Non-deterministic if cell execution order changes

### Strategy 3: Hybrid Key-Value Fingerprint
Hash only the key, not the full values, with optional value participation.

**Implementation:**
```python
def generate_fingerprint_label(data: list[Any], include_values: bool = False) -> str:
    """Generate label from key with optional value fingerprinting.

    Args:
        data: [key, value1, value2, ...] from show_eqn
        include_values: If True, include hash of value types (not values themselves)

    Returns:
        Label string like "eq-sigma-a1b2c3" or "eq-F"
    """
    key = data[0]
    key_str = str(key).replace("\\", "").replace("{", "").replace("}", "").replace("_", "-")

    if include_values:
        # Hash value types/structure, not actual values
        value_types = tuple(type(v).__name__ for v in data[1:] if v is not None)
        fingerprint = generate_id(value_types, length=4)
        label_text = f"{key_str}-{fingerprint}"
    else:
        label_text = key_str

    return f"{config.latex.eq_prefix}{label_text}{config.latex.eq_suffix}"
```

**Pros:**
- Type-based fingerprint stable to value changes
- Distinguishes between `{sigma: expr}` vs `{sigma: numeric}` vs `{sigma: description}`
- No global state needed

**Cons:**
- Type signature changes still break labels (rare but possible)
- Fingerprint less human-readable than counter
- More complex mental model

### Strategy 4: First-Column-Only Stable Labels
Label based on LHS key + type/content of first RHS value (most stable column).

**Implementation:**
```python
def generate_first_col_label(data: list[Any]) -> str:
    """Generate label from key and first value column.

    Assumes first value column is most stable (usually symbolic expression).

    Args:
        data: [key, value1, value2, ...] from show_eqn

    Returns:
        Label string like "eq-sigma-expr" or "eq-F-param"
    """
    key = data[0]
    key_str = str(key).replace("\\", "").replace("{", "").replace("}", "").replace("_", "-")

    # Classify first value
    if len(data) > 1 and data[1] is not None:
        first_val = data[1]
        if hasattr(first_val, 'free_symbols'):  # SymPy expression
            suffix = "expr"
        elif hasattr(first_val, 'units'):  # Pint quantity
            suffix = "param"
        elif isinstance(first_val, str):
            suffix = "desc"
        else:
            suffix = "val"
        label_text = f"{key_str}-{suffix}"
    else:
        label_text = key_str

    return f"{config.latex.eq_prefix}{label_text}{config.latex.eq_suffix}"
```

**Pros:**
- Leverages keecas usage pattern: `[_p|_e, _v, _d]` structure
- Distinguishes parameter/expression/value/description rows naturally
- Intuitive: `eq-sigma-expr` for expression, `eq-sigma-val` for numeric
- Stable as long as column structure unchanged

**Cons:**
- Assumes consistent first-column semantics
- Still has collision risk if same key appears twice with same type
- More heuristic/implicit than explicit

## Recommended Approach

### Primary Recommendation: Strategy 4 (First-Column-Only)
Best balance of stability, readability, and practical collision avoidance for typical keecas workflows.

**Rationale:**
- Keecas conventions already structure data by semantic columns (`_p`, `_e`, `_v`, `_d`)
- Natural collision avoidance: Same key typically appears once per semantic type
- Human-readable: `eq-sigma-expr`, `eq-F-param` clearly indicate what the label refers to
- Works with existing Dataframe structure without additional state

### Config Implementation ✅ IMPLEMENTED

**Current Implementation:**

Config attribute added to `LatexConfig`:

```python
@dataclass
class LatexConfig:
    # ... other fields ...
    label: Callable | None = None  # Runtime-only: default label generator
```

User-facing API:

```python
# Set runtime default (callable only, not serializable to TOML)
config.latex.label = my_label_callable

# Per-call override (existing behavior preserved)
show_eqn(eqns, label=generate_stable_label)  # Override default

# Or None to use config default
show_eqn(eqns, label=None)  # Uses config.latex.label if set, else no labels

# Or dict/str for full control (existing behavior)
show_eqn(eqns, label={sigma: "stress-calc", F: "force-input"})
```

**Implementation Details:**
- Added `label: Callable | None = None` to `LatexConfig` class (manager.py:81)
- Field is intentionally excluded from TOML serialization (not serializable)
- `show_eqn()` checks `config.latex.label` when `label=None` (display.py:715-716)
- Config template includes documentation comment explaining runtime-only usage
- Supports `None` (no labels) or `Callable` (dynamic generation)

**TOML Limitation:**
- Cannot specify callables in TOML files
- Config option is Python runtime-only: `config.latex.label = callable`
- String/dict defaults would not make sense (not reusable across different equations)

### Fallback Hierarchy (Current Behavior)

When `label` parameter is `None` in `show_eqn()`:
1. Check `config.latex.label`
2. If set (callable), use it to generate labels
3. If `None`, fall back to `{k: None for k in keys}` (no labels)

## Implementation Plan

### Phase 1: Core Infrastructure ✅ COMPLETED
1. ~~Create new module `src/keecas/label_strategies.py` with strategy functions~~
   - **DEFERRED**: User wants time to evaluate strategy implementations

2. ~~Add `LabelConfig` to config system~~ → **MODIFIED**:
   - ✅ Added `label: Callable | None` to existing `LatexConfig` class
   - ✅ Excluded from TOML serialization (runtime-only)
   - ✅ Added documentation to config template
   - No separate `LabelConfig` class needed (simpler approach)

3. ~~Update `show_eqn()` in `display.py`~~ → ✅ COMPLETED (by user):
   - ✅ When `label=None`, check `config.latex.label`
   - ✅ Use callable if set, otherwise default to no labels

### Phase 2: Strategy Implementation (PENDING USER EVALUATION)
1. **User wants to evaluate which strategies to implement**
   - Strategies 1-4 outlined above for consideration
   - User will decide after "simmering" on the design

2. Once strategies are chosen, implement in `src/keecas/label_strategies.py`:
   - Strategy functions with signature: `(data: list[Any]) -> str`
   - Unit tests for each strategy
   - Integration tests with `config.latex.label`

3. Documentation updates:
   - Add to `CLAUDE.md` under label conventions
   - Update `show_eqn()` docstring with strategy examples
   - Add examples to `docs/` or example notebooks

### Phase 3: Documentation & Migration (PENDING)
1. Update example notebooks to demonstrate chosen strategies
2. Add section to README about label generation
3. Migration guide if needed (breaking changes acceptable for v1.0.0)

## Edge Cases & Considerations

### 1. Empty/None Keys
Strategy must handle `None` keys gracefully → return empty string.

### 2. Callable Label Parameter
When user explicitly passes callable, it overrides config completely (existing behavior preserved).

### 3. Dict Label Parameter
When user explicitly passes dict, it overrides config completely (existing behavior preserved).

### 4. KaTeX Mode
Labels suppressed in KaTeX mode regardless of strategy (`config.display.katex = True`).

### 5. Multi-label Environments
Strategies must work with environments that support per-row labels (align) and single labels (equation).

### 6. Symbol Serialization
LaTeX symbols like `\sigma_{Sd}` need sanitization:
- Remove backslashes: `\sigma` → `sigma`
- Replace braces: `_{Sd}` → `-Sd`
- Replace commas: `\tau_{1\,Rd}` → `tau-1-Rd`

### 7. Backward Compatibility
v1.0.0 allows breaking changes, but document migration path:
- Old behavior: `label=None` → no labels
- New behavior: `label=None` → use `config.label.default_strategy`
- Preserve old: Set `config.label.default_strategy = "none"`

## Open Questions for User Evaluation

1. **Counter Strategy Inclusion?**
   - Should we include Strategy 2 (counter-based) despite global state concerns?
   - Use case: User wants `eq-sigma-1`, `eq-sigma-2`, ... across notebook
   - Complexity: Requires global registry, serialization for reproducibility
   - **Current approach**: User can implement custom counter if needed

2. **User-Defined Strategies?**
   - Allow users to register custom strategy functions?
   - **Current solution**: User directly assigns callable: `config.latex.label = my_callable`
   - Simple and flexible without registration complexity

3. **Which strategies to implement?**
   - Strategy 1 (key-only): Simple but collision-prone
   - Strategy 2 (counter): Stateful, non-deterministic
   - Strategy 3 (fingerprint): Type-based hash
   - Strategy 4 (first-col): Recommended, leverages keecas conventions
   - **User to decide after evaluation**

4. **Label Validation?**
   - Check for LaTeX label validity (no spaces, special chars)?
   - Warn on potential collisions?
   - **Decision**: Defer to future if needed (low priority)

## Success Criteria

### Phase 1 (Config Infrastructure) ✅ COMPLETED
1. ✅ User can set `config.latex.label = callable` at runtime
2. ✅ `show_eqn(eqns)` with `label=None` uses config default
3. ✅ No breaking changes to existing explicit `label` parameter usage
4. ✅ Documentation in config template

### Phase 2 (Strategy Implementation) - PENDING
1. Implement chosen label generation strategies
2. Labels remain stable when RHS numeric values change
3. Labels are human-readable and semantically meaningful
4. Full test coverage for implemented strategies
5. Documentation includes examples of each strategy

## Timeline Estimate (Revised)

- ✅ Phase 1 (Config Infrastructure): **COMPLETED** (1 hour)
- Phase 2 (Strategy Implementation): 3-5 hours (pending user decision)
- Phase 3 (Documentation): 2-3 hours
- **Total Remaining**: 5-8 hours (after strategy selection)

## Non-Goals

- Automatic collision detection/warnings (future enhancement)
- Persistent counter state across sessions (future enhancement)
- Label namespace management (future enhancement)
- GUI/interactive label selection (out of scope)

## Alternative Considered: Do Nothing

**Rationale for rejection:** While users can manually provide label callables or dicts, config-level defaults significantly improve UX for common cases. The "first column" strategy aligns naturally with keecas conventions and provides substantial value with minimal complexity.

## References

- Current implementation: `src/keecas/label.py` (`generate_unique_label`)
- Usage context: `src/keecas/display.py` (`show_eqn`, `_attach_label`)
- Config system: `src/keecas/config/manager.py`
- Conventions: `CLAUDE.md` (symbol naming, dict patterns)
