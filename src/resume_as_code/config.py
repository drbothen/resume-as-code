"""Configuration hierarchy loader for Resume as Code."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from resume_as_code.models.config import ConfigSource, ResumeConfig
from resume_as_code.utils.console import warning


class ConfigError(Exception):
    """Raised when configuration loading fails."""

    pass


# Config file locations
USER_CONFIG_PATH = Path.home() / ".config" / "resume-as-code" / "config.yaml"
PROJECT_CONFIG_NAME = ".resume.yaml"

# Environment variable prefix
ENV_PREFIX = "RESUME_"

# Config source tracking for the most recent get_config() call
# Note: We don't cache ResumeConfig instances because:
# 1. CLI invocations are separate processes (no caching benefit)
# 2. Tests use different cwd/configs and caching causes isolation issues
_config_sources: dict[str, ConfigSource] = {}


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Load YAML file if it exists, return empty dict otherwise.

    Raises:
        ConfigError: If the YAML file exists but contains invalid syntax.
    """
    if not path.exists():
        return {}
    try:
        with path.open() as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML syntax in {path}: {e}") from e


def load_user_config() -> tuple[dict[str, Any], Path | None]:
    """Load user config from ~/.config/resume-as-code/config.yaml."""
    if USER_CONFIG_PATH.exists():
        return load_yaml_file(USER_CONFIG_PATH), USER_CONFIG_PATH
    return {}, None


def load_project_config(
    config_path: Path | None = None,
) -> tuple[dict[str, Any], Path | None]:
    """Load project config from specified path or default .resume.yaml.

    Args:
        config_path: Explicit path to config file. If provided, uses this
            instead of looking for .resume.yaml in current directory.

    Returns:
        Tuple of (config dict, path used) or ({}, None) if no config found.
    """
    if config_path is not None:
        # Explicit path provided - Click validates existence
        return load_yaml_file(config_path), config_path

    # Default behavior: check cwd
    project_path = Path.cwd() / PROJECT_CONFIG_NAME
    if project_path.exists():
        return load_yaml_file(project_path), project_path
    return {}, None


def load_env_config() -> dict[str, Any]:
    """Load config from RESUME_* environment variables."""
    config: dict[str, Any] = {}
    for key, value in os.environ.items():
        if key.startswith(ENV_PREFIX):
            # Convert RESUME_OUTPUT_DIR to output_dir
            config_key = key[len(ENV_PREFIX) :].lower()
            config[config_key] = value
    return config


def merge_configs(
    defaults: dict[str, Any],
    user: dict[str, Any],
    project: dict[str, Any],
    env: dict[str, Any],
    cli: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge configs with correct precedence (CLI > env > project > user > defaults)."""
    result = {**defaults}
    result.update(user)
    result.update(project)
    result.update(env)
    if cli:
        # Filter out None values from CLI (unset flags)
        result.update({k: v for k, v in cli.items() if v is not None})
    return result


def reset_config() -> None:
    """Reset config source tracking. Primarily for testing."""
    global _config_sources
    _config_sources = {}


def get_config(
    cli_overrides: dict[str, Any] | None = None,
    project_config_path: Path | None = None,
) -> ResumeConfig:
    """Get the effective configuration with all sources merged.

    Args:
        cli_overrides: CLI flag values to override config.
        project_config_path: Custom path to project config file. If provided,
            uses this instead of looking for .resume.yaml in current directory.

    Returns:
        The merged ResumeConfig instance.
    """
    global _config_sources

    # Get defaults from model
    defaults = ResumeConfig().model_dump()

    # Load from sources
    user_config, user_path = load_user_config()
    project_config, project_path = load_project_config(config_path=project_config_path)
    env_config = load_env_config()

    # Merge with precedence
    merged = merge_configs(
        defaults=defaults,
        user=user_config,
        project=project_config,
        env=env_config,
        cli=cli_overrides,
    )

    # Track sources for each value
    _config_sources.clear()
    _config_sources.update(
        _track_sources(
            defaults,
            user_config,
            project_config,
            env_config,
            cli_overrides or {},
            user_path,
            project_path,
        )
    )

    config = ResumeConfig(**merged)

    # Warn about legacy config without schema_version (Story 9.1)
    if config.schema_version is None and project_path is not None:
        warning(
            f"Config file {project_path} has no schema_version. "
            "Run 'resume migrate' to update to the latest schema."
        )

    return config


def get_config_sources() -> dict[str, ConfigSource]:
    """Get the source tracking for the most recently loaded config.

    Returns:
        Dictionary mapping config keys to their ConfigSource, showing where
        each value came from (default, user, project, env, or cli).

    Note:
        Returns sources for the last config loaded via get_config().
        Call get_config() first to ensure sources are populated.
    """
    return _config_sources


def _serialize_value(
    value: Any,
) -> str | int | float | bool | dict[str, object] | list[object] | None:
    """Convert a value to a JSON-serializable type for ConfigSource."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]
    # For Pydantic models (like ScoringWeights), convert to dict
    if hasattr(value, "model_dump"):
        result: dict[str, object] = value.model_dump()
        return result
    return str(value)


def _track_sources(
    defaults: dict[str, Any],
    user: dict[str, Any],
    project: dict[str, Any],
    env: dict[str, Any],
    cli: dict[str, Any],
    user_path: Path | None,
    project_path: Path | None,
) -> dict[str, ConfigSource]:
    """Track where each config value came from."""
    sources: dict[str, ConfigSource] = {}

    for key in defaults:
        if key in cli and cli[key] is not None:
            sources[key] = ConfigSource(value=_serialize_value(cli[key]), source="cli")
        elif key in env:
            sources[key] = ConfigSource(value=_serialize_value(env[key]), source="env")
        elif key in project:
            sources[key] = ConfigSource(
                value=_serialize_value(project[key]),
                source="project",
                path=str(project_path) if project_path else None,
            )
        elif key in user:
            sources[key] = ConfigSource(
                value=_serialize_value(user[key]),
                source="user",
                path=str(user_path) if user_path else None,
            )
        else:
            sources[key] = ConfigSource(value=_serialize_value(defaults[key]), source="default")

    return sources
