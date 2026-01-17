"""Integration tests for impact scoring in HybridRanker.

Story 7.13: Impact Category Classification
Tests integration of impact classification into ranking workflow.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from resume_as_code.models.config import ScoringWeights
from resume_as_code.services.ranker import HybridRanker


@pytest.fixture
def mock_embedding_service() -> MagicMock:
    """Create a mock embedding service."""
    import numpy as np

    service = MagicMock()
    # Return consistent embeddings for testing
    service.embed_batch.return_value = np.array([[0.5] * 384])
    service.embed_passage.return_value = np.array([0.5] * 384)
    service.embed_jd_sections.return_value = {
        "full": np.array([0.5] * 384),
        "requirements": np.array([0.5] * 384),
        "skills": np.array([0.5] * 384),
    }
    service.embed_work_unit_sections.return_value = {
        "outcome": np.array([0.5] * 384),
        "actions": np.array([0.5] * 384),
        "skills": np.array([0.5] * 384),
        "title": np.array([0.5] * 384),
    }
    return service


@pytest.fixture
def ranker_with_impact(mock_embedding_service: MagicMock) -> HybridRanker:
    """Create a ranker with impact matching enabled."""
    return HybridRanker(embedding_service=mock_embedding_service)


@pytest.fixture
def ranker_no_impact(mock_embedding_service: MagicMock) -> HybridRanker:
    """Create a ranker with impact matching disabled."""
    return HybridRanker(embedding_service=mock_embedding_service)


@pytest.fixture
def scoring_weights_with_impact() -> ScoringWeights:
    """Scoring weights with impact matching enabled."""
    return ScoringWeights(
        use_impact_matching=True,
        impact_blend=0.1,
        quantified_boost=1.25,
    )


@pytest.fixture
def scoring_weights_no_impact() -> ScoringWeights:
    """Scoring weights with impact matching disabled."""
    return ScoringWeights(
        use_impact_matching=False,
        impact_blend=0.0,
    )


@pytest.fixture
def mock_jd_sales() -> MagicMock:
    """Create a mock JD for a sales role."""
    jd = MagicMock()
    jd.title = "Account Executive"
    jd.text_for_ranking = "Looking for sales professional to drive revenue..."
    jd.keywords = ["sales", "revenue", "customer"]
    jd.skills = ["negotiation", "CRM"]
    jd.experience_level = "senior"
    return jd


@pytest.fixture
def mock_jd_engineering() -> MagicMock:
    """Create a mock JD for an engineering role."""
    jd = MagicMock()
    jd.title = "Senior Software Engineer"
    jd.text_for_ranking = "Looking for engineer to build scalable systems..."
    jd.keywords = ["engineering", "software", "systems"]
    jd.skills = ["Python", "AWS"]
    jd.experience_level = "senior"
    return jd


class TestRankerImpactScoring:
    """Test impact integration in ranking."""

    def test_impact_disabled_returns_neutral(
        self,
        ranker_no_impact: HybridRanker,
        mock_jd_sales: MagicMock,
        scoring_weights_no_impact: ScoringWeights,
    ) -> None:
        """AC7: Impact disabled returns neutral 0.5 score."""
        work_unit = {
            "id": "wu-test",
            "title": "Revenue Generation",
            "outcome": {
                "result": "Generated $5M in new revenue",
                "quantified_impact": "$5M ARR",
            },
            "skills_demonstrated": ["sales"],
        }

        score = ranker_no_impact._calculate_impact_score(
            work_unit, mock_jd_sales, scoring_weights_no_impact
        )
        assert score == 0.5  # Neutral

    def test_financial_impact_for_sales_role(
        self,
        ranker_with_impact: HybridRanker,
        mock_jd_sales: MagicMock,
        scoring_weights_with_impact: ScoringWeights,
    ) -> None:
        """Financial impact should score higher for sales role."""
        financial_wu = {
            "id": "wu-financial",
            "title": "Revenue Generation",
            "outcome": {
                "result": "Generated $5M in new revenue",
                "quantified_impact": "45% increase in ARR",
            },
            "skills_demonstrated": ["sales"],
        }

        score = ranker_with_impact._calculate_impact_score(
            financial_wu, mock_jd_sales, scoring_weights_with_impact
        )

        # Financial impact should have high alignment with sales role
        assert score >= 0.5

    def test_operational_impact_for_engineering_role(
        self,
        ranker_with_impact: HybridRanker,
        mock_jd_engineering: MagicMock,
        scoring_weights_with_impact: ScoringWeights,
    ) -> None:
        """Operational impact should score higher for engineering role."""
        operational_wu = {
            "id": "wu-operational",
            "title": "Performance Optimization",
            "outcome": {
                "result": "Reduced latency by 40% through caching",
                "quantified_impact": "99.9% uptime achieved",
            },
            "skills_demonstrated": ["Python", "AWS"],
        }

        score = ranker_with_impact._calculate_impact_score(
            operational_wu, mock_jd_engineering, scoring_weights_with_impact
        )

        # Operational impact should have high alignment with engineering role
        assert score >= 0.5

    def test_impact_mismatch_lower_score(
        self,
        ranker_with_impact: HybridRanker,
        mock_jd_sales: MagicMock,
        scoring_weights_with_impact: ScoringWeights,
    ) -> None:
        """Technical impact for sales role should have lower alignment."""
        technical_wu = {
            "id": "wu-technical",
            "title": "API Development",
            "outcome": {
                "result": "Implemented RESTful API with microservices architecture",
            },
            "skills_demonstrated": ["Python", "AWS"],
        }

        score = ranker_with_impact._calculate_impact_score(
            technical_wu, mock_jd_sales, scoring_weights_with_impact
        )

        # Technical impact should have low alignment with sales role
        assert score <= 0.5

    def test_quantified_boost_applied(
        self,
        ranker_with_impact: HybridRanker,
        mock_jd_sales: MagicMock,
        scoring_weights_with_impact: ScoringWeights,
    ) -> None:
        """AC5: Quantified impacts should receive 25% boost."""
        quantified_wu = {
            "id": "wu-quantified",
            "title": "Sales Achievement",
            "outcome": {
                "result": "Generated revenue",
                "quantified_impact": "$2M annually",
            },
            "skills_demonstrated": ["sales"],
        }

        unquantified_wu = {
            "id": "wu-unquantified",
            "title": "Sales Achievement",
            "outcome": {
                "result": "Generated significant revenue for the company",
            },
            "skills_demonstrated": ["sales"],
        }

        quantified_score = ranker_with_impact._calculate_impact_score(
            quantified_wu, mock_jd_sales, scoring_weights_with_impact
        )
        unquantified_score = ranker_with_impact._calculate_impact_score(
            unquantified_wu, mock_jd_sales, scoring_weights_with_impact
        )

        # Quantified should be higher due to 25% boost
        assert quantified_score >= unquantified_score

    def test_custom_quantified_boost_value(
        self,
        ranker_with_impact: HybridRanker,
        mock_jd_sales: MagicMock,
    ) -> None:
        """Custom quantified_boost values should flow through to scoring."""
        quantified_wu = {
            "id": "wu-quantified",
            "title": "Sales Achievement",
            "outcome": {
                "result": "Generated revenue",
                "quantified_impact": "$2M annually",
            },
            "skills_demonstrated": ["sales"],
        }

        # No boost (1.0)
        no_boost_weights = ScoringWeights(
            use_impact_matching=True,
            quantified_boost=1.0,
        )
        no_boost_score = ranker_with_impact._calculate_impact_score(
            quantified_wu, mock_jd_sales, no_boost_weights
        )

        # High boost (1.5 = 50%)
        high_boost_weights = ScoringWeights(
            use_impact_matching=True,
            quantified_boost=1.5,
        )
        high_boost_score = ranker_with_impact._calculate_impact_score(
            quantified_wu, mock_jd_sales, high_boost_weights
        )

        # Higher boost should produce higher score (unless capped at 1.0)
        assert high_boost_score >= no_boost_score
        # Verify non-trivial difference when not capped
        if high_boost_score < 1.0:
            assert high_boost_score > no_boost_score


class TestImpactReasonGeneration:
    """Test impact reason generation (AC6)."""

    def test_impact_reason_generated_for_alignment(
        self,
        ranker_with_impact: HybridRanker,
        mock_jd_sales: MagicMock,
        scoring_weights_with_impact: ScoringWeights,
    ) -> None:
        """AC6: Impact alignment should generate match reason."""
        work_unit = {
            "id": "wu-test",
            "title": "Revenue Generation",
            "outcome": {
                "result": "Generated $5M in new revenue",
            },
            "skills_demonstrated": ["sales"],
        }

        reason = ranker_with_impact._generate_impact_reason(
            work_unit, mock_jd_sales, 0.8, scoring_weights_with_impact
        )

        assert reason is not None
        assert "Financial" in reason
        assert "Sales" in reason

    def test_no_impact_reason_for_disabled(
        self,
        ranker_no_impact: HybridRanker,
        mock_jd_sales: MagicMock,
        scoring_weights_no_impact: ScoringWeights,
    ) -> None:
        """AC7: No impact reason when disabled."""
        work_unit = {
            "id": "wu-test",
            "title": "Revenue Generation",
            "outcome": {
                "result": "Generated $5M in new revenue",
            },
            "skills_demonstrated": ["sales"],
        }

        reason = ranker_no_impact._generate_impact_reason(
            work_unit, mock_jd_sales, 0.8, scoring_weights_no_impact
        )

        assert reason is None

    def test_no_impact_reason_for_low_score(
        self,
        ranker_with_impact: HybridRanker,
        mock_jd_sales: MagicMock,
        scoring_weights_with_impact: ScoringWeights,
    ) -> None:
        """No impact reason for low alignment scores."""
        work_unit = {
            "id": "wu-test",
            "title": "Code Review",
            "outcome": {
                "result": "Reviewed code for the team",
            },
            "skills_demonstrated": [],
        }

        reason = ranker_with_impact._generate_impact_reason(
            work_unit, mock_jd_sales, 0.2, scoring_weights_with_impact
        )

        # Low scores should not generate a reason
        assert reason is None


class TestBlendScoresWithImpact:
    """Test score blending includes impact."""

    def test_blend_includes_impact(
        self,
        ranker_with_impact: HybridRanker,
        scoring_weights_with_impact: ScoringWeights,
    ) -> None:
        """Blend scores should include impact component."""
        relevance = [0.8, 0.6]
        recency = [1.0, 0.5]
        seniority = [0.9, 0.7]
        impact = [0.9, 0.3]  # High vs low impact

        blended = ranker_with_impact._blend_scores(
            relevance, recency, seniority, impact, scoring_weights_with_impact
        )

        # First work unit should have higher final score
        assert blended[0] > blended[1]
        assert len(blended) == 2

    def test_impact_blend_configurable(
        self,
        ranker_with_impact: HybridRanker,
    ) -> None:
        """Impact blend weight is configurable."""
        relevance = [0.5]
        recency = [1.0]
        seniority = [0.5]
        impact = [1.0]

        # Low impact blend
        low_blend = ScoringWeights(impact_blend=0.05)
        low_result = ranker_with_impact._blend_scores(
            relevance, recency, seniority, impact, low_blend
        )

        # High impact blend
        high_blend = ScoringWeights(impact_blend=0.2)
        high_result = ranker_with_impact._blend_scores(
            relevance, recency, seniority, impact, high_blend
        )

        # Higher impact blend should increase score more
        assert high_result[0] != low_result[0]


class TestRankingResultIncludesImpact:
    """Test RankingResult includes impact_score field."""

    def test_ranking_result_has_impact_score(
        self,
        ranker_with_impact: HybridRanker,
        mock_jd_sales: MagicMock,
        scoring_weights_with_impact: ScoringWeights,
    ) -> None:
        """RankingResult should include impact_score field."""
        work_units = [
            {
                "id": "wu-financial",
                "title": "Revenue Generation",
                "outcome": {
                    "result": "Generated $5M in new revenue",
                },
                "skills_demonstrated": ["sales"],
            }
        ]

        result = ranker_with_impact.rank(
            work_units,
            mock_jd_sales,
            top_k=10,
            scoring_weights=scoring_weights_with_impact,
        )

        assert len(result.results) == 1
        assert hasattr(result.results[0], "impact_score")
        assert 0.0 <= result.results[0].impact_score <= 1.0
