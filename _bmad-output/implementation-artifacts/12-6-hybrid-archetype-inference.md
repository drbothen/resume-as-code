# Story 12.6: Enhanced Archetype Inference with Semantic Embeddings

## Status: Done

---

## Story

**As a** user with domain-specific work units (cybersecurity, compliance, etc.),
**I want** archetype inference that understands meaning beyond simple keywords,
**So that** my work units are accurately classified even when using specialized terminology.

**Note**: This story replaces the regex-only approach from Story 12-3 with a hybrid weighted-regex + semantic embedding approach as the default and only behavior.

---

## Context & Background

### Epic 12 Goal

Add persistent archetype tracking to work units for categorization analysis, PAR validation, and improved resume generation.

### Previous Stories

- **12-1** (done): Added `WorkUnitArchetype` enum and required `archetype` field to model
- **12-2** (done): Persist archetype when using `--archetype` flag
- **12-3** (review): Basic regex-based inference service with CLI command
- **12-4** (ready-for-dev): PAR structure validation by archetype
- **12-5** (ready-for-dev): Archetype reporting statistics

### Problem Statement

The current regex-based inference (Story 12-3) has limitations:

1. **Domain-specific terminology**: Terms like "ATO", "RMF", "IV&V" don't match generic patterns
2. **Flat pattern weighting**: All patterns count equally, but "P1" is a stronger incident signal than "detected"
3. **Keyword-only matching**: Doesn't understand synonyms or conceptual similarity

**Evidence from jmagady-resume testing:**
- 43 work units analyzed, most scored <30% confidence
- Only 2 work units exceeded 0.3 threshold (both migrations with explicit "migrated" keyword)
- Cybersecurity-heavy content (ATO, RMF compliance) not recognized as greenfield/leadership

### Solution: Hybrid Approach

Combine three techniques:

1. **Weighted Regex** (Option 4): Strong signals score higher (e.g., "P1" = 3.0 vs "detected" = 1.0)
2. **Semantic Embeddings** (Option 2): Use existing EmbeddingService to compare meaning
3. **Hybrid Flow** (Option 3): Try weighted regex first, fall back to semantic matching

```
Work Unit Text
      │
      ▼
┌─────────────────┐
│ Weighted Regex  │  ◄── Strong patterns score higher
└────────┬────────┘
         │
         ▼
    confidence ≥ 0.5?
      /        \
    YES         NO
     │           │
     ▼           ▼
 Return      ┌─────────────────┐
 Result      │    Semantic     │  ◄── Embeddings compare meaning
             │   Embeddings    │
             └────────┬────────┘
                      │
                      ▼
                Return Result
```

---

## Acceptance Criteria

### AC1: Weighted Pattern Scoring

**Given** regex patterns with assigned weights (e.g., `("P1", 3.0)`, `("detected", 1.0)`)
**When** scoring a work unit
**Then** weighted sum is used: `score = matched_weight / total_weight`

### AC2: Semantic Archetype Descriptions

**Given** rich text descriptions for each archetype
**When** semantic scoring is performed
**Then** uses existing `EmbeddingService.similarity()` to compare work unit text against archetype descriptions

### AC3: Hybrid Fallback Logic

**Given** weighted regex score < 0.5
**When** inference is performed
**Then** automatically falls back to semantic embedding comparison

### AC4: Method Attribution in Results

**Given** an inference result
**When** returned to CLI or JSON
**Then** includes `method` field: `"regex"`, `"semantic"`, or `"fallback"`

### AC5: Improved Accuracy on Domain-Specific Content

**Given** a work unit with "Achieved first-attempt ATO for submarine base"
**When** inference runs
**Then** correctly identifies as `greenfield` via semantic similarity (not `minimal`)

---

## Technical Implementation

### 1. Update Archetype Inference Service

Location: `src/resume_as_code/services/archetype_inference_service.py`

```python
"""Archetype inference service with hybrid regex + semantic matching."""

from __future__ import annotations

import re
from typing import Any, Literal

from resume_as_code.models.work_unit import WorkUnit, WorkUnitArchetype
from resume_as_code.services.embedding_service import EmbeddingService

# Weighted patterns: (pattern, weight)
# Higher weight = stronger signal for archetype
ARCHETYPE_PATTERNS_WEIGHTED: dict[WorkUnitArchetype, list[tuple[str, float]]] = {
    WorkUnitArchetype.INCIDENT: [
        (r"\bp1\b", 3.0),           # Very strong signal
        (r"\bp2\b", 2.5),
        (r"outage", 2.5),
        (r"incident", 2.0),
        (r"breach", 2.5),
        (r"triaged", 2.0),
        (r"mitigated", 2.0),
        (r"resolved.*production", 2.0),
        (r"mttr", 2.0),
        (r"security\s+event", 2.0),
        (r"escalation", 1.5),
        (r"on-?call", 1.5),
        (r"detected", 1.0),         # Weaker signal
    ],
    WorkUnitArchetype.GREENFIELD: [
        (r"from\s+scratch", 3.0),
        (r"built\s+new", 2.5),
        (r"designed\s+(?:and\s+)?(?:built|implemented)", 2.5),
        (r"architected", 2.0),
        (r"launched", 2.0),
        (r"pioneered", 2.5),
        (r"new\s+(?:system|feature|product|platform)", 2.0),
        (r"ground-?up", 2.5),
        (r"stood\s+up", 2.0),
        (r"established\s+(?:new|first)", 2.0),
        (r"first\s+(?:ever|time|attempt)", 2.0),
    ],
    WorkUnitArchetype.MIGRATION: [
        (r"migrat(?:ed|ion)", 3.0),
        (r"cloud\s+migration", 3.0),
        (r"upgraded", 2.0),
        (r"transitioned", 2.0),
        (r"legacy\s+(?:replacement|system)", 2.5),
        (r"database\s+migration", 2.5),
        (r"platform\s+(?:upgrade|migration)", 2.5),
        (r"cutover", 2.0),
        (r"decommission", 1.5),
    ],
    WorkUnitArchetype.OPTIMIZATION: [
        (r"optimiz(?:ed|ation)", 3.0),
        (r"reduced\s+(?:latency|cost|time)", 2.5),
        (r"\d+%\s+(?:reduction|improvement|faster)", 3.0),
        (r"improv(?:ed|ing)\s+performance", 2.5),
        (r"profiled", 2.0),
        (r"cost\s+(?:reduction|savings)", 2.5),
        (r"latency\s+reduction", 2.5),
        (r"resource\s+(?:optimization|rightsizing)", 2.0),
        (r"bottleneck", 1.5),
    ],
    WorkUnitArchetype.LEADERSHIP: [
        (r"led\s+(?:team|effort|program)", 3.0),
        (r"mentor(?:ed|ing)", 2.5),
        (r"coach(?:ed|ing)", 2.5),
        (r"managed\s+(?:\d+|team)", 2.5),
        (r"aligned\s+stakeholders", 2.0),
        (r"championed", 2.0),
        (r"unified\s+teams", 2.0),
        (r"cross-?(?:team|functional)", 2.0),
        (r"organizational\s+(?:change|impact)", 2.0),
        (r"built\s+(?:the\s+)?team", 2.5),
        (r"hired", 1.5),
        (r"directed", 2.0),
    ],
    WorkUnitArchetype.STRATEGIC: [
        (r"strateg(?:y|ic)", 3.0),
        (r"market\s+(?:analysis|positioning)", 2.5),
        (r"competitive\s+(?:analysis|advantage)", 2.5),
        (r"positioned", 2.0),
        (r"partnership", 2.0),
        (r"market\s+share", 2.5),
        (r"business\s+development", 2.5),
        (r"roadmap", 2.0),
        (r"vision", 1.5),
    ],
    WorkUnitArchetype.TRANSFORMATION: [
        (r"transformation", 3.0),
        (r"digital\s+transformation", 3.0),
        (r"enterprise-?wide", 2.5),
        (r"board-?level", 2.5),
        (r"organizational\s+change", 2.5),
        (r"company-?wide", 2.5),
        (r"global\s+(?:initiative|rollout)", 2.5),
        (r"moderniz(?:ed|ation)", 2.0),
    ],
    WorkUnitArchetype.CULTURAL: [
        (r"culture", 3.0),
        (r"talent\s+development", 2.5),
        (r"engagement", 2.0),
        (r"attrition", 2.0),
        (r"retention", 2.0),
        (r"cultivated", 2.0),
        (r"dei|diversity", 2.5),
        (r"employee\s+experience", 2.5),
        (r"inclusion", 2.0),
    ],
}

# Rich semantic descriptions for embedding comparison
ARCHETYPE_DESCRIPTIONS: dict[WorkUnitArchetype, str] = {
    WorkUnitArchetype.INCIDENT: (
        "Resolved critical production incident, security breach, or system outage. "
        "On-call response, triaged and mitigated P1/P2 issues, reduced MTTR. "
        "Emergency response, incident management, service restoration."
    ),
    WorkUnitArchetype.GREENFIELD: (
        "Built new system from scratch, designed and launched new product or platform. "
        "Pioneered new capability, architected greenfield solution. First-time implementation, "
        "stood up new service, achieved initial certification or authorization. "
        "Created something that didn't exist before."
    ),
    WorkUnitArchetype.MIGRATION: (
        "Migrated legacy system to modern platform, cloud migration, database upgrade. "
        "Transitioned from on-premise to cloud, platform modernization. "
        "Replaced outdated technology, upgraded infrastructure, decommissioned legacy systems."
    ),
    WorkUnitArchetype.OPTIMIZATION: (
        "Optimized performance, reduced latency and costs. Improved efficiency, "
        "profiled and tuned system, resource rightsizing. Achieved percentage improvements, "
        "cost savings, faster response times, better throughput."
    ),
    WorkUnitArchetype.LEADERSHIP: (
        "Led team, mentored engineers, coached direct reports. Aligned stakeholders, "
        "built and grew team, cross-functional leadership. Managed people, "
        "developed talent, drove organizational change through influence."
    ),
    WorkUnitArchetype.STRATEGIC: (
        "Developed strategy, market analysis, competitive positioning. Business "
        "development, partnerships, market expansion. Defined roadmap, "
        "created vision, established strategic direction."
    ),
    WorkUnitArchetype.TRANSFORMATION: (
        "Led digital transformation, enterprise-wide change initiative. "
        "Organizational transformation, company-wide rollout, modernization program. "
        "Board-level initiatives, global change management."
    ),
    WorkUnitArchetype.CULTURAL: (
        "Improved team culture, talent development, employee engagement. "
        "Reduced attrition, DEI initiatives, cultivated inclusive environment. "
        "Employee experience, retention programs, culture change."
    ),
}

# Minimum confidence thresholds
MIN_CONFIDENCE_THRESHOLD = 0.5
SEMANTIC_CONFIDENCE_THRESHOLD = 0.3  # Lower for embeddings (similarity scores are different scale)

InferenceMethod = Literal["regex", "semantic", "fallback"]


def score_weighted_regex(text: str, archetype: WorkUnitArchetype) -> float:
    """Score text against weighted regex patterns.

    Args:
        text: Lowercase text to search.
        archetype: Archetype to score against.

    Returns:
        Score from 0.0 to 1.0 based on weighted pattern match ratio.
    """
    patterns = ARCHETYPE_PATTERNS_WEIGHTED.get(archetype, [])
    if not patterns:
        return 0.0

    total_weight = sum(weight for _, weight in patterns)
    matched_weight = sum(
        weight for pattern, weight in patterns
        if re.search(pattern, text, re.IGNORECASE)
    )
    return matched_weight / total_weight


def score_semantic(
    text: str,
    archetype: WorkUnitArchetype,
    embedding_service: EmbeddingService,
) -> float:
    """Score text against archetype using semantic similarity.

    Args:
        text: Text to compare.
        archetype: Archetype to score against.
        embedding_service: Service for computing embeddings.

    Returns:
        Cosine similarity score from 0.0 to 1.0.
    """
    description = ARCHETYPE_DESCRIPTIONS.get(archetype, "")
    if not description:
        return 0.0

    return embedding_service.similarity(text, description)


def infer_archetype_hybrid(
    work_unit: WorkUnit | dict[str, Any],
    embedding_service: EmbeddingService,
    regex_threshold: float = MIN_CONFIDENCE_THRESHOLD,
    semantic_threshold: float = SEMANTIC_CONFIDENCE_THRESHOLD,
) -> tuple[WorkUnitArchetype, float, InferenceMethod]:
    """Infer archetype using hybrid regex + semantic approach.

    First attempts weighted regex matching. If confidence is below threshold,
    falls back to semantic embedding comparison.

    Args:
        work_unit: WorkUnit object or raw dict from YAML.
        embedding_service: Service for semantic similarity.
        regex_threshold: Minimum regex confidence to skip semantic.
        semantic_threshold: Minimum semantic confidence to return non-minimal.

    Returns:
        Tuple of (archetype, confidence, method) where method indicates
        which algorithm produced the result.
    """
    text = extract_text_content(work_unit)

    # Phase 1: Try weighted regex
    regex_scores: dict[WorkUnitArchetype, float] = {}
    for archetype in WorkUnitArchetype:
        if archetype == WorkUnitArchetype.MINIMAL:
            continue
        regex_scores[archetype] = score_weighted_regex(text, archetype)

    best_regex = max(regex_scores, key=regex_scores.get)
    best_regex_score = regex_scores[best_regex]

    if best_regex_score >= regex_threshold:
        return (best_regex, best_regex_score, "regex")

    # Phase 2: Fall back to semantic matching
    semantic_scores: dict[WorkUnitArchetype, float] = {}
    for archetype in WorkUnitArchetype:
        if archetype == WorkUnitArchetype.MINIMAL:
            continue
        semantic_scores[archetype] = score_semantic(text, archetype, embedding_service)

    best_semantic = max(semantic_scores, key=semantic_scores.get)
    best_semantic_score = semantic_scores[best_semantic]

    if best_semantic_score >= semantic_threshold:
        return (best_semantic, best_semantic_score, "semantic")

    # Neither method confident enough
    return (WorkUnitArchetype.MINIMAL, max(best_regex_score, best_semantic_score), "fallback")


# Main entry point - always uses hybrid approach
def infer_archetype(
    work_unit: WorkUnit | dict[str, Any],
    embedding_service: EmbeddingService,
    threshold: float = MIN_CONFIDENCE_THRESHOLD,
) -> tuple[WorkUnitArchetype, float, InferenceMethod]:
    """Infer archetype using hybrid weighted-regex + semantic approach.

    Args:
        work_unit: WorkUnit object or raw dict from YAML.
        embedding_service: Service for semantic similarity.
        threshold: Minimum confidence for non-minimal result.

    Returns:
        Tuple of (archetype, confidence, method).
    """
    return infer_archetype_hybrid(
        work_unit,
        embedding_service,
        regex_threshold=threshold,
        semantic_threshold=SEMANTIC_CONFIDENCE_THRESHOLD,
    )
```

### 2. Update CLI Command

Location: `src/resume_as_code/commands/infer.py`

Replace the inference logic to always use hybrid approach:

```python
from resume_as_code.services.embedding_service import get_embedding_service
from resume_as_code.services.archetype_inference_service import infer_archetype

def infer_archetypes_command(
    ctx: click.Context,
    apply: bool,
    min_confidence: float,
    include_assigned: bool,
) -> None:
    # ... existing setup ...

    # Initialize embedding service (always needed now)
    embedding_service = get_embedding_service()

    for yaml_file in sorted(work_units_dir.glob("*.yaml")):
        # ... load data ...

        archetype, confidence, method = infer_archetype(
            data, embedding_service, min_confidence
        )

        result: dict[str, str | float | bool | None] = {
            "file": yaml_file.name,
            "id": data.get("id", "unknown"),
            "inferred": archetype.value,
            "confidence": round(confidence, 2),
            "existing": existing_archetype,
            "applied": False,
            "method": method,
        }
        # ... rest of loop ...
```

Update display to show method:

```python
# In human-readable output - always show method
console.print(
    f"  {r['file']}: [{conf_color}]{r['inferred']}[/{conf_color}] "
    f"({conf:.0%}) [dim]({r['method']})[/dim] {status}"
)
```

### 3. Add Unit Tests

Location: `tests/unit/services/test_archetype_inference_service.py`

Add new test class:

```python
class TestWeightedRegexScoring:
    """Tests for weighted pattern scoring."""

    def test_strong_signal_scores_higher(self) -> None:
        """P1 (weight 3.0) should contribute more than detected (weight 1.0)."""
        text_p1 = "resolved p1 issue"
        text_detected = "detected an issue"

        score_p1 = score_weighted_regex(text_p1, WorkUnitArchetype.INCIDENT)
        score_detected = score_weighted_regex(text_detected, WorkUnitArchetype.INCIDENT)

        assert score_p1 > score_detected

    def test_multiple_strong_signals_accumulate(self) -> None:
        """Multiple high-weight matches should score higher."""
        text = "resolved p1 outage, triaged and mitigated incident"
        score = score_weighted_regex(text, WorkUnitArchetype.INCIDENT)
        assert score > 0.4


class TestSemanticScoring:
    """Tests for semantic embedding scoring."""

    def test_semantic_matches_conceptually_similar(self) -> None:
        """ATO achievement should match greenfield semantically."""
        from resume_as_code.services.embedding_service import get_embedding_service

        embedding_service = get_embedding_service()
        text = "achieved first-attempt ato for submarine base security authorization"

        greenfield_score = score_semantic(text, WorkUnitArchetype.GREENFIELD, embedding_service)
        incident_score = score_semantic(text, WorkUnitArchetype.INCIDENT, embedding_service)

        # ATO is a first-time achievement (greenfield-like), not an incident
        assert greenfield_score > incident_score


class TestHybridInference:
    """Tests for hybrid inference."""

    def test_uses_regex_when_confident(self) -> None:
        """Should use regex result when confidence is high."""
        from resume_as_code.services.embedding_service import get_embedding_service

        data = {
            "title": "Resolved P1 database outage affecting production",
            "problem": {"statement": "Critical outage detected"},
            "actions": ["Triaged", "Mitigated", "Resolved"],
            "outcome": {"result": "Restored in 30 min"},
            "tags": ["incident-response"],
        }

        embedding_service = get_embedding_service()
        archetype, confidence, method = infer_archetype_hybrid(data, embedding_service)

        assert archetype == WorkUnitArchetype.INCIDENT
        assert method == "regex"

    def test_falls_back_to_semantic(self) -> None:
        """Should use semantic when regex confidence is low."""
        from resume_as_code.services.embedding_service import get_embedding_service

        data = {
            "title": "Achieved first-attempt ATO for submarine base",
            "problem": {"statement": "Required security authorization for facility controls"},
            "actions": ["Developed security documentation", "Conducted assessments"],
            "outcome": {"result": "Obtained Authority to Operate"},
            "tags": ["compliance", "cybersecurity"],
        }

        embedding_service = get_embedding_service()
        archetype, confidence, method = infer_archetype_hybrid(data, embedding_service)

        # Should recognize as greenfield (first-time achievement) via semantics
        assert method == "semantic"
        assert archetype != WorkUnitArchetype.MINIMAL

    def test_returns_fallback_when_uncertain(self) -> None:
        """Should return minimal with fallback method when both approaches fail."""
        from resume_as_code.services.embedding_service import get_embedding_service

        data = {
            "title": "Did some work",
            "problem": {"statement": "Had a task"},
            "actions": ["Worked on it"],
            "outcome": {"result": "Completed"},
            "tags": [],
        }

        embedding_service = get_embedding_service()
        archetype, confidence, method = infer_archetype_hybrid(
            data, embedding_service, regex_threshold=0.5, semantic_threshold=0.5
        )

        assert archetype == WorkUnitArchetype.MINIMAL
        assert method == "fallback"


class TestInferArchetypeFunction:
    """Tests for main infer_archetype function."""

    def test_returns_three_tuple(self) -> None:
        """infer_archetype() should return (archetype, confidence, method)."""
        from resume_as_code.services.embedding_service import get_embedding_service

        data = {
            "title": "Migrated database to cloud",
            "problem": {"statement": "Legacy system"},
            "actions": ["Planned migration", "Executed cutover"],
            "outcome": {"result": "Completed migration"},
            "tags": [],
        }

        embedding_service = get_embedding_service()
        archetype, confidence, method = infer_archetype(data, embedding_service)

        assert archetype == WorkUnitArchetype.MIGRATION
        assert isinstance(confidence, float)
        assert method in ("regex", "semantic", "fallback")
```

---

## Implementation Checklist

- [x] Add weighted patterns dict `ARCHETYPE_PATTERNS_WEIGHTED`
- [x] Add semantic descriptions dict `ARCHETYPE_DESCRIPTIONS`
- [x] Implement `score_weighted_regex()` function
- [x] Implement `score_semantic()` function
- [x] Implement `infer_archetype_hybrid()` function
- [x] Update `infer_archetype()` to use hybrid approach (breaking change to signature)
- [x] Update CLI command to use embedding service
- [x] Add `method` field to JSON output
- [x] Update human-readable output to show method
- [x] Update existing tests for new function signature
- [x] Add unit tests for weighted scoring
- [x] Add unit tests for semantic scoring
- [x] Add unit tests for hybrid inference
- [x] Update CLI integration tests for new output format
- [x] Run `ruff check src tests --fix`
- [x] Run `ruff format src tests`
- [x] Run `mypy src --strict`
- [x] Run `pytest -v`

---

## Files to Create/Modify

| File | Change |
|------|--------|
| `src/resume_as_code/services/archetype_inference_service.py` | Add weighted patterns, semantic descriptions, hybrid function |
| `src/resume_as_code/commands/infer.py` | Add `--hybrid` flag, update output |
| `tests/unit/services/test_archetype_inference_service.py` | Add weighted, semantic, hybrid tests |
| `tests/test_cli.py` | Add CLI integration tests for `--hybrid` |

---

## Dependencies

- **Story 12-3** (review): Base inference service (must be complete)
- **Epic 4**: Existing `EmbeddingService` (already implemented)

---

## Anti-Patterns to Avoid

1. **DO NOT** cache embeddings in this story - use existing cache from EmbeddingService
2. **DO NOT** train custom models - use existing sentence-transformers
3. **DO NOT** require API keys - use local embedding model
4. **DO NOT** add optional regex-only mode - hybrid is the only approach

---

## Performance Considerations

- Semantic inference is slower due to embedding computation
- First run may need to download embedding model (~100MB)
- Existing embedding cache will speed up repeated analyses
- Consider batching embeddings for large work unit collections (future optimization)

---

## Verification Commands

```bash
# Run inference (always uses hybrid approach)
uv run resume infer-archetypes

# Apply with lower threshold
uv run resume infer-archetypes --apply --min-confidence 0.3

# JSON output shows method used for each result
uv run resume --json infer-archetypes

# Run specific tests
uv run pytest tests/unit/services/test_archetype_inference_service.py -v -k "hybrid or weighted or semantic"

# Run full quality check
uv run ruff check src tests --fix && uv run ruff format src tests && uv run mypy src --strict && uv run pytest
```

---

## Example Output

```
Archetype Inference Results

  wu-ato-submarine.yaml: greenfield (67%) (semantic) APPLIED
  wu-aws-migration.yaml: migration (52%) (regex) APPLIED
  wu-led-team-rmf.yaml: leadership (58%) (semantic) APPLIED
  wu-generic-task.yaml: minimal (18%) (fallback) suggested

Total: 4 | Min confidence: 0.5
```

The `method` indicator shows which algorithm produced the result:
- `(regex)` - Weighted regex matched with high confidence
- `(semantic)` - Embedding similarity matched when regex was uncertain
- `(fallback)` - Neither method confident, returned `minimal`

---

## Story Points: 5

**Rationale**: Medium complexity - extends existing service with new scoring methods, reuses existing embedding infrastructure. Main work is in designing good archetype descriptions and tuning thresholds.

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Implemented hybrid regex + semantic embedding approach for archetype inference
- Added `similarity()` method to `EmbeddingService` for cosine similarity between texts
- Weighted regex patterns with signal strengths (1.0-3.0) for each archetype
- Rich semantic descriptions for each archetype for embedding comparison
- Updated `infer_archetype()` to return 3-tuple: (archetype, confidence, method)
- CLI shows method used for each inference: regex, semantic, or fallback
- Fixed CLI integration tests by mocking EmbeddingService for controlled behavior
- All 2787 tests pass, ruff and mypy clean

### File List

- `src/resume_as_code/services/archetype_inference_service.py` - Complete rewrite with hybrid approach
- `src/resume_as_code/services/embedder.py` - Added `similarity()` method
- `src/resume_as_code/commands/infer.py` - Updated for new API and method display
- `tests/unit/services/test_archetype_inference_service.py` - Complete rewrite with new tests
- `tests/unit/test_embedding_service.py` - Added `TestEmbeddingServiceSimilarity` class
- `tests/test_cli.py` - Fixed CLI integration tests with EmbeddingService mocking
