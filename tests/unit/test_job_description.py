"""Tests for JobDescription model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from resume_as_code.models.job_description import (
    ExperienceLevel,
    JobDescription,
    Requirement,
)


class TestExperienceLevel:
    """Tests for ExperienceLevel enum."""

    def test_experience_level_values(self) -> None:
        """Should have all expected experience levels."""
        assert ExperienceLevel.ENTRY.value == "entry"
        assert ExperienceLevel.MID.value == "mid"
        assert ExperienceLevel.SENIOR.value == "senior"
        assert ExperienceLevel.STAFF.value == "staff"
        assert ExperienceLevel.LEAD.value == "lead"
        assert ExperienceLevel.PRINCIPAL.value == "principal"
        assert ExperienceLevel.EXECUTIVE.value == "executive"


class TestRequirement:
    """Tests for Requirement model."""

    def test_create_required_requirement(self) -> None:
        """Should create a required requirement."""
        req = Requirement(text="5+ years of Python experience")
        assert req.text == "5+ years of Python experience"
        assert req.is_required is True
        assert req.category is None

    def test_create_nice_to_have_requirement(self) -> None:
        """Should create a nice-to-have requirement."""
        req = Requirement(
            text="Machine learning experience",
            is_required=False,
            category="technical",
        )
        assert req.text == "Machine learning experience"
        assert req.is_required is False
        assert req.category == "technical"


class TestJobDescription:
    """Tests for JobDescription model."""

    def test_create_minimal_job_description(self) -> None:
        """Should create a JobDescription with only raw_text."""
        jd = JobDescription(raw_text="Software Engineer position")
        assert jd.raw_text == "Software Engineer position"
        assert jd.title is None
        assert jd.company is None
        assert jd.skills == []
        assert jd.requirements == []
        assert jd.experience_level == ExperienceLevel.MID
        assert jd.years_experience is None
        assert jd.keywords == []

    def test_create_full_job_description(self) -> None:
        """Should create a JobDescription with all fields."""
        reqs = [
            Requirement(text="Python experience", is_required=True),
            Requirement(text="Go experience", is_required=False),
        ]
        jd = JobDescription(
            raw_text="Full JD text here",
            title="Senior Software Engineer",
            company="ACME Corp",
            skills=["python", "kubernetes", "aws"],
            requirements=reqs,
            experience_level=ExperienceLevel.SENIOR,
            years_experience=5,
            keywords=["engineer", "cloud", "platform"],
        )
        assert jd.title == "Senior Software Engineer"
        assert jd.company == "ACME Corp"
        assert jd.skills == ["python", "kubernetes", "aws"]
        assert len(jd.requirements) == 2
        assert jd.experience_level == ExperienceLevel.SENIOR
        assert jd.years_experience == 5
        assert "platform" in jd.keywords

    def test_text_for_ranking_property(self) -> None:
        """Should combine title and raw_text for ranking."""
        jd = JobDescription(
            raw_text="Looking for an engineer",
            title="Senior Software Engineer",
        )
        ranking_text = jd.text_for_ranking
        assert "Senior Software Engineer" in ranking_text
        assert "Looking for an engineer" in ranking_text

    def test_text_for_ranking_without_title(self) -> None:
        """Should return just raw_text when no title."""
        jd = JobDescription(raw_text="Looking for an engineer")
        assert jd.text_for_ranking == "Looking for an engineer"

    def test_raw_text_required(self) -> None:
        """Should require raw_text field."""
        with pytest.raises(PydanticValidationError):
            JobDescription()  # type: ignore[call-arg]
