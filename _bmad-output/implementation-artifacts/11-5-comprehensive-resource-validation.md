# Story 11.5: Comprehensive Resource Validation

Status: done

## Story

As a **resume-as-code user**,
I want **`resume validate` to check ALL resources, not just work units**,
So that **I can catch all errors before running build or plan commands**.

## Acceptance Criteria

1. **AC1: Default validates everything** - Given a user runs `resume validate` with no arguments, when validation completes, then ALL resources are validated: Work Units, Positions, Certifications, Education, Publications, Board Roles, Highlights, and `.resume.yaml` config.

2. **AC2: Summary output** - Given validation of all resources, when complete, then summary output shows status per resource type with counts (e.g., "Certifications: ✓ 11/11 valid").

3. **AC3: Subcommand for individual validation** - Given `resume validate positions` (subcommand), when validation runs, then only positions.yaml is validated with position-specific results.

4. **AC4: Cross-field validation** - Given cross-resource validation, when a certification has `date > expires`, then a validation error is reported with the specific field and issue identified.

5. **AC5: JSON output support** - Given the `--json` flag, when running `resume validate`, then output is structured JSON with all validation results including resource type, item count, errors, and warnings.

6. **AC6: Exit codes** - Given validation completes, when there are errors, then exit code is 3 (VALIDATION_ERROR); when only warnings exist, exit code is 0.

## Tasks / Subtasks

- [x] Task 1: Create validators package structure
  - [x] 1.1 Create `src/resume_as_code/services/validators/__init__.py`
  - [x] 1.2 Create `src/resume_as_code/services/validators/base.py` with `ResourceValidator` ABC
  - [x] 1.3 Define `ResourceValidationResult` dataclass

- [x] Task 2: Implement position validator (AC: 1, 4)
  - [x] 2.1 Create `validators/position_validator.py`
  - [x] 2.2 Validate Pydantic schema (via Position model)
  - [x] 2.3 Validate cross-field: `start_date <= end_date`
  - [x] 2.4 Validate date formats (YYYY-MM)

- [x] Task 3: Implement certification validator (AC: 1, 4)
  - [x] 3.1 Create `validators/certification_validator.py`
  - [x] 3.2 Validate Pydantic schema (via Certification model)
  - [x] 3.3 Validate cross-field: `date <= expires` (if both present)
  - [x] 3.4 Warn on expired certifications

- [x] Task 4: Implement education validator (AC: 1)
  - [x] 4.1 Create `validators/education_validator.py`
  - [x] 4.2 Validate Pydantic schema (via Education model)

- [x] Task 5: Implement publication validator (AC: 1, 4)
  - [x] 5.1 Create `validators/publication_validator.py`
  - [x] 5.2 Validate Pydantic schema (via Publication model)
  - [x] 5.3 Validate date format (YYYY-MM-DD or YYYY-MM)

- [x] Task 6: Implement board role validator (AC: 1, 4)
  - [x] 6.1 Create `validators/board_role_validator.py`
  - [x] 6.2 Validate Pydantic schema (via BoardRole model)
  - [x] 6.3 Validate cross-field: `start_date <= end_date` (if end_date present)

- [x] Task 7: Implement highlight validator (AC: 1)
  - [x] 7.1 Create `validators/highlight_validator.py`
  - [x] 7.2 Validate each highlight is non-empty string
  - [x] 7.3 Warn on highlights > 150 characters

- [x] Task 8: Implement config validator (AC: 1)
  - [x] 8.1 Create `validators/config_validator.py`
  - [x] 8.2 Validate .resume.yaml against Pydantic ResumeConfig model
  - [x] 8.3 Validate schema_version format
  - [x] 8.4 Validate referenced paths exist (work_units_dir, positions_path, etc.)

- [x] Task 9: Create validation orchestrator
  - [x] 9.1 Create `validators/orchestrator.py` to run all validators
  - [x] 9.2 Aggregate results from all validators
  - [x] 9.3 Generate combined summary with per-resource counts

- [x] Task 10: Update validate command for subcommands (AC: 2, 3, 5, 6)
  - [x] 10.1 Convert validate to Click group with subcommands
  - [x] 10.2 Add subcommands: work-units, positions, certifications, education, publications, board-roles, highlights, config
  - [x] 10.3 Make default (no subcommand) run all validators
  - [x] 10.4 Update JSON output format to include all resource types
  - [x] 10.5 Preserve backward compatibility for existing flags

- [x] Task 11: Create summary output formatting (AC: 2)
  - [x] 11.1 Create Rich table or panel for summary display
  - [x] 11.2 Show per-resource type counts
  - [x] 11.3 Show overall status with total errors/warnings

- [x] Task 12: Write tests
  - [x] 12.1 Unit tests for each validator
  - [x] 12.2 Integration tests for validate command
  - [x] 12.3 Test JSON output format
  - [x] 12.4 Test exit codes

- [x] Task 13: Update documentation
  - [x] 13.1 Update CLAUDE.md with new validate subcommands
  - [x] 13.2 Add validation examples to documentation

## Dev Notes

### Problem Statement

The `resume validate` command only validates Work Units against their JSON schema. Other resources (positions, certifications, education, publications, board-roles, highlights) are only validated by Pydantic at load time, meaning users must run other commands to discover validation errors.

**Current Behavior:**
```bash
resume validate                    # Only validates work-units/
resume validate --check-positions  # Validates work unit position_id references, not positions.yaml itself
```

Other resources fail silently until a command tries to load them:
```bash
resume list certifications         # Fails here if certifications.yaml is malformed
```

### Current Implementation Analysis

**validate.py (`src/resume_as_code/commands/validate.py`):**
- Only validates work units via `validate_path()`
- Has `--content-quality`, `--content-density`, `--check-positions` flags
- Uses `ValidationSummary` and `ValidationResult` from `services/validator.py`

**validator.py (`src/resume_as_code/services/validator.py`):**
- Loads Work Unit JSON schema from `schemas/work-unit.schema.json`
- Uses `jsonschema.Draft202012Validator` for validation
- Returns `ValidationResult` with file path, valid flag, and errors list

**data_loader.py:**
- Uses Pydantic TypeAdapter for validation when loading
- No explicit validation API - validation happens implicitly on load
- Each resource type has a dedicated loader function

### Proposed Architecture

```
src/resume_as_code/services/validators/
├── __init__.py
├── base.py                      # ResourceValidator ABC, ResourceValidationResult
├── orchestrator.py              # Runs all validators, aggregates results
├── work_unit_validator.py       # Existing logic (moved/adapted)
├── position_validator.py        # New
├── certification_validator.py   # New
├── education_validator.py       # New
├── publication_validator.py     # New
├── board_role_validator.py      # New
├── highlight_validator.py       # New
└── config_validator.py          # New
```

### Base Validator Interface

```python
# src/resume_as_code/services/validators/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from resume_as_code.models.errors import StructuredError


@dataclass
class ResourceValidationResult:
    """Result of validating a single resource type."""

    resource_type: str  # e.g., "positions", "certifications"
    source_path: Path | None  # File path if from dedicated file
    valid_count: int
    invalid_count: int
    warning_count: int = 0
    errors: list[StructuredError] = field(default_factory=list)
    warnings: list[StructuredError] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return self.valid_count + self.invalid_count

    @property
    def is_valid(self) -> bool:
        return self.invalid_count == 0


class ResourceValidator(ABC):
    """Base class for resource validators."""

    @property
    @abstractmethod
    def resource_type(self) -> str:
        """Resource type name for display (e.g., 'Positions')."""
        pass

    @abstractmethod
    def validate(self, project_path: Path) -> ResourceValidationResult:
        """Validate all resources of this type.

        Args:
            project_path: Project root directory.

        Returns:
            Validation result with counts and errors.
        """
        pass
```

### Validation Rules per Resource

| Resource | Schema | Cross-field | Cross-resource |
|----------|--------|-------------|----------------|
| Work Units | JSON schema | date logic | position_id exists |
| Positions | Pydantic | start_date <= end_date | - |
| Certifications | Pydantic | date <= expires | - |
| Education | Pydantic | - | - |
| Publications | Pydantic | valid date format | - |
| Board Roles | Pydantic | start_date <= end_date | - |
| Highlights | list[str] | non-empty, <= 150 chars | - |
| Config | Pydantic | paths exist | schema_version valid |

### CLI Structure

```bash
resume validate                      # Validate everything (NEW default)
resume validate work-units           # Just work units (current behavior)
resume validate positions            # Just positions.yaml
resume validate certifications       # Just certifications
resume validate education            # Just education
resume validate publications         # Just publications
resume validate board-roles          # Just board roles
resume validate highlights           # Just highlights
resume validate config               # Just .resume.yaml
```

**Backward Compatibility:**
- Existing flags (`--content-quality`, `--content-density`, `--check-positions`) continue to work
- Only apply to work-units validation (as currently)
- When running `resume validate` (all), these flags apply to work-units portion

### Summary Output Format

```
Validating all resources...

Work Units:     ✓ 44/44 valid
Positions:      ✓ 12/12 valid
Certifications: ✓ 11/11 valid
Education:      ✓ 1/1 valid
Publications:   ⚠ 43/45 valid (2 warnings)
Board Roles:    ✓ 1/1 valid
Highlights:     ✓ 5/5 valid
Config:         ✓ Valid

────────────────────────────────
Overall: ✓ All resources valid (2 warnings)
```

**Error Output:**
```
Work Units:     ✗ 42/44 valid (2 errors)
  work-units/wu-2024-01-invalid.yaml
    SCHEMA_ERROR: Missing required field 'title'
    💡 Add a descriptive title for this work unit
```

### JSON Output Format

```json
{
  "format_version": "1.0.0",
  "status": "error",
  "command": "validate",
  "timestamp": "2026-01-18T10:30:00Z",
  "data": {
    "summary": {
      "total_resources": 8,
      "valid_resources": 7,
      "errors": 2,
      "warnings": 3
    },
    "resources": {
      "work_units": {
        "valid_count": 42,
        "invalid_count": 2,
        "warning_count": 1,
        "errors": [
          {
            "code": "SCHEMA_VALIDATION_ERROR",
            "message": "title: 'title' is a required property",
            "path": "work-units/wu-invalid.yaml",
            "suggestion": "Add a descriptive title"
          }
        ],
        "warnings": []
      },
      "positions": {
        "valid_count": 12,
        "invalid_count": 0,
        "warning_count": 0,
        "errors": [],
        "warnings": []
      },
      "certifications": {
        "valid_count": 11,
        "invalid_count": 0,
        "warning_count": 2,
        "errors": [],
        "warnings": [
          {
            "code": "CERTIFICATION_EXPIRED",
            "message": "Certification 'CKA' expired on 2025-06",
            "path": "certifications.yaml:3",
            "severity": "warning"
          }
        ]
      }
      // ... other resources
    }
  }
}
```

### Example Validator Implementation

```python
# src/resume_as_code/services/validators/certification_validator.py
from pathlib import Path

from resume_as_code.data_loader import load_certifications
from resume_as_code.models.certification import Certification
from resume_as_code.models.errors import StructuredError
from resume_as_code.services.validators.base import (
    ResourceValidationResult,
    ResourceValidator,
)


class CertificationValidator(ResourceValidator):
    """Validator for certifications."""

    @property
    def resource_type(self) -> str:
        return "Certifications"

    def validate(self, project_path: Path) -> ResourceValidationResult:
        errors: list[StructuredError] = []
        warnings: list[StructuredError] = []
        valid_count = 0
        invalid_count = 0

        try:
            certs = load_certifications(project_path)
        except Exception as e:
            # Pydantic validation failed on load
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=project_path / "certifications.yaml",
                valid_count=0,
                invalid_count=1,
                errors=[
                    StructuredError(
                        code="LOAD_ERROR",
                        message=f"Failed to load certifications: {e}",
                        path="certifications.yaml",
                        suggestion="Check YAML syntax and field types",
                        recoverable=True,
                    )
                ],
            )

        for i, cert in enumerate(certs):
            cert_errors = self._validate_certification(cert, i)
            if cert_errors:
                invalid_count += 1
                errors.extend(cert_errors)
            else:
                valid_count += 1

            # Check for warnings (expired, etc.)
            cert_warnings = self._check_warnings(cert, i)
            warnings.extend(cert_warnings)

        return ResourceValidationResult(
            resource_type=self.resource_type,
            source_path=self._find_source_path(project_path),
            valid_count=valid_count,
            invalid_count=invalid_count,
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
        )

    def _validate_certification(
        self, cert: Certification, index: int
    ) -> list[StructuredError]:
        """Validate cross-field rules for a certification."""
        errors: list[StructuredError] = []

        # Check date <= expires (if both present)
        if cert.date and cert.expires:
            if cert.date > cert.expires:
                errors.append(
                    StructuredError(
                        code="INVALID_DATE_RANGE",
                        message=f"Certification '{cert.name}' has date ({cert.date}) after expires ({cert.expires})",
                        path=f"certifications[{index}]",
                        suggestion="Ensure date is before or equal to expires",
                        recoverable=True,
                    )
                )

        return errors

    def _check_warnings(
        self, cert: Certification, index: int
    ) -> list[StructuredError]:
        """Check for warning conditions."""
        warnings: list[StructuredError] = []

        status = cert.get_status()
        if status == "expired":
            warnings.append(
                StructuredError(
                    code="CERTIFICATION_EXPIRED",
                    message=f"Certification '{cert.name}' expired on {cert.expires}",
                    path=f"certifications[{index}]",
                    suggestion="Update expiration date or set display: false",
                    recoverable=True,
                )
            )
        elif status == "expires_soon":
            warnings.append(
                StructuredError(
                    code="CERTIFICATION_EXPIRES_SOON",
                    message=f"Certification '{cert.name}' expires within 90 days ({cert.expires})",
                    path=f"certifications[{index}]",
                    suggestion="Consider renewing this certification",
                    recoverable=True,
                )
            )

        return warnings

    def _find_source_path(self, project_path: Path) -> Path | None:
        """Find the actual source file for certifications."""
        # Check dedicated file first
        cert_path = project_path / "certifications.yaml"
        if cert_path.exists():
            return cert_path
        # Falls back to .resume.yaml (embedded)
        return project_path / ".resume.yaml"
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/resume_as_code/services/validators/__init__.py` | Create | Package init |
| `src/resume_as_code/services/validators/base.py` | Create | ABC and result dataclass |
| `src/resume_as_code/services/validators/orchestrator.py` | Create | Run all validators |
| `src/resume_as_code/services/validators/position_validator.py` | Create | Position validation |
| `src/resume_as_code/services/validators/certification_validator.py` | Create | Certification validation |
| `src/resume_as_code/services/validators/education_validator.py` | Create | Education validation |
| `src/resume_as_code/services/validators/publication_validator.py` | Create | Publication validation |
| `src/resume_as_code/services/validators/board_role_validator.py` | Create | Board role validation |
| `src/resume_as_code/services/validators/highlight_validator.py` | Create | Highlight validation |
| `src/resume_as_code/services/validators/config_validator.py` | Create | Config validation |
| `src/resume_as_code/commands/validate.py` | Modify | Add subcommands, orchestration |
| `CLAUDE.md` | Update | Document new subcommands |
| `tests/unit/services/validators/` | Create | Unit tests for validators |

### Project Context Rules to Follow

From `_bmad-output/project-context.md`:

- **Use `|` union syntax** not `Union[]` for types
- **Never use `print()`** — use Rich console from `utils/console.py`
- **Pydantic v2 syntax** — use `field_validator` and `model_validator`
- **Run ruff + mypy before completing any task**
- **Error hierarchy** — use `StructuredError` from `models/errors.py`
- **Keep commands thin, services thick** — validation logic in validators, not in command

### Exit Code Handling

```python
# Exit codes from models/errors.py
VALIDATION_ERROR = 3

# In validate command:
if any_errors:
    sys.exit(3)  # VALIDATION_ERROR
else:
    sys.exit(0)  # Success (warnings don't affect exit code)
```

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-11-technical-debt-platform-enhancements.md#Story-11.5]
- [Source: _bmad-output/implementation-artifacts/tech-debt.md#TD-008]
- Current validate command: `src/resume_as_code/commands/validate.py`
- Current validator service: `src/resume_as_code/services/validator.py`
- Data loader: `src/resume_as_code/data_loader.py`
- Models: `src/resume_as_code/models/`

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - Clean implementation

### Completion Notes List

- All 6 ACs verified and passing
- 66 tests (26 unit + 40 integration) all passing
- Lint (ruff) clean
- Type check (mypy --strict) clean
- Backward compatibility preserved for `--content-quality`, `--content-density`, `--check-positions` flags

### Change Log
- 2026-01-18: Story created with comprehensive implementation architecture
- 2026-01-19: Implementation complete (commit fa6e891)
- 2026-01-19: Code review completed, all issues remediated

### File List
- `src/resume_as_code/services/validators/__init__.py` - Package init with exports
- `src/resume_as_code/services/validators/base.py` - ResourceValidator ABC and ResourceValidationResult dataclass
- `src/resume_as_code/services/validators/orchestrator.py` - ValidationOrchestrator and AggregatedValidationResult
- `src/resume_as_code/services/validators/work_unit_validator.py` - Work unit validation wrapper
- `src/resume_as_code/services/validators/position_validator.py` - Position validation
- `src/resume_as_code/services/validators/certification_validator.py` - Certification validation with expiry warnings
- `src/resume_as_code/services/validators/education_validator.py` - Education validation
- `src/resume_as_code/services/validators/publication_validator.py` - Publication validation
- `src/resume_as_code/services/validators/board_role_validator.py` - Board role validation with date range checks
- `src/resume_as_code/services/validators/highlight_validator.py` - Highlight validation with length warnings
- `src/resume_as_code/services/validators/config_validator.py` - Config validation with path checks
- `src/resume_as_code/commands/validate.py` - Click group with 8 subcommands
- `CLAUDE.md` - Updated with validate subcommands documentation
- `tests/unit/test_resource_validators.py` - 26 unit tests for validators
- `tests/integration/test_validate_command.py` - 40 integration tests for CLI
