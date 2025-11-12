

# keecas

[![Tests](https://github.com/kompre/keecas/actions/workflows/test.yml/badge.svg)](https://github.com/kompre/keecas/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/keecas.svg)](https://pypi.org/project/keecas/)
[![Python Version](https://img.shields.io/pypi/pyversions/keecas.svg)](https://pypi.org/project/keecas/)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://kompre.github.io/keecas)

Symbolic and units-aware calculations for Jupyter notebooks with beautiful LaTeX output.

## What is keecas?

keecas minimizes boilerplate for symbolic calculations using **Python dicts** as the core container - **keys** represent left-hand side symbols, **values** represent right-hand side expressions. Built on [SymPy](https://www.sympy.org/), [Pint](https://pint.readthedocs.io/), and [Pipe](https://github.com/JulienPalard/Pipe), it provides automatic unit conversion and LaTeX rendering for [Quarto](https://quarto.org) documents.

## Quick Example

```python
from keecas import symbols, u, pc, show_eqn

# 1. Define symbols with LaTeX notation
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

# 4. Evaluation with pipe operations
_v = {
    k: v | pc.subs(_e | _p) | pc.convert_to([u.MPa]) | pc.N
    for k, v in _e.items()
}

# 5. Display as LaTeX amsmath
show_eqn([_p | _e, _v])
```

**Output:**
```latex
\begin{align}
    F & = 10{\,}\text{kN} &    \\[8pt]
    A & = 50{\,}\text{cm}^{2} &    \\[8pt]
    \sigma & = \dfrac{F}{A} & = 2.0{\,}\text{MPa}
\end{align}
```

See [hello_world.ipynb](examples/hello_world.ipynb) for more examples.

## Installation

```bash
pip install keecas
# or
uv add keecas
```

## Quick Start

Launch JupyterLab with keecas template:

```bash
keecas edit                        # Minimal template
keecas edit --template quickstart  # Comprehensive examples
keecas edit analysis.ipynb         # Open specific notebook
keecas edit --temp                 # Temporary session
```

## Configuration

Manage global and local settings via TOML files:

```bash
# Initialize configuration
keecas config init --global

# Edit configuration
keecas config edit --global    # Terminal editor
keecas config open --local     # System editor (GUI)

# View configuration
keecas config show             # Merged settings
keecas config path             # File locations
```

## Key Features

- **Dict-based equations**: Natural mapping of LHS to RHS
- **Pipe operations**: Chain operations like `expr | pc.subs(...) | pc.N`
- **Unit-aware**: Automatic conversion between Pint and SymPy units
- **LaTeX output**: Renders as amsmath align blocks
- **Cross-references**: Label generation for Quarto documents
- **Multi-language**: 10 languages supported (5 fully localized)
- **Configuration**: Global/local TOML-based settings

## Documentation

Full documentation: [https://kompre.github.io/keecas](https://kompre.github.io/keecas)

## License

MIT License - see [LICENSE](https://opensource.org/licenses/MIT)
