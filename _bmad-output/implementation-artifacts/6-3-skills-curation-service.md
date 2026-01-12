# Story 6.3: Skills Curation Service

Status: done

## Story

As a **user**,
I want **my skills section to show relevant, deduplicated skills**,
So that **recruiters see a focused list instead of a skill dump**.

## Acceptance Criteria

1. **Given** work units contain skills: ["AWS", "aws", "Python", "python", "Terraform"]
   **When** skills are extracted for the resume
   **Then** duplicates are removed (case-insensitive): ["AWS", "Python", "Terraform"]

2. **Given** skills from work units and tags combined exceed 50 items
   **When** skills are curated
   **Then** maximum 15 skills appear on the resume
   **And** skills matching JD keywords are prioritized

3. **Given** a JD mentions "Kubernetes" 3 times and "Python" 2 times
   **When** skills are curated
   **Then** Kubernetes and Python rank higher than skills not in JD
   **And** skills are ordered by JD relevance, not alphabetically

4. **Given** I configure `skills.exclude: ["PHP", "jQuery"]` in config
   **When** skills are curated
   **Then** excluded skills never appear regardless of work unit content

5. **Given** I configure `skills.max_display: 12` in config
   **When** skills are curated
   **Then** only top 12 skills are shown

6. **Given** skills are curated
   **When** I run `resume plan --jd file.txt`
   **Then** the skill coverage section shows which skills will be included
   **And** shows which were excluded due to dedup or low relevance

## Tasks / Subtasks

- [x] Task 1: Create SkillsConfig model (AC: #4, #5)
  - [x] 1.1: Create `SkillsConfig` Pydantic model in `models/config.py`
  - [x] 1.2: Add fields: max_display, exclude, prioritize
  - [x] 1.3: Add `skills: SkillsConfig` field to `ResumeConfig`
  - [x] 1.4: Set sensible defaults (max_display=15)

- [x] Task 2: Create SkillCurator service (AC: #1, #2, #3)
  - [x] 2.1: Create `services/skill_curator.py`
  - [x] 2.2: Implement case-insensitive deduplication
  - [x] 2.3: Implement JD keyword scoring
  - [x] 2.4: Implement skill ranking by relevance
  - [x] 2.5: Implement max_count limiting
  - [x] 2.6: Return both included and excluded skills with reasons

- [x] Task 3: Integrate with ResumeData (AC: #1, #2)
  - [x] 3.1: Update `ResumeData.from_work_units()` to use SkillCurator
  - [x] 3.2: Extract skills from all work unit fields (skills, tags)
  - [x] 3.3: Pass JD keywords when available
  - [x] 3.4: Store curated skills in ResumeData

- [x] Task 4: Update plan command (AC: #6)
  - [x] 4.1: Add skills curation info to plan output
  - [x] 4.2: Show included skills with JD match indicator
  - [x] 4.3: Show excluded skills with exclusion reason
  - [x] 4.4: Display in skill coverage section

- [x] Task 5: Update build command (AC: #1, #2, #3, #4, #5)
  - [x] 5.1: Load SkillsConfig from config
  - [x] 5.2: Pass exclude list and max_display to curator
  - [x] 5.3: Pass JD keywords to curator when --jd provided

- [x] Task 6: Testing
  - [x] 6.1: Add unit tests for SkillCurator deduplication
  - [x] 6.2: Add unit tests for JD keyword scoring
  - [x] 6.3: Add unit tests for skill ranking
  - [x] 6.4: Add unit tests for exclude list filtering
  - [x] 6.5: Add unit tests for max_display limiting
  - [x] 6.6: Add integration tests for plan output

- [x] Task 7: Code quality verification
  - [x] 7.1: Run `ruff check src tests --fix`
  - [x] 7.2: Run `mypy src --strict` with zero errors
  - [x] 7.3: Run `pytest` - all tests pass

## Dev Notes

### Architecture Compliance

This story implements FR41 (curated, deduplicated skills) per the PRD. The SkillCurator service follows the "commands thin, services thick" pattern from project-context.md.

**Critical Rules from project-context.md:**
- Use `|` union syntax for optional fields (Python 3.10+)
- Services do the heavy lifting, commands orchestrate
- Never use `print()` - use Rich console
- Return structured data for JSON mode support

### SkillsConfig Model

```python
# In models/config.py

class SkillsConfig(BaseModel):
    """Configuration for skills curation."""

    max_display: int = Field(default=15, ge=1, le=50)
    exclude: list[str] = Field(default_factory=list)
    prioritize: list[str] = Field(default_factory=list)  # Always include these first
```

### SkillCurator Service Design

```python
# src/resume_as_code/services/skill_curator.py

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Set


@dataclass
class CurationResult:
    """Result of skill curation."""

    included: list[str]  # Skills to display, ordered by relevance
    excluded: list[tuple[str, str]]  # (skill, reason) pairs
    stats: dict[str, int]  # Curation statistics


class SkillCurator:
    """Curates skills for resume display.

    Handles deduplication, JD-based ranking, exclusions, and limiting.
    """

    def __init__(
        self,
        max_count: int = 15,
        exclude: list[str] | None = None,
        prioritize: list[str] | None = None,
    ) -> None:
        self.max_count = max_count
        self.exclude = {s.lower() for s in (exclude or [])}
        self.prioritize = {s.lower() for s in (prioritize or [])}

    def curate(
        self,
        raw_skills: set[str],
        jd_keywords: set[str] | None = None,
    ) -> CurationResult:
        """Curate skills for resume display.

        Args:
            raw_skills: All skills extracted from work units.
            jd_keywords: Keywords from job description (optional).

        Returns:
            CurationResult with included/excluded skills and reasons.
        """
        jd_keywords = jd_keywords or set()
        jd_lower = {k.lower() for k in jd_keywords}

        # Step 1: Normalize and deduplicate (case-insensitive)
        normalized = self._deduplicate(raw_skills)

        # Step 2: Remove excluded skills
        filtered, excluded_by_config = self._filter_excluded(normalized)

        # Step 3: Score by JD relevance
        scored = self._score_skills(filtered, jd_lower)

        # Step 4: Sort by score (prioritized first, then JD matches, then others)
        sorted_skills = self._sort_by_relevance(scored)

        # Step 5: Limit to max_count
        included = sorted_skills[: self.max_count]
        excluded_by_limit = [
            (s, "exceeded_max_display") for s in sorted_skills[self.max_count :]
        ]

        # Combine exclusions
        all_excluded = excluded_by_config + excluded_by_limit

        return CurationResult(
            included=included,
            excluded=all_excluded,
            stats={
                "total_raw": len(raw_skills),
                "after_dedup": len(normalized),
                "after_filter": len(filtered),
                "included": len(included),
                "excluded": len(all_excluded),
            },
        )

    def _deduplicate(self, skills: set[str]) -> dict[str, str]:
        """Deduplicate skills case-insensitively, keeping best casing.

        Returns dict mapping lowercase -> display form.
        Prefers: Title Case > UPPERCASE > lowercase
        """
        normalized: dict[str, str] = {}
        for skill in skills:
            lower = skill.lower()
            if lower not in normalized:
                normalized[lower] = skill
            else:
                # Prefer title case or existing if better
                existing = normalized[lower]
                if skill.istitle() and not existing.istitle():
                    normalized[lower] = skill
                elif skill.isupper() and existing.islower():
                    normalized[lower] = skill
        return normalized

    def _filter_excluded(
        self, normalized: dict[str, str]
    ) -> tuple[dict[str, str], list[tuple[str, str]]]:
        """Remove excluded skills."""
        filtered = {}
        excluded = []
        for lower, display in normalized.items():
            if lower in self.exclude:
                excluded.append((display, "config_exclude"))
            else:
                filtered[lower] = display
        return filtered, excluded

    def _score_skills(
        self, skills: dict[str, str], jd_keywords: set[str]
    ) -> dict[str, tuple[str, int]]:
        """Score skills by JD relevance.

        Returns dict mapping lowercase -> (display, score).
        Score: 100 for prioritized, 10 for JD match, 1 for others.
        """
        scored = {}
        for lower, display in skills.items():
            if lower in self.prioritize:
                score = 100
            elif lower in jd_keywords:
                score = 10
            else:
                score = 1
            scored[lower] = (display, score)
        return scored

    def _sort_by_relevance(self, scored: dict[str, tuple[str, int]]) -> list[str]:
        """Sort skills by score descending, then alphabetically."""
        sorted_items = sorted(
            scored.items(),
            key=lambda x: (-x[1][1], x[1][0].lower()),  # -score, then alpha
        )
        return [display for _, (display, _) in sorted_items]
```

### Integration with ResumeData

```python
# In models/resume.py or commands/build.py

def _extract_skills_from_work_units(work_units: list[WorkUnit]) -> set[str]:
    """Extract all skills from work units."""
    skills: set[str] = set()
    for wu in work_units:
        if wu.skills:
            skills.update(wu.skills)
        if wu.tags:
            skills.update(wu.tags)
    return skills


def _curate_skills(
    work_units: list[WorkUnit],
    config: ResumeConfig,
    jd_keywords: set[str] | None = None,
) -> list[str]:
    """Curate skills for resume."""
    raw_skills = _extract_skills_from_work_units(work_units)

    curator = SkillCurator(
        max_count=config.skills.max_display,
        exclude=config.skills.exclude,
        prioritize=config.skills.prioritize,
    )

    result = curator.curate(raw_skills, jd_keywords)
    return result.included
```

### Plan Command Output Enhancement

```python
# In commands/plan.py - add to plan output

def _display_skills_coverage(
    curation_result: CurationResult,
    jd_keywords: set[str],
) -> None:
    """Display skills curation in plan output."""
    console.print("\n[bold]Skills Curation:[/]")

    # Included skills
    table = Table(show_header=True)
    table.add_column("Skill", style="green")
    table.add_column("JD Match", style="cyan")

    jd_lower = {k.lower() for k in jd_keywords}
    for skill in curation_result.included:
        match = "✓" if skill.lower() in jd_lower else ""
        table.add_row(skill, match)

    console.print(table)

    # Stats
    stats = curation_result.stats
    console.print(
        f"\n[dim]Curated {stats['included']} from {stats['total_raw']} total skills[/]"
    )

    # Excluded (if any significant)
    if curation_result.excluded:
        console.print(f"[dim]Excluded: {len(curation_result.excluded)} skills[/]")
```

### Example .resume.yaml with Skills Config

```yaml
# Skills curation settings
skills:
  max_display: 15
  exclude:
    - "PHP"
    - "jQuery"
    - "Visual Basic"
  prioritize:
    - "Python"
    - "Kubernetes"
    - "AWS"
```

### Dependencies

This story REQUIRES:
- Story 4.1 (JD Parser) - Extracts keywords from JD [DONE]
- Story 6.1 (Profile Configuration) - Config pattern [DONE in Epic 6]

This story ENABLES:
- Story 6.4 (Executive Template) - Uses curated skills
- Improved ATS keyword optimization

### Files to Create/Modify

**New Files:**
- `src/resume_as_code/services/skill_curator.py` - SkillCurator service
- `tests/unit/test_skill_curator.py` - Unit tests

**Modified Files:**
- `src/resume_as_code/models/config.py` - Add SkillsConfig
- `src/resume_as_code/models/resume.py` - Use curated skills in ResumeData
- `src/resume_as_code/commands/build.py` - Integrate skill curation
- `src/resume_as_code/commands/plan.py` - Add skills coverage to output

### Testing Strategy

```python
# tests/unit/test_skill_curator.py

import pytest

from resume_as_code.services.skill_curator import SkillCurator, CurationResult


class TestSkillCurator:
    """Tests for SkillCurator service."""

    def test_deduplication_case_insensitive(self):
        """Should deduplicate skills case-insensitively."""
        curator = SkillCurator()
        result = curator.curate({"AWS", "aws", "Aws"})

        assert len(result.included) == 1
        assert result.included[0] in ["AWS", "aws", "Aws"]

    def test_prefers_title_case(self):
        """Should prefer title case when deduplicating."""
        curator = SkillCurator()
        result = curator.curate({"PYTHON", "python", "Python"})

        assert result.included[0] == "Python"

    def test_jd_keyword_prioritization(self):
        """Should prioritize JD-matching skills."""
        curator = SkillCurator(max_count=3)
        result = curator.curate(
            {"Python", "Java", "Ruby", "Go"},
            jd_keywords={"python", "go"},
        )

        # Python and Go should be first (JD matches)
        assert "Python" in result.included[:2]
        assert "Go" in result.included[:2]

    def test_max_display_limit(self):
        """Should limit to max_count skills."""
        curator = SkillCurator(max_count=3)
        result = curator.curate({"A", "B", "C", "D", "E"})

        assert len(result.included) == 3
        assert len(result.excluded) == 2

    def test_exclude_list(self):
        """Should exclude configured skills."""
        curator = SkillCurator(exclude=["PHP", "jQuery"])
        result = curator.curate({"Python", "PHP", "JavaScript", "jQuery"})

        assert "PHP" not in result.included
        assert "jQuery" not in result.included
        assert len([e for e in result.excluded if e[1] == "config_exclude"]) == 2

    def test_prioritize_list(self):
        """Should put prioritized skills first."""
        curator = SkillCurator(prioritize=["Kubernetes"])
        result = curator.curate({"Python", "Java", "Kubernetes", "Docker"})

        assert result.included[0] == "Kubernetes"

    def test_stats_tracking(self):
        """Should track curation statistics."""
        curator = SkillCurator(max_count=2, exclude=["PHP"])
        result = curator.curate({"Python", "python", "PHP", "Java", "Go"})

        assert result.stats["total_raw"] == 5
        assert result.stats["after_dedup"] == 4  # Python deduped
        assert result.stats["after_filter"] == 3  # PHP excluded
        assert result.stats["included"] == 2  # max_count
```

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_skill_curator.py -v

# Manual verification:
uv run resume plan --jd examples/job-description.txt
# Check Skills Curation section in output
# Verify JD-matching skills are prioritized
```

### References

- [Source: epics.md#Story 6.3](_bmad-output/planning-artifacts/epics.md)
- [Architecture: ATS Keyword Optimization](_bmad-output/planning-artifacts/architecture.md#1.4)
- [Related: Story 4.1 JD Parser](_bmad-output/implementation-artifacts/4-1-job-description-parser.md)

## Dev Agent Record

### Agent Model Used

claude-opus-4-5-20251101

### Debug Log References

None

### Completion Notes List

- All 7 tasks completed successfully following TDD (Red-Green-Refactor) methodology
- Created SkillsConfig Pydantic model with max_display, exclude, and prioritize fields
- Created SkillCurator service with case-insensitive deduplication, JD-based ranking, exclude filtering, and max_count limiting
- Integrated skill curation into ResumeData.from_work_units() method
- Added Skills Curation section to plan command output (both Rich and JSON)
- Updated build command to pass skills_config and jd_keywords to ResumeData
- All 1033 tests pass, mypy strict mode passes, ruff linting passes

### File List

**New Files:**
- `src/resume_as_code/services/skill_curator.py` - SkillCurator service with CurationResult dataclass
- `tests/unit/test_skill_curator.py` - 20 unit tests for SkillCurator

**Modified Files:**
- `src/resume_as_code/models/config.py` - Added SkillsConfig model and skills field to ResumeConfig
- `src/resume_as_code/models/resume.py` - Updated from_work_units() to accept skills_config and jd_keywords
- `src/resume_as_code/commands/plan.py` - Added skills curation display and JSON output
- `src/resume_as_code/commands/build.py` - Pass skills_config and jd_keywords to ResumeData
- `tests/unit/test_config_models.py` - Added 11 tests for SkillsConfig
- `tests/unit/test_resume_model.py` - Added 6 tests for skills curation integration
- `tests/unit/test_build_command.py` - Updated test to reflect deduplication behavior
- `tests/integration/test_plan_command.py` - Added 4 tests for skills curation in plan output

## Code Review Record

### Review Date
2026-01-12

### Issues Found and Remediated

| # | Severity | Issue | Resolution |
|---|----------|-------|------------|
| 1 | Medium | Type annotation uses `Any` instead of `ResumeConfig` in `_curate_skills_from_work_units()` | Added `TYPE_CHECKING` import and proper `ResumeConfig` type annotation |
| 2 | Low | Empty strings could be added to skills set when extracting from work units | Added filtering for empty/whitespace strings in skill extraction loop |
| 3 | Low | Missing test coverage for empty/whitespace skill handling | Added `TestSkillCuratorEmptyStrings` class with 3 tests |
| 4 | N/A | False positive - identified as non-issue during review | No change needed |
| 5 | Low | Redundant JD keyword lowercasing (done in curator and again in display) | Refactored to lowercase once at call site and pass through |
| 6 | Low | Missing edge case tests for `_get_jd_keywords_from_plan()` exception handling | Added `TestGetJDKeywordsFromPlan` class with 4 tests |

### Files Modified During Remediation

- `src/resume_as_code/commands/plan.py` - TYPE_CHECKING import, ResumeConfig type, empty string filtering, JD keyword refactor
- `src/resume_as_code/services/skill_curator.py` - Empty/whitespace string filtering in `_deduplicate()`
- `tests/unit/test_skill_curator.py` - Added `TestSkillCuratorEmptyStrings` class (3 tests)
- `tests/unit/test_build_command.py` - Added `TestGetJDKeywordsFromPlan` class (4 tests)

### Verification

- All 1040 tests pass
- `ruff check` passes
- `mypy --strict` passes
