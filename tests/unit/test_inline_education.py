"""Tests for inline education creation (Story 6.9 extension).

Tests for:
- new education command with non-interactive flags
- JSON output format
- Duplicate detection
- EducationService
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main as cli


class TestNewEducationCommand:
    """Tests for 'new education' command."""

    def test_creates_education_non_interactive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create education with --degree and --institution flags."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "education",
                "--degree",
                "BS Computer Science",
                "--institution",
                "MIT",
                "--year",
                "2015",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Education created" in result.output
        assert (tmp_path / ".resume.yaml").exists()

        # Verify file content
        import yaml

        with open(tmp_path / ".resume.yaml") as f:
            data = yaml.safe_load(f)

        assert "education" in data
        assert len(data["education"]) == 1
        assert data["education"][0]["degree"] == "BS Computer Science"
        assert data["education"][0]["institution"] == "MIT"
        assert data["education"][0]["graduation_year"] == "2015"

    def test_education_with_all_fields(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create education with all optional fields."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "education",
                "--degree",
                "MS Cybersecurity",
                "--institution",
                "Georgia Tech",
                "--year",
                "2018",
                "--honors",
                "Magna Cum Laude",
                "--gpa",
                "3.9/4.0",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"

        import yaml

        with open(tmp_path / ".resume.yaml") as f:
            data = yaml.safe_load(f)

        edu = data["education"][0]
        assert edu["degree"] == "MS Cybersecurity"
        assert edu["institution"] == "Georgia Tech"
        assert edu["graduation_year"] == "2018"
        assert edu["honors"] == "Magna Cum Laude"
        assert edu["gpa"] == "3.9/4.0"

    def test_education_json_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return structured JSON output."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--json",
                "new",
                "education",
                "--degree",
                "BS Test",
                "--institution",
                "Test University",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["education_created"] is True
        assert data["data"]["degree"] == "BS Test"
        assert data["data"]["institution"] == "Test University"

    def test_education_duplicate_detection(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should detect and report duplicate education records."""
        monkeypatch.chdir(tmp_path)

        # Create initial education
        (tmp_path / ".resume.yaml").write_text(
            """education:
  - degree: "BS Computer Science"
    institution: "MIT"
"""
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--json",
                "new",
                "education",
                "--degree",
                "BS Computer Science",
                "--institution",
                "MIT",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["education_created"] is False

    def test_education_invalid_year_format(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error on invalid year format."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "education",
                "--degree",
                "Test",
                "--institution",
                "Test Uni",
                "--year",
                "20",
            ],
        )

        assert result.exit_code != 0
        assert "invalid" in result.output.lower() or "YYYY" in result.output

    def test_education_case_insensitive_matching(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should match education case-insensitively."""
        monkeypatch.chdir(tmp_path)

        # Create initial education
        (tmp_path / ".resume.yaml").write_text(
            """education:
  - degree: "BS Computer Science"
    institution: "MIT"
"""
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "education",
                "--degree",
                "bs computer science",
                "--institution",
                "mit",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        # Should find existing, not create new
        assert "already exists" in result.output


class TestEducationPipeSeparated:
    """Tests for pipe-separated education creation."""

    def test_creates_education_pipe_separated(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create education with pipe-separated format."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "education",
                "BS Computer Science|MIT|2015|Magna Cum Laude",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Education created" in result.output
        assert (tmp_path / ".resume.yaml").exists()

        import yaml

        with open(tmp_path / ".resume.yaml") as f:
            data = yaml.safe_load(f)

        edu = data["education"][0]
        assert edu["degree"] == "BS Computer Science"
        assert edu["institution"] == "MIT"
        assert edu["graduation_year"] == "2015"
        assert edu["honors"] == "Magna Cum Laude"

    def test_creates_education_pipe_minimal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create education with just degree and institution."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "education",
                "MS Cybersecurity|Georgia Tech",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Education created" in result.output

        import yaml

        with open(tmp_path / ".resume.yaml") as f:
            data = yaml.safe_load(f)

        edu = data["education"][0]
        assert edu["degree"] == "MS Cybersecurity"
        assert edu["institution"] == "Georgia Tech"

    def test_pipe_format_with_partial_fields(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should handle pipe format with some empty fields."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "education",
                "PhD Computer Science|Stanford||",  # No year or honors
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"

        import yaml

        with open(tmp_path / ".resume.yaml") as f:
            data = yaml.safe_load(f)

        edu = data["education"][0]
        assert edu["degree"] == "PhD Computer Science"
        assert edu["institution"] == "Stanford"
        assert edu.get("graduation_year") is None
        assert edu.get("honors") is None

    def test_pipe_format_json_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return JSON output with pipe-separated format."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--json",
                "new",
                "education",
                "BS Test|Test University|2020",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["education_created"] is True
        assert data["data"]["degree"] == "BS Test"
        assert data["data"]["institution"] == "Test University"

    def test_pipe_format_missing_institution_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error if institution is missing in pipe format."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "education",
                "BS Computer Science",  # Only degree, no institution
            ],
        )

        # Should error because institution is required
        assert result.exit_code != 0
        assert "Institution" in result.output or "format" in result.output.lower()

    def test_flags_override_pipe_values(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should allow flags to override pipe-separated values."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "education",
                "Pipe Degree|Pipe Institution|2015|Pipe Honors",
                "--degree",
                "Flag Degree",  # Override degree
                "--institution",
                "Flag Institution",  # Override institution
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"

        import yaml

        with open(tmp_path / ".resume.yaml") as f:
            data = yaml.safe_load(f)

        edu = data["education"][0]
        assert edu["degree"] == "Flag Degree"
        assert edu["institution"] == "Flag Institution"
        # These should still come from pipe since not overridden
        assert edu["graduation_year"] == "2015"
        assert edu["honors"] == "Pipe Honors"


class TestEducationService:
    """Tests for EducationService directly."""

    def test_service_load_empty(self, tmp_path: Path) -> None:
        """Should return empty list if no config exists."""
        from resume_as_code.services.education_service import EducationService

        service = EducationService(config_path=tmp_path / ".resume.yaml")
        edu = service.load_education()
        assert edu == []

    def test_service_save_and_load(self, tmp_path: Path) -> None:
        """Should save and load education records."""
        from resume_as_code.models.education import Education
        from resume_as_code.services.education_service import EducationService

        service = EducationService(config_path=tmp_path / ".resume.yaml")

        edu = Education(degree="BS Test", institution="Test Uni")
        service.save_education(edu)

        # Reload (clear cache)
        service._education = None
        loaded = service.load_education()
        assert len(loaded) == 1
        assert loaded[0].degree == "BS Test"
