# Story 4.4: Exclusion Reasoning

Status: ready-for-dev

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

- [ ] Task 1: Extend plan command for exclusions (AC: #1, #4)
  - [ ] 1.1: Update `commands/plan.py` with exclusion display
  - [ ] 1.2: Add `--show-excluded` flag
  - [ ] 1.3: Default to showing top 5 excluded Work Units
  - [ ] 1.4: Option to show all excluded with `--show-all-excluded`

- [ ] Task 2: Implement exclusion reason generation (AC: #2, #3)
  - [ ] 2.1: Create `ExclusionReason` enum/model
  - [ ] 2.2: Generate "Low relevance" reason for scores < 20%
  - [ ] 2.3: Generate "Below threshold" reason for others
  - [ ] 2.4: Include score in reason text

- [ ] Task 3: Rich output for exclusions (AC: #1, #5)
  - [ ] 3.1: Display excluded section with muted styling
  - [ ] 3.2: Show score, title, and reason for each
  - [ ] 3.3: Group by exclusion reason if many items
  - [ ] 3.4: Add suggestions for improving relevance

- [ ] Task 4: JSON output for exclusions (AC: #1)
  - [ ] 4.1: Include excluded Work Units in JSON output
  - [ ] 4.2: Include exclusion reasons in JSON

- [ ] Task 5: Code quality verification
  - [ ] 5.1: Run `ruff check src tests --fix`
  - [ ] 5.2: Run `mypy src --strict` with zero errors
  - [ ] 5.3: Add tests for exclusion reason generation

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
    SKILL_MISMATCH = "skill_mismatch"

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

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

