# Story 2.3: Create Work Unit Command

Status: done

## Story

As a **user**,
I want **to create a new Work Unit with a single command**,
So that **I can capture accomplishments quickly while they're fresh**.

## Acceptance Criteria

1. **Given** I run `resume new work-unit`
   **When** the command executes
   **Then** I am prompted to select an archetype (or use default)
   **And** a new YAML file is created with the naming convention `wu-YYYY-MM-DD-<slug>.yaml`
   **And** my configured editor opens with the scaffolded file

2. **Given** I run `resume new work-unit --archetype incident`
   **When** the command executes
   **Then** the incident archetype template is used
   **And** no archetype prompt is shown

3. **Given** I run `resume new work-unit` and provide a title
   **When** the file is created
   **Then** the slug is derived from the title (lowercase, hyphenated)
   **And** the file is placed in `work-units/` directory

4. **Given** the `work-units/` directory doesn't exist
   **When** I create my first Work Unit
   **Then** the directory is created automatically

5. **Given** I have `$EDITOR` or `$VISUAL` set
   **When** the Work Unit is created
   **Then** that editor opens the file
   **And** if neither is set, a helpful message is shown

## Tasks / Subtasks

- [x] Task 1: Create new command module (AC: #1, #2)
  - [x] 1.1: Create `src/resume_as_code/commands/new.py`
  - [x] 1.2: Implement `resume new` command group
  - [x] 1.3: Implement `resume new work-unit` subcommand
  - [x] 1.4: Add `--archetype` option with archetype choices
  - [x] 1.5: Add `--title` option for specifying title upfront

- [x] Task 2: Create work unit service (AC: #3, #4)
  - [x] 2.1: Create `src/resume_as_code/services/work_unit_service.py`
  - [x] 2.2: Implement `generate_id(title: str, date: date)` function
  - [x] 2.3: Implement `generate_slug(title: str)` function
  - [x] 2.4: Implement `get_work_units_dir()` function
  - [x] 2.5: Implement `create_work_unit_file(archetype: str, title: str)` function
  - [x] 2.6: Handle directory creation if not exists

- [x] Task 3: Implement editor integration (AC: #5)
  - [x] 3.1: Create `src/resume_as_code/utils/editor.py`
  - [x] 3.2: Implement `get_editor()` to check $VISUAL, $EDITOR, config
  - [x] 3.3: Implement `open_in_editor(path: Path)` function
  - [x] 3.4: Handle missing editor gracefully with helpful message

- [x] Task 4: Implement archetype selection (AC: #1, #2)
  - [x] 4.1: If `--archetype` not provided, show selection menu
  - [x] 4.2: List available archetypes with descriptions
  - [x] 4.3: Default to "greenfield" if no selection made
  - [x] 4.4: Support `--archetype` flag to skip selection

- [x] Task 5: Wire command into CLI (AC: #1)
  - [x] 5.1: Register `new` command group in `cli.py`
  - [x] 5.2: Add command help text
  - [x] 5.3: Support `--json` output mode

- [x] Task 6: Code quality verification
  - [x] 6.1: Run `ruff check src tests --fix`
  - [x] 6.2: Run `ruff format src tests`
  - [x] 6.3: Run `mypy src --strict` with zero errors
  - [x] 6.4: Add unit tests for slug generation
  - [x] 6.5: Add integration tests for command

## Dev Notes

### Architecture Compliance

This story implements the primary user-facing command for Work Unit creation. It must integrate with archetypes, configuration, and editor utilities.

**Source:** [Architecture Section 3.3 - CLI Interface Design](_bmad-output/planning-artifacts/architecture.md#33-cli-interface-design)
**Source:** [epics.md#Story 2.3](_bmad-output/planning-artifacts/epics.md)

### Dependencies

This story REQUIRES:
- Story 1.1 (Project Scaffolding) - CLI skeleton
- Story 1.2 (Rich Console) - Output formatting
- Story 1.3 (Configuration) - Config for work_units_dir, editor
- Story 2.1 (Work Unit Schema) - Schema for validation
- Story 2.2 (Archetype Templates) - Templates for scaffolding

### Non-Interactive Mode (FR38)

**CRITICAL:** This command must support non-interactive usage for AI agents.

When `--archetype` and `--title` are provided, no prompts should be shown:

```bash
# Interactive (shows archetype menu)
resume new work-unit

# Non-interactive (no prompts)
resume new work-unit --archetype incident --title "Resolved P1 database outage"
```

### Command Implementation

**`src/resume_as_code/commands/new.py`:**

```python
"""New command for creating Work Units."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import click

from resume_as_code.config import get_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.archetype_service import list_archetypes, load_archetype
from resume_as_code.services.work_unit_service import (
    create_work_unit_file,
    generate_id,
)
from resume_as_code.utils.console import console, success, info
from resume_as_code.utils.editor import get_editor, open_in_editor
from resume_as_code.utils.errors import handle_errors


@click.group("new")
def new_group() -> None:
    """Create new resources."""
    pass


@new_group.command("work-unit")
@click.option(
    "--archetype",
    "-a",
    type=click.Choice(list_archetypes()),
    help="Archetype template to use",
)
@click.option(
    "--title",
    "-t",
    help="Work Unit title (used to generate ID slug)",
)
@click.option(
    "--no-edit",
    is_flag=True,
    help="Don't open editor after creation",
)
@click.pass_context
@handle_errors
def new_work_unit(
    ctx: click.Context,
    archetype: str | None,
    title: str | None,
    no_edit: bool,
) -> None:
    """Create a new Work Unit from an archetype template."""
    config = get_config()

    # Select archetype (interactive if not provided)
    if archetype is None:
        archetype = _select_archetype_interactive(ctx)

    # Get title (interactive if not provided)
    if title is None:
        title = _prompt_title_interactive(ctx)

    # Generate ID and create file
    work_unit_id = generate_id(title, date.today())
    file_path = create_work_unit_file(
        archetype=archetype,
        work_unit_id=work_unit_id,
        title=title,
        work_units_dir=config.work_units_dir,
    )

    # Output result
    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="new work-unit",
            data={
                "id": work_unit_id,
                "file": str(file_path),
                "archetype": archetype,
            },
        )
        click.echo(response.to_json())
    elif not ctx.obj.quiet:
        success(f"Created Work Unit: {work_unit_id}")
        info(f"File: {file_path}")

    # Open in editor
    if not no_edit and not ctx.obj.json_output and not ctx.obj.quiet:
        editor = get_editor(config)
        if editor:
            open_in_editor(file_path, editor)
        else:
            info("Set $EDITOR or $VISUAL to auto-open files")


def _select_archetype_interactive(ctx: click.Context) -> str:
    """Interactively select an archetype."""
    if ctx.obj.json_output or ctx.obj.quiet:
        # Non-interactive mode - use default
        return "greenfield"

    archetypes = list_archetypes()
    console.print("\n[bold]Select an archetype:[/bold]\n")

    for i, name in enumerate(archetypes, 1):
        console.print(f"  {i}. {name}")

    console.print(f"\n  [dim]Default: greenfield[/dim]")

    choice = click.prompt(
        "Choice",
        type=click.IntRange(1, len(archetypes)),
        default=archetypes.index("greenfield") + 1 if "greenfield" in archetypes else 1,
        show_default=False,
    )

    return archetypes[choice - 1]


def _prompt_title_interactive(ctx: click.Context) -> str:
    """Interactively prompt for title."""
    if ctx.obj.json_output or ctx.obj.quiet:
        # Non-interactive mode - use placeholder
        return "untitled-work-unit"

    return click.prompt("Work Unit title")
```

### Work Unit Service

**`src/resume_as_code/services/work_unit_service.py`:**

```python
"""Work Unit service for file operations."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from resume_as_code.services.archetype_service import load_archetype


def generate_slug(title: str) -> str:
    """Generate URL-safe slug from title.

    Examples:
        "Resolved P1 Database Outage" -> "resolved-p1-database-outage"
        "Built ML Pipeline (v2)" -> "built-ml-pipeline-v2"
    """
    # Lowercase
    slug = title.lower()

    # Replace special chars with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)

    # Truncate to reasonable length
    if len(slug) > 50:
        slug = slug[:50].rsplit("-", 1)[0]

    return slug


def generate_id(title: str, today: date) -> str:
    """Generate Work Unit ID from title and date.

    Format: wu-YYYY-MM-DD-slug

    Examples:
        generate_id("Database Migration", date(2024, 3, 15))
        -> "wu-2024-03-15-database-migration"
    """
    slug = generate_slug(title)
    date_str = today.strftime("%Y-%m-%d")
    return f"wu-{date_str}-{slug}"


def get_work_units_dir(base_dir: Path | None = None) -> Path:
    """Get the work units directory, creating if needed."""
    if base_dir is None:
        base_dir = Path.cwd() / "work-units"

    if not base_dir.exists():
        base_dir.mkdir(parents=True)

    return base_dir


def create_work_unit_file(
    archetype: str,
    work_unit_id: str,
    title: str,
    work_units_dir: Path,
) -> Path:
    """Create a new Work Unit file from archetype.

    Returns:
        Path to the created file.
    """
    # Ensure directory exists
    work_units_dir = get_work_units_dir(work_units_dir)

    # Load archetype content
    content = load_archetype(archetype)

    # Replace placeholders
    content = content.replace(
        'id: "wu-YYYY-MM-DD-',
        f'id: "{work_unit_id.rsplit("-", 1)[0]}-',
    )
    content = content.replace("wu-YYYY-MM-DD-", work_unit_id.rsplit("-", 1)[0] + "-")

    # Replace title placeholder if present
    if 'title: "' in content:
        # Find and replace the first title line
        content = re.sub(
            r'title: "[^"]*"',
            f'title: "{title}"',
            content,
            count=1,
        )

    # Write file
    file_path = work_units_dir / f"{work_unit_id}.yaml"
    file_path.write_text(content)

    return file_path
```

### Editor Utility

**`src/resume_as_code/utils/editor.py`:**

```python
"""Editor integration utilities."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from resume_as_code.models.config import ResumeConfig


def get_editor(config: ResumeConfig | None = None) -> str | None:
    """Get the configured editor.

    Priority:
    1. Config file setting
    2. $VISUAL environment variable
    3. $EDITOR environment variable
    4. None (no editor available)
    """
    # Check config
    if config and config.editor:
        return config.editor

    # Check environment
    return os.environ.get("VISUAL") or os.environ.get("EDITOR")


def open_in_editor(path: Path, editor: str) -> None:
    """Open a file in the specified editor.

    Args:
        path: Path to file to open
        editor: Editor command (e.g., "code", "vim", "nano")
    """
    # Handle editors that need special flags
    if editor in ("code", "code-insiders"):
        # VS Code: use --wait to block until closed
        subprocess.run([editor, "--wait", str(path)], check=False)
    elif editor in ("subl", "sublime"):
        # Sublime: use --wait
        subprocess.run([editor, "--wait", str(path)], check=False)
    else:
        # Default: just open the file
        subprocess.run([editor, str(path)], check=False)
```

### CLI Registration

**Update `src/resume_as_code/cli.py`:**

```python
# Add import
from resume_as_code.commands.new import new_group

# Register command group after main
main.add_command(new_group)
```

### Project Structure After This Story

```
src/resume_as_code/
├── commands/
│   ├── __init__.py
│   ├── config_cmd.py
│   └── new.py              # NEW: resume new work-unit
├── services/
│   ├── __init__.py
│   ├── archetype_service.py
│   └── work_unit_service.py  # NEW
└── utils/
    ├── __init__.py
    ├── console.py
    ├── errors.py
    └── editor.py           # NEW
```

### Testing Requirements

**`tests/unit/test_work_unit_service.py`:**

```python
"""Tests for Work Unit service."""

from datetime import date

import pytest

from resume_as_code.services.work_unit_service import (
    generate_id,
    generate_slug,
)


class TestGenerateSlug:
    """Test slug generation."""

    def test_lowercase_conversion(self):
        assert generate_slug("Hello World") == "hello-world"

    def test_special_chars_replaced(self):
        assert generate_slug("ML Pipeline (v2)") == "ml-pipeline-v2"

    def test_multiple_spaces_collapsed(self):
        assert generate_slug("hello   world") == "hello-world"

    def test_leading_trailing_hyphens_removed(self):
        assert generate_slug("--hello--") == "hello"

    def test_long_titles_truncated(self):
        long_title = "a" * 100
        slug = generate_slug(long_title)
        assert len(slug) <= 50


class TestGenerateId:
    """Test Work Unit ID generation."""

    def test_format_correct(self):
        result = generate_id("Database Migration", date(2024, 3, 15))
        assert result == "wu-2024-03-15-database-migration"

    def test_slug_included(self):
        result = generate_id("P1 Incident Response", date(2024, 1, 1))
        assert "p1-incident-response" in result
```

**`tests/integration/test_new_command.py`:**

```python
"""Integration tests for new work-unit command."""

from pathlib import Path

from click.testing import CliRunner

from resume_as_code.cli import main


def test_new_work_unit_creates_file(tmp_path, monkeypatch):
    """Should create work unit file."""
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["new", "work-unit", "--archetype", "greenfield", "--title", "Test Project", "--no-edit"],
    )

    assert result.exit_code == 0
    assert (tmp_path / "work-units").exists()

    files = list((tmp_path / "work-units").glob("*.yaml"))
    assert len(files) == 1
    assert "test-project" in files[0].name


def test_new_work_unit_json_output(tmp_path, monkeypatch):
    """Should output JSON when --json flag used."""
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--json", "new", "work-unit", "--archetype", "incident", "--title", "Outage"],
    )

    assert result.exit_code == 0
    assert '"status": "success"' in result.output
    assert '"archetype": "incident"' in result.output
```

### Verification Commands

```bash
# Test non-interactive creation
resume new work-unit --archetype incident --title "Test Incident" --no-edit

# Verify file created
ls work-units/

# Test with JSON output
resume --json new work-unit --archetype greenfield --title "New Project"

# Interactive mode (will prompt)
resume new work-unit

# Code quality
ruff check src tests --fix
mypy src --strict
pytest tests/unit/test_work_unit_service.py tests/integration/test_new_command.py -v
```

### References

- [Source: architecture.md#Section 3.3 - CLI Interface Design](_bmad-output/planning-artifacts/architecture.md)
- [Source: epics.md#Story 2.3](_bmad-output/planning-artifacts/epics.md)
- [Source: project-context.md](_bmad-output/project-context.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No issues encountered during implementation.

### Completion Notes List

- Implemented `resume new work-unit` command with full archetype and title options
- Created work_unit_service.py with slug generation (handles unicode, special chars, truncation)
- Created editor.py utility with support for VS Code, Sublime, and standard editors
- All 5 acceptance criteria satisfied:
  - AC#1: Interactive archetype selection with numbered menu
  - AC#2: `--archetype` flag bypasses prompt
  - AC#3: Slug derived from title (lowercase, hyphenated)
  - AC#4: work-units directory auto-created if missing
  - AC#5: Editor integration with $VISUAL/$EDITOR fallback and helpful message
- Non-interactive mode supported via `--archetype` + `--title` flags (FR38)
- JSON output mode supported via `--json` flag
- Quiet mode supported via `--quiet` flag
- 331 tests pass including 11 unit tests for slug/id generation and 10 integration tests for command
- All code passes ruff check, ruff format, and mypy --strict

### File List

**New Files:**
- src/resume_as_code/commands/new.py
- src/resume_as_code/services/work_unit_service.py
- src/resume_as_code/utils/editor.py
- tests/unit/test_work_unit_service.py
- tests/unit/test_editor.py (added in code review)
- tests/integration/test_new_command.py

**Modified Files:**
- src/resume_as_code/cli.py (added new_group registration)

### Change Log

- 2026-01-11: Story 2.3 implemented - `resume new work-unit` command with full archetype scaffolding, editor integration, and non-interactive support
- 2026-01-11: Code review completed - Fixed 8 issues (5 MEDIUM, 3 LOW). Added YAML string escaping for special chars, unit tests for editor utility, interactive mode tests, explicit subprocess timeout. Coverage improved 70% → 92%.

