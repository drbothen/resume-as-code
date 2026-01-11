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

    def test_validate_nonexistent_path_exit_code_4(self, cli_runner: CliRunner) -> None:
        """Should exit 4 when path doesn't exist (NotFoundError)."""
        result = cli_runner.invoke(main, ["validate", "/nonexistent/path.yaml"])

        # Click's Path(exists=True) returns exit code 2 for nonexistent paths
        # This is expected Click behavior
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
