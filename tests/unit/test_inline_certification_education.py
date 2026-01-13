"""Tests for inline certification and education creation (Story 6.9 extension).

Tests for:
- new certification command with non-interactive flags
- new education command with non-interactive flags
- JSON output format
- Duplicate detection
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main as cli


class TestNewCertificationCommand:
    """Tests for 'new certification' command."""

    def test_creates_certification_non_interactive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create certification with --name flag."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "certification",
                "--name",
                "AWS Solutions Architect",
                "--issuer",
                "Amazon Web Services",
                "--date",
                "2023-06",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Certification created" in result.output
        assert (tmp_path / ".resume.yaml").exists()

        # Verify file content
        import yaml

        with open(tmp_path / ".resume.yaml") as f:
            data = yaml.safe_load(f)

        assert "certifications" in data
        assert len(data["certifications"]) == 1
        assert data["certifications"][0]["name"] == "AWS Solutions Architect"
        assert data["certifications"][0]["issuer"] == "Amazon Web Services"

    def test_certification_with_all_fields(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create certification with all optional fields."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "certification",
                "--name",
                "CISSP",
                "--issuer",
                "ISC2",
                "--date",
                "2022-01",
                "--expires",
                "2025-01",
                "--credential-id",
                "123456",
                "--url",
                "https://isc2.org/verify/123456",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"

        import yaml

        with open(tmp_path / ".resume.yaml") as f:
            data = yaml.safe_load(f)

        cert = data["certifications"][0]
        assert cert["name"] == "CISSP"
        assert cert["issuer"] == "ISC2"
        assert cert["date"] == "2022-01"
        assert cert["expires"] == "2025-01"
        assert cert["credential_id"] == "123456"
        assert cert["url"] == "https://isc2.org/verify/123456"

    def test_certification_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return structured JSON output."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--json",
                "new",
                "certification",
                "--name",
                "Test Cert",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["certification_created"] is True
        assert data["data"]["name"] == "Test Cert"

    def test_certification_duplicate_detection(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should detect and report duplicate certifications."""
        monkeypatch.chdir(tmp_path)

        # Create initial certification
        (tmp_path / ".resume.yaml").write_text(
            """certifications:
  - name: "Existing Cert"
    issuer: "Some Org"
"""
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--json",
                "new",
                "certification",
                "--name",
                "Existing Cert",
                "--issuer",
                "Some Org",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["certification_created"] is False

    def test_certification_invalid_date_format(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error on invalid date format."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "certification",
                "--name",
                "Test",
                "--date",
                "invalid",
            ],
        )

        assert result.exit_code != 0
        assert "invalid" in result.output.lower() or "YYYY-MM" in result.output


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
        assert data["education"][0]["year"] == "2015"

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
        assert edu["year"] == "2018"
        assert edu["honors"] == "Magna Cum Laude"
        assert edu["gpa"] == "3.9/4.0"

    def test_education_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
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


class TestCertificationService:
    """Tests for CertificationService directly."""

    def test_service_load_empty(self, tmp_path: Path) -> None:
        """Should return empty list if no config exists."""
        from resume_as_code.services.certification_service import CertificationService

        service = CertificationService(config_path=tmp_path / ".resume.yaml")
        certs = service.load_certifications()
        assert certs == []

    def test_service_save_and_load(self, tmp_path: Path) -> None:
        """Should save and load certifications."""
        from resume_as_code.models.certification import Certification
        from resume_as_code.services.certification_service import CertificationService

        service = CertificationService(config_path=tmp_path / ".resume.yaml")

        cert = Certification(name="Test Cert", issuer="Test Org")
        service.save_certification(cert)

        # Reload (clear cache)
        service._certifications = None
        loaded = service.load_certifications()
        assert len(loaded) == 1
        assert loaded[0].name == "Test Cert"


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
