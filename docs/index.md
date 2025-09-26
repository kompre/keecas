# Keecas Documentation

Welcome to Keecas, a Python package for symbolic and units-aware calculations in Jupyter notebooks, specifically designed for Quarto rendered PDF documents.

## What is Keecas?

Keecas combines three powerful Python libraries:

- **SymPy** - Symbolic mathematics
- **Pint** - Physical units and quantities
- **Pipe** - Functional programming patterns

This combination provides a streamlined interface for mathematical computations with beautiful LaTeX output, perfect for engineering documentation and calculations.

## Key Features

- 🔢 **Symbolic Mathematics**: Work with symbolic expressions and equations
- 📏 **Unit-Aware Calculations**: Automatic unit conversion and dimensional analysis
- 📝 **LaTeX Output**: Beautiful equation rendering for documents
- 📊 **Jupyter Integration**: Seamless notebook workflow
- 🌍 **Internationalization**: Support for multiple languages and locales
- ⚙️ **Configurable**: Flexible configuration system

## Quick Example

```python
from keecas import symbols, u, pc, show_eqn

# Define symbols with LaTeX notation
F, A, sigma = symbols(r"F, A, \sigma")

# Parameters with units
_p = {
    F: 10 * u.kN,
    A: 50 * u.cm**2,
}

# Expressions
_e = {
    sigma: "F / A" | pc.parse_expr
}

# Evaluate and display
_v = {
    k: v | pc.subs(_e | _p) | pc.convert_to([u.MPa]) | pc.N
    for k, v in _e.items()
}

show_eqn([_p | _e, _v])
```

## Getting Started

- [Installation Guide](getting-started/installation.md) - Install Keecas and dependencies
- [Quick Start](getting-started/quickstart.md) - Your first calculations with Keecas
- [Configuration](getting-started/configuration.md) - Set up your preferences

## Documentation Sections

### [User Guide](user-guide/conventions.md)
Learn the conventions, patterns, and best practices for using Keecas effectively.

### [API Reference](api-reference/display.md)
Complete reference for all functions, classes, and modules.

### [CLI Reference](cli-reference/commands.md)
Command-line interface for configuration and Jupyter integration.

### [Developer Guide](developer-guide/contributing.md)
Information for contributors and developers extending Keecas.

## Community and Support

- **GitHub Repository**: [kompre/keecas](https://github.com/kompre/keecas)
- **Issues and Bug Reports**: [GitHub Issues](https://github.com/kompre/keecas/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kompre/keecas/discussions)

## License

Keecas is released under the MIT License. See the [LICENSE](https://github.com/kompre/keecas/blob/main/LICENSE) file for details.