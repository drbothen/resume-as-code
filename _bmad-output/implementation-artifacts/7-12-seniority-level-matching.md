# Story 7.12: Seniority Level Matching

**Epic:** Epic 7 - Schema & Data Model Refactoring
**Story Points:** 5
**Priority:** P3
**Status:** Done

---

## User Story

As a **job seeker**,
I want **my career level matched against the job's seniority requirements**,
So that **I'm not ranked for roles significantly above or below my experience**.

---

## Background

The JD parser already extracts `experience_level` (see `src/resume_as_code/models/job_description.py:10-19`). The `ExperienceLevel` enum includes: ENTRY, MID, SENIOR, STAFF, LEAD, PRINCIPAL, EXECUTIVE.

This story adds the complementary side: inferring or explicitly setting seniority on work units and factoring seniority alignment into the ranking score.

**Research Basis:** LinkedIn and Eightfold use title embeddings and career trajectory to predict seniority fit.

---

## Acceptance Criteria

### AC1: Optional seniority_level field on WorkUnit
**Given** a work unit YAML file
**When** I add `seniority_level: senior`
**Then** it validates successfully
**And** the value is available for matching

### AC2: Seniority inference from position title
**Given** a work unit without `seniority_level` set
**When** ranking runs
**Then** seniority is inferred from the attached position's title
**And** scope indicators (team_size, P&L) boost toward executive levels

### AC3: Title pattern matching
**Given** position title "Senior Platform Engineer"
**When** seniority inference runs
**Then** it returns "senior"

**Given** position title "VP of Engineering"
**When** seniority inference runs
**Then** it returns "executive"

### AC4: Seniority alignment scoring
**Given** JD with `experience_level: SENIOR`
**When** matching work units
**Then** work units with senior-level indicators score higher
**And** work units with executive-level get slight penalty (overqualified)
**And** work units with entry-level get larger penalty (underqualified)

### AC5: Configurable mismatch penalty
**Given** seniority scoring in config
**When** mismatch occurs
**Then** penalty is applied based on configured weights
**And** can be disabled by setting `use_seniority_matching: false`

### AC6: Backward compatibility
**Given** work units without seniority_level field
**When** validation runs
**Then** validation passes (field is optional)
**And** inference provides reasonable defaults

---

## Technical Design

### 1. Reuse Existing ExperienceLevel Enum

Rather than creating a duplicate type, import from job_description.py:

```python
# src/resume_as_code/models/work_unit.py
from resume_as_code.models.job_description import ExperienceLevel

class WorkUnit(BaseModel):
    # ... existing fields ...

    seniority_level: ExperienceLevel | None = Field(
        default=None,
        description="Optional seniority level for explicit matching. If not set, inferred from position title."
    )
```

### 2. Seniority Inference Service

Create new service for title-based seniority inference:

```python
# src/resume_as_code/services/seniority_inference.py
"""Seniority level inference from position titles and scope."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from resume_as_code.models.job_description import ExperienceLevel

if TYPE_CHECKING:
    from resume_as_code.models.position import Position
    from resume_as_code.models.work_unit import WorkUnit


# Title patterns ordered from most senior to least (first match wins)
TITLE_SENIORITY_PATTERNS: list[tuple[ExperienceLevel, list[str]]] = [
    (ExperienceLevel.EXECUTIVE, [
        r"\bcto\b", r"\bceo\b", r"\bcfo\b", r"\bcoo\b", r"\bcio\b", r"\bciso\b",
        r"\bvp\b", r"\bvice president\b", r"\bchief\b", r"\bevp\b",
        r"\bpresident\b", r"\bgeneral manager\b",
    ]),
    (ExperienceLevel.PRINCIPAL, [
        r"\bprincipal\b", r"\bdistinguished\b", r"\bfellow\b",
    ]),
    (ExperienceLevel.STAFF, [
        r"\bstaff\b", r"\barchitect\b",
    ]),
    (ExperienceLevel.LEAD, [
        r"\blead\b", r"\btech lead\b", r"\bteam lead\b", r"\bengineering manager\b",
        r"\bmanager\b", r"\bdirector\b",
    ]),
    (ExperienceLevel.SENIOR, [
        r"\bsenior\b", r"\bsr\.?\b", r"\bsr\s",
    ]),
    (ExperienceLevel.MID, [
        r"\b(?:ii|iii|2|3)\b", r"\bdeveloper\b", r"\bengineer\b", r"\banalyst\b",
    ]),
    (ExperienceLevel.ENTRY, [
        r"\bjunior\b", r"\bjr\.?\b", r"\bjr\s", r"\bassociate\b", r"\bintern\b",
        r"\bentry\b", r"\bgraduate\b",
    ]),
]


def infer_seniority_from_title(title: str) -> ExperienceLevel:
    """Infer seniority level from a job title string.

    Args:
        title: Position or job title to analyze

    Returns:
        Inferred ExperienceLevel, defaults to MID if no patterns match
    """
    title_lower = title.lower()

    for level, patterns in TITLE_SENIORITY_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, title_lower):
                return level

    return ExperienceLevel.MID  # Default for unrecognized titles


def infer_seniority(
    work_unit: WorkUnit,
    position: Position | None = None,
) -> ExperienceLevel:
    """Infer seniority level for a work unit.

    Priority:
    1. Explicit seniority_level on work unit (if set)
    2. Position title analysis
    3. Scope indicators (team size, P&L)
    4. Work unit title analysis
    5. Default to MID

    Args:
        work_unit: The work unit to analyze
        position: Optional attached position for title/scope data

    Returns:
        Inferred or explicit ExperienceLevel
    """
    # Priority 1: Explicit seniority on work unit
    if work_unit.seniority_level is not None:
        return work_unit.seniority_level

    # Priority 2: Position title
    if position and position.title:
        title_level = infer_seniority_from_title(position.title)

        # Priority 3: Scope indicators can boost to executive
        if position.scope:
            scope = position.scope
            # P&L responsibility or significant revenue = executive
            if scope.pl_responsibility or (scope.revenue and _parse_currency(scope.revenue) >= 100_000_000):
                return ExperienceLevel.EXECUTIVE
            # Large team = at least staff
            if scope.team_size and scope.team_size >= 50:
                return max(title_level, ExperienceLevel.STAFF, key=_level_rank)
            # Medium team = at least lead
            if scope.team_size and scope.team_size >= 10:
                return max(title_level, ExperienceLevel.LEAD, key=_level_rank)

        return title_level

    # Priority 4: Work unit title
    return infer_seniority_from_title(work_unit.title)


def _parse_currency(value: str) -> int:
    """Parse currency string to integer value.

    Examples:
        "$500M" -> 500_000_000
        "$2.5B" -> 2_500_000_000
        "$50K" -> 50_000
    """
    if not value:
        return 0

    # Remove $ and commas
    cleaned = re.sub(r'[$,]', '', value.upper())

    # Extract number and suffix
    match = re.match(r'([\d.]+)\s*([KMB])?', cleaned)
    if not match:
        return 0

    number = float(match.group(1))
    suffix = match.group(2)

    multipliers = {'K': 1_000, 'M': 1_000_000, 'B': 1_000_000_000}
    multiplier = multipliers.get(suffix, 1)

    return int(number * multiplier)


def _level_rank(level: ExperienceLevel) -> int:
    """Return numeric rank for level comparison."""
    ranks = {
        ExperienceLevel.ENTRY: 1,
        ExperienceLevel.MID: 2,
        ExperienceLevel.SENIOR: 3,
        ExperienceLevel.LEAD: 4,
        ExperienceLevel.STAFF: 5,
        ExperienceLevel.PRINCIPAL: 6,
        ExperienceLevel.EXECUTIVE: 7,
    }
    return ranks.get(level, 2)


def calculate_seniority_alignment(
    work_unit_level: ExperienceLevel,
    jd_level: ExperienceLevel,
) -> float:
    """Calculate alignment score between work unit and JD seniority.

    Applies asymmetric penalties per AC4:
    - Overqualified (wu > jd): slight penalty (executive applying for senior)
    - Underqualified (wu < jd): larger penalty (entry applying for senior)

    Returns:
        Float between 0.0 and 1.0:
        - 1.0: Perfect match
        - Overqualified: 0.9 (1 level), 0.8 (2), 0.75 (3), 0.7 (4+)
        - Underqualified: 0.8 (1 level), 0.6 (2), 0.4 (3), 0.3 (4+)
    """
    wu_rank = _level_rank(work_unit_level)
    jd_rank = _level_rank(jd_level)

    diff = wu_rank - jd_rank  # Positive = overqualified, negative = underqualified

    if diff == 0:
        return 1.0

    if diff > 0:
        # Overqualified: slight penalty
        overqualified_scores = {1: 0.9, 2: 0.8, 3: 0.75}
        return overqualified_scores.get(diff, 0.7)
    else:
        # Underqualified: larger penalty
        underqualified_scores = {-1: 0.8, -2: 0.6, -3: 0.4}
        return underqualified_scores.get(diff, 0.3)
```

### 3. Configuration Extension

Add seniority matching config to ScoringWeights:

```python
# src/resume_as_code/models/config.py - add to ScoringWeights class

class ScoringWeights(BaseModel):
    # ... existing fields ...

    use_seniority_matching: bool = Field(
        default=True,
        description="Enable seniority level matching against JD"
    )
    seniority_blend: float = Field(
        default=0.1,
        ge=0.0,
        le=0.3,
        description="How much seniority alignment affects final score (0.1 = 10%)"
    )
```

### 4. Ranker Integration

Integrate seniority scoring into HybridRanker:

```python
# src/resume_as_code/services/ranker.py - add method and integrate

from resume_as_code.services.seniority_inference import (
    infer_seniority,
    calculate_seniority_alignment,
)

class HybridRanker:
    # ... existing methods ...

    def _calculate_seniority_score(
        self,
        work_unit: WorkUnit,
        jd: JobDescription,
    ) -> float:
        """Calculate seniority alignment score for a work unit.

        Returns 1.0 if seniority matching is disabled.
        """
        if not self.config.scoring_weights.use_seniority_matching:
            return 1.0

        # Get work unit's attached position (if available via PrivateAttr)
        position = getattr(work_unit, '_position', None)

        # Infer work unit seniority
        wu_level = infer_seniority(work_unit, position)

        # Get JD seniority
        jd_level = jd.experience_level

        # Calculate alignment
        return calculate_seniority_alignment(wu_level, jd_level)

    def _blend_all_scores(
        self,
        relevance_score: float,
        recency_score: float,
        seniority_score: float,
    ) -> float:
        """Blend all scoring components into final score.

        Formula:
        final = relevance × (1 - recency_blend - seniority_blend)
              + recency × recency_blend
              + seniority × seniority_blend
        """
        weights = self.config.scoring_weights
        recency_blend = weights.recency_blend
        seniority_blend = weights.seniority_blend
        relevance_blend = 1.0 - recency_blend - seniority_blend

        return (
            relevance_score * relevance_blend
            + recency_score * recency_blend
            + seniority_score * seniority_blend
        )
```

### 5. Match Reasons Enhancement

Add seniority to match reasons for transparency:

```python
# In ranker.py match reason generation

def _generate_match_reasons(
    self,
    work_unit: WorkUnit,
    jd: JobDescription,
    scores: dict,
) -> list[str]:
    reasons = []

    # ... existing reason generation ...

    # Seniority alignment reason
    if self.config.scoring_weights.use_seniority_matching:
        seniority_score = scores.get("seniority", 1.0)
        if seniority_score >= 0.9:
            reasons.append("Seniority level matches JD requirements")
        elif seniority_score >= 0.7:
            reasons.append("Seniority level close to JD requirements")
        elif seniority_score < 0.5:
            reasons.append(f"Seniority mismatch (score: {seniority_score:.0%})")

    return reasons
```

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/resume_as_code/models/work_unit.py` | Modify | Add `seniority_level: ExperienceLevel \| None` field |
| `src/resume_as_code/services/seniority_inference.py` | Create | Seniority inference service |
| `src/resume_as_code/models/config.py` | Modify | Add `use_seniority_matching`, `seniority_blend` to ScoringWeights |
| `src/resume_as_code/services/ranker.py` | Modify | Integrate seniority scoring |
| `tests/unit/services/test_seniority_inference.py` | Create | Unit tests for inference |
| `tests/unit/services/test_ranker_seniority.py` | Create | Ranker seniority integration tests |

---

## Test Cases

### Unit Tests: Seniority Inference

```python
# tests/unit/services/test_seniority_inference.py
import pytest
from resume_as_code.models.job_description import ExperienceLevel
from resume_as_code.services.seniority_inference import (
    infer_seniority_from_title,
    calculate_seniority_alignment,
    _parse_currency,
)


class TestInferSeniorityFromTitle:
    """Test title pattern matching."""

    @pytest.mark.parametrize("title,expected", [
        ("CTO", ExperienceLevel.EXECUTIVE),
        ("VP of Engineering", ExperienceLevel.EXECUTIVE),
        ("Chief Technology Officer", ExperienceLevel.EXECUTIVE),
        ("Principal Engineer", ExperienceLevel.PRINCIPAL),
        ("Distinguished Engineer", ExperienceLevel.PRINCIPAL),
        ("Staff Software Engineer", ExperienceLevel.STAFF),
        ("Solutions Architect", ExperienceLevel.STAFF),
        ("Engineering Manager", ExperienceLevel.LEAD),
        ("Tech Lead", ExperienceLevel.LEAD),
        ("Senior Software Engineer", ExperienceLevel.SENIOR),
        ("Sr. Developer", ExperienceLevel.SENIOR),
        ("Software Engineer II", ExperienceLevel.MID),
        ("Developer", ExperienceLevel.MID),
        ("Junior Developer", ExperienceLevel.ENTRY),
        ("Associate Engineer", ExperienceLevel.ENTRY),
        ("Software Engineering Intern", ExperienceLevel.ENTRY),
    ])
    def test_title_pattern_matching(self, title: str, expected: ExperienceLevel):
        assert infer_seniority_from_title(title) == expected

    def test_unknown_title_defaults_to_mid(self):
        assert infer_seniority_from_title("Specialist") == ExperienceLevel.MID


class TestSeniorityAlignment:
    """Test alignment score calculation with asymmetric penalties."""

    def test_exact_match(self):
        score = calculate_seniority_alignment(
            ExperienceLevel.SENIOR, ExperienceLevel.SENIOR
        )
        assert score == 1.0

    def test_overqualified_one_level(self):
        # LEAD applying for SENIOR job (overqualified)
        score = calculate_seniority_alignment(
            ExperienceLevel.LEAD, ExperienceLevel.SENIOR
        )
        assert score == 0.9  # Slight penalty

    def test_underqualified_one_level(self):
        # SENIOR applying for LEAD job (underqualified)
        score = calculate_seniority_alignment(
            ExperienceLevel.SENIOR, ExperienceLevel.LEAD
        )
        assert score == 0.8  # Moderate penalty

    def test_asymmetric_penalty(self):
        # Same distance, different direction
        overqualified = calculate_seniority_alignment(
            ExperienceLevel.STAFF, ExperienceLevel.SENIOR  # +2 levels
        )
        underqualified = calculate_seniority_alignment(
            ExperienceLevel.MID, ExperienceLevel.LEAD  # -2 levels
        )
        assert overqualified > underqualified  # 0.8 > 0.6

    def test_major_underqualified(self):
        score = calculate_seniority_alignment(
            ExperienceLevel.ENTRY, ExperienceLevel.EXECUTIVE
        )
        assert score == 0.3  # Major underqualified penalty


class TestParseCurrency:
    """Test currency string parsing."""

    @pytest.mark.parametrize("value,expected", [
        ("$500M", 500_000_000),
        ("$2.5B", 2_500_000_000),
        ("$50K", 50_000),
        ("$1,000,000", 1_000_000),
        ("100M", 100_000_000),
        ("$10.5M", 10_500_000),
        ("", 0),
    ])
    def test_currency_parsing(self, value: str, expected: int):
        assert _parse_currency(value) == expected
```

### Integration Tests: Ranker with Seniority

```python
# tests/unit/services/test_ranker_seniority.py
import pytest
from resume_as_code.models.job_description import ExperienceLevel, JobDescription
from resume_as_code.models.work_unit import WorkUnit
from resume_as_code.services.ranker import HybridRanker


class TestRankerSeniorityScoring:
    """Test seniority integration in ranking."""

    def test_seniority_disabled_returns_neutral_score(self, ranker_no_seniority):
        """When seniority matching disabled, score is 1.0."""
        wu = WorkUnit(title="Junior Dev task", ...)
        jd = JobDescription(experience_level=ExperienceLevel.EXECUTIVE, ...)

        score = ranker_no_seniority._calculate_seniority_score(wu, jd)
        assert score == 1.0

    def test_matching_seniority_boosts_score(self, ranker_with_seniority):
        """Work units matching JD seniority rank higher."""
        senior_wu = WorkUnit(title="Led team initiative", seniority_level=ExperienceLevel.SENIOR)
        junior_wu = WorkUnit(title="Assisted with project", seniority_level=ExperienceLevel.ENTRY)

        jd = JobDescription(experience_level=ExperienceLevel.SENIOR, raw_text="...")

        senior_score = ranker_with_seniority._calculate_seniority_score(senior_wu, jd)
        junior_score = ranker_with_seniority._calculate_seniority_score(junior_wu, jd)

        assert senior_score > junior_score
        assert senior_score == 1.0
```

---

## Definition of Done

- [x] `seniority_level` field added to WorkUnit model (optional, ExperienceLevel enum)
- [x] `seniority_inference.py` service created with:
  - [x] `infer_seniority_from_title()` function
  - [x] `infer_seniority()` function (handles position scope)
  - [x] `calculate_seniority_alignment()` function
- [x] Config extended with `use_seniority_matching` and `seniority_blend`
- [x] HybridRanker integrates seniority scoring
- [x] Match reasons include seniority alignment info
- [x] Unit tests pass for inference logic
- [x] Integration tests pass for ranker
- [x] Backward compatible (no seniority_level = inference kicks in)
- [x] `uv run ruff check` passes
- [x] `uv run mypy src --strict` passes

---

## Implementation Notes

1. **Reuse ExperienceLevel**: Don't create a new enum. Import from `job_description.py` for consistency.

2. **Pattern Order Matters**: Title patterns are checked in order from most senior to least. "Senior Manager" should match LEAD (manager) not SENIOR.

3. **Scope Trumps Title**: A "Software Engineer" with $100M P&L responsibility should be EXECUTIVE, not MID.

4. **Blend Weight**: Default 10% is conservative. Users can tune up to 30% for roles where seniority fit is critical.

5. **Graceful Degradation**: If position isn't attached to work unit, fall back to work unit title inference.

---

## Implementation Learnings

**Position Wiring Required**: The original design assumed positions would be attached to WorkUnit models via `_position` PrivateAttr. However, the ranker receives raw dicts, not model instances.

**Fix applied**: Added `positions: dict[str, Any] | None` parameter to `HybridRanker.rank()` and `_calculate_seniority_score()`. Updated `plan.py` and `build.py` to always load positions and pass to ranker. This enables scope-based boosting (P&L, revenue, team size) to work correctly.

**Files modified beyond original scope**:
- `plan.py`: Load positions unconditionally, pass to `ranker.rank()`
- `build.py`: Load positions unconditionally, pass to `ranker.rank()`
- `ranker.py`: Add `positions` parameter, look up by `position_id`

---

## Dev Agent Record

### File List

| File | Action | Description |
|------|--------|-------------|
| `src/resume_as_code/models/work_unit.py` | Modified | Added `seniority_level: ExperienceLevel \| None` field |
| `src/resume_as_code/services/seniority_inference.py` | Created | Seniority inference service with asymmetric penalty scoring |
| `src/resume_as_code/models/config.py` | Modified | Added `use_seniority_matching`, `seniority_blend` to ScoringWeights |
| `src/resume_as_code/services/ranker.py` | Modified | Integrated seniority scoring with positions support |
| `src/resume_as_code/commands/plan.py` | Modified | Load positions and pass to ranker |
| `src/resume_as_code/commands/build.py` | Modified | Load positions and pass to ranker |
| `schemas/work-unit.schema.json` | Modified | Added seniority_level field with ExperienceLevel enum |
| `tests/unit/services/test_seniority_inference.py` | Created | Unit tests for inference with asymmetric penalty tests |
| `tests/unit/services/test_ranker_seniority.py` | Created | Ranker seniority integration tests |

### Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-01-16 | Implemented asymmetric seniority penalty | AC4 requires overqualified to have slight penalty vs larger penalty for underqualified |
| 2026-01-16 | Added positions parameter to ranker | Enable scope-based boosting (P&L, revenue, team size) |
| 2026-01-16 | Updated tests for asymmetric scoring | Tests now validate directional penalty differences |

### Decisions Made

1. **Reused ExperienceLevel enum** from job_description.py rather than creating duplicate
2. **Pattern order matters** - LEAD patterns checked before SENIOR so "Senior Manager" → LEAD
3. **Asymmetric penalties** - Overqualified (0.9/0.8/0.75/0.7) vs Underqualified (0.8/0.6/0.4/0.3)
4. **Positions passed as dict** - Ranker receives positions dict rather than attached Position objects
