# Story 7.16: CLI Config File Override

## User Story
**As a** power user or CI/CD pipeline operator
**I want** to specify an alternative config file path via `--config` flag
**So that** I can use different configurations without modifying project files or changing directories

## Background

### Current Behavior
The config hierarchy currently supports:
1. CLI flags (highest precedence)
2. Environment variables (`RESUME_*`)
3. Project config (`.resume.yaml` in current directory)
4. User config (`~/.config/resume-as-code/config.yaml`)
5. Defaults (lowest precedence)

However, the project config path is **hardcoded** to `Path.cwd() / ".resume.yaml"` in two places:
1. `config.py:load_project_config()` - uses `Path.cwd() / PROJECT_CONFIG_NAME`
2. 20 service instantiations across command files - all use `Path.cwd() / ".resume.yaml"`

### Problem
Users cannot:
- Use a config file with a different name (e.g., `resume-work.yaml` vs `resume-consulting.yaml`)
- Use a config file in a different directory without changing `cwd`
- Test different configurations in CI/CD pipelines without file manipulation

### Solution
Add a global `--config` flag that overrides the default project config path:
```bash
resume --config /path/to/custom.yaml plan --jd job.txt
resume --config ~/.resume-profiles/executive.yaml build
```

## Acceptance Criteria

### AC1: Global --config flag added
- [ ] `--config PATH` flag added to main CLI group
- [ ] Flag accepts absolute or relative paths
- [ ] Flag is optional (current behavior is default)

### AC2: Config path stored in Context
- [ ] `Context` class has `config_path: Path | None` attribute
- [ ] `config_path` defaults to `None` (use default behavior)
- [ ] When set, `config_path` is used instead of `Path.cwd() / ".resume.yaml"`

### AC3: Config loader respects override
- [ ] `get_config()` accepts optional `project_config_path: Path | None` parameter
- [ ] `load_project_config()` accepts optional path parameter
- [ ] When path provided, uses that instead of default

### AC4: All services use context config path
- [ ] All 20 service instantiations updated to use `ctx.obj.config_path`
- [ ] Services receive `None` when no override (use their default behavior)
- [ ] Pattern: `service = FooService(config_path=ctx.obj.config_path or Path.cwd() / ".resume.yaml")`

### AC5: Error handling
- [ ] Clear error if specified config file doesn't exist
- [ ] Error includes the attempted path for debugging
- [ ] Exit code 2 (CONFIG_ERROR) for config file issues

### AC6: Help text accurate
- [ ] `--config` flag shows in `resume --help`
- [ ] Help text explains it overrides project config path
- [ ] Example usage shown in help

## Technical Design

### Files to Modify

#### 1. `src/resume_as_code/context.py`
Add `config_path` attribute to Context:

```python
class Context:
    """Click context object for storing global options and configuration."""

    def __init__(self) -> None:
        self.json_output: bool = False
        self.verbose: bool = False
        self.quiet: bool = False
        self.config_path: Path | None = None  # NEW: Custom config file path
        self._config: ResumeConfig | None = None

    @property
    def config(self) -> ResumeConfig:
        """Get the effective configuration, loading it lazily if needed."""
        if self._config is None:
            from resume_as_code.config import get_config

            self._config = get_config(project_config_path=self.config_path)
        return self._config
```

#### 2. `src/resume_as_code/cli.py`
Add `--config` option to main group:

```python
@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="resume")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to config file (overrides default .resume.yaml)",
)
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.option("-v", "--verbose", is_flag=True, help="Show verbose debug output")
@click.option("-q", "--quiet", is_flag=True, help="Suppress all output, exit code only")
@click.pass_context
@handle_errors
def main(
    ctx: click.Context,
    config_path: Path | None,
    json_output: bool,
    verbose: bool,
    quiet: bool,
) -> None:
    """Resume as Code - CLI tool for git-native resume generation."""
    ctx.ensure_object(Context)
    ctx.obj.config_path = config_path  # Store in context
    ctx.obj.json_output = json_output
    ctx.obj.verbose = verbose
    ctx.obj.quiet = quiet
    # ... rest of function
```

#### 3. `src/resume_as_code/config.py`
Update config loading functions:

```python
def load_project_config(
    config_path: Path | None = None,
) -> tuple[dict[str, Any], Path | None]:
    """Load project config from specified path or default .resume.yaml."""
    if config_path is not None:
        # Explicit path provided - must exist (Click validates this)
        return load_yaml_file(config_path), config_path

    # Default behavior: check cwd
    project_path = Path.cwd() / PROJECT_CONFIG_NAME
    if project_path.exists():
        return load_yaml_file(project_path), project_path
    return {}, None


def get_config(
    cli_overrides: dict[str, Any] | None = None,
    project_config_path: Path | None = None,
) -> ResumeConfig:
    """Get the effective configuration with all sources merged.

    Args:
        cli_overrides: CLI flag values to override config
        project_config_path: Custom path to project config file
    """
    global _config, _config_sources

    defaults = ResumeConfig().model_dump()
    user_config, user_path = load_user_config()
    project_config, project_path = load_project_config(project_config_path)
    env_config = load_env_config()

    # ... rest of function unchanged
```

#### 4. Command files (20 locations)
Update service instantiations to use context config path:

**Pattern to apply in each location:**

Before:
```python
service = CertificationService(config_path=Path.cwd() / ".resume.yaml")
```

After:
```python
config_path = ctx.obj.config_path or Path.cwd() / ".resume.yaml"
service = CertificationService(config_path=config_path)
```

**Files to update:**
- `commands/list_cmd.py` (5 locations: lines 151, 178, 205, 232, 723)
- `commands/show.py` (5 locations: lines 298, 398, 482, 533, 623)
- `commands/remove.py` (5 locations: lines 38, 217, 302, 477, 566)
- `commands/new.py` (5 locations: lines 1105, 1248, 1370, 1477, 1644)

**Helper function option:**
Consider adding a helper to Context to reduce repetition:

```python
# In context.py
@property
def effective_config_path(self) -> Path:
    """Get the effective config path (custom or default)."""
    return self.config_path or Path.cwd() / ".resume.yaml"
```

Then commands use:
```python
service = CertificationService(config_path=ctx.obj.effective_config_path)
```

### Validation Behavior

The `--config` flag uses Click's path validation:
- `exists=True` - File must exist
- `dir_okay=False` - Must be a file, not directory
- `path_type=Path` - Returns pathlib.Path object

If file doesn't exist, Click automatically shows error and exits.

### Config Source Tracking

When `--config` is used, the source tracking should show:
```python
ConfigSource(value=..., source="project", path="/custom/path.yaml")
```

This is already handled since `load_project_config()` returns the actual path used.

## Test Cases

### Unit Tests

#### Test: --config flag parsed correctly
```python
def test_config_flag_parsed(cli_runner, tmp_path):
    """--config flag should be stored in context."""
    config_file = tmp_path / "custom.yaml"
    config_file.write_text("work_unit_dir: custom-units\n")

    result = cli_runner.invoke(main, ["--config", str(config_file), "config"])

    assert result.exit_code == 0
    assert "custom-units" in result.output
```

#### Test: --config overrides default
```python
def test_config_overrides_default(cli_runner, tmp_path, monkeypatch):
    """Custom config should override .resume.yaml in cwd."""
    # Create default config in cwd
    default_config = tmp_path / ".resume.yaml"
    default_config.write_text("work_unit_dir: default-units\n")

    # Create custom config
    custom_config = tmp_path / "custom.yaml"
    custom_config.write_text("work_unit_dir: custom-units\n")

    monkeypatch.chdir(tmp_path)

    result = cli_runner.invoke(main, ["--config", str(custom_config), "config"])

    assert "custom-units" in result.output
    assert "default-units" not in result.output
```

#### Test: Missing config file error
```python
def test_config_missing_file_error(cli_runner):
    """Non-existent config file should show clear error."""
    result = cli_runner.invoke(main, ["--config", "/nonexistent/path.yaml", "config"])

    assert result.exit_code != 0
    assert "does not exist" in result.output.lower() or "no such file" in result.output.lower()
```

#### Test: Services receive config path
```python
def test_services_receive_config_path(cli_runner, tmp_path, mocker):
    """Services should receive the custom config path."""
    config_file = tmp_path / "custom.yaml"
    config_file.write_text("certifications: []\n")

    mock_service = mocker.patch("resume_as_code.commands.list_cmd.CertificationService")

    cli_runner.invoke(main, ["--config", str(config_file), "list", "certifications"])

    mock_service.assert_called_once()
    call_kwargs = mock_service.call_args.kwargs
    assert call_kwargs["config_path"] == config_file
```

### Integration Tests

#### Test: Full workflow with custom config
```python
def test_full_workflow_custom_config(cli_runner, tmp_path):
    """Full workflow should work with custom config."""
    # Setup custom config
    config_file = tmp_path / "profile.yaml"
    config_file.write_text("""
work_unit_dir: work-units
output_dir: output
    """)

    # Create required directories
    (tmp_path / "work-units").mkdir()

    result = cli_runner.invoke(
        main,
        ["--config", str(config_file), "validate"],
        catch_exceptions=False
    )

    assert result.exit_code == 0
```

## Definition of Done

- [ ] `--config` flag added to main CLI group
- [ ] Flag documented in help text
- [ ] Context stores and provides config path
- [ ] `get_config()` accepts project config path parameter
- [ ] `load_project_config()` accepts optional path parameter
- [ ] All 20 service instantiations updated
- [ ] Unit tests for flag parsing (≥3 tests)
- [ ] Unit tests for config loading (≥2 tests)
- [ ] Integration test for full workflow
- [ ] All existing tests pass
- [ ] `uv run ruff check src tests --fix` passes
- [ ] `uv run mypy src --strict` passes

## Implementation Notes

### Recommended Approach
1. Start with `context.py` - add `config_path` and `effective_config_path`
2. Update `cli.py` - add `--config` option, wire to context
3. Update `config.py` - add path parameter to functions
4. Update command files - use `ctx.obj.effective_config_path`
5. Add tests

### Refactoring Opportunity
The 20 hardcoded paths could be reduced by:
1. Having services default to `None` for config_path
2. Services internally resolve to default if `None`
3. This way commands just pass `ctx.obj.config_path` (could be `None`)

This is optional for this story but would clean up the pattern.

### Story Points: 2
Low complexity - mostly mechanical changes with clear pattern.

## Out of Scope
- Multiple config file merging (e.g., `--config a.yaml --config b.yaml`)
- Config file generation/init command
- Config file validation command
