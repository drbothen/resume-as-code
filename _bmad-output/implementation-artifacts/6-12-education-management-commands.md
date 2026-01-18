# Story 6.12: Education Management Commands

Status: done

## Story

As a **user**,
I want **interactive commands to manage my education history**,
So that **I can easily add degrees without editing YAML**.

## Acceptance Criteria

1. **Given** I run `resume new education`
   **When** prompted
   **Then** I'm asked for:
     1. Degree/program name (required)
     2. Institution name (required)
     3. Graduation year (YYYY)
     4. Honors/distinction (optional)
     5. GPA (optional)

2. **Given** I complete the education prompts
   **When** the education entry is created
   **Then** it is added to the `education` array in `.resume.yaml`
   **And** confirmation shows: "Added education: BS Computer Science, UT Austin (2012)"

3. **Given** I run `resume list education`
   **When** education entries exist
   **Then** a formatted table shows:
   | Degree | Institution | Year | Honors |
   |--------|-------------|------|--------|
   | BS Computer Science | UT Austin | 2012 | Magna Cum Laude |
   | MS Cybersecurity | Georgia Tech | 2018 | |

4. **Given** I run `resume remove education "BS Computer Science"`
   **When** the education entry exists
   **Then** it is removed from `.resume.yaml`
   **And** confirmation shows: "Removed education: BS Computer Science"

5. **Given** I run `resume show education "BS Computer"`
   **When** education entries match the partial query
   **Then** detailed view shows: degree, institution, year, honors, GPA
   **And** display setting is shown if hidden

6. **Given** I run non-interactively (LLM mode):
   ```bash
   resume new education \
     --degree "Master of Science in Cybersecurity" \
     --institution "Georgia Tech" \
     --year 2018
   ```
   **When** the command executes
   **Then** the education entry is added without prompts

7. **Given** I run `resume --json list education`
   **When** education entries exist
   **Then** JSON output includes all education fields

8. **Given** education entries are rendered on resume
   **When** the user has 10+ years experience
   **Then** education appears after experience (industry standard)
   **And** this ordering is handled by templates, not this story

## Tasks / Subtasks

- [x] Task 1: Create `new education` subcommand (AC: #1, #2, #5)
  - [x] 1.1: Add `education` subcommand to `commands/new.py`
  - [x] 1.2: Implement Rich prompts for interactive input:
    - Degree/program name (required, text prompt)
    - Institution name (required, text prompt)
    - Graduation year (YYYY, validated)
    - Honors/distinction (optional, text)
    - GPA (optional, text)
  - [x] 1.3: Add non-interactive flags: `--degree`, `--institution`, `--year`, `--honors`, `--gpa`
  - [x] 1.4: Implement config file update using EducationService (adapted from story design)
  - [x] 1.5: Display confirmation message with formatted education entry

- [x] Task 2: Create `list education` command (AC: #3, #6)
  - [x] 2.1: Add `list_education()` to `commands/list_cmd.py` (integrated with existing list group)
  - [x] 2.2: Add `list_education()` command function
  - [x] 2.3: Implement Rich table with columns: Degree, Institution, Year, Honors
  - [x] 2.4: Handle empty education list gracefully
  - [x] 2.5: Implement JSON output with all education fields

- [x] Task 3: Create `remove education` command (AC: #4)
  - [x] 3.1: Add `remove_education()` command function to `commands/remove.py`
  - [x] 3.2: Accept degree name as argument
  - [x] 3.3: Search education by degree name (case-insensitive partial match)
  - [x] 3.4: Confirm removal in interactive mode (skip with `--yes`)
  - [x] 3.5: Update `.resume.yaml` with education entry removed
  - [x] 3.6: Display confirmation message

- [x] Task 3.5: Create `show education` command (AC: #5) [Added during code review]
  - [x] 3.5.1: Add `show_education()` command function to `commands/show.py`
  - [x] 3.5.2: Accept degree name as argument (partial match supported)
  - [x] 3.5.3: Implement Rich formatted output with all education fields
  - [x] 3.5.4: Implement JSON output via `--json` flag
  - [x] 3.5.5: Handle not-found and multiple-match cases

- [x] Task 4: Register commands in CLI (AC: all)
  - [x] 4.1: Register `new education` in main CLI group (via @new_group.command decorator)
  - [x] 4.2: Register `list education` in main CLI group (via @list_command.command decorator)
  - [x] 4.3: Register `remove education` in main CLI group (via @remove_group.command decorator)
  - [x] 4.4: Register `show education` in main CLI group (via @show_group.command decorator)
  - [x] 4.5: Add help text for all commands

- [x] Task 5: Extend EducationService (AC: #2, #4)
  - [x] 5.1: `save_education()` method already exists
  - [x] 5.2: Add `remove_education()` method to EducationService
  - [x] 5.3: Add `find_educations_by_degree()` method for partial matching

- [x] Task 5.5: Add empty string validation to Education model [Added during code review]
  - [x] 5.5.1: Add `field_validator` for `degree` and `institution` fields
  - [x] 5.5.2: Reject empty or whitespace-only strings
  - [x] 5.5.3: Strip whitespace from valid values
  - [x] 5.5.4: Add 5 unit tests for validation behavior

- [x] Task 6: Testing (AC: all)
  - [x] 6.1: Add unit tests for education name matching
  - [x] 6.2: Add integration tests for `new education` (interactive mock)
  - [x] 6.3: Add integration tests for `new education` (non-interactive)
  - [x] 6.4: Add integration tests for `list education`
  - [x] 6.5: Add integration tests for `remove education`
  - [x] 6.6: Add integration tests for `show education` [Added during code review]
  - [x] 6.7: Add tests for JSON output format
  - [x] 6.8: Add tests for empty education handling

- [x] Task 7: Code quality verification
  - [x] 7.1: Run `ruff check src tests --fix` - passed
  - [x] 7.2: Run `mypy src --strict` with zero errors - passed
  - [x] 7.3: Run `pytest` - all 1346 tests pass

## Dev Notes

### Architecture Compliance

This story adds CLI commands for managing education entries stored in `.resume.yaml`. It reuses patterns from Story 6.11 (Certification Management Commands) for consistency.

**Critical Rules from project-context.md:**
- Use Click for CLI commands
- Use Rich for console output and prompts
- Use `|` union syntax for optional fields (Python 3.10+)
- Support both interactive and non-interactive modes
- JSON output for programmatic parsing

### Command Structure

```python
# CLI command structure
resume new education              # Interactive mode
resume new education --degree "..." --institution "..." --year 2018
resume list education             # Table output
resume --json list education      # JSON output
resume remove education "BS Computer Science"
```

### Implementation Patterns

#### New Education Command

```python
# src/resume_as_code/commands/new.py (extend existing)

import click
from rich.prompt import Prompt, Confirm
from rich.console import Console

from resume_as_code.models.education import Education
from resume_as_code.services.config_writer import ConfigWriter

console = Console()


@new.command("education")
@click.option("--degree", help="Degree or program name")
@click.option("--institution", help="Institution name")
@click.option("--year", help="Graduation year (YYYY)")
@click.option("--honors", help="Honors or distinction")
@click.option("--gpa", help="GPA (e.g., 3.8/4.0)")
@click.pass_context
def new_education(
    ctx: click.Context,
    degree: str | None,
    institution: str | None,
    year: str | None,
    honors: str | None,
    gpa: str | None,
) -> None:
    """Create a new education entry."""
    non_interactive = ctx.obj.get("non_interactive", False)

    # Interactive prompts if flags not provided
    if not degree:
        if non_interactive:
            raise click.UsageError("--degree is required in non-interactive mode")
        degree = Prompt.ask("Degree/program name")

    if not institution:
        if non_interactive:
            raise click.UsageError("--institution is required in non-interactive mode")
        institution = Prompt.ask("Institution name")

    if not year and not non_interactive:
        year = Prompt.ask("Graduation year (YYYY)", default="")
        year = year or None

    if not honors and not non_interactive:
        honors = Prompt.ask("Honors/distinction", default="")
        honors = honors or None

    if not gpa and not non_interactive:
        gpa = Prompt.ask("GPA", default="")
        gpa = gpa or None

    # Create education entry
    edu = Education(
        degree=degree,
        institution=institution,
        year=year,
        honors=honors,
        gpa=gpa,
    )

    # Add to config
    writer = ConfigWriter()
    writer.add_education(edu)

    # Format confirmation
    confirm_parts = [degree, institution]
    if year:
        confirm_parts.append(f"({year})")
    confirm_msg = ", ".join(confirm_parts[:2])
    if year:
        confirm_msg += f" ({year})"

    console.print(f"[green]Added education: {confirm_msg}[/green]")
```

#### List Education Command

```python
# src/resume_as_code/commands/education.py

import json

import click
from rich.console import Console
from rich.table import Table

from resume_as_code.config import get_config

console = Console()


@click.command("education")
@click.pass_context
def list_education(ctx: click.Context) -> None:
    """List all education entries."""
    config = get_config()
    json_mode = ctx.obj.get("json_mode", False)

    if not config.education:
        if json_mode:
            click.echo('{"status": "success", "data": []}')
        else:
            console.print("[dim]No education entries found.[/dim]")
        return

    if json_mode:
        # JSON output
        data = [edu.model_dump(exclude_none=True) for edu in config.education]
        click.echo(json.dumps({"status": "success", "data": data}, indent=2))
        return

    # Rich table output
    table = Table(title="Education")
    table.add_column("Degree", style="cyan")
    table.add_column("Institution")
    table.add_column("Year")
    table.add_column("Honors")

    for edu in config.education:
        table.add_row(
            edu.degree,
            edu.institution,
            edu.year or "-",
            edu.honors or "-",
        )

    console.print(table)
```

#### Remove Education Command

```python
# src/resume_as_code/commands/education.py (continued)

from rich.prompt import Confirm


@click.command("education")
@click.argument("degree")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def remove_education(ctx: click.Context, degree: str, yes: bool) -> None:
    """Remove an education entry by degree name."""
    config = get_config()

    # Find matching education (case-insensitive)
    matching = [
        e for e in config.education
        if degree.lower() in e.degree.lower()
    ]

    if not matching:
        console.print(f"[red]No education entry found matching '{degree}'[/red]")
        raise SystemExit(4)  # NOT_FOUND

    if len(matching) > 1:
        console.print(f"[yellow]Multiple education entries match '{degree}':[/yellow]")
        for edu in matching:
            console.print(f"  - {edu.degree}")
        console.print("[yellow]Please be more specific.[/yellow]")
        raise SystemExit(1)

    edu = matching[0]

    # Confirm removal
    if not yes:
        if not Confirm.ask(f"Remove education '{edu.degree}'?"):
            console.print("[dim]Cancelled.[/dim]")
            return

    # Remove from config
    writer = ConfigWriter()
    writer.remove_education(edu.degree)

    console.print(f"[green]Removed education: {edu.degree}[/green]")
```

### ConfigWriter Extensions

```python
# src/resume_as_code/services/config_writer.py (extend existing)

from resume_as_code.models.education import Education


class ConfigWriter:
    """Service for updating .resume.yaml configuration."""

    # ... existing methods from Story 6.11 ...

    def add_education(self, edu: Education) -> None:
        """Add education entry to config."""
        data = self._load()

        if "education" not in data:
            data["education"] = []

        # Add education as dict
        edu_dict = edu.model_dump(exclude_none=True)
        # Remove display field if True (default)
        if edu_dict.get("display") is True:
            del edu_dict["display"]
        data["education"].append(edu_dict)

        self._save(data)

    def remove_education(self, degree: str) -> None:
        """Remove education by degree name."""
        data = self._load()

        if "education" not in data:
            return

        data["education"] = [
            e for e in data["education"]
            if e.get("degree", "").lower() != degree.lower()
        ]

        self._save(data)
```

### Dependencies

This story REQUIRES:
- Story 6.6 (Education Model) - Must have Education Pydantic model
- Story 6.11 (Certification Commands) - ConfigWriter service patterns
- Story 1.3 (Configuration) - Config loading infrastructure
- Story 1.2 (Rich Console) - Rich output formatting

This story ENABLES:
- Complete education management without YAML editing
- LLM agents to manage education programmatically

### Files to Create/Modify

**New Files:**
- `src/resume_as_code/commands/education.py` - List and remove commands
- `tests/unit/test_education_commands.py` - Unit tests
- `tests/integration/test_education_commands.py` - Integration tests

**Modified Files:**
- `src/resume_as_code/commands/new.py` - Add `new education` subcommand
- `src/resume_as_code/services/config_writer.py` - Add education methods
- `src/resume_as_code/cli.py` - Register new commands

### Testing Strategy

```python
# tests/unit/test_education_commands.py

import pytest

from resume_as_code.models.education import Education


class TestEducationMatching:
    """Tests for education entry matching."""

    def test_exact_match(self):
        """Should match exact degree name."""
        education = [
            Education(degree="BS Computer Science", institution="MIT"),
            Education(degree="MS Cybersecurity", institution="Georgia Tech"),
        ]
        query = "BS Computer Science"
        matches = [e for e in education if query.lower() in e.degree.lower()]
        assert len(matches) == 1
        assert matches[0].degree == "BS Computer Science"

    def test_partial_match(self):
        """Should match partial degree name."""
        education = [
            Education(degree="BS Computer Science", institution="MIT"),
            Education(degree="MS Cybersecurity", institution="Georgia Tech"),
        ]
        query = "Computer"
        matches = [e for e in education if query.lower() in e.degree.lower()]
        assert len(matches) == 1
        assert matches[0].degree == "BS Computer Science"

    def test_case_insensitive(self):
        """Should match case-insensitively."""
        education = [
            Education(degree="BS Computer Science", institution="MIT"),
        ]
        query = "bs computer science"
        matches = [e for e in education if query.lower() in e.degree.lower()]
        assert len(matches) == 1

    def test_no_match(self):
        """Should return empty for no match."""
        education = [
            Education(degree="BS Computer Science", institution="MIT"),
        ]
        query = "MBA"
        matches = [e for e in education if query.lower() in e.degree.lower()]
        assert len(matches) == 0


class TestEducationFormatting:
    """Tests for education display formatting."""

    def test_format_full(self):
        """Should format with all fields."""
        edu = Education(
            degree="BS Computer Science",
            institution="UT Austin",
            year="2012",
            honors="Magna Cum Laude",
        )
        display = edu.format_display()
        assert "BS Computer Science" in display
        assert "UT Austin" in display
        assert "2012" in display
        assert "Magna Cum Laude" in display

    def test_format_minimal(self):
        """Should format with required fields only."""
        edu = Education(
            degree="MBA",
            institution="Harvard",
        )
        display = edu.format_display()
        assert display == "MBA, Harvard"
```

### Integration Tests

```python
# tests/integration/test_education_commands.py

import pytest
from click.testing import CliRunner

from resume_as_code.cli import cli


class TestNewEducationCommand:
    """Integration tests for new education command."""

    def test_non_interactive_required_fields(self, tmp_path, monkeypatch):
        """Should create education with required flags."""
        monkeypatch.chdir(tmp_path)

        # Create minimal config
        config = tmp_path / ".resume.yaml"
        config.write_text("output_dir: ./dist\n")

        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "education",
            "--degree", "BS Computer Science",
            "--institution", "MIT",
            "--year", "2015",
        ])

        assert result.exit_code == 0
        assert "Added education" in result.output

        # Verify config updated
        content = config.read_text()
        assert "BS Computer Science" in content
        assert "MIT" in content

    def test_non_interactive_all_fields(self, tmp_path, monkeypatch):
        """Should create education with all flags."""
        monkeypatch.chdir(tmp_path)

        config = tmp_path / ".resume.yaml"
        config.write_text("output_dir: ./dist\n")

        runner = CliRunner()
        result = runner.invoke(cli, [
            "new", "education",
            "--degree", "BS Computer Science",
            "--institution", "UT Austin",
            "--year", "2012",
            "--honors", "Magna Cum Laude",
            "--gpa", "3.8/4.0",
        ])

        assert result.exit_code == 0
        content = config.read_text()
        assert "Magna Cum Laude" in content


class TestListEducationCommand:
    """Integration tests for list education command."""

    def test_list_with_entries(self, tmp_path, monkeypatch):
        """Should list education entries in table."""
        monkeypatch.chdir(tmp_path)

        config = tmp_path / ".resume.yaml"
        config.write_text("""
education:
  - degree: "BS Computer Science"
    institution: "MIT"
    year: "2015"
""")

        runner = CliRunner()
        result = runner.invoke(cli, ["list", "education"])

        assert result.exit_code == 0
        assert "BS Computer Science" in result.output
        assert "MIT" in result.output

    def test_list_json_output(self, tmp_path, monkeypatch):
        """Should output JSON with --json flag."""
        monkeypatch.chdir(tmp_path)

        config = tmp_path / ".resume.yaml"
        config.write_text("""
education:
  - degree: "MS Cybersecurity"
    institution: "Georgia Tech"
    year: "2018"
""")

        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "list", "education"])

        assert result.exit_code == 0
        assert '"status": "success"' in result.output
        assert '"degree": "MS Cybersecurity"' in result.output

    def test_list_empty(self, tmp_path, monkeypatch):
        """Should handle empty education list."""
        monkeypatch.chdir(tmp_path)

        config = tmp_path / ".resume.yaml"
        config.write_text("output_dir: ./dist\n")

        runner = CliRunner()
        result = runner.invoke(cli, ["list", "education"])

        assert result.exit_code == 0
        assert "No education entries found" in result.output


class TestRemoveEducationCommand:
    """Integration tests for remove education command."""

    def test_remove_by_name(self, tmp_path, monkeypatch):
        """Should remove education by degree name."""
        monkeypatch.chdir(tmp_path)

        config = tmp_path / ".resume.yaml"
        config.write_text("""
education:
  - degree: "BS Computer Science"
    institution: "MIT"
    year: "2015"
  - degree: "MS Cybersecurity"
    institution: "Georgia Tech"
    year: "2018"
""")

        runner = CliRunner()
        result = runner.invoke(cli, [
            "remove", "education", "BS Computer Science", "--yes"
        ])

        assert result.exit_code == 0
        assert "Removed education" in result.output

        # Verify config updated
        content = config.read_text()
        assert "BS Computer Science" not in content
        assert "MS Cybersecurity" in content
```

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_education_commands.py -v
uv run pytest tests/integration/test_education_commands.py -v

# Manual verification:
# Interactive mode
uv run resume new education

# Non-interactive mode
uv run resume new education \
  --degree "BS Computer Science" \
  --institution "UT Austin" \
  --year 2012 \
  --honors "Magna Cum Laude"

# List education
uv run resume list education
uv run resume --json list education

# Remove education
uv run resume remove education "BS Computer Science"
```

### References

- [Source: epics.md#Story 6.12](_bmad-output/planning-artifacts/epics.md)
- [Story 6.6: Education Model](6-6-education-model-rendering.md)
- [Story 6.11: Certification Management Commands](6-11-certification-management-commands.md) - Reuse patterns

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None - implementation proceeded without issues.

### Completion Notes List

- Task 1 (`new education`) was already implemented in commands/new.py from a previous story
- Task 2 (`list education`) added to commands/list_cmd.py following certification patterns
- Task 3 (`remove education`) added to commands/remove.py following certification patterns
- Task 3.5 (`show education`) added to commands/show.py during code review for CRUD consistency
- Task 5 adapted: Used EducationService instead of ConfigWriter (service already existed with save_education method)
- Added `find_educations_by_degree()` and `remove_education()` methods to EducationService
- Task 5.5: Added empty string validation to Education model (rejects empty/whitespace-only degree and institution)
- All 38 education-specific tests pass (27 original + 6 for show + 5 for validation)
- Full regression suite: 1357 tests pass
- Code quality: ruff check passed, mypy --strict passed
- CLAUDE.md resource coverage table updated to show education as complete

### File List

**Modified Files:**
- `src/resume_as_code/services/education_service.py` - Added `find_educations_by_degree()` and `remove_education()` methods
- `src/resume_as_code/commands/list_cmd.py` - Added `list_education` command and output helpers
- `src/resume_as_code/commands/remove.py` - Added `remove_education` command
- `src/resume_as_code/commands/show.py` - Added `show_education` command [Added during code review]
- `CLAUDE.md` - Updated resource coverage table for education [Added during code review]

**New Files:**
- `tests/unit/test_education_commands.py` - 38 tests for education management commands

**Pre-existing (minor changes):**
- `src/resume_as_code/commands/new.py` - Already had `new education` command
- `src/resume_as_code/models/education.py` - Added empty string validation for degree/institution [Modified during code review]

## Change Log

- 2026-01-12: Implemented education management commands (list, remove) and tests. All ACs satisfied.
- 2026-01-12: Code review expansion - Added `show education` command for CRUD consistency.
- 2026-01-12: Code review fix - Added empty string validation to Education model. All 38 tests pass.
