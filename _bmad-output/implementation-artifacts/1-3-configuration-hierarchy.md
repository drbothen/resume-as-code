# Story 1.3: Configuration Hierarchy

Status: done

## Story

As a **user**,
I want **configuration loaded from multiple sources with clear precedence**,
So that **I can set project defaults and override them when needed**.

## Acceptance Criteria

1. **Given** a project config exists at `.resume.yaml`
   **When** I run a resume command
   **Then** settings from `.resume.yaml` are applied

2. **Given** a user config exists at `~/.config/resume-as-code/config.yaml`
   **When** I run a resume command and no project config exists
   **Then** settings from user config are applied

3. **Given** both project and user configs exist
   **When** I run a resume command
   **Then** project config values override user config values

4. **Given** I pass a CLI flag (e.g., `--output-dir ./custom`)
   **When** the command executes
   **Then** the CLI flag overrides both project and user config

5. **Given** no config files exist
   **When** I run a resume command
   **Then** sensible defaults are used (e.g., `output_dir: ./dist`)

6. **Given** I run `resume config`
   **When** the command executes
   **Then** I see the current effective configuration with sources indicated

## Tasks / Subtasks

- [x] Task 1: Create configuration Pydantic models (AC: #1-#5)
  - [x] 1.1: Create `src/resume_as_code/models/config.py`
  - [x] 1.2: Implement `ResumeConfig` model with all configurable fields
  - [x] 1.3: Define sensible defaults for all fields
  - [x] 1.4: Add field validators for path and enum fields

- [x] Task 2: Create configuration loader (AC: #1-#5)
  - [x] 2.1: Create `src/resume_as_code/config.py` (module-level loader)
  - [x] 2.2: Implement `load_user_config()` from `~/.config/resume-as-code/config.yaml`
  - [x] 2.3: Implement `load_project_config()` from `.resume.yaml`
  - [x] 2.4: Implement `load_env_config()` from `RESUME_*` environment variables
  - [x] 2.5: Implement `merge_configs()` with correct precedence
  - [x] 2.6: Implement `get_config()` singleton accessor

- [x] Task 3: Create config schema file (AC: #1)
  - [x] 3.1: Create `schemas/config.schema.json` for validation
  - [x] 3.2: Document all configurable fields in schema

- [x] Task 4: Implement `resume config` command (AC: #6)
  - [x] 4.1: Create `src/resume_as_code/commands/config_cmd.py`
  - [x] 4.2: Implement `resume config` to show effective config
  - [x] 4.3: Show source of each value (default/user/project/env/cli)
  - [x] 4.4: Support `--json` output mode
  - [x] 4.5: Register command in `cli.py`

- [x] Task 5: Wire configuration into CLI (AC: #4)
  - [x] 5.1: Load config at CLI startup in `cli.py`
  - [x] 5.2: Pass config through Click context
  - [x] 5.3: Ensure CLI flags can override config values

- [x] Task 6: Code quality verification
  - [x] 6.1: Run `ruff check src tests --fix`
  - [x] 6.2: Run `ruff format src tests`
  - [x] 6.3: Run `mypy src --strict` with zero errors
  - [x] 6.4: Add unit tests for config loading and merging
  - [x] 6.5: Add integration tests for `resume config` command

## Dev Notes

### Architecture Compliance

This story implements the configuration hierarchy that ALL commands will use. Follow the precedence order exactly as specified in the architecture.

**Source:** [Architecture Section 3.7 - Configuration Hierarchy](_bmad-output/planning-artifacts/architecture.md#37-configuration-hierarchy)

### Dependencies

This story REQUIRES:
- Story 1.1 (Project Scaffolding) - CLI skeleton
- Story 1.2 (Rich Console) - Output formatting utilities

### Configuration Precedence (CRITICAL)

From highest to lowest priority:

| Level | Source | Example |
|-------|--------|---------|
| 1 (Highest) | CLI flags | `--output-dir ./custom` |
| 2 | Environment | `RESUME_OUTPUT_DIR=./env` |
| 3 | Project config | `.resume.yaml` in cwd |
| 4 | User config | `~/.config/resume-as-code/config.yaml` |
| 5 (Lowest) | Built-in defaults | `output_dir: ./dist` |

### Configuration Model

**`src/resume_as_code/models/config.py`:**

```python
"""Configuration models for Resume as Code."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ScoringWeights(BaseModel):
    """Weights for ranking algorithm."""

    title_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    skills_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    experience_weight: float = Field(default=1.0, ge=0.0, le=10.0)


class ResumeConfig(BaseModel):
    """Complete configuration for Resume as Code."""

    # Output settings
    output_dir: Path = Field(default=Path("./dist"))
    default_format: Literal["pdf", "docx", "both"] = Field(default="both")
    default_template: str = Field(default="modern")

    # Work unit settings
    work_units_dir: Path = Field(default=Path("./work-units"))

    # Ranking settings
    scoring_weights: ScoringWeights = Field(default_factory=ScoringWeights)
    default_top_k: int = Field(default=8, ge=1, le=50)

    # Editor settings
    editor: str | None = Field(default=None)  # Falls back to $EDITOR

    @field_validator("output_dir", "work_units_dir", mode="before")
    @classmethod
    def expand_path(cls, v: str | Path) -> Path:
        """Expand ~ and resolve path."""
        if isinstance(v, str):
            v = Path(v)
        return v.expanduser()


class ConfigSource(BaseModel):
    """Tracks the source of each config value."""

    value: str | int | float | bool | dict[str, object] | list[object] | None
    source: Literal["default", "user", "project", "env", "cli"]
    path: str | None = None  # File path if from file
```

### Configuration Loader

**`src/resume_as_code/config.py`:**

```python
"""Configuration hierarchy loader for Resume as Code."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from resume_as_code.models.config import ResumeConfig, ConfigSource

# Config file locations
USER_CONFIG_PATH = Path.home() / ".config" / "resume-as-code" / "config.yaml"
PROJECT_CONFIG_NAME = ".resume.yaml"

# Environment variable prefix
ENV_PREFIX = "RESUME_"

# Singleton config instance
_config: ResumeConfig | None = None
_config_sources: dict[str, ConfigSource] = {}


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Load YAML file if it exists, return empty dict otherwise."""
    if not path.exists():
        return {}
    with path.open() as f:
        return yaml.safe_load(f) or {}


def load_user_config() -> tuple[dict[str, Any], Path | None]:
    """Load user config from ~/.config/resume-as-code/config.yaml."""
    if USER_CONFIG_PATH.exists():
        return load_yaml_file(USER_CONFIG_PATH), USER_CONFIG_PATH
    return {}, None


def load_project_config() -> tuple[dict[str, Any], Path | None]:
    """Load project config from .resume.yaml in current directory."""
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
            config_key = key[len(ENV_PREFIX):].lower()
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


def get_config(cli_overrides: dict[str, Any] | None = None) -> ResumeConfig:
    """Get the effective configuration with all sources merged."""
    global _config, _config_sources

    # Get defaults from model
    defaults = ResumeConfig().model_dump()

    # Load from sources
    user_config, user_path = load_user_config()
    project_config, project_path = load_project_config()
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
    _config_sources = _track_sources(
        defaults, user_config, project_config, env_config, cli_overrides or {},
        user_path, project_path
    )

    _config = ResumeConfig(**merged)
    return _config


def get_config_sources() -> dict[str, ConfigSource]:
    """Get the source tracking for current config."""
    return _config_sources


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
            sources[key] = ConfigSource(value=cli[key], source="cli")
        elif key in env:
            sources[key] = ConfigSource(value=env[key], source="env")
        elif key in project:
            sources[key] = ConfigSource(
                value=project[key], source="project",
                path=str(project_path) if project_path else None
            )
        elif key in user:
            sources[key] = ConfigSource(
                value=user[key], source="user",
                path=str(user_path) if user_path else None
            )
        else:
            sources[key] = ConfigSource(value=defaults[key], source="default")

    return sources
```

### Config Command Implementation

**`src/resume_as_code/commands/config_cmd.py`:**

```python
"""Configuration command for Resume as Code."""

from __future__ import annotations

import click
from rich.table import Table

from resume_as_code.config import get_config, get_config_sources, reset_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.utils.console import console


@click.command("config")
@click.pass_context
def config_command(ctx: click.Context) -> None:
    """Display current effective configuration with sources."""
    # Reset config to ensure fresh load with current environment
    reset_config()

    config = get_config()
    sources = get_config_sources()

    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="config",
            data={
                "config": config.model_dump(mode="json"),
                "sources": {k: v.model_dump() for k, v in sources.items()},
            },
        )
        click.echo(response.to_json())
        return

    if ctx.obj.quiet:
        return

    # Rich table output
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Source", style="yellow")

    config_dict = config.model_dump()
    for key, value in config_dict.items():
        source = sources.get(key)
        source_str: str = source.source if source else "unknown"
        if source and source.path:
            source_str = f"{source.source} ({source.path})"
        table.add_row(key, str(value), source_str)

    console.print(table)
```

### CLI Integration

**Update `src/resume_as_code/cli.py`:**

```python
# Add import
from resume_as_code.commands.config_cmd import config_command

# Register command after main group definition
main.add_command(config_command)
```

### Environment Variable Mapping

| Environment Variable | Config Field | Example |
|---------------------|--------------|---------|
| `RESUME_OUTPUT_DIR` | `output_dir` | `./custom-dist` |
| `RESUME_DEFAULT_FORMAT` | `default_format` | `pdf` |
| `RESUME_DEFAULT_TEMPLATE` | `default_template` | `ats-safe` |
| `RESUME_WORK_UNITS_DIR` | `work_units_dir` | `./my-units` |
| `RESUME_EDITOR` | `editor` | `code` |

### Project Structure After This Story

```
src/resume_as_code/
├── __init__.py
├── __main__.py
├── cli.py                    # Updated with config command
├── config.py                 # NEW: Configuration loader
├── commands/
│   ├── __init__.py           # NEW
│   └── config_cmd.py         # NEW: resume config command
├── models/
│   ├── __init__.py
│   ├── config.py             # NEW: Config Pydantic models
│   └── output.py
└── utils/
    ├── __init__.py
    └── console.py

schemas/
└── config.schema.json        # NEW: Config JSON Schema
```

### Config Schema

**`schemas/config.schema.json`:**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://resume-as-code.dev/schemas/config.schema.json",
  "title": "Resume as Code Configuration",
  "type": "object",
  "properties": {
    "output_dir": {
      "type": "string",
      "description": "Directory for generated resume files",
      "default": "./dist"
    },
    "default_format": {
      "type": "string",
      "enum": ["pdf", "docx", "both"],
      "default": "both"
    },
    "default_template": {
      "type": "string",
      "default": "modern"
    },
    "work_units_dir": {
      "type": "string",
      "default": "./work-units"
    },
    "scoring_weights": {
      "type": "object",
      "properties": {
        "title_weight": { "type": "number", "minimum": 0, "maximum": 10 },
        "skills_weight": { "type": "number", "minimum": 0, "maximum": 10 },
        "experience_weight": { "type": "number", "minimum": 0, "maximum": 10 }
      }
    },
    "default_top_k": {
      "type": "integer",
      "minimum": 1,
      "maximum": 50,
      "default": 8
    },
    "editor": {
      "type": ["string", "null"],
      "description": "Editor to use for work unit creation"
    }
  }
}
```

### Testing Requirements

**`tests/unit/test_config.py`:**

```python
"""Tests for configuration loading."""

from pathlib import Path
from unittest.mock import patch

import pytest

from resume_as_code.config import (
    get_config,
    load_env_config,
    merge_configs,
)
from resume_as_code.models.config import ResumeConfig


def test_default_config_values():
    """Default config should have sensible values."""
    config = ResumeConfig()
    assert config.output_dir == Path("./dist")
    assert config.default_format == "both"
    assert config.default_template == "modern"


def test_env_config_loads_prefixed_vars():
    """Environment variables with RESUME_ prefix should be loaded."""
    with patch.dict("os.environ", {"RESUME_OUTPUT_DIR": "./custom"}):
        env_config = load_env_config()
        assert env_config["output_dir"] == "./custom"


def test_merge_configs_precedence():
    """CLI should override project, project should override user."""
    defaults = {"output_dir": "./dist"}
    user = {"output_dir": "./user"}
    project = {"output_dir": "./project"}
    cli = {"output_dir": "./cli"}

    result = merge_configs(defaults, user, project, {}, cli)
    assert result["output_dir"] == "./cli"


def test_merge_configs_cli_none_ignored():
    """None values from CLI should not override."""
    defaults = {"output_dir": "./dist"}
    project = {"output_dir": "./project"}
    cli = {"output_dir": None}

    result = merge_configs(defaults, {}, project, {}, cli)
    assert result["output_dir"] == "./project"
```

### Verification Commands

```bash
# Test with no config files (defaults)
resume config
# Should show all defaults with source="default"

# Create user config
mkdir -p ~/.config/resume-as-code
echo "output_dir: ./user-dist" > ~/.config/resume-as-code/config.yaml
resume config
# Should show output_dir from user config

# Create project config
echo "output_dir: ./project-dist" > .resume.yaml
resume config
# Should show output_dir from project config (overrides user)

# Test environment override
RESUME_OUTPUT_DIR=./env-dist resume config
# Should show output_dir from env (overrides project)

# Test JSON output
resume --json config

# Code quality
ruff check src tests --fix
ruff format src tests
mypy src --strict
pytest tests/unit/test_config.py
```

### References

- [Source: architecture.md#Section 3.7 - Configuration Hierarchy](_bmad-output/planning-artifacts/architecture.md)
- [Source: architecture.md#Section 5.4 - Cross-Cutting Concerns](_bmad-output/planning-artifacts/architecture.md)
- [Source: project-context.md - Critical Implementation Rules](_bmad-output/project-context.md)
- [Source: epics.md#Story 1.3](_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- Implemented `ResumeConfig`, `ScoringWeights`, and `ConfigSource` Pydantic models with full type hints and field validators
- Created configuration loader with 5-level precedence: CLI > env > project > user > defaults
- Implemented `resume config` command showing effective configuration with Rich table output and JSON mode
- Added config to CLI context for lazy-loaded access by all commands
- Created JSON Schema for config validation at `schemas/config.schema.json`
- Added `ConfigError` exception class for user-friendly error handling on malformed YAML
- All 144 tests pass with zero regressions
- mypy --strict passes with no errors
- ruff check/format passes with no issues

### Code Review Fixes Applied

- H1: Added `uv.lock` to File List for traceability
- M1: Updated `ConfigSource.value` type annotation in story template to match implementation (`dict[str, object] | list[object]`)
- M2: Updated story template to use `click.echo()` instead of `print()`
- M3: Added `reset_config()` call to story template
- M4: Added `ConfigError` exception and test for malformed YAML handling
- L1: Added 12 unit tests for `_serialize_value()` function
- L2: Refactored tests to use `monkeypatch.chdir()` instead of `os.chdir()` for safer test isolation

### File List

**New Files:**
- `src/resume_as_code/models/config.py` - Configuration Pydantic models
- `src/resume_as_code/config.py` - Configuration loader with precedence hierarchy
- `src/resume_as_code/commands/config_cmd.py` - resume config command
- `schemas/config.schema.json` - JSON Schema for config validation
- `tests/unit/test_config_models.py` - Unit tests for config models (22 tests)
- `tests/unit/test_config_loader.py` - Unit tests for config loader (39 tests, includes _serialize_value and malformed YAML)
- `tests/unit/test_config_cmd.py` - Unit tests for config command (6 tests)
- `tests/test_config_integration.py` - Integration tests for config with CLI (8 tests)

**Modified Files:**
- `src/resume_as_code/models/__init__.py` - Added config model exports
- `src/resume_as_code/commands/__init__.py` - Added config_command export
- `src/resume_as_code/cli.py` - Added config to Context, registered config command
- `pyproject.toml` - Added types-PyYAML dev dependency
- `uv.lock` - Updated lockfile for types-PyYAML dependency

