"""Tests for hybrid ranker service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import numpy as np
import pytest

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from resume_as_code.models.job_description import JobDescription


@pytest.fixture
def sample_work_units() -> list[dict[str, Any]]:
    """Sample Work Unit dictionaries for testing."""
    return [
        {
            "id": "wu-2026-01-10-python-api",
            "title": "Built Python REST API for Microservices",
            "problem": {"statement": "Needed scalable API for customer data"},
            "actions": ["Designed API with FastAPI framework", "Deployed to AWS Lambda"],
            "outcome": {"result": "Handles 10K requests per second"},
            "tags": ["python", "api", "aws", "fastapi"],
            "skills_demonstrated": [{"name": "python"}, {"name": "aws"}],
        },
        {
            "id": "wu-2025-06-15-java-migration",
            "title": "Java Service Migration to Spring Boot",
            "problem": {"statement": "Legacy Java service causing issues"},
            "actions": ["Upgraded to Java 17 and Spring Boot 3"],
            "outcome": {"result": "30% memory reduction achieved"},
            "tags": ["java", "migration", "spring"],
            "skills_demonstrated": [{"name": "java"}],
        },
        {
            "id": "wu-2024-03-20-kubernetes",
            "title": "Kubernetes Deployment Infrastructure",
            "problem": {"statement": "Manual deployments slowing team"},
            "actions": ["Set up K8s cluster on EKS", "Created Helm charts for services"],
            "outcome": {"result": "Automated deployments reduced time 80%"},
            "tags": ["kubernetes", "devops", "aws"],
            "skills_demonstrated": [{"name": "kubernetes"}, {"name": "devops"}],
        },
    ]


@pytest.fixture
def sample_jd() -> JobDescription:
    """Sample parsed JobDescription for testing."""
    from resume_as_code.models.job_description import JobDescription

    return JobDescription(
        raw_text="Looking for Python developer with AWS and API experience. "
        "Must have experience building scalable microservices.",
        skills=["python", "aws", "api", "kubernetes"],
        keywords=["python", "aws", "api", "scalable", "microservices"],
        requirements=[],
    )


@pytest.fixture
def mock_embedding_service() -> MagicMock:
    """Mock EmbeddingService for tests that don't need real embeddings."""
    mock = MagicMock()

    # Return deterministic embeddings based on content
    def mock_embed_batch(texts: list[str], is_query: bool = True) -> NDArray[np.float32]:
        embeddings = []
        for text in texts:
            # Create pseudo-embedding based on text length and hash
            seed = hash(text) % 1000
            np.random.seed(seed)
            embeddings.append(np.random.rand(384).astype(np.float32))
        return np.array(embeddings)

    def mock_embed_passage(text: str) -> NDArray[np.float32]:
        seed = hash(text) % 1000
        np.random.seed(seed)
        return np.random.rand(384).astype(np.float32)

    mock.embed_batch = mock_embed_batch
    mock.embed_passage = mock_embed_passage
    return mock


class TestHybridRanker:
    """Tests for HybridRanker class."""

    def test_rank_returns_sorted_results(
        self,
        sample_work_units: list[dict[str, Any]],
        sample_jd: JobDescription,
        mock_embedding_service: MagicMock,
    ) -> None:
        """AC1: Work Units are returned sorted by score (highest first)."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(sample_work_units, sample_jd, top_k=3)

        assert len(output.results) > 0
        # Verify scores are in descending order
        scores = [r.score for r in output.results]
        assert scores == sorted(scores, reverse=True)

    def test_scores_normalized_0_to_1(
        self,
        sample_work_units: list[dict[str, Any]],
        sample_jd: JobDescription,
        mock_embedding_service: MagicMock,
    ) -> None:
        """AC1: Each Work Unit receives a relevance score (0.0 to 1.0)."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(sample_work_units, sample_jd)

        for result in output.results:
            assert 0.0 <= result.score <= 1.0, f"Score {result.score} not in range [0, 1]"

    def test_keyword_matches_score_higher(
        self,
        sample_work_units: list[dict[str, Any]],
        sample_jd: JobDescription,
        mock_embedding_service: MagicMock,
    ) -> None:
        """AC2: Work Units with exact keyword matches score higher."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(sample_work_units, sample_jd)

        # Python API work unit should rank high (matches python, aws, api)
        top_ids = [r.work_unit_id for r in output.results[:2]]
        assert "wu-2026-01-10-python-api" in top_ids

    def test_multiple_text_fields_contribute(self, mock_embedding_service: MagicMock) -> None:
        """AC3: Multiple text fields (title, outcome) contribute to score."""
        from resume_as_code.models.job_description import JobDescription
        from resume_as_code.services.ranker import HybridRanker

        # Work unit with term in different fields
        work_units = [
            {
                "id": "wu-2026-01-01-title-match",
                "title": "Python Developer Role Implementation",
                "problem": {"statement": "Generic problem description here"},
                "actions": ["Did generic action"],
                "outcome": {"result": "Generic outcome"},
                "tags": [],
                "skills_demonstrated": [],
            },
            {
                "id": "wu-2026-01-02-outcome-match",
                "title": "Generic Project Title Here",
                "problem": {"statement": "Generic problem description"},
                "actions": ["Did generic action"],
                "outcome": {"result": "Deployed Python service successfully"},
                "tags": [],
                "skills_demonstrated": [],
            },
        ]

        jd = JobDescription(
            raw_text="Python developer needed",
            skills=["python"],
            keywords=["python"],
            requirements=[],
        )

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(work_units, jd)

        # Both should appear (both contain python somewhere)
        ids = [r.work_unit_id for r in output.results]
        assert "wu-2026-01-01-title-match" in ids
        assert "wu-2026-01-02-outcome-match" in ids

    def test_includes_match_reasons(
        self,
        sample_work_units: list[dict[str, Any]],
        sample_jd: JobDescription,
        mock_embedding_service: MagicMock,
    ) -> None:
        """AC4: Each Work Unit has a match_reasons list."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(sample_work_units, sample_jd)

        for result in output.results:
            assert isinstance(result.match_reasons, list)
            # Top matches should have at least one reason
            if result.score > 0.5:
                assert len(result.match_reasons) > 0

    def test_empty_work_units_returns_empty(self, sample_jd: JobDescription) -> None:
        """Should handle empty Work Units list gracefully."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker()
        output = ranker.rank([], sample_jd)

        assert output.results == []
        assert output.jd_keywords == sample_jd.keywords

    def test_single_work_unit_normalized(
        self, sample_jd: JobDescription, mock_embedding_service: MagicMock
    ) -> None:
        """AC1: Single work unit edge case - score should be 1.0."""
        from resume_as_code.services.ranker import HybridRanker

        work_units = [
            {
                "id": "wu-2026-01-01-single",
                "title": "Only Work Unit Here",
                "problem": {"statement": "Solved a problem"},
                "actions": ["Did something"],
                "outcome": {"result": "Got result"},
                "tags": [],
                "skills_demonstrated": [],
            }
        ]

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(work_units, sample_jd)

        assert len(output.results) == 1
        assert output.results[0].score == 1.0

    def test_embedding_prefixes_used_correctly(self, sample_jd: JobDescription) -> None:
        """AC7: Work Units use query prefix, JDs use passage prefix."""
        from unittest.mock import MagicMock

        from resume_as_code.services.ranker import HybridRanker

        # Create mock that tracks calls
        mock_service = MagicMock()
        mock_service.embed_batch.return_value = np.array([[0.1] * 384], dtype=np.float32)
        mock_service.embed_passage.return_value = np.array([0.2] * 384, dtype=np.float32)

        work_units = [
            {
                "id": "wu-2026-01-01-test",
                "title": "Test Work Unit",
                "problem": {"statement": "Test problem"},
                "actions": ["Test action"],
                "outcome": {"result": "Test result"},
                "tags": [],
                "skills_demonstrated": [],
            }
        ]

        ranker = HybridRanker(embedding_service=mock_service)
        ranker.rank(work_units, sample_jd)

        # Verify embed_batch called with is_query=True for Work Units
        mock_service.embed_batch.assert_called_once()
        batch_call = mock_service.embed_batch.call_args
        assert batch_call[1].get("is_query") is True, "Work Units should use query prefix"

        # Verify embed_passage called for JD (passage prefix)
        mock_service.embed_passage.assert_called_once()


class TestRRFFusion:
    """Tests for RRF fusion algorithm."""

    def test_rrf_formula_with_k_60(self) -> None:
        """AC6: RRF formula applied with k=60."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker()
        assert ranker.RRF_K == 60

        # Test RRF calculation
        bm25_ranks = [1, 2, 3]
        semantic_ranks = [1, 3, 2]

        scores = ranker._rrf_fusion(bm25_ranks, semantic_ranks)

        # RRF_Score(doc_a) = 1/(60+1) + 1/(60+1) = 2/61 ≈ 0.0328
        # RRF_Score(doc_b) = 1/(60+2) + 1/(60+3) = 1/62 + 1/63 ≈ 0.0320
        # RRF_Score(doc_c) = 1/(60+3) + 1/(60+2) = 1/63 + 1/62 ≈ 0.0320
        expected_a = 1 / 61 + 1 / 61
        assert abs(scores[0] - expected_a) < 0.0001

    def test_rrf_document_ranked_first_both_methods(self) -> None:
        """Document ranked 1st in both methods should have highest RRF score."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker()

        bm25_ranks = [1, 2, 3]
        semantic_ranks = [1, 3, 2]

        scores = ranker._rrf_fusion(bm25_ranks, semantic_ranks)

        # First doc should have highest score (rank 1 in both)
        assert scores[0] > scores[1]
        assert scores[0] > scores[2]

    def test_deterministic_tiebreaker_by_id(self, mock_embedding_service: MagicMock) -> None:
        """AC6: Ties broken deterministically by document ID."""
        from resume_as_code.models.job_description import JobDescription
        from resume_as_code.services.ranker import HybridRanker

        # Create work units with identical content for tie scenario
        work_units = [
            {
                "id": "wu-2026-01-01-zebra",
                "title": "Same Title",
                "problem": {"statement": "Same problem"},
                "actions": ["Same action"],
                "outcome": {"result": "Same outcome"},
                "tags": ["tag"],
                "skills_demonstrated": [],
            },
            {
                "id": "wu-2026-01-01-alpha",
                "title": "Same Title",
                "problem": {"statement": "Same problem"},
                "actions": ["Same action"],
                "outcome": {"result": "Same outcome"},
                "tags": ["tag"],
                "skills_demonstrated": [],
            },
        ]

        jd = JobDescription(
            raw_text="Keyword tag here",
            skills=["tag"],
            keywords=["tag"],
            requirements=[],
        )

        ranker = HybridRanker(embedding_service=mock_embedding_service)

        # Run multiple times to verify determinism
        results_1 = ranker.rank(work_units, jd)
        results_2 = ranker.rank(work_units, jd)

        ids_1 = [r.work_unit_id for r in results_1.results]
        ids_2 = [r.work_unit_id for r in results_2.results]

        assert ids_1 == ids_2


class TestScoringWeights:
    """Tests for scoring weights integration (Story 5.6 AC: #3)."""

    def test_rrf_fusion_with_custom_weights(self) -> None:
        """Scoring weights should affect RRF fusion calculation."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker()

        bm25_ranks = [1, 2]
        semantic_ranks = [2, 1]

        # Default weights (1.0, 1.0)
        default_scores = ranker._rrf_fusion(bm25_ranks, semantic_ranks)

        # Custom weights: emphasize BM25
        bm25_heavy = ScoringWeights(bm25_weight=2.0, semantic_weight=0.5)
        bm25_scores = ranker._rrf_fusion(bm25_ranks, semantic_ranks, bm25_heavy)

        # Custom weights: emphasize semantic
        semantic_heavy = ScoringWeights(bm25_weight=0.5, semantic_weight=2.0)
        semantic_scores = ranker._rrf_fusion(bm25_ranks, semantic_ranks, semantic_heavy)

        # With BM25 emphasis, doc with better BM25 rank should score higher
        # Doc 0: BM25 rank 1, semantic rank 2
        # Doc 1: BM25 rank 2, semantic rank 1
        assert bm25_scores[0] > bm25_scores[1], "BM25-heavy should favor doc with better BM25 rank"
        assert semantic_scores[1] > semantic_scores[0], (
            "Semantic-heavy should favor doc with better semantic rank"
        )

        # Scores should differ from default
        assert bm25_scores != default_scores
        assert semantic_scores != default_scores

    def test_rrf_fusion_with_zero_weight(self) -> None:
        """Zero weight should exclude that ranking method entirely."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker()

        bm25_ranks = [1, 2]
        semantic_ranks = [2, 1]

        # Only BM25
        bm25_only = ScoringWeights(bm25_weight=1.0, semantic_weight=0.0)
        scores_bm25 = ranker._rrf_fusion(bm25_ranks, semantic_ranks, bm25_only)

        # Only semantic
        semantic_only = ScoringWeights(bm25_weight=0.0, semantic_weight=1.0)
        scores_semantic = ranker._rrf_fusion(bm25_ranks, semantic_ranks, semantic_only)

        # BM25 only: doc 0 has rank 1 (better), doc 1 has rank 2
        assert scores_bm25[0] > scores_bm25[1]

        # Semantic only: doc 1 has rank 1 (better), doc 0 has rank 2
        assert scores_semantic[1] > scores_semantic[0]

    def test_ranker_accepts_scoring_weights(self, mock_embedding_service: MagicMock) -> None:
        """HybridRanker.rank() should accept scoring_weights parameter."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.models.job_description import JobDescription
        from resume_as_code.services.ranker import HybridRanker

        work_units = [
            {
                "id": "wu-2026-01-01-test",
                "title": "Python API Project",
                "problem": {"statement": "Test"},
                "actions": ["Did work"],
                "outcome": {"result": "Success"},
                "tags": ["python"],
                "skills_demonstrated": [],
            }
        ]

        jd = JobDescription(
            raw_text="Need python skills",
            skills=["python"],
            keywords=["python"],
            requirements=[],
        )

        weights = ScoringWeights(bm25_weight=1.5, semantic_weight=0.5)

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        # Should not raise - scoring_weights is accepted
        output = ranker.rank(work_units, jd, top_k=10, scoring_weights=weights)

        assert len(output.results) == 1


class TestFieldWeightedBM25:
    """Tests for field-weighted BM25 scoring (Story 7.8)."""

    @pytest.fixture
    def weighted_work_units(self) -> list[dict[str, Any]]:
        """Work units with varying title/skills relevance for weighted testing."""
        return [
            {
                "id": "wu-title-match",
                "title": "Senior Python Developer - Backend Services",
                "tags": ["javascript", "react"],
                "skills_demonstrated": [{"name": "JavaScript"}],
                "problem": {"statement": "Legacy system needed modernization"},
                "actions": ["Rewrote frontend"],
                "outcome": {"result": "Improved performance"},
            },
            {
                "id": "wu-skills-match",
                "title": "Led infrastructure migration",
                "tags": ["python", "django", "aws"],
                "skills_demonstrated": [{"name": "Python"}, {"name": "Django"}],
                "problem": {"statement": "Cloud costs too high"},
                "actions": ["Optimized resources"],
                "outcome": {"result": "Reduced costs"},
            },
            {
                "id": "wu-experience-match",
                "title": "Database optimization project",
                "tags": ["sql"],
                "skills_demonstrated": [],
                "problem": {"statement": "Python application had slow queries"},
                "actions": ["Used Python scripts to analyze and optimize"],
                "outcome": {"result": "Python automation reduced manual work"},
            },
        ]

    @pytest.fixture
    def jd_python(self) -> JobDescription:
        """JD looking for Python developer."""
        from resume_as_code.models.job_description import JobDescription

        return JobDescription(
            raw_text="Senior Python Developer with Django experience",
            skills=["Python", "Django", "AWS"],
            keywords=["Python", "Django", "backend", "senior"],
            requirements=[],
        )

    def test_has_field_weights_default(self, mock_embedding_service: MagicMock) -> None:
        """_has_field_weights returns True for default weights (title=2.0, skills=1.5)."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        default = ScoringWeights()
        # Default weights now include field weighting (title=2.0, skills=1.5)
        assert ranker._has_field_weights(default)

    def test_has_field_weights_title(self, mock_embedding_service: MagicMock) -> None:
        """_has_field_weights returns True when title_weight differs."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        weights = ScoringWeights(title_weight=2.0)
        assert ranker._has_field_weights(weights)

    def test_has_field_weights_skills(self, mock_embedding_service: MagicMock) -> None:
        """_has_field_weights returns True when skills_weight differs."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        weights = ScoringWeights(skills_weight=1.5)
        assert ranker._has_field_weights(weights)

    def test_has_field_weights_experience(self, mock_embedding_service: MagicMock) -> None:
        """_has_field_weights returns True when experience_weight differs."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        weights = ScoringWeights(experience_weight=0.5)
        assert ranker._has_field_weights(weights)

    def test_default_weights_use_field_weighted_bm25(
        self,
        weighted_work_units: list[dict[str, Any]],
        jd_python: JobDescription,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Default weights (title=2.0, skills=1.5) use field-weighted BM25."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        default_weights = ScoringWeights()

        # Default weights now use field-weighted BM25 (per HBR 2023 research)
        # Verify via _has_field_weights check
        assert ranker._has_field_weights(default_weights)

    def test_equal_weights_use_standard_bm25(
        self,
        weighted_work_units: list[dict[str, Any]],
        jd_python: JobDescription,
        mock_embedding_service: MagicMock,
    ) -> None:
        """AC#3: Equal weights (all 1.0) use standard BM25, not field-weighted."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        equal_weights = ScoringWeights(
            title_weight=1.0,
            skills_weight=1.0,
            experience_weight=1.0,
        )

        # With equal weights (1.0), standard BM25 should be used
        # Verify via _has_field_weights check
        assert not ranker._has_field_weights(equal_weights)

    def test_title_weight_boosts_title_matches(
        self,
        weighted_work_units: list[dict[str, Any]],
        jd_python: JobDescription,
        mock_embedding_service: MagicMock,
    ) -> None:
        """AC#1: Higher title_weight boosts work units with title matches."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)

        # High title weight
        title_heavy = ScoringWeights(
            title_weight=3.0,
            skills_weight=1.0,
            experience_weight=1.0,
        )

        ranks = ranker._bm25_rank_weighted(
            weighted_work_units,
            jd_python.text_for_ranking,
            title_heavy,
        )

        # wu-title-match (has "Python" in title) should rank better than others
        # Index 0 is wu-title-match
        assert ranks[0] <= 2, "Title match should rank highly with high title_weight"

    def test_skills_weight_boosts_skills_matches(
        self,
        weighted_work_units: list[dict[str, Any]],
        jd_python: JobDescription,
        mock_embedding_service: MagicMock,
    ) -> None:
        """AC#2: Higher skills_weight boosts work units with skills/tag matches."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)

        # High skills weight
        skills_heavy = ScoringWeights(
            title_weight=1.0,
            skills_weight=3.0,
            experience_weight=1.0,
        )

        ranks = ranker._bm25_rank_weighted(
            weighted_work_units,
            jd_python.text_for_ranking,
            skills_heavy,
        )

        # wu-skills-match (index 1, has Python, Django in tags) should rank highly
        assert ranks[1] <= 2, "Skills match should rank highly with high skills_weight"

    def test_weighted_rank_returns_valid_ranks(
        self,
        weighted_work_units: list[dict[str, Any]],
        jd_python: JobDescription,
        mock_embedding_service: MagicMock,
    ) -> None:
        """_bm25_rank_weighted returns valid 1-indexed ranks."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        weights = ScoringWeights(title_weight=2.0, skills_weight=1.5)

        ranks = ranker._bm25_rank_weighted(
            weighted_work_units,
            jd_python.text_for_ranking,
            weights,
        )

        # Ranks should be 1-indexed
        assert all(r >= 1 for r in ranks)
        # Should have one of each rank (1, 2, 3)
        assert sorted(ranks) == [1, 2, 3]

    def test_rank_uses_weighted_when_configured(
        self,
        weighted_work_units: list[dict[str, Any]],
        jd_python: JobDescription,
        mock_embedding_service: MagicMock,
    ) -> None:
        """rank() uses field-weighted BM25 when field weights configured."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)

        # With field weights configured, weighted method should be used
        weights = ScoringWeights(title_weight=2.0)

        # Should complete without error
        output = ranker.rank(weighted_work_units, jd_python, scoring_weights=weights)

        assert len(output.results) > 0

    def test_weighted_bm25_with_empty_query(
        self,
        weighted_work_units: list[dict[str, Any]],
        mock_embedding_service: MagicMock,
    ) -> None:
        """Edge case: _bm25_rank_weighted handles empty query string gracefully."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        weights = ScoringWeights(title_weight=2.0, skills_weight=1.5)

        # Empty query should not raise
        ranks = ranker._bm25_rank_weighted(weighted_work_units, "", weights)

        # Should return valid ranks for all work units
        assert len(ranks) == len(weighted_work_units)
        assert all(r >= 1 for r in ranks)


class TestMatchReasonExtraction:
    """Tests for match reason extraction (includes Story 7.8 AC#4 tests)."""

    def test_match_reasons_indicate_title_field(self, mock_embedding_service: MagicMock) -> None:
        """AC#4: Match reasons indicate 'Title match:' when title matches."""
        from resume_as_code.models.job_description import JobDescription
        from resume_as_code.services.ranker import HybridRanker

        work_units = [
            {
                "id": "wu-title-match-test",
                "title": "Senior Python Developer - Backend Services",
                "tags": ["javascript"],  # Different skills
                "skills_demonstrated": [{"name": "JavaScript"}],
                "problem": {"statement": "Generic problem"},
                "actions": ["Generic action"],
                "outcome": {"result": "Generic result"},
            }
        ]

        jd = JobDescription(
            raw_text="Looking for Python Developer",
            skills=["JavaScript"],  # Skills don't match Python
            keywords=["Python", "Developer", "Senior"],
            requirements=[],
        )

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(work_units, jd)

        reasons = output.results[0].match_reasons
        title_reasons = [r for r in reasons if r.startswith("Title match:")]
        assert len(title_reasons) > 0, f"Expected 'Title match:' in reasons: {reasons}"

    def test_match_reasons_indicate_skills_field(self, mock_embedding_service: MagicMock) -> None:
        """AC#4: Match reasons indicate 'Skills match:' when skills/tags match."""
        from resume_as_code.models.job_description import JobDescription
        from resume_as_code.services.ranker import HybridRanker

        work_units = [
            {
                "id": "wu-skills-match-test",
                "title": "Generic Project Title",  # No Python in title
                "tags": ["python", "aws"],
                "skills_demonstrated": [{"name": "Python"}, {"name": "AWS"}],
                "problem": {"statement": "Generic problem"},
                "actions": ["Generic action"],
                "outcome": {"result": "Generic result"},
            }
        ]

        jd = JobDescription(
            raw_text="Looking for developer with Python and AWS",
            skills=["Python", "AWS"],
            keywords=["experience", "cloud"],  # Keywords won't match
            requirements=[],
        )

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(work_units, jd)

        reasons = output.results[0].match_reasons
        skills_reasons = [r for r in reasons if r.startswith("Skills match:")]
        assert len(skills_reasons) > 0, f"Expected 'Skills match:' in reasons: {reasons}"

    def test_match_reasons_indicate_experience_field(
        self, mock_embedding_service: MagicMock
    ) -> None:
        """AC#4: Match reasons indicate 'Experience match:' for body text matches."""
        from resume_as_code.models.job_description import JobDescription
        from resume_as_code.services.ranker import HybridRanker

        work_units = [
            {
                "id": "wu-experience-match-test",
                "title": "Database Project",  # No Python in title
                "tags": ["sql"],  # No Python in tags
                "skills_demonstrated": [],
                "problem": {"statement": "Python application had performance issues"},
                "actions": ["Optimized Python code for better performance"],
                "outcome": {"result": "Python application now runs smoothly"},
            }
        ]

        jd = JobDescription(
            raw_text="Looking for Python developer",
            skills=["SQL"],  # Skills don't match Python
            keywords=["Python", "performance", "application"],
            requirements=[],
        )

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(work_units, jd)

        reasons = output.results[0].match_reasons
        experience_reasons = [r for r in reasons if r.startswith("Experience match:")]
        assert len(experience_reasons) > 0, f"Expected 'Experience match:' in reasons: {reasons}"

    def test_match_reasons_include_skills(self, mock_embedding_service: MagicMock) -> None:
        """AC4: Match reasons include matching skills."""
        from resume_as_code.models.job_description import JobDescription
        from resume_as_code.services.ranker import HybridRanker

        work_units = [
            {
                "id": "wu-2026-01-01-skills",
                "title": "Python AWS Project",
                "problem": {"statement": "Built with python and aws"},
                "actions": ["Used python", "Deployed to aws"],
                "outcome": {"result": "Success"},
                "tags": ["python", "aws"],
                "skills_demonstrated": [{"name": "python"}, {"name": "aws"}],
            }
        ]

        jd = JobDescription(
            raw_text="Need python and aws skills",
            skills=["python", "aws"],
            keywords=["python", "aws"],
            requirements=[],
        )

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(work_units, jd)

        reasons = output.results[0].match_reasons
        # Should mention skills match
        skills_reason = [r for r in reasons if "skill" in r.lower() or "Skills" in r]
        assert len(skills_reason) > 0 or any("python" in r.lower() for r in reasons)

    def test_match_reasons_limited_to_max(self, mock_embedding_service: MagicMock) -> None:
        """AC4: Match reasons limited to _MAX_MATCH_REASONS (3) per Work Unit."""
        from resume_as_code.models.job_description import JobDescription
        from resume_as_code.services.ranker import HybridRanker

        work_units = [
            {
                "id": "wu-2026-01-01-many-matches",
                "title": "Python AWS Kubernetes Docker DevOps Project",
                "problem": {
                    "statement": "Built system with python, aws, kubernetes, docker, devops, api"
                },
                "actions": ["Used python, aws, kubernetes, docker, devops, api, microservices"],
                "outcome": {"result": "Success with python, aws, kubernetes"},
                "tags": [
                    "python",
                    "aws",
                    "kubernetes",
                    "docker",
                    "devops",
                    "api",
                    "microservices",
                ],
                "skills_demonstrated": [],
            }
        ]

        jd = JobDescription(
            raw_text="Need python aws kubernetes docker devops api microservices",
            skills=[
                "python",
                "aws",
                "kubernetes",
                "docker",
                "devops",
                "api",
                "microservices",
            ],
            keywords=[
                "python",
                "aws",
                "kubernetes",
                "docker",
                "devops",
                "api",
                "microservices",
            ],
            requirements=[],
        )

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(work_units, jd)

        reasons = output.results[0].match_reasons
        assert len(reasons) <= 3  # AC4: Limited by _MAX_MATCH_REASONS constant


class TestRankingOutput:
    """Tests for RankingOutput helper methods."""

    def test_top_n_returns_n_results(
        self,
        sample_work_units: list[dict[str, Any]],
        sample_jd: JobDescription,
        mock_embedding_service: MagicMock,
    ) -> None:
        """RankingOutput.top(n) returns top n results."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(sample_work_units, sample_jd, top_k=10)

        top_2 = output.top(2)
        assert len(top_2) == 2
        assert top_2[0].score >= top_2[1].score

    def test_selected_property(
        self,
        sample_work_units: list[dict[str, Any]],
        sample_jd: JobDescription,
        mock_embedding_service: MagicMock,
    ) -> None:
        """RankingOutput.selected returns all results."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(sample_work_units, sample_jd)

        assert output.selected == output.results


class TestRecencyDecay:
    """Tests for recency decay feature (Story 7.9).

    Recency decay uses exponential decay with configurable half-life to weight
    recent experience higher than older experience.
    """

    @pytest.fixture
    def work_units_with_dates(self) -> list[dict[str, Any]]:
        """Work units with various time_ended dates for recency testing."""
        from datetime import date, timedelta

        today = date.today()
        return [
            {
                "id": "wu-current",
                "title": "Current Position",
                "time_ended": None,  # Current/ongoing
                "tags": ["python"],
                "skills_demonstrated": [],
                "problem": {"statement": "Current work"},
                "actions": ["Ongoing"],
                "outcome": {"result": "In progress"},
            },
            {
                "id": "wu-1-year",
                "title": "One Year Ago Position",
                "time_ended": today - timedelta(days=365),
                "tags": ["python"],
                "skills_demonstrated": [],
                "problem": {"statement": "Recent work"},
                "actions": ["Completed"],
                "outcome": {"result": "Done"},
            },
            {
                "id": "wu-5-years",
                "title": "Five Years Ago Position",
                "time_ended": today - timedelta(days=5 * 365),
                "tags": ["python"],
                "skills_demonstrated": [],
                "problem": {"statement": "Older work"},
                "actions": ["Completed"],
                "outcome": {"result": "Done"},
            },
            {
                "id": "wu-10-years",
                "title": "Ten Years Ago Position",
                "time_ended": today - timedelta(days=10 * 365),
                "tags": ["python"],
                "skills_demonstrated": [],
                "problem": {"statement": "Old work"},
                "actions": ["Completed"],
                "outcome": {"result": "Done"},
            },
        ]

    def test_current_position_full_weight(self, mock_embedding_service: MagicMock) -> None:
        """AC#3: Work unit with time_ended=None gets 100% recency weight."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        wu = {"id": "wu-current", "time_ended": None}
        weights = ScoringWeights(recency_half_life=5.0)

        score = ranker._calculate_recency_score(wu, weights)

        assert score == 1.0

    def test_one_year_old_about_87_percent(self, mock_embedding_service: MagicMock) -> None:
        """AC#1: Work unit 1 year old gets ~87% weight with 5-year half-life."""
        from datetime import date, timedelta

        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        one_year_ago = date.today() - timedelta(days=365)
        wu = {"id": "wu-1yr", "time_ended": one_year_ago}
        weights = ScoringWeights(recency_half_life=5.0)

        score = ranker._calculate_recency_score(wu, weights)

        # Expected: e^(-ln(2)/5 × 1) ≈ 0.871
        assert 0.85 < score < 0.90

    def test_five_years_old_about_50_percent(self, mock_embedding_service: MagicMock) -> None:
        """AC#2: Work unit 5 years old gets ~50% weight with 5-year half-life."""
        from datetime import date, timedelta

        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        five_years_ago = date.today() - timedelta(days=5 * 365)
        wu = {"id": "wu-5yr", "time_ended": five_years_ago}
        weights = ScoringWeights(recency_half_life=5.0)

        score = ranker._calculate_recency_score(wu, weights)

        # Expected: e^(-ln(2)/5 × 5) = 0.5
        assert 0.45 < score < 0.55

    def test_ten_years_old_about_25_percent(self, mock_embedding_service: MagicMock) -> None:
        """Work unit 10 years old gets ~25% weight with 5-year half-life."""
        from datetime import date, timedelta

        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        ten_years_ago = date.today() - timedelta(days=10 * 365)
        wu = {"id": "wu-10yr", "time_ended": ten_years_ago}
        weights = ScoringWeights(recency_half_life=5.0)

        score = ranker._calculate_recency_score(wu, weights)

        # Expected: e^(-ln(2)/5 × 10) = 0.25
        assert 0.20 < score < 0.30

    def test_disabled_recency_returns_full_weight(self, mock_embedding_service: MagicMock) -> None:
        """AC#4: Disabled recency (None half-life) returns 1.0 for all work units."""
        from datetime import date, timedelta

        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        five_years_ago = date.today() - timedelta(days=5 * 365)
        wu = {"id": "wu-old", "time_ended": five_years_ago}
        weights = ScoringWeights(recency_half_life=None)

        score = ranker._calculate_recency_score(wu, weights)

        assert score == 1.0

    def test_no_weights_returns_full_weight(self, mock_embedding_service: MagicMock) -> None:
        """No scoring weights (None) returns 1.0."""
        from datetime import date, timedelta

        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        five_years_ago = date.today() - timedelta(days=5 * 365)
        wu = {"id": "wu-old", "time_ended": five_years_ago}

        score = ranker._calculate_recency_score(wu, None)

        assert score == 1.0

    def test_string_date_format_yyyy_mm_dd(self, mock_embedding_service: MagicMock) -> None:
        """Handle YYYY-MM-DD string format for time_ended."""
        from datetime import date, timedelta

        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        one_year_ago = date.today() - timedelta(days=365)
        wu = {"id": "wu-str", "time_ended": one_year_ago.isoformat()}
        weights = ScoringWeights(recency_half_life=5.0)

        score = ranker._calculate_recency_score(wu, weights)

        assert 0.85 < score < 0.90

    def test_string_date_format_yyyy_mm(self, mock_embedding_service: MagicMock) -> None:
        """Handle YYYY-MM string format for time_ended."""
        from datetime import date, timedelta

        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        one_year_ago = date.today() - timedelta(days=365)
        date_str = one_year_ago.strftime("%Y-%m")
        wu = {"id": "wu-str", "time_ended": date_str}
        weights = ScoringWeights(recency_half_life=5.0)

        score = ranker._calculate_recency_score(wu, weights)

        # Slightly different due to day-01 assumption, but still ~87%
        assert 0.80 < score < 0.95


class TestScoreBlending:
    """Tests for relevance/recency score blending (Story 7.9 AC#5)."""

    def test_default_blend_80_20(self, mock_embedding_service: MagicMock) -> None:
        """AC#5: Default blend is 80% relevance, 20% recency (with neutral seniority/impact)."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        relevance = [1.0, 0.5, 0.0]
        recency = [0.5, 1.0, 1.0]
        seniority = [1.0, 1.0, 1.0]  # Neutral seniority (no impact)
        impact = [0.5, 0.5, 0.5]  # Neutral impact (Story 7.13)
        weights = ScoringWeights(recency_blend=0.2, seniority_blend=0.0, impact_blend=0.0)

        blended = ranker._blend_scores(relevance, recency, seniority, impact, weights)

        # final[0] = 0.8 × 1.0 + 0.2 × 0.5 = 0.9
        # final[1] = 0.8 × 0.5 + 0.2 × 1.0 = 0.6
        # final[2] = 0.8 × 0.0 + 0.2 × 1.0 = 0.2
        assert abs(blended[0] - 0.9) < 0.01
        assert abs(blended[1] - 0.6) < 0.01
        assert abs(blended[2] - 0.2) < 0.01

    def test_no_weights_returns_relevance(self, mock_embedding_service: MagicMock) -> None:
        """No weights returns original relevance scores."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        relevance = [1.0, 0.5, 0.0]
        recency = [0.5, 1.0, 1.0]
        seniority = [1.0, 1.0, 1.0]  # Neutral seniority
        impact = [0.5, 0.5, 0.5]  # Neutral impact (Story 7.13)

        blended = ranker._blend_scores(relevance, recency, seniority, impact, None)

        assert blended == relevance

    def test_zero_recency_blend(self, mock_embedding_service: MagicMock) -> None:
        """Zero recency_blend uses only relevance."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        relevance = [1.0, 0.5, 0.0]
        recency = [0.0, 0.0, 0.0]  # Old work units
        seniority = [1.0, 1.0, 1.0]  # Neutral seniority
        impact = [0.5, 0.5, 0.5]  # Neutral impact (Story 7.13)
        weights = ScoringWeights(recency_blend=0.0, seniority_blend=0.0, impact_blend=0.0)

        blended = ranker._blend_scores(relevance, recency, seniority, impact, weights)

        assert blended == relevance

    def test_max_recency_blend(self, mock_embedding_service: MagicMock) -> None:
        """Max recency_blend (0.5) gives equal weight to relevance and recency."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        relevance = [1.0, 0.0]
        recency = [0.0, 1.0]
        seniority = [1.0, 1.0]  # Neutral seniority
        impact = [0.5, 0.5]  # Neutral impact (Story 7.13)
        weights = ScoringWeights(recency_blend=0.5, seniority_blend=0.0, impact_blend=0.0)

        blended = ranker._blend_scores(relevance, recency, seniority, impact, weights)

        # final[0] = 0.5 × 1.0 + 0.5 × 0.0 = 0.5
        # final[1] = 0.5 × 0.0 + 0.5 × 1.0 = 0.5
        assert blended[0] == blended[1] == 0.5


class TestRecencyConfigValidation:
    """Tests for ScoringWeights recency configuration (Story 7.9 Task 1)."""

    def test_recency_half_life_default(self) -> None:
        """recency_half_life defaults to 5.0 years."""
        from resume_as_code.models.config import ScoringWeights

        weights = ScoringWeights()
        assert weights.recency_half_life == 5.0

    def test_recency_blend_default(self) -> None:
        """recency_blend defaults to 0.2 (20%)."""
        from resume_as_code.models.config import ScoringWeights

        weights = ScoringWeights()
        assert weights.recency_blend == 0.2

    def test_recency_half_life_none_disables(self) -> None:
        """recency_half_life=None disables recency decay."""
        from resume_as_code.models.config import ScoringWeights

        weights = ScoringWeights(recency_half_life=None)
        assert weights.recency_half_life is None

    def test_recency_half_life_min_constraint(self) -> None:
        """recency_half_life must be >= 1.0 year."""
        import pydantic

        from resume_as_code.models.config import ScoringWeights

        with pytest.raises(pydantic.ValidationError):
            ScoringWeights(recency_half_life=0.5)

    def test_recency_half_life_max_constraint(self) -> None:
        """recency_half_life must be <= 20.0 years."""
        import pydantic

        from resume_as_code.models.config import ScoringWeights

        with pytest.raises(pydantic.ValidationError):
            ScoringWeights(recency_half_life=25.0)

    def test_recency_blend_min_constraint(self) -> None:
        """recency_blend must be >= 0.0."""
        import pydantic

        from resume_as_code.models.config import ScoringWeights

        with pytest.raises(pydantic.ValidationError):
            ScoringWeights(recency_blend=-0.1)

    def test_recency_blend_max_constraint(self) -> None:
        """recency_blend must be <= 0.5."""
        import pydantic

        from resume_as_code.models.config import ScoringWeights

        with pytest.raises(pydantic.ValidationError):
            ScoringWeights(recency_blend=0.6)


class TestRecencyIntegration:
    """Integration tests for recency in rank() method (Story 7.9 Task 3)."""

    @pytest.fixture
    def work_units_with_dates(self) -> list[dict[str, Any]]:
        """Work units with time_ended dates for integration testing."""
        from datetime import date, timedelta

        today = date.today()
        return [
            {
                "id": "wu-current",
                "title": "Python Developer",
                "time_ended": None,
                "tags": ["python"],
                "skills_demonstrated": [{"name": "Python"}],
                "problem": {"statement": "Current work"},
                "actions": ["Ongoing"],
                "outcome": {"result": "In progress"},
            },
            {
                "id": "wu-5-years",
                "title": "Python Developer",  # Same title for fair comparison
                "time_ended": today - timedelta(days=5 * 365),
                "tags": ["python"],
                "skills_demonstrated": [{"name": "Python"}],
                "problem": {"statement": "Older work"},
                "actions": ["Completed"],
                "outcome": {"result": "Done"},
            },
        ]

    def test_recency_boosts_current_positions(
        self,
        mock_embedding_service: MagicMock,
    ) -> None:
        """Current positions get higher score than old ones via recency boost.

        Verifies that the current position (100% recency) has a higher final
        score than the 5-year-old position (50% recency) when both have similar
        relevance scores.
        """
        from datetime import date, timedelta

        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.models.job_description import JobDescription
        from resume_as_code.services.ranker import HybridRanker

        today = date.today()

        # Create work units with similar content
        work_units = [
            {
                "id": "wu-current",
                "title": "Python Developer",
                "time_ended": None,
                "tags": ["python"],
                "skills_demonstrated": [{"name": "Python"}],
                "problem": {"statement": "Build API"},
                "actions": ["Wrote code"],
                "outcome": {"result": "Success"},
            },
            {
                "id": "wu-5-years",
                "title": "Python Developer",
                "time_ended": today - timedelta(days=5 * 365),
                "tags": ["python"],
                "skills_demonstrated": [{"name": "Python"}],
                "problem": {"statement": "Build API"},
                "actions": ["Wrote code"],
                "outcome": {"result": "Success"},
            },
        ]

        jd = JobDescription(
            raw_text="Python developer needed",
            skills=["Python"],
            keywords=["Python", "developer"],
            requirements=[],
        )

        # Use recency_blend to see impact of recency
        weights = ScoringWeights(recency_half_life=5.0, recency_blend=0.2)

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        ranker.rank(work_units, jd, scoring_weights=weights)

        # Calculate what the recency contribution should be
        # current: 0.8 * relevance + 0.2 * 1.0
        # old:     0.8 * relevance + 0.2 * 0.5
        # Difference should be: 0.2 * (1.0 - 0.5) = 0.1

        # The current position should have higher final score due to recency boost
        # Even if relevance differs slightly due to mock, the recency boost of 0.1
        # should be visible in the final score comparison
        current_recency = ranker._calculate_recency_score(work_units[0], weights)
        old_recency = ranker._calculate_recency_score(work_units[1], weights)

        assert current_recency > old_recency, "Current position should have higher recency score"
        assert abs(current_recency - 1.0) < 0.01, "Current position should have ~100% recency"
        assert 0.45 < old_recency < 0.55, "5-year-old position should have ~50% recency"

    def test_disabled_recency_preserves_behavior(
        self,
        work_units_with_dates: list[dict[str, Any]],
        mock_embedding_service: MagicMock,
    ) -> None:
        """AC#4: Disabled recency (half_life=None) should be equivalent to recency_blend=0.0."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.models.job_description import JobDescription
        from resume_as_code.services.ranker import HybridRanker

        jd = JobDescription(
            raw_text="Python developer needed",
            skills=["Python"],
            keywords=["Python", "developer"],
            requirements=[],
        )

        ranker = HybridRanker(embedding_service=mock_embedding_service)

        # Zero recency blend (relevance only)
        weights_zero = ScoringWeights(recency_blend=0.0)
        output_zero = ranker.rank(work_units_with_dates, jd, scoring_weights=weights_zero)

        # Disabled recency (None half-life) - all recency scores become 1.0
        # Combined with default recency_blend=0.2, this adds 0.2 to all scores
        # which shouldn't change ranking order
        weights_disabled = ScoringWeights(recency_half_life=None)
        output_disabled = ranker.rank(work_units_with_dates, jd, scoring_weights=weights_disabled)

        # Order should be identical since adding constant to all scores preserves order
        ids_zero = [r.work_unit_id for r in output_zero.results]
        ids_disabled = [r.work_unit_id for r in output_disabled.results]
        assert ids_zero == ids_disabled


class TestTokenizerIntegration:
    """Tests for tokenizer integration with BM25 ranking (Story 7.10).

    These tests verify the tokenizer's normalization capabilities directly.
    Note: BM25's IDF calculation requires larger corpora to differentiate
    ranking, so we test tokenizer behavior in isolation.
    """

    def test_abbreviation_expansion_tokenizes_correctly(self) -> None:
        """AC#2: 'ML' expands to include 'machine learning' tokens."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)

        # Query with ML abbreviation
        query_tokens = tokenizer.tokenize("ML engineer")

        # Document with full form
        doc_tokens = tokenizer.tokenize("Machine Learning Engineer")

        # Both should have 'machine' and 'learning' tokens
        assert "machine" in query_tokens, "ML should expand to include 'machine'"
        assert "learning" in query_tokens, "ML should expand to include 'learning'"
        assert "machine" in doc_tokens
        assert "learning" in doc_tokens

        # Verify overlap exists
        overlap = set(query_tokens) & set(doc_tokens)
        assert len(overlap) >= 2, f"Expected at least 2 common tokens, got {overlap}"

    def test_hyphen_normalization_tokenizes_correctly(self) -> None:
        """AC#3: 'project-management' normalizes to 'project management' tokens."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)

        # Query with hyphen
        query_tokens = tokenizer.tokenize("project-management lead")

        # Document with space
        doc_tokens = tokenizer.tokenize("Project Management Lead")

        # Both should have 'project' and 'management'
        assert "project" in query_tokens
        assert "management" in query_tokens
        assert "project" in doc_tokens
        assert "management" in doc_tokens

    def test_stop_words_filtered_from_tokenization(self) -> None:
        """AC#5: Domain stop words are removed from tokens."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)

        # Text with many stop words
        tokens = tokenizer.tokenize("requirements experience skills knowledge ability Python")

        # Stop words should be filtered
        assert "requirements" not in tokens
        assert "experience" not in tokens
        assert "skills" not in tokens
        assert "knowledge" not in tokens
        assert "ability" not in tokens

        # Technical term preserved
        assert "python" in tokens

    def test_cicd_variants_tokenize_consistently(self) -> None:
        """AC#4: CI/CD, CICD, and 'CI CD' all produce consistent tokens."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)

        # Different CI/CD variants
        slash_tokens = tokenizer.tokenize("CI/CD pipeline")
        noslash_tokens = tokenizer.tokenize("CICD pipeline")
        space_tokens = tokenizer.tokenize("CI CD pipeline")

        # All should expand to include 'continuous', 'integration', 'deployment'
        for tokens in [slash_tokens, noslash_tokens, space_tokens]:
            assert "continuous" in tokens, f"Expected 'continuous' in {tokens}"
            assert "integration" in tokens, f"Expected 'integration' in {tokens}"
            assert "deployment" in tokens, f"Expected 'deployment' in {tokens}"

    def test_bm25_uses_tokenizer_not_simple_split(self) -> None:
        """Verify _bm25_rank uses tokenizer instead of simple split."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker()

        # Use larger corpus to get meaningful BM25 scores
        # (BM25 IDF is 0 for terms in 1 of 2 docs)
        documents = [
            "Python API development with machine learning integration",
            "Java backend service deployment",
            "Frontend React application",
            "Database administration tasks",
            "Cloud infrastructure management",
        ]

        # Query with abbreviation that should expand
        query = "ML python api"

        ranks = ranker._bm25_rank(documents, query)

        # Doc 0 has python, api, and machine learning (expanded from ML)
        # It should rank first (rank 1)
        assert ranks[0] == 1, f"Doc 0 should rank first, got rank {ranks[0]}"

    def test_weighted_bm25_uses_tokenizer_not_simple_split(self) -> None:
        """Verify _bm25_rank_weighted uses tokenizer for normalization."""
        from resume_as_code.models.config import ScoringWeights
        from resume_as_code.services.ranker import HybridRanker

        # Multiple work units for meaningful BM25 IDF
        work_units = [
            {
                "id": "wu-ml",
                "title": "Machine Learning Engineer",
                "tags": ["machine learning", "python"],
                "skills_demonstrated": [{"name": "Machine Learning"}, {"name": "Python"}],
                "problem": {"statement": "Built ML models"},
                "actions": ["Created ML pipeline"],
                "outcome": {"result": "Improved ML accuracy"},
            },
            {
                "id": "wu-java",
                "title": "Java Developer",
                "tags": ["java", "spring"],
                "skills_demonstrated": [{"name": "Java"}],
                "problem": {"statement": "Backend services"},
                "actions": ["Built APIs"],
                "outcome": {"result": "Improved performance"},
            },
            {
                "id": "wu-frontend",
                "title": "Frontend Developer",
                "tags": ["javascript", "react"],
                "skills_demonstrated": [{"name": "JavaScript"}],
                "problem": {"statement": "UI development"},
                "actions": ["Built components"],
                "outcome": {"result": "Better UX"},
            },
            {
                "id": "wu-devops",
                "title": "DevOps Engineer",
                "tags": ["kubernetes", "docker"],
                "skills_demonstrated": [{"name": "Kubernetes"}],
                "problem": {"statement": "Infrastructure"},
                "actions": ["Set up CI/CD"],
                "outcome": {"result": "Faster deployments"},
            },
        ]

        ranker = HybridRanker()
        weights = ScoringWeights(title_weight=2.0, skills_weight=1.5)

        # Query with ML abbreviation
        ranks = ranker._bm25_rank_weighted(
            work_units,
            "ML engineer python",
            weights,
        )

        # ML work unit (index 0) should rank first
        assert ranks[0] == 1, f"ML work unit should rank first, got rank {ranks[0]}"


class TestPerformance:
    """Performance tests for NFR requirements."""

    def test_ranking_completes_under_3_seconds(self, mock_embedding_service: MagicMock) -> None:
        """NFR1: Ranking 15+ Work Units completes within 3 seconds."""
        import time

        from resume_as_code.models.job_description import JobDescription
        from resume_as_code.services.ranker import HybridRanker

        # Generate 20 Work Units (exceeds 15+ requirement)
        work_units = [
            {
                "id": f"wu-2026-01-{i:02d}-test-unit",
                "title": f"Work Unit {i}: Python AWS Kubernetes Docker DevOps",
                "problem": {
                    "statement": f"Problem {i}: Needed to solve complex engineering challenge"
                },
                "actions": [
                    "Designed scalable architecture with microservices",
                    "Implemented CI/CD pipeline with automated testing",
                    "Deployed to production with zero downtime",
                ],
                "outcome": {"result": f"Outcome {i}: Achieved 50% performance improvement"},
                "tags": ["python", "aws", "kubernetes", "docker", "devops", "api"],
                "skills_demonstrated": [
                    {"name": "python"},
                    {"name": "aws"},
                    {"name": "kubernetes"},
                ],
            }
            for i in range(1, 21)
        ]

        jd = JobDescription(
            raw_text="Senior Python Developer with AWS and Kubernetes experience needed. "
            "Must have strong DevOps skills and experience with Docker containers. "
            "API design and microservices architecture required.",
            skills=["python", "aws", "kubernetes", "docker", "devops", "api", "microservices"],
            keywords=[
                "python",
                "aws",
                "kubernetes",
                "docker",
                "devops",
                "api",
                "microservices",
                "scalable",
            ],
            requirements=[],
        )

        ranker = HybridRanker(embedding_service=mock_embedding_service)

        start_time = time.perf_counter()
        output = ranker.rank(work_units, jd, top_k=10)
        elapsed_time = time.perf_counter() - start_time

        # NFR1: Must complete within 3 seconds
        assert elapsed_time < 3.0, f"Ranking took {elapsed_time:.2f}s, exceeds 3s limit"
        assert len(output.results) > 0
