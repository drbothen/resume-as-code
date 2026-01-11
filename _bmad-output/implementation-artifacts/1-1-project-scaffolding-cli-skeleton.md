# Story 1.1: Project Scaffolding & CLI Skeleton

Status: done

## Story

As a **developer**,
I want **a properly structured Python CLI project with a working entry point**,
So that **I have a foundation to build all resume commands upon**.

## Acceptance Criteria

1. **Given** the project is cloned and dependencies installed
   **When** I run `resume --help`
   **Then** I see the CLI help output with available commands listed
   **And** the exit code is 0

2. **Given** the project structure exists
   **When** I inspect the directory
   **Then** I find `pyproject.toml` with all dependencies per Architecture spec
   **And** I find `src/resume_as_code/` with `__init__.py`, `__main__.py`, and `cli.py`
   **And** I find `schemas/`, `archetypes/`, and `tests/` directories

3. **Given** I run `python -m resume_as_code`
   **When** the module executes
   **Then** it behaves identically to the `resume` command

## Tasks / Subtasks

- [x] Task 1: Create project directory and pyproject.toml (AC: #2)
  - [x] 1.1: Create `resume-as-code/` directory structure (or use current directory if appropriate)
  - [x] 1.2: Create `pyproject.toml` with exact dependencies from Architecture Section 2.4
  - [x] 1.3: Include dev dependencies and build system config

- [x] Task 2: Create src/ package structure (AC: #2)
  - [x] 2.1: Create `src/resume_as_code/` directory
  - [x] 2.2: Create `__init__.py` with `__version__ = "0.1.0"`
  - [x] 2.3: Create `__main__.py` for `python -m resume_as_code` entry point
  - [x] 2.4: Create `cli.py` with Click app entry point

- [x] Task 3: Create placeholder directories (AC: #2)
  - [x] 3.1: Create `schemas/` directory with placeholder `.gitkeep`
  - [x] 3.2: Create `archetypes/` directory with placeholder `.gitkeep`
  - [x] 3.3: Create `tests/` directory with `__init__.py` and `conftest.py`

- [x] Task 4: Create CLI skeleton with Click (AC: #1, #3)
  - [x] 4.1: Implement `main()` function in `cli.py` with Click group
  - [x] 4.2: Add `--version` flag showing version from `__init__.py`
  - [x] 4.3: Add `--help` that displays available commands
  - [x] 4.4: Wire `__main__.py` to call `cli.main()`

- [x] Task 5: Install and verify (AC: #1, #3)
  - [x] 5.1: Run `uv sync --all-extras` to install in editable mode
  - [x] 5.2: Verify `resume --help` works and exits with code 0
  - [x] 5.3: Verify `python -m resume_as_code --help` works identically

- [x] Task 6: Code quality verification
  - [x] 6.1: Run `ruff check src tests --fix`
  - [x] 6.2: Run `ruff format src tests`
  - [x] 6.3: Run `mypy src --strict` with zero errors
  - [x] 6.4: Run `pytest` to verify test infrastructure works (4 tests passed)

## Dev Notes

### Architecture Compliance

This is the foundation story - all subsequent work builds on this structure. Follow the architecture document precisely.

**Source:** [Architecture Section 2.3 - Project Structure](_bmad-output/planning-artifacts/architecture.md#23-project-structure)
**Source:** [Architecture Section 2.4 - pyproject.toml Specification](_bmad-output/planning-artifacts/architecture.md#24-pyprojecttoml-specification)

### Technology Stack (Exact Versions)

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | >=3.10 | Required for union types, match statements |
| Click | >=8.1 | CLI framework |
| Pydantic | >=2.0 | V2 syntax (model_validator, not validator) |
| Hatchling | (build) | Build backend |
| Rich | >=13 | CLI output (not used in this story but include) |
| Ruff | Latest | Linting + formatting |
| mypy | Latest | Strict mode required |
| pytest | >=8.0 | Testing framework |

### pyproject.toml Reference

```toml
[project]
name = "resume-as-code"
version = "0.1.0"
description = "CLI tool for git-native resume generation from structured work units"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
  { name = "Joshua Magady" },
]
dependencies = [
  "click>=8.1",
  "pyyaml>=6.0",
  "ruamel.yaml>=0.18",
  "pydantic>=2.0",
  "jsonschema>=4.20",
  "jinja2>=3.1",
  "weasyprint>=60",
  "python-docx>=1.1",
  "docxtpl>=0.16",
  "sentence-transformers>=2.2",
  "rank-bm25>=0.2",
  "rich>=13",
]

[project.scripts]
resume = "resume_as_code.cli:main"

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-cov",
  "mypy",
  "ruff",
  "pre-commit",
]
llm = [
  "anthropic>=0.25",
  "openai>=1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.mypy]
python_version = "3.10"
strict = true
```

### Project Structure for This Story

```
resume-as-code/           # Or current directory
├── pyproject.toml
├── src/
│   └── resume_as_code/
│       ├── __init__.py   # __version__ = "0.1.0"
│       ├── __main__.py   # python -m entry point
│       └── cli.py        # Click app
├── schemas/
│   └── .gitkeep
├── archetypes/
│   └── .gitkeep
└── tests/
    ├── __init__.py
    └── conftest.py       # Shared fixtures
```

### CLI Implementation Pattern

**`src/resume_as_code/__init__.py`:**
```python
"""Resume as Code - CLI tool for git-native resume generation."""

__version__ = "0.1.0"
```

**`src/resume_as_code/__main__.py`:**
```python
"""Entry point for python -m resume_as_code."""

from resume_as_code.cli import main

if __name__ == "__main__":
    main()
```

**`src/resume_as_code/cli.py`:**
```python
"""Click CLI application for Resume as Code."""

from __future__ import annotations

import click

from resume_as_code import __version__


@click.group()
@click.version_option(version=__version__, prog_name="resume")
def main() -> None:
    """Resume as Code - CLI tool for git-native resume generation."""
    pass


if __name__ == "__main__":
    main()
```

### Project Structure Notes

- **src/ layout**: Required per Architecture - enables clean imports and packaging
- **Hatchling build backend**: Modern, simple, minimal config
- **Editable install**: Use `uv sync --all-extras` for development
- **uv required**: This project uses uv for package management

### Critical Rules from Project Context

**Source:** [project-context.md](_bmad-output/project-context.md)

- **Type hints required** on all public functions and methods
- **Use `|` union syntax** not `Union[]` (Python 3.10+)
- **Prefer `from __future__ import annotations`** for forward references
- **Never use `print()`** — use Rich console from `utils/console.py` (future story)
- **Exception handling**: Catch specific exceptions, never bare `except:`

### Testing Notes

**`tests/conftest.py`:**
```python
"""Shared pytest fixtures for Resume as Code tests."""

from __future__ import annotations

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()
```

**`tests/__init__.py`:**
```python
"""Resume as Code test suite."""
```

### Verification Commands

After implementation, run these commands to verify:

```bash
# Install dependencies
uv sync --all-extras

# Verify CLI works
uv run resume --help
echo $?  # Should be 0

# Verify module entry point
uv run python -m resume_as_code --help

# Verify version
uv run resume --version

# Code quality
uv run ruff check src tests --fix
uv run ruff format src tests
uv run mypy src --strict

# Tests
uv run pytest
```

### References

- [Source: architecture.md#Section 2.3 - Project Structure](_bmad-output/planning-artifacts/architecture.md)
- [Source: architecture.md#Section 2.4 - pyproject.toml](_bmad-output/planning-artifacts/architecture.md)
- [Source: architecture.md#Section 4.2 - Naming Patterns](_bmad-output/planning-artifacts/architecture.md)
- [Source: project-context.md - Critical Implementation Rules](_bmad-output/project-context.md)
- [Source: epics.md#Story 1.1](_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- None required

### Completion Notes List

- Created project scaffolding with pyproject.toml matching Architecture spec
- Implemented src/resume_as_code package with __init__.py, __main__.py, cli.py
- CLI uses Click with group pattern, shows help with no args (invoke_without_command=True)
- All code passes mypy --strict with zero errors
- All code passes ruff check and ruff format
- Added 4 CLI tests covering: --help, --version, no args, version value
- All tests pass (pytest 4 passed)
- Verified `resume --help` exits with code 0
- Verified `python -m resume_as_code --help` behaves identically

### File List

**Created:**
- pyproject.toml
- README.md
- src/resume_as_code/__init__.py
- src/resume_as_code/__main__.py
- src/resume_as_code/cli.py
- schemas/.gitkeep
- archetypes/.gitkeep
- tests/__init__.py
- tests/conftest.py
- tests/test_cli.py

**Generated (by uv):**
- uv.lock
- .venv/

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-10 | Initial implementation - project scaffolding and CLI skeleton | Dev Agent (Amelia) |
| 2026-01-10 | Code review fixes: .gitignore, test assertions, py.typed marker | Dev Agent (Amelia) |
