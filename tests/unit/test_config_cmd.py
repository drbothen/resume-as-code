"""Tests for config command."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from resume_as_code.cli import main
from resume_as_code.config import reset_config


class TestConfigCommand:
    """Test the config command."""

    def test_config_command_exists(self, cli_runner: CliRunner) -> None:
        """Config command should be registered."""
        result = cli_runner.invoke(main, ["config", "--help"])
        assert result.exit_code == 0
        assert "configuration" in result.output.lower()

    def test_config_command_shows_settings(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Config command should display configuration settings."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config"])
            assert result.exit_code == 0
            # Should show key configuration fields
            assert "output_dir" in result.output
            assert "default_format" in result.output

    def test_config_command_shows_sources(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Config command should show source of each value."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config"])
            assert result.exit_code == 0
            assert "default" in result.output.lower()

    def test_config_command_json_mode(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Config command should output JSON when --json flag is used."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["--json", "config"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["status"] == "success"
            assert data["command"] == "config"
            assert "config" in data["data"]
            assert "sources" in data["data"]

    def test_config_command_quiet_mode(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Config command should produce no output in quiet mode."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["--quiet", "config"])
            assert result.exit_code == 0
            assert result.output == ""

    def test_config_shows_project_config_source(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Config command should show project config source when present."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create a project config file
            project_config = Path(".resume.yaml")
            project_config.write_text("output_dir: ./custom-dist\n")

            result = cli_runner.invoke(main, ["config"])
            assert result.exit_code == 0
            assert "project" in result.output.lower()


class TestConfigSetValue:
    """Tests for config set functionality (AC: #4)."""

    def test_config_set_value_creates_project_config(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """resume config <key> <value> should create/update project config (AC: #4)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "output_dir", "./custom"])

            assert result.exit_code == 0
            # Verify config file was created
            config_file = Path(".resume.yaml")
            assert config_file.exists()
            content = config_file.read_text()
            assert "output_dir" in content
            assert "custom" in content

    def test_config_set_value_updates_existing_config(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """resume config <key> <value> should update existing config value."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create initial config
            config_file = Path(".resume.yaml")
            config_file.write_text("output_dir: ./old-value\ndefault_format: pdf\n")

            result = cli_runner.invoke(main, ["config", "output_dir", "./new-value"])

            assert result.exit_code == 0
            content = config_file.read_text()
            assert "new-value" in content
            # Should preserve other values
            assert "default_format" in content

    def test_config_set_shows_confirmation(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """resume config <key> <value> should show confirmation message."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "output_dir", "./custom"])

            assert result.exit_code == 0
            # Should indicate the value was set
            assert "output_dir" in result.output.lower() or "set" in result.output.lower()


class TestConfigListFlag:
    """Tests for config --list flag (AC: #5)."""

    def test_config_list_shows_all_values(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """resume config --list should show all config values with sources (AC: #5)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "--list"])

            assert result.exit_code == 0
            # Should show config values
            assert "output_dir" in result.output
            assert "default_format" in result.output
            # Should show sources
            assert "default" in result.output.lower()

    def test_config_list_shows_project_sources(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """resume config --list should show project config source."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create project config
            config_file = Path(".resume.yaml")
            config_file.write_text("output_dir: ./resumes\n")

            result = cli_runner.invoke(main, ["config", "--list"])

            assert result.exit_code == 0
            assert "project" in result.output.lower()
