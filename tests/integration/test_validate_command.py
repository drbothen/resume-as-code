"""Integration tests for validate command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main

VALID_WORK_UNIT = """\
schema_version: "4.0.0"
archetype: minimal
id: "wu-2026-01-10-test-work-unit"
title: "Test Work Unit for Validation"

problem:
  statement: "A test problem statement that is long enough"

actions:
  - "Took an action that is long enough"

outcome:
  result: "Got a result that is long enough"
"""

INVALID_WORK_UNIT = """\
schema_version: "4.0.0"
archetype: minimal
id: "wu-2026-01-10-test"
# Missing required fields: title, problem, actions, outcome
"""


class TestValidateCommandSuccess:
    """Tests for validate command success scenarios."""

    def test_validate_all_pass_exit_code_0(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should exit 0 when all Work Units valid (AC #4)."""
        # Create work-units directory with valid file
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(VALID_WORK_UNIT)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate"])

        assert result.exit_code == 0
        assert "passed validation" in result.output.lower() or "valid" in result.output.lower()

    def test_validate_specific_file(self, tmp_path: Path, cli_runner: CliRunner) -> None:
        """Should validate only specified file (AC #2)."""
        file_path = tmp_path / "wu-test.yaml"
        file_path.write_text(VALID_WORK_UNIT)

        # Story 11.5: Use work-units subcommand with PATH argument
        result = cli_runner.invoke(main, ["validate", "work-units", str(file_path)])

        assert result.exit_code == 0

    def test_validate_directory(self, tmp_path: Path, cli_runner: CliRunner) -> None:
        """Should validate all YAML files in directory (AC #3)."""
        (tmp_path / "wu-1.yaml").write_text(VALID_WORK_UNIT)
        (tmp_path / "wu-2.yaml").write_text(VALID_WORK_UNIT)

        # Story 11.5: Use work-units subcommand with PATH argument
        result = cli_runner.invoke(main, ["validate", "work-units", str(tmp_path)])

        assert result.exit_code == 0

    def test_validate_no_work_units_dir(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should handle missing work-units directory gracefully."""
        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate"])

        # Should succeed with informational message (no files to validate)
        assert result.exit_code == 0


class TestValidateCommandErrors:
    """Tests for validate command error scenarios."""

    def test_validate_with_errors_exit_code_3(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should exit 3 when Work Units have errors (AC #5)."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-invalid.yaml").write_text(INVALID_WORK_UNIT)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate"])

        assert result.exit_code == 3

    def test_validate_nonexistent_path_click_error(self, cli_runner: CliRunner) -> None:
        """Should exit 2 when path doesn't exist (Click validation)."""
        # Story 11.5: Use work-units subcommand with PATH argument
        result = cli_runner.invoke(main, ["validate", "work-units", "/nonexistent/path.yaml"])

        # Click's Path(exists=True) validates before command runs, returns exit code 2
        assert result.exit_code == 2


class TestValidateCommandJsonOutput:
    """Tests for validate command JSON output."""

    def test_validate_json_output_structure(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output valid JSON with expected structure (AC #6).

        Story 11.5: validate (no subcommand) now returns aggregated results
        with resources array. Use work-units subcommand for legacy structure.
        """
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(VALID_WORK_UNIT)

        monkeypatch.chdir(tmp_path)
        # Use work-units subcommand for work-unit specific output structure
        result = cli_runner.invoke(main, ["--json", "validate", "work-units"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "valid_count" in data["data"]
        assert "invalid_count" in data["data"]
        assert "files" in data["data"]

    def test_validate_json_output_with_errors(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include errors array in JSON output when invalid."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-invalid.yaml").write_text(INVALID_WORK_UNIT)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["--json", "validate"])

        assert result.exit_code == 3
        data = json.loads(result.output)
        assert data["status"] == "error"
        assert "errors" in data

    def test_validate_json_empty_directory(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return JSON with zero counts for empty directory.

        Story 11.5: validate (no subcommand) returns aggregated results.
        Use work-units subcommand for legacy structure.
        """
        work_units = tmp_path / "work-units"
        work_units.mkdir()

        monkeypatch.chdir(tmp_path)
        # Use work-units subcommand for work-unit specific output structure
        result = cli_runner.invoke(main, ["--json", "validate", "work-units"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["valid_count"] == 0
        assert data["data"]["invalid_count"] == 0


class TestValidateCommandSummary:
    """Tests for validate command summary output."""

    def test_shows_file_count_summary(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show total files checked and pass/fail count (AC #1)."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-1.yaml").write_text(VALID_WORK_UNIT)
        (work_units / "wu-2.yaml").write_text(VALID_WORK_UNIT)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate"])

        assert result.exit_code == 0
        # Should show count of validated files
        assert "2" in result.output

    def test_lists_invalid_files_with_errors(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should list each invalid file with its errors (AC #5)."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-invalid.yaml").write_text(INVALID_WORK_UNIT)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate"])

        assert result.exit_code == 3
        # Rich may wrap long paths with newlines, so normalize before checking
        normalized_output = result.output.replace("\n", "")
        assert "wu-invalid.yaml" in normalized_output

    def test_rich_output_color_coded(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should have color-coded errors in Rich output (AC #5)."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-invalid.yaml").write_text(INVALID_WORK_UNIT)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate"], color=True)

        # Check error indicator present
        assert result.exit_code == 3
        # Rich output should contain error symbols
        assert "✗" in result.output or "failed" in result.output.lower()

    def test_rich_output_shows_suggestions(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show suggestions with errors (AC #5)."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-invalid.yaml").write_text(INVALID_WORK_UNIT)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate"])

        assert result.exit_code == 3
        # Should include helpful suggestions
        assert "Add" in result.output or "required" in result.output.lower()


WORK_UNIT_WITH_WEAK_VERBS = """\
schema_version: "4.0.0"
archetype: minimal
id: "wu-2026-01-10-test-weak-verbs"
title: "Test Work Unit with Weak Verbs"

problem:
  statement: "A test problem statement that is long enough"

actions:
  - "Managed a team of engineers to deliver the project"
  - "Handled customer complaints and resolved issues"
  - "Managed the budget for the department"

outcome:
  result: "Things got better overall for the team"
"""


class TestValidateContentQuality:
    """Tests for content quality validation (AC #6, #7)."""

    def test_content_quality_flag_detects_weak_verbs(
        self, tmp_path: Path, cli_runner: CliRunner
    ) -> None:
        """Should detect weak action verbs with --content-quality flag (AC #6)."""
        file_path = tmp_path / "wu-weak.yaml"
        file_path.write_text(WORK_UNIT_WITH_WEAK_VERBS)

        # Story 11.5: Use work-units subcommand for content quality flags
        result = cli_runner.invoke(
            main, ["validate", "work-units", "--content-quality", str(file_path)]
        )

        assert result.exit_code == 0  # Valid schema, warnings don't affect exit code
        assert "WEAK_ACTION_VERB" in result.output
        assert "managed" in result.output.lower()

    def test_content_quality_suggests_alternatives(
        self, tmp_path: Path, cli_runner: CliRunner
    ) -> None:
        """Should suggest strong verb alternatives (AC #7)."""
        file_path = tmp_path / "wu-weak.yaml"
        file_path.write_text(WORK_UNIT_WITH_WEAK_VERBS)

        # Story 11.5: Use work-units subcommand for content quality flags
        result = cli_runner.invoke(
            main, ["validate", "work-units", "--content-quality", str(file_path)]
        )

        assert result.exit_code == 0
        # Should suggest alternatives for 'managed'
        assert "orchestrated" in result.output.lower() or "directed" in result.output.lower()

    def test_content_quality_detects_verb_repetition(
        self, tmp_path: Path, cli_runner: CliRunner
    ) -> None:
        """Should flag verb repetition (AC #6)."""
        file_path = tmp_path / "wu-weak.yaml"
        file_path.write_text(WORK_UNIT_WITH_WEAK_VERBS)

        # Story 11.5: Use work-units subcommand for content quality flags
        result = cli_runner.invoke(
            main, ["validate", "work-units", "--content-quality", str(file_path)]
        )

        assert result.exit_code == 0
        assert "VERB_REPETITION" in result.output
        assert "managed" in result.output.lower()

    def test_content_quality_detects_missing_quantification(
        self, tmp_path: Path, cli_runner: CliRunner
    ) -> None:
        """Should warn about missing quantification (AC #6)."""
        file_path = tmp_path / "wu-weak.yaml"
        file_path.write_text(WORK_UNIT_WITH_WEAK_VERBS)

        # Story 11.5: Use work-units subcommand for content quality flags
        result = cli_runner.invoke(
            main, ["validate", "work-units", "--content-quality", str(file_path)]
        )

        assert result.exit_code == 0
        assert "MISSING_QUANTIFICATION" in result.output

    def test_content_quality_json_output(self, tmp_path: Path, cli_runner: CliRunner) -> None:
        """Should include content warnings in JSON output."""
        file_path = tmp_path / "wu-weak.yaml"
        file_path.write_text(WORK_UNIT_WITH_WEAK_VERBS)

        # Story 11.5: Use work-units subcommand for content quality flags
        result = cli_runner.invoke(
            main, ["--json", "validate", "work-units", "--content-quality", str(file_path)]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "content_warnings" in data["data"]
        assert len(data["data"]["content_warnings"]) > 0


class TestValidateContentDensity:
    """Tests for content density validation (AC #8)."""

    def test_content_density_warns_short_bullets(
        self, tmp_path: Path, cli_runner: CliRunner
    ) -> None:
        """Should warn about too-short bullets (AC #8)."""
        # Action must be at least 10 chars to pass schema, but under 100 for density warning
        short_action = "Completed a short task here"  # 27 chars, triggers density warning
        work_unit = f"""\
schema_version: "4.0.0"
archetype: minimal
id: "wu-2026-01-10-test-short"
title: "Test Work Unit with Short Actions"

problem:
  statement: "A test problem statement that is long enough"

actions:
  - "{short_action}"

outcome:
  result: "Got a result that is long enough"
"""
        file_path = tmp_path / "wu-short.yaml"
        file_path.write_text(work_unit)

        # Story 11.5: Use work-units subcommand for content density flags
        result = cli_runner.invoke(
            main, ["validate", "work-units", "--content-density", str(file_path)]
        )

        assert result.exit_code == 0
        assert "BULLET_TOO_SHORT" in result.output
        assert "100" in result.output  # Minimum character count

    def test_content_density_warns_long_bullets(
        self, tmp_path: Path, cli_runner: CliRunner
    ) -> None:
        """Should warn about too-long bullets (AC #8)."""
        long_action = "x" * 200
        work_unit = f"""\
schema_version: "4.0.0"
archetype: minimal
id: "wu-2026-01-10-test-long"
title: "Test Work Unit with Long Actions"

problem:
  statement: "A test problem statement that is long enough"

actions:
  - "{long_action}"

outcome:
  result: "Got a result that is long enough"
"""
        file_path = tmp_path / "wu-long.yaml"
        file_path.write_text(work_unit)

        # Story 11.5: Use work-units subcommand for content density flags
        result = cli_runner.invoke(
            main, ["validate", "work-units", "--content-density", str(file_path)]
        )

        assert result.exit_code == 0
        assert "BULLET_TOO_LONG" in result.output
        assert "160" in result.output  # Maximum character count

    def test_content_density_no_warning_optimal_length(
        self, tmp_path: Path, cli_runner: CliRunner
    ) -> None:
        """Should not warn for optimal length bullets (100-160 chars)."""
        optimal_action = "x" * 130  # Within range
        work_unit = f"""\
schema_version: "4.0.0"
archetype: minimal
id: "wu-2026-01-10-test-optimal"
title: "Test Work Unit with Optimal Actions"

problem:
  statement: "A test problem statement that is long enough"

actions:
  - "{optimal_action}"

outcome:
  result: "Got a result that is long enough"
"""
        file_path = tmp_path / "wu-optimal.yaml"
        file_path.write_text(work_unit)

        # Story 11.5: Use work-units subcommand for content density flags
        result = cli_runner.invoke(
            main, ["validate", "work-units", "--content-density", str(file_path)]
        )

        assert result.exit_code == 0
        # Should show successful validation without density warnings
        assert "BULLET_TOO_SHORT" not in result.output
        assert "BULLET_TOO_LONG" not in result.output

    def test_content_density_json_output(self, tmp_path: Path, cli_runner: CliRunner) -> None:
        """Should include content density warnings in JSON output."""
        # Action must be at least 10 chars to pass schema, but under 100 for density warning
        short_action = "Completed a short task here"  # 27 chars
        work_unit = f"""\
schema_version: "4.0.0"
archetype: minimal
id: "wu-2026-01-10-test-short"
title: "Test Work Unit with Short Actions"

problem:
  statement: "A test problem statement that is long enough"

actions:
  - "{short_action}"

outcome:
  result: "Got a result that is long enough"
"""
        file_path = tmp_path / "wu-short.yaml"
        file_path.write_text(work_unit)

        # Story 11.5: Use work-units subcommand for content density flags
        result = cli_runner.invoke(
            main, ["--json", "validate", "work-units", "--content-density", str(file_path)]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "content_warnings" in data["data"]
        assert any(w["code"] == "BULLET_TOO_SHORT" for w in data["data"]["content_warnings"])


WORK_UNIT_WITH_POSITION = """\
schema_version: "4.0.0"
archetype: minimal
id: "wu-2026-01-10-with-position"
title: "Test Work Unit with Position ID"
position_id: "pos-techcorp-senior"

problem:
  statement: "A test problem statement that is long enough"

actions:
  - "Took an action that is long enough"

outcome:
  result: "Got a result that is long enough"
"""

WORK_UNIT_WITHOUT_POSITION = """\
schema_version: "4.0.0"
archetype: minimal
id: "wu-2026-01-10-no-position"
title: "Test Work Unit without Position ID"

problem:
  statement: "A test problem statement that is long enough"

actions:
  - "Took an action that is long enough"

outcome:
  result: "Got a result that is long enough"
"""

POSITIONS_YAML = """\
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-techcorp-senior:
    employer: "TechCorp Industries"
    title: "Senior Platform Engineer"
    start_date: "2022-01"
  pos-techcorp-junior:
    employer: "TechCorp Industries"
    title: "Platform Engineer"
    start_date: "2020-01"
    end_date: "2021-12"
"""


class TestValidatePositionReferences:
    """Tests for position_id validation (Story 6.7, AC #7)."""

    def test_check_positions_warns_missing_position_id(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should warn about missing position_id (AC #7)."""
        # Create work-units directory with file without position_id
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(WORK_UNIT_WITHOUT_POSITION)

        # Create positions.yaml
        (tmp_path / "positions.yaml").write_text(POSITIONS_YAML)

        monkeypatch.chdir(tmp_path)
        # Story 11.5: Use work-units subcommand for --check-positions flag
        result = cli_runner.invoke(main, ["validate", "work-units", "--check-positions"])

        # Missing position_id is a warning, not an error - validation passes
        assert result.exit_code == 0
        assert "MISSING_POSITION_ID" in result.output

    def test_check_positions_error_invalid_position_id(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error on invalid position_id reference (AC #3)."""
        # Create work-units directory with file referencing non-existent position
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        work_unit_content = WORK_UNIT_WITH_POSITION.replace(
            "pos-techcorp-senior", "pos-nonexistent"
        )
        (work_units / "wu-test.yaml").write_text(work_unit_content)

        # Create positions.yaml without the referenced position
        (tmp_path / "positions.yaml").write_text(POSITIONS_YAML)

        monkeypatch.chdir(tmp_path)
        # Story 11.5: Use work-units subcommand for --check-positions flag
        result = cli_runner.invoke(main, ["validate", "work-units", "--check-positions"])

        # Invalid position_id is an error - validation fails
        assert result.exit_code == 3  # ValidationError exit code
        assert "INVALID_POSITION_ID" in result.output
        assert "pos-nonexistent" in result.output

    def test_check_positions_valid_position_id_passes(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should pass when position_id exists (AC #3)."""
        # Create work-units directory with valid position reference
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(WORK_UNIT_WITH_POSITION)

        # Create positions.yaml with the referenced position
        (tmp_path / "positions.yaml").write_text(POSITIONS_YAML)

        monkeypatch.chdir(tmp_path)
        # Story 11.5: Use work-units subcommand for --check-positions flag
        result = cli_runner.invoke(main, ["validate", "work-units", "--check-positions"])

        # Valid position_id passes without errors
        assert result.exit_code == 0
        assert "INVALID_POSITION_ID" not in result.output

    def test_check_positions_no_positions_file_warns(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should warn about missing position_id when no positions.yaml exists."""
        # Create work-units directory with file referencing a position
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(WORK_UNIT_WITH_POSITION)

        # No positions.yaml file

        monkeypatch.chdir(tmp_path)
        # Story 11.5: Use work-units subcommand for --check-positions flag
        result = cli_runner.invoke(main, ["validate", "work-units", "--check-positions"])

        # Without positions.yaml, position_id is treated as invalid reference
        assert result.exit_code == 3  # Error for invalid position_id
        assert "INVALID_POSITION_ID" in result.output

    def test_check_positions_json_output(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include position errors in JSON output."""
        # Create work-units directory with invalid position reference
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        work_unit_content = WORK_UNIT_WITH_POSITION.replace(
            "pos-techcorp-senior", "pos-nonexistent"
        )
        (work_units / "wu-test.yaml").write_text(work_unit_content)

        # Create positions.yaml
        (tmp_path / "positions.yaml").write_text(POSITIONS_YAML)

        monkeypatch.chdir(tmp_path)
        # Story 11.5: Use work-units subcommand for --check-positions flag
        result = cli_runner.invoke(main, ["--json", "validate", "work-units", "--check-positions"])

        assert result.exit_code == 3
        data = json.loads(result.output)
        assert "position_errors" in data["data"]
        assert any(e["code"] == "INVALID_POSITION_ID" for e in data["data"]["position_errors"])
        assert data["status"] == "error"

    def test_check_positions_json_output_warnings(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include position warnings in JSON output."""
        # Create work-units directory with file without position_id
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(WORK_UNIT_WITHOUT_POSITION)

        # Create positions.yaml
        (tmp_path / "positions.yaml").write_text(POSITIONS_YAML)

        monkeypatch.chdir(tmp_path)
        # Story 11.5: Use work-units subcommand for --check-positions flag
        result = cli_runner.invoke(main, ["--json", "validate", "work-units", "--check-positions"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "content_warnings" in data["data"]
        assert any(w["code"] == "MISSING_POSITION_ID" for w in data["data"]["content_warnings"])


# =============================================================================
# Story 11.5: Comprehensive Validation Tests
# =============================================================================


# Story 11.5: Certifications are root-level lists (not wrapped in certifications: key)
VALID_CERTIFICATIONS = """\
- name: "AWS Solutions Architect"
  issuer: "Amazon Web Services"
  date: "2023-01"
"""

INVALID_CERTIFICATIONS_DATE = """\
- name: "Invalid Cert"
  issuer: "Test Issuer"
  date: "2025-01"
  expires: "2024-01"
"""


class TestValidateAllResources:
    """Tests for comprehensive validation (Story 11.5 AC1)."""

    def test_validate_all_resources(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should validate all resource types when no subcommand (AC1)."""
        # Create minimal project
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(VALID_WORK_UNIT)
        (tmp_path / "positions.yaml").write_text(POSITIONS_YAML)
        (tmp_path / "certifications.yaml").write_text(VALID_CERTIFICATIONS)
        config_yaml = "schema_version: '2.0.0'\nwork_units_dir: work-units"
        (tmp_path / ".resume.yaml").write_text(config_yaml)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate"])

        assert result.exit_code == 0
        # Should show summary table with all resource types
        assert "Work Units" in result.output
        assert "Positions" in result.output
        assert "Certifications" in result.output

    def test_validate_all_shows_summary_table(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show summary table with counts (AC2)."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(VALID_WORK_UNIT)
        config_yaml = "schema_version: '2.0.0'\nwork_units_dir: work-units"
        (tmp_path / ".resume.yaml").write_text(config_yaml)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate"])

        assert result.exit_code == 0
        # Table headers should be present
        assert "Resource Type" in result.output
        assert "Valid" in result.output
        assert "Invalid" in result.output

    def test_validate_all_exit_code_on_errors(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should exit 3 when any resource has errors (AC6)."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(VALID_WORK_UNIT)
        (tmp_path / "certifications.yaml").write_text(INVALID_CERTIFICATIONS_DATE)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate"])

        assert result.exit_code == 3

    def test_validate_all_json_output(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output aggregated JSON with --json (AC5)."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(VALID_WORK_UNIT)
        config_yaml = "schema_version: '2.0.0'\nwork_units_dir: work-units"
        (tmp_path / ".resume.yaml").write_text(config_yaml)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["--json", "validate"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_valid" in data["data"]
        assert "total_invalid" in data["data"]
        assert "resources" in data["data"]
        assert isinstance(data["data"]["resources"], list)


class TestValidateSubcommands:
    """Tests for individual resource validation subcommands (Story 11.5 AC3)."""

    def test_validate_positions_subcommand(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should validate only positions with subcommand (AC3)."""
        (tmp_path / "positions.yaml").write_text(POSITIONS_YAML)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate", "positions"])

        assert result.exit_code == 0
        assert "Positions" in result.output

    def test_validate_certifications_subcommand(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should validate only certifications with subcommand (AC3)."""
        (tmp_path / "certifications.yaml").write_text(VALID_CERTIFICATIONS)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate", "certifications"])

        assert result.exit_code == 0
        assert "Certifications" in result.output

    def test_validate_certifications_cross_field_error(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should detect date > expires error (AC4)."""
        (tmp_path / "certifications.yaml").write_text(INVALID_CERTIFICATIONS_DATE)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate", "certifications"])

        assert result.exit_code == 3
        assert "INVALID_DATE_RANGE" in result.output

    def test_validate_work_units_subcommand(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should validate work-units with subcommand."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(VALID_WORK_UNIT)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate", "work-units"])

        assert result.exit_code == 0
        assert "passed" in result.output.lower()

    def test_validate_subcommand_json_output(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON for single resource (AC5)."""
        (tmp_path / "positions.yaml").write_text(POSITIONS_YAML)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["--json", "validate", "positions"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["resource_type"] == "Positions"
        assert "valid_count" in data["data"]
        assert "is_valid" in data["data"]

    def test_validate_config_subcommand(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should validate config with subcommand."""
        config_yaml = "schema_version: '2.0.0'\nwork_units_dir: work-units"
        (tmp_path / ".resume.yaml").write_text(config_yaml)
        (tmp_path / "work-units").mkdir()

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate", "config"])

        assert result.exit_code == 0
        assert "Config" in result.output

    def test_validate_board_roles_subcommand(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should validate board roles with subcommand."""
        # Story 11.5: Board roles are root-level lists (not wrapped in board_roles: key)
        board_roles_yaml = """\
- organization: "TechStartup Inc"
  role: "Technical Advisor"
  type: "advisory"
  start_date: "2021-01"
"""
        (tmp_path / "board-roles.yaml").write_text(board_roles_yaml)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate", "board-roles"])

        assert result.exit_code == 0
        assert "Board Roles" in result.output


class TestValidateHelpText:
    """Tests for validate command help text."""

    def test_validate_help_shows_subcommands(self, cli_runner: CliRunner) -> None:
        """Should list all subcommands in help."""
        result = cli_runner.invoke(main, ["validate", "--help"])

        assert result.exit_code == 0
        assert "work-units" in result.output
        assert "positions" in result.output
        assert "certifications" in result.output
        assert "education" in result.output
        assert "publications" in result.output
        assert "board-roles" in result.output
        assert "highlights" in result.output
        assert "config" in result.output


# Story 12.4 work unit fixtures for archetype validation
INCIDENT_ALIGNED_WORK_UNIT = """\
schema_version: "4.0.0"
id: "wu-2026-01-10-incident-response"
archetype: incident
title: "Resolved production database outage"

problem:
  statement: "Production database outage affecting 10K users during peak hours"
  context: "Critical P1 incident requiring immediate response"

actions:
  - "Detected via monitoring alerts and triaged impact"
  - "Mitigated by failing over to replica"
  - "Resolved root cause in connection pool configuration"
  - "Communicated status to stakeholders throughout"

outcome:
  result: "Restored service in 45 minutes"
  quantified_impact: "Prevented $50K impact with MTTR under SLA"
"""

MISALIGNED_ARCHETYPE_WORK_UNIT = """\
schema_version: "4.0.0"
id: "wu-2026-01-10-wrong-archetype"
archetype: incident
title: "Built new analytics platform from scratch"

problem:
  statement: "Team needed real-time analytics capability for business"
  context: "Gap in observability for customer behavior"

actions:
  - "Designed event-driven architecture"
  - "Built streaming data pipeline"
  - "Deployed to production with CI/CD"

outcome:
  result: "Delivered analytics platform serving 1M events/day"
  quantified_impact: "Enabled product team to make data-driven decisions"
"""


class TestValidateArchetypeAlignment:
    """Tests for --check-archetype flag (Story 12.4)."""

    def test_check_archetype_aligned_passes(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should pass when PAR structure matches archetype (AC1, AC2)."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(INCIDENT_ALIGNED_WORK_UNIT)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate", "work-units", "--check-archetype"])

        # Aligned work unit should not have archetype warnings
        assert result.exit_code == 0
        assert "ARCHETYPE_MISALIGNMENT" not in result.output

    def test_check_archetype_misaligned_warns(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should warn when PAR structure doesn't match archetype (AC6)."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(MISALIGNED_ARCHETYPE_WORK_UNIT)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate", "work-units", "--check-archetype"])

        # Misaligned work unit should have warnings but still pass (warnings not errors)
        assert result.exit_code == 0  # AC6: warnings don't fail validation
        assert "ARCHETYPE_MISALIGNMENT" in result.output
        assert "incident" in result.output.lower()

    def test_check_archetype_json_output(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include archetype warnings in JSON output."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(MISALIGNED_ARCHETYPE_WORK_UNIT)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["--json", "validate", "work-units", "--check-archetype"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "archetype_warnings" in data["data"]
        assert len(data["data"]["archetype_warnings"]) > 0
        assert data["data"]["archetype_warnings"][0]["code"] == "ARCHETYPE_MISALIGNMENT"

    def test_check_archetype_minimal_no_validation(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Minimal archetype should pass without validation (AC4)."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(VALID_WORK_UNIT)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["validate", "work-units", "--check-archetype"])

        # Minimal archetype should pass without archetype warnings
        assert result.exit_code == 0
        assert "ARCHETYPE_MISALIGNMENT" not in result.output

    def test_check_archetype_help_text(self, cli_runner: CliRunner) -> None:
        """Should show --check-archetype in help (AC5)."""
        result = cli_runner.invoke(main, ["validate", "work-units", "--help"])

        assert result.exit_code == 0
        assert "--check-archetype" in result.output
        assert "PAR structure" in result.output or "archetype" in result.output
