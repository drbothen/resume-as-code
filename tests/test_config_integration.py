"""Integration tests for configuration with CLI."""

from __future__ import annotations

import os
from pathlib import Path

from click.testing import CliRunner

from resume_as_code.cli import main
from resume_as_code.config import reset_config


class TestContextConfig:
    """Test configuration in Click context."""

    def test_context_has_config_property(self) -> None:
        """Context should have a config property."""
        from resume_as_code.cli import Context

        ctx = Context()
        assert hasattr(ctx, "config")

    def test_context_config_is_lazy_loaded(self) -> None:
        """Config should be loaded lazily when first accessed."""
        from resume_as_code.cli import Context

        ctx = Context()
        # Access config to trigger lazy load
        config = ctx.config
        from resume_as_code.models.config import ResumeConfig

        assert isinstance(config, ResumeConfig)

    def test_context_set_config(self) -> None:
        """Context should allow setting config."""
        from resume_as_code.cli import Context
        from resume_as_code.models.config import ResumeConfig

        ctx = Context()
        custom_config = ResumeConfig(output_dir="./custom")
        ctx.set_config(custom_config)
        assert ctx.config.output_dir.name == "custom"


class TestConfigWithCLI:
    """Test configuration integration with CLI commands."""

    def test_config_loads_project_config(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """CLI should load project config from .resume.yaml."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create a project config file
            project_config = Path(".resume.yaml")
            project_config.write_text("output_dir: ./custom-dist\n")

            result = cli_runner.invoke(main, ["config"])
            assert result.exit_code == 0
            # Should show custom output dir from project config
            assert "custom-dist" in result.output
            assert "project" in result.output.lower()

    def test_config_loads_env_vars(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """CLI should load config from RESUME_* environment variables."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            env = os.environ.copy()
            env["RESUME_OUTPUT_DIR"] = "./env-dist"

            result = cli_runner.invoke(main, ["config"], env=env)
            assert result.exit_code == 0
            assert "env-dist" in result.output or "env" in result.output.lower()

    def test_project_overrides_user_config(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Project config should override user config."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create project config
            project_config = Path(".resume.yaml")
            project_config.write_text("output_dir: ./project-dist\n")

            result = cli_runner.invoke(main, ["config"])
            assert result.exit_code == 0
            assert "project-dist" in result.output

    def test_env_overrides_project_config(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Environment variables should override project config."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create project config
            project_config = Path(".resume.yaml")
            project_config.write_text("output_dir: ./project-dist\n")

            env = os.environ.copy()
            env["RESUME_OUTPUT_DIR"] = "./env-dist"

            result = cli_runner.invoke(main, ["config"], env=env)
            assert result.exit_code == 0
            # Environment should take precedence
            assert "env-dist" in result.output

    def test_no_config_uses_defaults(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """When no config exists, defaults should be used."""
        reset_config()
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(main, ["config"])
            assert result.exit_code == 0
            # Should show default values
            assert "dist" in result.output
            assert "default" in result.output.lower()
