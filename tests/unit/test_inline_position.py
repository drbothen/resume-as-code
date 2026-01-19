"""Tests for inline position creation (Story 6.9).

Tests for:
- --position flag parsing and auto-creation
- --position-id validation
- JSON output format
- Non-interactive position creation
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main as cli


class TestPositionFlagParsing:
    """Tests for --position flag format parsing."""

    def test_parse_position_flag_basic(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should parse basic position format: Employer|Title|StartDate|EndDate."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--position",
                "TechCorp|Engineer|2022-01|",
                "--title",
                "Test achievement",
                "--from-memory",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Position created" in result.output
        assert (tmp_path / "positions.yaml").exists()

    def test_parse_position_flag_with_end_date(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should parse position with end date."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--position",
                "Acme Corp|Consultant|2020-01|2022-06",
                "--title",
                "Security audit",
                "--from-memory",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"

    def test_parse_position_flag_invalid_format(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error on invalid position format."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--position",
                "Missing|Pipes",  # Only 2 parts instead of 4
                "--title",
                "Test",
                "--from-memory",
            ],
        )

        assert result.exit_code != 0
        assert "format" in result.output.lower() or "invalid" in result.output.lower()


class TestPositionAutoCreation:
    """Tests for automatic position creation via --position flag."""

    def test_creates_position_with_work_unit(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create position when using --position flag (AC#1)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--position",
                "TechCorp Industries|Senior Engineer|2022-01|",
                "--title",
                "Led ICS security assessment",
                "--from-memory",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Position created" in result.output
        assert (tmp_path / "positions.yaml").exists()

        # Verify position file content
        import yaml

        with open(tmp_path / "positions.yaml") as f:
            positions_data = yaml.safe_load(f)

        assert "positions" in positions_data
        # Find the created position
        position_ids = list(positions_data["positions"].keys())
        assert len(position_ids) == 1
        pos = positions_data["positions"][position_ids[0]]
        assert pos["employer"] == "TechCorp Industries"
        assert pos["title"] == "Senior Engineer"
        assert pos["start_date"] == "2022-01"

    def test_reuses_existing_position(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should reuse position if employer+title match (AC#2)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        # Create initial position
        (tmp_path / "positions.yaml").write_text(
            """schema_version: "4.0.0"
archetype: minimal
positions:
  pos-techcorp-engineer:
    employer: "TechCorp"
    title: "Engineer"
    start_date: "2022-01"
"""
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--position",
                "TechCorp|Engineer|2022-01|",
                "--title",
                "Another achievement",
                "--from-memory",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Position created" not in result.output
        assert "Using position" in result.output or "pos-techcorp-engineer" in result.output

        # Verify no duplicate position created
        import yaml

        with open(tmp_path / "positions.yaml") as f:
            positions_data = yaml.safe_load(f)

        assert len(positions_data["positions"]) == 1


class TestPositionIdFlag:
    """Tests for --position-id flag validation."""

    def test_position_id_validation_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should work with valid --position-id (AC#3)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        # Create existing position
        (tmp_path / "positions.yaml").write_text(
            """schema_version: "4.0.0"
archetype: minimal
positions:
  pos-techcorp-senior:
    employer: "TechCorp"
    title: "Senior Engineer"
    start_date: "2022-01"
"""
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--position-id",
                "pos-techcorp-senior",
                "--title",
                "Architected hybrid platform",
                "--from-memory",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"

    def test_position_id_validation_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error if --position-id doesn't exist (AC#3)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--position-id",
                "pos-nonexistent",
                "--title",
                "Test",
                "--from-memory",
            ],
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_position_and_position_id_mutually_exclusive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error if both --position and --position-id provided."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--position",
                "Company|Title|2022-01|",
                "--position-id",
                "pos-existing",
                "--title",
                "Test",
                "--from-memory",
            ],
        )

        assert result.exit_code != 0
        assert "both" in result.output.lower() or "cannot" in result.output.lower()


class TestJsonOutput:
    """Tests for JSON output format."""

    def test_json_output_with_position_creation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return structured JSON (AC#4)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--json",
                "new",
                "work-unit",
                "--position",
                "Company|Title|2023-01|",
                "--title",
                "Test achievement",
                "--from-memory",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert "work_unit_id" in data["data"] or "id" in data["data"]
        assert "position_id" in data["data"]
        assert "position_created" in data["data"]
        assert data["data"]["position_created"] is True

    def test_json_output_with_existing_position(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show position_created=false when reusing."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        # Create existing position
        (tmp_path / "positions.yaml").write_text(
            """schema_version: "4.0.0"
archetype: minimal
positions:
  pos-company-title:
    employer: "Company"
    title: "Title"
    start_date: "2023-01"
"""
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--json",
                "new",
                "work-unit",
                "--position",
                "Company|Title|2023-01|",
                "--title",
                "Test",
                "--from-memory",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["position_created"] is False


class TestNonInteractivePosition:
    """Tests for non-interactive position creation (AC#5, AC#6)."""

    def test_creates_position_with_flags(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create position without prompts (AC#5)."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "position",
                "--employer",
                "Acme Corp",
                "--title",
                "Consultant",
                "--start-date",
                "2018-03",
                "--end-date",
                "2020-05",
                "--employment-type",
                "contract",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Position created" in result.output or "success" in result.output.lower()

    def test_creates_position_with_promoted_from(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should track promotion chain (AC#6)."""
        monkeypatch.chdir(tmp_path)

        # Create base position first
        (tmp_path / "positions.yaml").write_text(
            """schema_version: "4.0.0"
archetype: minimal
positions:
  pos-techcorp-engineer:
    employer: "TechCorp"
    title: "Engineer"
    start_date: "2020-01"
    end_date: "2022-01"
"""
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "position",
                "--employer",
                "TechCorp",
                "--title",
                "Senior Engineer",
                "--start-date",
                "2022-01",
                "--promoted-from",
                "pos-techcorp-engineer",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"

        # Verify promoted_from is set
        import yaml

        with open(tmp_path / "positions.yaml") as f:
            positions_data = yaml.safe_load(f)

        # Find the new position (not the original)
        for _pos_id, pos in positions_data["positions"].items():
            if pos.get("title") == "Senior Engineer":
                assert pos.get("promoted_from") == "pos-techcorp-engineer"
                break
        else:
            pytest.fail("New position not found")

    def test_position_json_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return JSON for non-interactive position creation."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--json",
                "new",
                "position",
                "--employer",
                "TestCorp",
                "--title",
                "Developer",
                "--start-date",
                "2023-01",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert "position_id" in data["data"] or "id" in data["data"]


class TestPositionPipeSeparated:
    """Tests for pipe-separated position creation."""

    def test_creates_position_pipe_separated(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create position with pipe-separated format."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "position",
                "TechCorp Industries|Senior Engineer|2022-01|2024-06",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Position created" in result.output
        assert (tmp_path / "positions.yaml").exists()

        import yaml

        with open(tmp_path / "positions.yaml") as f:
            data = yaml.safe_load(f)

        pos = list(data["positions"].values())[0]
        assert pos["employer"] == "TechCorp Industries"
        assert pos["title"] == "Senior Engineer"
        assert pos["start_date"] == "2022-01"
        assert pos["end_date"] == "2024-06"

    def test_creates_position_pipe_without_end_date(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create current position (no end date) with pipe format."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "position",
                "Acme Corp|Consultant|2023-06",  # No end date (3 segments)
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Position created" in result.output

        import yaml

        with open(tmp_path / "positions.yaml") as f:
            data = yaml.safe_load(f)

        pos = list(data["positions"].values())[0]
        assert pos["employer"] == "Acme Corp"
        assert pos["title"] == "Consultant"
        assert pos["start_date"] == "2023-06"
        assert pos.get("end_date") is None

    def test_pipe_format_json_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return JSON output with pipe-separated format."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--json",
                "new",
                "position",
                "TestCorp|Developer|2024-01",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert "position_id" in data["data"]

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
                "position",
                "Pipe Employer|Pipe Title|2020-01|2022-01",
                "--employer",
                "Flag Employer",  # Override employer
                "--title",
                "Flag Title",  # Override title
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"

        import yaml

        with open(tmp_path / "positions.yaml") as f:
            data = yaml.safe_load(f)

        pos = list(data["positions"].values())[0]
        assert pos["employer"] == "Flag Employer"
        assert pos["title"] == "Flag Title"
        # These should still come from pipe since not overridden
        assert pos["start_date"] == "2020-01"
        assert pos["end_date"] == "2022-01"

    def test_pipe_format_invalid_too_few_segments(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error if too few segments in pipe format."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "position",
                "TechCorp|Engineer",  # Only 2 segments, need at least 3
            ],
        )

        assert result.exit_code != 0
        assert "format" in result.output.lower() or "StartDate" in result.output


class TestListPositionsJson:
    """Tests for JSON output in list positions (AC#7)."""

    def test_json_list_positions(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return JSON array of positions (AC#7)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "positions.yaml").write_text(
            """schema_version: "4.0.0"
archetype: minimal
positions:
  pos-test:
    employer: "Test"
    title: "Role"
    start_date: "2022-01"
"""
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "list", "positions"])

        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert "positions" in data["data"]
        assert len(data["data"]["positions"]) == 1


class TestPositionMatching:
    """Tests for position matching logic (Task 6)."""

    def test_case_insensitive_matching(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should match positions case-insensitively."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        # Create position with mixed case
        (tmp_path / "positions.yaml").write_text(
            """schema_version: "4.0.0"
archetype: minimal
positions:
  pos-techcorp-engineer:
    employer: "TechCorp"
    title: "Engineer"
    start_date: "2022-01"
"""
        )

        runner = CliRunner()
        # Use lowercase in --position flag
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--position",
                "techcorp|engineer|2022-01|",
                "--title",
                "Test",
                "--from-memory",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        # Should reuse existing position, not create new
        assert "Position created" not in result.output

    def test_whitespace_normalized_matching(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should match positions with normalized whitespace."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        # Create position
        (tmp_path / "positions.yaml").write_text(
            """schema_version: "4.0.0"
archetype: minimal
positions:
  pos-tech-corp-engineer:
    employer: "Tech Corp"
    title: "Software Engineer"
    start_date: "2022-01"
"""
        )

        runner = CliRunner()
        # Use extra whitespace in --position flag
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--position",
                "  Tech Corp  |  Software Engineer  |2022-01|",
                "--title",
                "Test",
                "--from-memory",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        # Should reuse existing position, not create new
        assert "Position created" not in result.output
