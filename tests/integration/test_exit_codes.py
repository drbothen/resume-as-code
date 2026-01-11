"""Integration tests for CLI exit codes (AC #1-#6)."""

from __future__ import annotations

from click.testing import CliRunner

from resume_as_code.cli import main


def test_help_returns_exit_code_0() -> None:
    """--help should exit with code 0 (AC #1)."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0


def test_version_returns_exit_code_0() -> None:
    """--version should exit with code 0 (AC #1)."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0


def test_no_command_returns_exit_code_0() -> None:
    """Running with no command should show help and exit 0 (AC #1)."""
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0


def test_config_returns_exit_code_0() -> None:
    """config command should exit with code 0 when config exists (AC #1)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a minimal config file
        import os

        os.makedirs(".resume", exist_ok=True)
        with open(".resume/config.yaml", "w") as f:
            f.write("work_units_dir: work-units\noutput_dir: output\n")
        result = runner.invoke(main, ["config"])
        assert result.exit_code == 0


def test_unknown_command_returns_error() -> None:
    """Unknown command should return non-zero exit code."""
    runner = CliRunner()
    result = runner.invoke(main, ["nonexistent-command"])
    assert result.exit_code != 0
