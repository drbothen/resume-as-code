"""Tests for position management commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main


class TestNewPositionCommand:
    """Tests for new position command."""

    def test_creates_position_interactively(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create position through prompts."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Simulate interactive input:
        # 1. Employer name: Test Corp
        # 2. Job title: Engineer
        # 3. Location: Austin, TX
        # 4. Start date: 2022-01
        # 5. Is current? y
        # 6. Employment type: 1 (full-time)
        # 7. Was promotion? n
        input_data = "Test Corp\nEngineer\nAustin, TX\n2022-01\ny\n1\nn\n"

        result = runner.invoke(main, ["new", "position"], input=input_data)

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "Position created" in result.output

        # Verify positions.yaml created
        positions_file = tmp_path / "positions.yaml"
        assert positions_file.exists(), "positions.yaml not created"

        # Verify content
        content = positions_file.read_text()
        assert "Test Corp" in content
        assert "Engineer" in content

    def test_creates_position_with_end_date(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create past position with end date."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Not current position, provide end date
        input_data = "Past Corp\nFormer Role\nNew York\n2020-01\nn\n2022-06\n1\nn\n"

        result = runner.invoke(main, ["new", "position"], input=input_data)

        assert result.exit_code == 0, f"Command failed: {result.output}"
        content = (tmp_path / "positions.yaml").read_text()
        assert "2022-06" in content

    def test_creates_position_with_promotion(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should link promotion to previous position."""
        monkeypatch.chdir(tmp_path)

        # First create an existing position
        positions_yaml = tmp_path / "positions.yaml"
        positions_yaml.write_text(
            """schema_version: "1.0.0"
positions:
  pos-techcorp-junior:
    employer: TechCorp
    title: Junior Engineer
    start_date: "2020-01"
    end_date: "2022-01"
"""
        )

        runner = CliRunner()

        # Create promoted position, select first existing position
        # 1. Employer: TechCorp
        # 2. Title: Senior Engineer
        # 3. Location: (empty)
        # 4. Start: 2022-01
        # 5. Current: y
        # 6. Type: 1 (full-time)
        # 7. Promotion: y
        # 8. Select previous: 1
        input_data = "TechCorp\nSenior Engineer\n\n2022-01\ny\n1\ny\n1\n"

        result = runner.invoke(main, ["new", "position"], input=input_data)

        assert result.exit_code == 0, f"Command failed: {result.output}"
        content = positions_yaml.read_text()
        assert "promoted_from" in content
        assert "pos-techcorp-junior" in content

    def test_displays_generated_id(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should display the generated position ID."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        input_data = "My Company\nDeveloper\n\n2023-06\ny\n1\nn\n"

        result = runner.invoke(main, ["new", "position"], input=input_data)

        assert result.exit_code == 0
        assert "pos-my-company-developer" in result.output

    def test_json_output_mode(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should support JSON output mode."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # In JSON mode, we need non-interactive defaults
        input_data = "JSON Corp\nTest Role\n\n2023-01\ny\n1\nn\n"

        result = runner.invoke(main, ["--json", "new", "position"], input=input_data)

        assert result.exit_code == 0
        # Should have JSON in output
        assert '"status":' in result.output or "Position created" in result.output


class TestListPositionsCommand:
    """Tests for list positions command."""

    def test_lists_positions_table(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should display positions in table format."""
        monkeypatch.chdir(tmp_path)

        # Create positions.yaml
        (tmp_path / "positions.yaml").write_text(
            """schema_version: "1.0.0"
positions:
  pos-techcorp-senior:
    employer: TechCorp Industries
    title: Senior Platform Engineer
    start_date: "2022-01"
    employment_type: full-time
"""
        )

        runner = CliRunner()
        result = runner.invoke(main, ["list", "positions"])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "TechCorp" in result.output
        # Table may wrap "Senior Platform Engineer" - check parts exist
        assert "Senior" in result.output
        assert "Engineer" in result.output

    def test_empty_positions_message(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should show message when no positions exist."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "positions"])

        assert result.exit_code == 0
        assert "No positions found" in result.output

    def test_sorts_by_start_date_descending(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should sort positions by start date (most recent first)."""
        monkeypatch.chdir(tmp_path)

        (tmp_path / "positions.yaml").write_text(
            """schema_version: "1.0.0"
positions:
  pos-old:
    employer: Old Corp
    title: Junior Dev
    start_date: "2018-01"
  pos-new:
    employer: New Corp
    title: Senior Dev
    start_date: "2023-01"
  pos-mid:
    employer: Mid Corp
    title: Dev
    start_date: "2020-06"
"""
        )

        runner = CliRunner()
        result = runner.invoke(main, ["list", "positions"])

        assert result.exit_code == 0
        # New Corp should appear before Old Corp in output
        new_pos = result.output.find("New Corp")
        old_pos = result.output.find("Old Corp")
        assert new_pos < old_pos, "Positions not sorted by date descending"

    def test_json_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should support JSON output mode."""
        monkeypatch.chdir(tmp_path)

        (tmp_path / "positions.yaml").write_text(
            """schema_version: "1.0.0"
positions:
  pos-test:
    employer: Test Corp
    title: Engineer
    start_date: "2022-01"
"""
        )

        runner = CliRunner()
        result = runner.invoke(main, ["--json", "list", "positions"])

        assert result.exit_code == 0
        assert '"status":' in result.output


class TestShowPositionCommand:
    """Tests for show position command."""

    def test_shows_position_details(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should display position details."""
        monkeypatch.chdir(tmp_path)

        (tmp_path / "positions.yaml").write_text(
            """schema_version: "1.0.0"
positions:
  pos-techcorp-senior:
    employer: TechCorp Industries
    title: Senior Platform Engineer
    location: Austin, TX
    start_date: "2022-01"
    employment_type: full-time
"""
        )

        runner = CliRunner()
        result = runner.invoke(main, ["show", "position", "pos-techcorp-senior"])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "TechCorp Industries" in result.output
        assert "Senior Platform Engineer" in result.output
        assert "Austin, TX" in result.output

    def test_shows_related_work_units(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should list work units referencing position."""
        monkeypatch.chdir(tmp_path)

        (tmp_path / "positions.yaml").write_text(
            """schema_version: "1.0.0"
positions:
  pos-techcorp-senior:
    employer: TechCorp
    title: Senior Engineer
    start_date: "2022-01"
"""
        )

        # Create work unit referencing this position
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        (work_units_dir / "wu-2023-01-01-test.yaml").write_text(
            """id: wu-2023-01-01-test
title: Test Work Unit
position_id: pos-techcorp-senior
problem: Test problem
solution: Test solution
impact: Test impact
"""
        )

        runner = CliRunner()
        result = runner.invoke(main, ["show", "position", "pos-techcorp-senior"])

        assert result.exit_code == 0
        assert "Work Units" in result.output or "wu-2023-01-01-test" in result.output

    def test_shows_promotion_chain(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should display career progression."""
        monkeypatch.chdir(tmp_path)

        (tmp_path / "positions.yaml").write_text(
            """schema_version: "1.0.0"
positions:
  pos-techcorp-junior:
    employer: TechCorp
    title: Junior Engineer
    start_date: "2020-01"
    end_date: "2022-01"
  pos-techcorp-senior:
    employer: TechCorp
    title: Senior Engineer
    start_date: "2022-01"
    promoted_from: pos-techcorp-junior
"""
        )

        runner = CliRunner()
        result = runner.invoke(main, ["show", "position", "pos-techcorp-senior"])

        assert result.exit_code == 0
        # Should show progression
        output = result.output
        assert "Junior Engineer" in output or "Progression" in output or "Career" in output

    def test_position_not_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should error when position doesn't exist."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "position", "pos-nonexistent"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()
