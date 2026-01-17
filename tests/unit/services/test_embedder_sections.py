"""Tests for section-level embedding (Story 7.11)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pytest
from numpy.typing import NDArray

from resume_as_code.models.job_description import JobDescription, Requirement
from resume_as_code.services.embedder import EmbeddingService


@pytest.fixture
def mock_embedder() -> EmbeddingService:
    """Create embedder with mocked model for fast tests."""
    embedder = EmbeddingService()

    # Mock the model to return consistent embeddings
    mock_model = MagicMock()
    mock_model.encode.return_value = np.random.rand(384).astype(np.float32)
    embedder._model = mock_model
    embedder._model_hash = "test_hash"

    # Mock cache to avoid file I/O
    mock_cache = MagicMock()
    mock_cache.get.return_value = None  # Cache miss
    embedder._cache = mock_cache

    return embedder


class TestEmbedWorkUnitSections:
    """Tests for embed_work_unit_sections method."""

    def test_embeds_all_sections_when_present(self, mock_embedder: EmbeddingService) -> None:
        """AC#1: Each section is embedded separately."""
        wu: dict[str, Any] = {
            "id": "wu-test-001",
            "title": "Led platform migration to cloud",
            "problem": {
                "statement": "Legacy system was slow and expensive",
                "context": "High traffic periods caused outages",
            },
            "actions": ["Analyzed bottlenecks", "Implemented caching layer"],
            "outcome": {
                "result": "50% faster response times",
                "quantified_impact": "p99 latency reduced from 500ms to 100ms",
            },
            "tags": ["python", "aws", "terraform"],
            "skills_demonstrated": [{"name": "Docker"}, {"name": "Kubernetes"}],
        }

        sections = mock_embedder.embed_work_unit_sections(wu)

        # All sections should be present
        assert "title" in sections
        assert "problem" in sections
        assert "actions" in sections
        assert "outcome" in sections
        assert "skills" in sections

        # Each section should be an embedding array
        for _section_name, embedding in sections.items():
            assert isinstance(embedding, np.ndarray)
            assert embedding.dtype == np.float32

    def test_handles_missing_sections_gracefully(self, mock_embedder: EmbeddingService) -> None:
        """Gracefully handles work units with missing optional sections."""
        wu: dict[str, Any] = {
            "id": "wu-minimal",
            "title": "Quick bug fix",
            # No problem, actions, outcome, tags, or skills
        }

        sections = mock_embedder.embed_work_unit_sections(wu)

        # Only title should be present
        assert "title" in sections
        assert "problem" not in sections
        assert "actions" not in sections
        assert "outcome" not in sections
        assert "skills" not in sections

    def test_handles_string_format_problem(self, mock_embedder: EmbeddingService) -> None:
        """Handles string format for problem field."""
        wu: dict[str, Any] = {
            "id": "wu-string-problem",
            "title": "Fix issue",
            "problem": "The database was slow",
        }

        sections = mock_embedder.embed_work_unit_sections(wu)

        assert "problem" in sections

    def test_handles_string_format_actions(self, mock_embedder: EmbeddingService) -> None:
        """Handles string format for actions field."""
        wu: dict[str, Any] = {
            "id": "wu-string-actions",
            "title": "Fix issue",
            "actions": "Refactored the query logic",
        }

        sections = mock_embedder.embed_work_unit_sections(wu)

        assert "actions" in sections

    def test_handles_string_format_outcome(self, mock_embedder: EmbeddingService) -> None:
        """Handles string format for outcome field."""
        wu: dict[str, Any] = {
            "id": "wu-string-outcome",
            "title": "Fix issue",
            "outcome": "Response time improved by 40%",
        }

        sections = mock_embedder.embed_work_unit_sections(wu)

        assert "outcome" in sections

    def test_sections_cached_with_unique_keys(self, mock_embedder: EmbeddingService) -> None:
        """AC#5: Each section is cached separately with section identifier."""
        wu: dict[str, Any] = {
            "id": "wu-cache-test",
            "title": "Cache test title",
            "outcome": {"result": "Cache test outcome"},
        }

        # Track cache put calls
        cache_put_calls: list[str] = []

        def track_embed_query(text: str) -> NDArray[np.float32]:
            cache_put_calls.append(text)
            return np.random.rand(384).astype(np.float32)

        mock_embedder.embed_query = track_embed_query  # type: ignore[method-assign]

        mock_embedder.embed_work_unit_sections(wu)

        # Cache keys should include section prefix
        assert any("[title:wu-cache-test]" in key for key in cache_put_calls)
        assert any("[outcome:wu-cache-test]" in key for key in cache_put_calls)

    def test_skills_combines_tags_and_skills_demonstrated(
        self, mock_embedder: EmbeddingService
    ) -> None:
        """Skills section combines tags and skills_demonstrated."""
        wu: dict[str, Any] = {
            "id": "wu-skills-combine",
            "title": "Skills test",
            "tags": ["python", "aws"],
            "skills_demonstrated": [{"name": "Docker"}],
        }

        # Track what gets embedded
        embedded_texts: list[str] = []

        def track_embed(text: str) -> NDArray[np.float32]:
            embedded_texts.append(text)
            return np.random.rand(384).astype(np.float32)

        mock_embedder.embed_query = track_embed  # type: ignore[method-assign]

        sections = mock_embedder.embed_work_unit_sections(wu)

        assert "skills" in sections
        # The skills text should include both tags and skills_demonstrated
        skills_text = next(t for t in embedded_texts if "[skills:" in t)
        assert "python" in skills_text.lower()
        assert "aws" in skills_text.lower()
        assert "docker" in skills_text.lower()

    def test_empty_work_unit_returns_empty_dict(self, mock_embedder: EmbeddingService) -> None:
        """Empty work unit returns empty embeddings dict."""
        wu: dict[str, Any] = {"id": "wu-empty"}

        sections = mock_embedder.embed_work_unit_sections(wu)

        assert sections == {}

    def test_handles_missing_id_gracefully(self, mock_embedder: EmbeddingService) -> None:
        """Handles work units without id field."""
        wu: dict[str, Any] = {"title": "No ID work unit"}

        # Should not raise, uses "unknown" as fallback
        sections = mock_embedder.embed_work_unit_sections(wu)

        assert "title" in sections


class TestEmbedJDSections:
    """Tests for embed_jd_sections method (Task 2)."""

    def test_embeds_all_jd_sections_when_present(self, mock_embedder: EmbeddingService) -> None:
        """AC#2: JD sections are embedded for cross-matching."""
        jd = JobDescription(
            raw_text="We are looking for a senior Python developer...",
            title="Senior Python Developer",
            requirements=[
                Requirement(text="5+ years Python experience", is_required=True),
                Requirement(text="AWS experience preferred", is_required=False),
            ],
            skills=["Python", "AWS", "Docker"],
            keywords=["Python", "AWS", "Docker"],
        )

        sections = mock_embedder.embed_jd_sections(jd)

        # Should have requirements and skills sections
        assert "requirements" in sections or "full" in sections
        assert "skills" in sections
        assert "full" in sections

        # Each should be an embedding array
        for _section_name, embedding in sections.items():
            assert isinstance(embedding, np.ndarray)
            assert embedding.dtype == np.float32

    def test_handles_jd_with_only_raw_text(self, mock_embedder: EmbeddingService) -> None:
        """Handles JD with only raw_text (no structured requirements)."""
        jd = JobDescription(
            raw_text="Looking for a developer with Python and AWS skills.",
        )

        sections = mock_embedder.embed_jd_sections(jd)

        # Should still have full text embedding
        assert "full" in sections

    def test_requirements_text_computed_from_requirements_list(
        self, mock_embedder: EmbeddingService
    ) -> None:
        """Requirements section combines all requirement texts."""
        jd = JobDescription(
            raw_text="Job description text",
            requirements=[
                Requirement(text="Python proficiency", is_required=True),
                Requirement(text="CI/CD experience", is_required=True),
            ],
            skills=["Python"],
            keywords=["Python"],
        )

        # Track what gets embedded
        embedded_texts: list[str] = []

        def track_embed(text: str) -> NDArray[np.float32]:
            embedded_texts.append(text)
            return np.random.rand(384).astype(np.float32)

        mock_embedder.embed_passage = track_embed  # type: ignore[method-assign]

        mock_embedder.embed_jd_sections(jd)

        # Requirements text should contain requirement items
        requirements_texts = [t for t in embedded_texts if "[jd:requirements]" in t]
        if requirements_texts:
            req_text = requirements_texts[0]
            assert "python" in req_text.lower() or "ci/cd" in req_text.lower()

    def test_skills_section_from_skills_list(self, mock_embedder: EmbeddingService) -> None:
        """Skills section combines JD skills list."""
        jd = JobDescription(
            raw_text="Job description",
            skills=["Python", "AWS", "Kubernetes"],
            keywords=["Python"],
        )

        embedded_texts: list[str] = []

        def track_embed(text: str) -> NDArray[np.float32]:
            embedded_texts.append(text)
            return np.random.rand(384).astype(np.float32)

        mock_embedder.embed_passage = track_embed  # type: ignore[method-assign]

        mock_embedder.embed_jd_sections(jd)

        # Skills text should contain skills
        skills_texts = [t for t in embedded_texts if "[jd:skills]" in t]
        if skills_texts:
            skills_text = skills_texts[0]
            assert "python" in skills_text.lower()
            assert "aws" in skills_text.lower()

    def test_empty_skills_list_omits_skills_section(self, mock_embedder: EmbeddingService) -> None:
        """Empty skills list results in no skills section."""
        jd = JobDescription(
            raw_text="Job with no explicit skills listed",
            skills=[],
            keywords=[],
        )

        sections = mock_embedder.embed_jd_sections(jd)

        assert "skills" not in sections
        assert "full" in sections  # Full text should still be present
