"""Tests for CLI error handling utilities."""

from __future__ import annotations

import json

import click
from click.testing import CliRunner

from resume_as_code.models.errors import (
    ConfigurationError,
    NotFoundError,
    RuntimeSystemError,
    UserError,
    ValidationError,
)
from resume_as_code.utils.errors import handle_errors


class TestHandleErrorsDecorator:
    """Test the @handle_errors decorator."""

    def test_successful_function_returns_normally(self) -> None:
        """Functions that succeed return their result."""

        @handle_errors
        def success_func() -> str:
            return "success"

        result = success_func()
        assert result == "success"

    def test_user_error_exits_with_code_1(self) -> None:
        """UserError should exit with code 1."""

        @click.command()
        @handle_errors
        def fail_cmd() -> None:
            raise UserError("Invalid input")

        runner = CliRunner()
        result = runner.invoke(fail_cmd)
        assert result.exit_code == 1

    def test_configuration_error_exits_with_code_2(self) -> None:
        """ConfigurationError should exit with code 2."""

        @click.command()
        @handle_errors
        def fail_cmd() -> None:
            raise ConfigurationError("Bad config")

        runner = CliRunner()
        result = runner.invoke(fail_cmd)
        assert result.exit_code == 2

    def test_validation_error_exits_with_code_3(self) -> None:
        """ValidationError should exit with code 3."""

        @click.command()
        @handle_errors
        def fail_cmd() -> None:
            raise ValidationError("Validation failed")

        runner = CliRunner()
        result = runner.invoke(fail_cmd)
        assert result.exit_code == 3

    def test_not_found_error_exits_with_code_4(self) -> None:
        """NotFoundError should exit with code 4."""

        @click.command()
        @handle_errors
        def fail_cmd() -> None:
            raise NotFoundError("File not found")

        runner = CliRunner()
        result = runner.invoke(fail_cmd)
        assert result.exit_code == 4

    def test_system_error_exits_with_code_5(self) -> None:
        """RuntimeSystemError should exit with code 5."""

        @click.command()
        @handle_errors
        def fail_cmd() -> None:
            raise RuntimeSystemError("System failure")

        runner = CliRunner()
        result = runner.invoke(fail_cmd)
        assert result.exit_code == 5

    def test_unexpected_error_exits_with_code_5(self) -> None:
        """Unexpected exceptions should exit with code 5."""

        @click.command()
        @handle_errors
        def fail_cmd() -> None:
            raise RuntimeError("Unexpected error")

        runner = CliRunner()
        result = runner.invoke(fail_cmd)
        assert result.exit_code == 5


class TestErrorOutput:
    """Test error output formatting."""

    def test_error_message_in_output(self) -> None:
        """Error message should appear in output."""

        @click.command()
        @handle_errors
        def fail_cmd() -> None:
            raise UserError("This is the error message")

        runner = CliRunner()
        result = runner.invoke(fail_cmd)
        # Error goes to stdout when using CliRunner (it captures both)
        assert "This is the error message" in result.output

    def test_path_shown_when_provided(self) -> None:
        """Path should be shown when provided."""

        @click.command()
        @handle_errors
        def fail_cmd() -> None:
            raise ValidationError("Error", path="/some/file.yaml:10")

        runner = CliRunner()
        result = runner.invoke(fail_cmd)
        assert "/some/file.yaml:10" in result.output

    def test_suggestion_shown_when_provided(self) -> None:
        """Suggestion should be shown when provided."""

        @click.command()
        @handle_errors
        def fail_cmd() -> None:
            raise UserError("Error", suggestion="Try this instead")

        runner = CliRunner()
        result = runner.invoke(fail_cmd)
        assert "Try this instead" in result.output


class TestQuietMode:
    """Test error handling in quiet mode."""

    def test_quiet_mode_suppresses_output(self) -> None:
        """Quiet mode should suppress error output."""
        from resume_as_code.cli import main

        @main.command("fail-quiet-test")
        @handle_errors
        def fail_cmd() -> None:
            raise UserError("This error should be suppressed")

        runner = CliRunner()
        result = runner.invoke(main, ["--quiet", "fail-quiet-test"])
        assert result.exit_code == 1
        # In quiet mode, output should not contain the error message
        assert "This error should be suppressed" not in result.output

        # Clean up: remove the test command
        main.commands.pop("fail-quiet-test", None)


class TestJsonMode:
    """Test error handling in JSON mode."""

    def test_json_mode_outputs_structured_error(self) -> None:
        """JSON mode should output structured error."""
        from resume_as_code.cli import main

        @main.command("fail-json-test")
        @handle_errors
        def fail_cmd() -> None:
            raise ValidationError(
                message="Missing required field",
                path="test.yaml:5",
                suggestion="Add the field",
            )

        runner = CliRunner()
        result = runner.invoke(main, ["--json", "fail-json-test"])
        assert result.exit_code == 3

        # Parse JSON output
        output = json.loads(result.output)
        assert output["status"] == "error"
        assert len(output["errors"]) == 1
        assert output["errors"][0]["code"] == "VALIDATION_ERROR"
        assert output["errors"][0]["message"] == "Missing required field"
        assert output["errors"][0]["path"] == "test.yaml:5"
        assert output["errors"][0]["suggestion"] == "Add the field"
        assert output["errors"][0]["recoverable"] is True

        # Clean up
        main.commands.pop("fail-json-test", None)

    def test_json_mode_includes_command_name(self) -> None:
        """JSON output should include command name."""
        from resume_as_code.cli import main

        @main.command("fail-json-cmd-test")
        @handle_errors
        def fail_cmd() -> None:
            raise UserError("Error")

        runner = CliRunner()
        result = runner.invoke(main, ["--json", "fail-json-cmd-test"])

        output = json.loads(result.output)
        assert output["command"] == "fail-json-cmd-test"

        # Clean up
        main.commands.pop("fail-json-cmd-test", None)
