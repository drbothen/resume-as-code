# Story 4.4: Exclusion Reasoning

Status: done

## Story

As a **user**,
I want **to see which Work Units were excluded and why**,
So that **I trust the system isn't hiding relevant experience**.

## Acceptance Criteria

1. **Given** I run `resume plan --jd file.txt`
   **When** the command executes
   **Then** I see an "EXCLUDED" section after the selected Work Units
   **And** each excluded Work Unit shows: ID, title, and exclusion reason

2. **Given** a Work Unit is excluded due to low relevance
   **When** the exclusion is displayed
   **Then** the reason states "Low relevance score (23%)" or similar

3. **Given** a Work Unit is excluded due to being outside top N
   **When** the exclusion is displayed
   **Then** the reason states "Below selection threshold" with its score shown

4. **Given** I run `resume plan --jd file.txt --show-excluded`
   **When** the command executes
   **Then** the excluded section is shown (it may be hidden by default)

5. **Given** exclusions are displayed
   **When** I review them
   **Then** I can identify Work Units that might need terminology updates
   **And** I understand why the system made its choices

## Tasks / Subtasks

- [x] Task 1: Extend plan command for exclusions (AC: #1, #4)
  - [x] 1.1: Update `commands/plan.py` with exclusion display
  - [x] 1.2: Add `--show-excluded` flag
  - [x] 1.3: Default to showing top 5 excluded Work Units
  - [x] 1.4: Option to show all excluded with `--show-all-excluded`

- [x] Task 2: Implement exclusion reason generation (AC: #2, #3)
  - [x] 2.1: Create `ExclusionReason` enum/model
  - [x] 2.2: Generate "Low relevance" reason for scores < 20%
  - [x] 2.3: Generate "Below threshold" reason for others
  - [x] 2.4: Include score in reason text

- [x] Task 3: Rich output for exclusions (AC: #1, #5)
  - [x] 3.1: Display excluded section with muted styling
  - [x] 3.2: Show score, title, and reason for each
  - [x] 3.3: Group by exclusion reason if many items
  - [x] 3.4: Add suggestions for improving relevance

- [x] Task 4: JSON output for exclusions (AC: #1)
  - [x] 4.1: Include excluded Work Units in JSON output
  - [x] 4.2: Include exclusion reasons in JSON

- [x] Task 5: Code quality verification
  - [x] 5.1: Run `ruff check src tests --fix`
  - [x] 5.2: Run `mypy src --strict` with zero errors
  - [x] 5.3: Add tests for exclusion reason generation

## Dev Notes

### Architecture Compliance

This story builds trust through transparency. Users can see exactly why certain Work Units were not selected.

**Source:** [epics.md#Story 4.4](_bmad-output/planning-artifacts/epics.md)

### Dependencies

This story REQUIRES:
- Story 4.3 (Plan Command) - Base plan functionality

### Exclusion Reason Model

```python
from enum import Enum
from dataclasses import dataclass

class ExclusionType(str, Enum):
    LOW_RELEVANCE = "low_relevance"
    BELOW_THRESHOLD = "below_threshold"

@dataclass
class ExclusionReason:
    type: ExclusionType
    message: str
    suggestion: str | None = None

def get_exclusion_reason(result, threshold_score: float) -> ExclusionReason:
    """Determine why a Work Unit was excluded."""
    if result.score < 0.2:
        return ExclusionReason(
            type=ExclusionType.LOW_RELEVANCE,
            message=f"Low relevance score ({result.score:.0%})",
            suggestion="Consider adding JD keywords to this Work Unit",
        )
    return ExclusionReason(
        type=ExclusionType.BELOW_THRESHOLD,
        message=f"Below selection threshold ({result.score:.0%})",
        suggestion=None,
    )
```

### Enhanced Plan Output

```python
def _display_excluded(excluded: list, show_all: bool = False) -> None:
    """Display excluded Work Units with reasons."""
    to_show = excluded if show_all else excluded[:5]

    console.print("\n[bold dim]✗ EXCLUDED[/bold dim] "
                  f"({len(excluded)} total, showing {len(to_show)})\n")

    for result in to_show:
        reason = get_exclusion_reason(result, threshold_score=0.5)

        console.print(
            f"  [dim]{result.score:.0%}[/dim] "
            f"[dim]{result.work_unit['title']}[/dim]"
        )
        console.print(f"       [dim italic]{reason.message}[/dim italic]")

        if reason.suggestion:
            console.print(f"       [blue]💡 {reason.suggestion}[/blue]")

    if not show_all and len(excluded) > 5:
        console.print(f"\n  [dim]... and {len(excluded) - 5} more. "
                      "Use --show-all-excluded to see all.[/dim]")
```

### Verification Commands

```bash
# Show excluded Work Units
resume plan --jd sample-jd.txt --show-excluded

# Show all excluded
resume plan --jd sample-jd.txt --show-all-excluded

# JSON with exclusions
resume --json plan --jd sample-jd.txt
```

### References

- [Source: epics.md#Story 4.4](_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None required.

### Completion Notes List

- Created `ExclusionReason` model with `ExclusionType` enum (LOW_RELEVANCE, BELOW_THRESHOLD)
- Implemented `get_exclusion_reason()` function to determine exclusion reason based on score
- Added `--show-all-excluded` flag to plan command
- Updated `_display_excluded()` to use new exclusion reasons with muted styling
- Added suggestions for low relevance items ("Consider adding JD keywords")
- Shows "... and X more" when limiting to top 5
- Updated JSON output to include `excluded` array with `exclusion_reason` objects
- Added 8 new integration tests for exclusion functionality
- All tests pass, ruff and mypy clean
- Note: LOW_RELEVANCE_THRESHOLD (0.2) is currently hardcoded; consider making configurable via `.resume.yaml` in future (aligns with FR32)

### File List

- src/resume_as_code/models/exclusion.py (NEW)
- src/resume_as_code/models/__init__.py (MODIFIED)
- src/resume_as_code/commands/plan.py (MODIFIED)
- tests/integration/test_plan_command.py (MODIFIED)
- tests/unit/test_exclusion.py (NEW - added during code review)

## Senior Developer Review (AI)

### Review Date
2026-01-11

### Reviewer
Claude Opus 4.5 (Adversarial Code Review)

### Findings Summary
- **2 HIGH**: Untracked file, missing unit tests
- **3 MEDIUM**: Story/code mismatch, boundary test missing, hardcoded threshold
- **2 LOW**: Weak assertions, missing docstring

### Remediation Applied
All findings were remediated:

1. **H1 Fixed**: Staged `exclusion.py` in git (`git add`)
2. **H2 Fixed**: Created `tests/unit/test_exclusion.py` with 19 unit tests covering:
   - `ExclusionType` enum values and string subclass behavior
   - `ExclusionReason` dataclass creation and `to_dict()` serialization
   - `get_exclusion_reason()` function for all score ranges
   - Boundary testing at threshold (0.2)
3. **M1 Fixed**: Removed `SKILL_MISMATCH` reference from story Dev Notes
4. **M2 Fixed**: Added `test_boundary_at_threshold_returns_below_threshold` unit test
5. **M3 Documented**: Added note about future configurable threshold (FR32)
6. **L1 Fixed**: Strengthened integration test assertions for specific messages
7. **L2 Fixed**: Added comprehensive docstring to `to_dict()` method

### Verification
- All 42 related tests pass (19 unit + 23 integration)
- ruff check: All checks passed
- mypy --strict: No issues found

### Outcome
**APPROVED** - Story marked as done

