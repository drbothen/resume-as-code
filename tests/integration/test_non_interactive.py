"""Integration tests for non-interactive operation (AC #9, FR38)."""

from __future__ import annotations

from click.testing import CliRunner

from resume_as_code.cli import main


def test_cli_help_mentions_non_interactive() -> None:
    """CLI help should document non-interactive operation."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "non-interactive" in result.output.lower()


def test_all_commands_complete_without_input() -> None:
    """All commands should complete without requiring user input."""
    runner = CliRunner()

    # Test main help
    result = runner.invoke(main, ["--help"], input=None)
    assert result.exit_code == 0

    # Test config command (with isolated filesystem)
    with runner.isolated_filesystem():
        import os

        os.makedirs(".resume", exist_ok=True)
        with open(".resume/config.yaml", "w") as f:
            f.write("work_units_dir: work-units\noutput_dir: output\n")
        result = runner.invoke(main, ["config"], input=None)
        assert result.exit_code == 0

    # Test test-output command
    result = runner.invoke(main, ["test-output"], input=None)
    assert result.exit_code == 0

    # Test test-errors command (expected to fail with exit code, not hang)
    result = runner.invoke(main, ["test-errors", "--type", "user"], input=None)
    assert result.exit_code == 1  # UserError exit code


def test_json_mode_no_prompts() -> None:
    """JSON mode commands should complete without prompts."""
    runner = CliRunner()

    # Test config in JSON mode
    with runner.isolated_filesystem():
        import os

        os.makedirs(".resume", exist_ok=True)
        with open(".resume/config.yaml", "w") as f:
            f.write("work_units_dir: work-units\noutput_dir: output\n")
        result = runner.invoke(main, ["--json", "config"], input=None)
        assert result.exit_code == 0

    # Test test-output in JSON mode
    result = runner.invoke(main, ["--json", "test-output"], input=None)
    assert result.exit_code == 0


def test_quiet_mode_no_prompts() -> None:
    """Quiet mode commands should complete without prompts."""
    runner = CliRunner()

    # Test config in quiet mode
    with runner.isolated_filesystem():
        import os

        os.makedirs(".resume", exist_ok=True)
        with open(".resume/config.yaml", "w") as f:
            f.write("work_units_dir: work-units\noutput_dir: output\n")
        result = runner.invoke(main, ["--quiet", "config"], input=None)
        assert result.exit_code == 0
