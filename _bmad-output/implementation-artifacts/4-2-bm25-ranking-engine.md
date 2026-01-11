# Story 4.2: BM25 Ranking Engine

Status: ready-for-dev

## Story

As a **system**,
I want **to rank Work Units by relevance to a job description**,
So that **the most relevant accomplishments are selected for the resume**.

## Acceptance Criteria

1. **Given** a set of Work Units and a parsed job description
   **When** the ranker processes them
   **Then** each Work Unit receives a relevance score (0.0 to 1.0)
   **And** Work Units are returned sorted by score (highest first)

2. **Given** a Work Unit with exact keyword matches to the JD
   **When** ranking occurs
   **Then** it scores higher than Work Units with partial or no matches

3. **Given** a Work Unit's title, problem, actions, and outcome fields
   **When** the ranker processes it
   **Then** all text fields contribute to the relevance score

4. **Given** the ranking completes
   **When** I inspect the results
   **Then** each Work Unit has a `match_reasons` list explaining why it ranked where it did

5. **Given** a typical job description and 15+ Work Units
   **When** ranking runs
   **Then** it completes within 3 seconds (NFR1)

6. **Given** the hybrid ranking system uses RRF fusion
   **When** BM25 and semantic results are combined
   **Then** RRF formula is applied: `RRF_Score(d) = Σ (1 / (k + rank_i(d)))`
   **And** k=60 is used as the default parameter
   **And** top_k * 2 results are retrieved from each method before fusion
   **And** ties are broken deterministically by document ID

7. **Given** the embedding model requires instruction prefixes
   **When** Work Units are encoded for similarity
   **Then** they use the `"query: "` prefix
   **And** job descriptions use the `"passage: "` prefix

## Tasks / Subtasks

- [ ] Task 1: Create ranker service (AC: #1, #2, #3)
  - [ ] 1.1: Create `src/resume_as_code/services/ranker.py`
  - [ ] 1.2: Implement `RankingResult` model with score, match_reasons
  - [ ] 1.3: Implement Work Unit text extraction
  - [ ] 1.4: Build BM25 corpus from Work Units
  - [ ] 1.5: Implement BM25 scoring

- [ ] Task 2: Implement semantic ranking (AC: #1, #7)
  - [ ] 2.1: Integrate EmbeddingService from Story 4.1.5
  - [ ] 2.2: Embed Work Units with query prefix
  - [ ] 2.3: Embed JD with passage prefix
  - [ ] 2.4: Compute cosine similarity scores

- [ ] Task 3: Implement RRF fusion (AC: #6)
  - [ ] 3.1: Implement RRF formula with k=60
  - [ ] 3.2: Retrieve top_k * 2 from each method
  - [ ] 3.3: Combine scores using RRF
  - [ ] 3.4: Implement deterministic tie-breaking by ID

- [ ] Task 4: Implement match reason extraction (AC: #4)
  - [ ] 4.1: Identify matching keywords
  - [ ] 4.2: Identify matching skills
  - [ ] 4.3: Format match reasons for display
  - [ ] 4.4: Limit to top 3-5 reasons per Work Unit

- [ ] Task 5: Score normalization (AC: #1)
  - [ ] 5.1: Normalize final scores to 0.0-1.0 range
  - [ ] 5.2: Handle edge cases (no matches, single Work Unit)

- [ ] Task 6: Code quality verification
  - [ ] 6.1: Run `ruff check src tests --fix`
  - [ ] 6.2: Run `ruff format src tests`
  - [ ] 6.3: Run `mypy src --strict` with zero errors
  - [ ] 6.4: Add unit tests for BM25 scoring
  - [ ] 6.5: Add unit tests for RRF fusion
  - [ ] 6.6: Add performance test (NFR1: <3 seconds)

## Dev Notes

### Architecture Compliance

This story implements the core ranking algorithm per Architecture Section 4.2. The hybrid BM25 + semantic approach provides robust relevance scoring.

**Source:** [epics.md#Story 4.2](_bmad-output/planning-artifacts/epics.md)
**Source:** [Architecture Section 4.2 - Ranking Pipeline](_bmad-output/planning-artifacts/architecture.md)

### Dependencies

This story REQUIRES:
- Story 4.1 (Job Description Parser) - Parsed JD model
- Story 4.1.5 (Embedding Service) - Semantic embeddings
- Story 2.1 (Work Unit Schema) - Work Unit models

This story ENABLES:
- Story 4.3 (Plan Command) - Uses ranking results

### RRF Formula

Reciprocal Rank Fusion combines results from multiple ranking methods:

```
RRF_Score(d) = Σ (1 / (k + rank_i(d)))
```

Where:
- `d` is a document (Work Unit)
- `k` is a constant (default: 60)
- `rank_i(d)` is the rank of document d in ranking method i

### Ranker Implementation

**`src/resume_as_code/services/ranker.py`:**

```python
"""Hybrid BM25 + Semantic ranker with RRF fusion."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from rank_bm25 import BM25Okapi

if TYPE_CHECKING:
    from resume_as_code.models.job_description import JobDescription

from resume_as_code.services.embedder import EmbeddingService


@dataclass
class RankingResult:
    """Result of ranking a single Work Unit."""

    work_unit_id: str
    work_unit: dict
    score: float  # 0.0 to 1.0
    bm25_rank: int
    semantic_rank: int
    match_reasons: list[str] = field(default_factory=list)


@dataclass
class RankingOutput:
    """Complete ranking output."""

    results: list[RankingResult]
    jd_keywords: list[str]

    @property
    def selected(self) -> list[RankingResult]:
        """Get selected (top) results."""
        return self.results

    def top(self, n: int) -> list[RankingResult]:
        """Get top N results."""
        return self.results[:n]


class HybridRanker:
    """Hybrid BM25 + Semantic ranker with RRF fusion."""

    RRF_K = 60  # RRF constant

    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        """Initialize the ranker.

        Args:
            embedding_service: Optional embedding service (lazy-loaded if not provided).
        """
        self._embedding_service = embedding_service

    @property
    def embedding_service(self) -> EmbeddingService:
        """Lazy-load embedding service."""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    def rank(
        self,
        work_units: list[dict],
        jd: "JobDescription",
        top_k: int = 10,
    ) -> RankingOutput:
        """Rank Work Units against a job description.

        Args:
            work_units: List of Work Unit dictionaries.
            jd: Parsed JobDescription.
            top_k: Number of top results to return.

        Returns:
            RankingOutput with sorted results.
        """
        if not work_units:
            return RankingOutput(results=[], jd_keywords=jd.keywords)

        # Extract text from Work Units
        wu_texts = [self._extract_text(wu) for wu in work_units]
        wu_ids = [wu.get("id", f"wu-{i}") for i, wu in enumerate(work_units)]

        # BM25 ranking
        bm25_scores, bm25_ranks = self._bm25_rank(wu_texts, jd.text_for_ranking)

        # Semantic ranking
        semantic_scores, semantic_ranks = self._semantic_rank(
            wu_texts, jd.text_for_ranking
        )

        # RRF fusion
        rrf_scores = self._rrf_fusion(bm25_ranks, semantic_ranks, wu_ids)

        # Sort by RRF score
        sorted_indices = sorted(
            range(len(work_units)),
            key=lambda i: (rrf_scores[i], wu_ids[i]),  # Tie-break by ID
            reverse=True,
        )

        # Normalize scores to 0.0-1.0
        max_score = max(rrf_scores) if rrf_scores else 1.0
        normalized_scores = [s / max_score for s in rrf_scores]

        # Build results
        results: list[RankingResult] = []
        for idx in sorted_indices[:top_k * 2]:  # Return more for exclusion display
            match_reasons = self._extract_match_reasons(
                work_units[idx], jd
            )
            results.append(
                RankingResult(
                    work_unit_id=wu_ids[idx],
                    work_unit=work_units[idx],
                    score=normalized_scores[idx],
                    bm25_rank=bm25_ranks[idx],
                    semantic_rank=semantic_ranks[idx],
                    match_reasons=match_reasons,
                )
            )

        return RankingOutput(results=results, jd_keywords=jd.keywords)

    def _extract_text(self, work_unit: dict) -> str:
        """Extract searchable text from Work Unit."""
        parts = [
            work_unit.get("title", ""),
            work_unit.get("problem", {}).get("statement", ""),
            " ".join(work_unit.get("actions", [])),
            work_unit.get("outcome", {}).get("result", ""),
            " ".join(work_unit.get("tags", [])),
            " ".join(work_unit.get("skills_demonstrated", [])),
        ]
        return " ".join(filter(None, parts))

    def _bm25_rank(
        self, documents: list[str], query: str
    ) -> tuple[list[float], list[int]]:
        """Compute BM25 scores and ranks."""
        # Tokenize documents
        tokenized_docs = [doc.lower().split() for doc in documents]
        tokenized_query = query.lower().split()

        # Build BM25 index
        bm25 = BM25Okapi(tokenized_docs)

        # Get scores
        scores = bm25.get_scores(tokenized_query)

        # Compute ranks (1-indexed, lower is better)
        sorted_indices = np.argsort(scores)[::-1]
        ranks = [0] * len(scores)
        for rank, idx in enumerate(sorted_indices, 1):
            ranks[idx] = rank

        return list(scores), ranks

    def _semantic_rank(
        self, documents: list[str], query: str
    ) -> tuple[list[float], list[int]]:
        """Compute semantic similarity scores and ranks."""
        # Embed documents (as queries since they're Work Units)
        doc_embeddings = self.embedding_service.embed_batch(documents, is_query=True)

        # Embed JD (as passage)
        query_embedding = self.embedding_service.embed_passage(query)

        # Compute cosine similarity
        scores = self._cosine_similarity(doc_embeddings, query_embedding)

        # Compute ranks
        sorted_indices = np.argsort(scores)[::-1]
        ranks = [0] * len(scores)
        for rank, idx in enumerate(sorted_indices, 1):
            ranks[idx] = rank

        return list(scores), ranks

    def _cosine_similarity(
        self, doc_embeddings: np.ndarray, query_embedding: np.ndarray
    ) -> list[float]:
        """Compute cosine similarity between documents and query."""
        # Normalize
        doc_norms = np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
        query_norm = np.linalg.norm(query_embedding)

        doc_normalized = doc_embeddings / (doc_norms + 1e-9)
        query_normalized = query_embedding / (query_norm + 1e-9)

        # Dot product
        similarities = doc_normalized @ query_normalized

        return similarities.tolist()

    def _rrf_fusion(
        self,
        bm25_ranks: list[int],
        semantic_ranks: list[int],
        doc_ids: list[str],
    ) -> list[float]:
        """Combine rankings using Reciprocal Rank Fusion."""
        scores = []
        for i in range(len(bm25_ranks)):
            rrf_score = (
                1.0 / (self.RRF_K + bm25_ranks[i]) +
                1.0 / (self.RRF_K + semantic_ranks[i])
            )
            scores.append(rrf_score)
        return scores

    def _extract_match_reasons(
        self, work_unit: dict, jd: "JobDescription"
    ) -> list[str]:
        """Extract reasons why this Work Unit matched."""
        reasons: list[str] = []
        wu_text = self._extract_text(work_unit).lower()

        # Check for skill matches
        matching_skills = [
            skill for skill in jd.skills
            if skill.lower() in wu_text
        ]
        if matching_skills:
            reasons.append(f"Skills: {', '.join(matching_skills[:3])}")

        # Check for keyword matches
        matching_keywords = [
            kw for kw in jd.keywords[:10]
            if kw.lower() in wu_text
        ]
        if matching_keywords:
            reasons.append(f"Keywords: {', '.join(matching_keywords[:3])}")

        # Check for requirement coverage
        wu_tags = set(t.lower() for t in work_unit.get("tags", []))
        jd_skills_set = set(s.lower() for s in jd.skills)
        tag_matches = wu_tags & jd_skills_set
        if tag_matches:
            reasons.append(f"Tags match: {', '.join(list(tag_matches)[:2])}")

        # Limit to top 3 reasons
        return reasons[:3] if reasons else ["Semantic similarity"]
```

### Testing Requirements

**`tests/unit/test_ranker.py`:**

```python
"""Tests for hybrid ranker."""

import pytest
import numpy as np

from resume_as_code.services.ranker import HybridRanker, RankingResult


@pytest.fixture
def sample_work_units() -> list[dict]:
    """Sample Work Units for testing."""
    return [
        {
            "id": "wu-2026-01-10-python-api",
            "title": "Built Python REST API",
            "problem": {"statement": "Needed scalable API"},
            "actions": ["Designed with FastAPI", "Deployed to AWS"],
            "outcome": {"result": "Handles 10K req/sec"},
            "tags": ["python", "api", "aws"],
        },
        {
            "id": "wu-2025-06-15-java-migration",
            "title": "Java Service Migration",
            "problem": {"statement": "Legacy Java service"},
            "actions": ["Upgraded to Java 17"],
            "outcome": {"result": "30% memory reduction"},
            "tags": ["java", "migration"],
        },
        {
            "id": "wu-2024-03-20-kubernetes",
            "title": "Kubernetes Deployment",
            "problem": {"statement": "Manual deployments"},
            "actions": ["Set up K8s cluster", "Created Helm charts"],
            "outcome": {"result": "Automated deployments"},
            "tags": ["kubernetes", "devops"],
        },
    ]


@pytest.fixture
def sample_jd():
    """Sample parsed JD."""
    from resume_as_code.models.job_description import JobDescription

    return JobDescription(
        raw_text="Looking for Python developer with AWS and API experience",
        skills=["python", "aws", "api", "kubernetes"],
        keywords=["python", "aws", "api", "scalable"],
        requirements=[],
    )


class TestHybridRanker:
    """Tests for HybridRanker."""

    def test_ranks_work_units(self, sample_work_units, sample_jd):
        """Should rank Work Units by relevance."""
        ranker = HybridRanker()
        output = ranker.rank(sample_work_units, sample_jd, top_k=3)

        assert len(output.results) > 0
        # Python API should rank highest (matches python, aws, api)
        assert output.results[0].work_unit_id == "wu-2026-01-10-python-api"

    def test_scores_normalized(self, sample_work_units, sample_jd):
        """Scores should be between 0 and 1."""
        ranker = HybridRanker()
        output = ranker.rank(sample_work_units, sample_jd)

        for result in output.results:
            assert 0.0 <= result.score <= 1.0

    def test_includes_match_reasons(self, sample_work_units, sample_jd):
        """Should include match reasons."""
        ranker = HybridRanker()
        output = ranker.rank(sample_work_units, sample_jd)

        top_result = output.results[0]
        assert len(top_result.match_reasons) > 0

    def test_empty_work_units(self, sample_jd):
        """Should handle empty Work Units list."""
        ranker = HybridRanker()
        output = ranker.rank([], sample_jd)

        assert output.results == []


class TestRRFFusion:
    """Tests for RRF fusion."""

    def test_rrf_formula(self):
        """RRF should combine ranks correctly."""
        ranker = HybridRanker()

        # Document ranked 1st in both methods
        bm25_ranks = [1, 2, 3]
        semantic_ranks = [1, 3, 2]
        doc_ids = ["a", "b", "c"]

        scores = ranker._rrf_fusion(bm25_ranks, semantic_ranks, doc_ids)

        # First doc should have highest score (rank 1 in both)
        assert scores[0] > scores[1]
        assert scores[0] > scores[2]
```

### Verification Commands

```bash
# Test ranking (requires work units and JD)
python -c "
from resume_as_code.services.ranker import HybridRanker
from resume_as_code.services.jd_parser import parse_jd_text

jd = parse_jd_text('Senior Python Engineer with AWS experience needed')
work_units = [
    {'id': 'wu-1', 'title': 'Python API', 'tags': ['python', 'aws']},
    {'id': 'wu-2', 'title': 'Java Service', 'tags': ['java']},
]

ranker = HybridRanker()
output = ranker.rank(work_units, jd)

for r in output.results:
    print(f'{r.work_unit_id}: {r.score:.2%} - {r.match_reasons}')
"

# Code quality
ruff check src tests --fix
mypy src --strict
pytest tests/unit/test_ranker.py -v
```

### References

- [Source: epics.md#Story 4.2](_bmad-output/planning-artifacts/epics.md)
- [Source: architecture.md](_bmad-output/planning-artifacts/architecture.md)
- [Source: project-context.md](_bmad-output/project-context.md)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

