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


class TestMigrateCommand:
    """Integration tests for the migrate command (Story 9.1)."""

    def test_migrate_help_shows_output(self, cli_runner: CliRunner) -> None:
        """Test that migrate --help shows help output."""
        result = cli_runner.invoke(main, ["migrate", "--help"])
        assert result.exit_code == 0
        assert "migrate" in result.output.lower()
        assert "--status" in result.output
        assert "--dry-run" in result.output
        assert "--rollback" in result.output

    def test_migrate_status_up_to_date(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that migrate --status shows up-to-date when schema is current."""
        # Create config with current schema version
        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 4.0.0\noutput_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["migrate", "--status"])

        assert result.exit_code == 0
        assert "4.0.0" in result.output
        assert "Up to date" in result.output or "up to date" in result.output.lower()

    def test_migrate_status_needs_migration(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that migrate --status shows migration available for legacy config."""
        # Create legacy config (no schema_version)
        config = tmp_path / ".resume.yaml"
        config.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["migrate", "--status"])

        assert result.exit_code == 0
        assert "1.0.0" in result.output  # Detected as legacy
        assert "4.0.0" in result.output  # Target version (latest)
        assert "migration" in result.output.lower()

    def test_migrate_dry_run_shows_preview(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that migrate --dry-run previews changes without modifying files."""
        # Create legacy config
        config = tmp_path / ".resume.yaml"
        original_content = "output_dir: ./dist\n"
        config.write_text(original_content)
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["migrate", "--dry-run"])

        assert result.exit_code == 0
        assert "schema_version" in result.output.lower()
        assert "Would apply" in result.output or "would" in result.output.lower()
        # File should NOT be modified
        assert config.read_text() == original_content

    def test_migrate_already_current(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that migrate on current schema shows success."""
        # Create config with current schema version
        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 4.0.0\noutput_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["migrate"])

        assert result.exit_code == 0
        assert "current" in result.output.lower() or "4.0.0" in result.output

    def test_migrate_applies_migration(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that migrate applies migration when confirmed."""
        # Create legacy config
        config = tmp_path / ".resume.yaml"
        config.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)

        # Confirm the migration
        result = cli_runner.invoke(main, ["migrate"], input="y\n")

        assert result.exit_code == 0
        # Check that migration was applied (v1->v2->v3->v4)
        content = config.read_text()
        assert "schema_version: 4.0.0" in content
        assert "output_dir" in content

    def test_migrate_creates_backup(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that migrate creates backup before applying."""
        import re

        # Create legacy config
        config = tmp_path / ".resume.yaml"
        config.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)

        # Confirm the migration
        result = cli_runner.invoke(main, ["migrate"], input="y\n")

        assert result.exit_code == 0
        # Check for backup directory
        backup_dirs = [d for d in tmp_path.iterdir() if re.match(r"\.resume-backup-\d{4}", d.name)]
        assert len(backup_dirs) == 1
        backup_dir = backup_dirs[0]
        assert (backup_dir / ".resume.yaml").exists()

    def test_migrate_cancelled_when_declined(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that migrate is cancelled when user declines."""
        # Create legacy config
        config = tmp_path / ".resume.yaml"
        original_content = "output_dir: ./dist\n"
        config.write_text(original_content)
        monkeypatch.chdir(tmp_path)

        # Decline the migration
        result = cli_runner.invoke(main, ["migrate"], input="n\n")

        assert result.exit_code == 0
        assert "cancelled" in result.output.lower()
        # File should NOT be modified
        assert config.read_text() == original_content

    def test_migrate_quiet_mode_skips_confirmation(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that migrate with --quiet applies without confirmation."""
        # Create legacy config
        config = tmp_path / ".resume.yaml"
        config.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["--quiet", "migrate"])

        assert result.exit_code == 0
        # Migration should be applied (v1->v2->v3->v4)
        content = config.read_text()
        assert "schema_version: 4.0.0" in content

    def test_migrate_rollback_restores_files(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that migrate --rollback restores from backup."""
        import re

        # Create legacy config and apply migration
        config = tmp_path / ".resume.yaml"
        original_content = "output_dir: ./original\n"
        config.write_text(original_content)
        monkeypatch.chdir(tmp_path)

        # First, apply migration (creates backup)
        cli_runner.invoke(main, ["--quiet", "migrate"])

        # Find backup directory
        backup_dirs = [d for d in tmp_path.iterdir() if re.match(r"\.resume-backup-\d{4}", d.name)]
        assert len(backup_dirs) == 1
        backup_dir = backup_dirs[0]

        # Now rollback
        result = cli_runner.invoke(main, ["migrate", "--rollback", str(backup_dir)], input="y\n")

        assert result.exit_code == 0
        assert "Rollback complete" in result.output or "Restored" in result.output
        # Original content should be restored
        assert config.read_text() == original_content

    def test_migrate_no_config_file(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test migrate in directory with no config file."""
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["migrate", "--status"])

        assert result.exit_code == 0
        # Should detect as legacy version
        assert "1.0.0" in result.output

    def test_migrate_preserves_comments(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that migrate preserves YAML comments."""
        # Create legacy config with comments
        config = tmp_path / ".resume.yaml"
        config.write_text(
            """# My resume configuration
output_dir: ./dist  # Output directory
default_format: pdf
"""
        )
        monkeypatch.chdir(tmp_path)

        # Apply migration
        cli_runner.invoke(main, ["--quiet", "migrate"])

        content = config.read_text()
        # Comments should be preserved
        assert "# My resume configuration" in content
        assert "# Output directory" in content
        assert "schema_version: 4.0.0" in content

    def test_migrate_failure_preserves_backup(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that migration failure preserves backup for manual rollback.

        AC #5: When a migration step fails, the backup is preserved and
        the user is informed how to rollback using --rollback flag.

        Note: Rollback is MANUAL (not automatic) by design - this allows
        users to inspect changes before deciding to rollback.
        """
        from unittest.mock import patch

        from resume_as_code.migrations.base import MigrationResult

        # Create legacy config
        config = tmp_path / ".resume.yaml"
        original_content = "output_dir: ./dist\n"
        config.write_text(original_content)
        monkeypatch.chdir(tmp_path)

        # Mock the migration's apply method to return failure
        def mock_apply(self, ctx):  # noqa: ARG001
            return MigrationResult(success=False, errors=["Simulated migration failure"])

        with patch(
            "resume_as_code.migrations.v1_to_v2.MigrationV1ToV2.apply",
            mock_apply,
        ):
            result = cli_runner.invoke(main, ["--quiet", "migrate"])

        # Should exit with error
        assert result.exit_code == 1

        # Backup should be created
        backup_dirs = list(tmp_path.glob(".resume-backup-*"))
        assert len(backup_dirs) == 1
        backup_dir = backup_dirs[0]

        # Backup should contain the original config
        backup_config = backup_dir / ".resume.yaml"
        assert backup_config.exists()
        assert backup_config.read_text() == original_content

        # User can manually rollback using the backup
        result = cli_runner.invoke(main, ["--quiet", "migrate", "--rollback", str(backup_dir)])
        assert result.exit_code == 0
        # Original content should be restored
        assert config.read_text() == original_content


class TestInferArchetypesCommand:
    """Integration tests for the infer-archetypes command (Story 12.3)."""

    def test_infer_archetypes_help_shows_output(self, cli_runner: CliRunner) -> None:
        """Test that infer-archetypes --help shows help output."""
        result = cli_runner.invoke(main, ["infer-archetypes", "--help"])
        assert result.exit_code == 0
        assert "infer" in result.output.lower()
        assert "--apply" in result.output
        assert "--min-confidence" in result.output
        assert "--include-assigned" in result.output

    def test_infer_archetypes_no_work_units_dir(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that infer-archetypes handles missing work-units directory."""
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["infer-archetypes"])

        assert result.exit_code == 0
        assert "No work-units directory found" in result.output

    def test_infer_archetypes_json_no_work_units(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test JSON output when no work-units directory."""
        import json

        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["--json", "infer-archetypes"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["command"] == "infer-archetypes"
        assert data["data"]["total"] == 0

    def test_infer_archetypes_dry_run_default(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that infer-archetypes is dry-run by default (AC5)."""
        # Create work-units directory with a test file
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        work_unit_content = """id: wu-2024-01-01-test-incident
title: Resolved P1 database outage affecting production
problem:
  statement: Production database failed unexpectedly
actions:
  - Detected via monitoring alerts
  - Triaged and escalated
  - Mitigated impact
outcome:
  result: Restored service in 45 minutes
tags:
  - incident-response
"""
        (work_units_dir / "test.yaml").write_text(work_unit_content)
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["infer-archetypes"])

        assert result.exit_code == 0
        assert "incident" in result.output.lower()
        assert "suggested" in result.output.lower()
        # Verify file was NOT modified (dry-run)
        content = (work_units_dir / "test.yaml").read_text()
        assert "archetype:" not in content

    def test_infer_archetypes_apply_updates_files(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that --apply updates work unit files (AC4)."""
        # Create work-units directory with a test file
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        work_unit_content = """id: wu-2024-01-01-test-incident
title: Resolved P1 database outage affecting production
problem:
  statement: Production database failed unexpectedly
actions:
  - Detected via monitoring alerts
  - Triaged and escalated
  - Mitigated the incident
outcome:
  result: Restored service in 45 minutes
tags:
  - incident-response
"""
        (work_units_dir / "test.yaml").write_text(work_unit_content)
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["infer-archetypes", "--apply"])

        assert result.exit_code == 0
        assert "APPLIED" in result.output
        # Verify file was modified
        content = (work_units_dir / "test.yaml").read_text()
        assert "archetype: incident" in content

    def test_infer_archetypes_skips_assigned(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that work units with archetypes are skipped by default."""
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        # Work unit with archetype already assigned
        work_unit_content = """id: wu-2024-01-01-test
title: Some work unit with archetype
archetype: greenfield
problem:
  statement: Some problem statement here
actions:
  - Did some action
outcome:
  result: Got some result
tags: []
"""
        (work_units_dir / "test.yaml").write_text(work_unit_content)
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["infer-archetypes"])

        assert result.exit_code == 0
        assert "No work units to analyze" in result.output

    def test_infer_archetypes_include_assigned(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that --include-assigned re-infers existing archetypes."""
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        work_unit_content = """id: wu-2024-01-01-test
title: Built new system from scratch, architected
archetype: minimal
problem:
  statement: No analytics capability existed in organization
actions:
  - Designed architecture from the ground up
  - Built data pipeline system
outcome:
  result: Launched new analytics platform
tags:
  - greenfield
"""
        (work_units_dir / "test.yaml").write_text(work_unit_content)
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["infer-archetypes", "--include-assigned"])

        assert result.exit_code == 0
        # Should show suggestions even though archetype exists
        assert "greenfield" in result.output.lower() or "test.yaml" in result.output

    def test_infer_archetypes_json_output(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test JSON output format for infer-archetypes."""
        import json

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        work_unit_content = """id: wu-2024-01-01-test
title: Migrated legacy database to cloud platform
problem:
  statement: Legacy system was unmaintainable
actions:
  - Transitioned database
  - Upgraded platform
outcome:
  result: Completed cloud migration
tags:
  - migration
"""
        (work_units_dir / "test.yaml").write_text(work_unit_content)
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["--json", "infer-archetypes"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["command"] == "infer-archetypes"
        assert data["data"]["total"] == 1
        assert len(data["data"]["results"]) == 1
        assert "inferred" in data["data"]["results"][0]
        assert "confidence" in data["data"]["results"][0]

    def test_infer_archetypes_quiet_mode(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that --quiet suppresses output."""
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        work_unit_content = """id: wu-2024-01-01-test
title: Some test work unit
problem:
  statement: Some problem to solve
actions:
  - Did something
outcome:
  result: Got result
tags: []
"""
        (work_units_dir / "test.yaml").write_text(work_unit_content)
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["--quiet", "infer-archetypes"])

        assert result.exit_code == 0
        assert result.output.strip() == ""

    def test_infer_archetypes_custom_threshold(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that --min-confidence threshold affects results."""
        import json
        from unittest.mock import patch

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        # Ambiguous work unit that won't hit 0.5 threshold
        work_unit_content = """id: wu-2024-01-01-test
title: Did some work on project
problem:
  statement: There was a problem to address
actions:
  - Fixed it
outcome:
  result: It worked
tags: []
"""
        (work_units_dir / "test.yaml").write_text(work_unit_content)
        monkeypatch.chdir(tmp_path)

        # Mock embedding service to return low similarity scores
        # This ensures semantic fallback doesn't exceed thresholds
        with patch(
            "resume_as_code.services.embedder.EmbeddingService.similarity",
            return_value=0.1,
        ):
            # With high threshold, should return minimal (low regex + low semantic)
            result = cli_runner.invoke(
                main, ["--json", "infer-archetypes", "--min-confidence", "0.8"]
            )
            data = json.loads(result.output)
            assert data["data"]["results"][0]["inferred"] == "minimal"

            # With low threshold, may return specific archetype
            result_low = cli_runner.invoke(
                main, ["--json", "infer-archetypes", "--min-confidence", "0.1"]
            )
            data_low = json.loads(result_low.output)
            # Either minimal or specific archetype depending on content
            assert data_low["data"]["results"][0]["inferred"] in [
                "minimal",
                "greenfield",
                "migration",
                "optimization",
                "incident",
                "leadership",
                "strategic",
                "transformation",
                "cultural",
            ]

    def test_infer_archetypes_apply_skips_low_confidence(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that --apply does NOT update files when confidence is below threshold."""
        import json
        from unittest.mock import patch

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        # Ambiguous content that should have LOW confidence
        work_unit_content = """id: wu-2024-01-01-ambiguous
title: "Did some general work on the project"
schema_version: "4.0.0"
problem:
  statement: "There was something to do"
actions:
  - "Worked on it"
outcome:
  result: "It was completed"
tags: []
"""
        (work_units_dir / "test.yaml").write_text(work_unit_content)
        monkeypatch.chdir(tmp_path)

        # Mock embedding service to return low similarity scores
        # This ensures semantic fallback doesn't exceed thresholds
        with patch(
            "resume_as_code.services.embedder.EmbeddingService.similarity",
            return_value=0.1,
        ):
            # Apply with high threshold - should NOT modify file
            result = cli_runner.invoke(
                main, ["--json", "infer-archetypes", "--apply", "--min-confidence", "0.9"]
            )

            assert result.exit_code == 0
            data = json.loads(result.output)

            # Verify inferred archetype is minimal (low confidence)
            assert data["data"]["results"][0]["inferred"] == "minimal"
            # Verify it was NOT applied (confidence below threshold)
            assert data["data"]["results"][0]["applied"] is False

            # Verify the file was NOT modified
            content = (work_units_dir / "test.yaml").read_text()
            assert "archetype:" not in content
