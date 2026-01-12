"""Tests for hybrid ranker service."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import numpy as np
import pytest

if TYPE_CHECKING:
    from resume_as_code.models.job_description import JobDescription


@pytest.fixture
def sample_work_units() -> list[dict]:
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
def mock_embedding_service():
    """Mock EmbeddingService for tests that don't need real embeddings."""
    mock = MagicMock()

    # Return deterministic embeddings based on content
    def mock_embed_batch(texts: list[str], is_query: bool = True) -> np.ndarray:
        embeddings = []
        for text in texts:
            # Create pseudo-embedding based on text length and hash
            seed = hash(text) % 1000
            np.random.seed(seed)
            embeddings.append(np.random.rand(384).astype(np.float32))
        return np.array(embeddings)

    def mock_embed_passage(text: str) -> np.ndarray:
        seed = hash(text) % 1000
        np.random.seed(seed)
        return np.random.rand(384).astype(np.float32)

    mock.embed_batch = mock_embed_batch
    mock.embed_passage = mock_embed_passage
    return mock


class TestHybridRanker:
    """Tests for HybridRanker class."""

    def test_rank_returns_sorted_results(
        self, sample_work_units: list[dict], sample_jd: JobDescription, mock_embedding_service
    ):
        """AC1: Work Units are returned sorted by score (highest first)."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(sample_work_units, sample_jd, top_k=3)

        assert len(output.results) > 0
        # Verify scores are in descending order
        scores = [r.score for r in output.results]
        assert scores == sorted(scores, reverse=True)

    def test_scores_normalized_0_to_1(
        self, sample_work_units: list[dict], sample_jd: JobDescription, mock_embedding_service
    ):
        """AC1: Each Work Unit receives a relevance score (0.0 to 1.0)."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(sample_work_units, sample_jd)

        for result in output.results:
            assert 0.0 <= result.score <= 1.0, f"Score {result.score} not in range [0, 1]"

    def test_keyword_matches_score_higher(
        self, sample_work_units: list[dict], sample_jd: JobDescription, mock_embedding_service
    ):
        """AC2: Work Units with exact keyword matches score higher."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(sample_work_units, sample_jd)

        # Python API work unit should rank high (matches python, aws, api)
        top_ids = [r.work_unit_id for r in output.results[:2]]
        assert "wu-2026-01-10-python-api" in top_ids

    def test_multiple_text_fields_contribute(self, mock_embedding_service):
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
        self, sample_work_units: list[dict], sample_jd: JobDescription, mock_embedding_service
    ):
        """AC4: Each Work Unit has a match_reasons list."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(sample_work_units, sample_jd)

        for result in output.results:
            assert isinstance(result.match_reasons, list)
            # Top matches should have at least one reason
            if result.score > 0.5:
                assert len(result.match_reasons) > 0

    def test_empty_work_units_returns_empty(self, sample_jd: JobDescription):
        """Should handle empty Work Units list gracefully."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker()
        output = ranker.rank([], sample_jd)

        assert output.results == []
        assert output.jd_keywords == sample_jd.keywords

    def test_single_work_unit_normalized(self, sample_jd: JobDescription, mock_embedding_service):
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

    def test_embedding_prefixes_used_correctly(self, sample_jd: JobDescription):
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

    def test_rrf_formula_with_k_60(self):
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

    def test_rrf_document_ranked_first_both_methods(self):
        """Document ranked 1st in both methods should have highest RRF score."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker()

        bm25_ranks = [1, 2, 3]
        semantic_ranks = [1, 3, 2]

        scores = ranker._rrf_fusion(bm25_ranks, semantic_ranks)

        # First doc should have highest score (rank 1 in both)
        assert scores[0] > scores[1]
        assert scores[0] > scores[2]

    def test_deterministic_tiebreaker_by_id(self, mock_embedding_service):
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

    def test_rrf_fusion_with_custom_weights(self):
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

    def test_rrf_fusion_with_zero_weight(self):
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

    def test_ranker_accepts_scoring_weights(self, mock_embedding_service):
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


class TestMatchReasonExtraction:
    """Tests for match reason extraction."""

    def test_match_reasons_include_skills(self, mock_embedding_service):
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

    def test_match_reasons_limited_to_max(self, mock_embedding_service):
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
        self, sample_work_units: list[dict], sample_jd: JobDescription, mock_embedding_service
    ):
        """RankingOutput.top(n) returns top n results."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(sample_work_units, sample_jd, top_k=10)

        top_2 = output.top(2)
        assert len(top_2) == 2
        assert top_2[0].score >= top_2[1].score

    def test_selected_property(
        self, sample_work_units: list[dict], sample_jd: JobDescription, mock_embedding_service
    ):
        """RankingOutput.selected returns all results."""
        from resume_as_code.services.ranker import HybridRanker

        ranker = HybridRanker(embedding_service=mock_embedding_service)
        output = ranker.rank(sample_work_units, sample_jd)

        assert output.selected == output.results


class TestPerformance:
    """Performance tests for NFR requirements."""

    def test_ranking_completes_under_3_seconds(self, mock_embedding_service):
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
