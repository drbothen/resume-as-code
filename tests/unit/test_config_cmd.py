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
