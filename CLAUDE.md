# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`keecas` is a Python module for symbolic and units-aware calculations in Jupyter notebooks, specifically designed for Quarto rendered PDF documents. It combines `sympy` (symbolic math), `pint` (units), and `pipe` (functional programming) to provide a streamlined interface for mathematical computations with LaTeX output.

## Development Commands

### Testing
```bash
pytest
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
   - `options` dataclass: Global configuration for equation formatting
   - Supports multiple equation environments (align, equation, cases, etc.)
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

5. **Configuration** (`src/keecas/config.py`)
   - Default values for display options

### Key Design Patterns

- **Dictionary-Based Equations**: Mathematical equations are represented as dicts where keys are LHS symbols and values are RHS expressions
- **Pipe Functional Style**: Mathematical operations are chained using pipe operators (`|`)
- **Units Integration**: Seamless conversion between Pint quantities and SymPy units
- **LaTeX Generation**: Automatic conversion of symbolic expressions to formatted LaTeX output

### Module Imports Structure

The main `__init__.py` exposes:
- `Dataframe` class
- Display functions (`show_eqn`, `options`, `verifica`, etc.)
- Pipe commands as `pc` namespace
- Unit registry as `u`
- Common SymPy symbols and functions
- LaTeX printing utilities

## Keecas Usage Conventions

Keecas follows strict conventions to minimize boilerplate while maximizing expressiveness. **Always follow these patterns when working with keecas code.**

### Core Philosophy

Mathematical equations are mappings between LHS and RHS expressions. Use Python `dict` containers where:
- **Cell-local dicts** (prefixed with `_`): Live and die within a single cell for immediate display
- **Notebook-global dicts** (no prefix): Persist across cells for complex multi-step calculations

### Standard Dict Conventions

| Dict | Purpose | Example |
|------|---------|---------|
| `_p` | Cell-local parameters | `_p = {F: 10*u.kN, A: 50*u.cm**2}` |
| `_e` | Cell-local expressions | `_e = {sigma: "F / A" \| pc.parse_expr}` |
| `_v` | Cell-local evaluated values | `_v = {k: v \| pc.subs(_e\|_p) \| pc.N for k,v in _e.items()}` |
| `_d` | Cell-local descriptions | `_d = {F: "applied force", sigma: "stress"}` |
| `_l` | Cell-local labels | `_l = {k: str(k) for k in _e.keys()}` |
| `_c` | Cell-local checks | `_c = {k: check(v, 1.0) for k,v in _v.items()}` |
| `params` | Global parameters | `params.update(_p)` for persistence |
| `eqn` | Global expressions | `eqn.update(_e)` for persistence |

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
from keecas import symbols, u, pc, show_eqn, options, check

# Configuration for Quarto/KaTeX
options.katex = True              # Disable \label{} for KaTeX compatibility
options.PRINT_LABEL = True        # Print labels in dev mode
options.EQ_PREFIX = r"eq-PREFIX-" # Label prefixing

# Initialize global dicts
params = {}
eqn = {}
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
- Key test areas: dataframe operations, display formatting, pipe commands

### Jupyter Notebook Integration
- Primary use case is in Jupyter notebooks for engineering calculations
- LaTeX output is rendered via IPython.display.Markdown
- Supports both KaTeX (VS Code) and standard LaTeX rendering
- Example notebook: `examples/hello_world.ipynb`

## Important Notes

- The project targets Python >=3.12, <4.0
- Uses `src/` layout for package structure
- Built specifically for Quarto document generation
- LaTeX output includes engineering-specific formatting (equation numbering, cross-references)
- Float formatting and unit conversion are key features for engineering documentation
- when defining symbols prefer latex notation: instead of symbols('gamma'), use symbols(r'\gamma'). This way you can have complex latex symbol; if a symbol has a comma, escape it with `\`: tau_1_Rd = symbols(r'\tau_{1\,Rd}')