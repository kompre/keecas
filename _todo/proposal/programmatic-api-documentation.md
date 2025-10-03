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
        Basic parameter display:
        >>> F, A = symbols(r"F, A")
        >>> _p = {F: 100*u.kN, A: 20*u.cm**2}
        >>> show_eqn(_p)

        Multi-column with expressions and values:
        >>> sigma = symbols(r"\\sigma")
        >>> _e = {sigma: "F/A" | pc.parse_expr}
        >>> _v = {sigma: 5*u.MPa}
        >>> show_eqn([_p, _e, _v])

        Custom formatting and labels:
        >>> _l = {sigma: 'stress-calc'}
        >>> show_eqn([_e, _v], float_format='.2f', label=_l)

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

### 6. Add Pre-commit Hook for Documentation

**File**: `scripts/install-hooks.sh` (update existing)

**Add documentation check**:
```bash
#!/bin/bash

# ... existing hook setup ...

# Add documentation generation to pre-commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# ... existing Quarto example checks ...

# Check if Python source files changed
python_changed=$(git diff --cached --name-only --diff-filter=ACM | grep -E "^src/.*\.py$")

if [ -n "$python_changed" ]; then
    echo "Python source files changed, updating API documentation..."

    # Generate API docs
    python scripts/update_docs.py

    if [ $? -ne 0 ]; then
        echo "❌ API documentation generation failed"
        echo "Fix docstrings and try again"
        exit 1
    fi

    # Stage generated API docs
    git add docs/api-reference/*.qmd docs/api-reference/_sidebar.yml
fi

# ... rest of hook ...
EOF
```

### 7. Create Documentation Style Guide

**File**: `docs/contributing/docstring-style-guide.md`

**Content**:
- Google-style docstring format (standard for quartodoc)
- Examples for functions, classes, methods
- Type annotation requirements
- Cross-reference conventions
- Code example formatting
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
        Basic usage:
        >>> result = function_name(value1, value2)
        >>> print(result)
        expected output

        Advanced usage with options:
        >>> result = function_name(value1, arg2=custom_value)

    See Also:
        - related_function(): Brief description
        - AnotherClass: Related functionality

    Notes:
        - Important implementation detail 1
        - Important implementation detail 2
    """
```

### 8. Restructure API Reference Pages

**Current structure** (manual):
```
docs/api-reference/
├── index.qmd          # Manual overview
└── display.qmd        # Manual API docs
```

**New structure** (automated):
```
docs/api-reference/
├── index.qmd          # Manual overview (keep)
├── _sidebar.yml       # Generated by quartodoc
├── show_eqn.qmd       # Generated from docstrings
├── config.qmd         # Generated from docstrings
├── check.qmd          # Generated from docstrings
├── Dataframe.qmd      # Generated from docstrings
├── pipe_command.qmd   # Generated from docstrings
└── ...                # Other generated pages
```

**Migration plan**:
1. Keep `index.qmd` as manual overview/landing page
2. Delete old manual API pages after verification
3. Let quartodoc generate individual function/class pages
4. Update navigation links to point to generated pages

### 9. Add Documentation Validation

**File**: `scripts/validate_docs.py`

**Validation checks**:
```python
"""Validate documentation completeness and quality."""

import ast
import sys
from pathlib import Path
from typing import List, Tuple

def check_docstrings() -> List[Tuple[str, str]]:
    """Check all public functions have docstrings."""
    missing = []

    src_dir = Path("src/keecas")
    for py_file in src_dir.rglob("*.py"):
        if py_file.name.startswith("_") and py_file.name != "__init__.py":
            continue

        with open(py_file) as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):  # Public API
                    if not ast.get_docstring(node):
                        missing.append((str(py_file), node.name))

    return missing

def validate():
    """Run all documentation validation checks."""
    print("🔍 Validating documentation...")

    # Check for missing docstrings
    missing = check_docstrings()
    if missing:
        print(f"⚠️  Found {len(missing)} functions/classes without docstrings:")
        for filepath, name in missing[:10]:  # Show first 10
            print(f"   - {filepath}::{name}")
        if len(missing) > 10:
            print(f"   ... and {len(missing) - 10} more")
    else:
        print("✓ All public functions have docstrings")

    # Check API docs were generated
    api_dir = Path("docs/api-reference")
    generated_files = list(api_dir.glob("*.qmd"))
    if len(generated_files) < 5:  # Expect at least 5 major API pages
        print(f"⚠️  Only {len(generated_files)} API pages generated (expected >5)")
        return 1

    print(f"✓ Generated {len(generated_files)} API reference pages")
    return 0

if __name__ == "__main__":
    sys.exit(validate())
```

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
```

## Implementation Steps

1. **Add quartodoc dependency** to `pyproject.toml`
2. **Configure quartodoc** in `docs/_quarto.yml`
3. **Improve docstrings** for high-priority functions (show_eqn, check, config, Dataframe)
4. **Create update script** (`scripts/update_docs.py`)
5. **Update GitHub Actions** to run documentation generation
6. **Add pre-commit hook** for documentation validation
7. **Write style guide** for contributors
8. **Validate and test** generated documentation
9. **Update README** with documentation links
10. **Delete old manual API pages** after verification

## Acceptance Criteria

- ✅ Quartodoc configured and working
- ✅ API reference auto-generated from docstrings
- ✅ All high-priority functions have complete docstrings
- ✅ Documentation builds successfully in CI
- ✅ Generated docs match manual docs in quality
- ✅ Pre-commit hook validates documentation
- ✅ Style guide available for contributors
- ✅ Validation script checks docstring coverage
- ✅ README links to published documentation
- ✅ No manual API documentation remains

## Dependencies
- None (standalone task)
- Complements v1.0.0 release preparation

## Estimated Effort
- Quartodoc setup: 2 hours
- Docstring improvements: 6 hours (largest effort)
- Automation scripts: 2 hours
- GitHub Actions update: 1 hour
- Style guide: 1 hour
- Testing and validation: 2 hours
- **Total**: 14 hours

## Risks and Mitigations

**Risk**: Quartodoc doesn't support complex type annotations
**Mitigation**: Simplify type hints or use string annotations

**Risk**: Generated docs are low quality
**Mitigation**: Invest in high-quality docstrings upfront, use examples extensively

**Risk**: Build failures due to import errors
**Mitigation**: Quartodoc uses static analysis (griffe), doesn't import code

**Risk**: Breaking changes to quartodoc API
**Mitigation**: Pin version, test before upgrades

**Risk**: Docstring format incompatibility
**Mitigation**: Use standard Google-style, well-supported by quartodoc

## Future Enhancements

- Add type stub files (`.pyi`) for better IDE support
- Include complexity metrics in documentation
- Generate usage statistics (function call graphs)
- Add interactive examples with nbconvert
- Cross-reference examples from test suite
- Generate changelog from commit messages

## Notes

- Quartodoc uses griffe for static analysis (no code execution)
- Supports Google, NumPy, and Sphinx docstring styles (use Google)
- Can include inherited members from parent classes
- Supports cross-references with `:func:`, `:class:` syntax
- Generated sidebar integrates with Quarto navigation
- Existing manual overview pages can coexist with generated API pages
