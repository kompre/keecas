# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important: Unicode in Code and Documentation

**NEVER use Unicode special characters in Python code, comments, or docstrings.**

This includes:
- **Arrows**: Use `->` instead of `→`
- **Checkmarks**: Use `[exists]`/`[missing]` instead of `✓`/`✗`
- **Any non-ASCII symbols** in code documentation

**Why**: Windows uses the `charmap` codec by default which cannot encode many Unicode characters. This causes:
- `UnicodeEncodeError` when building documentation with quartodoc
- Terminal encoding errors when running CLI tools
- Inconsistent behavior across platforms

**Where it's OK**: Unicode is fine in:
- LaTeX strings (e.g., `r"\sigma"` for Greek letters)
- Code examples in docstrings where LaTeX is expected
- Output messages displayed through proper encoding

**Rule**: If it goes in a docstring, comment, or print statement - use ASCII only.

## Project Overview

`keecas` is a Python module for symbolic and units-aware calculations in Jupyter notebooks, specifically designed for Quarto rendered PDF documents. It combines `sympy` (symbolic math), `pint` (units), and `pipe` (functional programming) to provide a streamlined interface for mathematical computations with LaTeX output.

## Development Commands

### Documentation
For guidelines on writing API documentation with Google-style docstrings for quartodoc:
- See **[_docs/DOCSTRINGS.md](_docs/DOCSTRINGS.md)** for comprehensive guidelines and templates
- All API reference functions must follow these standards
- Examples should be tutorial-quality and demonstrate idiomatic usage

#### Docstring Formatting Standards

**Style**: Google-style docstrings (enforced by quartodoc and Ruff)

**Automatic Formatting**:
- Code examples in docstrings are automatically formatted by Ruff
- Use `{python}` fenced code blocks for Examples sections
- Ruff respects the 100-character line length for code examples

**Line Length Guidelines**:
- **Prose descriptions**: Aim for ~88 characters per line for readability
- **Code examples**: Automatically formatted (max 100 chars)
- **Long parameter descriptions**: Use multi-line format with continuation indent

**Code Examples in Docstrings**:
- Each example should demonstrate one clear concept
- Inline comments indicate expected output: `function_call()  # Returns: output`
- Type hints NOT required in docstring examples (lighter linting)
- Trailing commas optional in examples (focus on clarity over style)

**Example Format**:
```python
"""Function description.

Args:
    param: Short description that fits on one line.
    long_param: Longer description that needs wrapping.

        Continue with proper 4-space indent. Can use multiple paragraphs
        for complex parameters. Break at logical points (clauses, lists).

Returns:
    Description of return value.

Examples:
    ```{python}
    from keecas import symbols

    # Simple example
    result = function(arg)  # Returns: expected_output
    ```
"""
```

**Important**: Always follow ASCII-only rule (see "Important: Unicode in Code and Documentation").

### Testing
```bash
pytest
# or with uv:
uv run pytest
```

### CLI Interface
The project includes a comprehensive CLI for configuration management and Jupyter integration:
```bash
# Show version
keecas --version

# Jupyter development environment with templates
keecas edit [file] [--template TEMPLATE] [--port PORT] [--dir DIR] [--no-browser] [--token TOKEN] [--no-lab] [--list-templates] [--temp]

# Configuration management
keecas config init [--global|--local] [--force]     # Initialize config
keecas config edit [--global|--local]               # Edit with terminal editor
keecas config open [--global|--local]               # Open with system editor
keecas config show [--global|--local]               # Show configuration
keecas config path [--global|--local]               # Show config file paths
keecas config reset [--global|--local] [--force]    # Reset to defaults
```

**Terminal Output Features:**
- Displays session URL and direct notebook links for easy access/recovery
- Browser mode: Shows URLs after launching browser (single tab opens)
- No-browser mode: Provides copy-pasteable URLs for manual access
- Temporary sessions (`--temp`) include cleanup notice

### Building
The project uses `uv` as the build backend. To build:
```bash
uv build
```

### Installation in Development Mode
```bash
uv add keecas
# or for development with dependencies
pip install -e ".[dev]"
```

### Dependency Management
The project uses `uv.lock` for dependency locking. Install dependencies with:
```bash
uv sync
```

## CI/CD and Release Process

### Branch Protection
- **main**: Protected, requires PR + passing tests via GitHub Actions
- **dev**: Unprotected, allows rapid iteration
- **Feature branches**: Branch from dev, merge back to dev for collaboration
- **Release flow**: dev → main (via PR) → automated release

### Release Process

**Creating a release** (maintainers only):

1. **Bump version** on dev branch:
   ```bash
   git checkout dev
   uv version --bump major  # or minor, patch
   git commit -am "chore: bump version to X.Y.Z"
   git push origin dev
   ```

2. **Create PR from dev to main**:
   ```bash
   gh pr create --base main --title "Release vX.Y.Z" --label release
   ```
   - Use `--label test-release` for TestPyPI testing
   - Add release notes in PR description

3. **Merge PR**:
   - Tests run automatically on PR
   - Branch protection requires passing tests
   - Merge when approved and tests pass

4. **Automated workflow handles**:
   - Runs tests on merged code
   - Creates git tag (vX.Y.Z)
   - Builds package
   - Publishes to PyPI or TestPyPI (based on label)
   - Creates GitHub Release with PR notes

**Version targeting**:
- `release` label → Production PyPI
- `test-release` label → TestPyPI
- Pre-release versions (rc, alpha, beta, dev) automatically route to TestPyPI

### CI Workflows

**lint-fix.yml** - Runs on push to dev/feature branches and PRs to dev:
- Auto-fixes linting issues in `src/` and `tests/` only (Ruff check --fix + format)
- Commits fixes automatically if any are found ([skip ci] to avoid loops)
- Verifies linting passes after auto-fix
- **Important**: Runs BEFORE test.yml, ensuring clean code for testing
- **Scope**: Runs on dev, feature/** branches, and PRs to dev only
- **Excluded**: Does NOT run on PRs to main (test.yml already verifies linting) or push to main (protected branch)
- **Files**: Only lints production code (`src/`) and tests (`tests/`), not examples or templates

**test.yml** - Runs on PR to main/dev when code paths change:
- **Path filtering**: Only runs when these paths change:
  - `src/**` - Source code
  - `tests/**` - Test files
  - `pyproject.toml`, `uv.lock` - Dependencies
  - `.python-version` - Python version
  - `.github/workflows/**` - CI workflows
  - `scripts/**` - Build/validation scripts
- **Skipped**: Documentation-only changes (docs PRs can merge immediately)
- Linting verification (Ruff check - read-only)
- Tests (pytest)
- Docstring validation
- Caches uv dependencies for speed
- Cancels stale runs on new commits

**release.yml** - Runs on PR merge to main with release label:
- Tests before building
- Extracts version from pyproject.toml
- Determines publish target (PyPI/TestPyPI)
- Creates and pushes git tag
- Builds package with uv
- Publishes via PyPI Trusted Publishing (OIDC, no API tokens)
- Creates GitHub Release with PR notes and changelog

**docs.yml** - Runs on push to main:
- Generates API documentation with quartodoc
- Renders Quarto documentation
- Deploys to GitHub Pages (root path)
- Only triggered on main branch (dev branch docs not deployed)

### Developer Workflow

**Local development**:
```bash
# Create feature branch from dev
git checkout dev
git checkout -b feature/your-feature

# Make changes, commit (pre-commit hooks run automatically)
git commit -am "feat: your feature"

# Push and create PR to dev
git push -u origin feature/your-feature
gh pr create --base dev
```

**Pre-commit hooks** (installed via `scripts/install-hooks.sh`):
- Auto-fix linting issues with Ruff (check + format)
- Validate docstrings (fast check, < 1s)
- Render Quarto notebooks (for `examples/quarto_example/`)
- Can be skipped with `git commit --no-verify`
- **Note**: Tests only run in CI, not pre-commit (for speed)

**Two-layer linting strategy**:
- **Layer 1 (Local)**: Pre-commit hook auto-fixes 95% of linting issues before push
- **Layer 2 (CI)**: `lint-fix.yml` workflow catches remaining 5% (e.g., Claude GitHub Action sessions)
- **Result**: Zero-friction linting with no sync issues (fixes always on feature branches)
- **When to pull**: After CI auto-commits fixes, just `git pull` the branch before continuing work

### PR Workflow Examples

**Documentation changes**:
```bash
git checkout -b docs/update-guide
# Edit docs/guide.qmd or README.md
git commit -am "docs: update getting started guide"
gh pr create --base main
```
- No tests run (docs paths excluded)
- Can merge immediately to main
- docs.yml deploys after merge to main

**Code changes**:
```bash
git checkout -b fix/bug
# Edit src/keecas/display.py
git commit -am "fix: resolve display bug"
gh pr create --base main
```
- test.yml runs and must pass
- Includes linting verification
- Cannot merge until tests pass

**Dependency updates**:
```bash
git checkout -b chore/update-deps
uv add --dev pytest-cov
git commit -am "chore: add pytest-cov"
gh pr create --base main
```
- test.yml runs (pyproject.toml + uv.lock changed)
- Must pass before merge (critical for dependency changes)

**Releases**:
```bash
git checkout -b release/v1.1.0
uv version --bump minor
git commit -am "chore: bump version to 1.1.0"
gh pr create --base main --label release
```
- test.yml runs (pyproject.toml changed)
- check-release-version.yml runs (release label)
- Both must pass before merge
- After merge: release.yml tags, builds, publishes to PyPI

## Architecture Overview

### Core Components

1. **Display Module** (`src/keecas/display.py`)
   - Central component for LaTeX equation rendering
   - `show_eqn()`: Main function that converts Python dicts to LaTeX amsmath environments
   - `config` object: Global configuration for equation formatting (unified TOML-based system)
   - `check()`: Verification function with configurable templates for engineering calculations
   - **Environment System**: Template-based configuration for LaTeX environments
     - Dot notation access: `config.latex.environments.align.separator`
     - Built-in: align, alignat, cases, equation, gather, rcases, split (7 total)
     - User-extensible via `.keecas/config.toml` or `config.latex.environments.set()`
     - Inline definitions: Pass dict or `EnvironmentDefinition` to `show_eqn()`
     - Environment arguments support: `show_eqn(..., env_arg="{2}")` for alignat, etc.
     - Auto-generated config docs: `keecas config init` includes comprehensive examples
   - Handles float formatting, column wrapping, and cross-referencing

2. **Dataframe Module** (`src/keecas/dataframe.py`)
   - Custom dict-like class for tabular data with consistent row length
   - Supports operations like append, extend, and merging
   - Used internally by `show_eqn()` for handling multiple equation dictionaries
   - **LaTeX Context**: Keys represent row labels in LaTeX amsmath align blocks, values are lists that populate columns across each row
   - **Terminology**: Use "sequence" instead of "column" when describing input data to avoid confusion with LaTeX output columns

3. **Formatters Module** (`src/keecas/formatters.py`)
   - **Singledispatch-based** formatter system for converting values to LaTeX strings
   - **Main Entry Point**: `format_value(value, col_index, **kwargs)` - type-based dispatch to specialized formatters
   - **Pure Type Conversion**: Formatters convert Python values to LaTeX strings without decoration (no `= ` or `\quad` prefixes)
   - **Built-in Formatters**:
     - `format_str`: Python strings -> `\text{...}`
     - `format_int`: Integers -> LaTeX string
     - `format_float`: Floats -> LaTeX string (precision handled by `format_decimal_numbers()` in display.py)
     - `format_sympy`: SymPy expressions -> LaTeX via `sympy.latex()`
     - `format_mul`: Mul expressions with numeric/unit separation transformation
     - `format_pint`: Pint Quantity -> SymPy -> format_sympy (transformer)
     - `format_markdown`: IPython Markdown objects -> `\text{...}`
   - **Extensibility**: Users can register custom formatters with `@format_value.register(MyType)`
   - **Transformers**: format_pint and format_mul transform values then call format_sympy directly
   - **Separation of Concerns**: Formatters handle "what" (type conversion), col_wrapper handles "how" (presentation)

4. **Column Wrappers Module** (`src/keecas/col_wrappers.py`)
   - **Singledispatch-based** wrapper system for decorating columns with prefix/suffix
   - **Main Entry Point**: `wrap_column(value, col_index)` - returns `(prefix, suffix)` tuple
   - **Default Behavior**:
     - Numeric types (int, float, SymPy, Pint): `"= "` prefix for RHS columns (col_index > 0)
     - Text types (str, Markdown, Latex): `r"\quad"` prefix for RHS columns
     - LHS columns (col_index == 0): No wrapping for all types
   - **User Extensibility**:
     - Register custom wrappers: `@wrap_column.register(MyType)`
     - List form: `col_wrap=[None, "= ", r"\leq "]`
     - Callable form: Custom wrapper function with logic
     - Dict form: Type-based wrapping dictionary
   - **Use Cases**: Comparison operators (`=`, `\leq`, `\geq`, `\approx`), custom decorations
   - **Separation of Concerns**: Handles all "between LHS and RHS" syntax decoration

5. **Pipe Commands** (`src/keecas/pipe_command.py`)
   - Wraps common SymPy functions as `@Pipe` decorators for functional composition
   - Key functions: `subs`, `N`, `convert_to`, `doit`, `parse_expr`, `quantity_simplify`
   - Enables chain operations like `expr | pc.subs(vals) | pc.convert_to(units) | pc.N`

6. **Pint-SymPy Bridge** (`src/keecas/pint_sympy.py`)
   - Integrates Pint unit registry with SymPy symbolic expressions
   - Provides `unitregistry as u` for unit definitions
   - `update_pint_locale()`: Function for manual locale control
   - **Locale Support**: Automatic locale management for international unit formatting
   - **Language Integration**: 5 fully supported languages (de, es, fr, it, pt) with English fallback for others
   - **Conservative Behavior**: Intelligent locale switching that preserves system defaults

7. **Configuration System** (`src/keecas/config.py`)
   - **Unified TOML Configuration**: `.keecas/config.toml` files for global and local settings
   - **Hierarchical Priority**: Local > Global > Defaults
   - **Dynamic Propagation**: Configuration changes automatically update Pint locale and localization
   - **CLI Integration**: Full command-line interface for configuration management

8. **CLI Interface** (`src/keecas/cli.py`)
   - **Cross-platform Configuration Management**: Edit configs with terminal or system editors
   - **Version Display**: Built-in version information and help
   - **Consistent Interface**: All commands support explicit `--global` and `--local` flags

9. **Localization System** (`src/keecas/localization/`)
   - **Multi-language Support**: 10 languages with domain-specific translations
   - **SymPy Integration**: Localized mathematical terms (Domain, Range, verification terms)
   - **Automatic Sync**: Language changes propagate to Pint unit formatting

### Key Design Patterns

- **Dictionary-Based Equations**: Mathematical equations are represented as dicts where keys are LHS symbols and values are RHS expressions
- **Pipe Functional Style**: Mathematical operations are chained using pipe operators (`|`)
- **Units Integration**: Seamless conversion between Pint quantities and SymPy units
- **LaTeX Generation**: Automatic conversion of symbolic expressions to formatted LaTeX output

### Module Imports Structure

The main `__init__.py` exposes:
- `Dataframe` class
- Display functions (`show_eqn`, `config`, `check`, `dict_to_eq`, `eq_to_dict`)
- Column wrapper (`wrap_column` - singledispatch for column decoration)
- Formatters (`format_value`, `format_str`, `format_int`, `format_float`, `format_sympy`, `format_mul`, and optional `format_pint`, `format_markdown`)
- Pipe commands as `pc` namespace
- Unit registry as `u` and `update_pint_locale` function
- Common SymPy symbols and functions (`symbols`, `latex`, `Eq`, `Le`, etc.)
- LaTeX printing utilities (`platex`)

## Keecas Usage Conventions

Keecas follows strict conventions to minimize boilerplate while maximizing expressiveness. **Always follow these patterns when working with keecas code.**

### Core Philosophy

Mathematical equations are mappings between LHS and RHS expressions. Use Python `dict` containers where:
- **Cell-local dicts** (prefixed with `_`): Live and die within a single cell for immediate display
- **Notebook-global dicts** (no prefix): Persist across cells for complex multi-step calculations

### Standard Dict Conventions

| Dict     | Purpose                     | Example                                                        |
| -------- | --------------------------- | -------------------------------------------------------------- |
| `_p`     | Cell-local parameters       | `_p = {F: 10*u.kN, A: 50*u.cm**2}`                             |
| `_e`     | Cell-local expressions      | `_e = {sigma: "F / A" \| pc.parse_expr}`                       |
| `_v`     | Cell-local evaluated values | `_v = {k: v \| pc.subs(_e\|_p) \| pc.N for k,v in _e.items()}` |
| `_d`     | Cell-local descriptions     | `_d = {F: "applied force", sigma: "stress"}`                   |
| `_l`     | Cell-local labels           | `_l = {k: str(k) for k in _e.keys()}`                          |
| `_c`     | Cell-local checks           | `_c = {k: check(v, 1.0) for k,v in _v.items()}`                |
| `params` | Global parameters           | `params.update(_p)` for persistence                            |
| `eqn`    | Global expressions          | `eqn.update(_e)` for persistence                               |

### Standard Cell Pattern

```python
# 1. Define symbols (prefer LaTeX notation)
F, A, sigma = symbols(r"F, A, \sigma")

# 2. Cell-local parameters
_p = {
    F: 10 * u.kN,
    A: 50 * u.cm**2,
}

# 3. Cell-local expressions
_e = {
    sigma: "F / A" | pc.parse_expr
}

# 4. Evaluation using cell-local dicts
_v = {
    k: v | pc.subs(_e | _p) | pc.convert_to([u.MPa]) | pc.N
    for k, v in _e.items()
}

# 5. Display
show_eqn([_p | _e, _v])
```

### With Notebook Persistence

```python
# Setup cell (run once per notebook)
params = {}  # Global parameters
eqn = {}     # Global expressions

# Calculation cell with LaTeX symbols
q, L, delta = symbols(r"q, L, \delta")

_p = {q: 5 * u.kN/u.m, L: 8 * u.m}
params.update(_p)  # Save to global

_e = {delta: "5 * q * L^4 / (384 * E * I)" | pc.parse_expr}
eqn.update(_e)     # Save to global

# For cross-cell dependencies
_v = {
    k: v | pc.subs(eqn | params) | pc.convert_to([u.mm]) | pc.N
    for k, v in _e.items()
}
```

### Advanced Patterns

**Verification:**
```python
# Use LaTeX notation for engineering symbols
sigma_Sd, sigma_Rd, tau_Sd, tau_Rd = symbols(r"\sigma_{Sd}, \sigma_{Rd}, \tau_{Sd}, \tau_{Rd}")

_expr = [sigma_Sd / sigma_Rd, tau_Sd / tau_Rd]  # List of expressions to check
_v = {k: k | pc.subs(_e | _p) | pc.N for k in _expr}  # Expression as key
_c = {k: check(v, 1.0) for k, v in _v.items()}
```

**Labels and cross-references:**
```python
_l = {k: str(k) for k in _e.keys()}  # Auto-generate labels
show_eqn([_e, _v], label=_l)
# Reference in text: \eqref{eq-PREFIX-symbol}
```

**Symbol dependency ordering (automatic):**
```python
# Complex symbols with LaTeX notation - escape commas with backslash
tau_1_Rd, gamma_M0 = symbols(r"\tau_{1\,Rd}, \gamma_{M0}")

_e = {
    result: "sqrt(a^2 + b^2) / intermediate" | pc.parse_expr,  # Uses 'intermediate'
    intermediate: "a * b" | pc.parse_expr,                     # Defined after 'result'
}
# Keecas handles dependency ordering automatically
```

### Configuration Setup

```python
# Preferred import style
from keecas import symbols, u, pc, show_eqn, config, check

# Configuration for Quarto
config.display.katex = True                # Disable \label{} for KaTeX compatibility (Jupyter dev mode)
config.display.print_label = True          # Print labels in dev mode
config.latex.eq_prefix = r"eq-PREFIX-"     # Label prefixing
config.display.default_float_format = ".3f"  # Default float formatting

# Language and localization (automatic Pint sync)
config.language.language = 'it'           # Sets both keecas and Pint locales
# Supported: 'de', 'es', 'fr', 'it', 'pt' (full)
# Fallback: 'da', 'nl', 'no', 'sv', 'en' (English units)

# Initialize global dicts
params = {}
eqn = {}
```

**Note on v1.0.0 Changes:**
- `sep` parameter now defaults to `None` (uses environment separator)
- `config.display.default_float_format` added for global float formatting
- `float_format` supports cell-by-cell formatting (dict, list, Dataframe, tuple structures)
- Format specs can be with or without curly braces: `".3f"` or `"{:.3f}"`
- `disable_pint_locale` default changed to `True` (preserves compact symbols like "kN")
- `pint_default_format` moved from `[units]` to `[display]` section (formatting concern)

### Configuration Files

Keecas uses a hierarchical TOML configuration system:

**File Locations:**
- **Global**: `~/.keecas/config.toml` (user-wide settings)
- **Local**: `<project>/.keecas/config.toml` (project-specific settings)

**Priority Order:** Local > Global > Defaults

**CLI Management:**
```bash
# Initialize configuration files
keecas config init --global     # Create global config
keecas config init --local      # Create local config

# Edit configurations
keecas config edit --global     # Terminal editor ($EDITOR)
keecas config open --local      # System default editor (GUI)

# View configurations
keecas config show             # Show merged config
keecas config show --global    # Show only global
keecas config path             # Show file locations
```

**Configuration Access Pattern:**

**IMPORTANT**: All configuration uses dot-notation matching TOML structure. Python access paths directly mirror the TOML section hierarchy.

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

**Rule**: Python path always matches TOML section path. If a setting is under `[display]` in TOML, access it via `config.display.setting_name` in Python.

**Example TOML Configuration:**
```toml
# .keecas/config.toml

[language]
language = "it"                    # Italian units and localization
disable_pint_locale = true         # Default: True (preserves compact unit symbols like "kN")

[display]
katex = true                       # KaTeX compatibility mode
default_float_format = ".3f"       # Default format for floats in equations
pint_default_format = ".3f~P"      # Pint quantity formatting

[latex]
eq_prefix = "eq-"                  # Equation label prefix

[custom_translations]
"VERIFIED" = "VERIFICATO"          # Custom term translations

# Custom environment definitions
[environments.spaced_align]
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

**Accessing Environments in Code:**
```python
# Access built-in environment
sep = config.latex.environments.align.separator

# Set custom environment
config.latex.environments.set("custom", {
    "separator": "&",
    "line_separator": r" \\\n ",
    "supports_multiple_labels": True,
    "outer_environment": "align"
})

# Inline environment definition
show_eqn(equations, environment={
    "separator": "&",
    "line_separator": r" \\\n ",
    "supports_multiple_labels": True,
    "outer_environment": "align"
})

# Use with env_arg
show_eqn(equations, environment="alignat", env_arg="{2}")
```

### Symbol Naming Conventions

**✅ PREFERRED: LaTeX notation with raw strings**
```python
# Simple symbols
F, A, sigma = symbols(r"F, A, \sigma")

# Complex engineering symbols
sigma_Sd, tau_Rd = symbols(r"\sigma_{Sd}, \tau_{Rd}")

# Symbols with commas - escape with backslash
tau_1_Rd, gamma_M0 = symbols(r"\tau_{1\,Rd}, \gamma_{M0}")

# Greek letters
alpha, beta, gamma = symbols(r"\alpha, \beta, \gamma")
```

**❌ AVOID: Plain string notation**
```python
# Avoid - no LaTeX rendering
sigma, tau, gamma = symbols("sigma, tau, gamma")
```

### Do's and Don'ts

**✅ DO:**
- Use LaTeX notation with raw strings for symbol definitions
- Use underscore-prefixed dicts for cell-local data (`_p`, `_e`, `_v`, `_d`)
- Use `params.update(_p)` and `eqn.update(_e)` for persistence
- Use dict comprehensions for evaluation
- Use pipe operators for functional composition
- Escape commas in symbol names with `\,`
- Let keecas handle symbol dependency ordering

**❌ DON'T:**
- Use plain string notation for symbols - always prefer LaTeX
- Use verbose variable names like `parameters`, `equations`, `values`
- Manually manage symbol dependencies
- Use individual variables instead of dicts for related data
- Mix cell-local and global patterns unnecessarily

For complete details, see `_docs/CONVENTIONS.md`.

### Testing Strategy
- Tests are located in `tests/` directory
- Test files follow pattern `test_*.py`
- Key test areas: dataframe operations, display formatting, pipe commands, localization, configuration
- **Comprehensive Locale Testing**: Tests cover Pint locale behavior, fallback scenarios, and persistence issues
- **CLI Testing**: Configuration management and cross-platform editor detection
- **Integration Testing**: Multi-language support and automatic synchronization

### Jupyter Notebook Integration
- Primary use case is in Jupyter notebooks for engineering calculations
- LaTeX output is rendered via IPython.display.Markdown
- **Rendering Engines**:
  - **KaTeX** (VS Code Jupyter extension): Does not support `\label{}` commands
  - **MathJax** (Quarto HTML output): Full support with AMS configuration
- **Equation Numbering & Cross-references**:
  - Set `config.display.katex = True` during Jupyter development to suppress `\label{}`
  - Set `config.display.print_label = True` to display labels for easy copy-paste
  - For Quarto HTML output with working labels, add MathJax AMS config to YAML frontmatter:
    ```yaml
    format:
      html:
        include-in-header:
          - text: |
              <script>
              MathJax = { tex: { tags: 'ams' } };
              </script>
          - text: |
              <style>
              .math.display {
                max-width: 100%;
                padding-right: 3em;
              }
              </style>
    ```
  - The CSS prevents horizontal scrollbars by reserving space for equation numbers
  - With this configuration, `\label{}`, `\ref{}`, and `\eqref{}` work correctly in HTML output
  - PDF output always supports labels natively
  - Use `\eqref{eq-label}` for parenthesized references: (1), or `\ref{eq-label}` for plain references: 1
- Example notebooks: `examples/hello_world.ipynb`, `examples/quarto_example/quarto_example.ipynb`

### Quarto Examples and Automation
- Quarto examples are organized in subdirectories under `examples/` (e.g., `examples/quarto_example/`)
- Each Quarto example directory contains:
  - `.ipynb`: Source Jupyter notebook
  - `.qmd`: Generated Quarto markdown (auto-generated)
  - `.pdf`, `.html`: Rendered documents (auto-generated)
  - `_files/`: Supporting assets (auto-generated)
- **Git Hook Automation**: Pre-commit hook automatically converts and renders notebooks
  - Install with: `bash scripts/install-hooks.sh`
  - When committing `.ipynb` files in `examples/quarto_example/`, the hook:
    1. Converts notebook to QMD using `quarto convert`
    2. Renders to PDF and HTML with `--execute` flag
    3. Adds all generated files to the commit
  - Skip automation with: `git commit --no-verify`

## Important Notes

- The project targets Python >=3.12, <4.0
- Uses `src/` layout for package structure
- Built specifically for Quarto document generation
- LaTeX output includes engineering-specific formatting (equation numbering, cross-references)
- Float formatting and unit conversion are key features for engineering documentation
- **CLI Entry Point**: `keecas` command available after installation via `pyproject.toml` script entry
- **TOML Dependency**: Added `toml>=0.10.2` for configuration file support
- **Cross-platform Compatibility**: CLI works on Linux (xdg-open), macOS (open), Windows (start)
- **Locale Management**: Conservative behavior ensures system locales aren't disrupted
- **Unit Conversion in SymPy**: Pint quantities converted to SymPy maintain full conversion capabilities
  - Prefixed units (kN, daN, cm, etc.) convert automatically via SymPy's prefix system
  - Non-prefixed compound units (kgf, lbf, etc.) have scale factors automatically set from Pint definitions
  - All Pint units convert correctly in SymPy expressions via `pc.convert_to()`
- When defining symbols prefer LaTeX notation: instead of symbols('gamma'), use symbols(r'\gamma'). This way you can have complex LaTeX symbols; if a symbol has a comma, escape it with `\`: tau_1_Rd = symbols(r'\tau_{1\,Rd}')

## Language and Localization Support

### Fully Supported Languages (5)
- **German (de)**: `Zentimeter` units, complete mathematical term translations
- **Spanish (es)**: `centímetro` units, complete mathematical term translations
- **French (fr)**: `centimètre` units, complete mathematical term translations
- **Italian (it)**: `centimetro` units, complete mathematical term translations
- **Portuguese (pt)**: `centímetro` units, complete mathematical term translations

### Fallback Languages (5)
- **Danish (da)**, **Dutch (nl)**, **Norwegian (no)**, **Swedish (sv)**: English units with keecas term translations
- **English (en)**: Default behavior, conservative locale handling

### Automatic Behavior
- **Configuration Changes**: `options.language = 'it'` automatically updates both keecas and Pint locales
- **Fallback Strategy**: Unsupported languages gracefully fall back to English units
- **Persistence Fix**: No more "sticky" locales from previous language settings
- **Conservative English**: English locale only changes when explicitly switching from other languages

## Task Planning and Management

### `_todo` Directory Structure
The project uses a structured planning system located in `_todo/`:

```
_todo/
├── todo.md                    # Master task list written by user
├── proposal/                  # Initial task proposals
│   └── [task-name].md        # Claude's detailed plan awaiting user approval
├── pending/                   # Active development files
│   └── [task-name].md        # Approved tasks with progress updates
└── completed/                 # Finished tasks archive
    └── YYYY-MM-DD/           # Date-based folders for completion date
        └── [task-name].md    # Final summary + insights
```

### Planning Workflow
1. **Task Creation**: User writes tasks in `_todo/todo.md` with clear objectives and priorities
2. **Proposal Phase**: Claude creates detailed proposal in `_todo/proposal/[task-name].md`
   - Include original objective from todo.md and remove it from todo.md
   - Break down into specific implementation steps
   - Wait for user review, comments, and approval
3. **Development Phase**: After user approval, move proposal to `_todo/pending/[task-name].md`
   - Update file with implementation progress and activity summaries
   - Use for ongoing development updates
4. **Completion**: After task completion, move file to `_todo/completed/YYYY-MM-DD/`
   - Update with final summary and insights
   - Mark task as "Completed" in todo.md

### Session Startup Protocol
**IMPORTANT**: At the start of each session, always check:
1. `_todo/todo.md` for new or updated tasks from the user
2. `_todo/proposal/` for user-reviewed proposals ready to approve/implement
3. `_todo/pending/` for active tasks requiring progress updates
4. Current git status and recent commits for context

## Claude Code Session Management

### Documentation Updates Before Commits
IMPORTANT: Always update project documentation before making significant commits to maintain context across sessions:

1. **CLAUDE.md**: Ensure architecture changes, new CLI features, and conventions are documented
2. **README.md**: Update with user-facing features and installation instructions
3. **Test documentation**: Update testing strategy and coverage notes
4. **`_todo` Planning Files**: Update relevant planning files with progress and insights

### Memory Management Practices
- Use TodoWrite tool proactively for complex multi-step tasks
- Complete todos as work finishes to maintain accurate progress tracking
- Update documentation before major commits to preserve session context
- Document new patterns, conventions, and architectural decisions immediately
- Maintain DEVELOPMENT_CONTEXT.md as a session-to-session handoff document
- Check `_todo/todo.md` at session start for user-defined tasks

### Key Files for Context Preservation
- `CLAUDE.md`: Project architecture, conventions, CLI usage
- `_todo/todo.md`: Current user tasks and priorities
- `_todo/proposal/`: Proposals awaiting user review and approval
- `_todo/pending/`: Active development files requiring progress updates
- `pyproject.toml`: Dependencies, build configuration, CLI entry points
- `src/keecas/__init__.py`: Module structure and main exports
- `examples/`: Working examples and templates for reference
- backward compatibility is not an issue since it will a major update