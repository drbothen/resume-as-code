# Story 7.21: Resume Init Command

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **new user**,
I want **a `resume init` command to scaffold my project with sensible defaults**,
So that **I can quickly start capturing work units without manually creating config files**.

## Acceptance Criteria

1. **Given** `resume init` is run in a directory without `.resume.yaml`
   **When** the command completes successfully
   **Then** the following are created:
   - `.resume.yaml` with default configuration
   - `work-units/` directory
   - `positions.yaml` with empty list

2. **Given** no flags are provided (interactive mode)
   **When** running `resume init`
   **Then** prompts are displayed for profile info:
   - name (required)
   - email (optional)
   - phone (optional)
   - location (optional)
   - linkedin (optional, validates as URL)
   - github (optional, validates as URL)
   - website (optional, validates as URL)
   **And** profile values are written to `.resume.yaml`

3. **Given** `--non-interactive` flag is provided
   **When** running `resume init --non-interactive`
   **Then** files are created with placeholder values
   **And** no prompts are displayed
   **And** placeholder text indicates "TODO: Add your..."

4. **Given** `.resume.yaml` already exists
   **When** running `resume init`
   **Then** command fails with exit code 1
   **And** error message: "Configuration already exists: .resume.yaml"
   **And** suggests: "Use --force to reinitialize"

5. **Given** `--force` flag is provided and `.resume.yaml` exists
   **When** running `resume init --force`
   **Then** existing `.resume.yaml` is backed up to `.resume.yaml.bak`
   **And** new configuration is created
   **And** info message shows backup location

6. **Given** init completes successfully
   **When** displaying success output
   **Then** shows what was created:
   - "Created .resume.yaml"
   - "Created work-units/"
   - "Created positions.yaml"
   **And** suggests next steps:
   - "Next: `resume new position` to add your employment history"
   - "Then: `resume new work-unit` to capture achievements"

7. **Given** `--json` global flag is set
   **When** running `resume --json init`
   **Then** output is JSON format with:
   - `status: "success"`
   - `data.files_created: [".resume.yaml", "work-units/", "positions.yaml"]`
   - `data.backup_created: ".resume.yaml.bak"` (if --force used)

## Tasks / Subtasks

- [x] Task 1: Create init command structure (AC: #1, #2, #3)
  - [x] 1.1 Create `src/resume_as_code/commands/init.py`
  - [x] 1.2 Add `@click.command("init")` with options
  - [x] 1.3 Implement interactive profile prompts using Rich
  - [x] 1.4 Implement `--non-interactive` mode with placeholders
  - [x] 1.5 Wire command into cli.py via `_register_commands()`

- [x] Task 2: Implement file creation logic (AC: #1, #6)
  - [x] 2.1 Create default `.resume.yaml` with profile data
  - [x] 2.2 Create `work-units/` directory with `.gitkeep`
  - [x] 2.3 Create `positions.yaml` with `[]` content
  - [x] 2.4 Output success messages with Rich formatting
  - [x] 2.5 Display next steps suggestions

- [x] Task 3: Implement safety checks (AC: #4, #5)
  - [x] 3.1 Check for existing `.resume.yaml` before proceeding
  - [x] 3.2 Implement `--force` flag with backup logic
  - [x] 3.3 Create backup: `.resume.yaml.bak`
  - [x] 3.4 Return appropriate exit codes

- [x] Task 4: JSON output support (AC: #7)
  - [x] 4.1 Use `JSONResponse` model from `models/output.py`
  - [x] 4.2 Include files_created list in data
  - [x] 4.3 Include backup_created if applicable

- [x] Task 5: Unit and integration tests
  - [x] 5.1 Test init creates expected files
  - [x] 5.2 Test init fails when config exists
  - [x] 5.3 Test --force creates backup
  - [x] 5.4 Test --non-interactive creates placeholders
  - [x] 5.5 Test JSON output format
  - [x] 5.6 Test interactive prompts (with mock input)

- [x] Task 6: Quality checks
  - [x] 6.1 Run `ruff check src tests --fix`
  - [x] 6.2 Run `ruff format src tests`
  - [x] 6.3 Run `mypy src --strict` (zero errors)
  - [x] 6.4 Run full test suite
  - [x] 6.5 Update CLAUDE.md with new command

## Dev Notes

### Current State Analysis

**What exists:**
- `cli.py` with command registration via `_register_commands()` and `main.add_command()`
- `context.py` with `Context` class and `pass_context` decorator
- `models/config.py` with `ResumeConfig` and `ProfileConfig` models
- `models/output.py` with `JSONResponse` model for structured JSON output
- `utils/console.py` with `console`, `err_console`, `success()`, `info()`, `warning()` helpers
- `utils/errors.py` with `handle_errors` decorator
- Commands follow pattern: `@click.command("name")`, `@pass_context`, `@handle_errors`

**Gap:**
- No `init` command for explicit project setup
- New users must manually create config files
- No guided onboarding experience

### Implementation Pattern

**Command Structure (following existing patterns):**
```python
# src/resume_as_code/commands/init.py
"""Init command for initializing resume projects."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click
import yaml
from rich.prompt import Prompt

from resume_as_code.cli import pass_context
from resume_as_code.context import Context
from resume_as_code.models.output import JSONResponse
from resume_as_code.utils.console import console, err_console, info, success
from resume_as_code.utils.errors import handle_errors

DEFAULT_CONFIG: dict[str, Any] = {
    "output_dir": "./dist",
    "default_format": "both",
    "default_template": "modern",
    "work_units_dir": "./work-units",
    "positions_path": "./positions.yaml",
    "profile": {},
    "certifications": [],
    "education": [],
    "career_highlights": [],
}


@click.command("init")
@click.option(
    "--non-interactive",
    is_flag=True,
    help="Create config with placeholders, no prompts",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing config (creates .resume.yaml.bak backup)",
)
@pass_context
@handle_errors
def init_command(ctx: Context, non_interactive: bool, force: bool) -> None:
    """Initialize a new resume project.

    Creates .resume.yaml, work-units/ directory, and positions.yaml with
    sensible defaults. Interactive mode prompts for profile information.

    \b
    Example usage:
        resume init                     # Interactive setup
        resume init --non-interactive   # Quick setup with placeholders
        resume init --force             # Reinitialize (backs up existing)
    """
    config_path = Path(".resume.yaml")
    work_units_dir = Path("work-units")
    positions_path = Path("positions.yaml")

    files_created: list[str] = []
    backup_created: str | None = None

    # Safety check: existing config
    if config_path.exists() and not force:
        if ctx.json_output:
            _output_json_error(ctx, "Configuration already exists: .resume.yaml")
        else:
            err_console.print("[red]✗[/red] Configuration already exists: .resume.yaml")
            err_console.print("  [dim]Use --force to reinitialize (creates backup)[/dim]")
        raise SystemExit(1)

    # Create backup if force
    if config_path.exists() and force:
        backup_path = Path(".resume.yaml.bak")
        config_path.rename(backup_path)
        backup_created = str(backup_path)
        if not ctx.json_output and not ctx.quiet:
            info(f"Backed up existing config to {backup_path}")

    # Collect profile data
    if non_interactive:
        profile = _get_placeholder_profile()
    else:
        profile = _prompt_for_profile()

    # Create config file
    config = DEFAULT_CONFIG.copy()
    config["profile"] = {k: v for k, v in profile.items() if v is not None}
    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
    files_created.append(str(config_path))

    # Create work-units directory
    work_units_dir.mkdir(exist_ok=True)
    (work_units_dir / ".gitkeep").touch()
    files_created.append(str(work_units_dir) + "/")

    # Create positions.yaml
    positions_path.write_text("[]\n")
    files_created.append(str(positions_path))

    # Output
    if ctx.json_output:
        _output_json_success(files_created, backup_created)
    elif not ctx.quiet:
        _display_success(files_created, backup_created)


def _get_placeholder_profile() -> dict[str, str | None]:
    """Return profile with placeholder values."""
    return {
        "name": "TODO: Add your name",
        "email": None,
        "phone": None,
        "location": None,
        "linkedin": None,
        "github": None,
        "website": None,
    }


def _prompt_for_profile() -> dict[str, str | None]:
    """Interactively prompt for profile information."""
    console.print("\n[bold]Profile Setup[/bold]")
    console.print("[dim]Enter your information (press Enter to skip optional fields)[/dim]\n")

    name = Prompt.ask("[bold]Name[/bold] (required)")
    while not name.strip():
        console.print("[yellow]Name is required[/yellow]")
        name = Prompt.ask("[bold]Name[/bold] (required)")

    email = Prompt.ask("Email", default="") or None
    phone = Prompt.ask("Phone", default="") or None
    location = Prompt.ask("Location (e.g., San Francisco, CA)", default="") or None
    linkedin = Prompt.ask("LinkedIn URL", default="") or None
    github = Prompt.ask("GitHub URL", default="") or None
    website = Prompt.ask("Website URL", default="") or None

    return {
        "name": name.strip(),
        "email": email,
        "phone": phone,
        "location": location,
        "linkedin": linkedin,
        "github": github,
        "website": website,
    }


def _display_success(files_created: list[str], backup_created: str | None) -> None:
    """Display success message with next steps."""
    console.print()
    success("Project initialized!")
    console.print()

    console.print("[bold]Created:[/bold]")
    for f in files_created:
        console.print(f"  [green]✓[/green] {f}")

    if backup_created:
        console.print(f"  [yellow]↳[/yellow] Previous config backed up to {backup_created}")

    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. [cyan]resume new position[/cyan] - Add your employment history")
    console.print("  2. [cyan]resume new work-unit[/cyan] - Capture your achievements")
    console.print("  3. [cyan]resume plan --jd job.txt[/cyan] - Generate a tailored resume")
    console.print()


def _output_json_success(files_created: list[str], backup_created: str | None) -> None:
    """Output JSON success response."""
    data: dict[str, Any] = {"files_created": files_created}
    if backup_created:
        data["backup_created"] = backup_created

    response = JSONResponse(
        status="success",
        command="init",
        data=data,
    )
    console.print(response.model_dump_json(indent=2))


def _output_json_error(ctx: Context, message: str) -> None:
    """Output JSON error response."""
    response = JSONResponse(
        status="error",
        command="init",
        errors=[{"code": "CONFIG_EXISTS", "message": message, "recoverable": True}],
    )
    console.print(response.model_dump_json(indent=2))
```

**CLI Registration (in `cli.py`):**
```python
# In _register_commands() function
from resume_as_code.commands.init import init_command
main.add_command(init_command)
```

### Dependencies

- **Depends on:** None (foundational command)
- **Blocked by:** None

### Testing Strategy

```python
# tests/unit/test_init_command.py
from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main


@pytest.fixture
def empty_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create empty directory and change to it."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestInitCommand:
    def test_init_creates_expected_files(self, empty_dir: Path) -> None:
        """init creates .resume.yaml, work-units/, positions.yaml."""
        runner = CliRunner()
        result = runner.invoke(main, ["init", "--non-interactive"])

        assert result.exit_code == 0
        assert (empty_dir / ".resume.yaml").exists()
        assert (empty_dir / "work-units").is_dir()
        assert (empty_dir / "work-units" / ".gitkeep").exists()
        assert (empty_dir / "positions.yaml").exists()

    def test_init_fails_when_config_exists(self, empty_dir: Path) -> None:
        """init fails if .resume.yaml already exists."""
        (empty_dir / ".resume.yaml").write_text("existing: config")

        runner = CliRunner()
        result = runner.invoke(main, ["init"])

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_init_force_creates_backup(self, empty_dir: Path) -> None:
        """--force backs up existing config."""
        (empty_dir / ".resume.yaml").write_text("existing: config")

        runner = CliRunner()
        result = runner.invoke(main, ["init", "--force", "--non-interactive"])

        assert result.exit_code == 0
        assert (empty_dir / ".resume.yaml.bak").exists()
        assert (empty_dir / ".resume.yaml.bak").read_text() == "existing: config"

    def test_init_non_interactive_uses_placeholders(self, empty_dir: Path) -> None:
        """--non-interactive creates config with TODO placeholders."""
        runner = CliRunner()
        result = runner.invoke(main, ["init", "--non-interactive"])

        assert result.exit_code == 0
        content = (empty_dir / ".resume.yaml").read_text()
        assert "TODO:" in content

    def test_init_json_output(self, empty_dir: Path) -> None:
        """--json outputs structured JSON response."""
        runner = CliRunner()
        result = runner.invoke(main, ["--json", "init", "--non-interactive"])

        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert ".resume.yaml" in data["data"]["files_created"]

    def test_init_json_error_on_existing_config(self, empty_dir: Path) -> None:
        """--json outputs JSON error when config exists."""
        (empty_dir / ".resume.yaml").write_text("existing: config")

        runner = CliRunner()
        result = runner.invoke(main, ["--json", "init", "--non-interactive"])

        assert result.exit_code == 1
        import json
        data = json.loads(result.output)
        assert data["status"] == "error"
        assert data["errors"][0]["code"] == "CONFIG_EXISTS"

    def test_init_displays_next_steps(self, empty_dir: Path) -> None:
        """init shows next steps after success."""
        runner = CliRunner()
        result = runner.invoke(main, ["init", "--non-interactive"])

        assert result.exit_code == 0
        assert "resume new position" in result.output
        assert "resume new work-unit" in result.output

    def test_init_positions_yaml_is_empty_list(self, empty_dir: Path) -> None:
        """positions.yaml contains empty list."""
        runner = CliRunner()
        result = runner.invoke(main, ["init", "--non-interactive"])

        assert result.exit_code == 0
        content = (empty_dir / "positions.yaml").read_text()
        assert content.strip() == "[]"


class TestInitInteractive:
    def test_init_prompts_for_name(self, empty_dir: Path) -> None:
        """Interactive mode prompts for required name."""
        runner = CliRunner()
        result = runner.invoke(main, ["init"], input="John Doe\n\n\n\n\n\n\n")

        assert result.exit_code == 0
        content = (empty_dir / ".resume.yaml").read_text()
        assert "John Doe" in content

    def test_init_requires_name(self, empty_dir: Path) -> None:
        """Empty name reprompts."""
        runner = CliRunner()
        # First empty, then valid name
        result = runner.invoke(main, ["init"], input="\nJohn Doe\n\n\n\n\n\n\n")

        assert result.exit_code == 0
        assert "required" in result.output.lower()

    def test_init_saves_all_profile_fields(self, empty_dir: Path) -> None:
        """All profile fields are saved when provided."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["init"],
            input="John Doe\njohn@example.com\n555-1234\nSF, CA\nhttps://linkedin.com/in/john\nhttps://github.com/john\nhttps://john.dev\n",
        )

        assert result.exit_code == 0
        import yaml
        with open(empty_dir / ".resume.yaml") as f:
            config = yaml.safe_load(f)

        assert config["profile"]["name"] == "John Doe"
        assert config["profile"]["email"] == "john@example.com"
        assert config["profile"]["phone"] == "555-1234"
        assert config["profile"]["location"] == "SF, CA"
```

### Project Context Rules

From `project-context.md`:
- Run `ruff check` and `mypy --strict` before completing
- Use Rich console for CLI output, never `print()`
- Type hints required on all public functions
- Use `|` union syntax (Python 3.10+)
- Use `@handle_errors` decorator for consistent error handling
- Use `@pass_context` to access `Context` with json_output, quiet flags
- Follow existing command patterns in `commands/` directory

### CLAUDE.md Updates Required

Add to Quick Reference table:
```markdown
| `resume init` | Initialize new resume project |
| `resume init --non-interactive` | Quick setup with placeholders |
| `resume init --force` | Reinitialize (backs up existing config) |
```

### References

- [Source: src/resume_as_code/cli.py:66-93 - command registration pattern]
- [Source: src/resume_as_code/commands/new.py - Rich prompt patterns]
- [Source: src/resume_as_code/models/config.py - ResumeConfig, ProfileConfig]
- [Source: src/resume_as_code/models/output.py - JSONResponse model]
- [Source: src/resume_as_code/utils/console.py - console helpers]
- [Epic: epic-7-schema-data-model-refactoring.md - Story 7.21]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- RED phase: 17 tests written, all failing (command not found)
- GREEN phase: init command implemented, all 17 tests passing
- REFACTOR phase: Lint fixes (ternary operator), format applied

### Completion Notes List

- Implemented `resume init` command with interactive and non-interactive modes
- Created init.py with all AC requirements: file creation, profile prompts, --force backup, JSON output
- Wired command into cli.py via `_register_commands()`
- All 17 unit tests pass covering all 7 acceptance criteria
- ruff check and mypy --strict pass with zero errors
- Updated CLAUDE.md Quick Reference table with init command entries

### Code Review Fixes (2026-01-17)

**Issues Addressed:**
1. **[HIGH] AC #2 URL Validation** - Added `_is_valid_url()` function and `_prompt_for_url()` helper to validate linkedin, github, website URLs. Invalid URLs now prompt for re-entry.
2. **[MEDIUM] JSON error output consistency** - Changed `_output_json_error()` to use `err_console.print()` instead of `click.echo()` for consistent stream handling
3. **[MEDIUM] Unused parameter** - Removed unused `ctx` parameter from `_output_json_error()` function
4. **[MEDIUM] Inline import** - Removed inline `import click` from `_output_json_error()` (click already imported at module level)
5. **[MEDIUM] Test coverage** - Added 22 new tests for URL validation (9 valid URLs, 9 invalid URLs, 4 interactive validation tests)
6. **[LOW] Docstring** - Added parameter documentation to `_output_json_error()` docstring

**Test Results:** 39 tests passing (17 original + 22 URL validation tests)

### File List

**New files:**
- `src/resume_as_code/commands/init.py` - Init command implementation
- `tests/unit/test_init_command.py` - Unit tests for init command

**Modified files:**
- `src/resume_as_code/cli.py` - Added init_command import and registration
- `CLAUDE.md` - Added init command to Quick Reference table
