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
feature-branches → main (protected, requires PR + passing tests) → release (automated)

(optional) feature-branches → dev (staging, for batching several changes) → main
```

- **Feature branches**: create from `main` for a single, self-contained change; PR straight back to `main`
- **dev**: optional staging branch for batching multiple concurrent changes before they hit `main` together — not a required hop
- **main**: protected production branch, requires PR with passing tests; release-please watches it directly
- **Releases**: fully automated via release-please, no labels needed

**Why there's no mandatory `dev` hop:** release-please only reads conventional-commit messages that have landed on `main` since the last release tag — it has no concept of branch topology, so it computes the identical version bump and changelog whether a change arrives via `feature → main` directly or `feature → dev → main`. The CI gates are equivalent either way: `lint-fix.yml` auto-fixes on push to any branch except `main`, and `test.yml` runs on PR to `main` regardless of the source branch. The `feature → dev → main` two-hop flow predates release-please, from when releases were cut and gated manually per branch; now it's just a convenience for batching several things together, not a pipeline requirement. Default to PRing straight to `main` — this also keeps things simple when multiple people (or multiple parallel Claude Code sessions, local or remote) are each working on their own isolated branch, since nobody has to coordinate through a shared staging branch first. Reach for `dev` only when you deliberately want to stage several concurrent changes together before they land on `main` as one batch.

### Making Changes

1. **Create a feature branch from `main`** (or from `dev` if you're deliberately batching with other in-flight work):
   ```bash
   git checkout main
   git pull origin main
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

   Create PR to `main` for review (or to `dev` if you're batching this change with other in-flight work).

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

Releases are fully automated via [release-please](https://github.com/googleapis/release-please) — there is no manual version bump, ever. The version number is computed entirely from conventional commit messages (`feat:`, `fix:`, `BREAKING CHANGE`) merged into `main` since the last release tag.

### Creating a Release

1. **Open a PR from your feature branch straight to `main`** and merge it, same as any other change — there's no required `dev` staging step (see "Branch Strategy" above). Use `dev` first only if you're deliberately batching several changes into one landing on `main`.
2. **release-please opens/updates a standing PR** on `main` titled `chore(main): release X.Y.Z`, containing the computed version bump and an auto-generated `CHANGELOG.md` entry. It keeps itself up to date as more commits land on `main` — no need to touch it until you're ready to ship.
3. **Review that PR's diff** (just `pyproject.toml`, `CHANGELOG.md`, and the manifest file) and merge it whenever you want to cut a release.
4. **Merging it automatically**:
   - Creates the git tag (`vX.Y.Z`) and GitHub Release with the generated changelog as release notes
   - Triggers `publish-pypi`, which builds the package and publishes to PyPI via Trusted Publishing (OIDC, no API tokens)
   - Attaches the built `dist/*` artifacts to the GitHub Release

### Version Strategy

- **Semantic Versioning**: MAJOR.MINOR.PATCH, determined automatically:
  - Any `feat:` commit since the last release → minor bump
  - Any `BREAKING CHANGE` footer/`!` marker → major bump
  - Otherwise, any `fix:` commit → patch bump
- There is no pre-release/TestPyPI publishing path.

## CI/CD Workflows

### Test Workflow
Runs on every PR to `main`:
- Linting (Ruff)
- Tests (pytest)
- Docstring validation

### Release Workflow
Runs on push to `main`:
- `release-please` job opens/updates the standing release PR, computed from conventional commits
- `publish-pypi` job (gated on a new release actually being created): builds the package, publishes to PyPI via Trusted Publishing (OIDC), attaches build artifacts to the GitHub Release

### Documentation Workflow
Runs on push to `main` only:
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
