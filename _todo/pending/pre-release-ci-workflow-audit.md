# Pre-Release CI Workflow Audit

**Status**: In Development
**Created**: 2025-11-12
**Approved**: 2025-11-12
**Branch**: claude/pre-release-ci-workflow-audit-011CV4GR3DYguK4G3A5qG9ge
**Original Objective**: Analyze GitHub Actions workflows for main branch triggers and ensure proper protection before PR to main

---

## Development Progress

### 2025-11-12 - Session 1: Implementation Complete
- Created feature branch `feature/pre-release-ci-workflow-audit` from dev
- Moved proposal to pending
- Verified current workflow configurations
- **Implemented Change 1**: Excluded lint-fix.yml from main PRs (removed `main` from PR triggers)
- **Implemented Change 2**: Added path filtering to test.yml using whitelist approach
- **Implemented Change 3**: Expanded docs.yml path filter to include root markdown files and examples
- **Updated CLAUDE.md**: Updated CI Workflows section with detailed path filtering documentation
- All changes ready for commit and push

---

## Executive Summary

After deeper analysis, the current workflow configuration is **nearly optimal** with only one change needed:

**Required Change**: Exclude lint-fix.yml from main PRs (redundant with test.yml)

**Optional Optimization**: Add path filtering to test.yml - but argue AGAINST this based on risk/benefit analysis below.

---

## User Requirements Analysis

### Requirement 1: Test enforcement ✅
**Status**: Already configured correctly
- GitHub branch protection requires test.yml to pass
- test.yml includes linting verification
- No changes needed

### Requirement 2: Lint-fix exclusion ✅
**Status**: Needs implementation
- Remove main from lint-fix.yml PR triggers
- test.yml already verifies linting (read-only)
- Eliminates redundancy and potential conflicts

### Requirement 3: PR-based workflow for everything ✅
**Status**: Already enforced by GitHub settings
- User prefers PR workflow even for docs
- Branch protection prevents direct push to main
- No workflow changes needed for this

---

## Critical Decision: Path Filtering Strategy

You asked: "Why use `paths-ignore` instead of `paths` (src/, tests/, pyproject.toml, uv.lock)? Wouldn't it be easier and more reliable?"

**Answer: You're absolutely right. Using `paths` is superior. Here's why:**

### Option A: paths-ignore (my original proposal)
```yaml
paths-ignore:
  - 'docs/**'
  - '*.md'
  - '_todo/**'
  - 'examples/**'
```

**Problems**:
1. **Maintenance burden**: Must update list whenever new doc-like directories are added
2. **Error-prone**: Easy to forget a pattern, leading to unnecessary test runs
3. **Negative logic**: Defining what to exclude is harder to reason about than what to include
4. **Risk of over-exclusion**: Might accidentally exclude important files

### Option B: paths (your suggestion)
```yaml
paths:
  - 'src/**'
  - 'tests/**'
  - 'pyproject.toml'
  - 'uv.lock'
  - '.github/workflows/**'
```

**Advantages**:
1. **Explicit whitelist**: Only runs tests when files that affect code are changed
2. **Self-documenting**: List clearly shows "these are the files that need testing"
3. **Safer**: Can't accidentally skip tests for important files
4. **Easier maintenance**: New doc directories automatically excluded
5. **Positive logic**: "Run tests FOR these" is clearer than "Run tests EXCEPT for these"

**Recommendation: Use `paths` approach (Option B)**

---

## Counter-Argument: Should We Even Add Path Filtering?

Let me argue AGAINST path filtering entirely:

### Case Against Path Filtering

**Your comment**: "even docs should always be merged as pr"

**Implication**: If all changes go through PRs (including docs), and PRs are cheap to create, is the optimization worth the complexity?

**Risk Analysis**:

1. **False sense of security**
   - What if someone updates README.md with code examples that are now incorrect?
   - What if CONTRIBUTING.md describes a workflow that's broken?
   - Running tests catches these inconsistencies

2. **Maintenance burden**
   - Path filters must be kept in sync with project structure
   - Every workflow change requires careful review of filter accuracy

3. **Cognitive load**
   - Developers must remember: "docs PRs skip tests, code PRs don't"
   - Confusion when tests don't run as expected

4. **GitHub Actions minutes are not the bottleneck**
   - Free tier: 2,000 minutes/month
   - Your test suite runs in ~2-3 minutes
   - Even 100 PRs/month = 300 minutes (15% of quota)
   - Documentation PRs are infrequent

5. **Test suite should be fast anyway**
   - If tests are slow, fix the tests (caching, parallelization)
   - Skipping tests is treating the symptom, not the disease

**Alternative Philosophy**: "Always run tests, make them fast"

### Case For Path Filtering

**However**, there ARE valid reasons to use path filtering:

1. **PR iteration speed**
   - Docs PRs often need multiple small fixes (typos, formatting)
   - Waiting 2-3 minutes for tests on each iteration is frustrating
   - Path filtering reduces PR cycle time from minutes to seconds

2. **CI/CD feedback loops**
   - Faster feedback = better developer experience
   - Docs contributors shouldn't wait for unrelated tests

3. **Resource efficiency at scale**
   - As project grows, test suite will slow down
   - Docs changes become more frequent (community contributions)
   - Optimization pays off long-term

4. **Signal-to-noise ratio**
   - Every test run should be meaningful
   - Running tests on docs changes is "green checkmark noise"
   - Makes it harder to spot real test failures

**My Recommendation**: Implement path filtering using `paths` approach, but with conservative scope:

```yaml
on:
  pull_request:
    branches: [ main, dev ]
    paths:
      - 'src/**'
      - 'tests/**'
      - 'pyproject.toml'
      - 'uv.lock'
      - '.github/workflows/**' # ok for all workflows
      - 'scripts/**'  # Scripts could affect tests
```

**Rationale**:
- Examples can be ignored (already have `examples/**` path in docs.yml)
- `_todo/**` is planning docs, not code
- Root `*.md` files are documentation, not code
- CI workflow changes should trigger tests (workflow might be broken)

---

## Refined Implementation Plan

### Change 1: Exclude lint-fix from main PRs (REQUIRED)

**File**: `.github/workflows/lint-fix.yml`

**Current**:
```yaml
on:
  push:
    branches:
      - dev
      - 'feature/**'
  pull_request:
    branches: [ main, dev ]
```

**Proposed**:
```yaml
on:
  push:
    branches:
      - dev
      - 'feature/**'
  pull_request:
    branches: [ dev ]  # Remove main
```

**Rationale**: test.yml already verifies linting on main PRs (read-only). Auto-fix is only needed for dev/feature branches where rapid iteration happens.

---

### Change 2: Add path filtering to test.yml (RECOMMENDED)

**File**: `.github/workflows/test.yml`

**Current**:
```yaml
on:
  pull_request:
    branches: [ main, dev ]
```

**Proposed** (using `paths` whitelist):
```yaml
on:
  pull_request:
    branches: [ main, dev ]
    paths:
      - 'src/**'
      - 'tests/**'
      - 'pyproject.toml'
      - 'uv.lock'
      - '.github/workflows/**' 
      - 'scripts/**'
```

**Alternative** (using `paths-ignore` blacklist):
```yaml
on:
  pull_request:
    branches: [ main, dev ]
    paths-ignore:
      - 'docs/**'
      - '*.md'
      - 'README.md'
      - 'CHANGELOG.md'
      - 'CONTRIBUTING.md'
      - 'LICENSE'
      - '_todo/**'
      - 'examples/**'
```

**I strongly recommend the `paths` whitelist approach** for reasons explained above.

---

### Change 3: Expand docs.yml path filter (OPTIONAL)

**File**: `.github/workflows/docs.yml`

**Current**:
```yaml
on:
  push:
    branches: [main, dev]
    paths:
      - 'docs/**'
      - 'src/keecas/**/*.py'
      - 'scripts/update_docs.py'
      - '.github/workflows/docs.yml'
```

**Proposed**:
```yaml
on:
  push:
    branches: [main, dev]
    paths:
      - 'docs/**'
      - 'src/keecas/**/*.py'
      - 'scripts/update_docs.py'
      - '.github/workflows/docs.yml'
      - '*.md'  # Root markdown files
      - 'README.md'
      - 'CHANGELOG.md'
      - 'examples/**'  # Example notebooks might be linked in docs
```

**Rationale**: README changes should trigger docs rebuild since it's often the entry point to documentation.

---

## Workflow Scenarios

### Scenario 1: Code PR to main
**Files changed**: `src/keecas/display.py`, `tests/test_display.py`

**Workflows**:
- ✅ test.yml RUNS (matches `src/**` and `tests/**` paths)
- ❌ lint-fix.yml SKIPPED (excluded main PRs)
- ❌ check-release-version.yml SKIPPED (no release label)

**Outcome**: Tests must pass before merge (enforced by branch protection)

---

### Scenario 2: Docs PR to main
**Files changed**: `docs/guide.qmd`, `README.md`

**Workflows**:
- ❌ test.yml SKIPPED (no matching paths)
- ❌ lint-fix.yml SKIPPED (excluded main PRs)
- ❌ check-release-version.yml SKIPPED (no release label)

**Outcome**: PR can merge immediately, then docs.yml deploys on push to main

**Important**: Since test.yml is required but skipped, GitHub automatically allows merge. This is documented behavior: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/troubleshooting-required-status-checks#handling-skipped-but-required-checks

---

### Scenario 3: Mixed PR (code + docs) to main
**Files changed**: `src/keecas/display.py`, `docs/guide.qmd`

**Workflows**:
- ✅ test.yml RUNS (matches `src/**` path)
- ❌ lint-fix.yml SKIPPED (excluded main PRs)
- ❌ check-release-version.yml SKIPPED (no release label)

**Outcome**: Tests must pass. This is correct - if code changed, docs should be consistent.

---

### Scenario 4: Release PR to main (with `release` label)
**Files changed**: `pyproject.toml` (version bump), optionally `src/**`, `docs/**`

**Workflows**:
- ✅ test.yml RUNS (matches `pyproject.toml` path)
- ❌ lint-fix.yml SKIPPED (excluded main PRs)
- ✅ check-release-version.yml RUNS (has release label)

**Outcome**: Both tests and version validation must pass

**Post-merge**:
- release.yml runs (tests again, tags, builds, publishes to PyPI)
- docs.yml runs (rebuilds docs with new version)

---

### Scenario 5: Dependency update PR to main
**Files changed**: `pyproject.toml`, `uv.lock`

**Workflows**:
- ✅ test.yml RUNS (matches both paths)
- ❌ lint-fix.yml SKIPPED (excluded main PRs)
- ❌ check-release-version.yml SKIPPED (no release label)

**Outcome**: Tests must pass. This is critical - dependency changes can break code.

---

## Edge Cases and Gotchas

### Edge Case 1: CI workflow changes
**Files changed**: `.github/workflows/test.yml`

**Question**: Should workflow changes trigger tests?

**Answer**: YES. Workflow changes could break the test pipeline itself.

**Solution**: Include CI workflow files in `paths` filter:
```yaml
paths:
  - 'src/**'
  - 'tests/**'
  - '.github/workflows/test.yml'
  - '.github/workflows/lint-fix.yml'
```

---

### Edge Case 2: Script changes
**Files changed**: `scripts/validate_docstrings.py`

**Question**: Should script changes trigger tests?

**Answer**: YES. Scripts are used by tests (see test.yml line 59: `uv run python scripts/validate_docstrings.py`)

**Solution**: Include `scripts/**` in `paths` filter

---

### Edge Case 3: Hidden files
**Files changed**: `.python-version`

**Question**: Should hidden file changes trigger tests?

**Answer**: YES. Python version changes could break compatibility.

**Solution**: Either:
- Add explicit `.python-version` to `paths` filter, OR // this
- Don't use path filtering at all (conservative approach)

---

### Edge Case 4: Examples with code
**Files changed**: `examples/hello_world.ipynb`

**Question**: Should example changes trigger tests?

**Answer**: NO. Examples are documentation, not source code. They're tested by docs.yml (Quarto render with `--execute`).

**Solution**: Exclude examples from test.yml paths filter

---

## Final Recommendation

### Minimal Change (Conservative)
**Only implement Change 1**: Exclude lint-fix from main PRs

**Pros**:
- Low risk
- Solves the immediate redundancy issue
- No path filtering complexity

**Cons**:
- Docs PRs still wait for test suite
- Less efficient use of CI minutes

**Use this if**: You want maximum safety and docs PRs are infrequent

---

### Optimized Change (Recommended)
**Implement Changes 1 + 2**: Exclude lint-fix + add path filtering to test.yml

**Pros**:
- Fast docs PR iteration
- Better developer experience
- Still safe (whitelist approach)

**Cons**:
- More complex workflow configuration
- Must maintain path filter as project evolves

**Use this if**: You want better CI efficiency and expect frequent docs contributions

---

## Implementation: Optimized Approach

### Step 1: Update lint-fix.yml
```yaml
name: Auto-fix Linting Issues

on:
  push:
    branches:
      - dev
      - 'feature/**'
  pull_request:
    branches: [ dev ]  # Removed main

# ... rest unchanged
```

### Step 2: Update test.yml
```yaml
name: Run Tests

on:
  pull_request:
    branches: [ main, dev ]
    paths:
      - 'src/**'
      - 'tests/**'
      - 'pyproject.toml'
      - 'uv.lock'
      - '.python-version'
      - '.github/workflows/test.yml'
      - '.github/workflows/lint-fix.yml'
      - 'scripts/**'

# ... rest unchanged
```

**Note**: Using explicit whitelist (`paths`) instead of blacklist (`paths-ignore`) for better maintainability.

### Step 3: Update docs.yml (optional)
```yaml
name: Build and Deploy Documentation

on:
  push:
    branches: [main, dev]
    paths:
      - 'docs/**'
      - 'src/keecas/**/*.py'
      - 'scripts/update_docs.py'
      - '.github/workflows/docs.yml'
      - '*.md'
      - 'README.md'
      - 'CHANGELOG.md'
      - 'examples/**'
  workflow_run:
    workflows: ["Release"]
    types: [completed]
  workflow_dispatch:

# ... rest unchanged
```

---

## Validation Plan

### Test 1: Docs-only PR
```bash
git checkout -b docs/fix-typo
echo "fix typo" >> docs/guide.qmd
git commit -am "docs: fix typo"
gh pr create --base main
```

**Expected**:
- No workflows run
- PR shows "No checks" status (skipped, not failed)
- Can merge immediately
- After merge, docs.yml deploys

---

### Test 2: Code-only PR
```bash
git checkout -b fix/display-bug
echo "# bugfix" >> src/keecas/display.py
git commit -am "fix: resolve display bug"
gh pr create --base main
```

**Expected**:
- test.yml runs
- Must pass before merge
- lint-fix does NOT run (excluded main)

---

### Test 3: Mixed PR
```bash
git checkout -b feat/new-feature
echo "# feature" >> src/keecas/display.py
echo "# docs" >> docs/guide.qmd
git commit -am "feat: add feature with docs"
gh pr create --base main
```

**Expected**:
- test.yml runs (triggered by src/ change)
- Must pass before merge

---

### Test 4: Dependency PR
```bash
git checkout -b chore/update-deps
uv add --dev pytest-cov
git commit -am "chore: add pytest-cov"
gh pr create --base main
```

**Expected**:
- test.yml runs (triggered by pyproject.toml + uv.lock)
- Must pass before merge (critical for dependency changes)

---

## GitHub Branch Protection Settings

**Settings → Branches → main**

```
☑ Require a pull request before merging
  Required approvals: 0  # Solo maintainer
  ☐ Dismiss stale pull request approvals when new commits are pushed
  ☑ Require approval of the most recent reviewable push

☑ Require status checks to pass before merging
  ☑ Require branches to be up to date before merging
  Status checks that are required:
    - test / test

☑ Require conversation resolution before merging

☑ Require linear history

☑ Do not allow bypassing the above settings
  (Even admins cannot bypass)
```

**Important**:
- test.yml is required, but GitHub automatically allows merge when skipped by path filter
- You cannot push directly to main (PR required for all changes)
- Linear history prevents merge commits

---

## Documentation Updates for CLAUDE.md

Add this section after implementation:

```markdown
## CI/CD Workflows and Main Branch Protection

### Workflow Triggers

**test.yml** - Runs on PR to main/dev when these paths change:
- `src/**` - Source code
- `tests/**` - Test files
- `pyproject.toml`, `uv.lock` - Dependencies
- `.python-version` - Python version
- `.github/workflows/**` - CI workflows
- `scripts/**` - Build/validation scripts

**lint-fix.yml** - Runs on:
- Push to dev/feature branches (auto-fixes and commits)
- PR to dev branch (auto-fixes and commits)
- Does NOT run on PR to main (test.yml already checks linting)

**docs.yml** - Runs on push to main/dev when these paths change:
- `docs/**` - Documentation source
- `src/**/*.py` - API documentation
- `*.md` - Root markdown files
- `examples/**` - Example notebooks

**check-release-version.yml** - Runs on PR to main with `release` or `test-release` label

### PR Workflow Examples

**Documentation changes**:
```bash
git checkout -b docs/update-guide
# Edit docs/guide.qmd or README.md
git commit -am "docs: update getting started guide"
gh pr create --base main
```
- No tests run (docs paths excluded)
- Can merge immediately
- docs.yml deploys after merge

**Code changes**:
```bash
git checkout -b fix/bug
# Edit src/keecas/display.py
git commit -am "fix: resolve display bug"
gh pr create --base main
```
- test.yml runs and must pass
- Includes linting verification
- Cannot merge until tests pass

**Releases**:
```bash
git checkout -b release/v1.1.0
uv version --bump minor
git commit -am "chore: bump version to 1.1.0"
gh pr create --base main --label release
```

- test.yml runs (pyproject.toml changed)
- check-release-version.yml runs (release label)
- Both must pass before merge
- After merge: release.yml tags, builds, publishes to PyPI


---

## Risk Assessment

### Low Risk Changes
- ✅ Excluding lint-fix from main PRs (no behavioral change, just removes redundancy)

### Medium Risk Changes
- ⚠️ Adding path filtering to test.yml (could skip tests for important files if filter is wrong)

### Mitigation Strategies
1. **Conservative path whitelist**: Only include known code paths
2. **Include workflow files**: Workflow changes should trigger tests
3. **Include dependency files**: pyproject.toml, uv.lock, .python-version
4. **Monitor first few PRs**: Verify workflows trigger correctly
5. **Easy rollback**: Remove `paths:` section from test.yml if issues arise

---

## Conclusion

**Recommended Actions**:
1. ✅ Implement Change 1 (exclude lint-fix from main) - REQUIRED
2. ✅ Implement Change 2 (path filtering with whitelist) - RECOMMENDED
3. ✅ Implement Change 3 (expand docs.yml paths) - OPTIONAL

**Key Insight**: Using `paths` whitelist is superior to `paths-ignore` blacklist for maintainability and safety.

**Philosophy**: Optimize for common case (docs PRs are fast) while maintaining safety for critical case (code PRs are tested).

Ready to proceed with implementation?
