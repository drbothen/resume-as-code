"""Tests for inline work unit creation (Story 6.9 extension).

Tests for:
- Full inline work unit creation with --problem, --action, --result
- Multiple actions and skills
- JSON output format
- Validation of minimum lengths
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from resume_as_code.cli import main as cli


class TestInlineWorkUnitCreation:
    """Tests for full inline work unit creation."""

    def test_creates_work_unit_inline(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create complete work unit with inline flags."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--title",
                "Led ICS security assessment",
                "--problem",
                "Legacy ICS systems lacked security monitoring across 50 PLCs",
                "--action",
                "Deployed network sensors across industrial control systems",
                "--action",
                "Built custom detection rules for Modbus protocol anomalies",
                "--result",
                "Achieved 99.9% visibility into previously dark ICS traffic",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Created Work Unit" in result.output
        assert "Actions: 2" in result.output

        # Verify file exists and has correct content
        work_unit_files = list((tmp_path / "work-units").glob("*.yaml"))
        assert len(work_unit_files) == 1

        with open(work_unit_files[0]) as f:
            data = yaml.safe_load(f)

        assert data["title"] == "Led ICS security assessment"
        assert data["problem"]["statement"].startswith("Legacy ICS systems")
        assert len(data["actions"]) == 2
        assert data["outcome"]["result"].startswith("Achieved 99.9%")

    def test_creates_work_unit_with_all_optional_fields(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create work unit with all optional fields."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--title",
                "Platform migration project",
                "--problem",
                "Outdated platform caused reliability issues and high maintenance costs",
                "--action",
                "Designed and implemented new cloud-native architecture",
                "--result",
                "Reduced downtime by 95% and cut maintenance costs by half",
                "--impact",
                "Saved $500K annually in operational costs",
                "--skill",
                "Cloud Architecture",
                "--skill",
                "AWS",
                "--skill",
                "Terraform",
                "--tag",
                "infrastructure",
                "--tag",
                "cost-savings",
                "--start-date",
                "2023-01",
                "--end-date",
                "2023-06",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Skills: 3" in result.output
        assert "Tags: 2" in result.output

        work_unit_files = list((tmp_path / "work-units").glob("*.yaml"))
        with open(work_unit_files[0]) as f:
            data = yaml.safe_load(f)

        assert data["outcome"]["quantified_impact"] == "Saved $500K annually in operational costs"
        assert len(data["skills_demonstrated"]) == 3
        assert data["skills_demonstrated"][0]["name"] == "Cloud Architecture"
        assert len(data["tags"]) == 2
        assert "infrastructure" in data["tags"]
        assert data["time_started"] == "2023-01"
        assert data["time_ended"] == "2023-06"

    def test_creates_work_unit_with_position(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create work unit with inline position creation."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--position",
                "TechCorp|Senior Engineer|2022-01|",
                "--title",
                "Security incident response automation",
                "--problem",
                "Manual incident response took hours and was error-prone",
                "--action",
                "Built automated playbooks for common security incidents",
                "--result",
                "Reduced mean time to respond from hours to minutes",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Position created" in result.output

        # Verify position was created
        assert (tmp_path / "positions.yaml").exists()

        # Verify work unit references the position
        work_unit_files = list((tmp_path / "work-units").glob("*.yaml"))
        with open(work_unit_files[0]) as f:
            data = yaml.safe_load(f)

        assert "position_id" in data
        assert data["position_id"].startswith("pos-")

    def test_json_output_inline_creation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return structured JSON for inline creation."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--json",
                "new",
                "work-unit",
                "--title",
                "Test inline work unit",
                "--problem",
                "This is a test problem statement that is long enough",
                "--action",
                "This is a test action that meets the minimum length",
                "--result",
                "This is the test result",
                "--skill",
                "Testing",
                "--tag",
                "test",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["inline_created"] is True
        assert "id" in data["data"]
        assert data["data"]["skills_count"] == 1
        assert data["data"]["tags_count"] == 1


class TestInlineWorkUnitValidation:
    """Tests for inline work unit validation."""

    def test_problem_minimum_length(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should error if problem is too short."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--title",
                "Test work unit",
                "--problem",
                "Too short",  # < 20 chars
                "--action",
                "This is a valid action string",
                "--result",
                "This is a valid result",
            ],
        )

        assert result.exit_code != 0
        assert "20 characters" in result.output

    def test_result_minimum_length(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should error if result is too short."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--title",
                "Test work unit",
                "--problem",
                "This is a valid problem statement",
                "--action",
                "This is a valid action string",
                "--result",
                "Short",  # < 10 chars
            ],
        )

        assert result.exit_code != 0
        assert "10 characters" in result.output

    def test_action_minimum_length(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should error if any action is too short."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--title",
                "Test work unit",
                "--problem",
                "This is a valid problem statement",
                "--action",
                "Valid action that is long enough",
                "--action",
                "Short",  # < 10 chars
                "--result",
                "This is a valid result",
            ],
        )

        assert result.exit_code != 0
        assert "Action 2" in result.output
        assert "10 characters" in result.output


class TestInlineVsTemplateMode:
    """Tests for mode detection between inline and template modes."""

    def test_errors_with_partial_inline_fields(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error if only some inline fields provided (prevents silent fallback)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        # Only providing --problem without --action and --result
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--title",
                "Test work unit",
                "--problem",
                "This is a problem but no actions",
                "--from-memory",  # from-memory shouldn't prevent inline validation
            ],
        )

        assert result.exit_code != 0
        assert "Missing" in result.output
        assert "--action" in result.output
        assert "--result" in result.output

    def test_inline_mode_takes_precedence(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should use inline mode when all required fields provided."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new",
                "work-unit",
                "--archetype",
                "greenfield",  # Archetype is ignored in inline mode
                "--title",
                "Test inline mode",
                "--problem",
                "This problem triggers inline mode creation",
                "--action",
                "This action is long enough to pass validation",
                "--result",
                "Inline mode was used successfully",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        # Should not open editor (inline mode doesn't need editing)

        work_unit_files = list((tmp_path / "work-units").glob("*.yaml"))
        with open(work_unit_files[0]) as f:
            data = yaml.safe_load(f)

        # Should have real content, not template placeholders
        assert data["problem"]["statement"] == "This problem triggers inline mode creation"


class TestWorkUnitServiceFromData:
    """Tests for create_work_unit_from_data function."""

    def test_creates_valid_yaml(self, tmp_path: Path) -> None:
        """Should create valid YAML file."""
        from resume_as_code.services.work_unit_service import create_work_unit_from_data

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        file_path = create_work_unit_from_data(
            work_unit_id="wu-2024-01-15-test",
            title="Test Work Unit",
            problem_statement="This is the problem that needed solving",
            actions=["First action taken", "Second action taken"],
            result="The result achieved",
            work_units_dir=work_units_dir,
            archetype="minimal",
        )

        assert file_path.exists()

        with open(file_path) as f:
            data = yaml.safe_load(f)

        assert data["id"] == "wu-2024-01-15-test"
        assert data["title"] == "Test Work Unit"
        assert data["schema_version"] == "4.0.0"
        assert data["archetype"] == "minimal"
        assert data["problem"]["statement"] == "This is the problem that needed solving"
        assert len(data["actions"]) == 2
        assert data["outcome"]["result"] == "The result achieved"

    def test_includes_optional_fields(self, tmp_path: Path) -> None:
        """Should include optional fields when provided."""
        from resume_as_code.services.work_unit_service import create_work_unit_from_data

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        file_path = create_work_unit_from_data(
            work_unit_id="wu-2024-01-15-test",
            title="Test Work Unit",
            problem_statement="The problem statement",
            actions=["Action taken"],
            result="Result achieved",
            work_units_dir=work_units_dir,
            archetype="greenfield",
            position_id="pos-company-role",
            quantified_impact="50% improvement",
            skills=["Python", "Testing"],
            tags=["automation", "testing"],
            start_date="2024-01",
            end_date="2024-06",
        )

        with open(file_path) as f:
            data = yaml.safe_load(f)

        assert data["position_id"] == "pos-company-role"
        assert data["outcome"]["quantified_impact"] == "50% improvement"
        assert len(data["skills_demonstrated"]) == 2
        assert data["skills_demonstrated"][0]["name"] == "Python"
        assert len(data["tags"]) == 2
        assert data["time_started"] == "2024-01"
        assert data["time_ended"] == "2024-06"
