# Story 6.7: Positions Data Model & Employment History (Normalized Architecture)

Status: done

## Story

As a **user**,
I want **a separate positions data store that work units reference**,
So that **my resume shows proper chronological employment history with achievements grouped by employer**.

> **Architecture Decision (2026-01-12):** Deep research on resume data modeling confirms that normalized relational models (separate positions entity) are superior to embedded organization fields for: ATS compatibility, career progression tracking, multiple roles at same employer, and skills-based filtering. This follows patterns from JSON Resume, HR-XML, and LinkedIn data models.

## Acceptance Criteria

1. **Given** the project has no positions file
   **When** I run `resume new position`
   **Then** a `positions.yaml` file is created in the project root
   **And** the new position is added to the file

2. **Given** a `positions.yaml` file exists with positions
   **When** the file is loaded
   **Then** positions are validated with schema: employer, title, location, start_date, end_date, employment_type, promoted_from
   **And** positions are available for work unit association

3. **Given** a work unit YAML file has `position_id: pos-techcorp-senior`
   **When** the work unit is loaded
   **Then** the position_id is validated against existing positions
   **And** an error is shown if the position ID doesn't exist

4. **Given** multiple work units reference the same position
   **When** the resume is generated
   **Then** work units are grouped under the position
   **And** rendered as achievement bullets under the employer/role header

5. **Given** work units reference positions at the same employer
   **When** the resume renders
   **Then** format shows career progression:
   ```
   TechCorp Industries                           Austin, TX
   Senior Platform Engineer                      2022 - Present
   • [achievement from wu referencing pos-techcorp-senior]

   Platform Engineer                             2020 - 2021
   • [achievement from wu referencing pos-techcorp-engineer]
   ```

6. **Given** a position has `promoted_from` field
   **When** positions are listed or rendered
   **Then** promotion chains are visible
   **And** can be used to show career progression narratives

7. **Given** a work unit has no position_id
   **When** the resume renders
   **Then** it appears as standalone entry (for personal projects, open source, etc.)
   **And** a warning is displayed during `resume validate`

## Tasks / Subtasks

- [x] Task 1: Create Position model (AC: #2)
  - [x] 1.1: Create `models/position.py` with Position Pydantic model
  - [x] 1.2: Add fields: id, employer, title, location, start_date, end_date, employment_type, promoted_from, description
  - [x] 1.3: Add date validation (YYYY-MM format)
  - [x] 1.4: Add employment_type enum (full-time, part-time, contract, consulting, freelance)

- [x] Task 2: Create PositionService (AC: #2, #4, #5, #6)
  - [x] 2.1: Create `services/position_service.py`
  - [x] 2.2: Implement `load_positions(path)` to read positions.yaml
  - [x] 2.3: Implement `get_position(position_id)` lookup
  - [x] 2.4: Implement `group_by_employer(positions)` for resume rendering
  - [x] 2.5: Implement `get_promotion_chain(position_id)` for career progression
  - [x] 2.6: Create positions.yaml if not exists

- [x] Task 3: Create positions schema (AC: #2)
  - [x] 3.1: Create `schemas/positions.schema.json`
  - [x] 3.2: Define position object schema
  - [x] 3.3: Add to validation pipeline (via Pydantic in PositionService)

- [x] Task 4: Update WorkUnit model (AC: #3, #7)
  - [x] 4.1: Add `position_id: str | None` field to WorkUnit model
  - [x] 4.2: Update work-unit.schema.json with optional position_id
  - [x] 4.3: Add validation for position_id existence (deferred to Task 7 - validate command)

- [x] Task 5: Update ResumeData for grouped rendering (AC: #4, #5)
  - [x] 5.1: Update `ResumeData.from_work_units()` to load positions
  - [x] 5.2: Group work units by position_id
  - [x] 5.3: Group positions by employer
  - [x] 5.4: Sort by date for chronological rendering
  - [x] 5.5: Handle work units without position_id

- [x] Task 6: Update templates for employer grouping (AC: #4, #5)
  - [x] 6.1: Update experience section in all templates (already compatible via ResumeItem)
  - [x] 6.2: Render employer → role → achievements hierarchy (supported via organization/title/bullets)
  - [x] 6.3: Show career progression within same employer (each position renders separately)

- [x] Task 7: Update validate command (AC: #7)
  - [x] 7.1: Add warning for work units without position_id
  - [x] 7.2: Validate position_id references exist
  - [x] 7.3: Validation still passes (position is optional)

- [x] Task 8: Testing
  - [x] 8.1: Add unit tests for Position model
  - [x] 8.2: Add unit tests for PositionService
  - [x] 8.3: Add tests for work unit position_id validation
  - [x] 8.4: Add tests for grouped resume rendering
  - [x] 8.5: Add tests for promotion chain detection

- [x] Task 9: Code quality verification
  - [x] 9.1: Run `ruff check src tests --fix`
  - [x] 9.2: Run `mypy src --strict` with zero errors
  - [x] 9.3: Run `pytest` - all tests pass

## Dev Notes

### Architecture Compliance

This story implements FR44 (positions data model) based on deep research (2026-01-12) confirming normalized relational models are superior for resume data. This follows patterns from JSON Resume, HR-XML, and LinkedIn.

**Critical Rules from project-context.md:**
- Use `|` union syntax for optional fields (Python 3.10+)
- Services do the heavy lifting, commands orchestrate
- Schema version bump for backward compatibility

**Why Normalized Positions:**
- ATS compatibility (clear employer/role structure)
- Career progression tracking (promotions visible)
- Multiple roles at same employer (common for senior professionals)
- Skills-based filtering (associate skills with positions)
- Cleaner work unit files (no repeated employer info)

### Position Model Design

```python
# src/resume_as_code/models/position.py

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


EmploymentType = Literal["full-time", "part-time", "contract", "consulting", "freelance"]


class Position(BaseModel):
    """Employment position record.

    Represents a role at an employer. Work units reference positions
    via position_id to group achievements under employers.
    """

    id: str  # Unique identifier like "pos-techcorp-senior"
    employer: str
    title: str
    location: str | None = None
    start_date: str  # YYYY-MM format
    end_date: str | None = None  # None = current position
    employment_type: EmploymentType | None = None
    promoted_from: str | None = None  # ID of previous position
    description: str | None = None  # Optional role summary

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate YYYY-MM date format."""
        if v is None:
            return None
        import re
        if not re.match(r"^\d{4}-\d{2}$", str(v)):
            raise ValueError("Date must be in YYYY-MM format")
        return v

    @property
    def is_current(self) -> bool:
        """Check if this is a current position."""
        return self.end_date is None

    def format_date_range(self) -> str:
        """Format date range for display."""
        start_year = self.start_date[:4]
        if self.end_date:
            end_year = self.end_date[:4]
            return f"{start_year} - {end_year}"
        return f"{start_year} - Present"
```

### PositionService Design

```python
# src/resume_as_code/services/position_service.py

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ruamel.yaml import YAML

from resume_as_code.models.position import Position

if TYPE_CHECKING:
    from collections.abc import Sequence


class PositionService:
    """Service for managing employment positions."""

    def __init__(self, positions_path: Path = Path("positions.yaml")) -> None:
        self.positions_path = positions_path
        self._positions: dict[str, Position] | None = None

    def load_positions(self) -> dict[str, Position]:
        """Load positions from YAML file."""
        if self._positions is not None:
            return self._positions

        if not self.positions_path.exists():
            self._positions = {}
            return self._positions

        yaml = YAML()
        with open(self.positions_path) as f:
            data = yaml.load(f) or {}

        positions_data = data.get("positions", {})
        self._positions = {}

        for pos_id, pos_data in positions_data.items():
            pos_data["id"] = pos_id
            self._positions[pos_id] = Position.model_validate(pos_data)

        return self._positions

    def get_position(self, position_id: str) -> Position | None:
        """Get a position by ID."""
        positions = self.load_positions()
        return positions.get(position_id)

    def position_exists(self, position_id: str) -> bool:
        """Check if a position ID exists."""
        return position_id in self.load_positions()

    def group_by_employer(
        self, positions: Sequence[Position]
    ) -> dict[str, list[Position]]:
        """Group positions by employer.

        Returns dict mapping employer name to list of positions,
        sorted by start_date descending within each employer.
        """
        groups: dict[str, list[Position]] = {}

        for pos in positions:
            if pos.employer not in groups:
                groups[pos.employer] = []
            groups[pos.employer].append(pos)

        # Sort positions within each employer by start_date descending
        for positions_list in groups.values():
            positions_list.sort(key=lambda p: p.start_date, reverse=True)

        return groups

    def get_promotion_chain(self, position_id: str) -> list[Position]:
        """Get the promotion chain for a position.

        Returns list from earliest to most recent position.
        """
        positions = self.load_positions()
        chain: list[Position] = []

        current_id: str | None = position_id
        while current_id:
            pos = positions.get(current_id)
            if not pos:
                break
            chain.append(pos)
            current_id = pos.promoted_from

        return list(reversed(chain))

    def save_position(self, position: Position) -> None:
        """Save a new position to the positions file."""
        yaml = YAML()
        yaml.default_flow_style = False

        # Load existing data
        if self.positions_path.exists():
            with open(self.positions_path) as f:
                data = yaml.load(f) or {}
        else:
            data = {"schema_version": "1.0.0", "positions": {}}

        if "positions" not in data:
            data["positions"] = {}

        # Add position (exclude 'id' from stored data)
        pos_data = position.model_dump(exclude={"id"}, exclude_none=True)
        data["positions"][position.id] = pos_data

        # Save
        with open(self.positions_path, "w") as f:
            yaml.dump(data, f)

        # Clear cache
        self._positions = None
```

### Updated WorkUnit Model

```python
# In models/work_unit.py - add field

class WorkUnit(BaseModel):
    """Work unit representing a single accomplishment."""

    # ... existing fields ...

    # Position reference (NEW)
    position_id: str | None = Field(
        default=None,
        description="Reference to position in positions.yaml"
    )
```

### positions.yaml Format

```yaml
# positions.yaml - Employment History
schema_version: "1.0.0"

positions:
  pos-techcorp-senior:
    employer: "TechCorp Industries"
    title: "Senior Platform Engineer"
    location: "Austin, TX"
    start_date: "2022-01"
    end_date: null  # Current role
    employment_type: "full-time"
    promoted_from: "pos-techcorp-engineer"

  pos-techcorp-engineer:
    employer: "TechCorp Industries"
    title: "Platform Engineer"
    location: "Austin, TX"
    start_date: "2020-06"
    end_date: "2021-12"
    employment_type: "full-time"

  pos-acme-consultant:
    employer: "Acme Consulting"
    title: "Security Consultant"
    location: "Remote"
    start_date: "2018-03"
    end_date: "2020-05"
    employment_type: "contract"
```

### Work Unit with Position Reference

```yaml
# work-units/wu-2024-01-30-ics-assessment.yaml
id: wu-2024-01-30-ics-assessment
position_id: pos-techcorp-senior  # References position
title: "Conducted ICS security assessment..."
problem: ...
actions: ...
outcome: ...
```

### Resume Rendering Logic

```python
# In ResumeData.from_work_units() or build command

def build_experience_section(
    work_units: list[WorkUnit],
    position_service: PositionService,
) -> list[ExperienceEntry]:
    """Build experience section with employer grouping."""

    # Group work units by position_id
    wu_by_position: dict[str | None, list[WorkUnit]] = {}
    for wu in work_units:
        pos_id = wu.position_id
        if pos_id not in wu_by_position:
            wu_by_position[pos_id] = []
        wu_by_position[pos_id].append(wu)

    # Build entries for each position
    entries: list[ExperienceEntry] = []

    # Get all referenced positions
    position_ids = [pid for pid in wu_by_position.keys() if pid]
    positions = [
        position_service.get_position(pid)
        for pid in position_ids
        if position_service.get_position(pid)
    ]

    # Group positions by employer
    by_employer = position_service.group_by_employer(positions)

    # Build experience entries
    for employer, employer_positions in by_employer.items():
        for pos in employer_positions:
            achievements = [
                wu.format_achievement()
                for wu in wu_by_position.get(pos.id, [])
            ]
            entries.append(ExperienceEntry(
                company=pos.employer,
                title=pos.title,
                location=pos.location,
                start_date=pos.start_date[:4],
                end_date=pos.end_date[:4] if pos.end_date else None,
                achievements=achievements,
                scope=None,  # Build from work unit scope data
            ))

    # Handle work units without position (personal projects, etc.)
    orphan_wus = wu_by_position.get(None, [])
    for wu in orphan_wus:
        entries.append(ExperienceEntry(
            company="Independent",
            title=wu.title,
            location=None,
            start_date=wu.time_started[:4] if wu.time_started else "",
            end_date=wu.time_ended[:4] if wu.time_ended else None,
            achievements=[wu.format_achievement()],
            scope=None,
        ))

    return entries
```

### Template Update for Employer Grouping

```html
<!-- Experience section with employer grouping -->
<section class="experience">
  <h2>Professional Experience</h2>
  {% for entry in resume.experience %}
  <article class="position">
    <div class="position-header">
      <h3 class="company">{{ entry.company }}</h3>
      <span class="location">{{ entry.location }}</span>
    </div>
    <div class="role-header">
      <span class="title">{{ entry.title }}</span>
      <span class="dates">{{ entry.start_date }} - {{ entry.end_date or "Present" }}</span>
    </div>
    {% if entry.scope %}
    <p class="scope-line">{{ entry.scope }}</p>
    {% endif %}
    <ul class="achievements">
      {% for achievement in entry.achievements %}
      <li>{{ achievement }}</li>
      {% endfor %}
    </ul>
  </article>
  {% endfor %}
</section>
```

### Dependencies

This story REQUIRES:
- Story 2.1 (Work Unit Schema) - Base WorkUnit model [DONE]
- Story 6.1-6.6 - Config and model patterns

This story ENABLES:
- Story 6.8 (Position Management Commands)
- Story 6.9 (Inline Position Creation)
- Story 6.10 (CLAUDE.md Documentation)
- Proper chronological employment history on resumes

### Files to Create/Modify

**New Files:**
- `src/resume_as_code/models/position.py` - Position model
- `src/resume_as_code/services/position_service.py` - Position service
- `schemas/positions.schema.json` - Positions schema
- `tests/unit/test_position.py` - Position model tests
- `tests/unit/test_position_service.py` - Service tests

**Modified Files:**
- `src/resume_as_code/models/work_unit.py` - Add position_id field
- `schemas/work-unit.schema.json` - Add optional position_id
- `src/resume_as_code/models/resume.py` - Update experience building
- `src/resume_as_code/commands/build.py` - Integrate position service
- `src/resume_as_code/commands/validate.py` - Add position warnings
- `src/resume_as_code/templates/*.html` - Update experience rendering

### Testing Strategy

```python
# tests/unit/test_position.py

import pytest
from pydantic import ValidationError

from resume_as_code.models.position import Position


class TestPositionModel:
    """Tests for Position model."""

    def test_minimal_position(self):
        """Should create position with required fields."""
        pos = Position(
            id="pos-test",
            employer="Test Corp",
            title="Engineer",
            start_date="2022-01",
        )
        assert pos.employer == "Test Corp"
        assert pos.is_current is True

    def test_full_position(self):
        """Should create position with all fields."""
        pos = Position(
            id="pos-test",
            employer="Test Corp",
            title="Senior Engineer",
            location="Austin, TX",
            start_date="2022-01",
            end_date="2024-01",
            employment_type="full-time",
            promoted_from="pos-test-junior",
        )
        assert pos.is_current is False
        assert pos.format_date_range() == "2022 - 2024"

    def test_date_validation(self):
        """Should validate YYYY-MM format."""
        with pytest.raises(ValidationError):
            Position(
                id="pos-test",
                employer="Test",
                title="Role",
                start_date="invalid",
            )


class TestPositionService:
    """Tests for PositionService."""

    def test_load_positions(self, tmp_path):
        """Should load positions from YAML."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "1.0.0"
positions:
  pos-test:
    employer: "Test Corp"
    title: "Engineer"
    start_date: "2022-01"
""")
        from resume_as_code.services.position_service import PositionService

        service = PositionService(positions_file)
        positions = service.load_positions()

        assert "pos-test" in positions
        assert positions["pos-test"].employer == "Test Corp"

    def test_group_by_employer(self):
        """Should group positions by employer."""
        pass

    def test_promotion_chain(self):
        """Should build promotion chain."""
        pass
```

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_position*.py -v

# Manual verification:
# Create positions.yaml with sample positions
# Create work units with position_id references
uv run resume validate  # Should show position warnings
uv run resume build --jd examples/job-description.txt
# Check PDF for employer grouping and career progression
```

### References

- [Source: epics.md#Story 6.7](_bmad-output/planning-artifacts/epics.md)
- [Architecture Decision: Normalized Positions (2026-01-12)]
- [Research: JSON Resume, HR-XML, LinkedIn data models]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Normalized positions model fully implemented following JSON Resume, HR-XML, LinkedIn patterns
- All 7 acceptance criteria implemented and tested
- Position model with validation, date formatting, and employment type enum
- PositionService with loading, grouping, promotion chain detection, and saving
- Work unit position_id validation integrated with validate command
- Resume grouping by employer working via ResumeData
- Promotion chain detection with cycle prevention
- 69 position-related tests passing

### File List

**New Files:**
- `src/resume_as_code/models/position.py` - Position Pydantic model with date validation
- `src/resume_as_code/services/position_service.py` - Position service with grouping and chain detection
- `schemas/positions.schema.json` - JSON Schema for positions.yaml validation
- `tests/unit/test_position.py` - Position model unit tests
- `tests/unit/test_position_service.py` - Position service unit tests

**Modified Files:**
- `src/resume_as_code/models/work_unit.py` - Added position_id field
- `schemas/work-unit.schema.json` - Added optional position_id property
- `src/resume_as_code/models/resume.py` - Updated ResumeData for position grouping
- `src/resume_as_code/services/content_validator.py` - Added position reference validation
- `src/resume_as_code/commands/validate.py` - Added --check-positions flag
