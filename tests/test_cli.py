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


def test_version_matches_expected() -> None:
    """Test that version is 0.1.0 as specified."""
    assert __version__ == "0.1.0"
