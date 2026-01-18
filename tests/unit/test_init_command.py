"""Tests for init command (Story 7.21)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from resume_as_code.cli import main
from resume_as_code.commands.init import _is_valid_url
from resume_as_code.config import reset_config


class TestUrlValidation:
    """Test URL validation helper function."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com",
            "http://example.com",
            "https://linkedin.com/in/john-doe",
            "https://github.com/username",
            "https://john.dev",
            "https://sub.domain.example.com",
            "http://localhost:8080",
            "https://192.168.1.1",
            "https://example.com/path?query=value",
        ],
    )
    def test_valid_urls(self, url: str) -> None:
        """Valid URLs should pass validation."""
        assert _is_valid_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "not-a-url",
            "example.com",
            "ftp://example.com",
            "john.dev",
            "linkedin.com/in/john",
            "",
            "just some text",
            "http://",
            "https://",
        ],
    )
    def test_invalid_urls(self, url: str) -> None:
        """Invalid URLs should fail validation."""
        assert _is_valid_url(url) is False


class TestInitCommand:
    """Test the init command structure (Task 1)."""

    def test_init_command_exists(self, cli_runner: CliRunner) -> None:
        """Init command should be registered (AC #1)."""
        result = cli_runner.invoke(main, ["init", "--help"])
        assert result.exit_code == 0
        assert "init" in result.output.lower()

    def test_init_creates_expected_files(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """init --non-interactive creates .resume.yaml, work-units/, positions.yaml (AC #1)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["init", "--non-interactive"])

            assert result.exit_code == 0
            assert Path(".resume.yaml").exists()
            assert Path("work-units").is_dir()
            assert Path("work-units/.gitkeep").exists()
            assert Path("positions.yaml").exists()

    def test_init_fails_when_config_exists(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """init fails if .resume.yaml already exists (AC #4)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".resume.yaml").write_text("existing: config")

            result = cli_runner.invoke(main, ["init"])

            assert result.exit_code == 1
            assert "already exists" in result.output

    def test_init_suggests_force_flag(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """init suggests --force when config exists (AC #4)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".resume.yaml").write_text("existing: config")

            result = cli_runner.invoke(main, ["init"])

            assert result.exit_code == 1
            assert "--force" in result.output

    def test_init_force_creates_backup(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """--force backs up existing config (AC #5)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".resume.yaml").write_text("existing: config")

            result = cli_runner.invoke(main, ["init", "--force", "--non-interactive"])

            assert result.exit_code == 0
            assert Path(".resume.yaml.bak").exists()
            assert Path(".resume.yaml.bak").read_text() == "existing: config"

    def test_init_force_shows_backup_location(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """--force shows info about backup location (AC #5)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".resume.yaml").write_text("existing: config")

            result = cli_runner.invoke(main, ["init", "--force", "--non-interactive"])

            assert result.exit_code == 0
            assert ".resume.yaml.bak" in result.output

    def test_init_non_interactive_uses_placeholders(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """--non-interactive creates profile.yaml with TODO placeholders (Story 9.2)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["init", "--non-interactive"])

            assert result.exit_code == 0
            # Story 9.2: Profile data is now in profile.yaml
            content = Path("profile.yaml").read_text()
            assert "TODO:" in content

    def test_init_displays_created_files(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """init shows what was created (AC #6)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["init", "--non-interactive"])

            assert result.exit_code == 0
            assert ".resume.yaml" in result.output
            assert "work-units" in result.output
            assert "positions.yaml" in result.output

    def test_init_displays_next_steps(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """init shows next steps after success (AC #6)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["init", "--non-interactive"])

            assert result.exit_code == 0
            assert "resume new position" in result.output
            assert "resume new work-unit" in result.output

    def test_init_positions_yaml_is_empty_list(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """positions.yaml contains empty list."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["init", "--non-interactive"])

            assert result.exit_code == 0
            content = Path("positions.yaml").read_text()
            assert content.strip() == "[]"


class TestInitInteractive:
    """Test interactive mode (Task 1.3)."""

    def test_init_prompts_for_name(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Interactive mode prompts for required name (AC #2, Story 9.2)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["init"], input="John Doe\n\n\n\n\n\n\n")

            assert result.exit_code == 0
            # Story 9.2: Profile data is now in profile.yaml
            content = Path("profile.yaml").read_text()
            assert "John Doe" in content

    def test_init_validates_linkedin_url(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """LinkedIn URL is validated (AC #2, Story 9.2)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Invalid URL first, then valid
            result = cli_runner.invoke(
                main,
                ["init"],
                input="John Doe\n\n\n\nnot-a-url\nhttps://linkedin.com/in/john\n\n\n",
            )

            assert result.exit_code == 0
            assert "Invalid URL" in result.output
            # Story 9.2: Profile data is now in profile.yaml
            content = Path("profile.yaml").read_text()
            assert "https://linkedin.com/in/john" in content

    def test_init_validates_github_url(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """GitHub URL is validated (AC #2, Story 9.2)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Invalid URL first, then valid
            result = cli_runner.invoke(
                main,
                ["init"],
                input="John Doe\n\n\n\n\nbad-github\nhttps://github.com/john\n\n",
            )

            assert result.exit_code == 0
            assert "Invalid URL" in result.output
            # Story 9.2: Profile data is now in profile.yaml
            content = Path("profile.yaml").read_text()
            assert "https://github.com/john" in content

    def test_init_validates_website_url(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Website URL is validated (AC #2, Story 9.2)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Invalid URL first, then valid
            result = cli_runner.invoke(
                main,
                ["init"],
                input="John Doe\n\n\n\n\n\njohn.dev\nhttps://john.dev\n",
            )

            assert result.exit_code == 0
            assert "Invalid URL" in result.output
            # Story 9.2: Profile data is now in profile.yaml
            content = Path("profile.yaml").read_text()
            assert "https://john.dev" in content

    def test_init_allows_empty_url_fields(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Empty URL fields are allowed (optional fields)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["init"], input="John Doe\n\n\n\n\n\n\n")

            assert result.exit_code == 0
            # Should complete without errors
            assert "Invalid URL" not in result.output

    def test_init_requires_name(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Empty name reprompts (AC #2)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # First empty, then valid name
            result = cli_runner.invoke(main, ["init"], input="\nJohn Doe\n\n\n\n\n\n\n")

            assert result.exit_code == 0
            assert "required" in result.output.lower()

    def test_init_saves_all_profile_fields(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """All profile fields are saved to profile.yaml (Story 9.2)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(
                main,
                ["init"],
                input="John Doe\njohn@example.com\n555-1234\nSF, CA\nhttps://linkedin.com/in/john\nhttps://github.com/john\nhttps://john.dev\n",
            )

            assert result.exit_code == 0
            # Story 9.2: Profile data is now in profile.yaml
            with open("profile.yaml") as f:
                profile = yaml.safe_load(f)

            assert profile["name"] == "John Doe"
            assert profile["email"] == "john@example.com"
            assert profile["phone"] == "555-1234"
            assert profile["location"] == "SF, CA"


class TestInitJsonOutput:
    """Test JSON output mode (Task 4)."""

    def test_init_json_output(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """--json outputs structured JSON response (AC #7)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["--json", "init", "--non-interactive"])

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["status"] == "success"
            assert ".resume.yaml" in data["data"]["files_created"]

    def test_init_json_error_on_existing_config(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """--json outputs JSON error when config exists (AC #7)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".resume.yaml").write_text("existing: config")

            result = cli_runner.invoke(main, ["--json", "init", "--non-interactive"])

            assert result.exit_code == 1
            data = json.loads(result.output)
            assert data["status"] == "error"
            assert data["errors"][0]["code"] == "CONFIG_EXISTS"

    def test_init_json_includes_backup_path(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """JSON output includes backup_created when --force used (AC #7)."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".resume.yaml").write_text("existing: config")

            result = cli_runner.invoke(main, ["--json", "init", "--force", "--non-interactive"])

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["status"] == "success"
            assert data["data"]["backup_created"] == ".resume.yaml.bak"


class TestInitQuietMode:
    """Test quiet mode."""

    def test_init_quiet_mode_no_output(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Quiet mode produces no output."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["--quiet", "init", "--non-interactive"])

            assert result.exit_code == 0
            assert result.output == ""
            # But files should still be created
            assert Path(".resume.yaml").exists()
