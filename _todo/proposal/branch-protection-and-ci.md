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
- Branch protection on `main` and `dev` branches
- Required CI checks before merge
- Automated test runs on PRs
- Release workflow automation
- Clear separation: dev → main → release

## Example Workflows

<!-- User will provide example workflows here -->

### Example 1: Test Workflow
```yaml
# User to provide
```

### Example 2: Release Workflow
```yaml
# User to provide
```

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

<!-- To be detailed after reviewing example workflows -->

1. Create `.github/workflows/test.yml`
   - Run on: PR to main/dev, push to branches
   - Matrix testing across Python versions?
   - Test coverage reporting
   - Linting with Ruff
   - Docstring validation
   - Integration with pre-commit checks

2. Configure test job requirements
   - Python version matrix or single version?
   - Dependencies installation (uv sync)
   - Pytest configuration
   - Coverage thresholds?

### Phase 2: Branch Protection Rules

1. **main branch protection**:
   - Require PR reviews?
   - Require status checks to pass (test workflow)
   - Require branches to be up to date
   - Restrict direct pushes
   - Allow force pushes? (usually no)

2. **dev branch protection**:
   - Require status checks to pass
   - Less restrictive than main?
   - Allow direct pushes from maintainers?

### Phase 3: Release Workflow

<!-- To be detailed after reviewing example workflows -->

1. Create `.github/workflows/release.yml`
   - Trigger: Manual dispatch? Tag push? PR to main?
   - Version bumping strategy
   - Changelog generation
   - GitHub release creation
   - PyPI publishing integration (coordinate with existing proposal)

2. Release process
   - Semantic versioning enforcement
   - Git tag creation
   - Release notes automation
   - Asset uploads (wheel, sdist)

### Phase 4: Integration with Existing Workflows

1. Update docs workflow
   - Trigger on releases?
   - Deploy versioned docs?
   - Maintain dev/main doc separation

2. Pre-commit hook coordination
   - Keep local validation for fast feedback
   - CI as final gatekeeper
   - Avoid duplicate work

### Phase 5: Documentation and Developer Experience

1. Update CLAUDE.md with CI/CD patterns
2. Document branch strategy in README
3. Create CONTRIBUTING.md with PR workflow
4. Add status badges to README

## Branch Strategy

**Proposed workflow**:
```
feature-branches → dev → main → release (tags)
                    ↓      ↓
                  tests  tests + stricter rules
```

**Details**:
- Feature branches merge to `dev` via PR
- `dev` → `main` merge requires review + all checks
- Releases created from `main` via tags or manual trigger
- Version: Currently 0.1.2, targeting 1.0.0

## Dependencies

**Coordinates with**:
- [github-actions-pypi-publishing.md](proposal/github-actions-pypi-publishing.md) - PyPI release integration
- Existing docs workflow (`.github/workflows/docs.yml`)

**Blocks**:
- Branch protection must be configured before 1.0.0 release
- Test workflow needed before enabling required status checks

## Questions for User

1. **Test matrix**: Single Python version (3.13) or matrix (3.12, 3.13)?
2. **PR reviews**: Required on main? Required on dev?
3. **Coverage requirements**: Enforce minimum test coverage percentage?
4. **Release trigger**: Manual dispatch, tag push, or PR merge to main?
5. **Version bumping**: Manual in pyproject.toml or automated?
6. **Changelog**: Auto-generate from commits or manual?
7. **Branch permissions**: Who can merge to main? Who can create releases?

## Estimated Effort

**Phase 1 (Test workflow)**: 2-3 hours
- Workflow file creation: 1 hour
- Testing and debugging: 1-2 hours

**Phase 2 (Branch protection)**: 1 hour
- GitHub settings configuration
- Testing merge requirements

**Phase 3 (Release workflow)**: 3-4 hours
- Workflow creation: 2 hours
- Version/changelog automation: 1-2 hours

**Phase 4 (Integration)**: 1 hour
- Docs workflow updates
- Workflow coordination

**Phase 5 (Documentation)**: 1 hour
- CLAUDE.md updates
- CONTRIBUTING.md creation

**Total**: 8-10 hours

## Risks and Mitigations

**Risk**: Branch protection too strict - blocks development
**Mitigation**: Start with dev branch, iterate, then apply to main

**Risk**: CI runs too slow - developer friction
**Mitigation**: Optimize test suite, use caching, consider matrix strategy

**Risk**: Breaking existing workflows during migration
**Mitigation**: Test workflows on feature branch first, gradual rollout

**Risk**: Overly complex release process
**Mitigation**: Start simple (manual trigger), automate incrementally

**Risk**: Pre-commit hooks become redundant
**Mitigation**: Keep for fast local feedback, CI as final gate

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
- Python: 3.12+ required, currently testing on 3.13
- Build backend: uv (not setuptools)
- Pre-commit already validates docstrings and renders notebooks

## User Input Required

**Please provide**:
1. Example test workflow YAML
2. Example release workflow YAML
3. Answers to questions above
4. Any specific GitHub Actions or tools you prefer
5. Branch protection preferences
