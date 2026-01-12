# Story 4.5: Skill Coverage & Gap Analysis

Status: done

## Story

As a **user considering a job**,
I want **to see which JD requirements I cover and where I have gaps**,
So that **I can honestly assess my fit for the role**.

## Acceptance Criteria

1. **Given** I run `resume plan --jd file.txt`
   **When** the command executes
   **Then** I see a "COVERAGE" section showing skills/requirements from the JD
   **And** each requirement shows: covered (✓), weak (△), or gap (✗)

2. **Given** a JD requirement is strongly matched by selected Work Units
   **When** coverage is displayed
   **Then** it shows ✓ with the matching Work Unit IDs

3. **Given** a JD requirement has partial matches
   **When** coverage is displayed
   **Then** it shows △ with "Weak signal" and relevant Work Unit IDs

4. **Given** a JD requirement has no matches in any Work Units
   **When** coverage is displayed
   **Then** it shows ✗ as a gap
   **And** no judgment is implied (just factual reporting)

5. **Given** I run `resume plan --jd file.txt --json`
   **When** the command executes
   **Then** coverage data is included in the JSON output
   **And** gaps are clearly enumerated

## Tasks / Subtasks

- [x] Task 1: Create coverage analysis service (AC: #1, #2, #3, #4)
  - [x] 1.1: Create `src/resume_as_code/services/coverage_analyzer.py`
  - [x] 1.2: Implement skill matching against Work Units
  - [x] 1.3: Categorize matches as strong (✓), weak (△), or gap (✗)
  - [x] 1.4: Return coverage matrix with Work Unit references

- [x] Task 2: Integrate into plan command (AC: #1)
  - [x] 2.1: Call coverage analyzer after ranking
  - [x] 2.2: Display COVERAGE section in Rich output
  - [x] 2.3: Add to JSON output

- [x] Task 3: Rich output for coverage (AC: #1, #2, #3, #4)
  - [x] 3.1: Use color-coded symbols (green ✓, yellow △, red ✗)
  - [x] 3.2: Show matching Work Unit IDs for covered skills
  - [x] 3.3: Display coverage summary percentage

- [x] Task 4: Code quality verification
  - [x] 4.1: Run `ruff check src tests --fix`
  - [x] 4.2: Run `mypy src --strict` with zero errors
  - [x] 4.3: Add tests for coverage analysis

## Dev Notes

### Architecture Compliance

This is the "Do I belong in this room?" feature - honest assessment of fit without judgment.

**Source:** [epics.md#Story 4.5](_bmad-output/planning-artifacts/epics.md)

### Dependencies

This story REQUIRES:
- Story 4.1 (Job Description Parser) - JD skills extraction
- Story 4.3 (Plan Command) - Base plan functionality

### Coverage Analyzer Implementation

**`src/resume_as_code/services/coverage_analyzer.py`:**

```python
"""Skill coverage and gap analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CoverageLevel(str, Enum):
    STRONG = "strong"  # ✓
    WEAK = "weak"      # △
    GAP = "gap"        # ✗


@dataclass
class SkillCoverage:
    """Coverage status for a single skill."""

    skill: str
    level: CoverageLevel
    matching_work_units: list[str]  # Work Unit IDs

    @property
    def symbol(self) -> str:
        return {
            CoverageLevel.STRONG: "✓",
            CoverageLevel.WEAK: "△",
            CoverageLevel.GAP: "✗",
        }[self.level]

    @property
    def color(self) -> str:
        return {
            CoverageLevel.STRONG: "green",
            CoverageLevel.WEAK: "yellow",
            CoverageLevel.GAP: "red",
        }[self.level]


@dataclass
class CoverageReport:
    """Complete coverage analysis."""

    items: list[SkillCoverage]

    @property
    def strong_count(self) -> int:
        return sum(1 for i in self.items if i.level == CoverageLevel.STRONG)

    @property
    def weak_count(self) -> int:
        return sum(1 for i in self.items if i.level == CoverageLevel.WEAK)

    @property
    def gap_count(self) -> int:
        return sum(1 for i in self.items if i.level == CoverageLevel.GAP)

    @property
    def coverage_percentage(self) -> float:
        if not self.items:
            return 100.0
        covered = self.strong_count + (self.weak_count * 0.5)
        return (covered / len(self.items)) * 100


def analyze_coverage(
    jd_skills: list[str],
    selected_work_units: list[dict],
) -> CoverageReport:
    """Analyze skill coverage against JD requirements.

    Args:
        jd_skills: Skills extracted from job description.
        selected_work_units: Work Units selected for the resume.

    Returns:
        CoverageReport with coverage status for each skill.
    """
    items: list[SkillCoverage] = []

    for skill in jd_skills:
        skill_lower = skill.lower()
        matching_wus: list[str] = []
        match_strength = 0

        for wu in selected_work_units:
            wu_text = _get_wu_text(wu).lower()
            wu_tags = [t.lower() for t in wu.get("tags", [])]
            wu_skills = [s.lower() for s in wu.get("skills_demonstrated", [])]

            # Strong match: in tags or skills
            if skill_lower in wu_tags or skill_lower in wu_skills:
                matching_wus.append(wu.get("id", "unknown"))
                match_strength = max(match_strength, 2)

            # Weak match: mentioned in text
            elif skill_lower in wu_text:
                matching_wus.append(wu.get("id", "unknown"))
                match_strength = max(match_strength, 1)

        # Determine coverage level
        if match_strength >= 2:
            level = CoverageLevel.STRONG
        elif match_strength >= 1:
            level = CoverageLevel.WEAK
        else:
            level = CoverageLevel.GAP

        items.append(SkillCoverage(
            skill=skill,
            level=level,
            matching_work_units=matching_wus,
        ))

    return CoverageReport(items=items)


def _get_wu_text(wu: dict) -> str:
    """Extract all text from a Work Unit."""
    parts = [
        wu.get("title", ""),
        wu.get("problem", {}).get("statement", ""),
        " ".join(wu.get("actions", [])),
        wu.get("outcome", {}).get("result", ""),
    ]
    return " ".join(filter(None, parts))
```

### Rich Output for Coverage

```python
def _display_coverage(report: CoverageReport) -> None:
    """Display coverage analysis with Rich."""
    console.print(Panel(
        f"Coverage: {report.coverage_percentage:.0f}%\n"
        f"Strong: {report.strong_count} | Weak: {report.weak_count} | Gaps: {report.gap_count}",
        title="🎯 Skill Coverage",
        border_style="magenta",
    ))

    # Show each skill
    for item in report.items:
        wu_info = f" ({', '.join(item.matching_work_units[:2])})" if item.matching_work_units else ""
        console.print(
            f"  [{item.color}]{item.symbol}[/{item.color}] {item.skill}{wu_info}"
        )
```

### Verification Commands

```bash
# Run plan with coverage
resume plan --jd sample-jd.txt

# JSON output includes coverage
resume --json plan --jd sample-jd.txt | jq '.data.coverage'
```

### References

- [Source: epics.md#Story 4.5](_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Created `coverage_analyzer.py` service with `CoverageLevel` enum, `SkillCoverage` and `CoverageReport` dataclasses
- Implemented `analyze_coverage()` function that:
  - Matches JD skills against Work Unit tags and skills_demonstrated (strong match)
  - Matches against Work Unit text content (weak match)
  - Returns gap status for unmatched skills
  - Case-insensitive matching
- Integrated coverage analysis into `plan.py` command:
  - Called after ranking, using selected Work Units only
  - Added `_display_coverage()` function for Rich output with color-coded symbols
  - Added coverage data to JSON output via `to_dict()` serialization
- Added 20 unit tests in `test_coverage_analyzer.py` covering all data classes and functions
- Added 5 integration tests in `test_plan_command.py` for coverage display and JSON output
- All 736 tests pass
- ruff check and mypy --strict pass with zero errors

### File List

- src/resume_as_code/services/coverage_analyzer.py (created)
- src/resume_as_code/commands/plan.py (modified)
- tests/unit/test_coverage_analyzer.py (created)
- tests/integration/test_plan_command.py (modified)

## Senior Developer Review (AI)

**Reviewer:** Claude Opus 4.5 (Adversarial Code Review)
**Date:** 2026-01-11
**Outcome:** APPROVED with fixes applied

### Issues Found & Remediated

| # | Severity | Issue | Resolution |
|---|----------|-------|------------|
| 1 | MEDIUM | New files not staged in git | Staged `coverage_analyzer.py` and `test_coverage_analyzer.py` |
| 2 | MEDIUM | Code duplication (`_extract_wu_text` in 3 files) | Created shared `utils/work_unit_text.py`, refactored all usages |
| 3 | LOW | Missing test for dict-format skills_demonstrated | Added `test_dict_format_skills_demonstrated` test |
| 4 | LOW | Module not exported in services `__init__.py` | Added exports for `CoverageLevel`, `CoverageReport`, `SkillCoverage`, `analyze_coverage` |
| 5 | LOW | AC3 "Weak signal" text not shown | Added "Weak signal" indicator for weak coverage matches |

### Files Modified During Review

- src/resume_as_code/utils/work_unit_text.py (created - shared utility)
- src/resume_as_code/utils/__init__.py (modified - exports)
- src/resume_as_code/services/__init__.py (modified - exports)
- src/resume_as_code/services/coverage_analyzer.py (modified - use shared utility)
- src/resume_as_code/services/ranker.py (modified - use shared utility)
- src/resume_as_code/commands/plan.py (modified - use shared utility, add "Weak signal")
- tests/unit/test_coverage_analyzer.py (modified - add dict-format test)

### Verification

- All 737 tests pass (added 1 new test)
- ruff check passes
- mypy --strict passes

## Change Log

- 2026-01-11: Implemented skill coverage & gap analysis feature (Story 4.5)
- 2026-01-11: Code review: Fixed 5 issues, refactored duplicate code, added missing test

