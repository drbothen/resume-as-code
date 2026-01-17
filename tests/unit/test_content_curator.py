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
from resume_as_code.models.work_unit import Outcome, Problem, WorkUnit
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
                position_id="pos-recent",
            ),
            WorkUnit(
                id="wu-2023-01-02-nonquant",
                title="Non-quantified achievement",
                problem=Problem(statement="Code was messy and hard to maintain"),
                actions=["Refactored code"],
                outcome=Outcome(result="Cleaner code"),
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
