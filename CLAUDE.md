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

## Common Development Patterns

### Equation Definition Pattern
```python
# Define symbols
x, y = symbols('x, y')

# Parameters with units
params = {
    x: 5 * u.m,
    y: 10 * u.kg
}

# Symbolic expressions
eqns = {
    result: "x * y / 2" | pc.parse_expr
}

# Evaluated results
values = {
    k: v | pc.subs(eqns | params) | pc.convert_to([u.kN, u.m]) | pc.N
    for k, v in eqns.items()
}

# Display
show_eqn([params | eqns, values])
```

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