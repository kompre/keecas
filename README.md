

# keecas

[![Tests](https://github.com/kompre/keecas/actions/workflows/test.yml/badge.svg)](https://github.com/kompre/keecas/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/keecas.svg)](https://pypi.org/project/keecas/)
[![Python Version](https://img.shields.io/pypi/pyversions/keecas.svg)](https://pypi.org/project/keecas/)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://kompre.github.io/keecas)

A module for performing symbolic and units-aware calculations in a jupyter notebook. 

## Introduction

keecas is a Python module designed to simplify symbolic and units-aware calculations. It leverages well-known Python modules such as `sympy`, `pint`, and `pipe` to provide a convenient and easy-to-use interface.

It's meant to be used in a interactive environment such as jupyter notebook. It produces latex amsmath code that can be rendered by the notebook, displaying nicely formatted math expression. 

It's been developed to be used for [Quarto](https://quarto.org) rendered pdf documents, and it provides some specific features such as cross-reference support for equation.


## Features

*   Symbolic expression and computation using `sympy`
*   Units-aware calculations using `pint`
*   pipe style functions with `pipe`

## Examples

For a quick start, check out the [hello_world.ipynb](examples/hello_world.ipynb) example, which demonstrates how to use keecas to calculate the maximum bending moment for a simple beam.

## Installation

To install keecas, run the following command:

```bash
pip install keecas
```

or

```bash
uv add keecas
```

## Quick Start with CLI

After installation, you can quickly start working with keecas using the built-in CLI:

```bash
# Launch JupyterLab with minimal keecas template
keecas edit

# Create or open a specific notebook
keecas edit analysis.ipynb

# Create temporary notebook (auto-cleanup)
keecas edit --temp

# List available templates
keecas edit --list-templates

# Use comprehensive examples template
keecas edit --template quickstart
```

The CLI automatically:
- Creates notebooks from keecas templates with proper imports
- Launches JupyterLab with the notebook already open
- Handles temporary sessions with auto-cleanup
- Provides smart file naming (untitled-1.ipynb, untitled-2.ipynb, etc.)

## Configuration

keecas supports both global and local configuration via TOML files:

```bash
# Initialize and edit configuration
keecas config init --global
keecas config edit --global

# View current configuration
keecas config show
```



## Dependencies

keecas depends on the following packages:

*   `flatten-dict`
*   `ipython`
*   `pint`
*   `pipe`
*   `regex`
*   `ruamel-yaml`
*   `sympy`
*   `toml` (for configuration management)

## Testing

To run the tests, use the following command:

```bash
pytest
```

## License

keecas is licensed under the [MIT License](https://opensource.org/licenses/MIT).

## Acknowledgments

keecas is built on top of the excellent work of the `sympy`, `pint`, and `pipe` communities. We would like to thank the authors and maintainers of these projects for their contributions to the scientific Python ecosystem.
