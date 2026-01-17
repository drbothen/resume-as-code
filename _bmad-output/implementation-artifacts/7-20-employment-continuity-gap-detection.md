# Story 7.20: Employment Continuity & Gap Detection

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **job seeker**,
I want **my resume to maintain employment timeline continuity when work units are filtered by relevance**,
So that **tailored resumes don't appear to have unexplained employment gaps**.

## Acceptance Criteria

1. **Given** configuration `employment_continuity: minimum_bullet` (default)
   **When** filtering work units by JD relevance
   **Then** at least one work unit is included from each position
   **And** the highest-scoring work unit is selected even if below threshold

2. **Given** configuration `employment_continuity: allow_gaps`
   **When** filtering work units by JD relevance
   **Then** pure relevance filtering is applied
   **And** positions with no relevant work units are excluded

3. **Given** `employment_continuity: allow_gaps` is set
   **When** running `resume plan --jd job.txt`
   **Then** gap detection analyzes the resulting timeline
   **And** gaps >3 months are reported with warnings

4. **Given** a gap is detected during `plan`
   **When** displaying results
   **Then** warning shows: "⚠️ Employment Gap Detected"
   **And** shows which position(s) would be omitted
   **And** shows gap duration between positions
   **And** suggests using `--no-allow-gaps` to force minimum inclusion

5. **Given** CLI flag `--allow-gaps`
   **When** building a resume
   **Then** `employment_continuity: allow_gaps` behavior is used
   **And** gap detection warnings are shown

6. **Given** CLI flag `--no-allow-gaps`
   **When** building a resume
   **Then** `employment_continuity: minimum_bullet` behavior is used
   **And** at least one bullet per position is guaranteed

7. **Given** `--show-excluded` flag is used with detected gaps
   **When** displaying excluded work units
   **Then** excluded work units that would cause gaps are flagged
   **And** shows "⚠️ Excluding this creates X-month gap"

## Tasks / Subtasks

- [x] Task 1: Add configuration and type definitions (AC: #1, #2)
  - [x] 1.1 Add `EmploymentContinuityMode` type alias: `Literal["minimum_bullet", "allow_gaps"]`
  - [x] 1.2 Add `employment_continuity: EmploymentContinuityMode = "minimum_bullet"` to `ResumeConfig`
  - [x] 1.3 Add unit tests for config validation

- [x] Task 2: Create EmploymentContinuityService (AC: #1, #3)
  - [x] 2.1 Create `services/employment_continuity.py`
  - [x] 2.2 Implement `EmploymentGap` dataclass
  - [x] 2.3 Implement `ensure_continuity()` method
  - [x] 2.4 Implement `detect_gaps()` method
  - [x] 2.5 Implement `format_gap_warning()` method
  - [x] 2.6 Add unit tests for service

- [x] Task 3: Wire into plan command (AC: #3, #4)
  - [x] 3.1 Call `ensure_continuity()` after relevance scoring
  - [x] 3.2 Call `detect_gaps()` when mode is `allow_gaps`
  - [x] 3.3 Display gap warnings with Rich formatting
  - [x] 3.4 Add integration tests for plan with gaps

- [x] Task 4: Add CLI flags (AC: #5, #6)
  - [x] 4.1 Add `--allow-gaps/--no-allow-gaps` flag to plan.py
  - [x] 4.2 Add `--allow-gaps/--no-allow-gaps` flag to build.py
  - [x] 4.3 CLI flag overrides config when set
  - [x] 4.4 Add unit tests for CLI flag behavior

- [x] Task 5: Enhance --show-excluded output (AC: #7)
  - [x] 5.1 Flag excluded work units that would cause gaps
  - [x] 5.2 Show gap duration in excluded output
  - [x] 5.3 Add integration test for enhanced output

- [x] Task 6: Quality checks
  - [x] 6.1 Run `ruff check src tests --fix`
  - [x] 6.2 Run `ruff format src tests`
  - [x] 6.3 Run `mypy src --strict` (zero errors)
  - [x] 6.4 Update CLAUDE.md with new CLI options
  - [x] 6.5 Run full test suite

## Dev Notes

### Current State Analysis

**What exists:**
- `plan.py` command with work unit selection by relevance
- Position service with `load_positions()`
- Work unit ranking with scores
- `--show-excluded` flag for excluded work units

**Gap:**
- No continuity guarantee when filtering
- No gap detection
- Excluded positions can create timeline gaps

### Implementation Pattern

**Data Model:**
```python
# services/employment_continuity.py
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from resume_as_code.models.position import Position
    from resume_as_code.models.work_unit import WorkUnit

EmploymentContinuityMode = Literal["minimum_bullet", "allow_gaps"]

@dataclass
class EmploymentGap:
    """Detected gap in employment timeline."""
    start_date: date
    end_date: date
    duration_months: int
    missing_position_id: str
    missing_employer: str
```

**Service Implementation:**
```python
class EmploymentContinuityService:
    """Ensure employment timeline continuity in tailored resumes."""

    def __init__(
        self,
        mode: EmploymentContinuityMode = "minimum_bullet",
        min_gap_months: int = 3,
    ) -> None:
        self.mode = mode
        self.min_gap_months = min_gap_months

    def ensure_continuity(
        self,
        positions: list[Position],
        selected_work_units: list[WorkUnit],
        all_work_units: list[WorkUnit],
        scores: dict[str, float] | None = None,
    ) -> list[WorkUnit]:
        """Ensure at least one work unit per position if mode is minimum_bullet.

        Args:
            positions: All positions in timeline.
            selected_work_units: Work units selected by relevance scoring.
            all_work_units: All available work units.
            scores: Optional relevance scores for tiebreaking.

        Returns:
            Updated list of work units with continuity guaranteed.
        """
        if self.mode == "allow_gaps":
            return selected_work_units

        # Find positions with no selected work units
        selected_position_ids = {
            wu.position_id for wu in selected_work_units if wu.position_id
        }

        result = list(selected_work_units)

        for position in positions:
            if position.id not in selected_position_ids:
                # Find highest-scoring work unit for this position
                position_wus = [
                    wu for wu in all_work_units if wu.position_id == position.id
                ]
                if position_wus:
                    if scores:
                        best_wu = max(
                            position_wus,
                            key=lambda wu: scores.get(wu.id, 0),
                        )
                    else:
                        best_wu = position_wus[0]
                    result.append(best_wu)

        return result

    def detect_gaps(
        self,
        positions: list[Position],
        selected_work_units: list[WorkUnit],
    ) -> list[EmploymentGap]:
        """Detect employment gaps in the filtered resume.

        Args:
            positions: All positions in timeline.
            selected_work_units: Work units selected for resume.

        Returns:
            List of detected employment gaps >= min_gap_months.
        """
        # Get positions that have work units in the selection
        included_position_ids = {
            wu.position_id for wu in selected_work_units if wu.position_id
        }
        excluded_positions = [
            p for p in positions if p.id not in included_position_ids
        ]

        if not excluded_positions:
            return []

        gaps = []

        for excluded in excluded_positions:
            exc_start = self._parse_date(excluded.start_date)
            exc_end = self._parse_date(excluded.end_date) or date.today()

            gap_months = self._months_between(exc_start, exc_end)

            if gap_months >= self.min_gap_months:
                gaps.append(EmploymentGap(
                    start_date=exc_start,
                    end_date=exc_end,
                    duration_months=gap_months,
                    missing_position_id=excluded.id,
                    missing_employer=excluded.employer,
                ))

        return gaps

    def format_gap_warning(self, gaps: list[EmploymentGap]) -> str:
        """Format gap warnings for Rich console display."""
        if not gaps:
            return ""

        lines = ["[yellow]⚠️  Employment Gap Detected[/yellow]"]
        for gap in gaps:
            lines.append(
                f"    Missing: [bold]{gap.missing_employer}[/bold] "
                f"({gap.start_date.strftime('%Y-%m')} to {gap.end_date.strftime('%Y-%m')})"
            )
            lines.append(f"    Gap: {gap.duration_months} months")
        lines.append("")
        lines.append(
            "    [dim]Suggestion: Use --no-allow-gaps to include 1 bullet per position[/dim]"
        )

        return "\n".join(lines)

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse YYYY-MM date string."""
        if not date_str:
            return None
        year, month = date_str.split("-")
        return date(int(year), int(month), 1)

    def _months_between(self, start: date, end: date) -> int:
        """Calculate months between two dates."""
        return (end.year - start.year) * 12 + (end.month - start.month)
```

**Configuration:**
```python
# models/config.py
from typing import Literal

EmploymentContinuityMode = Literal["minimum_bullet", "allow_gaps"]

class ResumeConfig(BaseModel):
    # ... existing fields ...

    employment_continuity: EmploymentContinuityMode = Field(
        default="minimum_bullet",
        description="minimum_bullet: always include 1 work unit per position; "
        "allow_gaps: pure relevance filtering with gap warnings",
    )
```

**CLI Integration:**
```python
# commands/plan.py and commands/build.py

@click.option(
    "--allow-gaps/--no-allow-gaps",
    default=None,
    help="Allow/prevent employment gaps in resume (overrides config)",
)
def plan(allow_gaps: bool | None, ...):
    # Resolve mode
    if allow_gaps is True:
        mode = "allow_gaps"
    elif allow_gaps is False:
        mode = "minimum_bullet"
    else:
        mode = config.employment_continuity

    service = EmploymentContinuityService(mode=mode)
    ...
```

### Dependencies

- **Depends on:** Story 7.6 (Position reference integrity)
- **Blocked by:** None

### Testing Strategy

```python
# tests/unit/test_employment_continuity.py

class TestEnsureContinuity:
    def test_minimum_bullet_adds_missing_positions(self, positions, work_units):
        """minimum_bullet mode adds work unit for each missing position."""
        service = EmploymentContinuityService(mode="minimum_bullet")
        selected = [work_units[0]]  # Only from first position

        result = service.ensure_continuity(positions, selected, work_units)

        # Should add one from each missing position
        assert len(result) == len(positions)

    def test_allow_gaps_returns_unchanged(self, positions, work_units):
        """allow_gaps mode returns selection unchanged."""
        service = EmploymentContinuityService(mode="allow_gaps")
        selected = [work_units[0]]

        result = service.ensure_continuity(positions, selected, work_units)

        assert result == selected


class TestDetectGaps:
    def test_detects_excluded_position(self, positions, work_units):
        """Detects gap when position is excluded."""
        service = EmploymentContinuityService(min_gap_months=3)
        selected = [wu for wu in work_units if wu.position_id != positions[1].id]

        gaps = service.detect_gaps(positions, selected)

        assert len(gaps) == 1
        assert gaps[0].missing_position_id == positions[1].id

    def test_ignores_short_gaps(self, positions, work_units):
        """Gaps under min_gap_months are not reported."""
        service = EmploymentContinuityService(min_gap_months=6)
        # Position 1 is 3 months long
        selected = [wu for wu in work_units if wu.position_id != positions[1].id]

        gaps = service.detect_gaps(positions, selected)

        assert len(gaps) == 0


# tests/integration/test_plan_command.py

def test_plan_with_allow_gaps_shows_warning(cli_runner, tmp_path):
    """--allow-gaps shows gap warnings."""
    result = runner.invoke(cli, ["plan", "--allow-gaps", "--jd", "job.txt"])
    assert result.exit_code == 0
    assert "Employment Gap Detected" in result.output


def test_plan_no_allow_gaps_ensures_continuity(cli_runner, tmp_path):
    """--no-allow-gaps includes all positions."""
    result = runner.invoke(cli, ["plan", "--no-allow-gaps", "--jd", "job.txt"])
    assert result.exit_code == 0
    assert "Employment Gap Detected" not in result.output
```

### Project Context Rules

From `project-context.md`:
- Run `ruff check` and `mypy --strict` before completing
- Use Rich console for CLI output, never `print()`
- Type hints required on all public functions
- Use `|` union syntax (Python 3.10+)

### References

- [Depends: Story 7.6 - Position Reference Integrity]
- [Source: src/resume_as_code/commands/plan.py]
- [Source: src/resume_as_code/commands/build.py]
- [Source: src/resume_as_code/services/position_service.py]
- [Epic: epic-7-schema-data-model-refactoring.md - Story 7.20]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Implemented `EmploymentContinuityService` with two modes:
   - `minimum_bullet` (default): Guarantees at least one work unit per position
   - `allow_gaps`: Pure relevance filtering with gap detection warnings

2. Added `--allow-gaps/--no-allow-gaps` CLI flags to both `plan` and `build` commands

3. Employment gaps are detected and displayed with warnings showing:
   - Missing employer and position
   - Gap duration in months
   - Suggestion to use `--no-allow-gaps` to force continuity

4. Enhanced `--show-excluded` output to flag work units that would cause gaps

5. JSON output includes `employment_continuity` section with mode and gaps array

6. All quality checks passed:
   - `ruff check src tests` - 0 errors
   - `ruff format src tests` - clean
   - `mypy src --strict` - 0 errors
   - 21 tests pass (14 unit + 7 integration)

### File List

**New Files:**
- `src/resume_as_code/services/employment_continuity.py` - EmploymentContinuityService and EmploymentGap dataclass
- `tests/unit/test_employment_continuity.py` - Unit tests for employment continuity service

**Modified Files:**
- `src/resume_as_code/models/config.py` - Added `EmploymentContinuityMode` type and `employment_continuity` config field
- `src/resume_as_code/commands/plan.py` - Added CLI flag, continuity service integration, gap warnings display
- `src/resume_as_code/commands/build.py` - Added CLI flag, continuity service integration for implicit plans
- `tests/integration/test_plan_command.py` - Added `TestPlanCommandEmploymentContinuity` test class with 7 tests
- `CLAUDE.md` - Added documentation for new CLI options

## Senior Developer Review (AI)

**Reviewer:** Claude Opus 4.5 (Amelia - Dev Agent)
**Date:** 2026-01-17
**Outcome:** APPROVED

### Review Summary

All 7 Acceptance Criteria verified against implementation. All 6 tasks with 23 subtasks confirmed complete.

### Issues Found & Remediated

| Severity | Issue | Resolution |
|----------|-------|------------|
| MEDIUM | Dead code in `plan.py:351` - orphan set comprehension `{wu.id for wu in enhanced_wus}` | Removed dead line |
| LOW | Comment clarity on gap detection logic | Improved comment to clarify minimum_bullet vs allow_gaps behavior |

### Verification

- `ruff check`: All checks passed
- `mypy --strict`: No issues found
- Unit tests: 14 passed
- Integration tests: 7 passed
- Total: 21 tests passing

### Files Reviewed

- `src/resume_as_code/services/employment_continuity.py` - Clean implementation
- `src/resume_as_code/models/config.py` - Proper type definition
- `src/resume_as_code/commands/plan.py` - Fixed dead code, good integration
- `src/resume_as_code/commands/build.py` - Correct flag handling
- `tests/unit/test_employment_continuity.py` - Comprehensive coverage
- `tests/integration/test_plan_command.py` - All scenarios tested

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-01-17 | Dev Agent | Initial implementation complete |
| 2026-01-17 | Code Review | Fixed dead code in plan.py:351, improved comment clarity |
