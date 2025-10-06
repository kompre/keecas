# Programmatic API Documentation with Quarto Autodoc

## Original Objective
Update documentation and API reference programmatically using Quarto autodoc to prevent falling out of sync. No manual labor required - documentation should be automatically generated from source code.

## Context
- Current documentation: Manual `.qmd` files in `docs/` directory
- Existing API docs: `docs/api-reference/display.qmd` (manually maintained)
- Documentation system: Quarto-based, deployed via GitHub Actions
- Workflow: `.github/workflows/docs.yml`
- Current docs are partially outdated
- Preparing for v1.0.0 release

## Problem Statement

**Current issues**:
1. API documentation manually written and outdated
2. Function signatures change but docs don't update
3. Docstrings in code don't match published docs
4. No automated sync between code and documentation
5. High maintenance burden for documentation updates

**Solution**: Use `quartodoc` to automatically generate API reference from Python docstrings.

## Implementation Plan

### 1. Install and Configure Quartodoc

**Dependency addition**:
```toml
# Add to pyproject.toml [dependency-groups.dev]
"quartodoc>=0.7.0",
"griffe>=0.36.0",  # Quartodoc's AST parser
```

**Installation**:
```bash
uv add --dev quartodoc griffe
```

### 2. Create Quartodoc Configuration

**File**: `docs/_quarto.yml` (update existing)

**Add quartodoc configuration**:
```yaml
project:
  type: website

quartodoc:
  # Package to document
  package: keecas

  # Output directory for generated API docs
  dir: api-reference

  # Sidebar configuration
  sidebar: api-reference/_sidebar.yml

  # Rendering options
  renderer:
    style: markdown
    show_signature: true
    show_signature_annotations: true

  # Default options for code cells in examples
  options:
    echo: true

  # Documentation structure
  sections:
    - title: Display Module
      desc: LaTeX equation rendering and formatting
      contents:
        - name: show_eqn
          members: []
        - name: config
          members:
            - KeecasConfig.save
            - KeecasConfig.load
            - KeecasConfig.reset
            - KeecasConfig.to_dict
        - name: check
          members: []
        - name: dict_to_eq
          members: []
        - name: eq_to_dict
          members: []

    - title: Dataframe Module
      desc: Data container for tabular equation structures
      contents:
        - name: Dataframe
          members:
            - Dataframe.append
            - Dataframe.extend
            - Dataframe.merge
            - Dataframe.to_dict

    - title: Pipe Commands
      desc: Functional composition for mathematical operations
      contents:
        - name: pipe_command.subs
          members: []
        - name: pipe_command.N
          members: []
        - name: pipe_command.convert_to
          members: []
        - name: pipe_command.doit
          members: []
        - name: pipe_command.parse_expr
          members: []
        - name: pipe_command.quantity_simplify
          members: []

    - title: Configuration System
      desc: Configuration management and localization
      contents:
        - name: config.KeecasConfig
          members:
            - KeecasConfig.save
            - KeecasConfig.load
            - KeecasConfig.reset
            - KeecasConfig.show
        - name: config.EnvironmentManager
          members:
            - EnvironmentManager.get
            - EnvironmentManager.set
            - EnvironmentManager.list_environments

    - title: Pint-SymPy Bridge
      desc: Unit conversion and symbolic math integration
      contents:
        - name: pint_sympy.unitregistry
          members: []
        - name: pint_sympy.update_pint_locale
          members: []

    - title: CLI Interface
      desc: Command-line tools
      contents:
        - name: cli.main
          members: []
        - name: cli.edit_command
          members: []
        - name: cli.config_command
          members: []

website:
  title: "Keecas Documentation"
  # ... rest of existing config
```

### 3. Improve Source Code Docstrings

**Current docstring quality**: Varies significantly across modules

**Target docstring format** (Google style):
```python
def show_eqn(
    data: dict | list[dict] | Dataframe,
    col_wrap: list | None = None,
    float_format: str | dict | list | Dataframe | tuple | None = None,
    environment: str | dict | EnvironmentDefinition = "align",
    env_arg: str | None = None,
    label: dict | None = None,
    debug: bool = False
) -> IPython.display.Markdown:
    """Display mathematical equations as formatted LaTeX.

    Converts Python dictionaries containing symbolic expressions into
    rendered LaTeX equations suitable for Jupyter notebooks and Quarto
    documents.

    Args:
        data: Equation data as dict or list of dicts mapping LHS symbols
            to RHS expressions. Can also accept Dataframe objects.
        col_wrap: Column wrapping specifications for LaTeX formatting.
            List of wrappers where each element can be:
            - None: no wrapping
            - str: prefix (e.g., "=" or "&")
            - tuple: (prefix, suffix) pair
        float_format: Format specification for numerical values. Can be:
            - str: Applied to all floats (e.g., ".3f")
            - dict: Per-symbol formatting {symbol: format_spec}
            - list/Dataframe/tuple: Structured per-column formatting
        environment: LaTeX environment name or custom definition:
            - Built-in: "align", "equation", "cases", "gather", etc.
            - Custom: dict with separator, line_separator, etc.
        env_arg: Optional environment argument (e.g., "{2}" for alignat)
        label: Dictionary mapping symbols to label strings for
            cross-referencing. Labels formatted as {eq_prefix}{label}.
        debug: If True, display generated LaTeX source code

    Returns:
        IPython.display.Markdown object containing rendered LaTeX

    Raises:
        ValueError: If data structure is invalid or symbols undefined
        KeyError: If referenced symbols not found in expressions

    Examples:
        ```{python}
        from keecas import symbols, u, pc, show_eqn

        # Basic parameter display
        F, A = symbols(r"F, A")
        _p = {F: 100*u.kN, A: 20*u.cm**2}
        show_eqn(_p)
        ```

        ```{python}
        # Multi-column with expressions and values
        sigma = symbols(r"\sigma")
        _e = {sigma: "F/A" | pc.parse_expr}
        _v = {sigma: 5*u.MPa}
        show_eqn([_p, _e, _v])
        ```

        ```{python}
        # Custom formatting and labels
        _l = {sigma: 'stress-calc'}
        show_eqn([_e, _v], float_format='.2f', label=_l)
        ```

    See Also:
        - check(): Engineering verification with localization
        - dict_to_eq(): Convert dict to SymPy equations
        - config: Global configuration object

    Notes:
        - Symbols are automatically sorted by dependency order
        - LaTeX output respects config.katex setting
        - Float formatting supports format specs with or without braces
        - Environment separator defaults to None (uses environment default)
    """
```

**Docstring improvement priorities**:
1. **High priority** (user-facing API):
   - `show_eqn()` - Most important function
   - `check()` - Engineering verification
   - `config` class and methods
   - `Dataframe` class and methods
   - Pipe commands (`pc.*`)

2. **Medium priority** (configuration):
   - CLI functions
   - Configuration helpers
   - Environment management

3. **Low priority** (internal):
   - Helper functions (already documented via main functions)
   - Internal utilities

### 4. Create Automation Script

**File**: `scripts/update_docs.py`

**Purpose**: Regenerate API docs before documentation build

```python
"""Update API documentation using quartodoc."""

import subprocess
import sys
from pathlib import Path

def update_api_docs():
    """Regenerate API reference from source code docstrings."""
    docs_dir = Path("docs")

    # Run quartodoc to generate API reference
    print("🔄 Generating API documentation...")
    result = subprocess.run(
        ["uv", "run", "quartodoc", "build", "--config", str(docs_dir / "_quarto.yml")],
        cwd=Path.cwd(),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("❌ API documentation generation failed:")
        print(result.stderr)
        sys.exit(1)

    print("✓ API documentation generated successfully")

    # Validate output
    api_dir = docs_dir / "api-reference"
    if not api_dir.exists():
        print(f"⚠️  Warning: API directory not created at {api_dir}")
        sys.exit(1)

    # Count generated files
    generated_files = list(api_dir.glob("*.qmd"))
    print(f"✓ Generated {len(generated_files)} API reference pages")

    return 0

if __name__ == "__main__":
    sys.exit(update_api_docs())
```

### 5. Update GitHub Actions Workflow

**File**: `.github/workflows/docs.yml` (modify existing)

**Add documentation generation step**:
```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.13'

    - name: Install uv
      uses: astral-sh/setup-uv@v1
      with:
        version: "latest"

    - name: Install Python dependencies
      run: |
        uv sync --group dev
        uv pip install -e .

    # NEW STEP: Generate API documentation
    - name: Generate API Documentation
      run: |
        python scripts/update_docs.py

    - name: Setup Quarto
      uses: quarto-dev/quarto-actions/setup@v2
      with:
        version: release

    - name: Configure Quarto Python environment
      run: |
        echo "QUARTO_PYTHON=$(uv run which python)" >> $GITHUB_ENV

    - name: Render Quarto Documentation
      run: |
        cd docs
        uv run quarto render

    # ... rest of workflow
```

### 6. Add Pre-commit Docstring Validation

**File**: `scripts/install-hooks.sh` (update existing)

**Add lightweight docstring check**:
```bash
#!/bin/bash

# ... existing hook setup ...

# Add docstring validation to pre-commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# ... existing Quarto example checks ...

# Check if Python source files changed
python_changed=$(git diff --cached --name-only --diff-filter=ACM | grep -E "^src/.*\.py$")

if [ -n "$python_changed" ]; then
    echo "Validating docstrings for changed Python files..."

    # Quick validation: check changed functions have docstrings
    python scripts/validate_docstrings.py --changed-only

    if [ $? -ne 0 ]; then
        echo "❌ Docstring validation failed"
        echo "Add docstrings to modified functions"
        echo "Tip: API docs are regenerated automatically in CI"
        exit 1
    fi
fi

# ... rest of hook ...
EOF
```

**Note**: API documentation regeneration happens only in CI, not on commit (too slow).

### 7. Update CLAUDE.md with Docstring Conventions

**File**: `CLAUDE.md` (update existing)

**Add section on docstring conventions**:
- Google-style docstring format (standard for quartodoc)
- Use Quarto executable code blocks `\`\`\`{python}` for examples (echo: true set globally in _quarto.yml)
- Show rendered output for user-facing functions (`show_eqn`, `check`, `pc.*`)
- Use `#| eval: false` only when examples shouldn't execute (imports fail, etc.)
- Type annotation requirements (use modern union syntax: `dict | list`)
- Cross-reference conventions
- Common sections: Args, Returns, Raises, Examples, See Also, Notes

**Example template**:
```python
def function_name(arg1: Type1, arg2: Type2 = default) -> ReturnType:
    """One-line summary of function purpose.

    Detailed description of function behavior, edge cases,
    and important implementation details.

    Args:
        arg1: Description of arg1 purpose and constraints
        arg2: Description of arg2, including default behavior

    Returns:
        Description of return value and its structure

    Raises:
        ValueError: Condition that triggers this exception
        TypeError: When invalid type provided

    Examples:
        ```{python}
        # Basic usage
        result = function_name(value1, value2)
        print(result)
        ```

        ```{python}
        # Advanced usage with options
        result = function_name(value1, arg2=custom_value)
        ```

    See Also:
        - related_function(): Brief description
        - AnotherClass: Related functionality

    Notes:
        - Important implementation detail 1
        - Important implementation detail 2
    """
```

**Note**: No separate style guide file created; keeps conventions centralized in CLAUDE.md.

<!-- no, write convention in docstrings.md, don't clutter claude.md (just reference file) -->

### 8. Integration Strategy for API Reference

**Current structure** (manual):
```
docs/api-reference/
├── index.qmd          # Manual overview
└── display.qmd        # Manual API docs
```

**Hybrid approach** (start small):
```
docs/api-reference/ (generated by quartodoc)
├── index.qmd          
├── show_eqn.qmd   # Generated from docstrings
├── check.qmd      # Generated from docstrings
│
```

**Integration plan**:
1. **Test with display.py first**: Generate docs for `show_eqn`, `check`, `config`
2. **Expand gradually**: Add dataframe, pipe_command, config modules fter validation

### 9. Add Lightweight Docstring Validation

**File**: `scripts/validate_docstrings.py`

**Simple validation** (for pre-commit):
```python
"""Validate changed files have docstrings."""

import ast
import subprocess
import sys
from pathlib import Path

def get_changed_files():
    """Get staged Python files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True
    )
    files = result.stdout.strip().split('\n')
    return [f for f in files if f.startswith('src/') and f.endswith('.py')]

def check_file_docstrings(filepath: Path) -> list[str]:
    """Check public functions/classes in file have docstrings."""
    missing = []

    with open(filepath) as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):  # Public API
                if not ast.get_docstring(node):
                    missing.append(node.name)

    return missing

def main():
    """Validate docstrings in changed files."""
    changed_files = get_changed_files()

    if not changed_files:
        sys.exit(0)

    has_errors = False
    for filepath in changed_files:
        path = Path(filepath)
        if not path.exists():
            continue

        missing = check_file_docstrings(path)
        if missing:
            print(f"⚠️  {filepath}: Missing docstrings for {', '.join(missing)}")
            has_errors = True

    if has_errors:
        print("\nTip: Add Google-style docstrings to public functions/classes")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

**Note**: Lightweight validation only - checks presence, not quality. Runs fast in pre-commit hook.

### 10. Update README with Documentation Links

**File**: `README.md` (add section)

```markdown
## Documentation

Comprehensive documentation is available at: https://kompre.github.io/keecas

- **Getting Started**: Installation, quickstart, configuration
- **User Guide**: Conventions, examples, Jupyter/Quarto integration
- **API Reference**: Complete API documentation (auto-generated from source)
- **CLI Reference**: Command-line tool documentation

### Building Documentation Locally

```bash
# Install documentation dependencies
uv sync --group dev

# Generate API reference
python scripts/update_docs.py

# Render documentation site
cd docs
uv run quarto preview
```

Documentation is automatically rebuilt on every push to `main` via GitHub Actions.


## Implementation Steps

1. **Add quartodoc dependency** to `pyproject.toml` using `uv add --dev quartodoc griffe`
2. **Configure quartodoc** in `docs/_quarto.yml` (start with display.py only)
3. **Improve docstrings** for display.py functions: `show_eqn()`, `check()`, `config` (use Quarto code blocks)
4. **Create update script** (`scripts/update_docs.py`)
5. **Test quartodoc output**: Generate docs for display.py, validate quality
6. **Create validation script** (`scripts/validate_docstrings.py`) - lightweight, pre-commit safe
7. **Update pre-commit hook** for docstring validation (not generation)
8. **Update GitHub Actions** to run documentation generation in CI
9. **Add docstring conventions** to DOCSTRINGS.md 
10. **Integrate into existing docs**: _quarto.yml file is already set up for displaying content generated byquartodoc in api-reference folder
11. **Update README** with documentation build instructions
12. **Expand to other modules** after display.py validation succeeds

## Acceptance Criteria

**Phase 1 (display.py)** - BLOCKED:
- ✅ Quartodoc dependency installed (`quartodoc>=0.7.0,<0.8.0`, `griffe<1.0.0`)
- ✅ `show_eqn()`, `check()` have complete Google-style docstrings with Quarto code blocks
- ✅ Config module documented with comprehensive module-level docstring
- ✅ `scripts/update_docs.py` automation script created
- ❌ **BLOCKER**: Quartodoc 0.7.6 has renderer bug (`UnboundLocalError` in md_renderer.py:446)
  - Error occurs when rendering function signatures with certain parameter types
  - Affects both `show_eqn()` and `check()` functions
  - Root cause: Bug in quartodoc 0.7.6's md_renderer when handling parameters
  - **Resolution options**:
    1. Wait for quartodoc 0.8+ release with fixes
    2. Use alternative tool (sphinx-autoapi, mkdocstrings)
    3. Keep manual documentation with improved docstrings
- ⏸️ Generated display.py docs embedded in manual pages (blocked)
- ⏸️ Quality comparable to existing manual documentation (blocked)

**Phase 2 (automation)** - ON HOLD:
- ⏸️ `scripts/validate_docstrings.py` validates changed files only
- ⏸️ Pre-commit hook runs lightweight validation (fast)
- ⏸️ CI regenerates API docs on every push
- ⏸️ Documentation builds successfully in CI

**Phase 3 (expansion)** - ON HOLD:
- ⏸️ Docstring conventions documented in CLAUDE.md
- ⏸️ README includes documentation build instructions
- ⏸️ Dataframe, pipe_command modules documented
- ⏸️ Configuration system documented
- ⏸️ All public API has docstrings

## Current Status (2025-10-06)

**Phase 1 (display.py) - COMPLETED**:
1. ✅ Quartodoc and griffe dependencies (`quartodoc>=0.7.0,<0.8.0`, `griffe<1.0.0`)
2. ✅ Comprehensive Google-style docstrings with Quarto executable examples
   - `show_eqn()`: Multi-column layouts, formatting, environments (102 lines generated)
   - `check()`: Engineering verification with localization (88 lines generated)
3. ✅ Config module documentation via comprehensive module-level docstring
4. ✅ Quartodoc configuration in `docs/_quarto.yml` with Google parser and warning suppression
5. ✅ Automation script `scripts/update_docs.py` working
6. ✅ Documentation successfully generated:
   - `docs/api-reference/_generated/show_eqn.qmd`
   - `docs/api-reference/_generated/check.qmd`
   - `docs/api-reference/_generated/dict_to_eq.qmd`
   - `docs/api-reference/_generated/eq_to_dict.qmd`
   - `docs/api-reference/_sidebar.yml`
7. ✅ GitHub Actions workflow updated to run API generation before rendering

**Phase 1.5 (Docstring Guidelines) - COMPLETED (2025-10-06)**:
1. ✅ Comprehensive docstring guidelines documented in `DOCSTRINGS.md`
   - 10 core guidelines based on real-world quartodoc rendering issues
   - Complete template for Google-style docstrings
   - Common mistakes section with before/after examples
   - Tutorial-quality example standards
2. ✅ Guidelines address all issues found during Phase 1:
   - Type annotations matching runtime behavior (not just type checker)
   - ASCII-only documentation text (no unicode symbols)
   - Raw string prefix requirements for LaTeX examples
   - Four-element function descriptions (what/why/how/warning)
   - Operational parameter descriptions with behavioral details
   - Project convention-following examples (_p, _e, _v patterns)
   - Tutorial-quality progressive complexity
   - Practical workflow tips and integration examples
   - Essential Notes section covering config and compatibility
3. ✅ Guidelines cover all API reference scope:
   - Main functions: `show_eqn()`, `check()`
   - Data structures: `Dataframe` class
   - Configuration functions
   - Utility functions in public API
4. ✅ Reference implementation completed:
   - `show_eqn()` and `check()` docstrings follow all 10 guidelines
   - Examples demonstrate idiomatic keecas usage
   - Integration with typical workflows shown

**Blockers Resolved**:
1. Missing type annotation on `check()` test parameter → Fixed: `test: type = Le`
2. Unicode symbols in docstrings (Windows cp1252 encoding) → Fixed: Replaced ≤,≥ with <=,>=
3. Docstring parser mismatch → Fixed: Added `parser: google` to quartodoc config
4. Rendered warnings → Fixed: Added `warning: false` to execute section
5. Vague parameter descriptions → Fixed: Added operational details and behavioral explanations
6. Missing workflow integration → Fixed: Added tutorial-quality examples with check() integration
7. Type annotations suggesting incorrect usage → Fixed: Use `Any` when behavioral requirements matter

**Known Limitations**:
1. ⚠️ Quartodoc 0.7.6 renderer bug prevents documenting:
   - Dataframe class and methods (UnboundLocalError in md_renderer.py:446)
   - Pipe command functions (parameter rendering issues)
   - Complex type signatures with certain parameter types
2. ℹ️ Currently documenting only `display` module functions that work
3. ℹ️ Full module expansion blocked until quartodoc 0.8+ or alternative tool

**Phase 2 (Automation) - COMPLETED (2025-10-06)**:
1. ✅ Created `scripts/validate_docstrings.py` for pre-commit validation
   - Lightweight AST-based validation (fast for pre-commit)
   - Checks presence of docstrings on public functions/classes
   - Skips private API (names starting with _)
   - Exit code 0 on success, 1 on missing docstrings
2. ✅ Updated pre-commit hook (`scripts/pre-commit`)
   - Added docstring validation before notebook processing
   - Validates only staged Python files in src/
   - Provides helpful error messages with DOCSTRINGS.md reference
   - Can be skipped with `git commit --no-verify`
3. ✅ Updated install-hooks.sh documentation
   - Added docstring validation to hook description
4. ✅ Fixed CI pipeline (`/.github/workflows/docs.yml`)
   - Changed `python` to `uv run python` for consistency
   - API generation already integrated in Phase 1
5. ✅ Tested validation script
   - Correctly detects missing docstrings
   - Passes when all public API has docstrings
   - Exit codes work correctly for pre-commit integration

**Next Phase - Phase 3 (Expansion)**:
- ⏸️ Expand to other modules (blocked by quartodoc renderer bug)
- 🔄 Monitor quartodoc releases for bug fixes
- ⏸️ Document remaining modules once quartodoc supports them

## Dependencies
- None (standalone task)
- Complements v1.0.0 release preparation

## Estimated Effort

**Phase 1 (display.py)**:
- Quartodoc setup and configuration: 2 hours
- Docstring improvements for display.py: 3 hours
- Initial generation and testing: 1 hour
- **Subtotal**: 6 hours

**Phase 2 (automation)**:
- Update script (`update_docs.py`): 1 hour
- Validation script (`validate_docstrings.py`): 1 hour
- Pre-commit hook update: 0.5 hour
- GitHub Actions integration: 1 hour
- **Subtotal**: 3.5 hours

**Phase 3 (expansion)**:
- README updates: 0.5 hour
- Remaining modules docstrings: 4 hours
- Testing and refinement: 2 hours
- **Subtotal**: 7 hours

**Total**: 16.5 hours (phased approach allows early validation)

## Risks and Mitigations

**Risk**: Quartodoc doesn't handle dynamic attributes (like `config` object)
**Mitigation**: May need manual documentation for dynamic APIs; test early with display.py

**Risk**: Pipe decorators confuse quartodoc parsing
**Mitigation**: Test pipe_command.py early; consider separate manual docs if needed

**Risk**: Generated docs lower quality than manual
**Mitigation**: Phased approach allows quality comparison before full migration

**Risk**: Pre-commit hook slows down commits
**Mitigation**: Lightweight validation only (presence check), no generation in pre-commit

**Risk**: Quartodoc config structure incorrect
**Mitigation**: Start with minimal config for display.py, validate before expanding

**Risk**: Breaking changes to quartodoc API
**Mitigation**: Pin version `quartodoc>=0.7.0,<0.8.0`

**Risk**: Quarto code block examples don't render correctly
**Mitigation**: Test with actual Quarto rendering, not just generation

## Future Enhancements

- Add type stub files (`.pyi`) for better IDE support
- Include complexity metrics in documentation
- Generate usage statistics (function call graphs)
- Add interactive examples with nbconvert
- Cross-reference examples from test suite
- Generate changelog from commit messages

## Notes

- Quartodoc uses griffe for static analysis (no code execution required)
- Supports Google, NumPy, and Sphinx docstring styles (keecas uses Google)
- `echo: true` set globally in `_quarto.yml` - all code blocks show code by default
- Use `#| eval: false` only for examples that can't execute (import issues, etc.)
- User-facing functions should show actual rendered output (equations, checks, conversions)
- Phased implementation reduces risk: display.py first, expand after validation
- Pre-commit validation is lightweight (fast), API generation happens in CI only
- Dynamic attributes (config object) may require manual documentation