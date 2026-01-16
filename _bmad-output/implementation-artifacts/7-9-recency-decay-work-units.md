# Story 7.9: Recency Decay for Work Units

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **job seeker**,
I want **my recent work experience weighted higher than older experience**,
So that **my current skills and relevance are properly reflected in rankings**.

## Acceptance Criteria

1. **Given** a work unit with `time_ended: 2024-01` (1 year ago)
   **When** ranking against a JD with `recency_half_life: 5` years
   **Then** the work unit receives ~87% recency weight

2. **Given** a work unit with `time_ended: 2019-01` (5 years ago)
   **When** ranking with 5-year half-life
   **Then** the work unit receives ~50% recency weight

3. **Given** a work unit with `time_ended: null` (current position)
   **When** ranking runs
   **Then** the work unit receives 100% recency weight

4. **Given** recency decay is disabled (`recency_half_life: null`)
   **When** ranking runs
   **Then** all work units weighted equally (current behavior)

5. **Given** the final score calculation
   **When** combining relevance and recency
   **Then** formula is: `final = (relevance_blend × relevance) + (recency_blend × recency_decay)`
   **And** `relevance_blend + recency_blend = 1.0`

## Tasks / Subtasks

- [x] Task 1: Add recency config to ScoringWeights (AC: #4, #5)
  - [x] 1.1 Add `recency_half_life: float | None` field (default 5.0)
  - [x] 1.2 Add `recency_blend: float` field (default 0.2)
  - [x] 1.3 Add docstrings explaining the decay formula
  - [x] 1.4 Add validation constraints (ge=1.0, le=20.0 for half_life)

- [x] Task 2: Implement recency decay calculation (AC: #1, #2, #3)
  - [x] 2.1 Create `_calculate_recency_score()` method in HybridRanker
  - [x] 2.2 Handle `time_ended: null` as current date (100% weight)
  - [x] 2.3 Implement exponential decay formula
  - [x] 2.4 Return 1.0 when recency decay is disabled

- [x] Task 3: Integrate recency into ranking (AC: #5)
  - [x] 3.1 Modify `rank()` to calculate recency scores
  - [x] 3.2 Blend relevance and recency scores using configured weights
  - [x] 3.3 Ensure backward compatibility when recency disabled

- [x] Task 4: Add tests and quality checks
  - [x] 4.1 Unit tests for decay formula at various ages
  - [x] 4.2 Test current positions get 100% weight
  - [x] 4.3 Test disabled recency produces identical results
  - [x] 4.4 Run `ruff check` and `mypy --strict`

## Dev Notes

### Current State Analysis

**Existing Implementation:**
- `WorkUnit.time_ended: date | None` (work_unit.py:223) - available for age calculation
- `ScoringWeights` (config.py:50-65) - has bm25/semantic weights, no recency yet
- `HybridRanker.rank()` - combines BM25 and semantic scores via RRF

**Gap:** No recency consideration - 10-year-old achievements weighted same as recent ones.

### Exponential Decay Formula

The recency decay uses exponential decay with configurable half-life:

```
recency_score = e^(-λ × years_ago)

Where:
- λ = ln(2) / half_life  (decay constant)
- years_ago = (today - time_ended).days / 365.25
- half_life = configured number of years for score to reach 50%
```

**Example calculations with 5-year half-life:**

| Years Ago | Calculation | Recency Score |
|-----------|-------------|---------------|
| 0 (current) | e^0 | 1.000 (100%) |
| 1 year | e^(-0.139×1) | 0.871 (87%) |
| 2 years | e^(-0.139×2) | 0.758 (76%) |
| 5 years | e^(-0.139×5) | 0.500 (50%) |
| 10 years | e^(-0.139×10) | 0.250 (25%) |

### Implementation Pattern

**Config Extension:**
```python
# models/config.py - add to ScoringWeights

class ScoringWeights(BaseModel):
    """Weights for ranking algorithm."""

    # BM25 vs Semantic balance for RRF fusion
    bm25_weight: float = Field(default=1.0, ge=0.0, le=2.0)
    semantic_weight: float = Field(default=1.0, ge=0.0, le=2.0)

    # Field-specific weighting (Story 7.8)
    title_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    skills_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    experience_weight: float = Field(default=1.0, ge=0.0, le=10.0)

    # Recency decay (Story 7.9)
    recency_half_life: float | None = Field(
        default=5.0,
        ge=1.0,
        le=20.0,
        description="Years for experience to decay to 50% weight. None disables decay.",
    )
    recency_blend: float = Field(
        default=0.2,
        ge=0.0,
        le=0.5,
        description="Weight of recency in final score (0.2 = 20%). Relevance gets 1 - recency_blend.",
    )
```

**Recency Calculation:**
```python
# services/ranker.py - add to HybridRanker

import math
from datetime import date

def _calculate_recency_score(
    self,
    work_unit: dict[str, Any],
    scoring_weights: ScoringWeights | None,
) -> float:
    """Calculate recency decay score for a work unit.

    Uses exponential decay with configurable half-life.
    Current positions (time_ended=None) receive 100% weight.

    Args:
        work_unit: Work Unit dictionary.
        scoring_weights: Scoring weights with recency config.

    Returns:
        Recency score between 0.0 and 1.0.
    """
    # No decay if disabled
    if scoring_weights is None or scoring_weights.recency_half_life is None:
        return 1.0

    # Get end date (None means current/ongoing)
    time_ended = work_unit.get("time_ended")
    if time_ended is None:
        return 1.0  # Current position gets full weight

    # Parse date if string
    if isinstance(time_ended, str):
        # Handle YYYY-MM-DD or YYYY-MM format
        try:
            if len(time_ended) == 10:  # YYYY-MM-DD
                end_date = date.fromisoformat(time_ended)
            else:  # YYYY-MM
                end_date = date.fromisoformat(f"{time_ended}-01")
        except ValueError:
            return 1.0  # Invalid date, default to full weight
    elif isinstance(time_ended, date):
        end_date = time_ended
    else:
        return 1.0  # Unknown format, default to full weight

    # Calculate years ago
    today = date.today()
    years_ago = (today - end_date).days / 365.25

    # Handle future dates (shouldn't happen, but be safe)
    if years_ago < 0:
        return 1.0

    # Exponential decay: score = e^(-λ × years_ago)
    # Where λ = ln(2) / half_life
    half_life = scoring_weights.recency_half_life
    decay_constant = math.log(2) / half_life
    recency_score = math.exp(-decay_constant * years_ago)

    return recency_score


def _blend_scores(
    self,
    relevance_scores: list[float],
    recency_scores: list[float],
    scoring_weights: ScoringWeights | None,
) -> list[float]:
    """Blend relevance and recency scores.

    Formula: final = (relevance_blend × relevance) + (recency_blend × recency)

    Args:
        relevance_scores: Normalized relevance scores (0-1).
        recency_scores: Recency decay scores (0-1).
        scoring_weights: Weights configuration.

    Returns:
        Blended final scores.
    """
    if scoring_weights is None:
        return relevance_scores

    recency_blend = scoring_weights.recency_blend
    relevance_blend = 1.0 - recency_blend

    return [
        (relevance_blend * rel) + (recency_blend * rec)
        for rel, rec in zip(relevance_scores, recency_scores)
    ]
```

**Updated rank() Method:**
```python
def rank(
    self,
    work_units: list[dict[str, Any]],
    jd: JobDescription,
    top_k: int = 10,
    scoring_weights: ScoringWeights | None = None,
) -> RankingOutput:
    """Rank Work Units against a job description."""
    if not work_units:
        return RankingOutput(results=[], jd_keywords=jd.keywords)

    # ... existing BM25 and semantic ranking code ...

    # RRF fusion with optional weights
    rrf_scores = self._rrf_fusion(bm25_ranks, semantic_ranks, scoring_weights)

    # Normalize relevance scores to 0.0-1.0
    max_score = max(rrf_scores) if rrf_scores else 1.0
    min_score = min(rrf_scores) if rrf_scores else 0.0
    if max_score == min_score:
        normalized_relevance = [1.0] * len(rrf_scores)
    else:
        normalized_relevance = [
            (s - min_score) / (max_score - min_score) for s in rrf_scores
        ]

    # Calculate recency scores
    recency_scores = [
        self._calculate_recency_score(wu, scoring_weights)
        for wu in work_units
    ]

    # Blend relevance and recency
    final_scores = self._blend_scores(
        normalized_relevance, recency_scores, scoring_weights
    )

    # Sort by final score (higher is better)
    sorted_indices = sorted(
        range(len(work_units)),
        key=lambda i: (final_scores[i], wu_ids[i]),
        reverse=True,
    )

    # Build results
    results: list[RankingResult] = []
    for idx in sorted_indices[: top_k * 2]:
        match_reasons = self._extract_match_reasons(work_units[idx], jd)
        results.append(
            RankingResult(
                work_unit_id=wu_ids[idx],
                work_unit=work_units[idx],
                score=final_scores[idx],
                bm25_rank=bm25_ranks[idx],
                semantic_rank=semantic_ranks[idx],
                match_reasons=match_reasons,
            )
        )

    return RankingOutput(results=results, jd_keywords=jd.keywords)
```

### Testing Standards

```python
# tests/unit/services/test_ranker_recency.py
import pytest
import math
from datetime import date, timedelta
from unittest.mock import MagicMock

import numpy as np

from resume_as_code.models.config import ScoringWeights
from resume_as_code.services.ranker import HybridRanker


@pytest.fixture
def ranker() -> HybridRanker:
    """Create ranker with mocked embedding service."""
    mock_embedder = MagicMock()
    mock_embedder.embed_batch.return_value = np.zeros((3, 384))
    mock_embedder.embed_passage.return_value = np.zeros(384)
    return HybridRanker(embedding_service=mock_embedder)


class TestRecencyCalculation:
    """Tests for recency decay calculation."""

    def test_current_position_full_weight(self, ranker: HybridRanker) -> None:
        """Work unit with time_ended=None gets 100% weight."""
        wu = {"id": "wu-current", "time_ended": None}
        weights = ScoringWeights(recency_half_life=5.0)

        score = ranker._calculate_recency_score(wu, weights)

        assert score == 1.0

    def test_one_year_old_about_87_percent(self, ranker: HybridRanker) -> None:
        """Work unit 1 year old gets ~87% weight with 5-year half-life."""
        one_year_ago = date.today() - timedelta(days=365)
        wu = {"id": "wu-1yr", "time_ended": one_year_ago}
        weights = ScoringWeights(recency_half_life=5.0)

        score = ranker._calculate_recency_score(wu, weights)

        # Expected: e^(-ln(2)/5 × 1) ≈ 0.871
        assert 0.85 < score < 0.90

    def test_five_years_old_about_50_percent(self, ranker: HybridRanker) -> None:
        """Work unit 5 years old gets ~50% weight with 5-year half-life."""
        five_years_ago = date.today() - timedelta(days=5 * 365)
        wu = {"id": "wu-5yr", "time_ended": five_years_ago}
        weights = ScoringWeights(recency_half_life=5.0)

        score = ranker._calculate_recency_score(wu, weights)

        # Expected: e^(-ln(2)/5 × 5) = 0.5
        assert 0.45 < score < 0.55

    def test_ten_years_old_about_25_percent(self, ranker: HybridRanker) -> None:
        """Work unit 10 years old gets ~25% weight with 5-year half-life."""
        ten_years_ago = date.today() - timedelta(days=10 * 365)
        wu = {"id": "wu-10yr", "time_ended": ten_years_ago}
        weights = ScoringWeights(recency_half_life=5.0)

        score = ranker._calculate_recency_score(wu, weights)

        # Expected: e^(-ln(2)/5 × 10) = 0.25
        assert 0.20 < score < 0.30

    def test_disabled_recency_returns_full_weight(self, ranker: HybridRanker) -> None:
        """Disabled recency (None half-life) returns 1.0."""
        five_years_ago = date.today() - timedelta(days=5 * 365)
        wu = {"id": "wu-old", "time_ended": five_years_ago}
        weights = ScoringWeights(recency_half_life=None)

        score = ranker._calculate_recency_score(wu, weights)

        assert score == 1.0

    def test_no_weights_returns_full_weight(self, ranker: HybridRanker) -> None:
        """No scoring weights (None) returns 1.0."""
        five_years_ago = date.today() - timedelta(days=5 * 365)
        wu = {"id": "wu-old", "time_ended": five_years_ago}

        score = ranker._calculate_recency_score(wu, None)

        assert score == 1.0

    def test_string_date_format_yyyy_mm_dd(self, ranker: HybridRanker) -> None:
        """Handle YYYY-MM-DD string format."""
        one_year_ago = date.today() - timedelta(days=365)
        wu = {"id": "wu-str", "time_ended": one_year_ago.isoformat()}
        weights = ScoringWeights(recency_half_life=5.0)

        score = ranker._calculate_recency_score(wu, weights)

        assert 0.85 < score < 0.90

    def test_string_date_format_yyyy_mm(self, ranker: HybridRanker) -> None:
        """Handle YYYY-MM string format."""
        one_year_ago = date.today() - timedelta(days=365)
        date_str = one_year_ago.strftime("%Y-%m")
        wu = {"id": "wu-str", "time_ended": date_str}
        weights = ScoringWeights(recency_half_life=5.0)

        score = ranker._calculate_recency_score(wu, weights)

        # Slightly different due to day-01 assumption, but still ~87%
        assert 0.80 < score < 0.95


class TestScoreBlending:
    """Tests for relevance/recency score blending."""

    def test_default_blend_80_20(self, ranker: HybridRanker) -> None:
        """Default blend is 80% relevance, 20% recency."""
        relevance = [1.0, 0.5, 0.0]
        recency = [0.5, 1.0, 1.0]
        weights = ScoringWeights(recency_blend=0.2)

        blended = ranker._blend_scores(relevance, recency, weights)

        # final[0] = 0.8 × 1.0 + 0.2 × 0.5 = 0.9
        # final[1] = 0.8 × 0.5 + 0.2 × 1.0 = 0.6
        # final[2] = 0.8 × 0.0 + 0.2 × 1.0 = 0.2
        assert abs(blended[0] - 0.9) < 0.01
        assert abs(blended[1] - 0.6) < 0.01
        assert abs(blended[2] - 0.2) < 0.01

    def test_no_weights_returns_relevance(self, ranker: HybridRanker) -> None:
        """No weights returns original relevance scores."""
        relevance = [1.0, 0.5, 0.0]
        recency = [0.5, 1.0, 1.0]

        blended = ranker._blend_scores(relevance, recency, None)

        assert blended == relevance

    def test_zero_recency_blend(self, ranker: HybridRanker) -> None:
        """Zero recency_blend uses only relevance."""
        relevance = [1.0, 0.5, 0.0]
        recency = [0.0, 0.0, 0.0]  # Old work units
        weights = ScoringWeights(recency_blend=0.0)

        blended = ranker._blend_scores(relevance, recency, weights)

        assert blended == relevance

    def test_max_recency_blend(self, ranker: HybridRanker) -> None:
        """Max recency_blend (0.5) gives equal weight."""
        relevance = [1.0, 0.0]
        recency = [0.0, 1.0]
        weights = ScoringWeights(recency_blend=0.5)

        blended = ranker._blend_scores(relevance, recency, weights)

        # final[0] = 0.5 × 1.0 + 0.5 × 0.0 = 0.5
        # final[1] = 0.5 × 0.0 + 0.5 × 1.0 = 0.5
        assert blended[0] == blended[1] == 0.5
```

### Research Basis

Eightfold AI uses "recent skill vector similarity" as a distinct signal. Exponential decay with configurable half-life is industry standard.

**Recommended Defaults:**
- `recency_half_life: 5.0` - Experience older than 5 years is 50% weighted
- `recency_blend: 0.2` - 20% of score from recency, 80% from relevance

### Project Context Rules

From `project-context.md`:
- Run `ruff check` and `mypy --strict` before completing
- Use Rich console for CLI output, never `print()`
- Type hints required on all public functions
- Use `|` union syntax (Python 3.10+)

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-7-schema-data-model-refactoring.md#Story 7.9]
- [Source: src/resume_as_code/services/ranker.py - existing HybridRanker]
- [Source: src/resume_as_code/models/config.py:50-65 - ScoringWeights]
- [Source: src/resume_as_code/models/work_unit.py:223 - time_ended field]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None required.

### Completion Notes List

- Implemented exponential decay formula: `recency_score = e^(-λ × years_ago)` where `λ = ln(2) / half_life`
- Added `recency_half_life` (default 5.0 years) and `recency_blend` (default 0.2) to ScoringWeights
- Current positions (`time_ended=None`) receive 100% weight
- Supports both `date` objects and string formats (YYYY-MM-DD, YYYY-MM)
- Final score blending: `final = (1 - recency_blend) × relevance + recency_blend × recency`
- Added 23 new tests across 4 test classes (TestRecencyDecay, TestScoreBlending, TestRecencyConfigValidation, TestRecencyIntegration)
- All 54 ranker tests pass, ruff check and mypy --strict pass

**Code Review Remediation (2026-01-16):**
- Fixed pre-existing test assertion in `test_low_relevance_reason_for_low_scores` to accept boundary case
- Added integration test `test_recency_decay_boosts_recent_work_units` verifying end-to-end recency ranking

### File List

- `src/resume_as_code/models/config.py` - Added recency_half_life and recency_blend fields to ScoringWeights with docstrings
- `src/resume_as_code/services/ranker.py` - Added `_calculate_recency_score()` and `_blend_scores()` methods, integrated into `rank()`
- `tests/unit/test_ranker.py` - Added 23 new tests for recency decay feature
- `tests/integration/test_plan_command.py` - Added `test_recency_decay_boosts_recent_work_units` for Story 7.9 verification; fixed `test_low_relevance_reason_for_low_scores` threshold edge case

