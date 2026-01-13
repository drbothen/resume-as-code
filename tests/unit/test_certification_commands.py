"""Tests for Certification, Position, and Work Unit Management Commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main
from resume_as_code.services.certification_service import CertificationService
from resume_as_code.services.position_service import PositionService


class TestCertificationNameMatching:
    """Tests for certification name matching in CertificationService."""

    def test_find_certifications_by_name_exact_match(self, tmp_path: Path) -> None:
        """Should find certification by exact name match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "AWS Solutions Architect"
    issuer: "Amazon Web Services"
  - name: "CISSP"
    issuer: "ISC2"
"""
        )
        service = CertificationService(config_path=config_path)
        matches = service.find_certifications_by_name("CISSP")

        assert len(matches) == 1
        assert matches[0].name == "CISSP"

    def test_find_certifications_by_name_partial_match(self, tmp_path: Path) -> None:
        """Should find certification by partial name match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "AWS Solutions Architect - Professional"
    issuer: "Amazon Web Services"
  - name: "AWS Developer Associate"
    issuer: "Amazon Web Services"
"""
        )
        service = CertificationService(config_path=config_path)
        matches = service.find_certifications_by_name("AWS")

        assert len(matches) == 2

    def test_find_certifications_by_name_case_insensitive(self, tmp_path: Path) -> None:
        """Should match case-insensitively."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "CISSP"
    issuer: "ISC2"
"""
        )
        service = CertificationService(config_path=config_path)
        matches = service.find_certifications_by_name("cissp")

        assert len(matches) == 1
        assert matches[0].name == "CISSP"

    def test_find_certifications_by_name_no_match(self, tmp_path: Path) -> None:
        """Should return empty list when no match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "CISSP"
    issuer: "ISC2"
"""
        )
        service = CertificationService(config_path=config_path)
        matches = service.find_certifications_by_name("nonexistent")

        assert len(matches) == 0

    def test_find_certifications_empty_config(self, tmp_path: Path) -> None:
        """Should handle empty certifications list."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\n")
        service = CertificationService(config_path=config_path)
        matches = service.find_certifications_by_name("CISSP")

        assert len(matches) == 0


class TestRemoveCertificationService:
    """Tests for remove_certification in CertificationService."""

    def test_remove_certification_success(self, tmp_path: Path) -> None:
        """Should remove certification successfully."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "AWS Solutions Architect"
    issuer: "Amazon Web Services"
  - name: "CISSP"
    issuer: "ISC2"
"""
        )
        service = CertificationService(config_path=config_path)
        result = service.remove_certification("CISSP")

        assert result is True

        # Verify removal
        certs = service.load_certifications()
        assert len(certs) == 1
        assert certs[0].name == "AWS Solutions Architect"

    def test_remove_certification_not_found(self, tmp_path: Path) -> None:
        """Should return False when certification not found."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "CISSP"
    issuer: "ISC2"
"""
        )
        service = CertificationService(config_path=config_path)
        result = service.remove_certification("nonexistent")

        assert result is False

    def test_remove_certification_no_config_file(self, tmp_path: Path) -> None:
        """Should return False when config file doesn't exist."""
        config_path = tmp_path / ".resume.yaml"
        service = CertificationService(config_path=config_path)
        result = service.remove_certification("CISSP")

        assert result is False

    def test_remove_certification_partial_match(self, tmp_path: Path) -> None:
        """Should remove by partial name match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "AWS Solutions Architect - Professional"
    issuer: "Amazon Web Services"
"""
        )
        service = CertificationService(config_path=config_path)
        result = service.remove_certification("Solutions Architect")

        assert result is True

        # Verify removal
        certs = service.load_certifications()
        assert len(certs) == 0


class TestNewCertificationCommand:
    """Tests for `resume new certification` command."""

    def test_new_certification_non_interactive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create certification in non-interactive mode."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "certification",
                "--name",
                "AWS Solutions Architect",
                "--issuer",
                "Amazon Web Services",
                "--date",
                "2024-06",
            ],
        )

        assert result.exit_code == 0
        assert (
            "Certification created" in result.output or "AWS Solutions Architect" in result.output
        )

        # Verify file was created
        config_path = tmp_path / ".resume.yaml"
        assert config_path.exists()

    def test_new_certification_pipe_separated(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create certification from pipe-separated format."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "certification",
                "CISSP|ISC2|2023-01|2026-01",
            ],
        )

        assert result.exit_code == 0
        assert "CISSP" in result.output

    def test_new_certification_json_output(
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
                "certification",
                "--name",
                "Test Cert",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["certification_created"] is True

    def test_new_certification_duplicate_detection(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should detect duplicate certifications."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "CISSP"
    issuer: "ISC2"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "certification",
                "--name",
                "CISSP",
                "--issuer",
                "ISC2",
            ],
        )

        # Should indicate already exists (not an error, just info)
        assert "already exists" in result.output

    def test_new_certification_empty_name_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should reject empty certification name."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "certification",
                "--name",
                "",
            ],
        )

        assert result.exit_code != 0
        assert "cannot be empty" in result.output.lower()


class TestListCertificationsCommand:
    """Tests for `resume list certifications` command."""

    def test_list_certifications_table_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should display certifications in table format."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "AWS Solutions Architect"
    issuer: "Amazon Web Services"
    date: "2024-06"
    expires: "2099-06"
  - name: "CISSP"
    issuer: "ISC2"
    date: "2023-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "certifications"])

        assert result.exit_code == 0
        assert "AWS Solutions Architect" in result.output
        assert "CISSP" in result.output
        assert "Certification" in result.output

    def test_list_certifications_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should handle empty certifications list."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "certifications"])

        assert result.exit_code == 0
        assert "No certifications found" in result.output

    def test_list_certifications_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON with computed status."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "CISSP"
    issuer: "ISC2"
    date: "2023-01"
    expires: "2099-12"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "list", "certifications"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert len(data["data"]["certifications"]) == 1
        assert data["data"]["certifications"][0]["status"] == "active"

    def test_list_certifications_json_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output empty JSON list when no certifications."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "list", "certifications"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["count"] == 0
        assert data["data"]["certifications"] == []

    def test_list_certifications_expired_shows_tip(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show tip for expired certifications."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "Old Cert"
    issuer: "Old Issuer"
    expires: "2020-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "certifications"])

        assert result.exit_code == 0
        assert "Expired" in result.output
        assert "Tip:" in result.output or "renewing" in result.output.lower()


class TestRemoveCertificationCommand:
    """Tests for `resume remove certification` command."""

    def test_remove_certification_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should remove certification with --yes flag."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "CISSP"
    issuer: "ISC2"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "certification", "CISSP", "--yes"])

        assert result.exit_code == 0
        assert "Removed certification: CISSP" in result.output

    def test_remove_certification_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when certification not found."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "CISSP"
    issuer: "ISC2"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "certification", "nonexistent", "--yes"])

        assert result.exit_code == 4  # NOT_FOUND
        assert "No certification found" in result.output

    def test_remove_certification_multiple_matches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when multiple certifications match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "AWS Solutions Architect - Professional"
    issuer: "Amazon Web Services"
  - name: "AWS Developer Associate"
    issuer: "Amazon Web Services"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "certification", "AWS", "--yes"])

        assert result.exit_code == 1
        assert "Multiple certifications match" in result.output

    def test_remove_certification_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON on successful removal."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "CISSP"
    issuer: "ISC2"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "remove", "certification", "CISSP", "--yes"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["removed"] is True
        assert data["data"]["name"] == "CISSP"

    def test_remove_certification_interactive_confirm(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should prompt for confirmation in interactive mode."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "CISSP"
    issuer: "ISC2"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Simulate user typing 'y' for confirmation
        result = runner.invoke(main, ["remove", "certification", "CISSP"], input="y\n")

        assert result.exit_code == 0
        assert "Removed certification: CISSP" in result.output

    def test_remove_certification_interactive_cancel(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should cancel when user declines confirmation."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "CISSP"
    issuer: "ISC2"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Simulate user typing 'n' to decline
        result = runner.invoke(main, ["remove", "certification", "CISSP"], input="n\n")

        assert result.exit_code == 0
        assert "Cancelled" in result.output

        # Verify certification was not removed
        service = CertificationService(config_path=config_path)
        certs = service.load_certifications()
        assert len(certs) == 1


class TestPositionServiceRemove:
    """Tests for remove_position in PositionService."""

    def test_remove_position_success(self, tmp_path: Path) -> None:
        """Should remove position successfully."""
        positions_path = tmp_path / "positions.yaml"
        positions_path.write_text(
            """
positions:
  pos-acme-engineer:
    employer: Acme Corp
    title: Software Engineer
    start_date: "2020-01"
  pos-techco-senior:
    employer: TechCo
    title: Senior Engineer
    start_date: "2022-01"
"""
        )
        service = PositionService(positions_path=positions_path)
        result = service.remove_position("pos-acme-engineer")

        assert result is True

        # Verify removal
        positions = service.load_positions()
        assert len(positions) == 1
        assert "pos-techco-senior" in positions

    def test_remove_position_not_found(self, tmp_path: Path) -> None:
        """Should return False when position not found."""
        positions_path = tmp_path / "positions.yaml"
        positions_path.write_text(
            """
positions:
  pos-acme-engineer:
    employer: Acme Corp
    title: Software Engineer
    start_date: "2020-01"
"""
        )
        service = PositionService(positions_path=positions_path)
        result = service.remove_position("nonexistent")

        assert result is False

    def test_find_positions_by_query(self, tmp_path: Path) -> None:
        """Should find positions by employer/title query."""
        positions_path = tmp_path / "positions.yaml"
        positions_path.write_text(
            """
positions:
  pos-acme-engineer:
    employer: Acme Corp
    title: Software Engineer
    start_date: "2020-01"
  pos-acme-senior:
    employer: Acme Corp
    title: Senior Engineer
    start_date: "2022-01"
  pos-techco-dev:
    employer: TechCo
    title: Developer
    start_date: "2021-01"
"""
        )
        service = PositionService(positions_path=positions_path)

        # Search by employer
        matches = service.find_positions_by_query("Acme")
        assert len(matches) == 2

        # Search by title
        matches = service.find_positions_by_query("Senior")
        assert len(matches) == 1


class TestRemovePositionCommand:
    """Tests for `resume remove position` command."""

    def test_remove_position_by_id(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should remove position by exact ID."""
        positions_path = tmp_path / "positions.yaml"
        positions_path.write_text(
            """
positions:
  pos-acme-engineer:
    employer: Acme Corp
    title: Software Engineer
    start_date: "2020-01"
"""
        )
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(f"positions_path: {positions_path}\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "position", "pos-acme-engineer", "--yes"])

        assert result.exit_code == 0
        assert "Removed position" in result.output

    def test_remove_position_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when position not found."""
        positions_path = tmp_path / "positions.yaml"
        positions_path.write_text(
            """
positions:
  pos-acme-engineer:
    employer: Acme Corp
    title: Software Engineer
    start_date: "2020-01"
"""
        )
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(f"positions_path: {positions_path}\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "position", "nonexistent", "--yes"])

        assert result.exit_code == 4  # NOT_FOUND

    def test_remove_position_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON on successful removal."""
        positions_path = tmp_path / "positions.yaml"
        positions_path.write_text(
            """
positions:
  pos-acme-engineer:
    employer: Acme Corp
    title: Software Engineer
    start_date: "2020-01"
"""
        )
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(f"positions_path: {positions_path}\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "remove", "position", "pos-acme-engineer", "--yes"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["removed"] is True


class TestRemoveWorkUnitCommand:
    """Tests for `resume remove work-unit` command."""

    def test_remove_work_unit_by_id(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should remove work unit file by ID."""
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        wu_file = work_units_dir / "wu-2024-01-01-test-project.yaml"
        wu_file.write_text(
            """
id: wu-2024-01-01-test-project
title: Test Project
"""
        )
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(f"work_units_dir: {work_units_dir}\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "work-unit", "wu-2024-01-01-test-project", "--yes"])

        assert result.exit_code == 0
        assert "Removed work unit" in result.output
        assert not wu_file.exists()

    def test_remove_work_unit_partial_match(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should remove work unit by partial ID match."""
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        wu_file = work_units_dir / "wu-2024-01-01-test-project.yaml"
        wu_file.write_text(
            """
id: wu-2024-01-01-test-project
title: Test Project
"""
        )
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(f"work_units_dir: {work_units_dir}\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "work-unit", "test-project", "--yes"])

        assert result.exit_code == 0
        assert not wu_file.exists()

    def test_remove_work_unit_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when work unit not found."""
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(f"work_units_dir: {work_units_dir}\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "work-unit", "nonexistent", "--yes"])

        assert result.exit_code == 4  # NOT_FOUND

    def test_remove_work_unit_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON on successful removal."""
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        wu_file = work_units_dir / "wu-2024-01-01-test-project.yaml"
        wu_file.write_text(
            """
id: wu-2024-01-01-test-project
title: Test Project
"""
        )
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(f"work_units_dir: {work_units_dir}\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main, ["--json", "remove", "work-unit", "wu-2024-01-01-test-project", "--yes"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["removed"] is True

    def test_remove_work_unit_multiple_matches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when multiple work units match."""
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        (work_units_dir / "wu-2024-01-01-test-one.yaml").write_text("id: wu-2024-01-01-test-one\n")
        (work_units_dir / "wu-2024-01-02-test-two.yaml").write_text("id: wu-2024-01-02-test-two\n")
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(f"work_units_dir: {work_units_dir}\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "work-unit", "test", "--yes"])

        assert result.exit_code == 1
        assert "Multiple work units match" in result.output


class TestShowWorkUnitCommand:
    """Tests for `resume show work-unit` command."""

    def test_show_work_unit_by_id(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should display work unit details by exact ID."""
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        wu_file = work_units_dir / "wu-2024-01-01-test-project.yaml"
        wu_file.write_text(
            """
id: wu-2024-01-01-test-project
title: Test Project Implementation
position_id: pos-acme-engineer
date: "2024-01"
problem: The system was slow
actions:
  - Optimized database queries
  - Added caching layer
result: Improved performance by 50%
skills:
  - Python
  - PostgreSQL
tags:
  - performance
  - optimization
"""
        )
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(f"work_units_dir: {work_units_dir}\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "work-unit", "wu-2024-01-01-test-project"])

        assert result.exit_code == 0
        assert "Test Project Implementation" in result.output
        assert "pos-acme-engineer" in result.output
        assert "Problem:" in result.output
        assert "Actions:" in result.output
        assert "Result:" in result.output

    def test_show_work_unit_partial_match(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should find work unit by partial ID match."""
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        wu_file = work_units_dir / "wu-2024-01-01-unique-project.yaml"
        wu_file.write_text(
            """
id: wu-2024-01-01-unique-project
title: Unique Project
"""
        )
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(f"work_units_dir: {work_units_dir}\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "work-unit", "unique-project"])

        assert result.exit_code == 0
        assert "Unique Project" in result.output

    def test_show_work_unit_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when work unit not found."""
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(f"work_units_dir: {work_units_dir}\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "work-unit", "nonexistent"])

        assert result.exit_code == 4  # NOT_FOUND
        assert "not found" in result.output.lower()

    def test_show_work_unit_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON with all work unit fields."""
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        wu_file = work_units_dir / "wu-2024-01-01-test-project.yaml"
        wu_file.write_text(
            """
id: wu-2024-01-01-test-project
title: Test Project
position_id: pos-acme-engineer
date: "2024-01"
problem: Problem statement
actions:
  - Action one
  - Action two
result: Result achieved
skills:
  - Python
tags:
  - backend
archetype: greenfield
"""
        )
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(f"work_units_dir: {work_units_dir}\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "show", "work-unit", "wu-2024-01-01-test-project"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["command"] == "show work-unit"
        wu = data["data"]["work_unit"]
        assert wu["id"] == "wu-2024-01-01-test-project"
        assert wu["title"] == "Test Project"
        assert wu["position_id"] == "pos-acme-engineer"
        assert wu["archetype"] == "greenfield"
        assert len(wu["actions"]) == 2
        assert "Python" in wu["skills"]

    def test_show_work_unit_multiple_matches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when multiple work units match partial ID."""
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        (work_units_dir / "wu-2024-01-01-test-one.yaml").write_text(
            "id: wu-2024-01-01-test-one\ntitle: Test One\n"
        )
        (work_units_dir / "wu-2024-01-02-test-two.yaml").write_text(
            "id: wu-2024-01-02-test-two\ntitle: Test Two\n"
        )
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(f"work_units_dir: {work_units_dir}\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "work-unit", "test"])

        assert result.exit_code == 1
        assert "Multiple work units match" in result.output


class TestShowCertificationCommand:
    """Tests for `resume show certification` command."""

    def test_show_certification_by_name(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should display certification details by name."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "AWS Solutions Architect - Professional"
    issuer: "Amazon Web Services"
    date: "2024-06"
    expires: "2027-06"
    credential_id: "ABC123XYZ"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "certification", "AWS Solutions"])

        assert result.exit_code == 0
        assert "AWS Solutions Architect - Professional" in result.output
        assert "Amazon Web Services" in result.output
        assert "2024-06" in result.output
        assert "2027-06" in result.output
        assert "ABC123XYZ" in result.output

    def test_show_certification_partial_match(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should find certification by partial name match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "CISSP - Certified Information Systems Security Professional"
    issuer: "ISC2"
    date: "2023-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "certification", "CISSP"])

        assert result.exit_code == 0
        assert "CISSP" in result.output
        assert "ISC2" in result.output

    def test_show_certification_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when certification not found."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "AWS Solutions Architect"
    issuer: "AWS"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "certification", "nonexistent"])

        assert result.exit_code == 4  # NOT_FOUND
        assert "not found" in result.output.lower()

    def test_show_certification_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON with all certification fields."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "AWS Solutions Architect"
    issuer: "Amazon Web Services"
    date: "2024-06"
    expires: "2027-06"
    credential_id: "ABC123"
    url: "https://aws.amazon.com/verify/ABC123"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "show", "certification", "AWS"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["command"] == "show certification"
        cert = data["data"]["certification"]
        assert cert["name"] == "AWS Solutions Architect"
        assert cert["issuer"] == "Amazon Web Services"
        assert cert["date"] == "2024-06"
        assert cert["expires"] == "2027-06"
        assert cert["credential_id"] == "ABC123"
        assert "aws.amazon.com" in cert["url"]
        assert cert["status"] == "active"

    def test_show_certification_multiple_matches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when multiple certifications match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "AWS Solutions Architect"
    issuer: "AWS"
  - name: "AWS Developer Associate"
    issuer: "AWS"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "certification", "AWS"])

        assert result.exit_code == 1
        assert "Multiple certifications match" in result.output

    def test_show_certification_status_expired(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show Expired status for expired certification."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "Old Cert"
    issuer: "Test Org"
    date: "2020-01"
    expires: "2021-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "certification", "Old Cert"])

        assert result.exit_code == 0
        assert "Expired" in result.output

    def test_show_certification_no_expiration(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show Active status for certification without expiration."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
certifications:
  - name: "Lifetime Cert"
    issuer: "Test Org"
    date: "2020-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "certification", "Lifetime Cert"])

        assert result.exit_code == 0
        assert "Active" in result.output
        assert "Never" in result.output
