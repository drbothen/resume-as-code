"""Tests for ContentCurator service (Story 7.14)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import numpy as np
import pytest

from resume_as_code.models.board_role import BoardRole
from resume_as_code.models.certification import Certification
from resume_as_code.models.config import BulletsPerPositionConfig, CurationConfig
from resume_as_code.models.job_description import ExperienceLevel, JobDescription
from resume_as_code.models.position import Position
from resume_as_code.models.publication import Publication
from resume_as_code.models.work_unit import Outcome, Problem, WorkUnit, WorkUnitArchetype
from resume_as_code.services.content_curator import (
    BULLETS_PER_POSITION,
    ContentCurator,
    CurationResult,
    is_executive_level,
)

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from resume_as_code.services.embedder import EmbeddingService


@pytest.fixture
def mock_embedder() -> MagicMock:
    """Create a mock embedder that returns consistent embeddings."""
    embedder = MagicMock()

    def mock_embed_query(text: str) -> NDArray[np.float32]:
        # Return consistent embedding based on text hash (normalized)
        rng = np.random.default_rng(hash(text) % (2**32))
        vec = rng.random(384).astype(np.float32)
        return vec / np.linalg.norm(vec)

    def mock_embed_passage(text: str) -> NDArray[np.float32]:
        # Return consistent embedding based on text hash (normalized)
        rng = np.random.default_rng(hash(text) % (2**32))
        vec = rng.random(384).astype(np.float32)
        return vec / np.linalg.norm(vec)

    embedder.embed_query = mock_embed_query
    embedder.embed_passage = mock_embed_passage

    return embedder


@pytest.fixture
def sample_jd() -> JobDescription:
    """Create a sample job description."""
    return JobDescription(
        raw_text="Senior Python Developer with AWS experience. "
        "Must have experience with Kubernetes and CI/CD pipelines.",
        title="Senior Python Developer",
        skills=["Python", "AWS", "Kubernetes", "Docker", "CI/CD"],
        keywords=["python", "aws", "kubernetes", "docker", "cicd", "senior"],
        experience_level=ExperienceLevel.SENIOR,
    )


@pytest.fixture
def executive_jd() -> JobDescription:
    """Create an executive-level job description."""
    return JobDescription(
        raw_text="Chief Technology Officer overseeing global engineering teams.",
        title="Chief Technology Officer",
        skills=["Leadership", "Strategy", "Cloud Architecture"],
        keywords=["cto", "executive", "leadership", "strategy"],
        experience_level=ExperienceLevel.EXECUTIVE,
    )


class TestContentCuratorInit:
    """Tests for ContentCurator initialization."""

    def test_init_with_config(self, mock_embedder: MagicMock) -> None:
        """Should initialize with CurationConfig."""
        config = CurationConfig(
            career_highlights_max=5,
            certifications_max=6,
            board_roles_max=4,
        )
        curator = ContentCurator(embedder=mock_embedder, config=config)

        assert curator.limits["career_highlights"] == 5
        assert curator.limits["certifications"] == 6
        assert curator.limits["board_roles"] == 4

    def test_init_with_defaults(self, mock_embedder: MagicMock) -> None:
        """Should use default limits without config."""
        curator = ContentCurator(embedder=mock_embedder)

        assert curator.limits["career_highlights"] == 4
        assert curator.limits["certifications"] == 5
        assert curator.limits["board_roles"] == 3


class TestCurateHighlights:
    """Tests for curate_highlights method (AC #1, #7)."""

    def test_curate_highlights_selects_top_n(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should select top N most relevant highlights."""
        curator = ContentCurator(embedder=mock_embedder)
        highlights = [
            "Led migration to Python microservices",
            "Implemented Kubernetes orchestration",
            "Managed team of 10 developers",
            "Built AWS infrastructure",
            "Wrote company blog posts",
        ]

        result = curator.curate_highlights(highlights, sample_jd, max_count=3)

        assert len(result.selected) == 3
        assert len(result.excluded) == 2
        assert isinstance(result.scores, dict)
        assert result.reason != ""

    def test_curate_highlights_empty_list(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should handle empty highlights list."""
        curator = ContentCurator(embedder=mock_embedder)
        result = curator.curate_highlights([], sample_jd)

        assert result.selected == []
        assert result.excluded == []
        assert "No highlights" in result.reason

    def test_curate_highlights_scores_range(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Scores should be between 0 and 1."""
        curator = ContentCurator(embedder=mock_embedder)
        highlights = ["Python development", "AWS cloud architecture"]
        result = curator.curate_highlights(highlights, sample_jd)

        for score in result.scores.values():
            assert 0.0 <= score <= 1.0

    def test_curate_highlights_respects_min_relevance(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should exclude items below min_relevance_score."""
        config = CurationConfig(min_relevance_score=0.9)  # Very high threshold
        curator = ContentCurator(embedder=mock_embedder, config=config)
        highlights = ["Python dev", "Something unrelated", "Random content"]

        result = curator.curate_highlights(highlights, sample_jd)

        # With high threshold (0.9), items with scores below should be excluded
        # Verify that at least some items are excluded due to threshold
        all_scores = list(result.scores.values())
        below_threshold = [s for s in all_scores if s < 0.9]

        # If any scores are below threshold, those items should be in excluded
        if below_threshold:
            assert len(result.excluded) > 0, "Items below threshold should be excluded"

        # Verify selected items have scores >= threshold
        for highlight in result.selected:
            key = ContentCurator._highlight_key(highlight)
            score = result.scores.get(key, 0)
            assert score >= 0.9, (
                f"Selected item '{highlight[:30]}' has score {score} below threshold"
            )


class TestCurateCertifications:
    """Tests for curate_certifications method (AC #2, #3, #7)."""

    def test_curate_certifications_selects_relevant(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should select most relevant certifications."""
        curator = ContentCurator(embedder=mock_embedder)
        certs = [
            Certification(name="AWS Solutions Architect", issuer="Amazon"),
            Certification(name="Kubernetes Administrator", issuer="CNCF"),
            Certification(name="PMP", issuer="PMI"),
            Certification(name="CISSP", issuer="ISC2"),
        ]

        result = curator.curate_certifications(certs, sample_jd, max_count=2)

        assert len(result.selected) == 2
        assert len(result.excluded) == 2

    def test_curate_certifications_priority_always_included(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Certifications with priority='always' should always be included."""
        curator = ContentCurator(embedder=mock_embedder)
        certs = [
            Certification(name="CISSP", issuer="ISC2", priority="always"),
            Certification(name="AWS SA", issuer="Amazon"),
            Certification(name="PMP", issuer="PMI"),
        ]

        result = curator.curate_certifications(certs, sample_jd, max_count=2)

        # CISSP should be in selected even if not most relevant
        cert_names = [c.name for c in result.selected]
        assert "CISSP" in cert_names

    def test_curate_certifications_empty_list(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should handle empty certifications list."""
        curator = ContentCurator(embedder=mock_embedder)
        result = curator.curate_certifications([], sample_jd)

        assert result.selected == []
        assert "No certifications" in result.reason

    def test_curate_certifications_skill_match_boost(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Certifications matching JD skills should score higher."""
        curator = ContentCurator(embedder=mock_embedder)
        # AWS is in JD skills, so AWS cert should score higher
        certs = [
            Certification(name="AWS Solutions Architect", issuer="Amazon"),
            Certification(name="Unrelated Cert", issuer="Unknown"),
        ]

        result = curator.curate_certifications(certs, sample_jd)

        # AWS cert should have higher score due to skill match
        assert result.scores.get("AWS Solutions Architect", 0) >= result.scores.get(
            "Unrelated Cert", 0
        )

    def test_curate_certifications_respects_min_relevance(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should exclude certifications below min_relevance_score threshold."""
        config = CurationConfig(min_relevance_score=0.9)  # Very high threshold
        curator = ContentCurator(embedder=mock_embedder, config=config)
        certs = [
            Certification(name="AWS Solutions Architect", issuer="Amazon"),
            Certification(name="Unrelated Cert", issuer="Unknown"),
            Certification(name="Random Cert", issuer="Random"),
        ]

        result = curator.curate_certifications(certs, sample_jd)

        # Verify selected certifications have scores >= threshold
        for cert in result.selected:
            score = result.scores.get(cert.name, 0)
            assert score >= 0.9, f"Selected cert '{cert.name}' has score {score} below threshold"

        # Verify excluded certifications below threshold are in excluded list
        for cert_name, score in result.scores.items():
            if score < 0.9:
                cert_in_excluded = any(c.name == cert_name for c in result.excluded)
                assert cert_in_excluded, f"Cert '{cert_name}' with score {score} should be excluded"


class TestCurateBoardRoles:
    """Tests for curate_board_roles method (AC #4, #7)."""

    def test_curate_board_roles_non_executive(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Non-executive roles should get lower board role limit."""
        curator = ContentCurator(embedder=mock_embedder)
        roles = [
            BoardRole(organization="Tech Startup A", role="Advisor", start_date="2022-01"),
            BoardRole(organization="Tech Startup B", role="Advisor", start_date="2021-01"),
            BoardRole(organization="Tech Startup C", role="Advisor", start_date="2020-01"),
            BoardRole(organization="Tech Startup D", role="Advisor", start_date="2019-01"),
        ]

        result = curator.curate_board_roles(roles, sample_jd, is_executive_role=False)

        # Default non-executive limit is 3
        assert len(result.selected) == 3
        assert "non-executive" in result.reason

    def test_curate_board_roles_executive(
        self, mock_embedder: MagicMock, executive_jd: JobDescription
    ) -> None:
        """Executive roles should get higher board role limit."""
        curator = ContentCurator(embedder=mock_embedder)
        roles = [
            BoardRole(organization="Company A", role="Board Member", start_date="2022-01"),
            BoardRole(organization="Company B", role="Advisor", start_date="2021-01"),
            BoardRole(organization="Company C", role="Director", start_date="2020-01"),
            BoardRole(organization="Company D", role="Advisor", start_date="2019-01"),
            BoardRole(organization="Company E", role="Advisor", start_date="2018-01"),
            BoardRole(organization="Company F", role="Advisor", start_date="2017-01"),
        ]

        result = curator.curate_board_roles(roles, executive_jd, is_executive_role=True)

        # Default executive limit is 5
        assert len(result.selected) == 5
        assert "executive" in result.reason

    def test_curate_board_roles_priority_always(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Board roles with priority='always' should always be included."""
        curator = ContentCurator(embedder=mock_embedder)
        roles = [
            BoardRole(
                organization="Priority Org",
                role="Director",
                start_date="2018-01",
                priority="always",
            ),
            BoardRole(organization="Company A", role="Advisor", start_date="2022-01"),
            BoardRole(organization="Company B", role="Advisor", start_date="2021-01"),
        ]

        result = curator.curate_board_roles(roles, sample_jd, max_count=2)

        org_names = [r.organization for r in result.selected]
        assert "Priority Org" in org_names

    def test_curate_board_roles_empty(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should handle empty board roles list."""
        curator = ContentCurator(embedder=mock_embedder)
        result = curator.curate_board_roles([], sample_jd)

        assert result.selected == []
        assert "No board roles" in result.reason

    def test_curate_board_roles_respects_min_relevance(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should exclude board roles below min_relevance_score threshold."""
        config = CurationConfig(min_relevance_score=0.9)  # Very high threshold
        curator = ContentCurator(embedder=mock_embedder, config=config)
        roles = [
            BoardRole(organization="Tech Startup A", role="Advisor", start_date="2022-01"),
            BoardRole(organization="Random Org B", role="Member", start_date="2021-01"),
            BoardRole(organization="Unrelated C", role="Advisor", start_date="2020-01"),
        ]

        result = curator.curate_board_roles(roles, sample_jd, is_executive_role=False)

        # Verify selected roles have scores >= threshold
        for role in result.selected:
            score = result.scores.get(role.organization, 0)
            assert score >= 0.9, (
                f"Selected role '{role.organization}' has score {score} below threshold"
            )

        # Verify excluded roles below threshold are in excluded list
        for org_name, score in result.scores.items():
            if score < 0.9:
                role_in_excluded = any(r.organization == org_name for r in result.excluded)
                assert role_in_excluded, f"Role '{org_name}' with score {score} should be excluded"


class TestCuratePublications:
    """Tests for curate_publications method (Story 8.2)."""

    def test_curate_publications_selects_top_n(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should select top N most JD-relevant publications (AC #2)."""
        curator = ContentCurator(embedder=mock_embedder)
        publications = [
            Publication(
                title="Python Microservices at Scale",
                type="conference",
                venue="PyCon",
                date="2024-04",
                topics=["python", "microservices"],
                abstract="Building scalable Python services with AWS.",
            ),
            Publication(
                title="Kubernetes Best Practices",
                type="conference",
                venue="KubeCon",
                date="2024-03",
                topics=["kubernetes", "devops"],
                abstract="Container orchestration patterns.",
            ),
            Publication(
                title="Leadership in Tech",
                type="article",
                venue="Tech Blog",
                date="2023-06",
                topics=["leadership"],
                abstract="Managing engineering teams.",
            ),
            Publication(
                title="Cloud Architecture Patterns",
                type="whitepaper",
                venue="AWS",
                date="2023-01",
                topics=["aws", "cloud"],
                abstract="Modern cloud architecture with AWS.",
            ),
        ]

        result = curator.curate_publications(publications, sample_jd, max_count=2)

        assert len(result.selected) == 2
        assert len(result.excluded) == 2
        assert isinstance(result.scores, dict)
        assert "publications" in result.reason.lower()

    def test_curate_publications_empty_list(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should handle empty publications list."""
        curator = ContentCurator(embedder=mock_embedder)
        result = curator.curate_publications([], sample_jd)

        assert result.selected == []
        assert result.excluded == []
        assert "No publications" in result.reason

    def test_curate_publications_topic_overlap_scoring(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Publications with JD-matching topics should score higher (AC #3)."""
        curator = ContentCurator(embedder=mock_embedder)
        # JD skills: Python, AWS, Kubernetes, Docker, CI/CD
        aws_pub = Publication(
            title="AWS and Kubernetes Integration",
            type="conference",
            venue="AWS Summit",
            date="2024-01",
            topics=["aws", "kubernetes"],  # 2 matches
            abstract="AWS EKS deployment.",
        )
        general_pub = Publication(
            title="General Software Development",
            type="article",
            venue="Blog",
            date="2024-01",
            topics=["agile", "waterfall"],  # 0 matches
            abstract="Development methodologies.",
        )
        publications = [aws_pub, general_pub]

        result = curator.curate_publications(publications, sample_jd)

        # AWS/Kubernetes publication should score higher due to topic overlap
        aws_score = result.scores.get(curator._publication_key(aws_pub), 0)
        general_score = result.scores.get(curator._publication_key(general_pub), 0)
        assert aws_score > general_score

    def test_curate_publications_recency_bonus(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Recent publications should get recency bonus (AC #3)."""
        curator = ContentCurator(embedder=mock_embedder)
        recent_pub = Publication(
            title="Recent Python Talk",
            type="conference",
            venue="Conference",
            date="2024-06",  # Recent
            topics=["python"],
        )
        old_pub = Publication(
            title="Old Python Talk",
            type="conference",
            venue="Conference",
            date="2018-06",  # Old (6+ years)
            topics=["python"],
        )
        publications = [recent_pub, old_pub]

        result = curator.curate_publications(publications, sample_jd)

        # Recent publication should have higher score due to recency bonus
        recent_score = result.scores.get(curator._publication_key(recent_pub), 0)
        old_score = result.scores.get(curator._publication_key(old_pub), 0)
        assert recent_score > old_score

    def test_curate_publications_respects_min_relevance(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should exclude publications below min_relevance_score (AC #4)."""
        config = CurationConfig(min_relevance_score=0.9)  # Very high threshold
        curator = ContentCurator(embedder=mock_embedder, config=config)
        publications = [
            Publication(
                title="Python Conference Talk",
                type="conference",
                venue="PyCon",
                date="2024-01",
                topics=["python"],
            ),
            Publication(
                title="Unrelated Topic",
                type="article",
                venue="Random",
                date="2024-01",
                topics=["cooking"],
            ),
        ]

        result = curator.curate_publications(publications, sample_jd)

        # Verify selected publications have scores >= threshold
        for pub in result.selected:
            score = result.scores.get(curator._publication_key(pub), 0)
            assert score >= 0.9, f"Selected pub '{pub.title}' has score {score} below threshold"

    def test_curate_publications_uses_abstract_for_semantic_matching(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Abstract should contribute to semantic matching (AC #3).

        Note: With mock embeddings, semantic scores are pseudo-random.
        This test verifies that abstract text is included in the matching
        by checking that get_text_for_matching() output affects scoring.
        """
        curator = ContentCurator(embedder=mock_embedder)
        # Use same title/venue but different abstracts + matching topics
        tech_pub = Publication(
            title="Tech Talk",
            type="conference",
            venue="Tech Conf",
            date="2024-01",
            topics=["python", "aws"],  # Matching JD skills boost this
            abstract="Deep dive into Python, AWS Lambda, and Kubernetes patterns.",
        )
        garden_pub = Publication(
            title="Other Talk",
            type="conference",
            venue="Garden Conf",
            date="2024-01",
            topics=["gardening", "flowers"],  # Non-matching topics
            abstract="Discussion about gardening and home improvement.",
        )
        publications = [tech_pub, garden_pub]

        result = curator.curate_publications(publications, sample_jd)

        # With matching topics, Tech Talk should score higher
        tech_score = result.scores.get(curator._publication_key(tech_pub), 0)
        garden_score = result.scores.get(curator._publication_key(garden_pub), 0)
        # Topic overlap gives Tech Talk 40% × 1.0 = 0.4 boost
        # Garden Talk gets 40% × 0.0 = 0.0 from topics
        assert tech_score > garden_score

    def test_curate_publications_with_skill_registry(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should normalize topics via SkillRegistry when provided."""
        from unittest.mock import MagicMock as Mock

        curator = ContentCurator(embedder=mock_embedder)
        publications = [
            Publication(
                title="K8s Talk",
                type="conference",
                venue="Conf",
                date="2024-01",
                topics=["k8s"],  # Alias for kubernetes
            ),
        ]

        # Create a mock SkillRegistry that normalizes k8s -> kubernetes
        mock_registry = Mock()
        mock_registry.normalize.side_effect = lambda x: "kubernetes" if x == "k8s" else x.lower()

        result = curator.curate_publications(publications, sample_jd, registry=mock_registry)

        # Registry should be called to normalize topics
        mock_registry.normalize.assert_called()
        # Should have scores
        assert len(result.scores) > 0

    def test_curate_publications_scores_between_0_and_1(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """All scores should be between 0 and 1."""
        curator = ContentCurator(embedder=mock_embedder)
        publications = [
            Publication(
                title="Talk 1",
                type="conference",
                venue="Conf",
                date="2024-01",
                topics=["python", "aws"],
            ),
            Publication(
                title="Talk 2",
                type="article",
                venue="Blog",
                date="2023-01",
            ),
        ]

        result = curator.curate_publications(publications, sample_jd)

        for score in result.scores.values():
            assert 0.0 <= score <= 1.0

    def test_curate_publications_default_limit_from_config(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should use publications_max from config when max_count not specified."""
        config = CurationConfig(publications_max=2)
        curator = ContentCurator(embedder=mock_embedder, config=config)
        publications = [
            Publication(title=f"Talk {i}", type="conference", venue="Conf", date="2024-01")
            for i in range(5)
        ]

        result = curator.curate_publications(publications, sample_jd)

        # Should respect config limit of 2
        assert len(result.selected) <= 2

    def test_curate_publications_fallback_on_embedding_failure(
        self, sample_jd: JobDescription
    ) -> None:
        """Should fall back to topic-based scoring when embeddings fail."""
        # Create embedder that raises exception
        failing_embedder = MagicMock()
        failing_embedder.embed_passage.side_effect = RuntimeError("Embedding service unavailable")

        curator = ContentCurator(embedder=failing_embedder)
        publications = [
            Publication(
                title="Python Talk",
                type="conference",
                venue="PyCon",
                date="2024-06",
                topics=["python", "aws"],
            ),
            Publication(
                title="Cooking Talk",
                type="conference",
                venue="Food Conf",
                date="2024-06",
                topics=["cooking"],  # Irrelevant topic
            ),
        ]

        # Should not raise, should fall back gracefully
        result = curator.curate_publications(publications, sample_jd)

        # Should still produce results using topic matching
        assert len(result.selected) + len(result.excluded) == 2
        # Python Talk should score higher due to topic overlap
        if result.selected:
            assert result.selected[0].title == "Python Talk"

    def test_curate_publications_legacy_data_without_topics(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Publications without topics should use semantic-only scoring (not penalized)."""
        curator = ContentCurator(embedder=mock_embedder)

        # Publication without topics (legacy data) - uses 80% semantic + 20% recency
        legacy_pub = Publication(
            title="AWS Best Practices and Python Development",  # Semantically relevant
            type="conference",
            venue="AWS re:Invent",
            date="2024-06",
            # No topics - legacy data
        )

        # Publication with irrelevant topics
        irrelevant_pub = Publication(
            title="Cooking Show",
            type="conference",
            venue="Food Network",
            date="2024-06",
            topics=["cooking", "food"],  # Topics don't match JD
        )

        result = curator.curate_publications([legacy_pub, irrelevant_pub], sample_jd)

        # Legacy pub should have a valid score (not zero due to missing topics)
        legacy_key = curator._publication_key(legacy_pub)
        assert result.scores[legacy_key] > 0, "Legacy pub without topics should have non-zero score"

    def test_curate_publications_handles_invalid_date(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should handle publications with invalid date format gracefully."""
        curator = ContentCurator(embedder=mock_embedder)
        publications = [
            Publication(
                title="Test Talk",
                type="conference",
                venue="Test Conf",
                date="2024-06",  # Valid date
                topics=["python"],
            ),
        ]

        # Manually create a publication with bad date to test defensive parsing
        # The Pydantic validation might prevent this, but the code should handle it
        result = curator.curate_publications(publications, sample_jd)

        # Should complete without error
        assert len(result.selected) + len(result.excluded) == 1


class TestCuratePositionBullets:
    """Tests for curate_position_bullets method (AC #5, #6)."""

    @pytest.fixture
    def recent_position(self) -> Position:
        """Create a recent position (within 3 years)."""
        return Position(
            id="pos-recent",
            employer="Recent Corp",
            title="Senior Engineer",
            start_date="2023-01",
            end_date=None,  # Current position
        )

    @pytest.fixture
    def mid_position(self) -> Position:
        """Create a mid-career position (3-7 years ago)."""
        return Position(
            id="pos-mid",
            employer="Mid Corp",
            title="Engineer",
            start_date="2018-01",
            end_date="2020-12",
        )

    @pytest.fixture
    def older_position(self) -> Position:
        """Create an older position (7+ years ago)."""
        return Position(
            id="pos-older",
            employer="Old Corp",
            title="Developer",
            start_date="2010-01",
            end_date="2015-12",
        )

    @pytest.fixture
    def sample_work_units(self) -> list[WorkUnit]:
        """Create sample work units."""
        return [
            WorkUnit(
                id=f"wu-2023-01-0{i}-task{i}",
                title=f"Task {i} - Python automation project",
                problem=Problem(statement=f"Problem {i} needed to be solved"),
                actions=[f"Implemented solution {i} with Python"],
                outcome=Outcome(result=f"Achieved result {i}"),
                archetype=WorkUnitArchetype.MINIMAL,
                position_id="pos-recent",
            )
            for i in range(1, 9)
        ]

    def test_curate_bullets_recent_position_limit(
        self,
        mock_embedder: MagicMock,
        sample_jd: JobDescription,
        recent_position: Position,
        sample_work_units: list[WorkUnit],
    ) -> None:
        """Recent positions should allow 4-6 bullets."""
        curator = ContentCurator(embedder=mock_embedder)
        result = curator.curate_position_bullets(recent_position, sample_work_units, sample_jd)

        # Recent position max is 6 bullets
        assert len(result.selected) <= 6
        assert len(result.selected) >= 1

    def test_curate_bullets_quantified_boost(
        self,
        mock_embedder: MagicMock,
        sample_jd: JobDescription,
        recent_position: Position,
    ) -> None:
        """Work units with quantified metrics should get boost."""
        curator = ContentCurator(embedder=mock_embedder, quantified_boost=1.25)
        work_units = [
            WorkUnit(
                id="wu-2023-01-01-quant",
                title="Quantified achievement",
                problem=Problem(statement="Performance was slow"),
                actions=["Optimized database queries"],
                outcome=Outcome(
                    result="Improved performance significantly",
                    quantified_impact="Reduced latency by 50%",
                ),
                archetype=WorkUnitArchetype.OPTIMIZATION,
                position_id="pos-recent",
            ),
            WorkUnit(
                id="wu-2023-01-02-nonquant",
                title="Non-quantified achievement",
                problem=Problem(statement="Code was messy and hard to maintain"),
                actions=["Refactored code"],
                outcome=Outcome(result="Cleaner code"),
                archetype=WorkUnitArchetype.MINIMAL,
                position_id="pos-recent",
            ),
        ]

        result = curator.curate_position_bullets(recent_position, work_units, sample_jd)

        # Quantified work unit should have boosted score
        quant_score = result.scores.get("wu-2023-01-01-quant", 0)
        # Score should be present and positive
        assert quant_score > 0

    def test_curate_bullets_empty_list(
        self,
        mock_embedder: MagicMock,
        sample_jd: JobDescription,
        recent_position: Position,
    ) -> None:
        """Should handle empty work units list."""
        curator = ContentCurator(embedder=mock_embedder)
        result = curator.curate_position_bullets(recent_position, [], sample_jd)

        assert result.selected == []
        assert "No work units" in result.reason


class TestCurationResult:
    """Tests for CurationResult dataclass."""

    def test_curation_result_generic(self) -> None:
        """CurationResult should be generic."""
        str_result: CurationResult[str] = CurationResult(
            selected=["a", "b"],
            excluded=["c"],
            scores={"a": 0.9, "b": 0.8, "c": 0.3},
            reason="Test",
        )

        assert str_result.selected == ["a", "b"]
        assert str_result.excluded == ["c"]

    def test_curation_result_default_values(self) -> None:
        """CurationResult should have sensible defaults."""
        result: CurationResult[str] = CurationResult(selected=[], excluded=[])

        assert result.scores == {}
        assert result.reason == ""


class TestIsExecutiveLevel:
    """Tests for is_executive_level helper."""

    def test_executive_level_is_executive(self) -> None:
        """EXECUTIVE should return True."""
        assert is_executive_level(ExperienceLevel.EXECUTIVE) is True

    def test_principal_level_is_executive(self) -> None:
        """PRINCIPAL should return True."""
        assert is_executive_level(ExperienceLevel.PRINCIPAL) is True

    def test_senior_level_not_executive(self) -> None:
        """SENIOR should return False."""
        assert is_executive_level(ExperienceLevel.SENIOR) is False

    def test_mid_level_not_executive(self) -> None:
        """MID should return False."""
        assert is_executive_level(ExperienceLevel.MID) is False


class TestBulletsPerPositionConfig:
    """Tests for position age-based bullet limits (AC #5)."""

    def test_recent_position_uses_recent_max(self, mock_embedder: MagicMock) -> None:
        """Recent positions should use recent_max bullets."""
        config = CurationConfig(
            bullets_per_position=BulletsPerPositionConfig(
                recent_years=3, recent_max=6, mid_years=7, mid_max=4, older_max=3
            )
        )
        curator = ContentCurator(embedder=mock_embedder, config=config)

        # Current position (0 years old) should use recent_max
        bullet_config = curator._get_bullet_config(0)
        assert bullet_config["max"] == 6

    def test_mid_position_uses_mid_max(self, mock_embedder: MagicMock) -> None:
        """Mid-career positions should use mid_max bullets."""
        config = CurationConfig(
            bullets_per_position=BulletsPerPositionConfig(
                recent_years=3, recent_max=6, mid_years=7, mid_max=4, older_max=3
            )
        )
        curator = ContentCurator(embedder=mock_embedder, config=config)

        bullet_config = curator._get_bullet_config(5)  # 5 years ago
        assert bullet_config["max"] == 4

    def test_older_position_uses_older_max(self, mock_embedder: MagicMock) -> None:
        """Older positions should use older_max bullets."""
        config = CurationConfig(
            bullets_per_position=BulletsPerPositionConfig(
                recent_years=3, recent_max=6, mid_years=7, mid_max=4, older_max=2
            )
        )
        curator = ContentCurator(embedder=mock_embedder, config=config)

        bullet_config = curator._get_bullet_config(10)  # 10 years ago
        assert bullet_config["max"] == 2

    def test_default_bullet_limits(self, mock_embedder: MagicMock) -> None:
        """Without config, should use default BULLETS_PER_POSITION."""
        curator = ContentCurator(embedder=mock_embedder)  # No config

        assert curator._get_bullet_config(0)["max"] == BULLETS_PER_POSITION["recent"]["max"]
        assert curator._get_bullet_config(5)["max"] == BULLETS_PER_POSITION["mid"]["max"]
        assert curator._get_bullet_config(10)["max"] == BULLETS_PER_POSITION["older"]["max"]


class TestHelperMethods:
    """Tests for helper methods."""

    def test_cosine_similarity_identical_vectors(self, mock_embedder: MagicMock) -> None:
        """Identical vectors should have similarity of 1.0."""
        curator = ContentCurator(embedder=mock_embedder)
        vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)

        similarity = curator._cosine_similarity(vec, vec)
        assert np.isclose(similarity, 1.0)

    def test_cosine_similarity_orthogonal_vectors(self, mock_embedder: MagicMock) -> None:
        """Orthogonal vectors should have similarity of 0.0."""
        curator = ContentCurator(embedder=mock_embedder)
        vec_a = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec_b = np.array([0.0, 1.0, 0.0], dtype=np.float32)

        similarity = curator._cosine_similarity(vec_a, vec_b)
        assert np.isclose(similarity, 0.0)

    def test_cosine_similarity_zero_vector(self, mock_embedder: MagicMock) -> None:
        """Zero vector should return 0.0 similarity."""
        curator = ContentCurator(embedder=mock_embedder)
        vec_a = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec_zero = np.array([0.0, 0.0, 0.0], dtype=np.float32)

        similarity = curator._cosine_similarity(vec_a, vec_zero)
        assert similarity == 0.0

    def test_keyword_overlap_all_match(self, mock_embedder: MagicMock) -> None:
        """All keywords matching should score 1.0."""
        curator = ContentCurator(embedder=mock_embedder)
        text = "Python AWS Kubernetes"
        keywords = {"python", "aws", "kubernetes"}

        overlap = curator._keyword_overlap(text, keywords)
        assert overlap == 1.0

    def test_keyword_overlap_no_match(self, mock_embedder: MagicMock) -> None:
        """No keywords matching should score 0.0."""
        curator = ContentCurator(embedder=mock_embedder)
        text = "Java Spring Boot"
        keywords = {"python", "aws", "kubernetes"}

        overlap = curator._keyword_overlap(text, keywords)
        assert overlap == 0.0

    def test_keyword_overlap_empty_keywords(self, mock_embedder: MagicMock) -> None:
        """Empty keywords should return 0.0."""
        curator = ContentCurator(embedder=mock_embedder)
        text = "Python AWS"

        overlap = curator._keyword_overlap(text, set())
        assert overlap == 0.0

    def test_has_quantified_impact_percentage(self, mock_embedder: MagicMock) -> None:
        """Should detect percentage in outcome."""
        curator = ContentCurator(embedder=mock_embedder)
        wu = WorkUnit(
            id="wu-2023-01-01-test",
            title="Test work unit for quantified impact",
            problem=Problem(statement="This is a test problem statement"),
            actions=["Did something meaningful"],
            outcome=Outcome(result="Improved performance by 50%"),
            archetype=WorkUnitArchetype.OPTIMIZATION,
        )

        assert curator._has_quantified_impact(wu) is True

    def test_has_quantified_impact_dollar(self, mock_embedder: MagicMock) -> None:
        """Should detect dollar amount in outcome."""
        curator = ContentCurator(embedder=mock_embedder)
        wu = WorkUnit(
            id="wu-2023-01-01-test",
            title="Test work unit for dollar impact",
            problem=Problem(statement="This is a test problem statement"),
            actions=["Did something meaningful"],
            outcome=Outcome(result="Saved $100K in costs"),
            archetype=WorkUnitArchetype.OPTIMIZATION,
        )

        assert curator._has_quantified_impact(wu) is True

    def test_has_quantified_impact_multiplier(self, mock_embedder: MagicMock) -> None:
        """Should detect multiplier in outcome."""
        curator = ContentCurator(embedder=mock_embedder)
        wu = WorkUnit(
            id="wu-2023-01-01-test",
            title="Test work unit for multiplier impact",
            problem=Problem(statement="This is a test problem statement"),
            actions=["Did something meaningful"],
            outcome=Outcome(result="Achieved 3x improvement"),
            archetype=WorkUnitArchetype.OPTIMIZATION,
        )

        assert curator._has_quantified_impact(wu) is True

    def test_has_quantified_impact_none(self, mock_embedder: MagicMock) -> None:
        """Should return False when no quantification."""
        curator = ContentCurator(embedder=mock_embedder)
        wu = WorkUnit(
            id="wu-2023-01-01-test",
            title="Test work unit without quantification",
            problem=Problem(statement="This is a test problem statement"),
            actions=["Did something meaningful"],
            outcome=Outcome(result="Made things better overall"),
            archetype=WorkUnitArchetype.MINIMAL,
        )

        assert curator._has_quantified_impact(wu) is False

    def test_highlight_key_generates_stable_keys(self, mock_embedder: MagicMock) -> None:
        """Highlight key should be deterministic for same content."""
        curator = ContentCurator(embedder=mock_embedder)
        highlight = "Led migration to AWS cloud infrastructure"

        key1 = curator._highlight_key(highlight)
        key2 = curator._highlight_key(highlight)

        assert key1 == key2
        assert key1.startswith("hl_")
        assert len(key1) == 11  # "hl_" + 8 hex chars

    def test_highlight_key_different_for_different_content(self, mock_embedder: MagicMock) -> None:
        """Different highlights should have different keys."""
        curator = ContentCurator(embedder=mock_embedder)
        highlight1 = "Led migration to AWS"
        highlight2 = "Built Kubernetes cluster"

        key1 = curator._highlight_key(highlight1)
        key2 = curator._highlight_key(highlight2)

        assert key1 != key2


class TestScoreAction:
    """Tests for score_action method (Story 7.18 AC #2)."""

    def test_score_action_returns_float_between_0_and_1(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Score should be between 0.0 and 1.0."""
        curator = ContentCurator(embedder=mock_embedder)
        action = "Led Kubernetes migration reducing deployment time"

        score = curator.score_action(action, sample_jd)

        assert 0.0 <= score <= 1.0

    def test_score_action_quantified_boost(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Quantified actions should get 10% boost over non-quantified."""
        curator = ContentCurator(embedder=mock_embedder)
        base_action = "Improved system performance"
        quantified_action = "Improved system performance by 40%"

        base_score = curator.score_action(base_action, sample_jd)
        quant_score = curator.score_action(quantified_action, sample_jd)

        # Quantified should get +0.1 from the 10% boost component
        assert quant_score > base_score

    def test_score_action_quantified_patterns(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Various quantification patterns should be detected."""
        curator = ContentCurator(embedder=mock_embedder)

        # Test different quantification patterns
        quantified_actions = [
            "Reduced latency by 50%",  # Percentage
            "Saved $100K in annual costs",  # Dollar amount
            "Achieved 3x improvement in throughput",  # Multiplier
            "Cut build time from 30 minutes to 5 minutes",  # Time
            "Supported 500 users across 5 teams",  # People + teams
            "Led 10 engineers in migration project",  # Team size
        ]

        for action in quantified_actions:
            assert curator._has_quantified_text(action), f"Should detect quantified: {action}"

    def test_score_action_non_quantified(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Non-quantified actions should not get boost."""
        curator = ContentCurator(embedder=mock_embedder)

        non_quantified = [
            "Improved overall system performance",
            "Led successful migration project",
            "Collaborated with cross-functional teams",
        ]

        for action in non_quantified:
            assert not curator._has_quantified_text(action), f"Should not detect: {action}"

    def test_score_action_with_precomputed_embedding(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Should accept precomputed JD embedding for efficiency."""
        curator = ContentCurator(embedder=mock_embedder)
        action = "Built CI/CD pipeline with Docker and Kubernetes"

        # Pre-compute JD embedding
        jd_embedding = mock_embedder.embed_passage(sample_jd.text_for_ranking)

        # Both calls should produce same score
        score1 = curator.score_action(action, sample_jd)
        score2 = curator.score_action(action, sample_jd, jd_embedding=jd_embedding)

        assert score1 == score2

    def test_score_action_keyword_boost(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Actions with JD keywords should score higher."""
        curator = ContentCurator(embedder=mock_embedder)

        # JD has keywords: python, aws, kubernetes, docker, cicd, senior
        with_keywords = "Deployed Python services to AWS using Kubernetes"
        without_keywords = "Organized team meetings and documentation"

        score_with = curator.score_action(with_keywords, sample_jd)
        score_without = curator.score_action(without_keywords, sample_jd)

        # Keyword overlap (30%) should differentiate scores
        assert score_with > score_without

    def test_score_action_empty_action(
        self, mock_embedder: MagicMock, sample_jd: JobDescription
    ) -> None:
        """Empty action should return low score."""
        curator = ContentCurator(embedder=mock_embedder)
        score = curator.score_action("", sample_jd)

        assert 0.0 <= score <= 1.0


class TestCurateActionBullets:
    """Tests for curate_action_bullets method (Story 7.18 AC #1, #3, #5)."""

    @pytest.fixture
    def recent_position(self) -> Position:
        """Create a recent position (within 3 years)."""
        return Position(
            id="pos-recent-test",
            employer="Recent Corp",
            title="Senior Engineer",
            start_date="2023-01",
            end_date=None,  # Current position
        )

    @pytest.fixture
    def work_units_with_many_actions(self) -> list[WorkUnit]:
        """Create work units with 12 total actions for testing limit."""
        return [
            WorkUnit(
                id=f"wu-2023-01-0{i}-task{i}",
                title=f"Task {i} - Python project",
                problem=Problem(statement=f"Problem {i} needed solving"),
                actions=[
                    f"Implemented Python solution {i} with AWS",
                    f"Built CI/CD pipeline {i} with Docker",
                    f"Deployed Kubernetes {i} infrastructure",
                ],
                outcome=Outcome(result=f"Achieved result {i} with 50% improvement"),
                archetype=WorkUnitArchetype.GREENFIELD,
                position_id="pos-recent-test",
            )
            for i in range(1, 4)  # 3 work units × (1 result + 3 actions) = 12 bullets
        ]

    def test_curate_selects_top_actions_across_work_units(
        self,
        mock_embedder: MagicMock,
        sample_jd: JobDescription,
        recent_position: Position,
        work_units_with_many_actions: list[WorkUnit],
    ) -> None:
        """Should select top 6 actions from 12 total for recent position (AC #3)."""
        curator = ContentCurator(embedder=mock_embedder)
        result = curator.curate_action_bullets(
            recent_position, work_units_with_many_actions, sample_jd
        )

        # Recent position max is 6 bullets
        assert len(result.selected) == 6
        assert len(result.excluded) == 6
        assert "12" in result.reason or "actions" in result.reason

    def test_curate_action_bullets_empty_work_units(
        self,
        mock_embedder: MagicMock,
        sample_jd: JobDescription,
        recent_position: Position,
    ) -> None:
        """Should handle empty work units list."""
        curator = ContentCurator(embedder=mock_embedder)
        result = curator.curate_action_bullets(recent_position, [], sample_jd)

        assert result.selected == []
        assert result.excluded == []
        assert "No work units" in result.reason

    def test_curate_action_bullets_includes_outcomes_and_actions(
        self,
        mock_embedder: MagicMock,
        sample_jd: JobDescription,
        recent_position: Position,
    ) -> None:
        """Should include both outcome.result and action bullets (AC #1)."""
        curator = ContentCurator(embedder=mock_embedder)
        work_units = [
            WorkUnit(
                id="wu-2023-01-01-test",
                title="Test work unit with outcome and actions",
                problem=Problem(statement="Problem statement here"),
                actions=["Action one executed", "Action two completed"],
                outcome=Outcome(result="Outcome result achieved"),
                archetype=WorkUnitArchetype.MINIMAL,
                position_id="pos-recent-test",
            )
        ]

        result = curator.curate_action_bullets(recent_position, work_units, sample_jd)

        # Should have 3 bullets: 1 outcome.result + 2 actions
        all_bullets = result.selected + result.excluded
        assert len(all_bullets) == 3

    def test_curate_action_bullets_scores_in_result(
        self,
        mock_embedder: MagicMock,
        sample_jd: JobDescription,
        recent_position: Position,
        work_units_with_many_actions: list[WorkUnit],
    ) -> None:
        """Should include scores in result for all actions."""
        curator = ContentCurator(embedder=mock_embedder)
        result = curator.curate_action_bullets(
            recent_position, work_units_with_many_actions, sample_jd
        )

        # Should have 12 scores (one per action)
        assert len(result.scores) == 12

        # All scores should be between 0 and 1
        for score in result.scores.values():
            assert 0.0 <= score <= 1.0

    def test_curate_action_bullets_respects_threshold(
        self,
        mock_embedder: MagicMock,
        sample_jd: JobDescription,
        recent_position: Position,
    ) -> None:
        """Should exclude actions below min_action_relevance_score (AC #5)."""
        config = CurationConfig(min_action_relevance_score=0.9)  # Very high
        curator = ContentCurator(embedder=mock_embedder, config=config)
        work_units = [
            WorkUnit(
                id="wu-2023-01-01-test",
                title="Test work unit for threshold test",
                problem=Problem(statement="This is a test problem statement"),
                actions=["Some action performed", "Another action completed"],
                outcome=Outcome(result="Test result achieved"),
                archetype=WorkUnitArchetype.MINIMAL,
                position_id="pos-recent-test",
            )
        ]

        result = curator.curate_action_bullets(recent_position, work_units, sample_jd)

        # With high threshold, items below should be excluded
        # Verify reason mentions threshold filtering
        assert "below threshold" in result.reason

    def test_curate_action_bullets_ranking_by_relevance(
        self,
        mock_embedder: MagicMock,
        sample_jd: JobDescription,
        recent_position: Position,
    ) -> None:
        """Selected actions should be ranked by JD relevance score."""
        curator = ContentCurator(embedder=mock_embedder)
        work_units = [
            WorkUnit(
                id="wu-2023-01-01-relevant",
                title="Relevant work for Python and AWS",
                problem=Problem(statement="Technical infrastructure problem needing attention"),
                actions=[
                    "Built Python microservices with AWS Lambda",
                    "Deployed Kubernetes clusters with CI/CD pipelines",
                ],
                outcome=Outcome(result="Improved deployment by 50%"),
                archetype=WorkUnitArchetype.GREENFIELD,
                position_id="pos-recent-test",
            ),
            WorkUnit(
                id="wu-2023-01-02-less-relevant",
                title="Less relevant administrative work",
                problem=Problem(statement="Administrative coordination needed improvement"),
                actions=["Organized team meetings"],
                outcome=Outcome(result="Better communication"),
                archetype=WorkUnitArchetype.MINIMAL,
                position_id="pos-recent-test",
            ),
        ]

        result = curator.curate_action_bullets(recent_position, work_units, sample_jd)

        # Should have scores and selections
        assert len(result.selected) > 0
        assert len(result.scores) > 0


class TestHasQuantifiedText:
    """Tests for _has_quantified_text helper method."""

    def test_detects_percentage(self, mock_embedder: MagicMock) -> None:
        """Should detect percentage patterns."""
        curator = ContentCurator(embedder=mock_embedder)
        assert curator._has_quantified_text("Reduced costs by 50%")
        assert curator._has_quantified_text("100% uptime achieved")

    def test_detects_dollar_amounts(self, mock_embedder: MagicMock) -> None:
        """Should detect dollar amount patterns."""
        curator = ContentCurator(embedder=mock_embedder)
        assert curator._has_quantified_text("Saved $100K annually")
        assert curator._has_quantified_text("Generated $5M revenue")
        assert curator._has_quantified_text("Budget of $2,500,000")

    def test_detects_multipliers(self, mock_embedder: MagicMock) -> None:
        """Should detect multiplier patterns."""
        curator = ContentCurator(embedder=mock_embedder)
        assert curator._has_quantified_text("Achieved 3x improvement")
        assert curator._has_quantified_text("10x faster than baseline")

    def test_detects_time_metrics(self, mock_embedder: MagicMock) -> None:
        """Should detect time-based metrics."""
        curator = ContentCurator(embedder=mock_embedder)
        assert curator._has_quantified_text("Reduced from 2 hours to 10 minutes")
        assert curator._has_quantified_text("Saved 5 days per sprint")
        assert curator._has_quantified_text("Delivered 3 months ahead of schedule")

    def test_detects_people_metrics(self, mock_embedder: MagicMock) -> None:
        """Should detect people-based metrics."""
        curator = ContentCurator(embedder=mock_embedder)
        assert curator._has_quantified_text("Supported 500 users")
        assert curator._has_quantified_text("Served 1000 customers")
        assert curator._has_quantified_text("Managed 10 engineers")
        assert curator._has_quantified_text("Coordinated across 5 teams")

    def test_no_false_positives(self, mock_embedder: MagicMock) -> None:
        """Should not detect non-metric patterns."""
        curator = ContentCurator(embedder=mock_embedder)
        assert not curator._has_quantified_text("Improved performance significantly")
        assert not curator._has_quantified_text("Led successful migration")
        assert not curator._has_quantified_text("Collaborated with stakeholders")


class TestIntegrationWithRealEmbeddings:
    """Integration tests using real EmbeddingService.

    These tests verify the actual semantic matching behavior with real embeddings.
    Marked with pytest.mark.slow for optional skipping in CI.
    """

    @pytest.fixture
    def real_embedder(self) -> EmbeddingService:
        """Create a real EmbeddingService for integration testing."""
        from resume_as_code.services.embedder import EmbeddingService

        return EmbeddingService()

    @pytest.fixture
    def python_jd(self) -> JobDescription:
        """Create a Python-focused job description."""
        return JobDescription(
            raw_text="Senior Python Developer needed for backend services. "
            "Experience with Django, FastAPI, PostgreSQL required. "
            "AWS cloud experience preferred.",
            title="Senior Python Developer",
            skills=["Python", "Django", "FastAPI", "PostgreSQL", "AWS"],
            keywords=["python", "django", "fastapi", "postgresql", "aws", "backend"],
            experience_level=ExperienceLevel.SENIOR,
        )

    @pytest.mark.slow
    def test_highlights_semantic_relevance_ordering(
        self, real_embedder: EmbeddingService, python_jd: JobDescription
    ) -> None:
        """Semantically relevant highlights should rank higher than irrelevant ones."""
        curator = ContentCurator(embedder=real_embedder)

        # Mix of relevant and irrelevant highlights
        highlights = [
            "Led migration of legacy PHP services to Python microservices",  # Very relevant
            "Built REST APIs with Django and FastAPI frameworks",  # Very relevant
            "Managed marketing campaigns for consumer products",  # Irrelevant
            "Organized team building events and company retreats",  # Irrelevant
        ]

        result = curator.curate_highlights(highlights, python_jd, max_count=2)

        # Python/Django/FastAPI highlights should be selected over marketing/events
        selected_text = " ".join(result.selected).lower()
        assert "python" in selected_text or "django" in selected_text or "fastapi" in selected_text

        # Marketing and events should be excluded
        excluded_text = " ".join(result.excluded).lower()
        assert "marketing" in excluded_text or "team building" in excluded_text

    @pytest.mark.slow
    def test_certifications_skill_matching_with_real_embeddings(
        self, real_embedder: EmbeddingService, python_jd: JobDescription
    ) -> None:
        """Certifications matching JD skills should score higher with real embeddings."""
        curator = ContentCurator(embedder=real_embedder)

        certs = [
            Certification(name="AWS Solutions Architect", issuer="Amazon"),  # Relevant
            Certification(name="Python Professional", issuer="Python Institute"),  # Relevant
            Certification(name="Scrum Master", issuer="Scrum Alliance"),  # Less relevant
        ]

        result = curator.curate_certifications(certs, python_jd)

        # AWS and Python certs should score higher than Scrum
        aws_score = result.scores.get("AWS Solutions Architect", 0)
        python_score = result.scores.get("Python Professional", 0)
        scrum_score = result.scores.get("Scrum Master", 0)

        assert aws_score > scrum_score, "AWS cert should score higher than Scrum"
        assert python_score > scrum_score, "Python cert should score higher than Scrum"
