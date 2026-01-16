"""Tests for config command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
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

    def test_config_set_shows_confirmation(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """resume config <key> <value> should show confirmation message."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "output_dir", "./custom"])

            assert result.exit_code == 0
            # Should indicate the value was set
            assert "output_dir" in result.output.lower() or "set" in result.output.lower()


class TestConfigNestedAccess:
    """Tests for nested config access (profile keys)."""

    def test_config_get_profile_name(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """resume config profile.name should get profile name value."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create config with profile
            config_file = Path(".resume.yaml")
            config_file.write_text(
                """
profile:
  name: "Test User"
  email: "test@example.com"
"""
            )
            result = cli_runner.invoke(main, ["config", "profile.name"])

            assert result.exit_code == 0
            assert "Test User" in result.output

    def test_config_set_profile_name(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """resume config profile.name 'Jane Doe' should set profile name."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "profile.name", "Jane Doe"])

            assert result.exit_code == 0
            # Verify config file was created with nested structure
            config_file = Path(".resume.yaml")
            assert config_file.exists()
            content = config_file.read_text()
            assert "profile" in content
            assert "name" in content
            assert "Jane Doe" in content

    def test_config_get_profile_json(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """resume config --json profile should return profile as JSON."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create config with profile
            config_file = Path(".resume.yaml")
            config_file.write_text(
                """
profile:
  name: "Test User"
  email: "test@example.com"
"""
            )
            result = cli_runner.invoke(main, ["--json", "config", "profile"])

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["status"] == "success"
            assert data["data"]["key"] == "profile"
            assert data["data"]["value"]["name"] == "Test User"
            assert data["data"]["value"]["email"] == "test@example.com"


class TestConfigListFlag:
    """Tests for config --list flag (AC: #5)."""

    def test_config_list_shows_all_values(self, cli_runner: CliRunner, tmp_path: Path) -> None:
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

    def test_config_list_shows_project_sources(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """resume config --list should show project config source."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create project config
            config_file = Path(".resume.yaml")
            config_file.write_text("output_dir: ./resumes\n")

            result = cli_runner.invoke(main, ["config", "--list"])

            assert result.exit_code == 0
            assert "project" in result.output.lower()


class TestConfigCertifications:
    """Tests for resume config certifications --list (Story 6.2, AC #6)."""

    def test_certifications_list_empty(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """When no certifications configured, shows helpful message."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "certifications", "--list"])

            assert result.exit_code == 0
            assert "No certifications configured" in result.output
            assert "certifications:" in result.output

    def test_certifications_list_with_certs(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """When certifications exist, shows table with status."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            config_file = Path(".resume.yaml")
            config_file.write_text(
                "certifications:\n"
                '  - name: "AWS Solutions Architect"\n'
                '    issuer: "Amazon Web Services"\n'
                '    date: "2024-06"\n'
                '  - name: "CISSP"\n'
                '    issuer: "ISC2"\n'
                '    expires: "2099-01"\n'
            )

            result = cli_runner.invoke(main, ["config", "certifications", "--list"])

            assert result.exit_code == 0
            assert "AWS Solutions Architect" in result.output
            assert "Amazon Web Services" in result.output
            assert "CISSP" in result.output
            assert "active" in result.output

    def test_certifications_list_shows_expired_status(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Expired certifications show 'expired' status."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            config_file = Path(".resume.yaml")
            config_file.write_text(
                'certifications:\n  - name: "Old Cert"\n    expires: "2020-01"\n'
            )

            result = cli_runner.invoke(main, ["config", "certifications", "--list"])

            assert result.exit_code == 0
            assert "expired" in result.output

    def test_certifications_list_json_mode(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """JSON mode outputs certifications with status."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            config_file = Path(".resume.yaml")
            config_file.write_text('certifications:\n  - name: "AWS Cert"\n    issuer: "AWS"\n')

            result = cli_runner.invoke(main, ["--json", "config", "certifications", "--list"])

            assert result.exit_code == 0
            import json

            data = json.loads(result.output)
            assert data["status"] == "success"
            assert "certifications" in data["data"]
            assert data["data"]["certifications"][0]["name"] == "AWS Cert"
            assert "status" in data["data"]["certifications"][0]


class TestConfigONetStatus:
    """Tests for resume config --show-onet-status (Story 7.5, AC #6)."""

    def test_onet_status_flag_exists(self, cli_runner: CliRunner) -> None:
        """--show-onet-status flag should be available."""
        result = cli_runner.invoke(main, ["config", "--help"])
        assert result.exit_code == 0
        assert "--show-onet-status" in result.output

    def test_onet_status_not_configured(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """When O*NET not configured, shows helpful message."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config", "--show-onet-status"])

            assert result.exit_code == 0
            assert "not configured" in result.output.lower()

    def test_onet_status_shows_masked_key(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When API key configured, shows masked version."""
        reset_config()
        monkeypatch.setenv("ONET_API_KEY", "my-secret-api-key-12345")
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            config_file = Path(".resume.yaml")
            config_file.write_text("onet:\n  enabled: true\n")

            result = cli_runner.invoke(main, ["config", "--show-onet-status"])

            assert result.exit_code == 0
            # Should show masked key (e.g., "my-s***45")
            assert "***" in result.output
            # Should NOT show full key
            assert "my-secret-api-key-12345" not in result.output

    def test_onet_status_shows_cache_stats(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Shows cache statistics (entries, size)."""
        reset_config()
        monkeypatch.setenv("ONET_API_KEY", "test-key")
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            config_file = Path(".resume.yaml")
            config_file.write_text("onet:\n  enabled: true\n")

            result = cli_runner.invoke(main, ["config", "--show-onet-status"])

            assert result.exit_code == 0
            # Should show cache information
            assert "cache" in result.output.lower()

    def test_onet_status_shows_enabled_state(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Shows whether O*NET integration is enabled/disabled."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            config_file = Path(".resume.yaml")
            config_file.write_text("onet:\n  enabled: false\n")

            result = cli_runner.invoke(main, ["config", "--show-onet-status"])

            assert result.exit_code == 0
            assert "disabled" in result.output.lower()

    def test_onet_status_json_mode(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JSON mode outputs O*NET status as structured data."""
        reset_config()
        monkeypatch.setenv("ONET_API_KEY", "test-key-abc123")
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            config_file = Path(".resume.yaml")
            config_file.write_text("onet:\n  enabled: true\n")

            result = cli_runner.invoke(main, ["--json", "config", "--show-onet-status"])

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["status"] == "success"
            assert "onet" in data["data"]
            assert data["data"]["onet"]["enabled"] is True
            assert data["data"]["onet"]["configured"] is True
            # Key should be masked in JSON too
            assert "test-key-abc123" not in result.output
            assert "cache" in data["data"]["onet"]

    def test_onet_status_quiet_mode(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Quiet mode produces no output."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["--quiet", "config", "--show-onet-status"])

            assert result.exit_code == 0
            assert result.output == ""
