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
        """AC4: Match reasons limited to 3-5 per Work Unit."""
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
        assert len(reasons) <= 5  # AC4: 3-5 reasons max


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
