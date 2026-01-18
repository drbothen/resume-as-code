# Story 7.6: Position Reference Integrity

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **work unit position_id references validated at load time with Position objects attached**,
So that **invalid references are caught early and Position data is efficiently accessible**.

## Acceptance Criteria

1. **Given** a work unit with `position_id: pos-nonexistent`
   **When** I run `resume validate --check-positions`
   **Then** validation fails with error message
   **And** error includes the invalid position_id and suggestions

2. **Given** a work unit without position_id
   **When** validation runs
   **Then** it passes (position_id is optional for standalone projects)

3. **Given** WorkUnitLoader loads work units
   **When** positions are available
   **Then** each position_id is validated against positions.yaml
   **And** Position objects are attached to WorkUnit for efficient access

4. **Given** I call `work_unit.position`
   **When** position_id is valid
   **Then** I get the Position object directly
   **And** no separate lookup is needed

## Tasks / Subtasks

- [x] Task 1: Add Position attachment to WorkUnit model (AC: #4)
  - [x] 1.1 Add `_position: Position | None = PrivateAttr(default=None)` to WorkUnit
  - [x] 1.2 Add `position` property that returns `self._position`
  - [x] 1.3 Add `attach_position(position: Position)` method with ID validation
  - [x] 1.4 Add unit tests for position attachment

- [x] Task 2: Create WorkUnitLoader service (AC: #3)
  - [x] 2.1 Create `src/resume_as_code/services/work_unit_loader.py`
  - [x] 2.2 Implement `load_all(directory: Path) -> list[WorkUnit]` method
  - [x] 2.3 Implement `load_with_positions(positions: dict[str, Position]) -> list[WorkUnit]`
  - [x] 2.4 Validate position_id references and attach Position objects
  - [x] 2.5 Raise clear ValidationError for invalid position_ids

- [x] Task 3: Enhance error messages (AC: #1, #2)
  - [x] 3.1 Include invalid position_id value in error message
  - [x] 3.2 Suggest similar position IDs if available (fuzzy match)
  - [x] 3.3 Include suggestion to run `resume list positions` or create position
  - [x] 3.4 Ensure missing position_id is info-level (not error)

- [x] Task 4: Integrate with existing code (AC: #1, #3)
  - [x] 4.1 Update `resume plan` to use WorkUnitLoader
  - [x] 4.2 Update `resume build` to use WorkUnitLoader
  - [x] 4.3 Keep backward compatibility with existing validate command
  - [x] 4.4 Ensure `--check-positions` flag still works as expected

- [x] Task 5: Add tests and quality checks
  - [x] 5.1 Unit tests for WorkUnitLoader
  - [x] 5.2 Integration tests for validation flow
  - [x] 5.3 Run `ruff check` and `mypy --strict`

## Dev Notes

### Current State Analysis

**Existing Implementation:**
- `--check-positions` flag already exists in `commands/validate.py:45-48`
- Position validation implemented in `services/content_validator.py:145-191`
- `position_id` field exists on WorkUnit (`models/work_unit.py:226-228`)
- Error handling already distinguishes `MISSING_POSITION_ID` (info) from `INVALID_POSITION_ID` (error)

**Gap to Address:**
- No `position` property on WorkUnit (requires separate lookup)
- No centralized loader that attaches Position objects
- No fuzzy matching for suggestions on invalid position_id

### Implementation Pattern

**WorkUnit Enhancement:**
```python
# models/work_unit.py

from pydantic import PrivateAttr
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from resume_as_code.models.position import Position

class WorkUnit(BaseModel):
    # ... existing fields ...

    position_id: str | None = Field(
        default=None,
        description="Reference to position in positions.yaml for employer grouping",
    )

    # Private attribute for attached Position (not serialized)
    _position: Position | None = PrivateAttr(default=None)

    @property
    def position(self) -> Position | None:
        """Get attached Position object.

        Returns None if position_id is None or Position hasn't been attached.
        Use WorkUnitLoader.load_with_positions() to attach positions.
        """
        return self._position

    def attach_position(self, position: Position) -> None:
        """Attach a Position object to this WorkUnit.

        Args:
            position: Position to attach.

        Raises:
            ValueError: If position.id doesn't match position_id.
        """
        if self.position_id is None:
            raise ValueError("Cannot attach position to WorkUnit without position_id")
        if position.id != self.position_id:
            raise ValueError(
                f"Position ID mismatch: WorkUnit.position_id={self.position_id!r}, "
                f"Position.id={position.id!r}"
            )
        self._position = position
```

**WorkUnitLoader Service:**
```python
# src/resume_as_code/services/work_unit_loader.py
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from ruamel.yaml import YAML

from resume_as_code.models.errors import ValidationError
from resume_as_code.models.work_unit import WorkUnit

if TYPE_CHECKING:
    from resume_as_code.models.position import Position

logger = logging.getLogger(__name__)


class WorkUnitLoader:
    """Loads and validates Work Units from YAML files.

    Provides methods to load work units with optional position validation
    and attachment for efficient access.
    """

    def __init__(self, work_units_dir: Path) -> None:
        """Initialize loader.

        Args:
            work_units_dir: Directory containing work unit YAML files.
        """
        self.work_units_dir = work_units_dir
        self._yaml = YAML()
        self._yaml.preserve_quotes = True

    def load_all(self) -> list[WorkUnit]:
        """Load all work units from directory.

        Returns:
            List of WorkUnit objects.

        Raises:
            ValidationError: If any work unit fails schema validation.
        """
        work_units: list[WorkUnit] = []

        if not self.work_units_dir.exists():
            return work_units

        for yaml_file in sorted(self.work_units_dir.glob("*.yaml")):
            if yaml_file.name.startswith("."):
                continue

            with yaml_file.open() as f:
                data = self._yaml.load(f)

            try:
                wu = WorkUnit.model_validate(data)
                work_units.append(wu)
            except Exception as e:
                raise ValidationError(
                    f"Invalid work unit {yaml_file.name}: {e}"
                ) from e

        return work_units

    def load_with_positions(
        self,
        positions: dict[str, Position],
    ) -> list[WorkUnit]:
        """Load work units with position validation and attachment.

        Args:
            positions: Dictionary of position_id -> Position.

        Returns:
            List of WorkUnit objects with Position attached.

        Raises:
            ValidationError: If any position_id references invalid position.
        """
        work_units = self.load_all()
        invalid_refs: list[tuple[str, str]] = []  # (wu_id, position_id)

        for wu in work_units:
            if wu.position_id is None:
                continue

            if wu.position_id not in positions:
                invalid_refs.append((wu.id, wu.position_id))
            else:
                wu.attach_position(positions[wu.position_id])

        if invalid_refs:
            # Build helpful error message
            suggestions = self._suggest_positions(invalid_refs, set(positions.keys()))
            msg_parts = ["Invalid position_id references found:"]

            for wu_id, pos_id in invalid_refs:
                msg = f"\n  - {wu_id}: position_id={pos_id!r}"
                if pos_id in suggestions:
                    msg += f" (did you mean: {suggestions[pos_id]}?)"
                msg_parts.append(msg)

            msg_parts.append("\n\nRun 'resume list positions' to see valid position IDs")

            raise ValidationError("".join(msg_parts))

        return work_units

    def _suggest_positions(
        self,
        invalid_refs: list[tuple[str, str]],
        valid_ids: set[str],
    ) -> dict[str, str]:
        """Suggest similar position IDs for invalid references.

        Uses simple string similarity to find close matches.

        Args:
            invalid_refs: List of (wu_id, invalid_position_id) tuples.
            valid_ids: Set of valid position IDs.

        Returns:
            Dictionary mapping invalid_id -> suggested_id (if found).
        """
        from difflib import get_close_matches

        suggestions: dict[str, str] = {}

        for _, pos_id in invalid_refs:
            matches = get_close_matches(pos_id, list(valid_ids), n=1, cutoff=0.6)
            if matches:
                suggestions[pos_id] = matches[0]

        return suggestions
```

### Testing Standards

```python
# tests/unit/models/test_work_unit_position.py

import pytest
from pydantic import ValidationError as PydanticValidationError

from resume_as_code.models.work_unit import WorkUnit, Problem, Outcome
from resume_as_code.models.position import Position


@pytest.fixture
def sample_work_unit() -> WorkUnit:
    """Create sample work unit with position_id."""
    return WorkUnit(
        id="wu-2024-01-01-test",
        title="Test work unit",
        problem=Problem(statement="Test problem statement here"),
        actions=["First action with enough characters to pass validation"],
        outcome=Outcome(result="Test outcome result here"),
        position_id="pos-acme-engineer",
    )


@pytest.fixture
def sample_position() -> Position:
    """Create sample position."""
    return Position(
        id="pos-acme-engineer",
        employer="Acme Corp",
        title="Software Engineer",
        start_date="2022-01",
    )


def test_work_unit_position_property_none_by_default(sample_work_unit: WorkUnit) -> None:
    """Position property returns None before attachment."""
    assert sample_work_unit.position is None


def test_attach_position_success(
    sample_work_unit: WorkUnit, sample_position: Position
) -> None:
    """Attaching matching position succeeds."""
    sample_work_unit.attach_position(sample_position)

    assert sample_work_unit.position is not None
    assert sample_work_unit.position.id == "pos-acme-engineer"
    assert sample_work_unit.position.employer == "Acme Corp"


def test_attach_position_id_mismatch(sample_work_unit: WorkUnit) -> None:
    """Attaching position with wrong ID raises ValueError."""
    wrong_position = Position(
        id="pos-other-company",
        employer="Other Corp",
        title="Developer",
        start_date="2023-01",
    )

    with pytest.raises(ValueError, match="Position ID mismatch"):
        sample_work_unit.attach_position(wrong_position)


def test_attach_position_without_position_id() -> None:
    """Cannot attach position to WorkUnit without position_id."""
    wu = WorkUnit(
        id="wu-2024-01-02-standalone",
        title="Standalone work unit",
        problem=Problem(statement="Problem statement here"),
        actions=["Action with enough characters here"],
        outcome=Outcome(result="Outcome result here"),
        # position_id is None
    )

    position = Position(
        id="pos-any",
        employer="Any Corp",
        title="Any Title",
        start_date="2024-01",
    )

    with pytest.raises(ValueError, match="Cannot attach position"):
        wu.attach_position(position)
```

```python
# tests/unit/services/test_work_unit_loader.py

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from resume_as_code.models.errors import ValidationError
from resume_as_code.models.position import Position
from resume_as_code.services.work_unit_loader import WorkUnitLoader


@pytest.fixture
def temp_work_units_dir() -> Path:
    """Create temporary work units directory with sample files."""
    with TemporaryDirectory() as tmpdir:
        work_units_dir = Path(tmpdir) / "work-units"
        work_units_dir.mkdir()

        # Create valid work unit
        (work_units_dir / "wu-valid.yaml").write_text("""
id: wu-2024-01-01-valid
title: Valid work unit
position_id: pos-acme-engineer
problem:
  statement: Test problem statement here
actions:
  - First action with enough characters to pass validation
outcome:
  result: Test outcome result here
""")

        yield work_units_dir


def test_load_with_positions_attaches_position(temp_work_units_dir: Path) -> None:
    """Loading with positions attaches Position to WorkUnit."""
    loader = WorkUnitLoader(temp_work_units_dir)
    positions = {
        "pos-acme-engineer": Position(
            id="pos-acme-engineer",
            employer="Acme Corp",
            title="Engineer",
            start_date="2022-01",
        )
    }

    work_units = loader.load_with_positions(positions)

    assert len(work_units) == 1
    assert work_units[0].position is not None
    assert work_units[0].position.employer == "Acme Corp"


def test_load_with_positions_invalid_ref_raises_error(temp_work_units_dir: Path) -> None:
    """Invalid position_id raises ValidationError with suggestion."""
    loader = WorkUnitLoader(temp_work_units_dir)
    positions = {
        "pos-acme-engineer-senior": Position(  # Different from referenced ID
            id="pos-acme-engineer-senior",
            employer="Acme Corp",
            title="Senior Engineer",
            start_date="2022-01",
        )
    }

    with pytest.raises(ValidationError) as exc_info:
        loader.load_with_positions(positions)

    error_msg = str(exc_info.value)
    assert "pos-acme-engineer" in error_msg
    assert "did you mean" in error_msg.lower() or "resume list positions" in error_msg.lower()
```

### Project Context Rules

From `project-context.md`:
- Run `ruff check` and `mypy --strict` before completing
- Use Rich console for CLI output, never `print()`
- Type hints required on all public functions
- Use `|` union syntax (Python 3.10+)
- Use `model_config = ConfigDict(extra="forbid")` on all Pydantic models

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-7-schema-data-model-refactoring.md#Story 7.6]
- [Source: src/resume_as_code/commands/validate.py:45-48 - existing --check-positions flag]
- [Source: src/resume_as_code/services/content_validator.py:145-191 - validate_position_reference]
- [Source: src/resume_as_code/models/work_unit.py:226-228 - position_id field]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- **Task 1**: Added `_position` PrivateAttr, `position` property, and `attach_position()` method to WorkUnit model. Uses TYPE_CHECKING import to avoid circular dependencies.
- **Task 2**: Created WorkUnitLoader service with `load_all()`, `load_with_positions()`, and `validate_position_references()` methods. Includes fuzzy matching for position ID suggestions using `difflib.get_close_matches`.
- **Task 3**: Enhanced `validate_position_reference()` in content_validator.py with fuzzy matching suggestions for invalid position IDs.
- **Task 4**: Added `--strict-positions` flag to both `plan` and `build` commands. Integration uses WorkUnitLoader for early validation when flag is set. Backward compatibility maintained - existing dictionary-based flow unchanged.
- **Task 5**: All 21 new tests pass. Total test suite: 1596 tests passing. ruff and mypy --strict pass on all modified files.

### File List

**New Files:**
- `src/resume_as_code/services/work_unit_loader.py` - WorkUnitLoader service
- `tests/unit/models/test_work_unit_position.py` - Position attachment unit tests (5 tests)
- `tests/unit/services/test_work_unit_loader.py` - WorkUnitLoader unit tests (9 tests)

**Modified Files:**
- `src/resume_as_code/models/work_unit.py` - Added position attachment capability
- `src/resume_as_code/services/content_validator.py` - Added fuzzy matching for position suggestions
- `src/resume_as_code/commands/plan.py` - Added --strict-positions flag
- `src/resume_as_code/commands/build.py` - Added --strict-positions flag
- `tests/unit/test_content_validator.py` - Added TestPositionReference class (7 tests)

## Code Review

### Review Date
2026-01-16

### Reviewer
Amelia (Dev Agent - Adversarial Code Review)

### Issues Found and Remediated

1. **Lint UP035** - Fixed import `typing.Generator` → `collections.abc.Generator` in test file
2. **Broad Exception catch** - Changed `Exception` to `PydanticValidationError` in work_unit_loader.py:71
3. **Empty positions edge case** - Fixed `if positions:` check in plan.py and build.py to always validate
4. **Missing tests** - Added 4 tests for `validate_position_references()` public method
5. **Docstring accuracy** - Fixed "sorted by filename" → "sorted alphabetically by file path"

### Tech Debt Noted

**Duplicate Position Validation Pattern:**
- `content_validator.py:validate_position_reference()` - returns warnings for validate command
- `work_unit_loader.py:validate_position_references()` - returns tuple for plan/build commands

Both use `difflib.get_close_matches` for suggestions. This duplication exists because:
1. The validate command needs individual file-level warnings
2. The loader service needs batch validation with attachment

**Recommendation for Future:** Consider extracting shared fuzzy matching logic to a utility function if additional consumers emerge.

### Final Test Results
- All tests pass: 1600/1600 (added 4 new tests for validate_position_references)
- ruff check: PASS
- mypy --strict: PASS

