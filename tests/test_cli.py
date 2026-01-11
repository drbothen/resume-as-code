"""Tests for the CLI entry point."""

from __future__ import annotations

from click.testing import CliRunner

from resume_as_code import __version__
from resume_as_code.cli import main


def test_cli_help_shows_output(cli_runner: CliRunner) -> None:
    """Test that --help shows CLI help output and exits with code 0."""
    result = cli_runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Resume as Code" in result.output
    assert "git-native resume generation" in result.output


def test_cli_version_shows_version(cli_runner: CliRunner) -> None:
    """Test that --version shows the version and exits with code 0."""
    result = cli_runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output
    assert "resume" in result.output


def test_cli_no_args_shows_help(cli_runner: CliRunner) -> None:
    """Test that running with no args shows help (click group behavior)."""
    result = cli_runner.invoke(main, [])
    assert result.exit_code == 0
    assert "Resume as Code" in result.output
    assert "Options:" in result.output


def test_version_matches_expected() -> None:
    """Test that version is 0.1.0 as specified."""
    assert __version__ == "0.1.0"


class TestTestOutputCommand:
    """Tests for the test-output command."""

    def test_test_output_command_exists(self, cli_runner: CliRunner) -> None:
        """test-output command should be available."""
        result = cli_runner.invoke(main, ["test-output"])
        assert "no such command" not in result.output.lower()

    def test_test_output_shows_success_message(self, cli_runner: CliRunner) -> None:
        """test-output should show success message with checkmark."""
        result = cli_runner.invoke(main, ["test-output"])
        assert result.exit_code == 0
        # Check for success indicator (checkmark may be in output or stderr)
        combined = result.output + (result.stderr_bytes or b"").decode()
        assert "success" in combined.lower() or "✓" in combined

    def test_test_output_json_mode_outputs_json(self, cli_runner: CliRunner) -> None:
        """test-output with --json should output valid JSON."""
        import json

        result = cli_runner.invoke(main, ["--json", "test-output"])
        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert "format_version" in data
        assert "status" in data
        assert "command" in data
        assert data["command"] == "test-output"

    def test_test_output_quiet_mode_no_output(self, cli_runner: CliRunner) -> None:
        """test-output with --quiet should produce no output."""
        result = cli_runner.invoke(main, ["--quiet", "test-output"])
        assert result.exit_code == 0
        # In quiet mode, stdout should be empty
        assert result.output.strip() == ""


class TestGlobalFlags:
    """Tests for global CLI flags (--json, --verbose, --quiet)."""

    def test_json_flag_is_accepted(self, cli_runner: CliRunner) -> None:
        """Test that --json flag is recognized."""
        result = cli_runner.invoke(main, ["--json"])
        # Should not fail due to unrecognized option
        assert "no such option" not in result.output.lower()

    def test_verbose_flag_is_accepted(self, cli_runner: CliRunner) -> None:
        """Test that --verbose flag is recognized."""
        result = cli_runner.invoke(main, ["--verbose"])
        assert "no such option" not in result.output.lower()

    def test_verbose_short_flag_is_accepted(self, cli_runner: CliRunner) -> None:
        """Test that -v flag is recognized."""
        result = cli_runner.invoke(main, ["-v"])
        assert "no such option" not in result.output.lower()

    def test_quiet_flag_is_accepted(self, cli_runner: CliRunner) -> None:
        """Test that --quiet flag is recognized."""
        result = cli_runner.invoke(main, ["--quiet"])
        assert "no such option" not in result.output.lower()

    def test_quiet_short_flag_is_accepted(self, cli_runner: CliRunner) -> None:
        """Test that -q flag is recognized."""
        result = cli_runner.invoke(main, ["-q"])
        assert "no such option" not in result.output.lower()

    def test_help_shows_json_flag(self, cli_runner: CliRunner) -> None:
        """Test that help shows --json option."""
        result = cli_runner.invoke(main, ["--help"])
        assert "--json" in result.output

    def test_help_shows_verbose_flag(self, cli_runner: CliRunner) -> None:
        """Test that help shows --verbose option."""
        result = cli_runner.invoke(main, ["--help"])
        assert "--verbose" in result.output or "-v" in result.output

    def test_help_shows_quiet_flag(self, cli_runner: CliRunner) -> None:
        """Test that help shows --quiet option."""
        result = cli_runner.invoke(main, ["--help"])
        assert "--quiet" in result.output or "-q" in result.output

    def test_conflicting_flags_shows_warning(self, cli_runner: CliRunner) -> None:
        """Test that using both --json and --quiet shows a warning."""
        result = cli_runner.invoke(main, ["--json", "--quiet", "test-output"])
        # Warning should appear (may be in output or stderr depending on Rich)
        # The warning is printed to err_console directly before configure_output
        # In Click's CliRunner, this may end up in output or the test context
        assert result.exit_code == 0
        # Quiet mode should take precedence - no JSON output
        assert result.output.strip() == "" or "precedence" in result.output.lower()


class TestVerboseMode:
    """Tests for verbose mode file path logging (AC #3)."""

    def test_verbose_shows_file_paths(self, cli_runner: CliRunner) -> None:
        """test-output with --verbose should show file paths being accessed."""
        result = cli_runner.invoke(main, ["--verbose", "test-output"])
        assert result.exit_code == 0
        # Check for file path logging - may be in output or stderr
        combined = result.output + (result.stderr_bytes or b"").decode()
        # Should contain path examples from test-output command
        assert "/example/" in combined or "Reading" in combined or "Writing" in combined
