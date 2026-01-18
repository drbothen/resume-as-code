"""Tests for Education model."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from resume_as_code.models.education import Education


class TestEducationModel:
    """Tests for Education model."""

    def test_minimal_education(self) -> None:
        """Should create education with required fields only."""
        edu = Education(
            degree="BS Computer Science",
            institution="MIT",
        )
        assert edu.degree == "BS Computer Science"
        assert edu.institution == "MIT"
        assert edu.graduation_year is None
        assert edu.honors is None
        assert edu.gpa is None
        assert edu.display is True

    def test_full_education(self) -> None:
        """Should create education with all fields."""
        edu = Education(
            degree="BS Computer Science",
            institution="UT Austin",
            graduation_year="2012",
            honors="Magna Cum Laude",
            gpa="3.8/4.0",
            display=True,
        )
        assert edu.degree == "BS Computer Science"
        assert edu.institution == "UT Austin"
        assert edu.graduation_year == "2012"
        assert edu.honors == "Magna Cum Laude"
        assert edu.gpa == "3.8/4.0"
        assert edu.display is True

    def test_year_validation_valid_yyyy(self) -> None:
        """Should accept YYYY year format."""
        edu = Education(degree="BS", institution="School", graduation_year="2012")
        assert edu.graduation_year == "2012"

    def test_year_normalization_longer_date(self) -> None:
        """Should normalize longer date to YYYY."""
        edu = Education(degree="BS", institution="School", graduation_year="2012-05")
        assert edu.graduation_year == "2012"

    def test_year_normalization_full_date(self) -> None:
        """Should normalize YYYY-MM-DD to YYYY."""
        edu = Education(degree="BS", institution="School", graduation_year="2012-05-15")
        assert edu.graduation_year == "2012"

    def test_year_validation_invalid(self) -> None:
        """Should reject invalid year format."""
        with pytest.raises(ValidationError):
            Education(degree="BS", institution="School", graduation_year="invalid")

    def test_year_validation_invalid_partial(self) -> None:
        """Should reject year without 4 digits at start."""
        with pytest.raises(ValidationError):
            Education(degree="BS", institution="School", graduation_year="12")

    def test_display_default_true(self) -> None:
        """Display should default to True."""
        edu = Education(degree="BS", institution="School")
        assert edu.display is True

    def test_display_can_be_false(self) -> None:
        """Display can be set to False for hiding."""
        edu = Education(degree="Old Degree", institution="Old School", display=False)
        assert edu.display is False


class TestEducationFormatDisplay:
    """Tests for education display formatting."""

    def test_format_display_minimal(self) -> None:
        """Should format with minimal data."""
        edu = Education(degree="MBA", institution="Harvard")
        display = edu.format_display()
        assert display == "MBA, Harvard"

    def test_format_display_with_year(self) -> None:
        """Should format with year."""
        edu = Education(degree="MBA", institution="Harvard", graduation_year="2020")
        display = edu.format_display()
        assert display == "MBA, Harvard, 2020"

    def test_format_display_with_honors(self) -> None:
        """Should format with honors."""
        edu = Education(
            degree="BS Computer Science",
            institution="UT Austin",
            graduation_year="2012",
            honors="Magna Cum Laude",
        )
        display = edu.format_display()
        assert "BS Computer Science" in display
        assert "UT Austin" in display
        assert "2012" in display
        assert "Magna Cum Laude" in display
        assert " - Magna Cum Laude" in display

    def test_format_display_with_gpa_no_honors(self) -> None:
        """Should format with GPA when no honors."""
        edu = Education(
            degree="BS Computer Science",
            institution="UT Austin",
            graduation_year="2012",
            gpa="3.8/4.0",
        )
        display = edu.format_display()
        assert "BS Computer Science" in display
        assert "UT Austin" in display
        assert "2012" in display
        assert "GPA: 3.8/4.0" in display

    def test_format_display_honors_takes_precedence_over_gpa(self) -> None:
        """Should show honors but not GPA when both present."""
        edu = Education(
            degree="BS Computer Science",
            institution="UT Austin",
            graduation_year="2012",
            honors="Magna Cum Laude",
            gpa="3.8/4.0",
        )
        display = edu.format_display()
        assert "Magna Cum Laude" in display
        assert "GPA" not in display


class TestResumeConfigEducation:
    """Tests for education in ResumeConfig."""

    def test_education_default_empty(self) -> None:
        """ResumeConfig should default to None for education (Story 9.2).

        Note: Access education via data_loader for actual usage.
        """
        from resume_as_code.models.config import ResumeConfig

        config = ResumeConfig()
        assert config.education is None

    def test_education_list(self) -> None:
        """ResumeConfig should accept education list."""
        from resume_as_code.models.config import ResumeConfig

        config = ResumeConfig(
            education=[
                Education(degree="BS Computer Science", institution="MIT"),
                Education(degree="MBA", institution="Harvard"),
            ]
        )
        assert len(config.education) == 2
        assert config.education[0].degree == "BS Computer Science"
        assert config.education[1].degree == "MBA"

    def test_education_from_dict(self) -> None:
        """ResumeConfig should parse education from dict."""
        from resume_as_code.models.config import ResumeConfig

        config = ResumeConfig(
            education=[
                {"degree": "BS Computer Science", "institution": "MIT"},
                {"degree": "MBA", "institution": "Harvard", "graduation_year": "2020"},
            ]
        )
        assert len(config.education) == 2
        assert config.education[0].institution == "MIT"
        assert config.education[1].graduation_year == "2020"


class TestEducationLoadingFromConfig:
    """Tests for education loading from config files."""

    def test_education_load_from_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Education should load from .resume.yaml file."""
        from resume_as_code.config import get_config, reset_config

        reset_config()
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
education:
  - degree: "Bachelor of Science in Computer Science"
    institution: "University of Texas at Austin"
    graduation_year: "2012"
    honors: "Magna Cum Laude"
  - degree: "Master of Science in Cybersecurity"
    institution: "Georgia Tech"
    graduation_year: "2018"
"""
        )
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            assert len(config.education) == 2
            assert config.education[0].degree == "Bachelor of Science in Computer Science"
            assert config.education[0].institution == "University of Texas at Austin"
            assert config.education[0].graduation_year == "2012"
            assert config.education[0].honors == "Magna Cum Laude"
            assert config.education[1].degree == "Master of Science in Cybersecurity"
            assert config.education[1].graduation_year == "2018"

    def test_education_empty_when_not_in_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Education should be empty when not in config file."""
        from resume_as_code.config import get_config, reset_config

        reset_config()
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            # Story 9.2: config.education is None when not in config
            # Use data_loader for actual access
            assert config.education is None

    def test_education_with_display_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Education with display: false should load correctly."""
        from resume_as_code.config import get_config, reset_config

        reset_config()
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
education:
  - degree: "Old Degree"
    institution: "Old School"
    display: false
  - degree: "Current Degree"
    institution: "Current School"
    display: true
"""
        )
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            assert len(config.education) == 2
            assert config.education[0].display is False
            assert config.education[1].display is True


class TestEducationInResumeData:
    """Tests for education in ResumeData model."""

    def test_resume_data_with_education(self) -> None:
        """ResumeData should accept education list."""
        from resume_as_code.models.resume import ContactInfo, ResumeData

        edu_list = [
            Education(degree="BS Computer Science", institution="MIT", graduation_year="2015"),
            Education(degree="MBA", institution="Harvard", graduation_year="2020"),
        ]
        contact = ContactInfo(name="Test User")
        resume = ResumeData(contact=contact, education=edu_list)

        assert len(resume.education) == 2
        assert resume.education[0].degree == "BS Computer Science"
        assert resume.education[1].institution == "Harvard"

    def test_resume_data_empty_education_default(self) -> None:
        """ResumeData should default to empty education list."""
        from resume_as_code.models.resume import ContactInfo, ResumeData

        contact = ContactInfo(name="Test User")
        resume = ResumeData(contact=contact)

        assert resume.education == []
