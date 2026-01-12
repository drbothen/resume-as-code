# Story 6.9: Inline Position Creation (LLM-Optimized UX)

Status: ready-for-dev

## Story

As an **AI agent (Claude Code) helping a user build their resume**,
I want **non-interactive flags to create positions and work units in one command**,
So that **I can efficiently build the resume library without interactive prompts**.

## Acceptance Criteria

1. **Given** I run:
   ```bash
   resume new work-unit \
     --position "TechCorp Industries|Senior Engineer|2022-01|" \
     --title "Led ICS security assessment" \
     --archetype incident
   ```
   **When** the position doesn't exist
   **Then** a new position is auto-created in positions.yaml
   **And** the work unit is created referencing the new position
   **And** both IDs are returned in output

2. **Given** the position "TechCorp Industries + Senior Engineer" already exists
   **When** I use the `--position` flag with the same employer/title
   **Then** the existing position is reused (no duplicate created)
   **And** the work unit references the existing position

3. **Given** I want to reference an existing position by ID
   **When** I run:
   ```bash
   resume new work-unit \
     --position-id pos-techcorp-senior \
     --title "Architected hybrid platform"
   ```
   **Then** the work unit is created referencing that position
   **And** an error is shown if the position ID doesn't exist

4. **Given** I run with JSON output:
   ```bash
   resume --json new work-unit --position "Company|Title|2023-01|2024-01"
   ```
   **When** the command succeeds
   **Then** JSON output includes:
   ```json
   {
     "status": "success",
     "data": {
       "work_unit_id": "wu-2024-01-30-ics-assessment",
       "position_id": "pos-company-title",
       "position_created": true,
       "file_path": "work-units/wu-2024-01-30-ics-assessment.yaml"
     }
   }
   ```

5. **Given** I run `resume new position` non-interactively:
   ```bash
   resume new position \
     --employer "Acme Corp" \
     --title "Security Consultant" \
     --location "Remote" \
     --start-date 2018-03 \
     --end-date 2020-05 \
     --employment-type contract
   ```
   **When** the command executes
   **Then** the position is created without prompts
   **And** the position ID is returned

6. **Given** I'm creating a position that was a promotion
   **When** I run:
   ```bash
   resume new position \
     --employer "TechCorp" \
     --title "Senior Engineer" \
     --start-date 2022-01 \
     --promoted-from pos-techcorp-engineer
   ```
   **Then** the `promoted_from` field is set
   **And** career progression is tracked

7. **Given** I want to list positions programmatically
   **When** I run `resume --json list positions`
   **Then** positions are returned as a JSON array
   **And** includes all fields for each position

## Tasks / Subtasks

- [ ] Task 1: Add --position flag to new work-unit (AC: #1, #2)
  - [ ] 1.1: Add `--position` option with pipe-separated format
  - [ ] 1.2: Parse format: "Employer|Title|StartDate|EndDate"
  - [ ] 1.3: Implement position matching (find existing by employer+title)
  - [ ] 1.4: Auto-create position if not found
  - [ ] 1.5: Set position_id on work unit
  - [ ] 1.6: Return both IDs in output

- [ ] Task 2: Add --position-id flag to new work-unit (AC: #3)
  - [ ] 2.1: Add `--position-id` option
  - [ ] 2.2: Validate position exists
  - [ ] 2.3: Show clear error if not found
  - [ ] 2.4: Set position_id on work unit

- [ ] Task 3: Add JSON output for work-unit creation (AC: #4)
  - [ ] 3.1: Detect --json global flag
  - [ ] 3.2: Return structured JSON response
  - [ ] 3.3: Include work_unit_id, position_id, position_created, file_path
  - [ ] 3.4: Suppress Rich output in JSON mode

- [ ] Task 4: Add non-interactive flags to new position (AC: #5, #6)
  - [ ] 4.1: Add `--employer` option (required in non-interactive)
  - [ ] 4.2: Add `--title` option (required in non-interactive)
  - [ ] 4.3: Add `--location` option
  - [ ] 4.4: Add `--start-date` option
  - [ ] 4.5: Add `--end-date` option
  - [ ] 4.6: Add `--employment-type` option
  - [ ] 4.7: Add `--promoted-from` option
  - [ ] 4.8: Detect non-interactive mode (all required flags provided)
  - [ ] 4.9: Skip prompts when non-interactive

- [ ] Task 5: Add JSON output for list positions (AC: #7)
  - [ ] 5.1: Detect --json global flag
  - [ ] 5.2: Return positions as JSON array
  - [ ] 5.3: Include all position fields
  - [ ] 5.4: Suppress Rich table in JSON mode

- [ ] Task 6: Position matching logic
  - [ ] 6.1: Implement case-insensitive employer+title matching
  - [ ] 6.2: Normalize strings for comparison
  - [ ] 6.3: Return existing position if match found

- [ ] Task 7: Testing
  - [ ] 7.1: Add tests for --position flag parsing
  - [ ] 7.2: Add tests for position auto-creation
  - [ ] 7.3: Add tests for position reuse
  - [ ] 7.4: Add tests for --position-id validation
  - [ ] 7.5: Add tests for JSON output format
  - [ ] 7.6: Add tests for non-interactive position creation

- [ ] Task 8: Code quality verification
  - [ ] 8.1: Run `ruff check src tests --fix`
  - [ ] 8.2: Run `mypy src --strict` with zero errors
  - [ ] 8.3: Run `pytest` - all tests pass

## Dev Notes

### Architecture Compliance

This story implements FR46 (inline position creation for LLM UX) enabling AI agents to efficiently create resume content without interactive prompts. This is critical for Claude Code workflows.

**Critical Rules from project-context.md:**
- Support `--json` flag for structured output
- All commands must work non-interactively for CI/scripting
- Return proper exit codes and error messages

### --position Flag Format

```
--position "Employer|Title|StartDate|EndDate"
```

- **Pipe-separated** (not comma, which appears in employer names)
- **EndDate** can be empty for current position
- **Examples:**
  - `"TechCorp Industries|Senior Engineer|2022-01|"` (current)
  - `"Acme Corp|Consultant|2018-03|2020-05"` (ended)

### Parsing Logic

```python
def parse_position_flag(value: str) -> dict:
    """Parse --position flag value.

    Format: "Employer|Title|StartDate|EndDate"
    EndDate can be empty for current position.
    """
    parts = value.split("|")
    if len(parts) != 4:
        raise click.BadParameter(
            "Position must be in format: 'Employer|Title|StartDate|EndDate'"
        )

    employer, title, start_date, end_date = parts
    return {
        "employer": employer.strip(),
        "title": title.strip(),
        "start_date": start_date.strip(),
        "end_date": end_date.strip() or None,
    }
```

### Position Matching

```python
def find_existing_position(
    employer: str,
    title: str,
    positions: dict[str, Position],
) -> Position | None:
    """Find existing position by employer and title.

    Case-insensitive, whitespace-normalized matching.
    """
    employer_lower = employer.lower().strip()
    title_lower = title.lower().strip()

    for pos in positions.values():
        if (
            pos.employer.lower().strip() == employer_lower
            and pos.title.lower().strip() == title_lower
        ):
            return pos

    return None
```

### Updated new work-unit Command

```python
@new.command("work-unit")
@click.option(
    "--position",
    "position_spec",
    help="Create/reuse position: 'Employer|Title|StartDate|EndDate'",
)
@click.option(
    "--position-id",
    help="Reference existing position by ID",
)
@click.option("--title", help="Work unit title")
@click.option("--archetype", help="Archetype template to use")
# ... other existing options ...
@click.pass_context
@handle_errors
def new_work_unit(
    ctx: click.Context,
    position_spec: str | None,
    position_id: str | None,
    title: str | None,
    archetype: str | None,
    # ...
) -> None:
    """Create a new work unit."""
    json_mode = ctx.obj.get("json_mode", False)
    position_service = PositionService()

    # Handle position
    actual_position_id: str | None = None
    position_created = False

    if position_spec and position_id:
        raise click.UsageError("Cannot use both --position and --position-id")

    if position_id:
        # Validate existing position
        if not position_service.position_exists(position_id):
            raise ResourceNotFoundError(f"Position not found: {position_id}")
        actual_position_id = position_id

    elif position_spec:
        # Parse and find/create position
        pos_data = parse_position_flag(position_spec)
        positions = position_service.load_positions()
        existing = find_existing_position(
            pos_data["employer"],
            pos_data["title"],
            positions,
        )

        if existing:
            actual_position_id = existing.id
        else:
            # Create new position
            new_pos = Position(
                id=generate_position_id(pos_data["employer"], pos_data["title"]),
                employer=pos_data["employer"],
                title=pos_data["title"],
                start_date=pos_data["start_date"],
                end_date=pos_data["end_date"],
            )
            position_service.save_position(new_pos)
            actual_position_id = new_pos.id
            position_created = True

    # Create work unit with position_id
    work_unit = create_work_unit(
        title=title,
        archetype=archetype,
        position_id=actual_position_id,
        # ...
    )

    # Output
    if json_mode:
        output_json({
            "status": "success",
            "data": {
                "work_unit_id": work_unit.id,
                "position_id": actual_position_id,
                "position_created": position_created,
                "file_path": str(work_unit_path),
            },
        })
    else:
        console.print(f"[green]✓[/] Work unit created: {work_unit.id}")
        if position_created:
            console.print(f"[green]✓[/] Position created: {actual_position_id}")
        elif actual_position_id:
            console.print(f"[dim]Using position: {actual_position_id}[/]")
```

### Non-Interactive new position

```python
@new.command("position")
@click.option("--employer", help="Employer name")
@click.option("--title", help="Job title")
@click.option("--location", help="Location (city, state)")
@click.option("--start-date", help="Start date (YYYY-MM)")
@click.option("--end-date", help="End date (YYYY-MM) or blank for current")
@click.option(
    "--employment-type",
    type=click.Choice(["full-time", "part-time", "contract", "consulting", "freelance"]),
    help="Employment type",
)
@click.option("--promoted-from", help="Position ID this was promoted from")
@click.pass_context
@handle_errors
def new_position(
    ctx: click.Context,
    employer: str | None,
    title: str | None,
    location: str | None,
    start_date: str | None,
    end_date: str | None,
    employment_type: str | None,
    promoted_from: str | None,
) -> None:
    """Create a new employment position."""
    json_mode = ctx.obj.get("json_mode", False)

    # Determine interactive vs non-interactive mode
    non_interactive = employer is not None and title is not None and start_date is not None

    if non_interactive:
        # Non-interactive mode - use provided values
        position = Position(
            id=generate_position_id(employer, title),
            employer=employer,
            title=title,
            location=location,
            start_date=start_date,
            end_date=end_date or None,
            employment_type=employment_type,
            promoted_from=promoted_from,
        )
    else:
        # Interactive mode - prompt for values
        position = prompt_for_position_details()

    # Save position
    service = PositionService()
    service.save_position(position)

    # Output
    if json_mode:
        output_json({
            "status": "success",
            "data": {
                "position_id": position.id,
                "employer": position.employer,
                "title": position.title,
            },
        })
    else:
        console.print(f"[green]✓[/] Position created: [cyan]{position.id}[/]")
```

### JSON Output for list positions

```python
@list_cmd.command("positions")
@click.pass_context
@handle_errors
def list_positions(ctx: click.Context) -> None:
    """List all employment positions."""
    json_mode = ctx.obj.get("json_mode", False)
    service = PositionService()
    positions = service.load_positions()

    if json_mode:
        output_json({
            "status": "success",
            "data": {
                "positions": [
                    pos.model_dump(exclude_none=True)
                    for pos in positions.values()
                ],
            },
        })
        return

    # Rich table output (existing code)
    # ...
```

### Dependencies

This story REQUIRES:
- Story 6.7 (Positions Data Model) - Position model and service
- Story 6.8 (Position Management Commands) - Base commands

This story ENABLES:
- Story 6.10 (CLAUDE.md Documentation) - Document these workflows
- Efficient AI-assisted resume building

### Files to Modify

**Modified Files:**
- `src/resume_as_code/commands/new.py` - Add flags to new work-unit and new position
- `src/resume_as_code/commands/list.py` - Add JSON output to list positions
- `src/resume_as_code/services/position_service.py` - Add find_existing_position()

**New Files:**
- `tests/unit/test_inline_position.py` - Tests for inline creation

### Testing Strategy

```python
# tests/unit/test_inline_position.py

import pytest
from click.testing import CliRunner

from resume_as_code.cli import cli


class TestInlinePositionCreation:
    """Tests for inline position creation."""

    def test_creates_position_with_work_unit(self, tmp_path, monkeypatch):
        """Should create position when using --position flag."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new", "work-unit",
                "--position", "TechCorp|Engineer|2022-01|",
                "--title", "Test achievement",
                "--from-memory",
            ],
        )

        assert result.exit_code == 0
        assert "Position created" in result.output
        assert (tmp_path / "positions.yaml").exists()

    def test_reuses_existing_position(self, tmp_path, monkeypatch):
        """Should reuse position if employer+title match."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        # Create initial position
        (tmp_path / "positions.yaml").write_text("""
schema_version: "1.0.0"
positions:
  pos-techcorp-engineer:
    employer: "TechCorp"
    title: "Engineer"
    start_date: "2022-01"
""")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new", "work-unit",
                "--position", "TechCorp|Engineer|2022-01|",
                "--title", "Another achievement",
                "--from-memory",
            ],
        )

        assert result.exit_code == 0
        assert "Position created" not in result.output
        assert "Using position: pos-techcorp-engineer" in result.output

    def test_position_id_validation(self, tmp_path, monkeypatch):
        """Should error if --position-id doesn't exist."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new", "work-unit",
                "--position-id", "pos-nonexistent",
                "--title", "Test",
            ],
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_json_output_format(self, tmp_path, monkeypatch):
        """Should return structured JSON."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--json",
                "new", "work-unit",
                "--position", "Company|Title|2023-01|",
                "--title", "Test",
                "--from-memory",
            ],
        )

        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert "work_unit_id" in data["data"]
        assert "position_id" in data["data"]
        assert "position_created" in data["data"]


class TestNonInteractivePosition:
    """Tests for non-interactive position creation."""

    def test_creates_position_with_flags(self, tmp_path, monkeypatch):
        """Should create position without prompts."""
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "new", "position",
                "--employer", "Acme Corp",
                "--title", "Consultant",
                "--start-date", "2018-03",
                "--end-date", "2020-05",
                "--employment-type", "contract",
            ],
        )

        assert result.exit_code == 0
        assert "Position created" in result.output

    def test_json_list_positions(self, tmp_path, monkeypatch):
        """Should return JSON array of positions."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "positions.yaml").write_text("""
schema_version: "1.0.0"
positions:
  pos-test:
    employer: "Test"
    title: "Role"
    start_date: "2022-01"
""")

        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "list", "positions"])

        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert len(data["data"]["positions"]) == 1
```

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_inline_position.py -v

# Manual verification (LLM workflow):
uv run resume new work-unit \
  --position "TechCorp|Senior Engineer|2022-01|" \
  --title "Led platform migration" \
  --from-memory

uv run resume --json new work-unit \
  --position "Acme|Consultant|2020-01|2022-01" \
  --title "Delivered security audit"

uv run resume new position \
  --employer "StartupCo" \
  --title "CTO" \
  --start-date 2023-06 \
  --employment-type full-time

uv run resume --json list positions
```

### References

- [Source: epics.md#Story 6.9](_bmad-output/planning-artifacts/epics.md)
- [Related: Story 6.8 Position Management Commands](_bmad-output/implementation-artifacts/6-8-position-management-commands.md)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
