# Installation

## Requirements

Keecas requires Python 3.12 or higher.

## Installation Methods

### Using pip (Recommended)

```bash
pip install keecas
```

### Using uv (Fast Package Manager)

```bash
uv add keecas
```

### Development Installation

For development or to get the latest features:

```bash
# Clone the repository
git clone https://github.com/kompre/keecas.git
cd keecas

# Install in development mode
pip install -e ".[dev]"
```

## Dependencies

Keecas automatically installs the following core dependencies:

- **sympy** - Symbolic mathematics
- **pint** - Physical units and quantities
- **pipe** - Functional programming utilities
- **IPython** - Enhanced interactive Python (for Jupyter integration)

## Optional Dependencies

### Documentation Tools (for developers)

```bash
pip install keecas[docs]
```

This includes:
- mkdocs
- mkdocs-material
- mkdocstrings

### Development Tools

```bash
pip install keecas[dev]
```

This includes:
- pytest (testing)
- ruff (linting)
- All documentation dependencies

## Verification

Verify your installation by running:

```python
import keecas
print(keecas.__version__)
```

Or check the CLI:

```bash
keecas --version
```

## Jupyter Setup

Keecas works best in Jupyter environments. You can use the built-in CLI to launch Jupyter with templates:

```bash
# Launch JupyterLab with a keecas template
keecas edit --template quickstart

# Launch classic Jupyter Notebook
keecas edit --no-lab
```

## Troubleshooting

### Import Errors

If you encounter import errors, ensure all dependencies are properly installed:

```bash
pip install --upgrade keecas
```

### Jupyter Integration Issues

If LaTeX rendering doesn't work in Jupyter:

1. Ensure IPython is installed: `pip install ipython`
2. Restart your Jupyter kernel
3. Check that MathJax is enabled in your Jupyter environment

### Unit Registry Issues

If you encounter locale-related warnings:

```python
from keecas import config
config.disable_pint_locale = True
```

## Next Steps

Once installed, continue with the [Quick Start](quickstart.md) guide to begin using Keecas.