# Story 7.3: Standardized Date Types

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **consistent date handling with reusable annotated types**,
So that **date validation is centralized and dates display consistently**.

## Acceptance Criteria

1. **Given** a YearMonth field (e.g., "2024-01")
   **When** I set it with various formats
   **Then** it normalizes to YYYY-MM string
   **And** invalid formats raise ValidationError

2. **Given** a Year field (e.g., "2024" or 2024)
   **When** I set it with string or integer
   **Then** it normalizes to 4-digit string
   **And** invalid formats raise ValidationError

3. **Given** Position.start_date and Position.end_date
   **When** I inspect their types
   **Then** they use `YearMonth` annotated type
   **And** validation is automatic (no custom validators needed)

4. **Given** Education.graduation_year
   **When** I inspect its type
   **Then** it uses `Year` annotated type

5. **Given** all models using the new types
   **When** I run existing tests
   **Then** all tests pass without modification
   **And** validation behavior is identical to before

## Tasks / Subtasks

- [x] Task 1: Create reusable date types module (AC: #1, #2)
  - [x] 1.1 Create `src/resume_as_code/models/types.py` with YearMonth type
  - [x] 1.2 Add Year type with int-to-str coercion
  - [x] 1.3 Add proper docstrings and Field descriptions
  - [x] 1.4 Export from `models/__init__.py`
  - [x] 1.5 Add comprehensive unit tests for both types

- [x] Task 2: Update Position model (AC: #3)
  - [x] 2.1 Replace `start_date: str` with `start_date: YearMonth`
  - [x] 2.2 Replace `end_date: str | None` with `end_date: YearMonth | None`
  - [x] 2.3 Remove the `validate_date_format` field_validator
  - [x] 2.4 Verify existing tests pass

- [x] Task 3: Update Education model (AC: #4)
  - [x] 3.1 Rename `year` field to `graduation_year` (optional - confirm with user) - COMPLETED: renamed field to match AC #4
  - [x] 3.2 Replace type annotation with `Year | None`
  - [x] 3.3 Remove the `validate_year_format` field_validator
  - [x] 3.4 Verify existing tests pass

- [x] Task 4: Update Certification model (AC: #1)
  - [x] 4.1 Replace `date: str | None` with `date: YearMonth | None`
  - [x] 4.2 Replace `expires: str | None` with `expires: YearMonth | None`
  - [x] 4.3 Remove the `validate_date_format` field_validator
  - [x] 4.4 Verify existing tests pass

- [x] Task 5: Update BoardRole model (AC: #1)
  - [x] 5.1 Replace `start_date: str` with `start_date: YearMonth`
  - [x] 5.2 Replace `end_date: str | None` with `end_date: YearMonth | None`
  - [x] 5.3 Remove the `validate_date_format` field_validator
  - [x] 5.4 Verify existing tests pass

- [x] Task 6: Update Publication model (AC: #1)
  - [x] 6.1 Replace `date: str` with `date: YearMonth`
  - [x] 6.2 Remove the `validate_date_format` field_validator
  - [x] 6.3 Verify existing tests pass

- [x] Task 7: Final verification and documentation
  - [x] 7.1 Run `ruff check` and `mypy --strict`
  - [x] 7.2 Run full test suite
  - [x] 7.3 Update schema generation if needed - JSON schemas auto-generated via WithJsonSchema
  - [x] 7.4 Add usage examples to docstrings

## Dev Notes

### Technical Debt Being Addressed

**Current State: FIVE duplicate date validators**

| Model | Date Fields | Validator | Format |
|-------|-------------|-----------|--------|
| `position.py:65-73` | start_date, end_date | `validate_date_format` | YYYY-MM |
| `education.py:45-66` | year | `validate_year_format` | YYYY |
| `certification.py:27-47` | date, expires | `validate_date_format` | YYYY-MM |
| `board_role.py:28-46` | start_date, end_date | `validate_date_format` | YYYY-MM |
| `publication.py:27-43` | date | `validate_date_format` | YYYY-MM |

**Additional Inconsistency: WorkUnit uses Python `date` objects**
- `work_unit.py:222-223`: `time_started: date | None`, `time_ended: date | None`
- This is intentional (finer granularity) but should be documented

### Implementation Pattern

**Using Pydantic v2 `Annotated` with `BeforeValidator` + `Field` for JSON schema:**

```python
# src/resume_as_code/models/types.py
"""Reusable annotated types for consistent validation across models."""

from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import BeforeValidator, Field


def _normalize_year_month(v: Any) -> str | None:
    """Normalize input to YYYY-MM format.

    Accepts:
    - "2024-01" → "2024-01"
    - "2024-01-15" → "2024-01" (truncates day)
    - None → None (for optional fields)

    Args:
        v: Input value (string expected, or None).

    Returns:
        Normalized YYYY-MM string, or None.

    Raises:
        ValueError: If format is invalid (non-None, non-matching).
    """
    # CRITICAL: BeforeValidator runs on ALL values including None
    # Return None to let Pydantic's type system enforce required vs optional
    if v is None:
        return None
    v_str = str(v).strip()
    # Accept YYYY-MM or YYYY-MM-DD, normalize to YYYY-MM
    if re.match(r"^\d{4}-\d{2}(-\d{2})?$", v_str):
        return v_str[:7]
    raise ValueError(f"Date must be in YYYY-MM format, got: {v_str!r}")


def _normalize_year(v: Any) -> str | None:
    """Normalize input to YYYY format.

    Accepts:
    - 2024 (int) → "2024"
    - "2024" → "2024"
    - "2024-01" → "2024" (truncates month)
    - None → None (for optional fields)

    Args:
        v: Input value (string or int, or None).

    Returns:
        Normalized YYYY string, or None.

    Raises:
        ValueError: If format is invalid (non-None, non-matching).
    """
    # CRITICAL: BeforeValidator runs on ALL values including None
    if v is None:
        return None
    v_str = str(v).strip()
    if re.match(r"^\d{4}", v_str):
        return v_str[:4]
    raise ValueError(f"Year must be in YYYY format, got: {v_str!r}")


# Type aliases for use in model definitions
# NOTE: Field with pattern adds JSON schema constraint
YearMonth = Annotated[
    str,
    BeforeValidator(_normalize_year_month),
    Field(pattern=r"^\d{4}-\d{2}$", description="Date in YYYY-MM format"),
]
"""Date type for YYYY-MM format strings.

Used for:
- Position.start_date, Position.end_date
- Certification.date, Certification.expires
- BoardRole.start_date, BoardRole.end_date
- Publication.date
"""

Year = Annotated[
    str,
    BeforeValidator(_normalize_year),
    Field(pattern=r"^\d{4}$", description="Year in YYYY format"),
]
"""Year type for YYYY format strings.

Accepts both int and str input, normalizes to 4-digit string.

Used for:
- Education.graduation_year
"""
```

### Model Updates

**Position (example):**
```python
# Before:
class Position(BaseModel):
    start_date: str = Field(description="Start date in YYYY-MM format")
    end_date: str | None = Field(default=None, description="End date in YYYY-MM format")

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not re.match(r"^\d{4}-\d{2}$", str(v)):
            raise ValueError("Date must be in YYYY-MM format")
        return v

# After:
from resume_as_code.models.types import YearMonth

class Position(BaseModel):
    start_date: YearMonth = Field(description="Start date in YYYY-MM format")
    end_date: YearMonth | None = Field(default=None, description="End date in YYYY-MM format")
    # No validator needed - YearMonth handles validation automatically
```

**Education:**
```python
# Before:
class Education(BaseModel):
    year: str | None = None

    @field_validator("year", mode="before")
    @classmethod
    def validate_year_format(cls, v: str | None) -> str | None:
        if v is None:
            return None
        # ... validation logic
        return v_str[:4]

# After:
from resume_as_code.models.types import Year

class Education(BaseModel):
    graduation_year: Year | None = None  # Renamed from 'year' per AC #4
    # No validator needed - Year handles validation automatically
```

### Research Findings (2026-01-15)

**BeforeValidator and None Handling (CRITICAL):**

In Pydantic v2, `BeforeValidator` **runs on ALL values including None**, even for Optional fields.
This is different from `@field_validator(mode='after')` which skips None values.

**Implications:**
1. Validators MUST handle None explicitly by returning None (not raising)
2. Pydantic's type system then enforces required vs optional:
   - `start_date: YearMonth` → validator returns None → type validation fails ("should be string")
   - `end_date: YearMonth | None` → validator returns None → type validation passes

**JSON Schema Pattern Generation:**

To add `pattern` constraints to JSON schema from Annotated types:
- Use `Field(pattern=r"...")` inside the Annotated type definition
- The pattern is included in generated JSON schema automatically
- Order matters: `BeforeValidator` should come before `Field` in Annotated list

**Known Issue (GitHub #12417):**
Combining `BeforeValidator` with pattern constraints can sometimes produce incorrect schema output.
Verify generated schema with `model_json_schema()` during testing.

**Sources:**
- Pydantic v2 validators docs: https://docs.pydantic.dev/latest/concepts/validators/
- Pydantic v2 JSON schema docs: https://docs.pydantic.dev/latest/concepts/json_schema/
- GitHub issue #12417: https://github.com/pydantic/pydantic/issues/12417

### Edge Cases to Handle

1. **Optional fields with None**: `YearMonth | None` should accept None
   ```python
   # CRITICAL: BeforeValidator DOES run on None values
   # Validator must return None to allow it through
   # Pydantic type system then enforces required vs optional
   def _normalize_year_month(v: Any) -> str | None:
       if v is None:
           return None  # Pass through for optional fields
       # ... validation logic
   ```

2. **Required fields with None**: `start_date: YearMonth` should reject None
   ```python
   # Validator returns None → Pydantic type validation fails
   # Error: "Input should be a valid string, not NoneType"
   # This is the desired behavior for required fields
   ```

3. **Int year input**: Year type should coerce `2024` (int) to `"2024"` (str)
   ```python
   def _normalize_year(v: Any) -> str | None:
       if v is None:
           return None
       v_str = str(v).strip()  # Handles int → str conversion
   ```

4. **Extended formats**: Certification accepts YYYY-MM-DD, normalizes to YYYY-MM
   ```python
   # Already supported by current certification validator
   # Will be handled by _normalize_year_month
   ```

### JSON Schema Output

The annotated types will generate JSON schemas with:
- `type: "string"`
- `pattern: "^\\d{4}-\\d{2}$"` (for YearMonth)
- `pattern: "^\\d{4}$"` (for Year)

```json
{
  "properties": {
    "start_date": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}$",
      "title": "Start Date"
    }
  }
}
```

### Project Context Rules

From `project-context.md`:
- Run `ruff check` and `mypy --strict` before completing
- Use Rich console for CLI output, never `print()`
- Type hints required on all public functions
- Use `|` union syntax (Python 3.10+)
- Use `model_config = ConfigDict(extra="forbid")` on all Pydantic models

### Testing Standards

```python
# tests/unit/models/test_types.py

import pytest
from pydantic import BaseModel, ValidationError

from resume_as_code.models.types import Year, YearMonth


class YearMonthModel(BaseModel):
    """Test model for YearMonth type."""
    date: YearMonth  # Required field
    optional_date: YearMonth | None = None  # Optional field


class YearModel(BaseModel):
    """Test model for Year type."""
    year: Year  # Required field
    optional_year: Year | None = None  # Optional field


class TestYearMonth:
    """Tests for YearMonth annotated type."""

    def test_valid_format_accepted(self) -> None:
        """YYYY-MM format is accepted."""
        model = YearMonthModel(date="2024-01")
        assert model.date == "2024-01"

    def test_extended_format_normalized(self) -> None:
        """YYYY-MM-DD is normalized to YYYY-MM."""
        model = YearMonthModel(date="2024-01-15")
        assert model.date == "2024-01"

    def test_invalid_format_rejected(self) -> None:
        """Invalid format raises ValidationError."""
        with pytest.raises(ValidationError, match="YYYY-MM"):
            YearMonthModel(date="01-2024")

    def test_required_field_rejects_none(self) -> None:
        """Required YearMonth field rejects None."""
        # BeforeValidator returns None, then type validation fails
        with pytest.raises(ValidationError, match="string"):
            YearMonthModel(date=None)  # type: ignore[arg-type]

    def test_optional_accepts_none(self) -> None:
        """Optional YearMonth accepts None."""
        model = YearMonthModel(date="2024-01", optional_date=None)
        assert model.optional_date is None

    def test_optional_accepts_valid_value(self) -> None:
        """Optional YearMonth accepts valid value."""
        model = YearMonthModel(date="2024-01", optional_date="2025-06")
        assert model.optional_date == "2025-06"

    def test_invalid_month_format_valid(self) -> None:
        """Month outside 01-12 passes format validation (semantic validation separate)."""
        # BeforeValidator only checks format pattern, not semantic validity
        model = YearMonthModel(date="2024-99")
        assert model.date == "2024-99"  # Format valid, semantically invalid


class TestYear:
    """Tests for Year annotated type."""

    def test_string_year_accepted(self) -> None:
        """String year is accepted."""
        model = YearModel(year="2024")
        assert model.year == "2024"

    def test_int_year_coerced(self) -> None:
        """Integer year is coerced to string."""
        model = YearModel(year=2024)  # type: ignore[arg-type]
        assert model.year == "2024"

    def test_extended_format_normalized(self) -> None:
        """Extended format is normalized to YYYY."""
        model = YearModel(year="2024-01")
        assert model.year == "2024"

    def test_invalid_format_rejected(self) -> None:
        """Invalid format raises ValidationError."""
        with pytest.raises(ValidationError, match="YYYY"):
            YearModel(year="24")

    def test_required_field_rejects_none(self) -> None:
        """Required Year field rejects None."""
        with pytest.raises(ValidationError, match="string"):
            YearModel(year=None)  # type: ignore[arg-type]

    def test_optional_accepts_none(self) -> None:
        """Optional Year accepts None."""
        model = YearModel(year="2024", optional_year=None)
        assert model.optional_year is None


class TestJsonSchema:
    """Tests for JSON schema generation."""

    def test_year_month_schema_has_pattern(self) -> None:
        """YearMonth generates schema with pattern constraint."""
        schema = YearMonthModel.model_json_schema()
        # Verify pattern is in schema (may be in properties or $defs)
        assert "pattern" in str(schema)
        assert r"\d{4}-\d{2}" in str(schema)

    def test_year_schema_has_pattern(self) -> None:
        """Year generates schema with pattern constraint."""
        schema = YearModel.model_json_schema()
        assert "pattern" in str(schema)
        assert r"\d{4}" in str(schema)
```

### Backward Compatibility

All existing validators have identical behavior, so:
1. No data migration required
2. Existing YAML files remain valid
3. Existing tests should pass without changes

### WorkUnit.time_started/time_ended - Out of Scope

WorkUnit uses Python `date` objects (`time_started: date | None`, `time_ended: date | None`).
This is intentional for finer granularity (day-level precision) and is NOT being changed.
The `YearMonth` and `Year` types are for string-based date fields only.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#3.2 Data Architecture]
- [Source: _bmad-output/planning-artifacts/epics/epic-7-schema-data-model-refactoring.md#Story 7.3]
- [Source: src/resume_as_code/models/position.py:65-73 - validate_date_format]
- [Source: src/resume_as_code/models/education.py:45-66 - validate_year_format]
- [Source: src/resume_as_code/models/certification.py:27-47 - validate_date_format]
- [Source: src/resume_as_code/models/board_role.py:28-46 - validate_date_format]
- [Source: src/resume_as_code/models/publication.py:27-43 - validate_date_format]
- [Pydantic v2 Annotated validators: https://docs.pydantic.dev/latest/concepts/validators/#annotated-validators]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- Created `src/resume_as_code/models/types.py` with `YearMonth` and `Year` annotated types using Pydantic v2 `BeforeValidator` and `WithJsonSchema`
- `YearMonth` normalizes YYYY-MM-DD to YYYY-MM (consistent with existing Certification behavior)
- `Year` coerces int to string and normalizes extended formats to YYYY
- Used `WithJsonSchema` to override schema generation and include pattern constraints (workaround for Pydantic #12417)
- Removed 5 duplicate `validate_date_format` / `validate_year_format` field validators from Position, Education, Certification, BoardRole, Publication models
- Updated 3 tests that expected YYYY-MM-DD rejection to now expect normalization (Position, Publication)
- All 1701 tests pass with 33 warnings (unrelated to this change)
- ruff check and mypy --strict pass with no issues

### File List

- src/resume_as_code/models/types.py (new)
- src/resume_as_code/models/__init__.py (modified - exports Year, YearMonth)
- src/resume_as_code/models/position.py (modified - uses YearMonth, removed validator)
- src/resume_as_code/models/education.py (modified - uses Year, renamed year to graduation_year)
- src/resume_as_code/models/certification.py (modified - uses YearMonth, removed validator)
- src/resume_as_code/models/board_role.py (modified - uses YearMonth, removed validator)
- src/resume_as_code/models/publication.py (modified - uses YearMonth, removed validator)
- src/resume_as_code/providers/docx.py (modified - updated to use graduation_year)
- src/resume_as_code/templates/modern.html (modified - updated to use graduation_year)
- src/resume_as_code/templates/executive.html (modified - updated to use graduation_year)
- src/resume_as_code/templates/executive-classic.html (modified - updated to use graduation_year)
- src/resume_as_code/templates/ats-safe.html (modified - updated to use graduation_year)
- src/resume_as_code/commands/list_cmd.py (modified - updated JSON output key)
- src/resume_as_code/commands/show.py (modified - updated JSON output key)
- src/resume_as_code/commands/new.py (modified - updated Education constructor)
- tests/unit/test_types.py (new - 17 tests for YearMonth and Year types)
- tests/unit/test_position.py (modified - test_date_validation_full_date_normalized)
- tests/unit/test_publication.py (modified - test_date_format_validation_day_format_normalized)
- tests/unit/test_education.py (modified - updated all year references to graduation_year)
- tests/unit/test_inline_education.py (modified - updated Education constructor calls)
- tests/unit/test_docx_provider.py (modified - updated Education constructor calls)
- tests/unit/test_education_commands.py (modified - updated Education constructor calls and JSON assertions)
- tests/integration/test_template_rendering.py (modified - updated Education constructor calls)
- tests/unit/test_executive_template.py (modified - updated year to graduation_year)
- tests/unit/test_pdf_provider.py (modified - updated year to graduation_year)
- tests/unit/test_resume_model.py (modified - updated year to graduation_year)
- tests/integration/test_plan_command.py (modified - updated year to graduation_year)
- .resume.yaml (modified - updated year to graduation_year)
- examples/.resume.yaml (modified - updated year to graduation_year)

### Change Log

- 2026-01-15: Implemented Story 7.3 - Standardized Date Types. Created reusable YearMonth and Year annotated types, replaced duplicate validators across 5 models, added 17 new tests.
- 2026-01-15: Code Review Task 3.1 - Renamed Education.year to Education.graduation_year per AC #4. Updated model, providers (docx.py), templates (modern, executive, executive-classic, ats-safe), commands (list_cmd, show, new), and all test files. All 1701 tests pass.
- 2026-01-15: Code Review - All findings remediated:
  - M1: Fixed types.py docstring to show graduation_year instead of year
  - M2: Added documentation to CLI validation functions explaining intentional duplication
  - L2: Added ConfigDict(extra="forbid") to Education model for consistency
  - Data migration: Updated .resume.yaml and examples/.resume.yaml to use graduation_year
  - Test fixes: Updated test_executive_template.py, test_pdf_provider.py, test_resume_model.py, test_plan_command.py to use graduation_year
  - All 1701 tests pass, ruff clean, mypy --strict clean

