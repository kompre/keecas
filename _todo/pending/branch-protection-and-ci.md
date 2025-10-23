# Proposal: Branch Protection and CI/CD Workflow

## Objective

Configure comprehensive test and release workflows with branch protection rules to ensure code quality and safe deployments. Move from manual/pre-commit validation to automated CI/CD pipeline with gating mechanisms.

## Context

**Current State**:
- Pre-commit hooks run tests locally (`scripts/pre-commit`)
- Manual git operations without branch protection
- No automated PR validation
- No release automation
- Tests run on commits but don't gate merges
- GitHub Actions workflow exists for docs deployment (`.github/workflows/docs.yml`)

**Target State**:
- Branch protection on `main`
- Required CI checks before merge
- Automated test runs on PRs
- Release workflow automation
- Clear separation: dev → main → release

## Example Workflows Analysis

**Source files analyzed**:
- `.github/workflows/examples/test.yml` - Test workflow for PRs
- `.github/workflows/examples/release.yml` - Release workflow with label checking
- `.github/workflows/examples/release copy.yml` - Alternative release with better GitHub Release step

**Release process clarified**:
- User manually bumps version in `pyproject.toml` before release (semantic versioning)
- PR to main must have `release` or `test-release` label to trigger PyPI publishing
- Version pre-release identifiers (rc, alpha, beta, dev) automatically route to TestPyPI
- GitHub Release created with PR details and changelog

## Current GitHub Actions

**Existing workflow** (`.github/workflows/docs.yml`):
- Triggers: push to main/dev, manual dispatch
- Builds and deploys documentation
- Uses Quarto for rendering
- Deploys to GitHub Pages

## Problem Statement

**Current issues**:
1. No automated PR validation - merges can break main/dev
2. No branch protection - direct pushes possible
3. Manual release process - error-prone versioning
4. Tests only run locally via pre-commit
5. No CI/CD gating for code quality
6. Documentation deployment not tied to releases

**Solution**: Implement comprehensive CI/CD pipeline with branch protection and automated releases.

## Implementation Plan

### Phase 1: Test Workflow Setup

**File**: `.github/workflows/test.yml`

**Workflow configuration**:
```yaml
name: Run Tests

on:
  pull_request:
    branches: [ main ]

concurrency:
  group: test-${{ github.event.pull_request.number }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version-file: ".python-version"  # 3.13

      - name: Install uv
        uses: astral-sh/setup-uv@v6
        with:
          version: "latest"
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      - name: Install Quarto
        uses: quarto-dev/quarto-actions/setup@v2
        with:
          version: release

      - name: Install dependencies
        run: uv sync --group dev

      - name: Run linter (Ruff)
        run: uv run ruff check src/ tests/

      - name: Run tests
        run: uv run pytest tests -v

      - name: Validate docstrings
        run: uv run python scripts/validate_docstrings.py
```

**Key features**:
- Runs only on PRs to `main` (branch protection will ensure this gates merges)
- Uses Python 3.13 from `.python-version` file
- Caches uv dependencies for faster runs
- Installs Quarto (needed if tests render notebooks)
- Runs Ruff linter before tests (fast feedback on code style)
- Validates docstrings presence
- Cancels previous runs on new commits to same PR (faster CI)

### Phase 2: Branch Protection Rules

**main branch protection** (GitHub Settings → Branches → Add rule):
- ✅ **Require pull request before merging**
  - Required approvals: 1 (for collaborative projects) or 0 (for solo/trusted team)
  - Dismiss stale reviews: Yes (when new commits pushed)
- ✅ **Require status checks to pass**
  - Required checks: `test` (from test.yml workflow)
  - Require branches to be up to date before merging: Yes
- ✅ **Restrict who can push**
  - Block direct pushes to main
  - Allow only via PR merge
- ❌ **Do not allow force pushes**
- ❌ **Do not allow deletions**
- ✅ **Require linear history** (optional, enforces squash/rebase)

**dev branch** - No protection initially:
- Allows rapid development iteration
- Tests still run on PRs to main (dev → main flow)
- Can add similar protection later if needed

**Rationale**: Since PRs go from feature branches → dev → main, protecting only main ensures:
- All code in main has passed tests
- Dev branch remains flexible for experimentation
- Clear promotion path: dev (testing ground) → main (production-ready)

### Phase 3: Release Workflow

**File**: `.github/workflows/release.yml`

**Workflow configuration** (hybrid approach combining best features):

```yaml
name: Release

on:
  pull_request:
    types: [closed]

# Prevent concurrent releases
concurrency:
  group: release
  cancel-in-progress: false  # Queue releases instead of canceling

jobs:
  release:
    name: Automated Release
    # Only run if PR was merged to main and has 'release' or 'test-release' label
    if: |
      github.event.pull_request.merged == true &&
      github.event.pull_request.base.ref == 'main' &&
      (contains(github.event.pull_request.labels.*.name, 'release') ||
       contains(github.event.pull_request.labels.*.name, 'test-release'))
    runs-on: ubuntu-latest
    permissions:
      contents: write  # Create releases and tags
      id-token: write  # OIDC for PyPI Trusted Publishing

    steps:
      - name: Checkout main branch
        uses: actions/checkout@v4
        with:
          ref: main
          fetch-depth: 0  # Full history for proper tagging

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version-file: ".python-version"

      - name: Install uv
        uses: astral-sh/setup-uv@v6
        with:
          version: "latest"
          enable-cache: true

      - name: Install Quarto
        uses: quarto-dev/quarto-actions/setup@v2
        with:
          version: release

      - name: Install dependencies
        run: uv sync --group dev

      - name: Run tests
        run: uv run pytest tests -v

      - name: Extract version from pyproject.toml
        id: version
        run: |
          VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
          TAG="v$VERSION"

          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "tag=$TAG" >> $GITHUB_OUTPUT

          echo "📦 Version: $VERSION"
          echo "🏷️  Tag: $TAG"

      - name: Determine publish target
        id: target
        env:
          HAS_TEST_LABEL: ${{ contains(github.event.pull_request.labels.*.name, 'test-release') }}
        run: |
          VERSION="${{ steps.version.outputs.version }}"

          # Check label first, then fall back to version check
          if [ "$HAS_TEST_LABEL" == "true" ]; then
            echo "repository_url=https://test.pypi.org/legacy/" >> $GITHUB_OUTPUT
            echo "target_name=TestPyPI" >> $GITHUB_OUTPUT
            echo "is_production=false" >> $GITHUB_OUTPUT
            echo "🎯 Target: TestPyPI (test-release label)"
          elif echo "$VERSION" | grep -qE '(rc|alpha|beta|dev|a[0-9]|b[0-9])'; then
            echo "repository_url=https://test.pypi.org/legacy/" >> $GITHUB_OUTPUT
            echo "target_name=TestPyPI" >> $GITHUB_OUTPUT
            echo "is_production=false" >> $GITHUB_OUTPUT
            echo "🎯 Target: TestPyPI (pre-release version: $VERSION)"
          else
            echo "repository_url=https://upload.pypi.org/legacy/" >> $GITHUB_OUTPUT
            echo "target_name=PyPI" >> $GITHUB_OUTPUT
            echo "is_production=true" >> $GITHUB_OUTPUT
            echo "🎯 Target: Production PyPI (stable release: $VERSION)"
          fi

      - name: Check if tag already exists
        run: |
          if git rev-parse "refs/tags/${{ steps.version.outputs.tag }}" >/dev/null 2>&1; then
            echo "❌ Error: Tag ${{ steps.version.outputs.tag }} already exists!"
            echo ""
            echo "This version has already been released."
            echo "Please bump the version in pyproject.toml and try again."
            exit 1
          fi
          echo "✅ Tag ${{ steps.version.outputs.tag }} is available"

      - name: Create and push tag
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          git tag -a "${{ steps.version.outputs.tag }}" -m "Release version ${{ steps.version.outputs.version }}

          Released from PR #${{ github.event.pull_request.number }}: ${{ github.event.pull_request.title }}
          Target: ${{ steps.target.outputs.target_name }}"

          git push origin "${{ steps.version.outputs.tag }}"
          echo "✅ Created and pushed tag: ${{ steps.version.outputs.tag }}"

      - name: Build package
        run: |
          uv build
          echo "📦 Build artifacts:"
          ls -lh dist/

      - name: Publish to PyPI
        if: steps.target.outputs.is_production == 'true'
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          print-hash: true
          verbose: true

      - name: Publish to TestPyPI
        if: steps.target.outputs.is_production == 'false'
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/
          skip-existing: true
          print-hash: true
          verbose: true

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ steps.version.outputs.tag }}
          name: ${{ steps.target.outputs.is_production == 'true' && format('Release {0}', steps.version.outputs.version) || format('Release {0} (TestPyPI)', steps.version.outputs.version) }}
          body: |
            # ${{ github.event.pull_request.title }}

            ${{ github.event.pull_request.body }}

            ---

            **📦 Version:** `${{ steps.version.outputs.version }}`
            **🎯 Published To:** ${{ steps.target.outputs.target_name }}

            ${{ steps.target.outputs.is_production == 'false' && format('⚠️ **This is a test release published to TestPyPI**

            Install from TestPyPI:
            ```bash
            pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ keecas=={0}
            ```

            **TestPyPI Package:** https://test.pypi.org/project/keecas/{0}/', steps.version.outputs.version) || format('Install from PyPI:
            ```bash
            pip install keecas=={0}
            ```

            **PyPI Package:** https://pypi.org/project/keecas/{0}/', steps.version.outputs.version) }}

            **Full Changelog**: https://github.com/${{ github.repository }}/compare/${{ github.event.pull_request.base.sha }}...${{ steps.version.outputs.tag }}
          files: dist/*
          draft: false
          prerelease: ${{ steps.target.outputs.is_production == 'false' || contains(steps.version.outputs.version, 'a') || contains(steps.version.outputs.version, 'b') || contains(steps.version.outputs.version, 'rc') || contains(steps.version.outputs.version, 'dev') }}
          generate_release_notes: true
```

**Key features**:
- **Trigger**: PR merged to main with `release` or `test-release` label
- **Label-based targeting**:
  - `release` label → Production PyPI
  - `test-release` label → TestPyPI
  - Falls back to version check for pre-release identifiers
- **GitHub Release creation** using `softprops/action-gh-release@v2`:
  - Includes PR title and body in release notes
  - Dynamic installation instructions based on target
  - Attaches distribution files (wheel, sdist)
  - Generates changelog automatically
  - Marks as prerelease for TestPyPI or pre-release versions
- **Safety checks**:
  - Tests run before building
  - Tag existence validation
  - Concurrency control (no parallel releases)
- **PyPI Trusted Publishing**: Uses OIDC (no API tokens needed)

**Release process for maintainers**:
1. Create PR from dev to main with version bump in `pyproject.toml`
2. Add `release` label (production) or `test-release` label (TestPyPI)
3. Get PR approved and merge
4. Workflow automatically:
   - Runs tests
   - Creates git tag
   - Builds package
   - Publishes to PyPI/TestPyPI
   - Creates GitHub Release with notes

### Phase 4: Integration with Existing Workflows

**Docs workflow** (`.github/workflows/docs.yml`) - No changes needed:
- Already handles dev/main separation correctly
- Continues to deploy on push to main/dev
- Independent of release workflow (docs deploy != package release)
- API docs regenerate automatically via `scripts/update_docs.py`

**Pre-commit hooks** (`scripts/pre-commit`) - Keep as-is:
- Provides fast local feedback (tests + docstring validation + notebook rendering)
- Prevents broken commits before push
- CI acts as final gatekeeper for PRs
- No duplication: pre-commit catches issues early, CI validates before merge

**Relationship between workflows**:
```
Local development:
  └─ pre-commit hook (fast feedback)

PR to main:
  └─ test.yml (gatekeeper)
     └─ Branch protection blocks merge if fails

PR merged to main with release label:
  └─ release.yml (publish + tag + GitHub release)

Push to main/dev:
  └─ docs.yml (documentation deployment)
```

### Phase 5: Documentation and Developer Experience

**1. Update CLAUDE.md** - Add CI/CD section:
```markdown
## CI/CD and Release Process

### Branch Protection
- **main**: Protected, requires PR + passing tests
- **dev**: Unprotected, rapid iteration allowed
- Feature branches merge to dev, then dev → main via PR

### Release Process
1. Create PR from dev to main with version bump in `pyproject.toml`
2. Add label:
   - `release` for production PyPI
   - `test-release` for TestPyPI
3. Merge PR after approval and passing tests
4. Workflow automatically creates tag, publishes package, creates GitHub Release

### CI Workflows
- **test.yml**: Runs on PR to main (linting, tests, docstring validation)
- **release.yml**: Runs on PR merge to main with release label
- **docs.yml**: Runs on push to main/dev (documentation deployment)
```

**2. Update README** - Add status badges:
```markdown
# Keecas

[![Tests](https://github.com/kompre/keecas/actions/workflows/test.yml/badge.svg)](https://github.com/kompre/keecas/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/keecas.svg)](https://pypi.org/project/keecas/)
[![Python Version](https://img.shields.io/pypi/pyversions/keecas.svg)](https://pypi.org/project/keecas/)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://kompre.github.io/keecas)
```

**3. Create CONTRIBUTING.md** - Development workflow guide:
```markdown
# Contributing to Keecas

## Development Workflow

### Setting Up
```bash
git clone https://github.com/kompre/keecas.git
cd keecas
uv sync --group dev
bash scripts/install-hooks.sh
```

### Making Changes
1. Create feature branch from dev: `git checkout dev && git checkout -b feature/your-feature`
2. Make changes and commit (pre-commit hooks will run)
3. Push and create PR to dev for review
4. After approval, merge to dev

### Creating a Release
1. Create PR from dev to main with version bump in `pyproject.toml`
2. Update release notes in PR description
3. Add label: `release` (production) or `test-release` (TestPyPI)
4. Merge PR - automated release workflow handles the rest

### Running Tests Locally
```bash
uv run pytest tests -v
uv run ruff check src/ tests/
```


**4. Documentation updates**:
- Add release workflow diagram to CLAUDE.md
- Document PyPI Trusted Publishing setup requirements
- Update session management notes with CI/CD context

## Branch Strategy

**Implemented workflow**:
```
feature-branches → dev → main (protected) → release (automated)
                           ↓                      ↓
                      PR with tests          tag + PyPI + GitHub Release
```

**Flow details**:
1. **Feature development**:
   - Branch from dev: `git checkout -b feature/name`
   - Commit locally (pre-commit hooks validate)
   - PR to dev for collaboration

2. **Release preparation**:
   - Bump version in `pyproject.toml` on dev branch
   - Create PR from dev → main
   - Add `release` or `test-release` label
   - CI runs tests automatically

3. **Release execution**:
   - Merge PR to main (requires passing tests via branch protection)
   - Release workflow triggers automatically
   - Package published, tag created, GitHub Release generated

**Version strategy**: Currently 0.1.2, targeting 1.0.0
- Semantic versioning: MAJOR.MINOR.PATCH
- Pre-release identifiers (rc, alpha, beta, dev) route to TestPyPI
- Stable versions (e.g., 1.0.0) go to production PyPI

## Dependencies

**Coordinates with**:
- [github-actions-pypi-publishing.md](proposal/github-actions-pypi-publishing.md) - PyPI release integration
- Existing docs workflow (`.github/workflows/docs.yml`)

**Blocks**:
- Branch protection must be configured before 1.0.0 release
- Test workflow needed before enabling required status checks

## Implementation Decisions (Based on Analysis)

1. **Test matrix**: ✅ Single Python version (3.13 from `.python-version`)
   - Rationale: Project requires 3.12+, 3.13 is current, matrix adds CI time without major benefit

2. **PR reviews**: ⚙️ Configurable (0 or 1 required approvals on main)
   - Solo/trusted team: 0 approvals, tests are the gate
   - Collaborative: 1 approval for human review

3. **Coverage requirements**: ❌ Not enforced initially
   - Current: 158 passing tests, good coverage exists
   - Can add later with pytest-cov if needed

4. **Release trigger**: ✅ PR merge to main with label
   - `release` label → Production PyPI
   - `test-release` label → TestPyPI
   - Clean, intentional process with clear targeting

5. **Version bumping**: ✅ Manual in `pyproject.toml`
   - Maintainer control over semantic versioning
   - Clear intent before release
   - No surprises from automated bumps

6. **Changelog**: ✅ Hybrid approach
   - Manual: PR description becomes release notes
   - Automated: GitHub auto-generates commit-based changelog
   - Best of both: meaningful summary + detailed commit list

7. **Branch permissions**: ⚙️ Via branch protection rules
   - Main protected: PR required, tests must pass
   - Release happens automatically on merge (OIDC, no manual tokens)
   - GitHub Actions bot creates tags and releases

## Estimated Effort

**Phase 1 (Test workflow)**: 1 hour
- Create `.github/workflows/test.yml` from template
- Test on feature branch PR

**Phase 2 (Branch protection)**: 0.5 hours
- Configure GitHub settings (UI-based)
- Verify with test PR

**Phase 3 (Release workflow)**: 2 hours
- Create `.github/workflows/release.yml` from template
- Setup PyPI Trusted Publishing (GitHub + PyPI side)
- Test with `test-release` label to TestPyPI

**Phase 4 (Integration)**: 0.5 hours
- Verify workflow interactions
- No code changes needed

**Phase 5 (Documentation)**: 1 hour
- Update CLAUDE.md (CI/CD section)
- Create CONTRIBUTING.md
- Add README badges

**Total**: 5 hours (reduced due to complete workflow templates provided)

## Prerequisites and Setup Requirements

### PyPI Trusted Publishing Setup

**Required before Phase 3 (Release workflow)**:

1. **TestPyPI setup** (for testing):
   - Go to https://test.pypi.org/manage/account/publishing/
   - Add new "pending publisher"
   - Repository: `kompre/keecas`
   - Workflow name: `release.yml`
   - Environment name: (leave blank)

2. **Production PyPI setup** (before 1.0.0 release):
   - Go to https://pypi.org/manage/account/publishing/
   - Add new "pending publisher"
   - Repository: `kompre/keecas`
   - Workflow name: `release.yml`
   - Environment name: (leave blank)

3. **Verify OIDC works**:
   - First release should use `test-release` label
   - Confirms TestPyPI publishing works
   - Production release only after successful test

**No API tokens needed** - GitHub OIDC authentication handles everything securely.

## Risks and Mitigations

**Risk**: Branch protection too strict - blocks development
**Mitigation**: Only protecting main, dev remains flexible for iteration

**Risk**: CI runs too slow - developer friction
**Mitigation**: Caching enabled (uv dependencies), concurrency cancels old runs, single Python version

**Risk**: Breaking existing workflows during migration
**Mitigation**: Test + Release workflows are additive, don't modify existing docs.yml

**Risk**: PyPI Trusted Publishing misconfiguration
**Mitigation**: Test with TestPyPI first using `test-release` label before production

**Risk**: Pre-commit hooks become redundant
**Mitigation**: Different purposes - pre-commit for fast feedback, CI for PR gating

## Future Enhancements

- Automated dependency updates (Dependabot)
- Security scanning (CodeQL, Snyk)
- Performance regression testing
- Deployment previews for PRs
- Release announcement automation
- Semantic release automation
- Multi-platform testing (Windows, Linux, macOS)

## Notes

- Project currently on version 0.1.2, targeting 1.0.0
- Backward compatibility not a concern (major version bump)
- Tests: 158 passing, 21 warnings (Pint deprecation)
- Python: 3.12+ required, `.python-version` specifies 3.13
- Build backend: uv (not setuptools)
- Pre-commit already validates docstrings and renders notebooks
- No extras in pyproject.toml, only dev dependencies

## Summary

**What this proposal delivers**:

1. **Automated Testing** - Every PR to main validated by CI
2. **Branch Protection** - Main branch gated by passing tests
3. **Automated Releases** - Label-based PyPI publishing with GitHub Releases
4. **Complete Documentation** - CONTRIBUTING.md, badges, CI/CD guide
5. **Developer Experience** - Clear workflow, fast feedback, no manual steps

**Key features**:
- ✅ Complete workflow templates ready to use
- ✅ PyPI Trusted Publishing (no tokens/secrets)
- ✅ Test + production PyPI support
- ✅ GitHub Release generation with PR notes
- ✅ Pre-commit integration preserved
- ✅ Minimal configuration required (5 hours total)

**Release process** (post-implementation):
```bash
# 1. Bump version
uv version --bump major  # Update version: 0.1.2 → 1.0.0

# 2. Create PR
git checkout -b release/v1.0.0
git commit -am "chore: bump version to 1.0.0"
git push origin release/v1.0.0
gh pr create --base main --label release

# 3. Merge and done
# GitHub Actions handles: tests → build → tag → PyPI → GitHub Release
```

**Ready for approval and implementation.**
