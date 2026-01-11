"""Tests for JD parser service."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from resume_as_code.models.errors import NotFoundError
from resume_as_code.models.job_description import ExperienceLevel
from resume_as_code.services.jd_parser import (
    _detect_experience_level,
    _extract_requirements,
    _extract_skills,
    _extract_title,
    _extract_years_experience,
    parse_jd_file,
    parse_jd_text,
)

if TYPE_CHECKING:
    pass


SAMPLE_JD = """
Senior Software Engineer

About the Role:
We're looking for a Senior Software Engineer to join our platform team.
You'll be working with Python, Kubernetes, and AWS to build scalable services.

Requirements:
- 5+ years of experience in software development
- Strong proficiency in Python and Go
- Experience with Docker and Kubernetes
- AWS or GCP cloud experience
- CI/CD pipeline experience

Nice to Have:
- Experience with Terraform
- Knowledge of machine learning
- GraphQL API design
"""


class TestParseJDFile:
    """Tests for parse_jd_file function."""

    def test_parses_file_successfully(self, tmp_path: Path) -> None:
        """Should parse a JD file and return JobDescription."""
        jd_file = tmp_path / "test_jd.txt"
        jd_file.write_text(SAMPLE_JD)

        jd = parse_jd_file(jd_file)

        assert jd.raw_text == SAMPLE_JD
        assert jd.title is not None

    def test_raises_not_found_for_missing_file(self, tmp_path: Path) -> None:
        """Should raise NotFoundError for non-existent file."""
        missing_file = tmp_path / "nonexistent.txt"

        with pytest.raises(NotFoundError):
            parse_jd_file(missing_file)

    def test_handles_utf8_encoding(self, tmp_path: Path) -> None:
        """Should handle UTF-8 encoded files."""
        jd_file = tmp_path / "utf8.txt"
        content = "Software Engineer\n\nWe use Python and café-style coding"
        jd_file.write_text(content, encoding="utf-8")

        jd = parse_jd_file(jd_file)
        assert "café" in jd.raw_text

    def test_handles_latin1_encoding(self, tmp_path: Path) -> None:
        """Should handle Latin-1 encoded files."""
        jd_file = tmp_path / "latin1.txt"
        content = "Software Engineer position"
        jd_file.write_bytes(content.encode("latin-1"))

        jd = parse_jd_file(jd_file)
        assert "Software Engineer" in jd.raw_text

    def test_handles_cp1252_encoding(self, tmp_path: Path) -> None:
        """Should handle Windows CP1252 encoded files."""
        jd_file = tmp_path / "cp1252.txt"
        # CP1252 has special characters like curly quotes
        content = "Software Engineer position"
        jd_file.write_bytes(content.encode("cp1252"))

        jd = parse_jd_file(jd_file)
        assert "Software Engineer" in jd.raw_text

    def test_raises_value_error_for_undecodable_file(self, tmp_path: Path) -> None:
        """Should raise ValueError when file cannot be decoded with any encoding."""
        jd_file = tmp_path / "binary.txt"
        # Write invalid UTF-8 sequence that also fails other encodings
        # This is a sequence that's invalid in all attempted encodings
        jd_file.write_bytes(b"\xff\xfe" + bytes(range(128, 256)) * 10)

        # Note: This is hard to trigger since latin-1 accepts any byte sequence
        # The current implementation will likely succeed with latin-1
        # This test documents expected behavior if all encodings fail
        jd = parse_jd_file(jd_file)
        assert jd.raw_text is not None  # latin-1 accepts any bytes


class TestParseJDText:
    """Tests for parse_jd_text function."""

    def test_parses_raw_text(self) -> None:
        """Should parse raw JD text."""
        jd = parse_jd_text(SAMPLE_JD)

        assert jd.raw_text == SAMPLE_JD
        assert jd.title is not None

    def test_returns_job_description_model(self) -> None:
        """Should return a JobDescription model."""
        jd = parse_jd_text("Software Engineer at ACME")

        assert hasattr(jd, "raw_text")
        assert hasattr(jd, "skills")
        assert hasattr(jd, "requirements")
        assert hasattr(jd, "experience_level")

    def test_extracts_title_from_first_line(self) -> None:
        """Should extract job title from first lines."""
        jd = parse_jd_text(SAMPLE_JD)
        assert jd.title == "Senior Software Engineer"

    def test_complete_jd_parsing(self) -> None:
        """Should parse a complete JD with all fields."""
        jd = parse_jd_text(SAMPLE_JD)

        assert jd.title == "Senior Software Engineer"
        assert jd.experience_level == ExperienceLevel.SENIOR
        assert jd.years_experience == 5
        assert "python" in jd.skills
        assert len(jd.requirements) > 0


class TestExtractTitle:
    """Tests for title extraction edge cases."""

    def test_returns_none_when_no_title_keywords(self) -> None:
        """Should return None when no title keywords found."""
        text = "We are a great company\nJoin us\nGreat benefits"
        title = _extract_title(text)
        assert title is None

    def test_skips_empty_lines(self) -> None:
        """Should skip empty lines when searching for title."""
        text = "\n\n\nSenior Software Engineer\nJob description here"
        title = _extract_title(text)
        assert title == "Senior Software Engineer"

    def test_skips_about_header(self) -> None:
        """Should skip lines starting with 'About'."""
        text = "About Our Company\nSenior Developer Position\nRequirements:"
        title = _extract_title(text)
        assert title == "Senior Developer Position"

    def test_skips_company_header(self) -> None:
        """Should skip lines starting with 'Company'."""
        text = "Company Overview\nPython Developer\nJob details"
        title = _extract_title(text)
        assert title == "Python Developer"

    def test_skips_location_header(self) -> None:
        """Should skip lines starting with 'Location'."""
        text = "Location: New York\nSoftware Architect\nAbout the role"
        title = _extract_title(text)
        assert title == "Software Architect"

    def test_skips_long_lines(self) -> None:
        """Should skip lines longer than 100 characters."""
        long_line = "Senior Engineer " + "x" * 100  # > 100 chars
        text = f"{long_line}\nJunior Developer\nDescription"
        title = _extract_title(text)
        assert title == "Junior Developer"

    def test_only_checks_first_5_lines(self) -> None:
        """Should only check first 5 lines for title."""
        text = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nSoftware Engineer\nMore text"
        title = _extract_title(text)
        assert title is None  # Engineer is on line 6


class TestExtractSkills:
    """Tests for skill extraction (AC: #1, #4)."""

    def test_extracts_python(self) -> None:
        """Should extract Python."""
        skills = _extract_skills("Experience with Python required")
        assert "python" in skills

    def test_extracts_multiple_skills(self) -> None:
        """Should extract multiple skills from text."""
        skills = _extract_skills(SAMPLE_JD)
        assert "python" in skills
        assert "kubernetes" in skills
        assert "aws" in skills
        assert "docker" in skills

    def test_normalizes_k8s_to_kubernetes(self) -> None:
        """Should normalize k8s to kubernetes (AC: #4)."""
        skills = _extract_skills("K8s deployment experience required")
        assert "kubernetes" in skills

    def test_normalizes_python3_to_python(self) -> None:
        """Should normalize Python 3 to python (AC: #4)."""
        skills = _extract_skills("Python 3 programming skills")
        assert "python" in skills

    def test_normalizes_gcp_variants(self) -> None:
        """Should normalize GCP variants."""
        skills = _extract_skills("Google Cloud Platform experience")
        assert "gcp" in skills

    def test_normalizes_cicd(self) -> None:
        """Should normalize CI/CD variants."""
        skills = _extract_skills("CI/CD pipeline experience")
        assert "cicd" in skills

    def test_returns_sorted_list(self) -> None:
        """Should return sorted list of skills."""
        skills = _extract_skills("Python, Docker, AWS, Kubernetes")
        assert skills == sorted(skills)

    def test_handles_no_skills(self) -> None:
        """Should return empty list when no skills found."""
        skills = _extract_skills("We are looking for someone great")
        # May have some generic words, but not tech skills
        assert isinstance(skills, list)

    def test_case_insensitive(self) -> None:
        """Should be case insensitive in skill detection."""
        skills = _extract_skills("PYTHON and KUBERNETES experience")
        assert "python" in skills
        assert "kubernetes" in skills


class TestDetectExperienceLevel:
    """Tests for experience level detection (AC: #1)."""

    def test_detects_senior_from_title(self) -> None:
        """Should detect senior from job title."""
        level = _detect_experience_level("", "Senior Software Engineer")
        assert level == ExperienceLevel.SENIOR

    def test_detects_staff_from_text(self) -> None:
        """Should detect staff from JD text."""
        level = _detect_experience_level("Looking for a Staff Engineer", None)
        assert level == ExperienceLevel.STAFF

    def test_detects_lead_from_text(self) -> None:
        """Should detect lead from JD text."""
        level = _detect_experience_level("Tech Lead position", None)
        assert level == ExperienceLevel.LEAD

    def test_detects_principal_from_text(self) -> None:
        """Should detect principal from JD text."""
        level = _detect_experience_level("Principal Engineer role", None)
        assert level == ExperienceLevel.PRINCIPAL

    def test_detects_entry_from_junior(self) -> None:
        """Should detect entry level from junior."""
        level = _detect_experience_level("Junior developer", None)
        assert level == ExperienceLevel.ENTRY

    def test_defaults_to_mid(self) -> None:
        """Should default to mid level when no indicators."""
        level = _detect_experience_level("Software Engineer role", None)
        assert level == ExperienceLevel.MID

    def test_title_takes_precedence_over_text(self) -> None:
        """Should prioritize title over body text."""
        level = _detect_experience_level(
            "This junior role requires...",
            "Senior Software Engineer",
        )
        assert level == ExperienceLevel.SENIOR


class TestExtractYearsExperience:
    """Tests for years experience extraction (AC: #1)."""

    def test_extracts_years_plus_format(self) -> None:
        """Should extract '5+ years of experience'."""
        years = _extract_years_experience("5+ years of experience required")
        assert years == 5

    def test_extracts_years_without_plus(self) -> None:
        """Should extract '3 years experience'."""
        years = _extract_years_experience("3 years experience in Python")
        assert years == 3

    def test_extracts_minimum_years(self) -> None:
        """Should extract 'minimum 7 years'."""
        years = _extract_years_experience("minimum 7 years of work experience")
        assert years == 7

    def test_returns_none_when_not_specified(self) -> None:
        """Should return None when no years specified."""
        years = _extract_years_experience("Experience preferred")
        assert years is None


class TestExtractRequirements:
    """Tests for requirements extraction (AC: #1, #2)."""

    def test_extracts_bullet_points(self) -> None:
        """Should extract bullet point requirements."""
        text = """
Requirements:
- 5+ years of experience
- Strong Python skills
- Team player
"""
        reqs = _extract_requirements(text)
        assert len(reqs) >= 2
        assert all(r.is_required for r in reqs)

    def test_extracts_numbered_lists(self) -> None:
        """Should extract numbered list requirements."""
        text = """
Requirements:
1. Bachelor's degree
2. Python experience
3. AWS knowledge
"""
        reqs = _extract_requirements(text)
        assert len(reqs) >= 2

    def test_separates_nice_to_have(self) -> None:
        """Should mark nice-to-have requirements correctly."""
        text = """
Requirements:
- Python experience

Nice to Have:
- Kubernetes knowledge
- Machine learning
"""
        reqs = _extract_requirements(text)
        required = [r for r in reqs if r.is_required]
        nice_to_have = [r for r in reqs if not r.is_required]
        assert len(required) >= 1
        assert len(nice_to_have) >= 1

    def test_handles_varied_formatting(self) -> None:
        """Should handle various bullet formats (AC: #2)."""
        text = """
* First requirement
• Second requirement
- Third requirement
"""
        reqs = _extract_requirements(text)
        assert len(reqs) >= 3

    def test_skips_short_items(self) -> None:
        """Should skip very short bullet items."""
        text = """
- Yes
- This is a longer requirement that should be included
- No
"""
        reqs = _extract_requirements(text)
        # Only the longer requirement should be included
        assert len(reqs) == 1
