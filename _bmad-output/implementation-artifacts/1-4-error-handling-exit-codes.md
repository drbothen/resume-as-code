# Story 1.4: Error Handling & Exit Codes

Status: done

## Story

As a **developer integrating resume into scripts**,
I want **predictable exit codes and structured error messages**,
So that **I can handle failures programmatically**.

## Acceptance Criteria

1. **Given** a command succeeds
   **When** it completes
   **Then** the exit code is 0

2. **Given** a command fails due to invalid user input
   **When** it completes
   **Then** the exit code is 1 (user error, correctable)
   **And** an error message explains what was wrong

3. **Given** a command fails due to configuration error
   **When** it completes
   **Then** the exit code is 2 (configuration error)
   **And** an error message explains the config issue

4. **Given** a command fails due to validation error
   **When** it completes
   **Then** the exit code is 3 (validation error)
   **And** the error includes the file path and validation details

5. **Given** a command fails due to missing resource
   **When** it completes
   **Then** the exit code is 4 (resource not found)
   **And** the error identifies the missing file or resource

6. **Given** a command fails due to system/runtime error
   **When** it completes
   **Then** the exit code is 5 (system error)
   **And** the error describes the failure

7. **Given** I run with `--json` and an error occurs
   **When** the command fails
   **Then** the JSON output includes `status: "error"` and populated `errors` array
   **And** each error has `code`, `message`, `path`, `suggestion`, and `recoverable` fields

8. **Given** an error is recoverable
   **When** the error object is generated
   **Then** `recoverable: true` indicates the agent can retry after fixing the issue
   **And** `suggestion` provides an actionable fix recommendation

9. **Given** the CLI is run non-interactively (e.g., in CI or by AI agent)
   **When** any command executes
   **Then** no interactive prompts block execution (FR38)
   **And** all required input comes from flags or environment variables

## Tasks / Subtasks

- [x] Task 1: Create exception hierarchy (AC: #1-#6)
  - [x] 1.1: Create `src/resume_as_code/models/errors.py`
  - [x] 1.2: Implement `ResumeError` base exception with `exit_code` attribute
  - [x] 1.3: Implement `UserError` (exit code 1)
  - [x] 1.4: Implement `ConfigurationError` (exit code 2)
  - [x] 1.5: Implement `ValidationError` (exit code 3)
  - [x] 1.6: Implement `NotFoundError` (exit code 4)
  - [x] 1.7: Implement `RuntimeSystemError` (exit code 5)

- [x] Task 2: Create structured error model (AC: #7, #8)
  - [x] 2.1: Create `StructuredError` dataclass/model in `models/errors.py`
  - [x] 2.2: Add fields: `code`, `message`, `path`, `suggestion`, `recoverable`
  - [x] 2.3: Add `to_dict()` method for JSON serialization
  - [x] 2.4: Add factory methods on exceptions to create StructuredError

- [x] Task 3: Implement CLI error handling (AC: #1-#6)
  - [x] 3.1: Create error handler decorator/function in `utils/errors.py`
  - [x] 3.2: Catch exceptions at CLI level in `cli.py`
  - [x] 3.3: Format errors appropriately based on output mode (Rich/JSON/quiet)
  - [x] 3.4: Ensure correct exit codes are returned

- [x] Task 4: Integrate with JSON output (AC: #7)
  - [x] 4.1: Update `JSONResponse` model to include `errors` array
  - [x] 4.2: Populate errors array with `StructuredError` objects on failure
  - [x] 4.3: Set `status: "error"` when errors exist

- [x] Task 5: Create test command for error verification
  - [x] 5.1: Add `resume test-errors` command (temporary)
  - [x] 5.2: Trigger each error type to verify exit codes
  - [x] 5.3: Verify JSON error structure
  - [x] 5.4: Verify recoverable flag behavior

- [x] Task 6: Ensure non-interactive operation (AC: #9)
  - [x] 6.1: Audit all commands for interactive prompts
  - [x] 6.2: Replace prompts with required flags or sensible defaults
  - [x] 6.3: Document non-interactive usage in help text

- [x] Task 7: Code quality verification
  - [x] 7.1: Run `ruff check src tests --fix`
  - [x] 7.2: Run `ruff format src tests`
  - [x] 7.3: Run `mypy src --strict` with zero errors
  - [x] 7.4: Add unit tests for exception hierarchy
  - [x] 7.5: Add unit tests for structured error formatting
  - [x] 7.6: Add integration tests for exit codes

## Dev Notes

### Architecture Compliance

This story implements semantic exit codes critical for AI agent integration. The error structure with `recoverable` flag enables automated retry logic.

**Source:** [Architecture Section 3.3 - CLI Interface Design](_bmad-output/planning-artifacts/architecture.md#33-cli-interface-design)
**Source:** [Architecture Section 4.5 - Error Handling Patterns](_bmad-output/planning-artifacts/architecture.md#45-error-handling-patterns)

### Dependencies

This story REQUIRES:
- Story 1.1 (Project Scaffolding) - CLI skeleton
- Story 1.2 (Rich Console) - Output formatting, JSONResponse model

### Semantic Exit Codes (CRITICAL)

| Exit Code | Exception Class | Meaning | Example |
|-----------|-----------------|---------|---------|
| 0 | (none) | Success | Command completed |
| 1 | `UserError` | Invalid flag, missing required argument | `--invalid-flag` |
| 2 | `ConfigurationError` | Invalid config file, missing config | Malformed `.resume.yaml` |
| 3 | `ValidationError` | Schema validation failed | Work unit missing required field |
| 4 | `NotFoundError` | Work unit file not found | `resume validate missing.yaml` |
| 5 | `RuntimeSystemError` | File I/O error, network failure | Permission denied |

**Known Limitation:** Click's built-in `UsageError` also uses exit code 2 for invalid CLI arguments (wrong flags, missing required args). When exit code 2 is returned, consumers should check the error message or JSON `errors[].code` field to distinguish between Click usage errors and `ConfigurationError`.

### Exception Hierarchy

**`src/resume_as_code/models/errors.py`:**

```python
"""Exception hierarchy and structured errors for Resume as Code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class StructuredError:
    """Structured error for JSON output and AI agent consumption."""

    code: str  # "VALIDATION_ERROR", "CONFIG_ERROR", etc.
    message: str  # Human-readable description
    path: str | None = None  # File path with optional line number
    suggestion: str | None = None  # Actionable fix recommendation
    recoverable: bool = False  # Can agent retry after fixing?

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "suggestion": self.suggestion,
            "recoverable": self.recoverable,
        }


class ResumeError(Exception):
    """Base exception for all resume-as-code errors."""

    exit_code: int = 1
    error_code: str = "RESUME_ERROR"
    recoverable: bool = False

    def __init__(
        self,
        message: str,
        path: str | None = None,
        suggestion: str | None = None,
        recoverable: bool | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.path = path
        self.suggestion = suggestion
        if recoverable is not None:
            self.recoverable = recoverable

    def to_structured(self) -> StructuredError:
        """Convert to structured error for JSON output."""
        return StructuredError(
            code=self.error_code,
            message=self.message,
            path=self.path,
            suggestion=self.suggestion,
            recoverable=self.recoverable,
        )


class UserError(ResumeError):
    """Invalid user input - correctable by user."""

    exit_code = 1
    error_code = "USER_ERROR"
    recoverable = True  # User can fix and retry


class ConfigurationError(ResumeError):
    """Configuration is invalid or missing."""

    exit_code = 2
    error_code = "CONFIG_ERROR"
    recoverable = True  # User can fix config and retry


class ValidationError(ResumeError):
    """Schema or content validation failed."""

    exit_code = 3
    error_code = "VALIDATION_ERROR"
    recoverable = True  # User can fix file and retry


class NotFoundError(ResumeError):
    """Resource (file, work unit) not found."""

    exit_code = 4
    error_code = "NOT_FOUND_ERROR"
    recoverable = True  # User can create file and retry


class RuntimeSystemError(ResumeError):
    """System/runtime error (I/O, network, etc.)."""

    exit_code = 5
    error_code = "SYSTEM_ERROR"
    recoverable = False  # Usually requires investigation
```

### Error Handler Utility

**`src/resume_as_code/utils/errors.py`:**

```python
"""Error handling utilities for Resume as Code CLI."""

from __future__ import annotations

import sys
from functools import wraps
from typing import Any, Callable, TypeVar

import click

from resume_as_code.models.errors import ResumeError, StructuredError
from resume_as_code.models.output import JSONResponse
from resume_as_code.utils.console import error as print_error, err_console

F = TypeVar("F", bound=Callable[..., Any])


def handle_errors(func: F) -> F:
    """Decorator to handle ResumeError exceptions at CLI level."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        ctx = click.get_current_context(silent=True)
        try:
            return func(*args, **kwargs)
        except ResumeError as e:
            _handle_resume_error(e, ctx)
        except Exception as e:
            # Unexpected error - wrap as RuntimeSystemError
            from resume_as_code.models.errors import RuntimeSystemError
            sys_error = RuntimeSystemError(
                message=f"Unexpected error: {e}",
                suggestion="Please report this issue",
                recoverable=False,
            )
            _handle_resume_error(sys_error, ctx)

    return wrapper  # type: ignore[return-value]


def _handle_resume_error(e: ResumeError, ctx: click.Context | None) -> None:
    """Handle a ResumeError and exit with correct code."""
    structured = e.to_structured()

    # Check output mode from context
    json_output = getattr(ctx.obj, "json_output", False) if ctx and ctx.obj else False
    quiet = getattr(ctx.obj, "quiet", False) if ctx and ctx.obj else False

    if json_output:
        response = JSONResponse(
            status="error",
            command=ctx.info_name if ctx else "unknown",
            errors=[structured.to_dict()],
        )
        print(response.to_json())
    elif not quiet:
        # Rich formatted error
        print_error(e.message)
        if e.path:
            err_console.print(f"  [dim]Path:[/dim] {e.path}")
        if e.suggestion:
            err_console.print(f"  [dim]Suggestion:[/dim] {e.suggestion}")

    sys.exit(e.exit_code)
```

### CLI Integration

**Update `src/resume_as_code/cli.py`:**

```python
"""Click CLI application for Resume as Code."""

from __future__ import annotations

import click

from resume_as_code import __version__
from resume_as_code.utils.errors import handle_errors


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
@handle_errors  # Apply error handling to main group
def main(ctx: click.Context, json_output: bool, verbose: bool, quiet: bool) -> None:
    """Resume as Code - CLI tool for git-native resume generation."""
    ctx.ensure_object(Context)
    ctx.obj.json_output = json_output
    ctx.obj.verbose = verbose
    ctx.obj.quiet = quiet


# Apply @handle_errors to all subcommands as well
```

### Update JSONResponse Model

**Update `src/resume_as_code/models/output.py`:**

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
    errors: list[dict[str, Any]] = Field(default_factory=list)  # StructuredError dicts

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=2)
```

### Error JSON Structure Example

```json
{
  "format_version": "1.0.0",
  "status": "error",
  "command": "validate",
  "timestamp": "2026-01-10T14:32:00Z",
  "data": {},
  "warnings": [],
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "Missing required field 'problem.statement'",
      "path": "work-units/wu-2024-03-15-api.yaml:12",
      "suggestion": "Add a problem statement describing the challenge you solved",
      "recoverable": true
    }
  ]
}
```

### Recoverable Error Guidelines

| Error Type | Recoverable | Rationale |
|------------|-------------|-----------|
| `UserError` | true | User can fix arguments and retry |
| `ConfigurationError` | true | User can fix config file and retry |
| `ValidationError` | true | User can fix YAML file and retry |
| `NotFoundError` | true | User can create file and retry |
| `RuntimeSystemError` | false | Usually requires investigation |

### Non-Interactive Operation (FR38)

**CRITICAL:** All commands must operate without blocking prompts.

**Patterns to AVOID:**
```python
# BAD - blocks in CI/AI agent context
click.confirm("Are you sure?")
click.prompt("Enter value:")
input("Press Enter to continue...")
```

**Patterns to USE:**
```python
# GOOD - use flags with defaults
@click.option("--force", is_flag=True, help="Skip confirmation")
def dangerous_command(force: bool) -> None:
    if not force:
        raise UserError(
            message="This is a destructive operation",
            suggestion="Use --force to proceed",
            recoverable=True,
        )
```

### Project Structure After This Story

```
src/resume_as_code/
├── __init__.py
├── __main__.py
├── cli.py                    # Updated with error handling
├── config.py
├── commands/
│   ├── __init__.py
│   └── config_cmd.py
├── models/
│   ├── __init__.py
│   ├── config.py
│   ├── errors.py             # NEW: Exception hierarchy
│   └── output.py             # Updated with errors array
└── utils/
    ├── __init__.py
    ├── console.py
    └── errors.py             # NEW: Error handler utilities
```

### Testing Requirements

**`tests/unit/test_errors.py`:**

```python
"""Tests for exception hierarchy and structured errors."""

import pytest

from resume_as_code.models.errors import (
    ConfigurationError,
    NotFoundError,
    ResumeError,
    StructuredError,
    RuntimeSystemError,
    UserError,
    ValidationError,
)


class TestExitCodes:
    """Verify correct exit codes for each exception type."""

    def test_user_error_exit_code_1(self):
        assert UserError("test").exit_code == 1

    def test_configuration_error_exit_code_2(self):
        assert ConfigurationError("test").exit_code == 2

    def test_validation_error_exit_code_3(self):
        assert ValidationError("test").exit_code == 3

    def test_not_found_error_exit_code_4(self):
        assert NotFoundError("test").exit_code == 4

    def test_system_error_exit_code_5(self):
        assert RuntimeSystemError("test").exit_code == 5


class TestStructuredError:
    """Verify structured error formatting."""

    def test_to_dict_includes_all_fields(self):
        error = StructuredError(
            code="TEST_ERROR",
            message="Test message",
            path="test/path.yaml:10",
            suggestion="Fix the thing",
            recoverable=True,
        )
        d = error.to_dict()
        assert d["code"] == "TEST_ERROR"
        assert d["message"] == "Test message"
        assert d["path"] == "test/path.yaml:10"
        assert d["suggestion"] == "Fix the thing"
        assert d["recoverable"] is True


class TestRecoverableFlag:
    """Verify recoverable flag defaults."""

    def test_user_error_recoverable_by_default(self):
        assert UserError("test").recoverable is True

    def test_system_error_not_recoverable_by_default(self):
        assert RuntimeSystemError("test").recoverable is False

    def test_recoverable_can_be_overridden(self):
        error = RuntimeSystemError("test", recoverable=True)
        assert error.recoverable is True
```

**`tests/integration/test_exit_codes.py`:**

```python
"""Integration tests for CLI exit codes."""

from click.testing import CliRunner

from resume_as_code.cli import main


def test_help_returns_exit_code_0():
    """--help should exit with code 0."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0


def test_version_returns_exit_code_0():
    """--version should exit with code 0."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
```

### Verification Commands

```bash
# Test successful command (exit 0)
resume --help
echo $?  # Should be 0

# Test JSON error output
resume --json validate nonexistent.yaml
# Should output JSON with status:"error" and errors array

# Verify exit codes with test command (if implemented)
resume test-errors --type user
echo $?  # Should be 1

resume test-errors --type config
echo $?  # Should be 2

resume test-errors --type validation
echo $?  # Should be 3

resume test-errors --type notfound
echo $?  # Should be 4

resume test-errors --type system
echo $?  # Should be 5

# Code quality
ruff check src tests --fix
ruff format src tests
mypy src --strict
pytest tests/unit/test_errors.py tests/integration/test_exit_codes.py
```

### References

- [Source: architecture.md#Section 3.3 - CLI Interface Design](_bmad-output/planning-artifacts/architecture.md)
- [Source: architecture.md#Section 4.5 - Error Handling Patterns](_bmad-output/planning-artifacts/architecture.md)
- [Source: architecture.md#Section 4.4 - Format Patterns](_bmad-output/planning-artifacts/architecture.md)
- [Source: project-context.md - Critical Implementation Rules](_bmad-output/project-context.md)
- [Source: epics.md#Story 1.4](_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- Task 1: Created exception hierarchy with 6 exception classes (ResumeError, UserError, ConfigurationError, ValidationError, NotFoundError, RuntimeSystemError) and StructuredError dataclass. All 35 unit tests pass.
- Task 2: StructuredError dataclass already implemented in Task 1 with all fields (code, message, path, suggestion, recoverable), to_dict() method, and to_structured() factory method on exceptions.
- Task 3: Implemented @handle_errors decorator in utils/errors.py, applied to cli.py main group. Formats errors appropriately for Rich/JSON/quiet modes. All 18 error handling tests pass.
- Task 4: JSON integration already complete - JSONResponse model already has errors array, handle_errors populates it with StructuredError objects on failure with status: "error".
- Task 5: Created `resume test-errors` command that triggers each error type with --type flag. Supports --recoverable/--not-recoverable override. All 12 tests pass.
- Task 6: Audited all commands - no interactive prompts found. Added non-interactive documentation to CLI help. All 4 non-interactive tests pass.
- Task 7: Code quality verified - ruff check fixed 8 issues, ruff format reformatted 1 file, mypy strict passes with 0 errors. All 213 tests pass.

### Code Review Fixes (2026-01-11)

- Issue 1: Added exports for error classes to `models/__init__.py` and `handle_errors` to `utils/__init__.py`
- Issue 2: Fixed circular import by extracting `Context` class to new `context.py` module; added exports to `commands/__init__.py`
- Issue 3: Filled in agent model placeholder (Claude Opus 4.5)
- Issue 4: Documented exit code 2 conflict with Click in module docstring and story file
- Issue 5: Added documentation that recoverable errors should include suggestions
- Issue 6: Fixed --quiet/--json precedence - quiet mode now correctly takes precedence (consistent with warning message)
- Issue 7: Standardized error code naming - changed NOT_FOUND to NOT_FOUND_ERROR for consistency

### File List

- `src/resume_as_code/models/errors.py` (NEW)
- `src/resume_as_code/models/__init__.py` (MODIFIED - added error exports)
- `tests/unit/test_errors.py` (NEW)
- `src/resume_as_code/utils/errors.py` (NEW)
- `src/resume_as_code/utils/__init__.py` (MODIFIED - added handle_errors export)
- `src/resume_as_code/context.py` (NEW - extracted Context class to fix circular imports)
- `src/resume_as_code/cli.py` (MODIFIED - added @handle_errors decorator, imports Context from context.py)
- `src/resume_as_code/commands/__init__.py` (MODIFIED - added test_errors export)
- `src/resume_as_code/commands/test_output.py` (MODIFIED - imports Context from context.py)
- `tests/unit/test_error_handling.py` (NEW)
- `tests/integration/__init__.py` (NEW)
- `tests/integration/test_exit_codes.py` (NEW)
- `src/resume_as_code/commands/test_errors.py` (NEW)
- `tests/unit/test_test_errors_cmd.py` (NEW)
- `tests/integration/test_non_interactive.py` (NEW)

