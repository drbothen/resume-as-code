# Story 6.16: Enhanced Scope Indicators (P&L, Revenue, Geography)

Status: done

## Story

As a **CTO or senior executive**,
I want **enhanced scope indicators with P&L, revenue, and geographic reach**,
So that **my leadership scale is immediately visible for each position**.

> **Research Note (2026-01-12):** CTO resume research confirms that P&L responsibility, revenue impact, and geographic scope are the most important metrics for executive positions. These must appear prominently for every position.

## Acceptance Criteria

1. **Given** a position in `positions.yaml` has scope fields
   **When** the config is:
   ```yaml
   positions:
     pos-acme-cto:
       employer: "Acme Corporation"
       title: "Chief Technology Officer"
       start_date: "2020-01"
       scope:
         revenue: "$500M"
         team_size: 200
         direct_reports: 15
         budget: "$50M"
         pl_responsibility: "$100M"
         geography: "Global (15 countries)"
   ```
   **Then** the position loads and validates successfully
   **And** scope indicators are available for template rendering

2. **Given** a position has scope data
   **When** the executive or CTO template renders
   **Then** scope appears as a prominent line below the position title:
   ```
   $500M revenue | 200+ engineers | $50M technology budget | Global (15 countries)
   ```

3. **Given** a position has `pl_responsibility` field
   **When** the scope line is formatted
   **Then** P&L appears first (most important for CTO): "$100M P&L responsibility"

4. **Given** a position has only some scope fields
   **When** the scope line is formatted
   **Then** only populated fields appear (graceful handling)
   **And** fields are pipe-separated with consistent styling

5. **Given** work units have scope data (legacy)
   **When** the resume renders
   **Then** work unit scope data is merged/overridden by position scope
   **And** position scope takes precedence for the position-level display

6. **Given** I run `resume new position`
   **When** prompted
   **Then** I'm optionally asked for scope data:
     1. Revenue impact (e.g., "$500M")
     2. Team size (number)
     3. Direct reports (number)
     4. Budget managed (e.g., "$50M")
     5. P&L responsibility (e.g., "$100M")
     6. Geographic reach (e.g., "Global", "EMEA", "North America")

7. **Given** I run non-interactively (LLM mode):
   ```bash
   resume new position \
     --employer "Acme Corp" \
     --title "CTO" \
     --start-date 2020-01 \
     --scope-revenue "$500M" \
     --scope-team-size 200 \
     --scope-budget "$50M" \
     --scope-pl "$100M" \
     --scope-geography "Global (15 countries)"
   ```
   **When** the command executes
   **Then** the position is created with all scope fields

## Tasks / Subtasks

- [x] Task 1: Create PositionScope model (AC: #1)
  - [x] 1.1: Create `PositionScope` Pydantic model in `models/position.py`
  - [x] 1.2: Add fields: revenue, team_size, direct_reports, budget, pl_responsibility, geography, customers
  - [x] 1.3: All fields optional (str | None or int | None)
  - [x] 1.4: Add scope field to Position model: `scope: PositionScope | None = None`

- [x] Task 2: Create scope formatting service (AC: #2, #3, #4)
  - [x] 2.1: Add `format_scope_line()` function to `services/position_service.py`
  - [x] 2.2: Order: P&L first, then revenue, team_size, budget, geography
  - [x] 2.3: Pipe-separated output with consistent formatting
  - [x] 2.4: Return None if no scope fields populated

- [x] Task 3: Update ResumeData model (AC: #2, #5)
  - [x] 3.1: Update `ResumeData._build_item_from_position()` to include scope_line
  - [x] 3.2: Handle legacy work unit scope data (merge/override)
  - [x] 3.3: Pass scope_line to template context via ResumeItem

- [x] Task 4: Update templates (AC: #2)
  - [x] 4.1: Add scope line display to `templates/executive.html`
  - [x] 4.2: Position scope below title, above achievements
  - [x] 4.3: Update CSS styling for scope indicators in `templates/executive.css`
  - [x] 4.4: Use accent color, slightly smaller font, italic

- [x] Task 5: Update position management command (AC: #6, #7)
  - [x] 5.1: Add scope flags to `resume new position` command
  - [x] 5.2: Support interactive prompts for scope fields (optional)
  - [x] 5.3: Support all flags for non-interactive mode

- [x] Task 6: Update schema (AC: #1)
  - [x] 6.1: Update `positions.schema.json` with scope object

- [x] Task 7: Testing
  - [x] 7.1: Add unit tests for PositionScope model
  - [x] 7.2: Add tests for scope line formatting
  - [x] 7.3: Add tests for template rendering with scope
  - [x] 7.4: All 1564 tests pass

- [x] Task 8: Code quality verification
  - [x] 8.1: Run `ruff check src tests --fix` - passed
  - [x] 8.2: Run `mypy src --strict` - zero errors
  - [x] 8.3: Run `pytest` - all 1564 tests pass

## Dev Notes

### Architecture Compliance

This story implements FR52 (Enhanced Scope Indicators) based on CTO resume research (2026-01-12). Scope indicators are critical for demonstrating leadership scale.

**Critical Rules from project-context.md:**
- Use `|` union syntax for optional fields (Python 3.10+)
- Templates render gracefully when optional data missing
- Services do the heavy lifting, commands orchestrate

### Project Structure Notes

- **Alignment:** Extends existing Position model from Story 6.7 (positions data model)
- **Paths:** Extends `models/position.py`, adds service function in `services/position_service.py`
- **Modules:** No new modules - extends existing position model and service
- **Naming:** `PositionScope`, `scope`, `format_scope_line()` follow project conventions
- **Conflicts:** None detected - additive change to existing Position model

### PositionScope Model Design

```python
# src/resume_as_code/models/position.py

from __future__ import annotations

from pydantic import BaseModel


class PositionScope(BaseModel):
    """Scope indicators for executive positions."""

    revenue: str | None = None  # e.g., "$500M"
    team_size: int | None = None  # Total engineers/team members
    direct_reports: int | None = None  # Direct reports count
    budget: str | None = None  # e.g., "$50M technology budget"
    pl_responsibility: str | None = None  # P&L amount
    geography: str | None = None  # e.g., "Global", "APAC", "15 countries"
    customers: str | None = None  # e.g., "500K users", "Fortune 500 clients"


class Position(BaseModel):
    """Employment position record."""

    # ... existing fields ...
    scope: PositionScope | None = None
```

### Scope Formatting Service

```python
# src/resume_as_code/services/position_service.py

def format_scope_line(position: Position) -> str | None:
    """Format scope indicators for display."""
    if not position.scope:
        return None
    parts = []
    # P&L first (most important for CTO)
    if position.scope.pl_responsibility:
        parts.append(f"{position.scope.pl_responsibility} P&L")
    if position.scope.revenue:
        parts.append(f"{position.scope.revenue} revenue")
    if position.scope.team_size:
        parts.append(f"{position.scope.team_size}+ engineers")
    if position.scope.budget:
        parts.append(f"{position.scope.budget} budget")
    if position.scope.geography:
        parts.append(position.scope.geography)
    return " | ".join(parts) if parts else None
```

### Scope CSS Styling

```css
.scope-indicators {
  font-size: 10pt;
  color: #5a6a7a;
  margin-top: 0.25em;
  margin-bottom: 0.5em;
  font-style: italic;
}
```

### Dependencies

This story REQUIRES:
- Story 6.7 (Positions Data Model) - Position model exists

This story ENABLES:
- Story 6.4 (Executive Template) - Uses scope indicators
- Story 6.17 (CTO Template) - Uses prominent scope indicators

### Files to Create/Modify

**Modified Files:**
- `src/resume_as_code/models/position.py` - Add PositionScope model
- `src/resume_as_code/services/position_service.py` - Add format_scope_line()
- `src/resume_as_code/models/resume.py` - Include scope_line in template context
- `src/resume_as_code/templates/executive.html` - Add scope line display
- `src/resume_as_code/templates/executive.css` - Add scope styling
- `src/resume_as_code/commands/positions.py` - Add scope flags
- `positions.schema.json` - Add scope object

**New Files:**
- `tests/unit/test_position_scope.py` - Unit tests

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_position_scope.py -v

# Manual verification:
# Add scope to a position in positions.yaml
# Run: uv run resume build --jd examples/job-description.txt --template executive
# Open dist/resume.pdf and verify scope line appears below position title
```

### References

- [Source: epics.md#Story 6.16](_bmad-output/planning-artifacts/epics.md)
- [CTO Resume Research](_bmad-output/planning-artifacts/research/cto-resume-layout-research-2026-01-12.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- All 8 tasks completed successfully
- 24 new unit tests added in test_position_scope.py
- 4 CLI integration tests added in test_position_commands.py
- All 1564 tests pass (28 new tests for this story)
- mypy strict mode passes with zero errors
- ruff linting passes

### File List

**Modified:**
- src/resume_as_code/models/position.py
- src/resume_as_code/services/position_service.py
- src/resume_as_code/models/resume.py
- src/resume_as_code/templates/executive.html
- src/resume_as_code/templates/executive.css
- src/resume_as_code/commands/new.py
- schemas/positions.schema.json
- tests/unit/test_position_commands.py
- tests/unit/test_publication_commands.py

**Created:**
- tests/unit/test_position_scope.py
