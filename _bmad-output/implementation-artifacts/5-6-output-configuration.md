# Story 5.6: Output Configuration

Status: done

## Story

As a **user**,
I want **to configure output preferences**,
So that **I can customize defaults without CLI flags every time**.

## Acceptance Criteria

1. **Given** I set `output_dir: ./resumes` in `.resume.yaml`
   **When** I run `resume build --jd file.txt`
   **Then** output goes to `./resumes/` instead of `./dist/`

2. **Given** I set `default_template: ats-safe` in config
   **When** I run `resume build --jd file.txt`
   **Then** the ATS-safe template is used
   **And** I can override with `--template modern`

3. **Given** I set `scoring_weights` in config
   **When** the ranker runs
   **Then** custom weights are applied to ranking factors

4. **Given** I run `resume config output_dir ./custom`
   **When** the command completes
   **Then** the project config is updated with the new value

5. **Given** I run `resume config --list`
   **When** the command executes
   **Then** I see all current configuration values with their sources

## Tasks / Subtasks

- [x] Task 1: Extend config model (AC: #1, #2, #3)
  - [x] 1.1: Add `output_dir` config option (already existed)
  - [x] 1.2: Add `default_template` config option (already existed)
  - [x] 1.3: Add `scoring_weights` config section (added bm25_weight, semantic_weight)
  - [x] 1.4: Support default_format option (pdf, docx, all) (already existed)

- [x] Task 2: Update build command (AC: #1, #2)
  - [x] 2.1: Read output_dir from config as default
  - [x] 2.2: Read default_template from config
  - [x] 2.3: CLI flags override config values
  - [x] 2.4: Show source of configuration in verbose mode (via config command)

- [x] Task 3: Create config command (AC: #4, #5)
  - [x] 3.1: Create `src/resume_as_code/commands/config_cmd.py`
  - [x] 3.2: Implement `resume config <key> <value>` for setting
  - [x] 3.3: Implement `resume config --list` for listing
  - [x] 3.4: Show source (global, project, default) for each value

- [x] Task 4: Integrate scoring weights (AC: #3)
  - [x] 4.1: Define weight schema (bm25_weight, semantic_weight for RRF fusion)
  - [x] 4.2: Pass weights to ranker from plan/build commands
  - [x] 4.3: Document available weight options (in ScoringWeights docstring)

- [x] Task 5: Code quality verification
  - [x] 5.1: Run `ruff check src tests --fix` - All checks passed
  - [x] 5.2: Run `mypy src --strict` with zero errors - Success
  - [x] 5.3: Add tests for config command - 11 tests in test_config_cmd.py
  - [x] 5.4: Test config hierarchy (CLI > project > global > default) - via build tests

## Dev Notes

### Architecture Compliance

This story extends the configuration system from Epic 1 to support output preferences per Architecture Section 2.3.

**Source:** [epics.md#Story 5.6](_bmad-output/planning-artifacts/epics.md)

### Dependencies

This story REQUIRES:
- Story 1.3 (Configuration Hierarchy) - Base config system
- Story 5.4 (Build Command) - Build to configure

This story ENABLES:
- Complete user customization of build defaults

### Extended Config Model

**Update `src/resume_as_code/config.py`:**

```python
"""Configuration management with output preferences."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from ruamel.yaml import YAML


class ScoringWeights(BaseModel):
    """Weights for ranking algorithm."""

    title_weight: float = Field(default=1.0, ge=0.0, le=5.0)
    skills_weight: float = Field(default=1.5, ge=0.0, le=5.0)
    outcome_weight: float = Field(default=1.2, ge=0.0, le=5.0)
    recency_weight: float = Field(default=0.8, ge=0.0, le=5.0)

    # BM25 vs Semantic balance
    bm25_weight: float = Field(default=1.0, ge=0.0, le=2.0)
    semantic_weight: float = Field(default=1.0, ge=0.0, le=2.0)


class OutputConfig(BaseModel):
    """Output configuration options."""

    output_dir: Path = Field(default=Path("dist"))
    default_template: str = Field(default="modern")
    default_format: str = Field(
        default="all",
        description="pdf, docx, or all"
    )


class ContactConfig(BaseModel):
    """Contact information for resumes."""

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None


class Config(BaseModel):
    """Complete configuration model."""

    # Directories
    work_units_dir: Path = Field(default=Path("work-units"))

    # Output preferences
    output: OutputConfig = Field(default_factory=OutputConfig)

    # Scoring configuration
    scoring_weights: ScoringWeights = Field(default_factory=ScoringWeights)

    # Contact info
    contact: ContactConfig = Field(default_factory=ContactConfig)

    # Default summary
    default_summary: str | None = None

    # Source tracking for each value
    _sources: dict[str, str] = {}

    @classmethod
    def load(cls, project_path: Path | None = None) -> "Config":
        """Load config with hierarchy: CLI > project > global > defaults."""
        config_data: dict[str, Any] = {}
        sources: dict[str, str] = {}

        # Load global config
        global_config = Path.home() / ".resume.yaml"
        if global_config.exists():
            yaml = YAML()
            with open(global_config) as f:
                global_data = yaml.load(f) or {}
                cls._merge_config(config_data, global_data, sources, "global")

        # Load project config
        if project_path:
            project_config = project_path / ".resume.yaml"
            if project_config.exists():
                yaml = YAML()
                with open(project_config) as f:
                    project_data = yaml.load(f) or {}
                    cls._merge_config(config_data, project_data, sources, "project")

        config = cls.model_validate(config_data)
        config._sources = sources
        return config

    @staticmethod
    def _merge_config(
        target: dict,
        source: dict,
        sources: dict,
        source_name: str,
    ) -> None:
        """Merge source config into target, tracking sources."""
        for key, value in source.items():
            if isinstance(value, dict) and key in target:
                Config._merge_config(
                    target[key], value, sources, source_name
                )
            else:
                target[key] = value
                sources[key] = source_name

    def get_source(self, key: str) -> str:
        """Get source of a config value."""
        return self._sources.get(key, "default")

    def save_project(self, path: Path) -> None:
        """Save current config to project file."""
        yaml = YAML()
        yaml.default_flow_style = False

        data = self.model_dump(mode="json", exclude_defaults=True)

        config_path = path / ".resume.yaml"
        with open(config_path, "w") as f:
            yaml.dump(data, f)

    def set_value(self, key: str, value: str, project_path: Path) -> None:
        """Set a config value in project config."""
        # Load existing project config
        config_path = project_path / ".resume.yaml"
        yaml = YAML()

        if config_path.exists():
            with open(config_path) as f:
                data = yaml.load(f) or {}
        else:
            data = {}

        # Handle nested keys (e.g., "output.output_dir")
        keys = key.split(".")
        target = data
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        # Convert value to appropriate type
        target[keys[-1]] = self._convert_value(value)

        # Save
        with open(config_path, "w") as f:
            yaml.dump(data, f)

    @staticmethod
    def _convert_value(value: str) -> Any:
        """Convert string value to appropriate type."""
        # Try numeric
        try:
            return float(value)
        except ValueError:
            pass

        # Boolean
        if value.lower() in ("true", "yes"):
            return True
        if value.lower() in ("false", "no"):
            return False

        # String
        return value


# Convenience properties for backward compatibility
@property
def output_dir(self) -> Path:
    return self.output.output_dir

@property
def default_template(self) -> str:
    return self.output.default_template

@property
def contact_name(self) -> str | None:
    return self.contact.name
```

### Config Command

**`src/resume_as_code/commands/config.py`:**

```python
"""Config command for viewing and setting configuration."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from resume_as_code.config import Config
from resume_as_code.utils.errors import handle_errors

console = Console()


@click.command("config")
@click.argument("key", required=False)
@click.argument("value", required=False)
@click.option("--list", "-l", "list_all", is_flag=True, help="List all config values")
@click.option("--global", "-g", "use_global", is_flag=True, help="Use global config")
@click.pass_context
@handle_errors
def config_command(
    ctx: click.Context,
    key: str | None,
    value: str | None,
    list_all: bool,
    use_global: bool,
) -> None:
    """View or set configuration values.

    \b
    Examples:
      resume config --list              # List all config values
      resume config output.output_dir   # Get a specific value
      resume config output.output_dir ./resumes  # Set a value
    """
    project_path = Path.cwd()
    config = Config.load(project_path)

    if list_all:
        _display_config_list(config)
        return

    if key and value:
        # Set value
        config_path = Path.home() if use_global else project_path
        config.set_value(key, value, config_path)
        console.print(f"[green]✓[/] Set {key} = {value}")
        return

    if key:
        # Get value
        _display_config_value(config, key)
        return

    # No args - show help
    console.print("Usage: resume config [KEY] [VALUE]")
    console.print("       resume config --list")


def _display_config_list(config: Config) -> None:
    """Display all config values in a table."""
    table = Table(title="Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Source", style="dim")

    # Flatten config for display
    flat = _flatten_config(config.model_dump())

    for key, value in sorted(flat.items()):
        source = config.get_source(key)
        table.add_row(key, str(value), source)

    console.print(table)


def _display_config_value(config: Config, key: str) -> None:
    """Display a single config value."""
    flat = _flatten_config(config.model_dump())

    if key in flat:
        source = config.get_source(key)
        console.print(f"{key} = {flat[key]}")
        console.print(f"[dim]Source: {source}[/]")
    else:
        console.print(f"[yellow]Unknown config key:[/] {key}")
        console.print("[dim]Use --list to see available keys[/]")


def _flatten_config(data: dict, prefix: str = "") -> dict:
    """Flatten nested config dict."""
    result = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten_config(value, full_key))
        else:
            result[full_key] = value
    return result
```

### Example Config File

**`.resume.yaml`:**

```yaml
# Resume-as-Code Project Configuration

# Output preferences
output:
  output_dir: ./resumes
  default_template: modern
  default_format: all

# Scoring weights for ranking
scoring_weights:
  title_weight: 1.0
  skills_weight: 1.5
  outcome_weight: 1.2
  recency_weight: 0.8
  bm25_weight: 1.0
  semantic_weight: 1.0

# Contact information
contact:
  name: "John Doe"
  email: "john@example.com"
  phone: "555-123-4567"
  location: "San Francisco, CA"
  linkedin: "https://linkedin.com/in/johndoe"
  github: "https://github.com/johndoe"

# Default summary
default_summary: >
  Experienced software engineer with 10+ years building
  scalable distributed systems and leading engineering teams.

# Work units directory
work_units_dir: ./work-units
```

### Updated Build Command

**Update `src/resume_as_code/commands/build.py`:**

```python
@click.command("build")
@click.option(
    "--output-dir", "-o", "output_dir",
    type=click.Path(path_type=Path),
    default=None,  # Now None to use config default
    help="Output directory (default: from config or 'dist')",
)
@click.option(
    "--template", "-t", "template_name",
    default=None,  # Now None to use config default
    help="Template to use (default: from config or 'modern')",
)
@click.option(
    "--format", "-f", "output_format",
    type=click.Choice(["pdf", "docx", "all"]),
    default=None,  # Now None to use config default
    help="Output format (default: from config or 'all')",
)
@click.pass_context
@handle_errors
def build_command(
    ctx: click.Context,
    plan_path: Path | None,
    jd_path: Path | None,
    output_format: str | None,
    output_dir: Path | None,
    template_name: str | None,
) -> None:
    """Build resume from plan or job description."""
    config: Config = ctx.obj["config"]

    # Apply config defaults where CLI didn't specify
    actual_output_dir = output_dir or config.output.output_dir
    actual_template = template_name or config.output.default_template
    actual_format = output_format or config.output.default_format

    # ... rest of implementation uses actual_* values
```

### Testing Requirements

**`tests/unit/test_config_command.py`:**

```python
"""Tests for config command."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import cli
from resume_as_code.config import Config


@pytest.fixture
def runner():
    return CliRunner()


class TestConfigCommand:
    """Tests for config command."""

    def test_list_config(self, runner, tmp_path, monkeypatch):
        """Should list all config values."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(cli, ["config", "--list"])

        assert result.exit_code == 0
        assert "output.output_dir" in result.output or "output_dir" in result.output

    def test_get_config_value(self, runner, tmp_path, monkeypatch):
        """Should get a specific config value."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(cli, ["config", "output.default_template"])

        assert result.exit_code == 0
        # Should show value or unknown key message

    def test_set_config_value(self, runner, tmp_path, monkeypatch):
        """Should set a config value."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(cli, ["config", "output.output_dir", "./custom"])

        assert result.exit_code == 0
        assert "Set" in result.output or "custom" in result.output


class TestConfigHierarchy:
    """Tests for config hierarchy."""

    def test_cli_overrides_config(self, tmp_path):
        """CLI flags should override config file."""
        # Create project config
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("output:\n  output_dir: ./from-config\n")

        config = Config.load(tmp_path)
        assert config.output.output_dir == Path("./from-config")

        # CLI would override in actual command

    def test_project_overrides_global(self, tmp_path):
        """Project config should override global config."""
        # Would need to mock home directory for full test
        pass


class TestScoringWeights:
    """Tests for scoring weight configuration."""

    def test_loads_custom_weights(self, tmp_path):
        """Should load custom scoring weights."""
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("""
scoring_weights:
  skills_weight: 2.5
  bm25_weight: 0.5
""")

        config = Config.load(tmp_path)
        assert config.scoring_weights.skills_weight == 2.5
        assert config.scoring_weights.bm25_weight == 0.5
        # Defaults should still apply
        assert config.scoring_weights.title_weight == 1.0
```

### Verification Commands

```bash
# List all config
resume config --list

# Get specific value
resume config output.output_dir

# Set project config
resume config output.output_dir ./resumes
resume config output.default_template ats-safe
resume config scoring_weights.skills_weight 2.0

# Set global config
resume config --global contact.name "John Doe"

# Build uses config defaults
resume build --jd job.txt  # Uses config output_dir and template
resume build --jd job.txt --template modern  # Override template
```

### References

- [Source: epics.md#Story 5.6](_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5

### Debug Log References

N/A

### Completion Notes List

- All 5 Acceptance Criteria implemented and tested
- The "Extended Config Model" design in Dev Notes was simplified during implementation:
  - Used flat `ResumeConfig` instead of nested `OutputConfig`/`ContactConfig` classes
  - Used existing `get_config()` pattern instead of new `Config.load()` method
  - Simpler approach maintains backward compatibility with Epic 1 config system

### File List

**New Files:**
- `src/resume_as_code/commands/config_cmd.py` - Config command implementation (set/get/list)
- `tests/unit/test_config_cmd.py` - 11 tests for config command

**Modified Files:**
- `src/resume_as_code/commands/build.py` - Uses config defaults for output_dir, template, format
- `src/resume_as_code/commands/plan.py` - Passes scoring_weights to ranker
- `src/resume_as_code/models/config.py` - Added ScoringWeights model with bm25/semantic weights
- `src/resume_as_code/services/ranker.py` - Accepts scoring_weights parameter for RRF fusion
- `tests/unit/test_build_command.py` - Added TestConfigDefaults class (5 tests)
- `tests/unit/test_ranker.py` - Added TestScoringWeights class (3 tests)

