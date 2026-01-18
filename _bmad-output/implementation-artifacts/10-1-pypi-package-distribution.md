# Story 10.1: PyPI Package Distribution

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer wanting to use resume-as-code**,
I want **to install the tool via `pip install resume-as-code`**,
So that **I can easily set up and use the CLI without cloning the repository**.

## Acceptance Criteria

1. **Given** the package is published to PyPI
   **When** a user runs `pip install resume-as-code`
   **Then** the `resume` CLI command is available globally
   **And** all required dependencies are installed automatically

2. **Given** the pyproject.toml configuration
   **When** building the package
   **Then** the following metadata is included:
   - Name: `resume-as-code`
   - Version: dynamically from `__version__`
   - Description: Clear one-liner about the tool
   - Keywords: resume, cli, job-search, career
   - Classifiers: Python versions, license, topic
   - Project URLs: homepage, documentation, repository, issues

3. **Given** the package has optional features
   **When** a user wants LLM or NLP capabilities
   **Then** they can install extras: `pip install resume-as-code[llm]` or `pip install resume-as-code[nlp]`

4. **Given** a new version tag is pushed to GitHub
   **When** the GitHub Actions workflow triggers
   **Then** the package is automatically built and published to PyPI
   **And** a GitHub Release is created with changelog

5. **Given** the package is published
   **When** viewing the PyPI page
   **Then** the README is rendered correctly
   **And** all links work (docs, repo, issues)

6. **Given** a release workflow
   **When** preparing to publish
   **Then** tests must pass before publish
   **And** package is first published to TestPyPI for validation
   **And** then published to PyPI after TestPyPI verification

7. **Given** the installed package
   **When** running `resume --version`
   **Then** the version matches the published PyPI version

## Tasks / Subtasks

- [ ] Task 1: Update pyproject.toml metadata (AC: #2, #3)
  - [ ] 1.1 Add comprehensive classifiers (Python 3.10-3.13, MIT, Topic::Utilities)
  - [ ] 1.2 Add keywords for discoverability
  - [ ] 1.3 Add project URLs (homepage, docs, repository, issues, changelog)
  - [ ] 1.4 Verify optional dependencies are properly defined (llm, nlp, dev)
  - [ ] 1.5 Add `dynamic = ["version"]` with hatch-vcs or `__version__.py`

- [ ] Task 2: Create version management (AC: #7)
  - [ ] 2.1 Create `src/resume_as_code/__version__.py` with `__version__`
  - [ ] 2.2 Update `cli.py` to read version from `__version__.py`
  - [ ] 2.3 Configure pyproject.toml to use dynamic version
  - [ ] 2.4 Ensure version is single source of truth

- [ ] Task 3: Create GitHub Actions release workflow (AC: #4, #6)
  - [ ] 3.1 Create `.github/workflows/release.yml`
  - [ ] 3.2 Trigger on version tags (`v*.*.*`)
  - [ ] 3.3 Run full test suite before build
  - [ ] 3.4 Build wheel and sdist with `hatch build`
  - [ ] 3.5 Publish to TestPyPI first
  - [ ] 3.6 Run smoke test against TestPyPI package
  - [ ] 3.7 Publish to PyPI
  - [ ] 3.8 Create GitHub Release with auto-generated notes

- [ ] Task 4: Configure PyPI publishing (AC: #1, #5)
  - [ ] 4.1 Create PyPI account and project (manual)
  - [ ] 4.2 Create TestPyPI account and project (manual)
  - [ ] 4.3 Set up trusted publisher (GitHub OIDC) for both
  - [ ] 4.4 Add `PYPI_API_TOKEN` and `TEST_PYPI_API_TOKEN` to GitHub secrets
  - [ ] 4.5 Verify README renders on TestPyPI

- [ ] Task 5: Documentation updates (AC: #5)
  - [ ] 5.1 Add PyPI badge to README.md
  - [ ] 5.2 Add installation section: `pip install resume-as-code`
  - [ ] 5.3 Document optional extras in README
  - [ ] 5.4 Add version badge

- [ ] Task 6: Local build and test validation
  - [ ] 6.1 Run `hatch build` locally and verify wheel/sdist
  - [ ] 6.2 Install from local wheel in fresh venv
  - [ ] 6.3 Verify `resume --version` works
  - [ ] 6.4 Verify `resume --help` shows all commands
  - [ ] 6.5 Run basic smoke test (init, new, plan, build)

## Dev Notes

### Current State Analysis

**What exists:**
- `pyproject.toml` with basic metadata (name, version 0.1.0, description)
- Build system: hatchling
- Entry point: `resume = "resume_as_code.cli:main"`
- Optional dependencies: dev, llm, nlp
- Package structure: `src/resume_as_code/`

**Gaps:**
- No classifiers or keywords
- No project URLs
- Version hardcoded (not dynamic)
- No release workflow
- No PyPI publishing configuration

### Implementation Pattern

**Updated pyproject.toml sections:**
```toml
[project]
name = "resume-as-code"
dynamic = ["version"]
description = "CLI tool for git-native resume generation from structured work units"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
  { name = "Joshua Magady", email = "Josh.Magady@gmail.com" },
]
keywords = [
  "resume",
  "cv",
  "cli",
  "job-search",
  "career",
  "job-description",
  "pdf",
  "docx",
  "git",
  "yaml",
]
classifiers = [
  "Development Status :: 4 - Beta",
  "Environment :: Console",
  "Intended Audience :: End Users/Desktop",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: MIT License",
  "Operating System :: OS Independent",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Programming Language :: Python :: 3.13",
  "Topic :: Office/Business",
  "Topic :: Text Processing :: Markup",
  "Topic :: Utilities",
  "Typing :: Typed",
]

[project.urls]
Homepage = "https://github.com/drbothen/resume-as-code"
Documentation = "https://drbothen.github.io/resume-as-code/"
Repository = "https://github.com/drbothen/resume-as-code"
Issues = "https://github.com/drbothen/resume-as-code/issues"
Changelog = "https://github.com/drbothen/resume-as-code/releases"

[tool.hatch.version]
path = "src/resume_as_code/__version__.py"
```

**Version file (`src/resume_as_code/__version__.py`):**
```python
"""Version information for resume-as-code."""

__version__ = "0.1.0"
```

**GitHub Actions workflow (`.github/workflows/release.yml`):**
```yaml
name: Release to PyPI

on:
  push:
    tags:
      - 'v*.*.*'

permissions:
  contents: write
  id-token: write

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      - name: Install dependencies
        run: uv sync --all-extras
      - name: Run tests
        run: uv run pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install build tools
        run: pip install build
      - name: Build package
        run: python -m build
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish-testpypi:
    needs: build
    runs-on: ubuntu-latest
    environment: testpypi
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/

  smoke-test:
    needs: publish-testpypi
    runs-on: ubuntu-latest
    steps:
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Wait for TestPyPI propagation
        run: sleep 60
      - name: Install from TestPyPI
        run: |
          pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            resume-as-code
      - name: Smoke test
        run: |
          resume --version
          resume --help

  publish-pypi:
    needs: smoke-test
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1

  github-release:
    needs: publish-pypi
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
          files: |
            dist/*
```

### Dependencies

- **Depends on:** None (can be done independently)
- **Blocked by:** None
- **Enables:** Wider adoption, easier installation

### Testing Strategy

**Local validation:**
```bash
# Build locally
hatch build

# Create fresh venv and install
python -m venv /tmp/test-resume
source /tmp/test-resume/bin/activate
pip install dist/resume_as_code-*.whl

# Verify
resume --version
resume --help
resume init --non-interactive
```

**TestPyPI validation:**
```bash
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  resume-as-code

# Verify
resume --version
```

### Manual Steps Required

1. **Create PyPI account:** https://pypi.org/account/register/
2. **Create TestPyPI account:** https://test.pypi.org/account/register/
3. **Configure trusted publisher:**
   - PyPI: Project Settings → Publishing → Add trusted publisher
   - Repository: `drbothen/resume-as-code`
   - Workflow: `release.yml`
   - Environment: `pypi`
4. **Same for TestPyPI** with environment: `testpypi`

### Project Context Rules

From `project-context.md`:
- Use `uv` for local development
- Hatchling as build backend
- Follow conventional commits for releases
- Run full test suite before publishing

### References

- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [Hatch Version Management](https://hatch.pypa.io/latest/version/)
- [GitHub Actions PyPI Publish](https://github.com/pypa/gh-action-pypi-publish)
- [Source: pyproject.toml - current build configuration]

## Estimation

**Points:** 5
**Complexity:** Medium
**Risk:** Low (well-documented process)

## Notes

- First release should be `0.1.0` (current version)
- Consider using `hatch-vcs` for git-tag-based versioning in future
- May need to reserve package name on PyPI before first publish
