"""Integration tests for validate command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main

VALID_WORK_UNIT = """\
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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

        result = cli_runner.invoke(main, ["validate", str(file_path)])

        assert result.exit_code == 0

    def test_validate_directory(self, tmp_path: Path, cli_runner: CliRunner) -> None:
        """Should validate all YAML files in directory (AC #3)."""
        (tmp_path / "wu-1.yaml").write_text(VALID_WORK_UNIT)
        (tmp_path / "wu-2.yaml").write_text(VALID_WORK_UNIT)

        result = cli_runner.invoke(main, ["validate", str(tmp_path)])

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
        result = cli_runner.invoke(main, ["validate", "/nonexistent/path.yaml"])

        # Click's Path(exists=True) validates before command runs, returns exit code 2
        assert result.exit_code == 2


class TestValidateCommandJsonOutput:
    """Tests for validate command JSON output."""

    def test_validate_json_output_structure(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output valid JSON with expected structure (AC #6)."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-test.yaml").write_text(VALID_WORK_UNIT)

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["--json", "validate"])

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
        """Should return JSON with zero counts for empty directory."""
        work_units = tmp_path / "work-units"
        work_units.mkdir()

        monkeypatch.chdir(tmp_path)
        result = cli_runner.invoke(main, ["--json", "validate"])

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
        assert "wu-invalid.yaml" in result.output

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
schema_version: "1.0.0"
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

        result = cli_runner.invoke(main, ["validate", "--content-quality", str(file_path)])

        assert result.exit_code == 0  # Valid schema, warnings don't affect exit code
        assert "WEAK_ACTION_VERB" in result.output
        assert "managed" in result.output.lower()

    def test_content_quality_suggests_alternatives(
        self, tmp_path: Path, cli_runner: CliRunner
    ) -> None:
        """Should suggest strong verb alternatives (AC #7)."""
        file_path = tmp_path / "wu-weak.yaml"
        file_path.write_text(WORK_UNIT_WITH_WEAK_VERBS)

        result = cli_runner.invoke(main, ["validate", "--content-quality", str(file_path)])

        assert result.exit_code == 0
        # Should suggest alternatives for 'managed'
        assert "orchestrated" in result.output.lower() or "directed" in result.output.lower()

    def test_content_quality_detects_verb_repetition(
        self, tmp_path: Path, cli_runner: CliRunner
    ) -> None:
        """Should flag verb repetition (AC #6)."""
        file_path = tmp_path / "wu-weak.yaml"
        file_path.write_text(WORK_UNIT_WITH_WEAK_VERBS)

        result = cli_runner.invoke(main, ["validate", "--content-quality", str(file_path)])

        assert result.exit_code == 0
        assert "VERB_REPETITION" in result.output
        assert "managed" in result.output.lower()

    def test_content_quality_detects_missing_quantification(
        self, tmp_path: Path, cli_runner: CliRunner
    ) -> None:
        """Should warn about missing quantification (AC #6)."""
        file_path = tmp_path / "wu-weak.yaml"
        file_path.write_text(WORK_UNIT_WITH_WEAK_VERBS)

        result = cli_runner.invoke(main, ["validate", "--content-quality", str(file_path)])

        assert result.exit_code == 0
        assert "MISSING_QUANTIFICATION" in result.output

    def test_content_quality_json_output(self, tmp_path: Path, cli_runner: CliRunner) -> None:
        """Should include content warnings in JSON output."""
        file_path = tmp_path / "wu-weak.yaml"
        file_path.write_text(WORK_UNIT_WITH_WEAK_VERBS)

        result = cli_runner.invoke(
            main, ["--json", "validate", "--content-quality", str(file_path)]
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
schema_version: "1.0.0"
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

        result = cli_runner.invoke(main, ["validate", "--content-density", str(file_path)])

        assert result.exit_code == 0
        assert "BULLET_TOO_SHORT" in result.output
        assert "100" in result.output  # Minimum character count

    def test_content_density_warns_long_bullets(
        self, tmp_path: Path, cli_runner: CliRunner
    ) -> None:
        """Should warn about too-long bullets (AC #8)."""
        long_action = "x" * 200
        work_unit = f"""\
schema_version: "1.0.0"
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

        result = cli_runner.invoke(main, ["validate", "--content-density", str(file_path)])

        assert result.exit_code == 0
        assert "BULLET_TOO_LONG" in result.output
        assert "160" in result.output  # Maximum character count

    def test_content_density_no_warning_optimal_length(
        self, tmp_path: Path, cli_runner: CliRunner
    ) -> None:
        """Should not warn for optimal length bullets (100-160 chars)."""
        optimal_action = "x" * 130  # Within range
        work_unit = f"""\
schema_version: "1.0.0"
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

        result = cli_runner.invoke(main, ["validate", "--content-density", str(file_path)])

        assert result.exit_code == 0
        # Should show successful validation without density warnings
        assert "BULLET_TOO_SHORT" not in result.output
        assert "BULLET_TOO_LONG" not in result.output

    def test_content_density_json_output(self, tmp_path: Path, cli_runner: CliRunner) -> None:
        """Should include content density warnings in JSON output."""
        # Action must be at least 10 chars to pass schema, but under 100 for density warning
        short_action = "Completed a short task here"  # 27 chars
        work_unit = f"""\
schema_version: "1.0.0"
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

        result = cli_runner.invoke(
            main, ["--json", "validate", "--content-density", str(file_path)]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "content_warnings" in data["data"]
        assert any(w["code"] == "BULLET_TOO_SHORT" for w in data["data"]["content_warnings"])


WORK_UNIT_WITH_POSITION = """\
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
        result = cli_runner.invoke(main, ["validate", "--check-positions"])

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
        result = cli_runner.invoke(main, ["validate", "--check-positions"])

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
        result = cli_runner.invoke(main, ["validate", "--check-positions"])

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
        result = cli_runner.invoke(main, ["validate", "--check-positions"])

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
        result = cli_runner.invoke(main, ["--json", "validate", "--check-positions"])

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
        result = cli_runner.invoke(main, ["--json", "validate", "--check-positions"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "content_warnings" in data["data"]
        assert any(w["code"] == "MISSING_POSITION_ID" for w in data["data"]["content_warnings"])
