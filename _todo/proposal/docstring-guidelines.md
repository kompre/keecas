# Proposal: Google-Style Docstring Guidelines for Quartodoc

## Objective
Document lessons learned from display.py docstring corrections to establish guidelines for writing effective Google-style docstrings that render well in quartodoc-generated API documentation.

## Analysis: What Went Wrong

After comparing the original docstrings (commit d7f0c22) with user corrections, identified 14 critical issues:

### 1. Unicode Symbols Instead of ASCII
- **Wrong**: Used `≤, ≥, <, >, =, ≠` in parameter descriptions
- **Right**: Use ASCII `<=, >=, <, >, =, !=`
- **Reason**: Unicode can cause rendering issues in quartodoc/Sphinx and harder to read in plain text

### 2. Incorrect Type Annotations
- **Wrong**: `check(lhs: Basic, rhs: Basic)` - suggested symbolic SymPy objects
- **Right**: Type annotations need to reflect that the function accepts any type, but the critical requirement is that `test(lhs, rhs)` must evaluate to `True` or `False`. The function can accept SymPy expressions with units (they evaluate to boolean), but pure symbolic expressions without evaluation will fail.
- **Better annotation**: `check(lhs: Any, rhs: Any)` with clear docstring explanation
- **Reason**: Fundamentally misunderstood the function contract - focused on type rather than behavioral requirement

### 3. Vague Function Descriptions
- **Wrong**: "Compares two expressions using a test function and displays..."
- **Right**: "Compares two values using a test function that must evaluate to `True` or `False`... **The most common case is to be passed to a show_eqn function as secondary dict**"
- **Key point**: Emphasis should be on the evaluation requirement (`test(lhs, rhs)` → boolean), not on whether inputs are "numeric" vs "symbolic"
- **Reason**: Failed to emphasize the actual requirement (boolean evaluation) and common usage patterns

### 4. Missing Critical Warnings
- **Added**: Explicit NOTE about error conditions
  ```
  NOTE: if the test cannot evaluate to either True or False, an error will be raised.
  Common cause for this is that one of the arguments passed are not in the numeric form,
  but still in symbolic form.
  ```
- **Reason**: Users need to understand common failure modes

### 5. Examples Missing Primary Use Case
- **Wrong**: Only standalone `check()` calls
- **Right**: Added integration example with `show_eqn([_p | _e, _c])`
- **Reason**: Didn't demonstrate how function integrates with main workflow

### 6. Inconsistent Variable Naming
- **Wrong**: Used `_v` for both parameters and evaluated values
- **Right**: Use `_p` for parameters, `_e` for expressions, `_v` for values, `_c` for checks
- **Reason**: Violated project's standard naming conventions (see CLAUDE.md)

### 7. Non-Idiomatic Code Patterns
- **Wrong**: `show_eqn([_p, _e, _v])` - three separate dicts
- **Right**: `show_eqn([_p|_e, _v])` - merged first column
- **Reason**: Didn't understand how `show_eqn()` constructs the Dataframe:
  - `list[dict]` converts to Dataframe where keys from first dict define the rows
  - Values from each dict become columns in the Dataframe
  - Subsequent dicts only add column values if their keys match first dict's keys
  - Merging `_p|_e` displays all keys as rows in the output; `_v` adds values as a second column only for matching keys

### 8. Overly Simple Symbol Names
- **Wrong**: `F, A` - basic symbols
- **Right**: `F, A_load` with LaTeX `A_{load}`
- **Reason**: Examples should demonstrate realistic LaTeX subscript usage, and longer symbol names better demonstrate alignment behavior in rendered output

### 9. Single-Line Dict Formatting
- **Wrong**: `{F: 100*u.kN, A: 20*u.cm**2}`
- **Right**: Multi-line formatting:
  ```python
  _p = {
      F: 100*u.kN,
      A_load: 20*u.cm**2
  }
  ```
- **Reason**: Models readable style for real-world usage

### 10. Vague Parameter Descriptions
- **Wrong**: `sep` - "per-column customization"
- **Right**: "separator goes in between each column, so first separator is between first and second column, etc"
- **Reason**: Users need operational details, not just type information

### 11. Incomplete Formatter Documentation
- **Wrong**: Listed types: "Can be single Callable, dict, list, Dataframe..."
- **Right**: Added application scope: "Callable (applied to all cells), list of Callable (applied to each cell in a column), dict of Callable (applied to each cell in a row if key matches)..."
- **Reason**: Users need to understand when each variant applies

### 12. Missing Practical Tips
- **Added**:
  - `display()` tip for mid-cell usage
  - `config.print_label=True` explanation
  - `hash()` function for unique labels
  - Better environment customization examples
- **Reason**: Essential workflow patterns were omitted

### 13. Misleading Comments
- **Wrong**: `# Per-symbol float format`
- **Right**: `# applied to all element in the row` and `# per cell formatting`
- **Reason**: Comment didn't match actual behavior

### 14. Missing Type Options
- **Wrong**: "List elements can be None (no wrapping), str (prefix only), or tuple (prefix, suffix)"
- **Right**: Added "or Callable"
- **Reason**: Documented incomplete type signature

### 15. Missing Raw String Prefix
- **Wrong**: `"""Display mathematical equations...`
- **Right**: `r"""Display mathematical equations...`
- **Reason**: Without `r` prefix, backslashes in LaTeX examples might be interpreted as escape sequences

## Root Cause Analysis

**Core mistake**: Wrote reference documentation for developers who already understand the codebase, rather than educational documentation for users learning to use the tool.

### Key Conceptual Failures:
1. **Assumed expertise**: Wrote as if readers already understood keecas conventions
2. **Prioritized brevity over clarity**: Stripped essential context to save space
3. **Ignored workflow context**: Documented functions in isolation rather than showing how they fit into typical notebook usage
4. **Overlooked error prevention**: Didn't explain common mistakes and failure modes
5. **Used symbols inappropriately**: Unicode symbols reduced portability
6. **Didn't follow project conventions**: Examples violated standard patterns documented in CLAUDE.md
7. **Omitted practical tips**: Left out workflow helpers that real users need

## Proposed Guidelines for CLAUDE.md

### When Writing Google-Style Docstrings for Quartodoc:

#### 1. **Type Annotations Must Match Runtime Behavior**
   - Don't use abstract types (like `Basic`) when concrete types are required
   - Type hints should guide users toward correct usage, not just pass type checkers

#### 2. **Use ASCII in All Documentation Text**
   - Mathematical operators: Use `<=, >=, !=` not `≤, ≥, ≠`
   - Keep unicode only in code examples where needed for LaTeX rendering
   - Unicode symbols can cause issues with LaTeX compilers and rendering engines

#### 3. **Always Use Raw String Prefix**
   - Start docstrings with `r"""` to prevent backslash escape issues
   - Critical for examples containing LaTeX commands

#### 4. **Function Descriptions Must Include:**
   - **What**: Clear description of what function does
   - **Why**: Common use case and motivation
   - **How**: Integration with typical workflow
   - **Warning**: Common failure modes and error conditions

#### 5. **Parameter Descriptions Need Operational Details**
   - Don't just list types - explain how they behave
   - Include positional logic (e.g., "first separator is between first and second column")
   - Clarify scope (e.g., "applied to all cells" vs "applied to each cell in a row")

#### 6. **Examples Must Follow Project Conventions**
   - Use standard dict naming: `_p`, `_e`, `_v`, `_d`, `_l`, `_c`
   - Show realistic LaTeX symbols with subscripts: `A_{load}` not just `A`
   - Use multi-line dict formatting for readability
   - Demonstrate idiomatic patterns: `show_eqn([_p|_e, _v])` not `show_eqn([_p, _e, _v])`

#### 7. **Examples Should Be Tutorial-Quality**
   - Start simple, build complexity progressively
   - Show the most common use case first
   - Include integration examples showing how function fits into workflow
   - Add inline comments explaining non-obvious steps

#### 8. **Include Practical Workflow Tips**
   - Document helper patterns (e.g., `display()` for mid-cell output)
   - Show configuration options that affect behavior
   - Demonstrate clever techniques (e.g., using `hash()` for unique labels)

#### 9. **Separate Code Blocks for Clarity**
   - Each example should be self-contained when possible
   - Use separate `\`\`\`{python}` blocks for distinct concepts
   - Add descriptive comments before each block

#### 10. **Notes Section Should Cover:**
   - Configuration options that affect the function
   - Compatibility considerations (e.g., KaTeX mode)
   - Cross-references to related configuration settings
   - Tips for common usage patterns

### Example Template:

```python
def function_name(
    param1: ConcreteType,
    param2: ConcreteType,
    ...
) -> ReturnType:
    r"""Brief one-line summary.

    Longer description explaining:
    - What the function does
    - Why you would use it (common use case)
    - How it integrates with typical workflows

    NOTE: Critical warnings about common failure modes.

    Args:
        param1: Clear description with operational details (e.g., "applied to X when Y").
            Include behavior explanation, not just type information.
        param2: For complex parameters, explain each variant:
            - Type1: When/how it applies
            - Type2: When/how it applies
            - Type3: When/how it applies

    Returns:
        Description of return value and typical usage.

    Examples:
        ```{python}
        # Start with simplest use case
        from keecas import symbols, u, pc, function_name

        # Use realistic symbols following LaTeX conventions
        F, A_load = symbols(r"F, A_{load}")

        # Multi-line dict formatting
        _p = {
            F: 100*u.kN,
            A_load: 20*u.cm**2
        }

        function_name(_p)
        ```

        ```{python}
        # Show integration with typical workflow
        _e = {
            sigma: "F/A_load" | pc.parse_expr
        }

        _v = {k: v | pc.subs(_p | _e) | pc.N for k, v in _e.items()}

        # Demonstrate idiomatic usage pattern
        show_eqn([_p|_e, _v])
        ```

        ```{python}
        # Include practical tips
        from keecas import config

        # tip: useful workflow helper
        config.some_setting = True

        function_name(_p, special_option=True)
        ```

    See Also:
        - related_function(): Brief description
        - config.setting: Brief description

    Notes:
        - Configuration behavior details
        - Compatibility considerations
        - Common usage patterns
        - Cross-references to config settings
    """
```

## Implementation Plan

1. Create separate `DOCSTRINGS.md` file with comprehensive guidelines
2. Include all 10 guidelines with detailed examples
3. Add example template showing structure
4. Reference `DOCSTRINGS.md` from CLAUDE.md in relevant sections
5. Apply guidelines to all API reference docstrings

## User Decisions

1. **File location**: Create separate `DOCSTRINGS.md` file, referenced in CLAUDE.md ✓

2. **Additional guidelines**: Will add to DOCSTRINGS.md as they arise during development ✓

3. **Automated checks (linting)**:
   - User needs clarification on what this means
   - Possible options:
     - Pre-commit hooks to check docstring format
     - CI/CD validation of docstring structure
     - Ruff/pylint rules for Google-style compliance
     - Custom script to validate examples run without errors

4. **Priority**: All API reference docstrings should follow this schema ✓