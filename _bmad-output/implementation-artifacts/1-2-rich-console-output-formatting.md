# Story 1.2: Rich Console & Output Formatting

Status: done

## Story

As a **developer**,
I want **consistent, formatted CLI output with JSON option for scripting**,
So that **I can read output easily and pipe to other tools when needed**.

## Acceptance Criteria

1. **Given** I run any resume command
   **When** the command produces output
   **Then** the output uses Rich formatting with colors and symbols
   **And** success messages show green checkmarks
   **And** warnings show yellow warning symbols
   **And** errors show red X symbols

2. **Given** I run `resume --json <command>`
   **When** the command completes
   **Then** output is valid JSON with `format_version`, `status`, `command`, `timestamp`, `data`, `errors`, `warnings` fields
   **And** no Rich formatting is included in the output
   **And** only JSON appears on stdout (no other content)

3. **Given** I run `resume --verbose <command>`
   **When** the command executes
   **Then** additional debug information is displayed
   **And** file paths being accessed are shown

4. **Given** I run a command without `--verbose`
   **When** the command executes
   **Then** only essential output is shown (no debug clutter)

5. **Given** I run `resume --quiet <command>`
   **When** the command completes
   **Then** no output is produced
   **And** only the exit code indicates success/failure

6. **Given** any command produces progress or status messages
   **When** output is generated
   **Then** progress/status goes to stderr (not stdout)
   **And** only results/data go to stdout
   **And** `--json` mode produces clean JSON on stdout with no stderr noise

## Tasks / Subtasks

- [x] Task 1: Create console utility module (AC: #1, #6)
  - [x] 1.1: Create `src/resume_as_code/utils/__init__.py`
  - [x] 1.2: Create `src/resume_as_code/utils/console.py` with Rich Console singletons
  - [x] 1.3: Implement `console` (stdout) for results
  - [x] 1.4: Implement `err_console` (stderr) for progress/status/errors
  - [x] 1.5: Create helper functions: `success()`, `warning()`, `error()`, `info()`

- [x] Task 2: Create JSON output models (AC: #2)
  - [x] 2.1: Create `src/resume_as_code/models/output.py` with Pydantic models
  - [x] 2.2: Implement `JSONResponse` model with required fields
  - [x] 2.3: Implement `format_version: "1.0.0"` constant
  - [x] 2.4: Create `to_json()` helper for consistent JSON serialization

- [x] Task 3: Add global CLI flags (AC: #2, #3, #4, #5)
  - [x] 3.1: Add `--json` flag to main CLI group in `cli.py`
  - [x] 3.2: Add `--verbose` / `-v` flag to main CLI group
  - [x] 3.3: Add `--quiet` / `-q` flag to main CLI group
  - [x] 3.4: Store flags in Click context for subcommand access
  - [x] 3.5: Ensure mutual exclusivity: `--json` and `--quiet` suppress Rich output

- [x] Task 4: Implement output mode switching (AC: #1, #2, #5)
  - [x] 4.1: Create `OutputMode` enum: `rich`, `json`, `quiet`
  - [x] 4.2: Create `get_output_mode()` function to read from Click context
  - [x] 4.3: Update console helpers to respect output mode
  - [x] 4.4: Suppress Rich output when `--json` or `--quiet` is active

- [x] Task 5: Create test command for verification (AC: #1-#6)
  - [x] 5.1: Add temporary `resume test-output` command
  - [x] 5.2: Demonstrate success, warning, error, and info messages
  - [x] 5.3: Verify JSON output structure
  - [x] 5.4: Verify stdout/stderr separation
  - [x] 5.5: Remove test command after verification (or keep for dev)

- [x] Task 6: Code quality verification
  - [x] 6.1: Run `ruff check src tests --fix`
  - [x] 6.2: Run `ruff format src tests`
  - [x] 6.3: Run `mypy src --strict` with zero errors
  - [x] 6.4: Add unit tests for console utilities
  - [x] 6.5: Add unit tests for JSON output models

## Dev Notes

### Architecture Compliance

This story implements the output formatting infrastructure that ALL subsequent commands will use. Follow the architecture document precisely for stdout/stderr separation and JSON structure.

**Source:** [Architecture Section 3.3 - CLI Interface Design](_bmad-output/planning-artifacts/architecture.md#33-cli-interface-design)
**Source:** [Architecture Section 4.4 - Format Patterns](_bmad-output/planning-artifacts/architecture.md#44-format-patterns)

### Dependency on Story 1.1

This story REQUIRES Story 1.1 (Project Scaffolding) to be complete. The following must exist:
- `src/resume_as_code/cli.py` with Click app
- `src/resume_as_code/__init__.py` with `__version__`
- Working `resume` command entry point

### Console Singleton Pattern

**`src/resume_as_code/utils/console.py`:**

```python
"""Rich console utilities for Resume as Code CLI output."""

from __future__ import annotations

from rich.console import Console

# Singleton console instances
console = Console()  # stdout - for results only
err_console = Console(stderr=True)  # stderr - for progress/status/errors


def success(message: str) -> None:
    """Display a success message with green checkmark."""
    console.print(f"[green]✓[/green] {message}")


def warning(message: str) -> None:
    """Display a warning message with yellow symbol."""
    err_console.print(f"[yellow]⚠[/yellow] {message}")


def error(message: str) -> None:
    """Display an error message with red X."""
    err_console.print(f"[red]✗[/red] {message}")


def info(message: str) -> None:
    """Display an informational message."""
    console.print(f"[blue]ℹ[/blue] {message}")


def verbose(message: str) -> None:
    """Display verbose debug information (only when --verbose)."""
    err_console.print(f"[dim]{message}[/dim]")
```

### JSON Response Model

**`src/resume_as_code/models/output.py`:**

```python
"""Output models for JSON response formatting."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

FORMAT_VERSION = "1.0.0"


class JSONResponse(BaseModel):
    """Standard JSON response format for all commands."""

    format_version: str = Field(default=FORMAT_VERSION)
    status: str  # "success" | "error" | "dry_run"
    command: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=2)
```

### CLI Flag Implementation

**Update `src/resume_as_code/cli.py`:**

```python
"""Click CLI application for Resume as Code."""

from __future__ import annotations

import click

from resume_as_code import __version__


class Context:
    """Click context object for storing global options."""

    def __init__(self) -> None:
        self.json_output: bool = False
        self.verbose: bool = False
        self.quiet: bool = False


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group()
@click.version_option(version=__version__, prog_name="resume")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.option("-v", "--verbose", is_flag=True, help="Show verbose debug output")
@click.option("-q", "--quiet", is_flag=True, help="Suppress all output, exit code only")
@click.pass_context
def main(ctx: click.Context, json_output: bool, verbose: bool, quiet: bool) -> None:
    """Resume as Code - CLI tool for git-native resume generation."""
    ctx.ensure_object(Context)
    ctx.obj.json_output = json_output
    ctx.obj.verbose = verbose
    ctx.obj.quiet = quiet


if __name__ == "__main__":
    main()
```

### Stdout/Stderr Separation (CRITICAL)

**Architecture Requirement:** AI agents parse stdout only. All non-result output MUST go to stderr.

| Stream | Content | When |
|--------|---------|------|
| stdout | Command results, data, JSON response | Always |
| stderr | Progress, warnings, debug info, errors | Always |

**Implementation:**
```python
# CORRECT - results to stdout
console.print(result_table)

# CORRECT - progress to stderr
err_console.print("[dim]Processing 15 work units...[/dim]")

# CORRECT - JSON mode only outputs JSON to stdout
if ctx.obj.json_output:
    print(response.to_json())  # stdout only
```

### Output Mode Logic

```python
from enum import Enum


class OutputMode(Enum):
    RICH = "rich"
    JSON = "json"
    QUIET = "quiet"


def get_output_mode(ctx: Context) -> OutputMode:
    """Determine current output mode from context flags."""
    if ctx.quiet:
        return OutputMode.QUIET
    if ctx.json_output:
        return OutputMode.JSON
    return OutputMode.RICH
```

### Project Structure After This Story

```
src/resume_as_code/
├── __init__.py
├── __main__.py
├── cli.py              # Updated with global flags
├── models/
│   ├── __init__.py
│   └── output.py       # NEW: JSONResponse model
└── utils/
    ├── __init__.py     # NEW
    └── console.py      # NEW: Rich console utilities
```

### Critical Rules from Project Context

**Source:** [project-context.md](_bmad-output/project-context.md)

- **Never use `print()`** for user-facing output — use Rich console
- **Exception:** `print()` is OK for `--json` mode raw JSON output
- **Type hints required** on all public functions
- **Use `|` union syntax** not `Union[]`
- **Prefer `from __future__ import annotations`**

### Testing Requirements

**`tests/unit/test_console.py`:**
```python
"""Tests for console utilities."""

from resume_as_code.utils.console import success, warning, error, info


def test_success_formats_with_checkmark(capsys):
    """Success messages should have green checkmark."""
    # Note: Rich output testing requires special handling
    pass


def test_error_goes_to_stderr(capsys):
    """Error messages should go to stderr."""
    error("test error")
    captured = capsys.readouterr()
    assert "test error" in captured.err
```

**`tests/unit/test_output_models.py`:**
```python
"""Tests for JSON output models."""

import json

from resume_as_code.models.output import JSONResponse, FORMAT_VERSION


def test_json_response_has_format_version():
    """Response should include format version."""
    response = JSONResponse(status="success", command="test")
    data = json.loads(response.to_json())
    assert data["format_version"] == FORMAT_VERSION


def test_json_response_has_timestamp():
    """Response should include ISO timestamp."""
    response = JSONResponse(status="success", command="test")
    data = json.loads(response.to_json())
    assert "timestamp" in data
```

### Verification Commands

```bash
# Test Rich output (default)
resume test-output
# Should show: ✓ Success message (green)
#              ⚠ Warning message (yellow)
#              ✗ Error message (red)

# Test JSON output
resume --json test-output
# Should output valid JSON with format_version, status, etc.

# Test verbose mode
resume --verbose test-output
# Should show additional debug info

# Test quiet mode
resume --quiet test-output
echo $?  # Should show exit code only, no output

# Verify stdout/stderr separation
resume test-output 2>/dev/null  # Only results shown
resume test-output 1>/dev/null  # Only progress/errors shown

# Code quality
ruff check src tests --fix
ruff format src tests
mypy src --strict
pytest tests/unit/test_console.py tests/unit/test_output_models.py
```

### References

- [Source: architecture.md#Section 3.3 - CLI Interface Design](_bmad-output/planning-artifacts/architecture.md)
- [Source: architecture.md#Section 4.4 - Format Patterns](_bmad-output/planning-artifacts/architecture.md)
- [Source: architecture.md#Section 4.6 - Logging Patterns](_bmad-output/planning-artifacts/architecture.md)
- [Source: project-context.md - Critical Implementation Rules](_bmad-output/project-context.md)
- [Source: epics.md#Story 1.2](_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- Implemented Rich console utilities with stdout/stderr separation (AC #1, #6)
- Created JSONResponse Pydantic model with format_version 1.0.0 (AC #2)
- Added global CLI flags: --json, --verbose/-v, --quiet/-q (AC #2, #3, #4, #5)
- Implemented OutputMode enum and get_output_mode() for mode switching
- Created test-output command demonstrating all output modes
- All 69 tests pass, ruff check passes, mypy --strict passes with zero errors
- Added pytest configuration to pyproject.toml for proper test discovery

**Code Review Fixes (2026-01-11):**
- Added verbose_path() helper for file path logging (fixes AC #3 violation)
- Console helpers now respect output mode (suppress output in JSON/quiet modes)
- Added configure_output() for centralized mode configuration
- Added reset_output_mode() and set_verbose_enabled() for testing
- Added flag conflict warning when --json and --quiet are both used
- Added proper exports to commands/__init__.py
- Improved test assertion for error symbol verification
- Added comprehensive tests for output mode suppression behavior

### File List

**New Files:**
- src/resume_as_code/utils/__init__.py
- src/resume_as_code/utils/console.py
- src/resume_as_code/models/__init__.py
- src/resume_as_code/models/output.py
- src/resume_as_code/commands/__init__.py
- src/resume_as_code/commands/test_output.py
- tests/unit/__init__.py
- tests/unit/test_console.py
- tests/unit/test_output_models.py
- tests/unit/test_output_mode.py

**Modified Files:**
- src/resume_as_code/cli.py (added Context class, global flags, command registration, configure_output call, flag conflict warning)
- tests/test_cli.py (added global flags, test-output command tests, verbose mode tests, conflict warning test)
- pyproject.toml (added pytest configuration)

## Change Log

- 2026-01-10: Implemented Story 1.2 - Rich Console & Output Formatting
- 2026-01-11: Code review fixes - AC #3 compliance, output mode suppression, flag conflict warning

