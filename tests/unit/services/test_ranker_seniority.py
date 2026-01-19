"""Integration tests for seniority scoring in HybridRanker."""

from __future__ import annotations

import pytest

from resume_as_code.models.config import ScoringWeights
from resume_as_code.models.job_description import ExperienceLevel, JobDescription
from resume_as_code.services.ranker import HybridRanker


class TestRankerSeniorityScoring:
    """Test seniority integration in ranking."""

    @pytest.fixture
    def ranker(self) -> HybridRanker:
        """Create a ranker instance without embedding service for faster tests."""
        return HybridRanker(embedding_service=None)

    @pytest.fixture
    def scoring_weights_with_seniority(self) -> ScoringWeights:
        """Scoring weights with seniority matching enabled."""
        return ScoringWeights(
            use_seniority_matching=True,
            seniority_blend=0.1,
        )

    @pytest.fixture
    def scoring_weights_no_seniority(self) -> ScoringWeights:
        """Scoring weights with seniority matching disabled."""
        return ScoringWeights(
            use_seniority_matching=False,
            seniority_blend=0.1,
        )

    @pytest.fixture
    def senior_jd(self) -> JobDescription:
        """JD targeting senior level."""
        return JobDescription(
            raw_text="Senior Software Engineer needed with Python experience",
            experience_level=ExperienceLevel.SENIOR,
            skills=["python", "kubernetes"],
            keywords=["python", "kubernetes", "senior"],
        )

    def test_seniority_disabled_returns_neutral_score(
        self, ranker: HybridRanker, scoring_weights_no_seniority: ScoringWeights
    ) -> None:
        """When seniority matching disabled, score should be 1.0."""
        work_unit = {
            "id": "wu-2024-01-01-test",
            "title": "Junior developer task with Python",
            "problem": {"statement": "This is a test problem statement"},
            "actions": ["Action taken to resolve the issue"],
            "outcome": {"result": "Successful outcome achieved"},
        }
        jd = JobDescription(
            raw_text="Executive leadership role",
            experience_level=ExperienceLevel.EXECUTIVE,
            skills=[],
            keywords=[],
        )

        score = ranker._calculate_seniority_score(work_unit, jd, scoring_weights_no_seniority)
        assert score == 1.0

    def test_matching_seniority_returns_perfect_score(
        self, ranker: HybridRanker, scoring_weights_with_seniority: ScoringWeights
    ) -> None:
        """Work unit with matching seniority should score 1.0."""
        work_unit = {
            "id": "wu-2024-01-01-test",
            "title": "Senior engineer led migration project",
            "problem": {"statement": "This is a test problem statement"},
            "actions": ["Action taken to resolve the issue"],
            "outcome": {"result": "Successful outcome achieved"},
            "seniority_level": "senior",  # Explicit match
        }
        jd = JobDescription(
            raw_text="Senior Software Engineer role",
            experience_level=ExperienceLevel.SENIOR,
            skills=[],
            keywords=[],
        )

        score = ranker._calculate_seniority_score(work_unit, jd, scoring_weights_with_seniority)
        assert score == 1.0

    def test_mismatched_seniority_applies_penalty(
        self, ranker: HybridRanker, scoring_weights_with_seniority: ScoringWeights
    ) -> None:
        """Work unit with mismatched seniority should get penalty."""
        work_unit = {
            "id": "wu-2024-01-01-test",
            "title": "Junior developer task",
            "problem": {"statement": "This is a test problem statement"},
            "actions": ["Action taken to resolve the issue"],
            "outcome": {"result": "Successful outcome achieved"},
            "seniority_level": "entry",  # Mismatch with senior JD
        }
        jd = JobDescription(
            raw_text="Senior Software Engineer role",
            experience_level=ExperienceLevel.SENIOR,
            skills=[],
            keywords=[],
        )

        score = ranker._calculate_seniority_score(work_unit, jd, scoring_weights_with_seniority)
        # Entry (rank 1) applying for Senior (rank 3) = underqualified by 2 levels
        assert score == 0.6  # Underqualified penalty

    def test_seniority_inferred_from_title_when_not_set(
        self, ranker: HybridRanker, scoring_weights_with_seniority: ScoringWeights
    ) -> None:
        """Seniority should be inferred from title when not explicitly set."""
        work_unit = {
            "id": "wu-2024-01-01-test",
            "title": "VP of Engineering led strategic initiative",  # Executive title
            "problem": {"statement": "This is a test problem statement"},
            "actions": ["Action taken to resolve the issue"],
            "outcome": {"result": "Successful outcome achieved"},
            # No seniority_level set - should infer from title
        }
        jd = JobDescription(
            raw_text="Executive leadership role",
            experience_level=ExperienceLevel.EXECUTIVE,
            skills=[],
            keywords=[],
        )

        score = ranker._calculate_seniority_score(work_unit, jd, scoring_weights_with_seniority)
        assert score == 1.0  # VP matches Executive

    def test_blend_scores_includes_seniority(
        self, ranker: HybridRanker, scoring_weights_with_seniority: ScoringWeights
    ) -> None:
        """Blend scores should incorporate seniority."""
        relevance = [0.8, 0.6]
        recency = [1.0, 0.5]
        seniority = [1.0, 0.6]  # First matches, second has underqualified penalty
        impact = [0.5, 0.5]  # Neutral impact (Story 7.13)

        blended = ranker._blend_scores(
            relevance, recency, seniority, impact, scoring_weights_with_seniority
        )

        # With recency_blend=0.2, seniority_blend=0.1, impact_blend=0.1, relevance_blend=0.6
        # First should still score higher than second
        assert len(blended) == 2
        assert blended[0] > blended[1]  # First should score higher

    def test_match_reasons_include_seniority_match(
        self, ranker: HybridRanker, scoring_weights_with_seniority: ScoringWeights
    ) -> None:
        """Match reasons should include seniority when it matches well."""
        work_unit = {
            "id": "wu-2024-01-01-test",
            "title": "Test work unit",
            "problem": {"statement": "This is a test problem statement"},
            "actions": ["Action taken"],
            "outcome": {"result": "Result achieved"},
        }
        jd = JobDescription(
            raw_text="Test job",
            experience_level=ExperienceLevel.MID,
            skills=[],
            keywords=[],
        )

        reasons = ranker._extract_match_reasons(
            work_unit, jd, seniority_score=1.0, scoring_weights=scoring_weights_with_seniority
        )
        assert any("Seniority level matches" in r for r in reasons)

    def test_match_reasons_include_seniority_mismatch(
        self, ranker: HybridRanker, scoring_weights_with_seniority: ScoringWeights
    ) -> None:
        """Match reasons should flag seniority mismatch."""
        work_unit = {
            "id": "wu-2024-01-01-test",
            "title": "Test work unit",
            "problem": {"statement": "This is a test problem statement"},
            "actions": ["Action taken"],
            "outcome": {"result": "Result achieved"},
        }
        jd = JobDescription(
            raw_text="Test job",
            experience_level=ExperienceLevel.EXECUTIVE,
            skills=[],
            keywords=[],
        )

        reasons = ranker._extract_match_reasons(
            work_unit, jd, seniority_score=0.3, scoring_weights=scoring_weights_with_seniority
        )
        assert any("Seniority mismatch" in r for r in reasons)


class TestRankerSeniorityBlending:
    """Test seniority affects final ranking order."""

    @pytest.fixture
    def ranker(self) -> HybridRanker:
        """Create a ranker with a mock embedding service."""
        from unittest.mock import MagicMock

        import numpy as np

        mock_embedder = MagicMock()
        # Return identical embeddings so semantic ranking doesn't affect order
        mock_embedder.embed_batch.return_value = np.array([[1.0] * 384, [1.0] * 384])
        mock_embedder.embed_passage.return_value = np.array([1.0] * 384)

        return HybridRanker(embedding_service=mock_embedder)

    def test_seniority_influences_ranking_order(self, ranker: HybridRanker) -> None:
        """Work units with better seniority match should rank higher."""
        senior_wu = {
            "id": "wu-2024-01-01-senior",
            "title": "Senior engineer project",
            "problem": {"statement": "This is a test problem statement"},
            "actions": ["Action taken to resolve the issue"],
            "outcome": {"result": "Successful outcome achieved"},
            "seniority_level": "senior",
        }
        junior_wu = {
            "id": "wu-2024-01-01-junior",
            "title": "Junior developer task",
            "problem": {"statement": "This is a test problem statement"},
            "actions": ["Action taken to resolve the issue"],
            "outcome": {"result": "Successful outcome achieved"},
            "seniority_level": "entry",
        }
        jd = JobDescription(
            raw_text="Senior Software Engineer",
            experience_level=ExperienceLevel.SENIOR,
            skills=[],
            keywords=["senior", "engineer"],
        )

        scoring_weights = ScoringWeights(
            use_seniority_matching=True,
            seniority_blend=0.3,  # High blend to make seniority impact visible
            recency_blend=0.0,  # Disable recency for cleaner test
        )

        # Rank with senior WU listed second
        result = ranker.rank([junior_wu, senior_wu], jd, top_k=2, scoring_weights=scoring_weights)

        # Senior WU should rank higher due to seniority match
        assert result.results[0].work_unit_id == "wu-2024-01-01-senior"
        assert result.results[0].seniority_score > result.results[1].seniority_score

    def test_position_scope_boosts_seniority(self, ranker: HybridRanker) -> None:
        """Position with P&L scope should boost seniority to executive."""
        from resume_as_code.models.position import Position
        from resume_as_code.models.scope import Scope

        # Work unit with position_id reference
        wu_with_position = {
            "id": "wu-2024-01-01-exec",
            "title": "Led strategic initiative",  # No seniority keywords
            "schema_version": "4.0.0",
            "archetype": "minimal",
            "problem": {"statement": "This is a test problem statement"},
            "actions": ["Action taken to resolve the issue"],
            "outcome": {"result": "Successful outcome achieved"},
            "position_id": "pos-acme-director",  # References position with P&L
        }

        # Position with executive-level scope
        positions = {
            "pos-acme-director": Position(
                id="pos-acme-director",
                employer="Acme Corp",
                title="Director of Engineering",  # Would be LEAD without scope
                start_date="2020-01",
                scope=Scope(pl_responsibility="$50M"),  # This should boost to EXECUTIVE
            )
        }

        jd = JobDescription(
            raw_text="Executive leadership role",
            experience_level=ExperienceLevel.EXECUTIVE,
            skills=[],
            keywords=["executive", "leadership"],
        )

        scoring_weights = ScoringWeights(
            use_seniority_matching=True,
            seniority_blend=0.1,
        )

        # Calculate seniority score with positions dict
        score = ranker._calculate_seniority_score(wu_with_position, jd, scoring_weights, positions)

        # Should be 1.0 (perfect match) because P&L boosts to EXECUTIVE
        assert score == 1.0
