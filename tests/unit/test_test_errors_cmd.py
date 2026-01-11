"""Tests for the test-errors command."""

from __future__ import annotations

import json

from click.testing import CliRunner

from resume_as_code.cli import main


class TestTestErrorsCommand:
    """Test the test-errors command for exit code verification."""

    def test_user_error_exit_code_1(self) -> None:
        """--type user should exit with code 1."""
        runner = CliRunner()
        result = runner.invoke(main, ["test-errors", "--type", "user"])
        assert result.exit_code == 1

    def test_config_error_exit_code_2(self) -> None:
        """--type config should exit with code 2."""
        runner = CliRunner()
        result = runner.invoke(main, ["test-errors", "--type", "config"])
        assert result.exit_code == 2

    def test_validation_error_exit_code_3(self) -> None:
        """--type validation should exit with code 3."""
        runner = CliRunner()
        result = runner.invoke(main, ["test-errors", "--type", "validation"])
        assert result.exit_code == 3

    def test_notfound_error_exit_code_4(self) -> None:
        """--type notfound should exit with code 4."""
        runner = CliRunner()
        result = runner.invoke(main, ["test-errors", "--type", "notfound"])
        assert result.exit_code == 4

    def test_system_error_exit_code_5(self) -> None:
        """--type system should exit with code 5."""
        runner = CliRunner()
        result = runner.invoke(main, ["test-errors", "--type", "system"])
        assert result.exit_code == 5


class TestTestErrorsJsonOutput:
    """Test JSON output from test-errors command."""

    def test_json_error_structure(self) -> None:
        """JSON output should have correct structure."""
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "test-errors", "--type", "validation"])
        assert result.exit_code == 3

        output = json.loads(result.output)
        assert output["status"] == "error"
        assert len(output["errors"]) == 1

        error = output["errors"][0]
        assert error["code"] == "VALIDATION_ERROR"
        assert "message" in error
        assert "path" in error
        assert "suggestion" in error
        assert "recoverable" in error

    def test_json_validation_error_recoverable(self) -> None:
        """ValidationError should be recoverable by default."""
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "test-errors", "--type", "validation"])

        output = json.loads(result.output)
        assert output["errors"][0]["recoverable"] is True

    def test_json_system_error_not_recoverable(self) -> None:
        """SystemError should NOT be recoverable by default."""
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "test-errors", "--type", "system"])

        output = json.loads(result.output)
        assert output["errors"][0]["recoverable"] is False

    def test_recoverable_override_to_true(self) -> None:
        """--recoverable should override default to True."""
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "test-errors", "--type", "system", "--recoverable"])

        output = json.loads(result.output)
        assert output["errors"][0]["recoverable"] is True

    def test_recoverable_override_to_false(self) -> None:
        """--not-recoverable should override default to False."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["--json", "test-errors", "--type", "user", "--not-recoverable"]
        )

        output = json.loads(result.output)
        assert output["errors"][0]["recoverable"] is False


class TestTestErrorsQuietMode:
    """Test quiet mode with test-errors command."""

    def test_quiet_mode_no_output(self) -> None:
        """Quiet mode should suppress error output."""
        runner = CliRunner()
        result = runner.invoke(main, ["--quiet", "test-errors", "--type", "user"])
        assert result.exit_code == 1
        # Output should be empty or minimal
        assert "Invalid flag" not in result.output


class TestTestErrorsHelp:
    """Test help output for test-errors command."""

    def test_help_shows_error_types(self) -> None:
        """--help should show available error types."""
        runner = CliRunner()
        result = runner.invoke(main, ["test-errors", "--help"])
        assert result.exit_code == 0
        assert "user" in result.output
        assert "config" in result.output
        assert "validation" in result.output
        assert "notfound" in result.output
        assert "system" in result.output
