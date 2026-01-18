# Release Process

This document describes how to release new versions of `resume-as-code`.

## Overview

The release process uses GitHub Actions with multiple safeguards:

1. **Validate** - Check version format, match with `__version__.py`, prevent duplicates
2. **Test** - Run full test matrix (Python 3.10-3.13)
3. **Build** - Create and verify wheel/sdist
4. **Publish to TestPyPI** - Smoke test the package
5. **Publish to PyPI** - Final release
6. **GitHub Release** - Auto-generated release notes

## Release Methods

### Method 1: Prepare-Release Workflow (Recommended)

Use this for standard releases. It auto-determines the version from conventional commits.

1. Go to **Actions** → **Prepare Release** → **Run workflow**
2. Optionally override the version or enable dry-run
3. The workflow creates a release PR with:
   - Updated `__version__.py`
   - Updated `CHANGELOG.md`
   - Calculated version based on commits
4. Review and merge the PR
5. After merge, run the Release workflow (Method 2 or 3)

### Method 2: Manual Dispatch (Quick Release)

Use this when `__version__.py` is already updated.

1. Go to **Actions** → **Release to PyPI** → **Run workflow**
2. Enter the version (must match `__version__.py`)
3. Optionally skip TestPyPI for hotfixes
4. The workflow validates, tests, builds, and publishes

### Method 3: Git Tag (Traditional)

Use this for local release control.

```bash
# Ensure version is updated in __version__.py
git checkout main && git pull

# Create and push tag
git tag v0.2.0
git push origin v0.2.0
```

The tag push triggers the release workflow automatically.

## Version Bump Rules

Based on [Conventional Commits](https://www.conventionalcommits.org/):

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `feat!:` or `BREAKING CHANGE:` | Major (X.0.0) | `feat!: remove deprecated API` |
| `feat:` | Minor (0.X.0) | `feat: add new command` |
| `fix:`, `perf:`, etc. | Patch (0.0.X) | `fix: handle edge case` |

## Safeguards

The release workflow includes multiple checks:

- **Version format validation** - Must be semver (X.Y.Z or X.Y.Z-suffix)
- **Version consistency** - Release version must match `__version__.py`
- **Duplicate prevention** - Checks PyPI and git tags for existing versions
- **Concurrency lock** - Only one release can run at a time
- **TestPyPI smoke test** - Installs and tests before PyPI publish

## Environments

Configure these in GitHub repository settings:

### `testpypi` Environment

1. Go to **Settings** → **Environments** → **New environment**
2. Name: `testpypi`
3. Add trusted publisher on [TestPyPI](https://test.pypi.org/manage/account/publishing/):
   - **PyPI Project Name:** `resume-as-code-ng`
   - Owner: `drbothen`
   - Repository: `resume-as-code`
   - Workflow: `release.yml`
   - Environment: `testpypi`

### `pypi` Environment

1. Go to **Settings** → **Environments** → **New environment**
2. Name: `pypi`
3. Consider adding required reviewers for production releases
4. Add trusted publisher on [PyPI](https://pypi.org/manage/account/publishing/):
   - **PyPI Project Name:** `resume-as-code-ng`
   - Owner: `drbothen`
   - Repository: `resume-as-code`
   - Workflow: `release.yml`
   - Environment: `pypi`

## Local Testing

Before releasing, you can test the build locally:

```bash
# Run tests
uv run pytest -v

# Build package
uv build

# Verify wheel contents
unzip -l dist/*.whl | grep -E "resume_as_code|archetypes"

# Test installation
pip install dist/*.whl
resume --version
```

## Troubleshooting

### "Version mismatch" error

The release version doesn't match `__version__.py`. Either:
- Update `__version__.py` first, or
- Use the prepare-release workflow

### "Version already exists on PyPI" error

That version was already published. Bump to a new version.

### "Tag already exists" error

Delete the tag and recreate, or use a new version:
```bash
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0
```

### TestPyPI publish fails

Check the trusted publisher configuration on TestPyPI. The workflow name and environment must match exactly.
