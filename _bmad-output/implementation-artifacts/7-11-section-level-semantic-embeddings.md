# Story 7.11: Section-Level Semantic Embeddings

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **job seeker**,
I want **my skills section matched against JD requirements and my outcomes matched against JD responsibilities**,
So that **semantic matching is more precise and relevant**.

## Acceptance Criteria

1. **Given** a work unit with distinct sections (problem, actions, outcome, skills)
   **When** embedding for semantic search
   **Then** each section is embedded separately

2. **Given** section embeddings are computed
   **When** matching against JD
   **Then** work unit skills embed against JD skills section
   **And** work unit outcomes embed against JD requirements section

3. **Given** section-level similarity scores
   **When** aggregating to final score
   **Then** weighted formula applies:
   - Outcome match: 40%
   - Actions match: 30%
   - Skills match: 20%
   - Title match: 10%

4. **Given** a work unit with strong skills match but weak experience match
   **When** ranking
   **Then** the weighted aggregate reflects partial relevance

5. **Given** embedding cache exists
   **When** section embeddings are computed
   **Then** each section is cached separately with section identifier

## Tasks / Subtasks

- [x] Task 1: Add section embedding methods to EmbeddingService (AC: #1, #5)
  - [x] 1.1 Create `embed_work_unit_sections()` method
  - [x] 1.2 Extract sections: title, problem, actions, outcome, skills
  - [x] 1.3 Embed each section separately
  - [x] 1.4 Cache with section-prefixed keys for efficiency

- [x] Task 2: Add JD section embedding (AC: #2)
  - [x] 2.1 Create `embed_jd_sections()` method
  - [x] 2.2 Extract JD sections: requirements, skills, responsibilities
  - [x] 2.3 Embed JD sections separately

- [x] Task 3: Implement sectioned semantic ranking (AC: #2, #3, #4)
  - [x] 3.1 Create `_semantic_rank_sectioned()` method in HybridRanker
  - [x] 3.2 Compute cross-section similarity scores
  - [x] 3.3 Apply weighted aggregation formula
  - [x] 3.4 Add section weights to ScoringWeights config

- [x] Task 4: Integrate with rank() method (AC: #3, #4)
  - [x] 4.1 Add config option to enable sectioned semantic ranking
  - [x] 4.2 Fall back to full-document ranking when disabled
  - [x] 4.3 Ensure backward compatibility

- [x] Task 5: Add tests and quality checks
  - [x] 5.1 Unit tests for section embedding
  - [x] 5.2 Unit tests for weighted aggregation
  - [x] 5.3 Integration tests for sectioned ranking
  - [x] 5.4 Run `ruff check` and `mypy --strict`

## Dev Notes

### Current State Analysis

**Existing Implementation:**

`embedder.py:77-91` - Current embedding:
```python
def embed_query(self, text: str) -> NDArray[np.float32]:
    """Embed text as a query (for Work Units)."""
    prefixed = f"query: {text}" if "e5" in self.model_name.lower() else text
    return self._embed_with_cache(prefixed)
```

`ranker.py:164-181` - Current semantic ranking:
```python
def _semantic_rank(self, documents: list[str], query: str) -> list[int]:
    """Compute semantic similarity ranks."""
    # Embed documents (full text)
    doc_embeddings = self.embedding_service.embed_batch(documents, is_query=True)
    # Single embedding for entire JD
    query_embedding = self.embedding_service.embed_passage(query)
    # Cosine similarity
    scores = self._cosine_similarity(doc_embeddings, query_embedding)
```

**Gap:** Full-document embedding dilutes significance of individual sections. Skills buried in long experience text have less semantic weight.

### Implementation Pattern

**Section Embedding Types:**
```python
# models/embeddings.py (new file)
from __future__ import annotations

from typing import Literal, TypedDict

import numpy as np
from numpy.typing import NDArray


WorkUnitSection = Literal["title", "problem", "actions", "outcome", "skills"]
JDSection = Literal["requirements", "skills", "responsibilities", "full"]


class WorkUnitSectionEmbeddings(TypedDict, total=False):
    """Embeddings for each work unit section."""

    title: NDArray[np.float32]
    problem: NDArray[np.float32]
    actions: NDArray[np.float32]
    outcome: NDArray[np.float32]
    skills: NDArray[np.float32]


class JDSectionEmbeddings(TypedDict, total=False):
    """Embeddings for each JD section."""

    requirements: NDArray[np.float32]
    skills: NDArray[np.float32]
    responsibilities: NDArray[np.float32]
    full: NDArray[np.float32]
```

**EmbeddingService Extensions:**
```python
# services/embedder.py - add to EmbeddingService class

def embed_work_unit_sections(
    self,
    work_unit: dict[str, Any],
) -> WorkUnitSectionEmbeddings:
    """Generate separate embeddings for each work unit section.

    Embeds title, problem, actions, outcome, and skills separately
    for more precise semantic matching.

    Args:
        work_unit: Work Unit dictionary.

    Returns:
        Dictionary of section -> embedding arrays.
    """
    from resume_as_code.utils.work_unit_text import extract_skills_text

    sections: dict[str, str] = {}

    # Title
    if title := work_unit.get("title"):
        title_str = str(title).strip()
        if title_str:
            sections["title"] = title_str

    # Problem (statement + context)
    if problem := work_unit.get("problem"):
        if isinstance(problem, dict):
            problem_text = " ".join(filter(None, [
                problem.get("statement", ""),
                problem.get("context", ""),
            ]))
        else:
            problem_text = str(problem)
        if problem_text.strip():
            sections["problem"] = problem_text

    # Actions
    if actions := work_unit.get("actions"):
        if isinstance(actions, list):
            actions_text = " ".join(str(a) for a in actions)
        else:
            actions_text = str(actions)
        if actions_text.strip():
            sections["actions"] = actions_text

    # Outcome (result + quantified_impact)
    if outcome := work_unit.get("outcome"):
        if isinstance(outcome, dict):
            outcome_text = " ".join(filter(None, [
                outcome.get("result", ""),
                outcome.get("quantified_impact", ""),
            ]))
        else:
            outcome_text = str(outcome)
        if outcome_text.strip():
            sections["outcome"] = outcome_text

    # Skills (tags + skills_demonstrated)
    if skills_text := extract_skills_text(work_unit):
        sections["skills"] = skills_text

    # Embed each section with section-prefixed cache key
    embeddings: WorkUnitSectionEmbeddings = {}
    wu_id = work_unit.get("id", "unknown")

    for section_name, text in sections.items():
        # Prefix for cache differentiation: "[section:wu_id] text"
        cache_key = f"[{section_name}:{wu_id}] {text}"
        embedding = self.embed_query(cache_key)
        embeddings[section_name] = embedding  # type: ignore[literal-required]

    return embeddings


def embed_jd_sections(
    self,
    jd: JobDescription,
) -> JDSectionEmbeddings:
    """Generate separate embeddings for each JD section.

    Embeds requirements, skills, and responsibilities separately.

    Args:
        jd: Parsed JobDescription.

    Returns:
        Dictionary of section -> embedding arrays.
    """
    embeddings: JDSectionEmbeddings = {}

    # Requirements text (main matching target)
    if jd.requirements_text:
        embeddings["requirements"] = self.embed_passage(
            f"[jd:requirements] {jd.requirements_text}"
        )

    # Skills list as text
    if jd.skills:
        skills_text = " ".join(jd.skills)
        embeddings["skills"] = self.embed_passage(
            f"[jd:skills] {skills_text}"
        )

    # Full text for fallback
    if jd.text_for_ranking:
        embeddings["full"] = self.embed_passage(jd.text_for_ranking)

    return embeddings
```

**Config Extension:**
```python
# models/config.py - add to ScoringWeights

class ScoringWeights(BaseModel):
    # ... existing fields ...

    # Section-level semantic weights (Story 7.11)
    use_sectioned_semantic: bool = Field(
        default=False,
        description="Enable section-level semantic matching (more precise but slower).",
    )
    section_outcome_weight: float = Field(
        default=0.4, ge=0.0, le=1.0,
        description="Weight for outcome section in semantic scoring",
    )
    section_actions_weight: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="Weight for actions section in semantic scoring",
    )
    section_skills_weight: float = Field(
        default=0.2, ge=0.0, le=1.0,
        description="Weight for skills section in semantic scoring",
    )
    section_title_weight: float = Field(
        default=0.1, ge=0.0, le=1.0,
        description="Weight for title section in semantic scoring",
    )

    @model_validator(mode="after")
    def validate_section_weights_sum(self) -> ScoringWeights:
        """Validate section weights sum to ~1.0."""
        if self.use_sectioned_semantic:
            total = (
                self.section_outcome_weight
                + self.section_actions_weight
                + self.section_skills_weight
                + self.section_title_weight
            )
            if not (0.99 <= total <= 1.01):
                raise ValueError(
                    f"Section weights must sum to 1.0, got {total:.2f}"
                )
        return self
```

**Sectioned Semantic Ranking:**
```python
# services/ranker.py - add to HybridRanker

def _semantic_rank_sectioned(
    self,
    work_units: list[dict[str, Any]],
    jd: JobDescription,
    scoring_weights: ScoringWeights,
) -> list[int]:
    """Semantic ranking with section-level matching.

    Computes cross-section similarity:
    - Work unit outcome ↔ JD requirements
    - Work unit actions ↔ JD requirements
    - Work unit skills ↔ JD skills
    - Work unit title ↔ JD full text

    Args:
        work_units: List of Work Unit dictionaries.
        jd: Parsed JobDescription.
        scoring_weights: Weights configuration.

    Returns:
        List of ranks (1-indexed, lower is better).
    """
    # Embed JD sections
    jd_sections = self.embedding_service.embed_jd_sections(jd)
    jd_requirements = jd_sections.get("requirements", jd_sections.get("full"))
    jd_skills = jd_sections.get("skills", jd_sections.get("full"))
    jd_full = jd_sections.get("full")

    # Fallback if no requirements embedding
    if jd_requirements is None:
        jd_requirements = jd_full
    if jd_skills is None:
        jd_skills = jd_full

    scores: list[float] = []

    for wu in work_units:
        wu_sections = self.embedding_service.embed_work_unit_sections(wu)

        # Cross-section matching
        outcome_score = 0.0
        actions_score = 0.0
        skills_score = 0.0
        title_score = 0.0

        # Outcome ↔ Requirements
        if "outcome" in wu_sections and jd_requirements is not None:
            outcome_score = self._cosine_sim_single(
                wu_sections["outcome"], jd_requirements
            )

        # Actions ↔ Requirements
        if "actions" in wu_sections and jd_requirements is not None:
            actions_score = self._cosine_sim_single(
                wu_sections["actions"], jd_requirements
            )

        # Skills ↔ JD Skills
        if "skills" in wu_sections and jd_skills is not None:
            skills_score = self._cosine_sim_single(
                wu_sections["skills"], jd_skills
            )

        # Title ↔ Full JD
        if "title" in wu_sections and jd_full is not None:
            title_score = self._cosine_sim_single(
                wu_sections["title"], jd_full
            )

        # Weighted aggregation
        weighted_score = (
            scoring_weights.section_outcome_weight * outcome_score
            + scoring_weights.section_actions_weight * actions_score
            + scoring_weights.section_skills_weight * skills_score
            + scoring_weights.section_title_weight * title_score
        )
        scores.append(weighted_score)

    # Convert to ranks (1-indexed, lower is better)
    sorted_indices = np.argsort(scores)[::-1]
    ranks = [0] * len(scores)
    for rank, idx in enumerate(sorted_indices, 1):
        ranks[idx] = rank

    return ranks


def _cosine_sim_single(
    self,
    vec1: NDArray[np.float32],
    vec2: NDArray[np.float32],
) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vec1: First embedding vector.
        vec2: Second embedding vector.

    Returns:
        Cosine similarity (0.0 to 1.0, normalized).
    """
    # Normalize vectors
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 < 1e-9 or norm2 < 1e-9:
        return 0.0

    similarity = float(np.dot(vec1, vec2) / (norm1 * norm2))

    # Normalize from [-1, 1] to [0, 1]
    return (similarity + 1.0) / 2.0
```

**Updated _semantic_rank Method:**
```python
def _semantic_rank(
    self,
    documents: list[str],
    query: str,
    work_units: list[dict[str, Any]] | None = None,
    jd: JobDescription | None = None,
    scoring_weights: ScoringWeights | None = None,
) -> list[int]:
    """Compute semantic similarity ranks.

    Uses sectioned ranking if enabled and work_units/jd provided,
    otherwise falls back to full-document ranking.
    """
    # Use sectioned ranking if enabled
    if (
        scoring_weights is not None
        and scoring_weights.use_sectioned_semantic
        and work_units is not None
        and jd is not None
    ):
        return self._semantic_rank_sectioned(work_units, jd, scoring_weights)

    # Fallback: full-document ranking (existing implementation)
    doc_embeddings = self.embedding_service.embed_batch(documents, is_query=True)
    query_embedding = self.embedding_service.embed_passage(query)
    scores = self._cosine_similarity(doc_embeddings, query_embedding)

    sorted_indices = np.argsort(scores)[::-1]
    ranks = [0] * len(scores)
    for rank, idx in enumerate(sorted_indices, 1):
        ranks[idx] = rank

    return ranks
```

### Testing Standards

```python
# tests/unit/services/test_embedder_sections.py
import pytest
from unittest.mock import MagicMock, patch

import numpy as np

from resume_as_code.services.embedder import EmbeddingService


@pytest.fixture
def mock_embedder() -> EmbeddingService:
    """Create embedder with mocked model."""
    embedder = EmbeddingService()
    # Mock the model to return consistent embeddings
    mock_model = MagicMock()
    mock_model.encode.return_value = np.random.rand(384).astype(np.float32)
    embedder._model = mock_model
    embedder._model_hash = "test_hash"
    return embedder


class TestWorkUnitSectionEmbedding:
    """Tests for work unit section embedding."""

    def test_embeds_all_sections(self, mock_embedder: EmbeddingService) -> None:
        """All work unit sections are embedded separately."""
        wu = {
            "id": "wu-test",
            "title": "Led platform migration",
            "problem": {"statement": "Legacy system was slow", "context": "High traffic"},
            "actions": ["Analyzed bottlenecks", "Implemented caching"],
            "outcome": {"result": "50% faster", "quantified_impact": "p99 < 100ms"},
            "tags": ["python", "aws"],
            "skills_demonstrated": [{"name": "Docker"}],
        }

        sections = mock_embedder.embed_work_unit_sections(wu)

        assert "title" in sections
        assert "problem" in sections
        assert "actions" in sections
        assert "outcome" in sections
        assert "skills" in sections

    def test_handles_missing_sections(self, mock_embedder: EmbeddingService) -> None:
        """Gracefully handles work units with missing sections."""
        wu = {
            "id": "wu-minimal",
            "title": "Quick fix",
            # No problem, actions, outcome, skills
        }

        sections = mock_embedder.embed_work_unit_sections(wu)

        assert "title" in sections
        assert "problem" not in sections
        assert "outcome" not in sections

    def test_sections_are_cached_separately(self, mock_embedder: EmbeddingService) -> None:
        """Each section uses unique cache key."""
        wu = {
            "id": "wu-cache-test",
            "title": "Same title",
            "outcome": {"result": "Same outcome"},
        }

        # Mock cache to track calls
        mock_embedder._cache = MagicMock()
        mock_embedder._cache.get.return_value = None

        mock_embedder.embed_work_unit_sections(wu)

        # Verify cache was queried with section-specific keys
        cache_calls = mock_embedder._cache.get.call_args_list
        cache_keys = [call[0][0] for call in cache_calls]

        # Keys should include section prefix
        assert any("[title:" in key for key in cache_keys)
        assert any("[outcome:" in key for key in cache_keys)
```

```python
# tests/unit/services/test_ranker_sectioned.py
import pytest
from unittest.mock import MagicMock

import numpy as np

from resume_as_code.models.config import ScoringWeights
from resume_as_code.models.job_description import JobDescription
from resume_as_code.services.ranker import HybridRanker


@pytest.fixture
def mock_ranker() -> HybridRanker:
    """Create ranker with mocked embedding service."""
    mock_embedder = MagicMock()
    # Return random but consistent embeddings
    np.random.seed(42)
    mock_embedder.embed_work_unit_sections.return_value = {
        "title": np.random.rand(384).astype(np.float32),
        "outcome": np.random.rand(384).astype(np.float32),
        "actions": np.random.rand(384).astype(np.float32),
        "skills": np.random.rand(384).astype(np.float32),
    }
    mock_embedder.embed_jd_sections.return_value = {
        "requirements": np.random.rand(384).astype(np.float32),
        "skills": np.random.rand(384).astype(np.float32),
        "full": np.random.rand(384).astype(np.float32),
    }
    return HybridRanker(embedding_service=mock_embedder)


class TestSectionedSemanticRanking:
    """Tests for section-level semantic ranking."""

    def test_uses_sectioned_when_enabled(self, mock_ranker: HybridRanker) -> None:
        """Sectioned ranking is used when enabled."""
        weights = ScoringWeights(
            use_sectioned_semantic=True,
            section_outcome_weight=0.4,
            section_actions_weight=0.3,
            section_skills_weight=0.2,
            section_title_weight=0.1,
        )

        jd = JobDescription(
            title="Senior Engineer",
            text_for_ranking="Python developer needed",
            requirements_text="5+ years Python",
            skills=["Python", "AWS"],
            keywords=["Python"],
            experience_level="SENIOR",
        )

        work_units = [
            {"id": "wu-1", "title": "Python work"},
            {"id": "wu-2", "title": "Java work"},
        ]

        ranks = mock_ranker._semantic_rank_sectioned(work_units, jd, weights)

        assert len(ranks) == 2
        assert all(r >= 1 for r in ranks)

    def test_weighted_aggregation(self, mock_ranker: HybridRanker) -> None:
        """Section scores are weighted according to config."""
        weights = ScoringWeights(
            use_sectioned_semantic=True,
            section_outcome_weight=0.4,
            section_actions_weight=0.3,
            section_skills_weight=0.2,
            section_title_weight=0.1,
        )

        # Verify weights sum to 1.0
        total = (
            weights.section_outcome_weight
            + weights.section_actions_weight
            + weights.section_skills_weight
            + weights.section_title_weight
        )
        assert abs(total - 1.0) < 0.01

    def test_fallback_when_disabled(self, mock_ranker: HybridRanker) -> None:
        """Falls back to full-document ranking when disabled."""
        weights = ScoringWeights(use_sectioned_semantic=False)

        # Full-document method should be used
        mock_ranker._embedding_service.embed_batch.return_value = np.zeros((2, 384))
        mock_ranker._embedding_service.embed_passage.return_value = np.zeros(384)

        ranks = mock_ranker._semantic_rank(
            ["doc1", "doc2"],
            "query",
            work_units=[{"id": "wu-1"}, {"id": "wu-2"}],
            jd=None,
            scoring_weights=weights,
        )

        # Should call embed_batch (full-document), not embed_work_unit_sections
        assert mock_ranker._embedding_service.embed_batch.called


class TestSectionWeightsValidation:
    """Tests for section weight validation."""

    def test_valid_weights_sum_to_one(self) -> None:
        """Valid weights that sum to 1.0 are accepted."""
        weights = ScoringWeights(
            use_sectioned_semantic=True,
            section_outcome_weight=0.4,
            section_actions_weight=0.3,
            section_skills_weight=0.2,
            section_title_weight=0.1,
        )
        assert weights is not None

    def test_invalid_weights_rejected(self) -> None:
        """Weights that don't sum to 1.0 are rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="sum to 1.0"):
            ScoringWeights(
                use_sectioned_semantic=True,
                section_outcome_weight=0.5,
                section_actions_weight=0.5,
                section_skills_weight=0.5,
                section_title_weight=0.5,  # Sum = 2.0
            )
```

### Research Basis

Pinecone research shows section-level embeddings reduce noise and improve precision. Full-document embedding dilutes significance of individual sections.

**Recommended Section Weights:**
- Outcome: 40% - Results are most predictive of job fit
- Actions: 30% - What the candidate did
- Skills: 20% - Technical skill alignment
- Title: 10% - Role alignment

### Project Context Rules

From `project-context.md`:
- Run `ruff check` and `mypy --strict` before completing
- Use Rich console for CLI output, never `print()`
- Type hints required on all public functions
- Use `|` union syntax (Python 3.10+)

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-7-schema-data-model-refactoring.md#Story 7.11]
- [Source: src/resume_as_code/services/embedder.py - existing EmbeddingService]
- [Source: src/resume_as_code/services/embedding_cache.py - existing cache]
- [Source: src/resume_as_code/services/ranker.py:164-181 - existing _semantic_rank]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- AC#1: Section embedding via `embed_work_unit_sections()` - extracts title, problem, actions, outcome, skills separately
- AC#2: JD section embedding via `embed_jd_sections()` - embeds requirements, skills, full text; cross-matched with WU sections
- AC#3: Weighted aggregation formula implemented: Outcome 40%, Actions 30%, Skills 20%, Title 10%
- AC#4: Partial relevance reflected via weighted scores - strong skills with weak experience shows proportional match
- AC#5: Section-prefixed cache keys: `[section:wu_id] text` format for cache differentiation
- Feature gated by `use_sectioned_semantic` flag (default: False) for backward compatibility
- All 1998 tests pass, ruff clean, mypy --strict clean

### File List

**New Files:**
- `src/resume_as_code/models/embeddings.py` - WorkUnitSectionEmbeddings, JDSectionEmbeddings types
- `tests/unit/services/test_embedder_sections.py` - 14 tests for section embedding
- `tests/unit/services/test_ranker_sectioned.py` - 12 tests for sectioned ranking

**Modified Files:**
- `src/resume_as_code/services/embedder.py` - Added embed_work_unit_sections(), embed_jd_sections()
- `src/resume_as_code/services/ranker.py` - Added _semantic_rank_sectioned(), _cosine_sim_single(), updated rank()
- `src/resume_as_code/models/config.py` - Added section weights to ScoringWeights with validation
- `src/resume_as_code/models/job_description.py` - Added requirements_text property
