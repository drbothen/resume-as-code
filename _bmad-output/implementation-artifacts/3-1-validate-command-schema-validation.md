# Story 3.1: Validate Command & Schema Validation

Status: done

## Story

As a **user**,
I want **to validate my Work Units against the schema**,
So that **I catch errors before they cause problems during resume generation**.

## Acceptance Criteria

1. **Given** I run `resume validate`
   **When** the command executes
   **Then** all Work Units in `work-units/` are validated against the JSON Schema
   **And** a summary shows total files checked and pass/fail count

2. **Given** I run `resume validate path/to/specific-file.yaml`
   **When** the command executes
   **Then** only that specific file is validated

3. **Given** I run `resume validate work-units/`
   **When** the command executes
   **Then** all YAML files in that directory are validated

4. **Given** all Work Units are valid
   **When** validation completes
   **Then** exit code is 0
   **And** a success message is displayed

5. **Given** one or more Work Units are invalid
   **When** validation completes
   **Then** exit code is 3 (validation error per Story 1.4)
   **And** each invalid file is listed with its errors

6. **Given** I run `resume validate --json`
   **When** validation completes
   **Then** output is JSON with `valid_count`, `invalid_count`, and `errors` array

## Tasks / Subtasks

- [x] Task 1: Create validate command module (AC: #1, #2, #3)
  - [x] 1.1: Create `src/resume_as_code/commands/validate.py`
  - [x] 1.2: Implement `resume validate` command with Click
  - [x] 1.3: Add optional `path` argument (file or directory)
  - [x] 1.4: Default to `work-units/` directory if no path provided
  - [x] 1.5: Register command in `cli.py`

- [x] Task 2: Create validator service (AC: #1, #2, #3)
  - [x] 2.1: Create `src/resume_as_code/services/validator.py`
  - [x] 2.2: Implement `load_schema()` to load JSON Schema from `schemas/`
  - [x] 2.3: Implement `validate_file(path: Path) -> ValidationResult`
  - [x] 2.4: Implement `validate_directory(path: Path) -> list[ValidationResult]`
  - [x] 2.5: Use `jsonschema` library for validation
  - [x] 2.6: Parse YAML with `ruamel.yaml` to preserve line numbers

- [x] Task 3: Implement validation result model (AC: #4, #5, #6)
  - [x] 3.1: Create `ValidationResult` dataclass with file_path, valid, errors
  - [x] 3.2: Create `ValidationSummary` with valid_count, invalid_count, results
  - [x] 3.3: Implement JSON serialization for results

- [x] Task 4: Implement output formatting (AC: #4, #5, #6)
  - [x] 4.1: Display Rich-formatted success message when all valid
  - [x] 4.2: Display Rich-formatted error list when invalid
  - [x] 4.3: Implement `--json` output mode
  - [x] 4.4: Show summary counts (X passed, Y failed)

- [x] Task 5: Handle exit codes (AC: #4, #5)
  - [x] 5.1: Return exit code 0 when all Work Units valid
  - [x] 5.2: Return exit code 3 (ValidationError) when any invalid
  - [x] 5.3: Return exit code 2 when path doesn't exist (Click validation handles this)

- [x] Task 6: Code quality verification
  - [x] 6.1: Run `ruff check src tests --fix`
  - [x] 6.2: Run `ruff format src tests`
  - [x] 6.3: Run `mypy src --strict` with zero errors
  - [x] 6.4: Add unit tests for validator service
  - [x] 6.5: Add integration tests for validate command
  - [x] 6.6: Verify NFR3: validation completes within 1 second

## Dev Notes

### Architecture Compliance

This story implements FR6 (validate Work Units against JSON Schema). It must integrate with the error handling from Story 1.4 and use the console utilities from Story 1.2.

**Source:** [epics.md#Story 3.1](_bmad-output/planning-artifacts/epics.md)
**Source:** [Architecture Section 3.3 - CLI Interface Design](_bmad-output/planning-artifacts/architecture.md)

### Dependencies

This story REQUIRES:
- Story 1.1 (Project Scaffolding) - CLI skeleton
- Story 1.2 (Rich Console) - Output formatting
- Story 1.4 (Error Handling) - Exit codes and error structure
- Story 2.1 (Work Unit Schema) - JSON Schema to validate against

### Non-Functional Requirements

**NFR3:** `resume validate` must complete within 1 second for all Work Units.

### Command Implementation

**`src/resume_as_code/commands/validate.py`:**

```python
"""Validate command for Work Unit schema validation."""

from __future__ import annotations

from pathlib import Path

import click

from resume_as_code.config import get_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.validator import validate_path, ValidationSummary
from resume_as_code.utils.console import console, success, error, info
from resume_as_code.models.errors import ValidationError
from resume_as_code.utils.errors import handle_errors


@click.command("validate")
@click.argument(
    "path",
    type=click.Path(exists=True, path_type=Path),
    required=False,
)
@click.pass_context
@handle_errors
def validate_command(ctx: click.Context, path: Path | None) -> None:
    """Validate Work Units against the JSON Schema.

    PATH can be a single YAML file or a directory containing Work Units.
    Defaults to work-units/ directory if not specified.
    """
    config = get_config()

    # Default to work-units directory
    if path is None:
        path = config.work_units_dir
        if not path.exists():
            if ctx.obj.json_output:
                response = JSONResponse(
                    status="success",
                    command="validate",
                    data={"valid_count": 0, "invalid_count": 0, "files": []},
                )
                print(response.to_json())
            else:
                info("No work-units/ directory found. Nothing to validate.")
            return

    # Run validation
    summary = validate_path(path)

    # Output results
    if ctx.obj.json_output:
        _output_json(ctx, summary)
    else:
        _output_rich(summary)

    # Exit with appropriate code
    if summary.invalid_count > 0:
        raise ValidationError(
            message=f"{summary.invalid_count} Work Unit(s) failed validation",
            path=str(path),
        )


def _output_json(ctx: click.Context, summary: ValidationSummary) -> None:
    """Output validation results as JSON."""
    response = JSONResponse(
        status="success" if summary.invalid_count == 0 else "error",
        command="validate",
        data={
            "valid_count": summary.valid_count,
            "invalid_count": summary.invalid_count,
            "files": [
                {
                    "path": str(r.file_path),
                    "valid": r.valid,
                    "errors": [e.to_dict() for e in r.errors],
                }
                for r in summary.results
            ],
        },
    )
    print(response.to_json())


def _output_rich(summary: ValidationSummary) -> None:
    """Output validation results with Rich formatting."""
    for result in summary.results:
        if result.valid:
            success(f"✓ {result.file_path}")
        else:
            error(f"✗ {result.file_path}")
            for err in result.errors:
                console.print(f"  [red]→[/red] {err.message}")
                if err.suggestion:
                    console.print(f"    [dim]{err.suggestion}[/dim]")

    # Summary
    console.print()
    if summary.invalid_count == 0:
        success(f"All {summary.valid_count} Work Unit(s) passed validation")
    else:
        error(
            f"{summary.invalid_count} of {summary.total_count} Work Unit(s) "
            "failed validation"
        )
```

### Validator Service

**`src/resume_as_code/services/validator.py`:**

```python
"""Validator service for JSON Schema validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema
from ruamel.yaml import YAML

from resume_as_code.models.errors import StructuredError


@dataclass
class ValidationResult:
    """Result of validating a single Work Unit."""

    file_path: Path
    valid: bool
    errors: list[StructuredError] = field(default_factory=list)


@dataclass
class ValidationSummary:
    """Summary of validation across multiple files."""

    results: list[ValidationResult]

    @property
    def valid_count(self) -> int:
        return sum(1 for r in self.results if r.valid)

    @property
    def invalid_count(self) -> int:
        return sum(1 for r in self.results if not r.valid)

    @property
    def total_count(self) -> int:
        return len(self.results)


_schema: dict | None = None


def load_schema() -> dict:
    """Load the Work Unit JSON Schema."""
    global _schema
    if _schema is None:
        schema_path = Path(__file__).parent.parent / "schemas" / "work-unit.schema.json"
        with open(schema_path) as f:
            _schema = json.load(f)
    return _schema


def validate_file(path: Path) -> ValidationResult:
    """Validate a single Work Unit file.

    Args:
        path: Path to the YAML file.

    Returns:
        ValidationResult with file path, validity, and any errors.
    """
    yaml = YAML()
    yaml.preserve_quotes = True

    try:
        with open(path) as f:
            data = yaml.load(f)
    except Exception as e:
        return ValidationResult(
            file_path=path,
            valid=False,
            errors=[
                StructuredError(
                    code="YAML_PARSE_ERROR",
                    message=f"Failed to parse YAML: {e}",
                    path=str(path),
                    suggestion="Check YAML syntax - ensure proper indentation and formatting",
                    recoverable=True,
                )
            ],
        )

    schema = load_schema()
    # Use Draft202012Validator since schema uses draft/2020-12/schema
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(data))

    if not errors:
        return ValidationResult(file_path=path, valid=True)

    structured_errors = [
        _convert_schema_error(err, path) for err in errors
    ]

    return ValidationResult(
        file_path=path,
        valid=False,
        errors=structured_errors,
    )


def validate_directory(path: Path) -> list[ValidationResult]:
    """Validate all YAML files in a directory.

    Args:
        path: Path to directory containing Work Units.

    Returns:
        List of ValidationResults for each file.
    """
    results = []
    for yaml_file in sorted(path.glob("*.yaml")):
        results.append(validate_file(yaml_file))
    return results


def validate_path(path: Path) -> ValidationSummary:
    """Validate a file or directory.

    Args:
        path: Path to file or directory.

    Returns:
        ValidationSummary with all results.
    """
    if path.is_file():
        results = [validate_file(path)]
    else:
        results = validate_directory(path)

    return ValidationSummary(results=results)


def _convert_schema_error(
    error: jsonschema.ValidationError,
    file_path: Path,
) -> StructuredError:
    """Convert jsonschema error to StructuredError."""
    path_str = ".".join(str(p) for p in error.absolute_path) or "(root)"

    # Generate helpful suggestions based on error type
    suggestion = _generate_suggestion(error)

    return StructuredError(
        code="SCHEMA_VALIDATION_ERROR",
        message=f"{path_str}: {error.message}",
        path=str(file_path),
        suggestion=suggestion,
        recoverable=True,
    )


def _generate_suggestion(error: jsonschema.ValidationError) -> str:
    """Generate a helpful suggestion for the error."""
    if error.validator == "required":
        missing = error.message.split("'")[1]
        return f"Add the required field '{missing}' to your Work Unit"

    if error.validator == "enum":
        valid_values = ", ".join(str(v) for v in error.validator_value)
        return f"Use one of the valid values: {valid_values}"

    if error.validator == "type":
        expected = error.validator_value
        return f"Expected type '{expected}'"

    return "Check the field value against the schema requirements"
```

### CLI Registration

**Update `src/resume_as_code/cli.py`:**

```python
# Add import
from resume_as_code.commands.validate import validate_command

# Register command after main
main.add_command(validate_command)
```

### Testing Requirements

**`tests/unit/test_validator.py`:**

```python
"""Tests for validator service."""

from pathlib import Path

import pytest

from resume_as_code.services.validator import (
    validate_file,
    validate_directory,
    ValidationResult,
)


@pytest.fixture
def valid_work_unit(tmp_path: Path) -> Path:
    """Create a valid Work Unit file."""
    content = '''
schema_version: "1.0.0"
id: "wu-2026-01-10-test"
title: "Test Work Unit"

problem:
  statement: "A test problem"

actions:
  - "Took action"

outcome:
  result: "Got result"
'''
    file_path = tmp_path / "wu-test.yaml"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def invalid_work_unit(tmp_path: Path) -> Path:
    """Create an invalid Work Unit file."""
    content = '''
schema_version: "1.0.0"
id: "wu-2026-01-10-test"
# Missing required: title, problem, actions, outcome
'''
    file_path = tmp_path / "wu-invalid.yaml"
    file_path.write_text(content)
    return file_path


class TestValidateFile:
    """Tests for validate_file function."""

    def test_valid_file(self, valid_work_unit: Path):
        """Should return valid=True for valid Work Unit."""
        result = validate_file(valid_work_unit)
        assert result.valid is True
        assert result.errors == []

    def test_invalid_file(self, invalid_work_unit: Path):
        """Should return valid=False with errors for invalid Work Unit."""
        result = validate_file(invalid_work_unit)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_malformed_yaml(self, tmp_path: Path):
        """Should handle malformed YAML gracefully."""
        file_path = tmp_path / "malformed.yaml"
        file_path.write_text("invalid: yaml: content:")

        result = validate_file(file_path)
        assert result.valid is False
        assert "YAML_PARSE_ERROR" in result.errors[0].code


class TestValidateDirectory:
    """Tests for validate_directory function."""

    def test_validates_all_yaml_files(
        self, valid_work_unit: Path, invalid_work_unit: Path
    ):
        """Should validate all YAML files in directory."""
        results = validate_directory(valid_work_unit.parent)
        assert len(results) == 2

    def test_empty_directory(self, tmp_path: Path):
        """Should return empty list for directory with no YAML files."""
        results = validate_directory(tmp_path)
        assert results == []
```

**`tests/integration/test_validate_command.py`:**

```python
"""Integration tests for validate command."""

from pathlib import Path

from click.testing import CliRunner

from resume_as_code.cli import main


def test_validate_all_pass(tmp_path: Path, monkeypatch):
    """Should exit 0 when all Work Units valid."""
    monkeypatch.chdir(tmp_path)

    # Create work-units directory with valid file
    work_units = tmp_path / "work-units"
    work_units.mkdir()
    (work_units / "wu-test.yaml").write_text('''
schema_version: "1.0.0"
id: "wu-2026-01-10-test"
title: "Test"
problem:
  statement: "Test problem"
actions:
  - "Action"
outcome:
  result: "Result"
''')

    runner = CliRunner()
    result = runner.invoke(main, ["validate"])

    assert result.exit_code == 0
    assert "passed validation" in result.output


def test_validate_with_errors(tmp_path: Path, monkeypatch):
    """Should exit 3 when Work Units have errors."""
    monkeypatch.chdir(tmp_path)

    work_units = tmp_path / "work-units"
    work_units.mkdir()
    (work_units / "wu-invalid.yaml").write_text('''
schema_version: "1.0.0"
id: "wu-2026-01-10-test"
# Missing required fields
''')

    runner = CliRunner()
    result = runner.invoke(main, ["validate"])

    assert result.exit_code == 3


def test_validate_json_output(tmp_path: Path, monkeypatch):
    """Should output valid JSON with --json flag."""
    monkeypatch.chdir(tmp_path)

    work_units = tmp_path / "work-units"
    work_units.mkdir()

    runner = CliRunner()
    result = runner.invoke(main, ["--json", "validate"])

    assert result.exit_code == 0
    assert '"valid_count"' in result.output
    assert '"invalid_count"' in result.output
```

### Verification Commands

```bash
# Create test Work Units
mkdir -p work-units
cat > work-units/wu-valid.yaml << 'EOF'
schema_version: "1.0.0"
id: "wu-2026-01-10-valid"
title: "Valid Work Unit"
problem:
  statement: "A test problem"
actions:
  - "Took action"
outcome:
  result: "Got result"
EOF

# Validate all
resume validate

# Validate specific file
resume validate work-units/wu-valid.yaml

# Validate with JSON output
resume --json validate

# Test error handling
cat > work-units/wu-invalid.yaml << 'EOF'
schema_version: "1.0.0"
id: "wu-2026-01-10-invalid"
# Missing required fields
EOF

resume validate  # Should show errors and exit with code 3

# Code quality
ruff check src tests --fix
mypy src --strict
pytest tests/unit/test_validator.py tests/integration/test_validate_command.py -v

# Cleanup
rm work-units/wu-invalid.yaml
```

### References

- [Source: epics.md#Story 3.1](_bmad-output/planning-artifacts/epics.md)
- [Source: architecture.md](_bmad-output/planning-artifacts/architecture.md)
- [Source: project-context.md](_bmad-output/project-context.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - Implementation completed without debugging issues.

### Completion Notes List

- Implemented `resume validate` command following red-green-refactor TDD cycle
- Created validator service with `ValidationResult` and `ValidationSummary` dataclasses
- Used `jsonschema.Draft202012Validator` (matches schema's draft/2020-12/schema)
- Added type ignore for jsonschema import (no types-jsonschema stubs available)
- Both JSON and Rich modes exit directly via `sys.exit()` to avoid duplicate output
- All 6 acceptance criteria verified through 30 dedicated tests (19 unit + 11 integration)
- NFR3 verified: validation completes in ~0.19s (well under 1s requirement)
- Full test suite passes with zero failures
- Code quality verified: ruff and mypy --strict pass with zero errors

### File List

**Created:**
- src/resume_as_code/commands/validate.py
- src/resume_as_code/services/validator.py
- tests/unit/test_validator.py
- tests/integration/test_validate_command.py

**Modified:**
- src/resume_as_code/cli.py (added validate_command registration)

## Senior Developer Review (AI)

**Reviewer:** Claude Opus 4.5 (claude-opus-4-5-20251101)
**Date:** 2026-01-11
**Outcome:** APPROVED with fixes applied

### Issues Found and Remediated

| Severity | Issue | Resolution |
|----------|-------|------------|
| HIGH | Duplicate error output in Rich mode - error displayed twice | Fixed: Both modes now use `sys.exit()` instead of raising exception after output |
| MEDIUM | Test name `test_validate_nonexistent_path_exit_code_4` was misleading | Fixed: Renamed to `test_validate_nonexistent_path_click_error` |
| MEDIUM | No unit tests for `_generate_suggestion()` branches | Fixed: Added 7 new tests covering all suggestion types |
| MEDIUM | Story Dev Notes showed `Draft7Validator` but code uses `Draft202012Validator` | Fixed: Updated Dev Notes to match implementation |
| LOW | Task 5.3 claimed exit code 4 but Click returns 2 | Fixed: Updated task description to reflect actual behavior |

### Verification

- All 30 tests pass (up from 23 after adding `_generate_suggestion` tests)
- Ruff: All checks passed
- Mypy --strict: No issues found
- Manual verification of duplicate output fix confirmed

### Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-01-10 | Dev Agent (Opus 4.5) | Initial implementation |
| 2026-01-11 | Review Agent (Opus 4.5) | Code review fixes: duplicate output, test naming, suggestion coverage, doc accuracy |

