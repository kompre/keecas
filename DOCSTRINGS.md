# Google-Style Docstring Guidelines for Quartodoc

This document establishes guidelines for writing effective Google-style docstrings that render well in quartodoc-generated API documentation for the keecas project.

## Core Principle

**Write tutorial-quality documentation for users learning the tool, not reference documentation for developers who already understand the codebase.**

Docstrings should teach users how to use the API effectively through clear explanations, realistic examples, and practical workflow integration.

---

## The 10 Guidelines

### 1. Type Annotations Must Match Runtime Behavior

**Principle**: Type hints should guide users toward correct usage, not just satisfy type checkers.

- Focus on behavioral requirements, not just types
- Use `Any` when the actual requirement is about behavior (e.g., "must evaluate to boolean")
- Don't use abstract types (like `Basic`) when they suggest incorrect usage patterns

**Example - Wrong:**
```python
def check(lhs: Basic, rhs: Basic, test=Le) -> Markdown:
    """..."""
```
*Problem*: Suggests function accepts symbolic SymPy objects, but it actually requires expressions that evaluate to boolean.

**Example - Right:**
```python
def check(lhs: Any, rhs: Any, test: type = Le) -> Markdown:
    r"""Engineering verification function with localized pass/fail indicators.

    Compares two values using a test function that must evaluate to `True` or `False`.

    NOTE: if the test cannot evaluate to either True or False, an error will be raised.
    Common cause for this is that one of the arguments passed are not in numeric form,
    but still in symbolic form.

    Args:
        lhs: evaluated left-hand side expression. Can be numeric values, SymPy
            expressions with units (they evaluate to boolean), but pure symbolic
            expressions without evaluation will fail.
        ...
    """
```

---

### 2. Use ASCII in All Documentation Text

**Principle**: Ensure maximum compatibility across rendering engines and editors.

**Rules:**
- Mathematical operators: Use `<=, >=, !=` not `≤, ≥, ≠`
- Keep unicode only in code examples where needed for LaTeX rendering
- Unicode symbols can cause issues with LaTeX compilers and rendering engines

**Example - Wrong:**
```python
Args:
    test: Comparison function from SymPy's relational module. Options:
        - Le (≤): LessThan (default)
        - Ge (≥): GreaterThan
```

**Example - Right:**
```python
Args:
    test: Comparison function from SymPy's relational module. Options:
        - Le: LessThan (default, less than or equal)
        - Ge: GreaterThan (greater than or equal)
```

---

### 3. Always Use Raw String Prefix

**Principle**: Prevent backslash escape issues in LaTeX examples.

**Rules:**
- Start all docstrings with `r"""`
- Critical for examples containing LaTeX commands like `\sigma`, `\label`, `\\`

**Example:**
```python
def show_eqn(...) -> Markdown:
    r"""Display mathematical equations as formatted LaTeX amsmath block.

    Examples:
        ```{python}
        sigma = symbols(r"\sigma")
        custom_env = {
            "line_separator": r" \\ ",
            ...
        }
        ```
    """
```

---

### 4. Function Descriptions Must Include Four Elements

**Principle**: Give users complete context for understanding when and how to use the function.

**Required Elements:**
1. **What**: Clear description of what function does
2. **Why**: Common use case and motivation
3. **How**: Integration with typical workflow
4. **Warning**: Common failure modes and error conditions

**Example - Wrong:**
```python
def check(...) -> Markdown:
    """Compares two expressions using a test function and displays a formatted
    verification result with color-coded pass/fail indicators.
    """
```
*Problem*: Missing why (use case), how (workflow integration), and warnings (failure modes).

**Example - Right:**
```python
def check(...) -> Markdown:
    r"""Engineering verification function with localized pass/fail indicators.

    Compares two values using a test function that must evaluate to `True` or `False`
    and displays a formatted message based on the pass/fail status. Return message
    can be templated as Markdown object. The most common case is to be passed to a
    show_eqn function as secondary dict (the object will be formatted according to
    `cell_formatter` specification).

    NOTE: if the test cannot evaluate to either True or False, an error will be raised.
    Common cause for this is that one of the arguments passed are not in the numeric
    form, but still in symbolic form.
    """
```

---

### 5. Parameter Descriptions Need Operational Details

**Principle**: Explain how parameters behave, not just what types they accept.

**Rules:**
- Don't just list types - explain how they behave
- Include positional logic (e.g., "first separator is between first and second column")
- Clarify scope (e.g., "applied to all cells" vs "applied to each cell in a row")

**Example - Wrong:**
```python
Args:
    sep: Separator(s) between cells. Can be string or list of strings for
        per-column customization.
```

**Example - Right:**
```python
Args:
    sep: Separator(s) between cells in the amsmath block (e.g. `LHS & RHS & ...`).
        Can be string or list of strings for finer customization (separator goes
        in between each column, so first separator is between first and second
        column, etc). Defaults to environment's default separator (None uses
        environment default: "&" for align, "" for equation/gather).
```

**Example - Formatter Parameters:**
```python
Args:
    cell_formatter: Custom cell value formatter function(s). Can be:
        - single Callable[(value, col_index) -> str] (applied to all cells)
        - list of Callable (applied to each cell in a column)
        - dict of Callable (applied to each cell in a row if key matches)
        - dict of list of Callable or Dataframe for cell specific formatting
        - tuple (formatters, default)
        Defaults to config.display.cell_formatter.

    row_formatter: Custom row-level formatter function(s). Can be:
        - single Callable[(row_latex_str) -> str]
        - dict mapping symbol keys to formatters
        It applies to the composed entire row (str).
        Defaults to config.display.row_formatter.
```

---

### 6. Examples Must Follow Project Conventions

**Principle**: Examples should demonstrate idiomatic keecas usage patterns.

**Rules:**
- Use standard dict naming: `_p`, `_e`, `_v`, `_d`, `_l`, `_c`
- Show realistic LaTeX symbols with subscripts: `A_{load}` not just `A`
- Use multi-line dict formatting for readability
- Demonstrate idiomatic patterns from CLAUDE.md conventions
- Longer symbol names better demonstrate alignment behavior

**Example - Wrong:**
```python
Examples:
    ```{python}
    F, A = symbols(r"F, A")
    _v = {F: 100*u.kN, A: 20*u.cm**2}
    show_eqn([_p, _e, _v])  # Three separate dicts
    ```
```

**Example - Right:**
```python
Examples:
    ```{python}
    from keecas import symbols, u, pc, show_eqn

    # Use realistic symbols with LaTeX subscripts
    F, A_load = symbols(r"F, A_{load}")

    # Multi-line dict formatting
    _p = {
        F: 100*u.kN,
        A_load: 20*u.cm**2
    }

    sigma = symbols(r"\sigma")
    _e = {
        sigma: "F/A_load" | pc.parse_expr
    }

    _v = {k: v | pc.subs(_p | _e) | pc.N for k, v in _e.items()}

    # Idiomatic: merge _p|_e for first column
    show_eqn([_p|_e, _v])
    ```
```

**Understanding `show_eqn([_p|_e, _v])` pattern:**
- `list[dict]` converts to Dataframe where keys from first dict define the rows
- Values from each dict become columns in the Dataframe
- Subsequent dicts only add column values if their keys match first dict's keys
- Merging `_p|_e` displays all keys as rows in the output; `_v` adds values as a second column only for matching keys

---

### 7. Examples Should Be Tutorial-Quality

**Principle**: Progressive complexity that teaches users the full capability of the function.

**Structure:**
1. Start simple - basic use case with minimal parameters
2. Build complexity - add parameters and show integration
3. Advanced usage - demonstrate powerful features and edge cases

**Rules:**
- Show the most common use case first
- Include integration examples showing how function fits into workflow
- Add inline comments explaining non-obvious steps
- Use separate `{python}` blocks for distinct concepts

**Example:**
```python
Examples:
    ```{python}
    # Basic parameter display
    F, A_load = symbols(r"F, A_{load}")

    _p = {
        F: 100*u.kN,
        A_load: 20*u.cm**2
    }

    show_eqn(_p)
    ```

    ```{python}
    # Multi-column with expressions and values
    sigma = symbols(r"\sigma")

    _e = {
        sigma: "F/A_load" | pc.parse_expr
    }

    _v = {k: v | pc.subs(_p | _e) | pc.convert_to([u.MPa]) | pc.N for k, v in _e.items()}

    show_eqn([_p|_e, _v])
    ```

    ```{python}
    # Custom formatting and labels
    from keecas import config

    config.display.print_label = True

    # label dictionary
    _l = {
        F: 'force',
        A_load: 'area',
        sigma: 'stress-calc',
    }

    # specific float formatting
    _f = {
        F: '{:.1f}',           # applied to all elements in the row
        A_load: '{:.2f}',      # applied to all elements in the row
        sigma: [None, None, '.3f'],  # per cell formatting
    }

    show_eqn([_p|_e, _v], float_format=_f, label=_l)
    ```
```

---

### 8. Include Practical Workflow Tips

**Principle**: Help users avoid common pitfalls and discover powerful patterns.

**Include:**
- Helper patterns (e.g., `display()` for mid-cell output)
- Configuration options that affect behavior
- Clever techniques (e.g., using `hash()` for unique labels)
- Integration with common workflows

**Example:**
```python
Examples:
    ```{python}
    # Different environments
    from IPython.display import display

    # tip: if show_eqn used mid-cell, use display() to emit rendered output
    display(show_eqn(_p, environment="align"))
    show_eqn(_p, environment="gather")
    ```

    ```{python}
    # Custom formatting and description
    from keecas import config

    config.display.print_label = True

    # short description
    _d = {
        F: 'applied force',
        A_load: 'area of application',
        sigma: 'stress',
    }

    # tip: use hash function to create unique labels
    _l = {k: hash(v) for k,v in _d.items()}

    show_eqn([_p|_e, _v, _d], label=_l)
    ```
```

---

### 9. Demonstrate Integration with Main Workflows

**Principle**: Show how the function is typically used in real notebook workflows.

**For `check()` function:**
```python
Examples:
    ```{python}
    from keecas import symbols, u, pc, check, show_eqn

    # Most common pattern: use with show_eqn
    N_Ed, N_Rd = symbols(r"N_{Ed}, N_{Rd}")
    _p = {N_Ed: 850*u.kN, N_Rd: 1200*u.kN}

    _e = {
        k: k | pc.subs(_p) | pc.N for k in [N_Ed/N_Rd]
    }

    _c = {
        k: check(v, 1.0) for k, v in _e.items()
    }

    # Integration: check results as secondary dict
    show_eqn([_p | _e, _c])
    ```
```

---

### 10. Notes Section Should Cover Essential Context

**Principle**: Provide quick reference to configuration, compatibility, and usage patterns.

**Include:**
- Configuration options that affect the function
- Compatibility considerations (e.g., KaTeX mode)
- Cross-references to related configuration settings
- Tips for common usage patterns

**Example:**
```python
Notes:
    - Returns green indicator for passing checks, red for failing (default template)
    - Verification text ("VERIFIED"/"NOT_VERIFIED") automatically localized per config.language
    - Supports 10 languages: de, es, fr, it, pt, da, nl, no, sv, en
    - LaTeX output respects config.katex setting (disables labels for KaTeX compatibility)
    - Float formatting supports format specs with or without braces: ".3f" or "{:.3f}"
    - Environment separator defaults to None (uses environment-specific default)
    - Labels use config.latex.eq_prefix and eq_suffix for consistent referencing
    - use config.print_label=True to display resulting label to be used for referencing
      (it will display the label even in KaTeX mode)
```

---

## Complete Docstring Template

```python
def function_name(
    param1: ConcreteType,
    param2: ConcreteType | Any,
    optional_param: str | None = None,
    **kwargs: Any,
) -> ReturnType:
    r"""Brief one-line summary of what the function does.

    Longer description explaining:
    - What the function does (2-3 sentences)
    - Why you would use it (common use case and motivation)
    - How it integrates with typical workflows

    NOTE: Critical warnings about common failure modes or requirements.

    Args:
        param1: Clear description with operational details (e.g., "applied to X when Y").
            Include behavior explanation, not just type information.
        param2: For complex parameters, explain each variant with operational details:
            - Type1: When/how it applies (with behavioral details)
            - Type2: When/how it applies (with behavioral details)
            - Type3: When/how it applies (with behavioral details)
            Defaults to config.section.setting.
        optional_param: Description with default behavior.
        **kwargs: Additional keyword arguments:
            - kwarg1 (type): Description
            - kwarg2 (type): Description

    Returns:
        Description of return value and typical usage pattern.

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
        sigma = symbols(r"\sigma")

        _e = {
            sigma: "F/A_load" | pc.parse_expr
        }

        _v = {k: v | pc.subs(_p | _e) | pc.N for k, v in _e.items()}

        # Demonstrate idiomatic usage pattern
        show_eqn([_p|_e, _v])
        ```

        ```{python}
        # Include practical tips and configuration
        from keecas import config
        from IPython.display import display

        # tip: use display() for mid-cell output
        config.some_setting = True

        display(function_name(_p, special_option=True))
        ```

        ```{python}
        # Advanced usage or edge cases
        custom_config = {
            "key": "value",
            ...
        }

        # Demonstrate powerful feature
        function_name(_p, config=custom_config)
        ```

    See Also:
        - related_function(): Brief description of relationship
        - config.section.setting: Brief description of config option
        - AnotherClass: Brief description of related class

    Notes:
        - Configuration behavior details and defaults
        - Compatibility considerations (e.g., KaTeX mode, cross-platform)
        - Common usage patterns and workflows
        - Cross-references to config settings that affect behavior
        - Performance considerations if relevant
    """
```

---

## Common Mistakes to Avoid

### 1. Using Unicode Symbols
❌ **Wrong**: `Le (≤): LessThan`
✅ **Right**: `Le: LessThan (less than or equal)`

### 2. Vague Parameter Descriptions
❌ **Wrong**: `sep: Separator for columns`
✅ **Right**: `sep: Separator goes in between each column, so first separator is between first and second column, etc`

### 3. Missing Raw String Prefix
❌ **Wrong**: `"""Display equations...\n\n    \\sigma = symbols(r"\\sigma")"""`
✅ **Right**: `r"""Display equations...\n\n    \sigma = symbols(r"\sigma")"""`

### 4. Non-Idiomatic Examples
❌ **Wrong**: `show_eqn([_p, _e, _v])`
✅ **Right**: `show_eqn([_p|_e, _v])`

### 5. Single-Line Dicts and Missing Trailing Commas
❌ **Wrong**: `_p = {F: 100*u.kN, A: 20*u.cm**2}`
❌ **Wrong**:
```python
_p = {
    F: 100*u.kN,
    A_load: 20*u.cm**2  # Missing trailing comma
}
```
✅ **Right**:
```python
_p = {
    F: 100*u.kN,
    A_load: 20*u.cm**2,  # Trailing comma required
}
```

**Note**: Always include trailing commas in multi-line collections (dicts, lists, tuples). This applies to:
- All code examples in docstrings
- Function arguments spanning multiple lines
- Dict/list definitions

Trailing commas ensure cleaner git diffs and prevent syntax errors when reordering items.

### 6. Incorrect Variable Naming
❌ **Wrong**: Using `_v` for both parameters and values
✅ **Right**: `_p` for parameters, `_e` for expressions, `_v` for values, `_c` for checks

### 7. Missing Workflow Integration
❌ **Wrong**: Only showing standalone function calls
✅ **Right**: Showing how function integrates with `show_eqn()` and typical workflows

### 8. Incomplete Type Descriptions
❌ **Wrong**: `col_wrap: Can be str, dict, list, Dataframe, or tuple`
✅ **Right**: `col_wrap: List elements can be None (no wrapping), str (prefix only), tuple (prefix, suffix), or Callable`

### 9. Missing Practical Tips
❌ **Wrong**: No mention of `display()`, `config.print_label`, or `hash()` techniques
✅ **Right**: Including workflow tips in examples and notes

### 10. Misleading Comments
❌ **Wrong**: `# Per-symbol float format`
✅ **Right**: `# applied to all elements in the row` and `# per cell formatting`

---

## Application Scope

**All docstrings for API reference functions must follow these guidelines.**

This includes:
- `show_eqn()` - Main display function
- `check()` - Verification function
- `Dataframe` class - Core data structure
- All exported functions in `__init__.py`
- Configuration-related functions
- Utility functions in the public API

**Guidelines will be updated incrementally as new patterns and issues arise during development.**

---

## References

- Based on analysis from `_todo/proposal/docstring-guidelines.md`
- Lessons learned from display.py docstring corrections (commit d7f0c22 to current)
- Project conventions documented in CLAUDE.md
- Google Python Style Guide: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
- Quartodoc documentation: https://machow.github.io/quartodoc/
