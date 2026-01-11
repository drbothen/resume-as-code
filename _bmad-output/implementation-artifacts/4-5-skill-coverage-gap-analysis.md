# Story 4.5: Skill Coverage & Gap Analysis

Status: ready-for-dev

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

- [ ] Task 1: Create coverage analysis service (AC: #1, #2, #3, #4)
  - [ ] 1.1: Create `src/resume_as_code/services/coverage_analyzer.py`
  - [ ] 1.2: Implement skill matching against Work Units
  - [ ] 1.3: Categorize matches as strong (✓), weak (△), or gap (✗)
  - [ ] 1.4: Return coverage matrix with Work Unit references

- [ ] Task 2: Integrate into plan command (AC: #1)
  - [ ] 2.1: Call coverage analyzer after ranking
  - [ ] 2.2: Display COVERAGE section in Rich output
  - [ ] 2.3: Add to JSON output

- [ ] Task 3: Rich output for coverage (AC: #1, #2, #3, #4)
  - [ ] 3.1: Use color-coded symbols (green ✓, yellow △, red ✗)
  - [ ] 3.2: Show matching Work Unit IDs for covered skills
  - [ ] 3.3: Display coverage summary percentage

- [ ] Task 4: Code quality verification
  - [ ] 4.1: Run `ruff check src tests --fix`
  - [ ] 4.2: Run `mypy src --strict` with zero errors
  - [ ] 4.3: Add tests for coverage analysis

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

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

