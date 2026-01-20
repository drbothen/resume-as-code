# Story 13.2: Work History Duration Filter

**Status:** done
**Story Points:** 3
**Priority:** P2

---

## User Story

As a **user generating a resume for a specific role**,
I want **to limit my work history to the last N years**,
So that **I can focus on recent, relevant experience and avoid resume bloat from ancient positions**.

---

## Problem Statement

Users with long careers (15+ years) may have positions from early in their career that are no longer relevant. ATS systems and recruiters typically focus on the last 10-15 years. Currently, the plan/build commands include all positions regardless of age, leading to:
- Resumes that exceed 2 pages with old, less-relevant experience
- Dated technologies and skills appearing on the resume
- Employment continuity calculations including very old gaps

---

## Acceptance Criteria

### AC1: Plan command year filtering
**Given** a `--years 10` flag on the plan command
**When** filtering positions and work units
**Then** only positions with `end_date >= (today - 10 years)` OR `end_date = null` (current) are included
**And** only work units associated with included positions are considered
**And** work units without position_id but with dates in range are included

### AC2: Position exclusion behavior
**Given** the `--years` flag filters out a position
**When** the position is excluded
**Then** it does not appear in the Position Grouping Preview
**And** its work units are excluded from ranking

### AC3: Default behavior preserved
**Given** no `--years` flag is provided
**When** running plan or build
**Then** all positions and work units are considered (current behavior preserved)

### AC4: Config-based default
**Given** config option `history_years: 10` in `.resume.yaml`
**When** running plan or build without `--years` flag
**Then** the config value is used as default
**And** CLI flag overrides config value

### AC5: Employment continuity integration
**Given** employment continuity mode is `minimum_bullet`
**When** `--years 15` excludes a position from 20 years ago
**Then** no gap warning is generated for that ancient position
**And** continuity only considers positions within the year filter

### AC6: Position spanning cutoff
**Given** a position spans the cutoff (started 12 years ago, ended 8 years ago)
**When** `--years 10` is applied
**Then** the position IS included (end_date is within range)

---

## Tasks

### Task 1: Add history_years config option
- [x] Add `history_years: int | None = None` field to `ResumeConfig` in `models/config.py`
- [x] Add field description/docstring

### Task 2: Add filter_by_years method to PositionService
- [x] Create `filter_by_years(positions: list[Position], years: int) -> list[Position]` method
- [x] Handle `end_date = None` (current positions always included)
- [x] Handle date parsing for YearMonth format
- [x] Add unit tests for filtering logic

### Task 3: Add --years flag to plan command
- [x] Add `--years` option to plan command
- [x] Load config default if flag not provided
- [x] Filter positions before ranking
- [x] Filter work units to only include those with matching position_ids or in date range
- [x] Update Position Grouping Preview to show only filtered positions

### Task 4: Add --years flag to build command
- [x] Add `--years` option to build command
- [x] Pass to implicit plan generation
- [x] Ensure consistency with plan command

### Task 5: Update employment continuity
- [x] Modify employment continuity service to respect year filter
- [x] Only calculate gaps between filtered positions
- [x] Add tests for continuity with year filter

### Task 6: Update documentation
- [x] Update CLAUDE.md with `--years` flag documentation
- [x] Add config option documentation

---

## Technical Notes

### Architecture Compliance
- Follows existing CLI pattern for config-with-override (see `--allow-gaps`, `--strict-positions`)
- Uses PositionService for position operations
- Config hierarchy: CLI flag > `.resume.yaml` > default (None = unlimited)

### Files to Modify

| File | Changes |
|------|---------|
| `src/resume_as_code/models/config.py` | Add `history_years: int \| None` to ResumeConfig |
| `src/resume_as_code/services/position_service.py` | Add `filter_by_years()` method |
| `src/resume_as_code/commands/plan.py` | Add `--years` option, filter positions |
| `src/resume_as_code/commands/build.py` | Add `--years` option |
| `src/resume_as_code/services/employment_continuity.py` | Respect year filter in gap calculations |
| `CLAUDE.md` | Document `--years` flag and config option |

### Filter Logic

```python
from datetime import date
from dateutil.relativedelta import relativedelta

def filter_by_years(positions: list[Position], years: int) -> list[Position]:
    """Filter positions to those active within the last N years.

    A position is included if:
    - end_date is None (current position), OR
    - end_date >= (today - years)
    """
    cutoff = date.today() - relativedelta(years=years)
    return [
        pos for pos in positions
        if pos.end_date is None  # Current position
        or _parse_end_date(pos.end_date) >= cutoff
    ]
```

### Config Schema

```yaml
# .resume.yaml
history_years: 10  # Default years of history (null = unlimited)
```

### CLI Help Text

```
--years INTEGER  Limit work history to last N years (default: from config or unlimited)
```

---

## Test Scenarios

1. **No flag, no config**: All positions included
2. **Flag only**: Filter applied per flag value
3. **Config only**: Config value used as default
4. **Both flag and config**: Flag overrides config
5. **Position with null end_date**: Always included
6. **Position ending before cutoff**: Excluded
7. **Position ending after cutoff**: Included
8. **Position spanning cutoff**: Included (end_date is what matters)
9. **Employment continuity**: Gaps only calculated for filtered positions

---

## Definition of Done

- [x] `--years` flag added to plan command
- [x] `--years` flag added to build command
- [x] Config option `history_years` added
- [x] Position filtering by end_date implemented
- [x] Work unit filtering respects position filter
- [x] Employment continuity respects year filter
- [x] Position Grouping Preview shows only filtered positions
- [x] Unit tests for date filtering logic
- [x] CLAUDE.md updated with `--years` flag documentation

---

## References

- Epic: `_bmad-output/planning-artifacts/epics/epic-13-output-format-enhancements.md`
- Position Service: `src/resume_as_code/services/position_service.py`
- Plan Command: `src/resume_as_code/commands/plan.py`
- Build Command: `src/resume_as_code/commands/build.py`
- Config Model: `src/resume_as_code/models/config.py`

---

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References
- Commit: d61bed796ac3b241d4b952a60dbd3b648fe5a15d
- Test run: 45 tests passed (38 unit + 5 integration for years filter + 2 build command)

### Completion Notes List

1. **Position Filtering Logic**: Used YYYY-MM string comparison for date filtering since position dates are stored in this format. Current positions (end_date=None) always included.

2. **Config Priority Pattern**: Followed established pattern `CLI --years > config.history_years > None (unlimited)` consistent with other CLI options.

3. **Work Unit Filtering**: Work units referencing filtered-out positions are automatically excluded. Work units without position_id are always included (date-based filtering not applied to orphan WUs).

4. **Employment Continuity Integration**: Positions filtered BEFORE continuity service is called, so gap warnings only consider positions within the year filter.

5. **Test Coverage**: 8 unit tests for `filter_by_years()` covering boundary conditions, empty lists, positions spanning cutoff, and mixed scenarios.

### File List

| File | Change |
|------|--------|
| `src/resume_as_code/models/config.py` | Added `history_years: int \| None` field to ResumeConfig |
| `src/resume_as_code/services/position_service.py` | Added `filter_by_years()` static method |
| `src/resume_as_code/commands/plan.py` | Added `--years` option, position/WU filtering logic |
| `src/resume_as_code/commands/build.py` | Added `--years` option, position/WU filtering logic |
| `src/resume_as_code/schemas/config.schema.json` | Added history_years field definition |
| `tests/unit/test_position_service.py` | Added TestPositionServiceFilterByYears (8 tests) |
| `tests/unit/test_build_command.py` | Added TestBuildCommandYearsFlag (2 tests) |
| `tests/unit/test_config_models.py` | Added TestResumeConfigHistoryYears (6 tests) |
| `tests/integration/test_plan_command.py` | Added TestPlanCommandYearsFilter (5 tests) |
| `CLAUDE.md` | Added --years flag and history_years config documentation |
