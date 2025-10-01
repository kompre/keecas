# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`keecas` is a Python module for symbolic and units-aware calculations in Jupyter notebooks, specifically designed for Quarto rendered PDF documents. It combines `sympy` (symbolic math), `pint` (units), and `pipe` (functional programming) to provide a streamlined interface for mathematical computations with LaTeX output.

## Development Commands

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

3. **Pipe Commands** (`src/keecas/pipe_command.py`)
   - Wraps common SymPy functions as `@Pipe` decorators for functional composition
   - Key functions: `subs`, `N`, `convert_to`, `doit`, `parse_expr`, `quantity_simplify`
   - Enables chain operations like `expr | pc.subs(vals) | pc.convert_to(units) | pc.N`

4. **Pint-SymPy Bridge** (`src/keecas/pint_sympy.py`)
   - Integrates Pint unit registry with SymPy symbolic expressions
   - Provides `unitregistry as u` for unit definitions
   - `update_pint_locale()`: Function for manual locale control
   - **Locale Support**: Automatic locale management for international unit formatting
   - **Language Integration**: 5 fully supported languages (de, es, fr, it, pt) with English fallback for others
   - **Conservative Behavior**: Intelligent locale switching that preserves system defaults

5. **Configuration System** (`src/keecas/config.py`)
   - **Unified TOML Configuration**: `.keecas/config.toml` files for global and local settings
   - **Hierarchical Priority**: Local > Global > Defaults
   - **Dynamic Propagation**: Configuration changes automatically update Pint locale and localization
   - **CLI Integration**: Full command-line interface for configuration management

6. **CLI Interface** (`src/keecas/cli.py`)
   - **Cross-platform Configuration Management**: Edit configs with terminal or system editors
   - **Version Display**: Built-in version information and help
   - **Consistent Interface**: All commands support explicit `--global` and `--local` flags

7. **Localization System** (`src/keecas/localization/`)
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

# Configuration for Quarto/KaTeX
config.katex = True                        # Disable \label{} for KaTeX compatibility
config.print_label = True                  # Print labels in dev mode
config.eq_prefix = r"eq-PREFIX-"           # Label prefixing
config.display.default_float_format = ".3f"  # Default float formatting

# Language and localization (automatic Pint sync)
config.language = 'it'           # Sets both keecas and Pint locales
# Supported: 'de', 'es', 'fr', 'it', 'pt' (full)
# Fallback: 'da', 'nl', 'no', 'sv', 'en' (English units)

# Initialize global dicts
params = {}
eqn = {}
```

**Note on v1.0.0 Changes:**
- `sep` parameter now defaults to `None` (uses environment separator)
- `config.display.default_float_format` added for global float formatting
- Format specs can be with or without curly braces: `".3f"` or `"{:.3f}"`

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

**Example Configuration:**
```toml
# .keecas/config.toml
language = "it"                    # Italian units and localization
katex = true                       # KaTeX compatibility mode
eq_prefix = "eq-"                  # Equation label prefix
pint_default_format = ".3f~P"      # Pint number formatting
disable_pint_locale = false       # Allow automatic locale setting

[display]
default_float_format = ".3f"       # Default format for floats in equations

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

For complete details, see `docs/CONVENTIONS.md`.

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
- Supports both KaTeX (VS Code) and standard LaTeX rendering
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