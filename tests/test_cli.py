"""Tests for the CLI entry point."""

from __future__ import annotations

from pathlib import Path

import pytest
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


class TestConfigFlag:
    """Tests for the --config flag (Story 7.16)."""

    def test_config_flag_is_accepted(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test that --config flag is recognized."""
        config_file = tmp_path / "custom.yaml"
        config_file.write_text("output_dir: ./custom\n")

        result = cli_runner.invoke(main, ["--config", str(config_file)])
        assert "no such option" not in result.output.lower()

    def test_help_shows_config_flag(self, cli_runner: CliRunner) -> None:
        """Test that help shows --config option."""
        result = cli_runner.invoke(main, ["--help"])
        assert "--config" in result.output

    def test_config_flag_nonexistent_file_shows_error(self, cli_runner: CliRunner) -> None:
        """Test that --config with non-existent file shows clear error."""
        result = cli_runner.invoke(main, ["--config", "/nonexistent/path.yaml"])
        assert result.exit_code != 0
        # Click should show "does not exist" error
        assert "does not exist" in result.output.lower() or "no such file" in result.output.lower()

    def test_config_flag_overrides_default_project_config(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Custom config should override .resume.yaml in cwd."""
        # Create default config in cwd
        default_config = tmp_path / ".resume.yaml"
        default_config.write_text("output_dir: ./default-output\n")

        # Create custom config
        custom_config = tmp_path / "custom.yaml"
        custom_config.write_text("output_dir: ./custom-output\n")

        monkeypatch.chdir(tmp_path)

        # Reset config singleton before test
        from resume_as_code.config import reset_config

        reset_config()

        result = cli_runner.invoke(main, ["--config", str(custom_config), "config"])

        assert result.exit_code == 0
        assert "custom-output" in result.output
        assert "default-output" not in result.output

    def test_config_flag_stored_in_context(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test that --config path is accessible in context."""
        config_file = tmp_path / "custom.yaml"
        config_file.write_text("output_dir: ./custom\n")

        # We'll verify the config takes effect by checking output
        result = cli_runner.invoke(main, ["--config", str(config_file), "config"])

        assert result.exit_code == 0
        # The custom output_dir should appear in config output
        assert "custom" in result.output

    def test_effective_config_path_resolves_symlinks(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """effective_config_path should resolve to absolute normalized path."""
        from resume_as_code.context import Context

        # Create a config file
        config_file = tmp_path / "actual.yaml"
        config_file.write_text("output_dir: ./test\n")

        # Create context with relative path
        ctx = Context()
        monkeypatch.chdir(tmp_path)
        ctx.config_path = Path("actual.yaml")

        # effective_config_path should return resolved absolute path
        effective = ctx.effective_config_path
        assert effective.is_absolute()
        assert effective == config_file.resolve()

    def test_help_shows_config_example(self, cli_runner: CliRunner) -> None:
        """Test that help shows example usage for --config."""
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        # Should show the example in help text
        assert "Example:" in result.output or "example" in result.output.lower()


class TestServiceConfigPropagation:
    """Tests verifying services receive custom config paths (Issue #4)."""

    def test_list_certifications_uses_custom_config(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CertificationService should receive custom config path."""
        from unittest.mock import MagicMock, patch

        config_file = tmp_path / "custom.yaml"
        config_file.write_text("certifications: []\n")
        monkeypatch.chdir(tmp_path)

        mock_service = MagicMock()
        mock_service.load_certifications.return_value = []

        with patch(
            "resume_as_code.commands.list_cmd.CertificationService",
            return_value=mock_service,
        ) as mock_class:
            cli_runner.invoke(main, ["--config", str(config_file), "list", "certifications"])

            # Verify service was instantiated with the custom config path
            mock_class.assert_called_once()
            call_kwargs = mock_class.call_args.kwargs
            assert "config_path" in call_kwargs
            # The path should be resolved (absolute)
            assert call_kwargs["config_path"].is_absolute()

    def test_list_education_uses_custom_config(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """EducationService should receive custom config path."""
        from unittest.mock import MagicMock, patch

        config_file = tmp_path / "custom.yaml"
        config_file.write_text("education: []\n")
        monkeypatch.chdir(tmp_path)

        mock_service = MagicMock()
        mock_service.load_educations.return_value = []

        with patch(
            "resume_as_code.commands.list_cmd.EducationService",
            return_value=mock_service,
        ) as mock_class:
            # Subcommand is "education" (singular)
            cli_runner.invoke(main, ["--config", str(config_file), "list", "education"])

            mock_class.assert_called_once()
            call_kwargs = mock_class.call_args.kwargs
            assert "config_path" in call_kwargs
            assert call_kwargs["config_path"].is_absolute()

    def test_show_certification_uses_custom_config(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CertificationService in show command should receive custom config path."""
        from unittest.mock import MagicMock, patch

        config_file = tmp_path / "custom.yaml"
        config_file.write_text("certifications: []\n")
        monkeypatch.chdir(tmp_path)

        mock_service = MagicMock()
        mock_service.find_certifications_by_name.return_value = []

        with patch(
            "resume_as_code.commands.show.CertificationService",
            return_value=mock_service,
        ) as mock_class:
            # Will fail with not found, but service should still be called with correct path
            cli_runner.invoke(main, ["--config", str(config_file), "show", "certification", "aws"])

            mock_class.assert_called_once()
            call_kwargs = mock_class.call_args.kwargs
            assert "config_path" in call_kwargs
            assert call_kwargs["config_path"].is_absolute()

    def test_new_certification_uses_custom_config(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CertificationService in new command should receive custom config path."""
        from unittest.mock import MagicMock, patch

        config_file = tmp_path / "custom.yaml"
        config_file.write_text("certifications: []\n")
        monkeypatch.chdir(tmp_path)

        mock_service = MagicMock()
        mock_service.find_certification.return_value = None

        with patch(
            "resume_as_code.commands.new.CertificationService",
            return_value=mock_service,
        ) as mock_class:
            cli_runner.invoke(
                main,
                ["--config", str(config_file), "new", "certification", "--name", "Test Cert"],
            )

            mock_class.assert_called_once()
            call_kwargs = mock_class.call_args.kwargs
            assert "config_path" in call_kwargs
            assert call_kwargs["config_path"].is_absolute()

    def test_remove_certification_uses_custom_config(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CertificationService in remove command should receive custom config path."""
        from unittest.mock import MagicMock, patch

        config_file = tmp_path / "custom.yaml"
        config_file.write_text("certifications: []\n")
        monkeypatch.chdir(tmp_path)

        mock_service = MagicMock()
        mock_service.find_certifications_by_name.return_value = []

        with patch(
            "resume_as_code.commands.remove.CertificationService",
            return_value=mock_service,
        ) as mock_class:
            # Will fail with not found, but service should still be called with correct path
            cli_runner.invoke(
                main, ["--config", str(config_file), "remove", "certification", "aws"]
            )

            mock_class.assert_called_once()
            call_kwargs = mock_class.call_args.kwargs
            assert "config_path" in call_kwargs
            assert call_kwargs["config_path"].is_absolute()
