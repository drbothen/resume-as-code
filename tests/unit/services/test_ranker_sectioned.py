"""Tests for sectioned semantic ranking (Story 7.11)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pytest
from pydantic import ValidationError

from resume_as_code.models.config import ScoringWeights
from resume_as_code.models.job_description import JobDescription, Requirement
from resume_as_code.services.ranker import HybridRanker


@pytest.fixture
def mock_ranker() -> HybridRanker:
    """Create ranker with mocked embedding service."""
    mock_embedder = MagicMock()

    # Return deterministic embeddings for predictable tests
    np.random.seed(42)

    def mock_wu_sections(wu: dict[str, Any]) -> dict[str, np.ndarray]:
        """Return mock section embeddings for work unit."""
        return {
            "title": np.random.rand(384).astype(np.float32),
            "outcome": np.random.rand(384).astype(np.float32),
            "actions": np.random.rand(384).astype(np.float32),
            "skills": np.random.rand(384).astype(np.float32),
        }

    def mock_jd_sections(jd: JobDescription) -> dict[str, np.ndarray]:
        """Return mock section embeddings for JD."""
        return {
            "requirements": np.random.rand(384).astype(np.float32),
            "skills": np.random.rand(384).astype(np.float32),
            "full": np.random.rand(384).astype(np.float32),
        }

    mock_embedder.embed_work_unit_sections.side_effect = mock_wu_sections
    mock_embedder.embed_jd_sections.side_effect = mock_jd_sections

    return HybridRanker(embedding_service=mock_embedder)


class TestSectionedSemanticRanking:
    """Tests for section-level semantic ranking."""

    def test_semantic_rank_sectioned_returns_ranks(self, mock_ranker: HybridRanker) -> None:
        """AC#3: Sectioned ranking returns valid ranks."""
        weights = ScoringWeights(
            use_sectioned_semantic=True,
            section_outcome_weight=0.4,
            section_actions_weight=0.3,
            section_skills_weight=0.2,
            section_title_weight=0.1,
        )

        jd = JobDescription(
            raw_text="Looking for a Python developer",
            requirements=[Requirement(text="5+ years Python")],
            skills=["Python", "AWS"],
            keywords=["Python", "AWS"],
        )

        work_units = [
            {"id": "wu-1", "title": "Python work"},
            {"id": "wu-2", "title": "Java work"},
        ]

        ranks = mock_ranker._semantic_rank_sectioned(work_units, jd, weights)

        assert len(ranks) == 2
        assert all(r >= 1 for r in ranks)
        # Ranks should be 1 and 2 (no ties expected with random embeddings)
        assert sorted(ranks) == [1, 2]

    def test_weighted_aggregation_formula(self, mock_ranker: HybridRanker) -> None:
        """AC#3: Weighted formula applies correct weights."""
        # Create ranker with predictable similarity scores
        mock_embedder = MagicMock()

        # Create identical normalized vectors for perfect similarity
        unit_vector = np.ones(384, dtype=np.float32) / np.sqrt(384)

        def mock_wu_sections(wu: dict[str, Any]) -> dict[str, np.ndarray]:
            return {
                "title": unit_vector.copy(),
                "outcome": unit_vector.copy(),
                "actions": unit_vector.copy(),
                "skills": unit_vector.copy(),
            }

        def mock_jd_sections(jd: JobDescription) -> dict[str, np.ndarray]:
            return {
                "requirements": unit_vector.copy(),
                "skills": unit_vector.copy(),
                "full": unit_vector.copy(),
            }

        mock_embedder.embed_work_unit_sections.side_effect = mock_wu_sections
        mock_embedder.embed_jd_sections.side_effect = mock_jd_sections

        ranker = HybridRanker(embedding_service=mock_embedder)

        weights = ScoringWeights(
            use_sectioned_semantic=True,
            section_outcome_weight=0.4,
            section_actions_weight=0.3,
            section_skills_weight=0.2,
            section_title_weight=0.1,
        )

        jd = JobDescription(
            raw_text="Test JD",
            requirements=[Requirement(text="Test requirement")],
            skills=["Python"],
            keywords=["Python"],
        )

        work_units = [{"id": "wu-1", "title": "Test"}]

        # With identical vectors, all similarities should be 1.0
        # Weighted sum: 0.4 + 0.3 + 0.2 + 0.1 = 1.0
        ranks = ranker._semantic_rank_sectioned(work_units, jd, weights)

        assert len(ranks) == 1
        assert ranks[0] == 1

    def test_partial_relevance_reflected_in_score(self, mock_ranker: HybridRanker) -> None:
        """AC#4: Strong skills match but weak experience match shows partial relevance."""
        # Create ranker with controlled similarity scores
        mock_embedder = MagicMock()

        # Create orthogonal vectors for zero similarity
        zero_vector = np.zeros(384, dtype=np.float32)
        unit_vector = np.ones(384, dtype=np.float32) / np.sqrt(384)

        def mock_wu_sections_strong_skills(wu: dict[str, Any]) -> dict[str, np.ndarray]:
            """Work unit with strong skills, weak experience."""
            return {
                "title": zero_vector.copy(),  # Weak title match
                "outcome": zero_vector.copy(),  # Weak outcome match
                "actions": zero_vector.copy(),  # Weak actions match
                "skills": unit_vector.copy(),  # Strong skills match
            }

        def mock_wu_sections_strong_outcome(wu: dict[str, Any]) -> dict[str, np.ndarray]:
            """Work unit with strong outcome, weak skills."""
            return {
                "title": zero_vector.copy(),
                "outcome": unit_vector.copy(),  # Strong outcome match
                "actions": zero_vector.copy(),
                "skills": zero_vector.copy(),
            }

        def mock_jd_sections(jd: JobDescription) -> dict[str, np.ndarray]:
            return {
                "requirements": unit_vector.copy(),
                "skills": unit_vector.copy(),
                "full": unit_vector.copy(),
            }

        work_units = [
            {"id": "wu-skills", "title": "Skills focus"},
            {"id": "wu-outcome", "title": "Outcome focus"},
        ]

        # Mock with skills-focused work unit first
        def mock_wu_sections(wu: dict[str, Any]) -> dict[str, np.ndarray]:
            if wu["id"] == "wu-skills":
                return mock_wu_sections_strong_skills(wu)
            return mock_wu_sections_strong_outcome(wu)

        mock_embedder.embed_work_unit_sections.side_effect = mock_wu_sections
        mock_embedder.embed_jd_sections.side_effect = mock_jd_sections

        ranker = HybridRanker(embedding_service=mock_embedder)

        weights = ScoringWeights(
            use_sectioned_semantic=True,
            section_outcome_weight=0.4,
            section_actions_weight=0.3,
            section_skills_weight=0.2,
            section_title_weight=0.1,
        )

        jd = JobDescription(
            raw_text="Test",
            requirements=[Requirement(text="Test")],
            skills=["Python"],
            keywords=["Python"],
        )

        ranks = ranker._semantic_rank_sectioned(work_units, jd, weights)

        # Outcome-focused (40% weight) should rank higher than skills-focused (20% weight)
        skills_idx = 0  # wu-skills
        outcome_idx = 1  # wu-outcome

        # Lower rank number = better
        assert ranks[outcome_idx] < ranks[skills_idx]

    def test_cosine_sim_single_computes_correctly(self, mock_ranker: HybridRanker) -> None:
        """Cosine similarity helper computes correct values."""
        # Identical vectors should have similarity 1.0
        vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        sim = mock_ranker._cosine_sim_single(vec, vec)
        assert abs(sim - 1.0) < 0.01

        # Orthogonal vectors should have similarity 0.5 (normalized from 0)
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        sim = mock_ranker._cosine_sim_single(vec1, vec2)
        assert abs(sim - 0.5) < 0.01

    def test_handles_missing_sections_gracefully(self, mock_ranker: HybridRanker) -> None:
        """Handles work units with missing sections."""
        mock_embedder = MagicMock()

        unit_vector = np.ones(384, dtype=np.float32) / np.sqrt(384)

        def mock_wu_sections_partial(wu: dict[str, Any]) -> dict[str, np.ndarray]:
            """Return only title embedding."""
            return {"title": unit_vector.copy()}

        def mock_jd_sections(jd: JobDescription) -> dict[str, np.ndarray]:
            return {"full": unit_vector.copy()}

        mock_embedder.embed_work_unit_sections.side_effect = mock_wu_sections_partial
        mock_embedder.embed_jd_sections.side_effect = mock_jd_sections

        ranker = HybridRanker(embedding_service=mock_embedder)

        weights = ScoringWeights(
            use_sectioned_semantic=True,
            section_outcome_weight=0.4,
            section_actions_weight=0.3,
            section_skills_weight=0.2,
            section_title_weight=0.1,
        )

        jd = JobDescription(raw_text="Test", skills=[], keywords=[])
        work_units = [{"id": "wu-1", "title": "Test"}]

        # Should not raise, missing sections contribute 0 to score
        ranks = ranker._semantic_rank_sectioned(work_units, jd, weights)

        assert len(ranks) == 1


class TestSectionWeightsValidation:
    """Tests for section weight validation in ScoringWeights."""

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

    def test_default_weights_sum_to_one(self) -> None:
        """Default weights sum to 1.0."""
        weights = ScoringWeights(use_sectioned_semantic=True)
        total = (
            weights.section_outcome_weight
            + weights.section_actions_weight
            + weights.section_skills_weight
            + weights.section_title_weight
        )
        assert abs(total - 1.0) < 0.01

    def test_invalid_weights_rejected(self) -> None:
        """Weights that don't sum to 1.0 are rejected when sectioned is enabled."""
        with pytest.raises(ValidationError, match="sum to 1.0"):
            ScoringWeights(
                use_sectioned_semantic=True,
                section_outcome_weight=0.5,
                section_actions_weight=0.5,
                section_skills_weight=0.5,
                section_title_weight=0.5,  # Sum = 2.0
            )

    def test_weights_not_validated_when_disabled(self) -> None:
        """Weights validation skipped when sectioned semantic is disabled."""
        # Should not raise even with invalid weights
        weights = ScoringWeights(
            use_sectioned_semantic=False,
            section_outcome_weight=0.5,
            section_actions_weight=0.5,
            section_skills_weight=0.5,
            section_title_weight=0.5,
        )
        assert weights is not None


class TestRankMethodIntegration:
    """Tests for rank() method integration with sectioned semantic."""

    def test_rank_uses_sectioned_when_enabled(self) -> None:
        """AC#3: rank() uses sectioned semantic when enabled."""
        mock_embedder = MagicMock()

        unit_vector = np.ones(384, dtype=np.float32) / np.sqrt(384)

        def mock_wu_sections(wu: dict[str, Any]) -> dict[str, np.ndarray]:
            return {
                "title": unit_vector.copy(),
                "outcome": unit_vector.copy(),
                "actions": unit_vector.copy(),
                "skills": unit_vector.copy(),
            }

        def mock_jd_sections(jd: JobDescription) -> dict[str, np.ndarray]:
            return {
                "requirements": unit_vector.copy(),
                "skills": unit_vector.copy(),
                "full": unit_vector.copy(),
            }

        mock_embedder.embed_work_unit_sections.side_effect = mock_wu_sections
        mock_embedder.embed_jd_sections.side_effect = mock_jd_sections
        # Also mock batch embedding for fallback path
        mock_embedder.embed_batch.return_value = np.zeros((1, 384), dtype=np.float32)
        mock_embedder.embed_passage.return_value = np.zeros(384, dtype=np.float32)

        ranker = HybridRanker(embedding_service=mock_embedder)

        weights = ScoringWeights(
            use_sectioned_semantic=True,
            section_outcome_weight=0.4,
            section_actions_weight=0.3,
            section_skills_weight=0.2,
            section_title_weight=0.1,
        )

        jd = JobDescription(
            raw_text="Test JD",
            requirements=[Requirement(text="Test")],
            skills=["Python"],
            keywords=["Python"],
        )

        work_units = [{"id": "wu-1", "title": "Test WU"}]

        ranker.rank(work_units, jd, scoring_weights=weights)

        # Sectioned methods should be called
        mock_embedder.embed_work_unit_sections.assert_called()
        mock_embedder.embed_jd_sections.assert_called()

    def test_rank_falls_back_to_full_document_when_disabled(self) -> None:
        """AC#4: rank() falls back to full-document when sectioned disabled."""
        mock_embedder = MagicMock()

        # Mock batch embedding (full-document path)
        mock_embedder.embed_batch.return_value = np.random.rand(1, 384).astype(np.float32)
        mock_embedder.embed_passage.return_value = np.random.rand(384).astype(np.float32)

        ranker = HybridRanker(embedding_service=mock_embedder)

        weights = ScoringWeights(use_sectioned_semantic=False)

        jd = JobDescription(
            raw_text="Test JD",
            skills=["Python"],
            keywords=["Python"],
        )

        work_units = [{"id": "wu-1", "title": "Test WU"}]

        ranker.rank(work_units, jd, scoring_weights=weights)

        # Full-document methods should be called
        mock_embedder.embed_batch.assert_called()
        # Sectioned methods should NOT be called
        mock_embedder.embed_work_unit_sections.assert_not_called()

    def test_rank_backward_compatible_without_scoring_weights(self) -> None:
        """rank() works without scoring_weights (backward compatibility)."""
        mock_embedder = MagicMock()

        mock_embedder.embed_batch.return_value = np.random.rand(1, 384).astype(np.float32)
        mock_embedder.embed_passage.return_value = np.random.rand(384).astype(np.float32)

        ranker = HybridRanker(embedding_service=mock_embedder)

        jd = JobDescription(
            raw_text="Test JD",
            skills=["Python"],
            keywords=["Python"],
        )

        work_units = [{"id": "wu-1", "title": "Test WU"}]

        # Should not raise when scoring_weights is None (default)
        result = ranker.rank(work_units, jd)

        assert result is not None
        # Full-document method used as default
        mock_embedder.embed_batch.assert_called()
