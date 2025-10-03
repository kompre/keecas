# GitHub Actions for PyPI Publishing

## Original Objective
Setup GitHub Actions for building and publishing package to PyPI. Publishing should happen on new tag creation, and tag numbers should match version numbers in pyproject.toml.

## Context
- Current version: 0.1.2 (preparing for 1.0.0)
- Existing GitHub Actions: `.github/workflows/docs.yml` for documentation
- Build backend: `uv_build`
- Package manager: `uv`
- Breaking changes acceptable (major version bump)

## Implementation Plan

### 1. Create PyPI Publishing Workflow
**File**: `.github/workflows/publish.yml`

**Workflow structure**:
- **Trigger**: On tag push matching `v*.*.*` pattern (e.g., `v1.0.0`)
- **Jobs**:
  1. **validate-version**: Verify tag matches pyproject.toml version
  2. **build**: Build wheel and sdist using `uv build`
  3. **test-build**: Install and run tests on built package (not source)
  4. **publish-testpypi**: Upload to TestPyPI for verification
  5. **publish-pypi**: Upload to PyPI (requires manual approval gate)

**Key features**:
- Version validation before any build/publish steps
- Automated build artifact uploads
- TestPyPI upload for pre-release verification
- Production PyPI requires environment approval (manual gate)
- Build matrix: Test on Python 3.12, 3.13
- Platform matrix: Linux, macOS, Windows

**Secrets required**:
- `PYPI_API_TOKEN`: PyPI API token for production releases
- `TEST_PYPI_API_TOKEN`: TestPyPI token for test releases

### 2. Create Version Validation Script
**File**: `scripts/validate_version.py`

**Purpose**: Ensure git tag version matches pyproject.toml version

**Logic**:
```python
import sys
import toml
from pathlib import Path

def validate_version(tag_name):
    # Read version from pyproject.toml
    pyproject = toml.load(Path("pyproject.toml"))
    package_version = pyproject["project"]["version"]

    # Extract version from tag (remove 'v' prefix)
    tag_version = tag_name.lstrip('v')

    # Compare
    if package_version != tag_version:
        print(f"ERROR: Tag {tag_name} doesn't match package version {package_version}")
        sys.exit(1)

    print(f"✓ Version validated: {package_version}")

if __name__ == "__main__":
    tag_name = sys.argv[1] if len(sys.argv) > 1 else ""
    validate_version(tag_name)
```

### 3. Update Repository Settings

**GitHub Repository Configuration**:
1. **Environments**:
   - Create `pypi` environment with manual approval requirement
   - Add `PYPI_API_TOKEN` secret to `pypi` environment
   - Add `TEST_PYPI_API_TOKEN` to repository secrets

2. **Branch Protection** (optional but recommended): 
<!-- yes -->
   - Protect `main` branch
   - Require PR reviews before merging
   - Require status checks to pass

3. **Tags**:
   - Document tag naming convention in README 
   - Tag format: `v{major}.{minor}.{patch}` (e.g., `v1.0.0`)

### 4. Create Release Workflow Documentation
**File**: `docs/contributing/releases.md`

**Content**:
- Step-by-step release process
- Version bumping guidelines
- Tag creation commands
- Rollback procedures
- TestPyPI verification steps

**Release checklist**:
1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Update version references in documentation
4. Commit changes: `git commit -m "chore: Bump version to X.Y.Z"`
5. Create and push tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
6. Monitor GitHub Actions workflow
7. Verify TestPyPI upload
8. Approve PyPI production deployment
9. Create GitHub release with changelog

<!-- 

there should be a way for automatic version bumping connected to the workflow. Avoid manual change.

-->

### 5. Add Pre-release Testing Job

**Additional workflow step**:
- Install package from built wheel (not from source)
- Run full test suite: `uv run pytest`
- Verify CLI entry point: `keecas --version`
- Test import integrity: `python -c "import keecas; print(keecas.__version__)"`

### 6. Implement Rollback Strategy

**Rollback procedures**:
- PyPI doesn't allow file deletion (only yanking)
- Document how to yank releases: `twine upload --repository pypi --yank <version>`
- Immediate patch release process for critical bugs
- Communication plan for failed releases

## Testing Strategy

### Pre-Merge Testing
1. Create test tag on feature branch
2. Verify version validation script works
3. Test build process locally: `uv build`
4. Verify built package installs: `pip install dist/*.whl`

<!-- 

I don't want to have build folder in the directory

 -->

### Post-Merge Testing
1. Create test tag on main branch: `v0.1.3-rc1`
2. Monitor workflow execution
3. Verify TestPyPI upload: `pip install -i https://test.pypi.org/simple/ keecas`
4. Test installed package functionality
5. Delete test release and tag if successful

## Implementation Steps

1. **Create validation script** (`scripts/validate_version.py`)
2. **Create publish workflow** (`.github/workflows/publish.yml`)
3. **Test workflow** with release candidate tag
4. **Configure GitHub secrets** for PyPI tokens
5. **Create release documentation** (`docs/contributing/releases.md`)
6. **Update README** with release badge and process

## Acceptance Criteria

- ✅ GitHub Actions workflow triggers on `v*.*.*` tags
- ✅ Workflow validates tag matches pyproject.toml version
- ✅ Package builds successfully using `uv build`
- ✅ Built package passes full test suite
- ✅ TestPyPI upload succeeds automatically
- ✅ PyPI production upload requires manual approval
- ✅ Failed version validation blocks publishing
- ✅ Documentation exists for release process
- ✅ Rollback procedure documented

## Dependencies
- None (standalone task)

## Estimated Effort
- Implementation: 2-3 hours
- Testing: 1-2 hours
- Documentation: 1 hour
- **Total**: 4-6 hours

## Risks and Mitigations

**Risk**: Accidental production publish
**Mitigation**: Manual approval gate for PyPI environment

**Risk**: Version mismatch goes unnoticed
**Mitigation**: Validation script runs first, fails entire workflow

**Risk**: Build failures on specific platforms
**Mitigation**: Multi-platform build matrix, fail fast on errors

**Risk**: PyPI token exposure
**Mitigation**: Use GitHub environment secrets, never commit tokens

## Notes
- Keep existing `docs.yml` workflow intact
- Consider adding workflow_dispatch trigger for manual testing
- TestPyPI has different package name rules (may need unique name)
- PyPI package name `keecas` should be reserved before first publish

<!-- keecas is already present on pypi -->