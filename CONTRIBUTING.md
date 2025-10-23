# Contributing to Keecas

Thank you for your interest in contributing to Keecas! This guide will help you get started with the development workflow.

## Development Setup

### Prerequisites
- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- [Quarto](https://quarto.org/) for documentation
- Git

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kompre/keecas.git
   cd keecas
   ```

2. **Install dependencies**:
   ```bash
   uv sync --group dev
   ```

3. **Install pre-commit hooks**:
   ```bash
   bash scripts/install-hooks.sh
   ```

   This installs hooks that automatically:
   - Validate docstrings (fast check, < 1s)
   - Render Quarto notebooks (for `examples/quarto_example/`)

   **Note**: Tests run only in CI (not pre-commit) for faster local development

## Development Workflow

### Branch Strategy

```
feature-branches → dev → main (protected) → release (automated)
```

- **Feature branches**: Create from `dev` for new work
- **dev**: Integration branch for testing features
- **main**: Protected production branch, requires PR with passing tests
- **Releases**: Automated from `main` with labels

### Making Changes

1. **Create a feature branch from dev**:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow the coding style (enforced by Ruff)
   - Add tests for new functionality
   - Update docstrings following [DOCSTRINGS.md](DOCSTRINGS.md)
   - Run tests locally before committing

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

   Pre-commit hooks will automatically:
   - Validate docstrings (fast)
   - Render notebooks if changed

   **Tests run in CI** - commits are fast locally!

4. **Push and create PR**:
   ```bash
   git push -u origin feature/your-feature-name
   ```

   Create PR to `dev` branch for review.

### Testing Locally

**Run all tests**:
```bash
uv run pytest tests -v
```

**Run linter**:
```bash
uv run ruff check src/ tests/
```

**Validate docstrings**:
```bash
uv run python scripts/validate_docstrings.py
```

**Format code**:
```bash
uv run ruff format src/ tests/
```

## Coding Standards

### Code Style
- Follow PEP 8 (enforced by Ruff)
- Line length: 100 characters
- Use trailing commas in multi-line collections
- Type annotations required for public functions

### Docstrings
- Google-style docstrings for all public functions
- See [DOCSTRINGS.md](DOCSTRINGS.md) for comprehensive guidelines
- Include examples with realistic symbols and LaTeX notation
- Use ASCII-only text (no Unicode symbols)

### Commit Messages
Follow conventional commits format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions or changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

## Release Process

**For Maintainers Only**

### Creating a Release

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

   For TestPyPI testing, use `--label test-release` instead.

3. **Add release notes** in PR description:
   - Summarize major changes
   - List breaking changes (if any)
   - Mention contributors

4. **Merge PR**:
   - Ensure all tests pass
   - Get required approvals
   - Merge to main

5. **Automated workflow**:
   - Tests run on merged code
   - Package builds and publishes to PyPI/TestPyPI
   - Git tag created (vX.Y.Z)
   - GitHub Release generated with PR notes

### Version Strategy

- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Pre-releases**: Use identifiers (rc, alpha, beta, dev)
  - Example: `1.0.0rc1` automatically routes to TestPyPI
  - Stable versions (e.g., `1.0.0`) go to production PyPI

## CI/CD Workflows

### Test Workflow
Runs on every PR to `main`:
- Linting (Ruff)
- Tests (pytest)
- Docstring validation

### Release Workflow
Runs on PR merge to `main` with release label:
- Runs tests
- Builds package
- Creates git tag
- Publishes to PyPI/TestPyPI
- Creates GitHub Release

### Documentation Workflow
Runs on push to `main` or `dev`:
- Generates API docs with quartodoc
- Renders Quarto documentation
- Deploys to GitHub Pages

## Getting Help

- **Issues**: Check [existing issues](https://github.com/kompre/keecas/issues)
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: https://kompre.github.io/keecas

## Code of Conduct

Be respectful and constructive in all interactions. This project follows standard open-source community guidelines.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
