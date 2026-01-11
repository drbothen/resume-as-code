"""Integration tests for JD parser with sample files."""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_as_code.models.job_description import ExperienceLevel, JobDescription
from resume_as_code.services.jd_parser import parse_jd_file

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "job_descriptions"


class TestSeniorEngineerJD:
    """Integration tests with senior_engineer.txt sample file."""

    @pytest.fixture
    def jd(self) -> JobDescription:
        """Parse the senior engineer JD fixture."""

        return parse_jd_file(FIXTURES_DIR / "senior_engineer.txt")

    def test_extracts_title(self, jd: JobDescription) -> None:
        """Should extract job title from file."""
        assert jd.title is not None
        assert "Senior" in jd.title
        assert "Engineer" in jd.title

    def test_detects_senior_level(self, jd: JobDescription) -> None:
        """Should detect senior experience level."""
        assert jd.experience_level == ExperienceLevel.SENIOR

    def test_extracts_years_experience(self, jd: JobDescription) -> None:
        """Should extract 5+ years requirement."""
        assert jd.years_experience == 5

    def test_extracts_expected_skills(self, jd: JobDescription) -> None:
        """Should extract all major skills mentioned."""
        expected_skills = {"python", "docker", "kubernetes", "aws", "gcp", "cicd", "postgresql"}
        found_skills = set(jd.skills)
        # Check that most expected skills are found
        assert len(expected_skills & found_skills) >= 5

    def test_separates_required_vs_nice_to_have(self, jd: JobDescription) -> None:
        """Should separate required and nice-to-have requirements."""
        required = [r for r in jd.requirements if r.is_required]
        nice_to_have = [r for r in jd.requirements if not r.is_required]
        assert len(required) >= 3
        assert len(nice_to_have) >= 2

    def test_extracts_keywords(self, jd: JobDescription) -> None:
        """Should extract relevant keywords."""
        assert len(jd.keywords) > 0
        # Common words from the JD should appear
        keyword_text = " ".join(jd.keywords)
        assert any(kw in keyword_text for kw in ["experience", "engineering", "team"])


class TestJuniorDeveloperJD:
    """Integration tests with junior_developer.txt sample file."""

    @pytest.fixture
    def jd(self) -> JobDescription:
        """Parse the junior developer JD fixture."""

        return parse_jd_file(FIXTURES_DIR / "junior_developer.txt")

    def test_extracts_title(self, jd: JobDescription) -> None:
        """Should extract job title."""
        assert jd.title is not None
        assert "Developer" in jd.title

    def test_detects_entry_level(self, jd: JobDescription) -> None:
        """Should detect entry/junior experience level."""
        # "Junior" or "entry-level" in text should trigger ENTRY level
        assert jd.experience_level == ExperienceLevel.ENTRY

    def test_extracts_skills_from_varied_formats(self, jd: JobDescription) -> None:
        """Should extract skills from numbered lists and bullet points."""
        # The JD uses both numbered (1. 2. 3.) and bullet (* *) lists
        found_skills = set(jd.skills)
        assert "python" in found_skills or "javascript" in found_skills
        assert "git" in found_skills

    def test_handles_asterisk_bullets(self, jd: JobDescription) -> None:
        """Should handle asterisk bullet points."""
        # Requirements should be extracted from * bullets
        assert len(jd.requirements) >= 3


class TestStaffEngineerMarkdownJD:
    """Integration tests with staff_engineer_markdown.md sample file."""

    @pytest.fixture
    def jd(self) -> JobDescription:
        """Parse the staff engineer markdown JD fixture."""

        return parse_jd_file(FIXTURES_DIR / "staff_engineer_markdown.md")

    def test_extracts_title_from_markdown(self, jd: JobDescription) -> None:
        """Should extract title from markdown header."""
        # Title extraction should still work with markdown
        assert jd.title is not None
        assert "Engineer" in jd.title

    def test_detects_staff_level(self, jd: JobDescription) -> None:
        """Should detect staff experience level."""
        assert jd.experience_level == ExperienceLevel.STAFF

    def test_extracts_years_from_markdown(self, jd: JobDescription) -> None:
        """Should extract 8 years requirement."""
        assert jd.years_experience == 8

    def test_normalizes_k8s_to_kubernetes(self, jd: JobDescription) -> None:
        """Should normalize K8s to kubernetes."""
        assert "kubernetes" in jd.skills

    def test_normalizes_python3_to_python(self, jd: JobDescription) -> None:
        """Should normalize Python 3 to python."""
        assert "python" in jd.skills

    def test_extracts_terraform(self, jd: JobDescription) -> None:
        """Should extract terraform skill."""
        assert "terraform" in jd.skills

    def test_handles_markdown_bullet_formats(self, jd: JobDescription) -> None:
        """Should handle markdown list formats with bold text."""
        # Requirements should still be extracted despite markdown formatting
        assert len(jd.requirements) >= 3


class TestJDParserRobustness:
    """Tests for parser robustness across all sample files."""

    def test_all_fixture_files_parse_without_error(self) -> None:
        """Should parse all fixture files without raising exceptions."""
        for jd_file in FIXTURES_DIR.glob("*"):
            if jd_file.is_file():
                jd = parse_jd_file(jd_file)
                assert jd.raw_text is not None
                assert len(jd.raw_text) > 0

    def test_all_fixture_files_have_skills(self) -> None:
        """Should extract at least some skills from all files."""
        for jd_file in FIXTURES_DIR.glob("*"):
            if jd_file.is_file():
                jd = parse_jd_file(jd_file)
                assert len(jd.skills) >= 1, f"No skills found in {jd_file.name}"

    def test_all_fixture_files_have_requirements(self) -> None:
        """Should extract at least some requirements from all files."""
        for jd_file in FIXTURES_DIR.glob("*"):
            if jd_file.is_file():
                jd = parse_jd_file(jd_file)
                assert len(jd.requirements) >= 1, f"No requirements found in {jd_file.name}"
