# Story 6.8: Position Management Commands (Human-Friendly UX)

Status: done

## Story

As a **human user building my resume library**,
I want **interactive commands to manage positions**,
So that **I can easily set up my employment history without manually editing YAML**.

## Acceptance Criteria

1. **Given** I run `resume new position`
   **When** prompted
   **Then** I'm asked for:
     1. Employer name
     2. Job title
     3. Location (optional)
     4. Start date (YYYY-MM)
     5. End date (YYYY-MM or blank for current)
     6. Employment type (select from list)
     7. Was this a promotion? (y/n → select previous position if yes)

2. **Given** I complete the position prompts
   **When** the position is created
   **Then** a unique ID is generated: `pos-{employer-slug}-{title-slug}`
   **And** the position is appended to `positions.yaml`
   **And** the position ID is displayed for use in work units

3. **Given** I run `resume list positions`
   **When** positions exist
   **Then** a formatted table shows:
   | ID | Employer | Title | Dates | Type |
   |----|----------|-------|-------|------|
   | pos-techcorp-senior | TechCorp Industries | Senior Platform Engineer | 2022-Present | full-time |

4. **Given** I run `resume new work-unit`
   **When** prompted for position
   **Then** existing positions are listed for selection
   **And** I can choose "Create new position..." to inline-create
   **And** I can choose "No position (personal project)" to skip

5. **Given** a work unit's date range falls within a position's date range
   **When** I run `resume new work-unit --from-memory`
   **Then** the system suggests the matching position
   **And** I can accept or override the suggestion

6. **Given** I run `resume validate`
   **When** work units exist without position_id
   **Then** a warning suggests: "Work unit '{id}' has no position. Consider adding position_id."
   **And** validation still passes (position is optional)

7. **Given** I run `resume show position pos-techcorp-senior`
   **When** the position exists
   **Then** full details are displayed including:
     - Position info
     - List of work units referencing this position
     - Promotion chain (if part of one)

## Tasks / Subtasks

- [x] Task 1: Create `resume new position` command (AC: #1, #2)
  - [x] 1.1: Add `position` subcommand to `new` command group
  - [x] 1.2: Implement Rich prompts for each field
  - [x] 1.3: Add employer name prompt (required)
  - [x] 1.4: Add job title prompt (required)
  - [x] 1.5: Add location prompt (optional)
  - [x] 1.6: Add start date prompt with validation
  - [x] 1.7: Add end date prompt (blank for current)
  - [x] 1.8: Add employment type select from list
  - [x] 1.9: Add promotion question with position selection
  - [x] 1.10: Generate position ID from employer/title slugs
  - [x] 1.11: Save to positions.yaml via PositionService

- [x] Task 2: Create `resume list positions` command (AC: #3)
  - [x] 2.1: Add `positions` subcommand to `list` command group
  - [x] 2.2: Load positions via PositionService
  - [x] 2.3: Display as Rich table
  - [x] 2.4: Show ID, employer, title, dates, type columns
  - [x] 2.5: Sort by start_date descending (most recent first)

- [x] Task 3: Create `resume show position` command (AC: #7)
  - [x] 3.1: Add `position` subcommand to `show` command group (or new group)
  - [x] 3.2: Load position by ID
  - [x] 3.3: Display full position details
  - [x] 3.4: Find and list work units referencing this position
  - [x] 3.5: Show promotion chain if part of one

- [x] Task 4: Update `resume new work-unit` for position selection (AC: #4, #5)
  - [x] 4.1: Add position selection prompt to work-unit creation
  - [x] 4.2: List existing positions as options
  - [x] 4.3: Add "Create new position..." option
  - [x] 4.4: Add "No position (personal project)" option
  - [x] 4.5: Implement date-based position suggestion
  - [x] 4.6: Set position_id on created work unit

- [x] Task 5: Update validate command (AC: #6)
  - [x] 5.1: Add check for work units without position_id
  - [x] 5.2: Display warning (not error) for missing position
  - [x] 5.3: Ensure validation still passes

- [x] Task 6: ID generation utility
  - [x] 6.1: Create `slugify()` utility function
  - [x] 6.2: Generate `pos-{employer-slug}-{title-slug}` format
  - [x] 6.3: Handle duplicates (append number if needed)

- [x] Task 7: Testing
  - [x] 7.1: Add tests for new position command
  - [x] 7.2: Add tests for list positions command
  - [x] 7.3: Add tests for show position command
  - [x] 7.4: Add tests for position selection in new work-unit
  - [x] 7.5: Add tests for ID generation

- [x] Task 8: Code quality verification
  - [x] 8.1: Run `ruff check src tests --fix`
  - [x] 8.2: Run `mypy src --strict` with zero errors
  - [x] 8.3: Run `pytest` - all tests pass

## Dev Notes

### Architecture Compliance

This story implements FR45 (position management commands) with human-friendly interactive UX. It follows the command patterns established in Epic 2 (Work Unit Creation).

**Critical Rules from project-context.md:**
- Never use `print()` - use Rich console
- Use Rich prompts for interactive input
- Commands should be thin, delegate to services
- Support `--non-interactive` fallback for CI/scripting

### New Position Command Flow

```python
# src/resume_as_code/commands/new.py - extend existing

@new.command("position")
@click.pass_context
@handle_errors
def new_position(ctx: click.Context) -> None:
    """Create a new employment position interactively."""
    from rich.prompt import Prompt, Confirm

    console.print("[bold]Create New Position[/]\n")

    # Required fields
    employer = Prompt.ask("Employer name")
    title = Prompt.ask("Job title")

    # Optional fields
    location = Prompt.ask("Location (city, state)", default="")
    location = location if location else None

    # Date prompts
    start_date = Prompt.ask(
        "Start date (YYYY-MM)",
        default=datetime.now().strftime("%Y-%m"),
    )

    is_current = Confirm.ask("Is this your current position?", default=True)
    end_date = None
    if not is_current:
        end_date = Prompt.ask("End date (YYYY-MM)")

    # Employment type selection
    console.print("\n[bold]Employment Type:[/]")
    types = ["full-time", "part-time", "contract", "consulting", "freelance"]
    for i, t in enumerate(types, 1):
        console.print(f"  {i}. {t}")
    type_choice = Prompt.ask("Select type", choices=[str(i) for i in range(1, 6)])
    employment_type = types[int(type_choice) - 1]

    # Promotion check
    promoted_from = None
    if Confirm.ask("\nWas this a promotion from a previous position?", default=False):
        # Load existing positions and let user select
        service = PositionService()
        positions = service.load_positions()
        if positions:
            console.print("\n[bold]Select previous position:[/]")
            pos_list = list(positions.values())
            for i, pos in enumerate(pos_list, 1):
                console.print(f"  {i}. {pos.title} at {pos.employer}")
            prev_choice = Prompt.ask("Select position", choices=[str(i) for i in range(1, len(pos_list) + 1)])
            promoted_from = pos_list[int(prev_choice) - 1].id

    # Generate ID
    position_id = generate_position_id(employer, title)

    # Create and save position
    position = Position(
        id=position_id,
        employer=employer,
        title=title,
        location=location,
        start_date=start_date,
        end_date=end_date,
        employment_type=employment_type,
        promoted_from=promoted_from,
    )

    service = PositionService()
    service.save_position(position)

    console.print(f"\n[green]✓[/] Position created: [cyan]{position_id}[/]")
    console.print(f"[dim]Use this ID in work units: position_id: {position_id}[/]")
```

### List Positions Command

```python
# src/resume_as_code/commands/list.py - extend existing

@list_cmd.command("positions")
@click.pass_context
@handle_errors
def list_positions(ctx: click.Context) -> None:
    """List all employment positions."""
    from rich.table import Table

    service = PositionService()
    positions = service.load_positions()

    if not positions:
        console.print("[yellow]No positions found.[/]")
        console.print("[dim]Create one with: resume new position[/]")
        return

    table = Table(title="Employment Positions")
    table.add_column("ID", style="cyan")
    table.add_column("Employer", style="green")
    table.add_column("Title")
    table.add_column("Dates")
    table.add_column("Type", style="dim")

    # Sort by start_date descending
    sorted_positions = sorted(
        positions.values(),
        key=lambda p: p.start_date,
        reverse=True,
    )

    for pos in sorted_positions:
        dates = pos.format_date_range()
        table.add_row(
            pos.id,
            pos.employer,
            pos.title,
            dates,
            pos.employment_type or "",
        )

    console.print(table)
```

### Show Position Command

```python
# src/resume_as_code/commands/show.py (new file or extend existing)

@click.command("position")
@click.argument("position_id")
@click.pass_context
@handle_errors
def show_position(ctx: click.Context, position_id: str) -> None:
    """Show details of a specific position."""
    service = PositionService()
    position = service.get_position(position_id)

    if not position:
        raise ResourceNotFoundError(f"Position not found: {position_id}")

    # Display position details
    console.print(f"\n[bold cyan]{position.title}[/]")
    console.print(f"[green]{position.employer}[/]")
    if position.location:
        console.print(f"[dim]{position.location}[/]")
    console.print(f"\n{position.format_date_range()}")
    if position.employment_type:
        console.print(f"Type: {position.employment_type}")

    # Show work units referencing this position
    work_units = load_all_work_units(Path("work-units"))
    related_wus = [wu for wu in work_units if wu.position_id == position_id]

    if related_wus:
        console.print(f"\n[bold]Work Units ({len(related_wus)}):[/]")
        for wu in related_wus:
            console.print(f"  • {wu.id}: {wu.title[:50]}...")
    else:
        console.print("\n[dim]No work units reference this position[/]")

    # Show promotion chain
    chain = service.get_promotion_chain(position_id)
    if len(chain) > 1:
        console.print("\n[bold]Career Progression:[/]")
        for i, pos in enumerate(chain):
            prefix = "  └─" if i == len(chain) - 1 else "  ├─"
            marker = " [cyan](current)[/]" if pos.id == position_id else ""
            console.print(f"{prefix} {pos.title}{marker}")
```

### Position Selection in Work Unit Creation

```python
# Update resume new work-unit to include position selection

def prompt_for_position() -> str | None:
    """Prompt user to select or create a position."""
    service = PositionService()
    positions = service.load_positions()

    options = []
    if positions:
        # Add existing positions as options
        sorted_positions = sorted(
            positions.values(),
            key=lambda p: p.start_date,
            reverse=True,
        )
        for pos in sorted_positions:
            options.append((pos.id, f"{pos.title} at {pos.employer}"))

    # Always add these options
    options.append(("__new__", "Create new position..."))
    options.append(("__none__", "No position (personal project)"))

    console.print("\n[bold]Select Position:[/]")
    for i, (_, label) in enumerate(options, 1):
        console.print(f"  {i}. {label}")

    choice = Prompt.ask(
        "Select option",
        choices=[str(i) for i in range(1, len(options) + 1)],
    )
    selected_id, _ = options[int(choice) - 1]

    if selected_id == "__new__":
        # Inline create new position
        # ... call new_position logic ...
        return new_position_id
    elif selected_id == "__none__":
        return None
    else:
        return selected_id
```

### ID Generation Utility

```python
# src/resume_as_code/utils/slugify.py

import re
import unicodedata


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug.

    Examples:
        "TechCorp Industries" -> "techcorp-industries"
        "Senior Platform Engineer" -> "senior-platform-engineer"
    """
    # Normalize unicode characters
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Convert to lowercase
    text = text.lower()

    # Replace spaces and special chars with hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)

    # Remove leading/trailing hyphens
    return text.strip("-")


def generate_position_id(employer: str, title: str) -> str:
    """Generate unique position ID.

    Format: pos-{employer-slug}-{title-slug}
    Example: pos-techcorp-senior-platform-engineer
    """
    employer_slug = slugify(employer)[:20]  # Limit length
    title_slug = slugify(title)[:20]

    return f"pos-{employer_slug}-{title_slug}"
```

### Dependencies

This story REQUIRES:
- Story 6.7 (Positions Data Model) - Position model and service
- Story 2.3 (Create Work Unit Command) - Command patterns [DONE]

This story ENABLES:
- Story 6.9 (Inline Position Creation) - LLM-optimized UX
- Human-friendly position management

### Files to Create/Modify

**New Files:**
- `src/resume_as_code/utils/slugify.py` - Slug generation utility
- `src/resume_as_code/commands/show.py` - Show command (if not exists)
- `tests/unit/test_position_commands.py` - Command tests

**Modified Files:**
- `src/resume_as_code/commands/new.py` - Add `new position` subcommand
- `src/resume_as_code/commands/list.py` - Add `list positions` subcommand
- `src/resume_as_code/commands/validate.py` - Add position warnings
- `src/resume_as_code/cli.py` - Register new commands

### Testing Strategy

```python
# tests/unit/test_position_commands.py

import pytest
from click.testing import CliRunner

from resume_as_code.cli import cli


class TestNewPositionCommand:
    """Tests for new position command."""

    def test_creates_position_interactively(self, tmp_path, monkeypatch):
        """Should create position through prompts."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Simulate interactive input
        result = runner.invoke(
            cli,
            ["new", "position"],
            input="Test Corp\nEngineer\nAustin, TX\n2022-01\ny\n1\nn\n",
        )

        assert result.exit_code == 0
        assert "Position created" in result.output

        # Verify positions.yaml created
        assert (tmp_path / "positions.yaml").exists()


class TestListPositionsCommand:
    """Tests for list positions command."""

    def test_lists_positions_table(self, tmp_path, monkeypatch):
        """Should display positions in table format."""
        monkeypatch.chdir(tmp_path)

        # Create positions.yaml
        (tmp_path / "positions.yaml").write_text("""
schema_version: "1.0.0"
positions:
  pos-test:
    employer: "Test Corp"
    title: "Engineer"
    start_date: "2022-01"
""")

        runner = CliRunner()
        result = runner.invoke(cli, ["list", "positions"])

        assert result.exit_code == 0
        assert "Test Corp" in result.output
        assert "Engineer" in result.output

    def test_empty_positions_message(self, tmp_path, monkeypatch):
        """Should show message when no positions."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(cli, ["list", "positions"])

        assert "No positions found" in result.output


class TestShowPositionCommand:
    """Tests for show position command."""

    def test_shows_position_details(self, tmp_path, monkeypatch):
        """Should display position details."""
        pass

    def test_shows_related_work_units(self, tmp_path, monkeypatch):
        """Should list work units referencing position."""
        pass

    def test_shows_promotion_chain(self, tmp_path, monkeypatch):
        """Should display career progression."""
        pass


class TestSlugify:
    """Tests for slug generation."""

    def test_basic_slugify(self):
        from resume_as_code.utils.slugify import slugify

        assert slugify("TechCorp Industries") == "techcorp-industries"
        assert slugify("Senior Platform Engineer") == "senior-platform-engineer"

    def test_special_characters(self):
        from resume_as_code.utils.slugify import slugify

        assert slugify("O'Reilly & Associates") == "oreilly-associates"

    def test_position_id_generation(self):
        from resume_as_code.utils.slugify import generate_position_id

        result = generate_position_id("TechCorp", "Senior Engineer")
        assert result == "pos-techcorp-senior-engineer"
```

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_position_commands.py -v

# Manual verification:
uv run resume new position
# Follow prompts to create position

uv run resume list positions
# Should show table of positions

uv run resume show position pos-techcorp-senior
# Should show position details

uv run resume new work-unit
# Should prompt for position selection
```

### References

- [Source: epics.md#Story 6.8](_bmad-output/planning-artifacts/epics.md)
- [Related: Story 6.7 Positions Data Model](_bmad-output/implementation-artifacts/6-7-positions-data-model-employment-history.md)
- [Related: Story 2.3 Create Work Unit Command](_bmad-output/implementation-artifacts/2-3-create-work-unit-command.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- All 7 acceptance criteria implemented and tested
- AC#5 (date-based position suggestion) implemented via `suggest_position_for_date()` method
- Position commands integrated with existing CLI structure
- Consistent UX across all prompts (location prompt wording unified)
- Comprehensive test coverage for all commands and utilities

### File List

**New Files:**
- `src/resume_as_code/utils/slugify.py` - Slug generation and position ID utilities
- `src/resume_as_code/commands/show.py` - Show command group with position subcommand
- `tests/unit/test_position_commands.py` - CLI command tests
- `tests/unit/test_slugify.py` - Slug utility tests

**Modified Files:**
- `src/resume_as_code/commands/new.py` - Added `new position` subcommand, position selection in work-unit creation
- `src/resume_as_code/commands/list_cmd.py` - Added `list positions` subcommand
- `src/resume_as_code/commands/validate.py` - Added position reference warnings
- `src/resume_as_code/services/position_service.py` - Added `suggest_position_for_date()` method
- `src/resume_as_code/services/content_validator.py` - Added position validation
- `src/resume_as_code/cli.py` - Registered show command group
- `tests/unit/test_position_service.py` - Added date suggestion tests
