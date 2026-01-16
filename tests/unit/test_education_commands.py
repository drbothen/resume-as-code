"""Tests for Education Management Commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main
from resume_as_code.services.education_service import EducationService


class TestEducationNameMatching:
    """Tests for education name matching in EducationService."""

    def test_find_educations_by_degree_exact_match(self, tmp_path: Path) -> None:
        """Should find education by exact degree match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
  - degree: "MS Cybersecurity"
    institution: "Georgia Tech"
"""
        )
        service = EducationService(config_path=config_path)
        matches = service.find_educations_by_degree("BS Computer Science")

        assert len(matches) == 1
        assert matches[0].degree == "BS Computer Science"

    def test_find_educations_by_degree_partial_match(self, tmp_path: Path) -> None:
        """Should find education by partial degree match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
  - degree: "MS Computer Engineering"
    institution: "Stanford"
"""
        )
        service = EducationService(config_path=config_path)
        matches = service.find_educations_by_degree("Computer")

        assert len(matches) == 2

    def test_find_educations_by_degree_case_insensitive(self, tmp_path: Path) -> None:
        """Should match case-insensitively."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
"""
        )
        service = EducationService(config_path=config_path)
        matches = service.find_educations_by_degree("bs computer science")

        assert len(matches) == 1
        assert matches[0].degree == "BS Computer Science"

    def test_find_educations_by_degree_no_match(self, tmp_path: Path) -> None:
        """Should return empty list when no match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
"""
        )
        service = EducationService(config_path=config_path)
        matches = service.find_educations_by_degree("MBA")

        assert len(matches) == 0

    def test_find_educations_empty_config(self, tmp_path: Path) -> None:
        """Should handle empty education list."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\n")
        service = EducationService(config_path=config_path)
        matches = service.find_educations_by_degree("BS")

        assert len(matches) == 0


class TestRemoveEducationService:
    """Tests for remove_education in EducationService."""

    def test_remove_education_success(self, tmp_path: Path) -> None:
        """Should remove education successfully."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
  - degree: "MS Cybersecurity"
    institution: "Georgia Tech"
"""
        )
        service = EducationService(config_path=config_path)
        result = service.remove_education("BS Computer Science")

        assert result is True

        # Verify removal
        education = service.load_education()
        assert len(education) == 1
        assert education[0].degree == "MS Cybersecurity"

    def test_remove_education_not_found(self, tmp_path: Path) -> None:
        """Should return False when education not found."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
"""
        )
        service = EducationService(config_path=config_path)
        result = service.remove_education("MBA")

        assert result is False

    def test_remove_education_no_config_file(self, tmp_path: Path) -> None:
        """Should return False when config file doesn't exist."""
        config_path = tmp_path / ".resume.yaml"
        service = EducationService(config_path=config_path)
        result = service.remove_education("BS Computer Science")

        assert result is False

    def test_remove_education_case_insensitive(self, tmp_path: Path) -> None:
        """Should remove case-insensitively."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
"""
        )
        service = EducationService(config_path=config_path)
        result = service.remove_education("bs computer science")

        assert result is True

        # Verify removal
        education = service.load_education()
        assert len(education) == 0


class TestNewEducationCommand:
    """Tests for `resume new education` command."""

    def test_new_education_non_interactive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create education in non-interactive mode."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
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

        assert result.exit_code == 0
        assert "Education created" in result.output or "BS Computer Science" in result.output

        # Verify file was created
        config_path = tmp_path / ".resume.yaml"
        assert config_path.exists()

    def test_new_education_pipe_separated(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create education from pipe-separated format."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "education",
                "BS Computer Science|UT Austin|2012|Magna Cum Laude",
            ],
        )

        assert result.exit_code == 0
        assert "BS Computer Science" in result.output

    def test_new_education_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON in json mode."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
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

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["education_created"] is True

    def test_new_education_duplicate_detection(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should detect duplicate education entries."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "education",
                "--degree",
                "BS Computer Science",
                "--institution",
                "MIT",
            ],
        )

        # Should indicate already exists (not an error, just info)
        assert "already exists" in result.output

    def test_new_education_all_fields(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create education with all optional fields."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "education",
                "--degree",
                "BS Computer Science",
                "--institution",
                "UT Austin",
                "--year",
                "2012",
                "--honors",
                "Magna Cum Laude",
                "--gpa",
                "3.8/4.0",
            ],
        )

        assert result.exit_code == 0

        # Verify content
        config_path = tmp_path / ".resume.yaml"
        content = config_path.read_text()
        assert "Magna Cum Laude" in content
        assert "3.8/4.0" in content


class TestListEducationCommand:
    """Tests for `resume list education` command."""

    def test_list_education_table_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should display education in table format."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "UT Austin"
    graduation_year: "2012"
    honors: "Magna Cum Laude"
  - degree: "MS Cybersecurity"
    institution: "Georgia Tech"
    graduation_year: "2018"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "education"])

        assert result.exit_code == 0
        assert "BS Computer Science" in result.output
        assert "MS Cybersecurity" in result.output
        assert "UT Austin" in result.output
        assert "2012" in result.output

    def test_list_education_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should handle empty education list."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "education"])

        assert result.exit_code == 0
        assert "No education entries found" in result.output

    def test_list_education_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON with all education fields."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "MS Cybersecurity"
    institution: "Georgia Tech"
    graduation_year: "2018"
    honors: "With Distinction"
    gpa: "3.9/4.0"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "list", "education"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert len(data["data"]["education"]) == 1
        edu = data["data"]["education"][0]
        assert edu["degree"] == "MS Cybersecurity"
        assert edu["institution"] == "Georgia Tech"
        assert edu["graduation_year"] == "2018"
        assert edu["honors"] == "With Distinction"
        assert edu["gpa"] == "3.9/4.0"

    def test_list_education_json_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output empty JSON list when no education."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "list", "education"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["count"] == 0
        assert data["data"]["education"] == []


class TestRemoveEducationCommand:
    """Tests for `resume remove education` command."""

    def test_remove_education_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should remove education with --yes flag."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "education", "BS Computer Science", "--yes"])

        assert result.exit_code == 0
        assert "Removed education: BS Computer Science" in result.output

    def test_remove_education_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when education not found."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "education", "MBA", "--yes"])

        assert result.exit_code == 4  # NOT_FOUND
        assert "No education entry found" in result.output

    def test_remove_education_multiple_matches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when multiple education entries match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
  - degree: "MS Computer Engineering"
    institution: "Stanford"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "education", "Computer", "--yes"])

        assert result.exit_code == 1
        assert "Multiple education entries match" in result.output

    def test_remove_education_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON on successful removal."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main, ["--json", "remove", "education", "BS Computer Science", "--yes"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["removed"] is True
        assert data["data"]["degree"] == "BS Computer Science"

    def test_remove_education_interactive_confirm(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should prompt for confirmation in interactive mode."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Simulate user typing 'y' for confirmation
        result = runner.invoke(main, ["remove", "education", "BS Computer Science"], input="y\n")

        assert result.exit_code == 0
        assert "Removed education: BS Computer Science" in result.output

    def test_remove_education_interactive_cancel(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should cancel when user declines confirmation."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Simulate user typing 'n' to decline
        result = runner.invoke(main, ["remove", "education", "BS Computer Science"], input="n\n")

        assert result.exit_code == 0
        assert "Cancelled" in result.output

        # Verify education was not removed
        service = EducationService(config_path=config_path)
        education = service.load_education()
        assert len(education) == 1


class TestShowEducationCommand:
    """Tests for `resume show education` command."""

    def test_show_education_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should show education details."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
    graduation_year: "2015"
    honors: "Magna Cum Laude"
    gpa: "3.8/4.0"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "education", "BS Computer Science"])

        assert result.exit_code == 0
        assert "BS Computer Science" in result.output
        assert "MIT" in result.output
        assert "2015" in result.output
        assert "Magna Cum Laude" in result.output
        assert "3.8/4.0" in result.output

    def test_show_education_partial_match(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should find education by partial degree match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "education", "Computer"])

        assert result.exit_code == 0
        assert "BS Computer Science" in result.output

    def test_show_education_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when education not found."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "education", "MBA"])

        assert result.exit_code == 4  # NOT_FOUND

    def test_show_education_multiple_matches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when multiple education entries match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "BS Computer Science"
    institution: "MIT"
  - degree: "MS Computer Engineering"
    institution: "Stanford"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "education", "Computer"])

        assert result.exit_code == 1
        assert "Multiple education entries match" in result.output

    def test_show_education_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON with all education fields."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
education:
  - degree: "MS Cybersecurity"
    institution: "Georgia Tech"
    graduation_year: "2018"
    honors: "With Distinction"
    gpa: "3.9/4.0"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "show", "education", "MS Cybersecurity"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        edu = data["data"]["education"]
        assert edu["degree"] == "MS Cybersecurity"
        assert edu["institution"] == "Georgia Tech"
        assert edu["graduation_year"] == "2018"
        assert edu["honors"] == "With Distinction"
        assert edu["gpa"] == "3.9/4.0"
        assert "formatted" in edu


class TestNewEducationInteractive:
    """Tests for `resume new education` interactive mode."""

    def test_new_education_interactive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create education in interactive mode."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Provide all interactive prompts
        result = runner.invoke(
            main,
            ["new", "education"],
            input="PhD Computer Science\nStanford\n2020\nWith Honors\n3.9/4.0\n",
        )

        assert result.exit_code == 0
        assert "Education created" in result.output
        assert "PhD Computer Science" in result.output

        # Verify file was created with correct content
        config_path = tmp_path / ".resume.yaml"
        assert config_path.exists()
        content = config_path.read_text()
        assert "PhD Computer Science" in content
        assert "Stanford" in content


class TestEducationFormatting:
    """Tests for education display formatting."""

    def test_format_full(self) -> None:
        """Should format with all fields."""
        from resume_as_code.models.education import Education

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

    def test_format_minimal(self) -> None:
        """Should format with required fields only."""
        from resume_as_code.models.education import Education

        edu = Education(
            degree="MBA",
            institution="Harvard",
        )
        display = edu.format_display()
        assert display == "MBA, Harvard"

    def test_format_with_gpa_no_honors(self) -> None:
        """Should show GPA when no honors."""
        from resume_as_code.models.education import Education

        edu = Education(
            degree="BS Computer Science",
            institution="MIT",
            graduation_year="2015",
            gpa="3.8/4.0",
        )
        display = edu.format_display()
        assert "GPA: 3.8/4.0" in display


class TestEducationValidation:
    """Tests for Education model validation."""

    def test_empty_degree_rejected(self) -> None:
        """Should reject empty degree string."""
        from pydantic import ValidationError

        from resume_as_code.models.education import Education

        with pytest.raises(ValidationError) as exc_info:
            Education(degree="", institution="MIT")

        assert "Field cannot be empty" in str(exc_info.value)

    def test_whitespace_only_degree_rejected(self) -> None:
        """Should reject whitespace-only degree string."""
        from pydantic import ValidationError

        from resume_as_code.models.education import Education

        with pytest.raises(ValidationError) as exc_info:
            Education(degree="   ", institution="MIT")

        assert "Field cannot be empty" in str(exc_info.value)

    def test_empty_institution_rejected(self) -> None:
        """Should reject empty institution string."""
        from pydantic import ValidationError

        from resume_as_code.models.education import Education

        with pytest.raises(ValidationError) as exc_info:
            Education(degree="BS Computer Science", institution="")

        assert "Field cannot be empty" in str(exc_info.value)

    def test_whitespace_only_institution_rejected(self) -> None:
        """Should reject whitespace-only institution string."""
        from pydantic import ValidationError

        from resume_as_code.models.education import Education

        with pytest.raises(ValidationError) as exc_info:
            Education(degree="BS Computer Science", institution="  \t  ")

        assert "Field cannot be empty" in str(exc_info.value)

    def test_whitespace_stripped_from_valid_values(self) -> None:
        """Should strip whitespace from valid values."""
        from resume_as_code.models.education import Education

        edu = Education(degree="  BS Computer Science  ", institution="  MIT  ")

        assert edu.degree == "BS Computer Science"
        assert edu.institution == "MIT"
