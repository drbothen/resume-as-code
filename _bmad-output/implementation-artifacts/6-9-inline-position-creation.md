# Story 6.9: Inline Position Creation (LLM-Optimized UX)

Status: done

## Story

As an **AI agent (Claude Code) helping a user build their resume**,
I want **non-interactive flags to create positions, certifications, education, and work units**,
So that **I can efficiently build the resume library without interactive prompts**.

### Extended Scope (Phase 2)

This story was extended to support inline creation for all data models:
- **Positions** (stored in `positions.yaml`)
- **Certifications** (stored in `.resume.yaml`)
- **Education** (stored in `.resume.yaml`)

### Extended Scope (Phase 3)

Full inline work unit creation - create complete work units without editing template files:
- **Work Units** with `--problem`, `--action`, `--result` flags
- Optional `--skill`, `--tag`, `--impact`, `--start-date`, `--end-date`

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

### Extended Acceptance Criteria (Phase 2 - Certifications & Education)

8. **Given** I run `resume new certification` non-interactively:
   ```bash
   resume new certification \
     --name "AWS Solutions Architect" \
     --issuer "Amazon Web Services" \
     --date 2023-06 \
     --expires 2026-06
   ```
   **When** the command executes
   **Then** the certification is added to `.resume.yaml`
   **And** duplicate detection prevents re-adding same cert

9. **Given** I run `resume new education` non-interactively:
   ```bash
   resume new education \
     --degree "BS Computer Science" \
     --institution "MIT" \
     --year 2015 \
     --honors "Magna Cum Laude"
   ```
   **When** the command executes
   **Then** the education record is added to `.resume.yaml`
   **And** duplicate detection prevents re-adding same degree+institution

10. **Given** I run with JSON output:
    ```bash
    resume --json new certification --name "CISSP" --issuer "ISC2"
    ```
    **When** the command succeeds
    **Then** JSON output includes:
    ```json
    {
      "status": "success",
      "data": {
        "certification_created": true,
        "name": "CISSP",
        "issuer": "ISC2",
        "file": ".resume.yaml"
      }
    }
    ```

### Extended Acceptance Criteria (Phase 3 - Work Unit Inline Creation)

11. **Given** I run `resume new work-unit` with all inline flags:
    ```bash
    resume new work-unit \
      --position "TechCorp|Engineer|2022-01|" \
      --title "Led ICS security assessment" \
      --problem "Legacy ICS systems lacked security monitoring across 50 PLCs" \
      --action "Deployed network sensors across industrial control systems" \
      --action "Built custom detection rules for Modbus protocol anomalies" \
      --result "Achieved 99.9% visibility into previously dark ICS traffic" \
      --impact "Prevented potential $2M breach" \
      --skill "ICS Security" \
      --skill "Network Analysis" \
      --tag "security"
    ```
    **When** the command executes
    **Then** a complete work unit YAML file is created
    **And** no editor is opened (file is ready-to-use)
    **And** position is auto-created if needed

12. **Given** I provide inline data that doesn't meet minimums
    **When** problem < 20 chars OR result < 10 chars OR any action < 10 chars
    **Then** clear validation error is shown with expected lengths

13. **Given** I run with JSON output:
    ```bash
    resume --json new work-unit --title "Test" --problem "..." --action "..." --result "..."
    ```
    **When** the command succeeds
    **Then** JSON includes `inline_created: true` and counts for skills/tags

## Tasks / Subtasks

- [x] Task 1: Add --position flag to new work-unit (AC: #1, #2)
  - [x] 1.1: Add `--position` option with pipe-separated format
  - [x] 1.2: Parse format: "Employer|Title|StartDate|EndDate"
  - [x] 1.3: Implement position matching (find existing by employer+title)
  - [x] 1.4: Auto-create position if not found
  - [x] 1.5: Set position_id on work unit
  - [x] 1.6: Return both IDs in output

- [x] Task 2: Add --position-id flag to new work-unit (AC: #3)
  - [x] 2.1: Add `--position-id` option
  - [x] 2.2: Validate position exists
  - [x] 2.3: Show clear error if not found
  - [x] 2.4: Set position_id on work unit

- [x] Task 3: Add JSON output for work-unit creation (AC: #4)
  - [x] 3.1: Detect --json global flag
  - [x] 3.2: Return structured JSON response
  - [x] 3.3: Include work_unit_id, position_id, position_created, file_path
  - [x] 3.4: Suppress Rich output in JSON mode

- [x] Task 4: Add non-interactive flags to new position (AC: #5, #6)
  - [x] 4.1: Add `--employer` option (required in non-interactive)
  - [x] 4.2: Add `--title` option (required in non-interactive)
  - [x] 4.3: Add `--location` option
  - [x] 4.4: Add `--start-date` option
  - [x] 4.5: Add `--end-date` option
  - [x] 4.6: Add `--employment-type` option
  - [x] 4.7: Add `--promoted-from` option
  - [x] 4.8: Detect non-interactive mode (all required flags provided)
  - [x] 4.9: Skip prompts when non-interactive

- [x] Task 5: Add JSON output for list positions (AC: #7)
  - [x] 5.1: Detect --json global flag
  - [x] 5.2: Return positions as JSON array
  - [x] 5.3: Include all position fields
  - [x] 5.4: Suppress Rich table in JSON mode

- [x] Task 6: Position matching logic
  - [x] 6.1: Implement case-insensitive employer+title matching
  - [x] 6.2: Normalize strings for comparison
  - [x] 6.3: Return existing position if match found

- [x] Task 7: Testing
  - [x] 7.1: Add tests for --position flag parsing
  - [x] 7.2: Add tests for position auto-creation
  - [x] 7.3: Add tests for position reuse
  - [x] 7.4: Add tests for --position-id validation
  - [x] 7.5: Add tests for JSON output format
  - [x] 7.6: Add tests for non-interactive position creation

- [x] Task 8: Code quality verification
  - [x] 8.1: Run `ruff check src tests --fix`
  - [x] 8.2: Run `mypy src --strict` with zero errors
  - [x] 8.3: Run `pytest` - all tests pass

### Extended Tasks (Phase 2 - Certifications & Education)

- [x] Task 9: Create CertificationService (AC: #8, #10)
  - [x] 9.1: Create `services/certification_service.py`
  - [x] 9.2: Implement `load_certifications()` from .resume.yaml
  - [x] 9.3: Implement `save_certification()` to .resume.yaml
  - [x] 9.4: Implement `find_certification()` for duplicate detection

- [x] Task 10: Create EducationService (AC: #9)
  - [x] 10.1: Create `services/education_service.py`
  - [x] 10.2: Implement `load_education()` from .resume.yaml
  - [x] 10.3: Implement `save_education()` to .resume.yaml
  - [x] 10.4: Implement `find_education()` for duplicate detection

- [x] Task 11: Add `new certification` command (AC: #8, #10)
  - [x] 11.1: Add `--name` option (required for non-interactive)
  - [x] 11.2: Add `--issuer`, `--date`, `--expires`, `--credential-id`, `--url` options
  - [x] 11.3: Detect non-interactive mode (--name provided)
  - [x] 11.4: Check for duplicates before creating
  - [x] 11.5: Return JSON output with `certification_created` boolean

- [x] Task 12: Add `new education` command (AC: #9)
  - [x] 12.1: Add `--degree`, `--institution` options (required for non-interactive)
  - [x] 12.2: Add `--year`, `--honors`, `--gpa` options
  - [x] 12.3: Detect non-interactive mode (--degree and --institution provided)
  - [x] 12.4: Check for duplicates before creating
  - [x] 12.5: Return JSON output with `education_created` boolean

- [x] Task 13: Testing for Phase 2
  - [x] 13.1: Add tests for `new certification` command
  - [x] 13.2: Add tests for `new education` command
  - [x] 13.3: Add tests for CertificationService
  - [x] 13.4: Add tests for EducationService
  - [x] 13.5: Add tests for duplicate detection
  - [x] 13.6: Add tests for JSON output format

- [x] Task 14: Code quality verification (Phase 2)
  - [x] 14.1: Run `ruff check src tests --fix`
  - [x] 14.2: Run `mypy src --strict` with zero errors
  - [x] 14.3: Run `pytest` - all 1244 tests pass

### Extended Tasks (Phase 3 - Work Unit Inline Creation)

- [x] Task 15: Add inline flags to `new work-unit` (AC: #11, #12, #13)
  - [x] 15.1: Add `--problem` option for problem statement
  - [x] 15.2: Add `--action` option (multiple=True for multiple actions)
  - [x] 15.3: Add `--result` option for outcome result
  - [x] 15.4: Add `--impact` option for quantified impact
  - [x] 15.5: Add `--skill` option (multiple=True)
  - [x] 15.6: Add `--tag` option (multiple=True)
  - [x] 15.7: Add `--start-date` and `--end-date` options

- [x] Task 16: Implement inline mode logic (AC: #11, #12)
  - [x] 16.1: Detect inline mode (all of: title, problem, action(s), result)
  - [x] 16.2: Validate minimum lengths (problem >= 20, result >= 10, actions >= 10)
  - [x] 16.3: Call `create_work_unit_from_data()` for inline creation
  - [x] 16.4: Return JSON with `inline_created: true` and counts

- [x] Task 17: Testing for Phase 3
  - [x] 17.1: Test full inline work unit creation
  - [x] 17.2: Test inline with all optional fields (impact, skills, tags, dates)
  - [x] 17.3: Test inline with position auto-creation
  - [x] 17.4: Test validation errors for short strings
  - [x] 17.5: Test mode detection (inline vs template fallback)
  - [x] 17.6: Test JSON output format with inline_created flag

- [x] Task 18: Code quality verification (Phase 3)
  - [x] 18.1: Run `ruff check src tests --fix`
  - [x] 18.2: Run `mypy src --strict` with zero errors
  - [x] 18.3: Run `pytest` - all 1255 tests pass

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

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - Implementation completed without issues.

### Completion Notes List

**Phase 1 - Position Inline Creation:**
- Implemented `parse_position_flag()` function for pipe-separated format parsing
- Implemented `find_existing_position()` for case-insensitive employer+title matching
- Added `--position` flag to `new work-unit` command for inline position creation
- Added `--position-id` validation that returns exit code 4 if position doesn't exist
- Mutual exclusion between `--position` and `--position-id` flags enforced
- JSON output includes `position_created` boolean and `position_id`
- Added non-interactive mode to `new position` command with flags:
  - `--employer`, `--title`, `--start-date` (required for non-interactive)
  - `--location`, `--end-date`, `--employment-type`, `--promoted-from` (optional)
- `list positions` already supported JSON output via existing implementation
- All 16 new tests pass, 1229 total tests pass
- Mypy strict mode passes with no errors
- Ruff linting passes

**Phase 2 - Certification & Education Inline Creation (Extension):**
- Created `CertificationService` with load/save for `.resume.yaml` config
- Created `EducationService` with load/save for `.resume.yaml` config
- Added `new certification` command with non-interactive flags:
  - `--name` (required for non-interactive)
  - `--issuer`, `--date`, `--expires`, `--credential-id`, `--url` (optional)
- Added `new education` command with non-interactive flags:
  - `--degree`, `--institution` (required for non-interactive)
  - `--year`, `--honors`, `--gpa` (optional)
- Duplicate detection for both certifications and education (case-insensitive)
- JSON output with `certification_created`/`education_created` boolean
- All 15 new tests pass, 1244 total tests pass
- Mypy strict mode passes with no errors
- Ruff linting passes

**Phase 3 - Work Unit Inline Creation (Extension):**
- Added `create_work_unit_from_data()` to `work_unit_service.py` for programmatic work unit creation
- Added inline flags to `new work-unit` command:
  - `--problem` for problem statement (min 20 chars)
  - `--action` (multiple) for actions taken (min 10 chars each)
  - `--result` for outcome result (min 10 chars)
  - `--impact` for quantified impact (optional)
  - `--skill` (multiple) for skills demonstrated (optional)
  - `--tag` (multiple) for tags (optional)
  - `--start-date`, `--end-date` for time bounds (optional)
- Inline mode detection: if `title + problem + action(s) + result` all provided, creates file directly
- Validation with clear error messages for minimum length requirements
- JSON output includes `inline_created: true` and skill/tag counts
- All 11 new tests pass, 1255 total tests pass
- Mypy strict mode passes with no errors
- Ruff linting passes

### File List

**Modified Files:**
- src/resume_as_code/commands/new.py - Added --position flag, position matching, non-interactive position/certification/education/work-unit creation, inline work unit flags, partial inline flag validation
- src/resume_as_code/services/work_unit_service.py - Added create_work_unit_from_data() for inline creation
- tests/integration/test_new_command.py - Updated test to create position before referencing

**New Files:**
- tests/unit/test_inline_position.py - 16 tests for inline position creation
- src/resume_as_code/services/certification_service.py - Service for certification CRUD in .resume.yaml
- src/resume_as_code/services/education_service.py - Service for education CRUD in .resume.yaml
- tests/unit/test_inline_certification.py - 8 tests for inline certification creation
- tests/unit/test_inline_education.py - 7 tests for inline education creation
- tests/unit/test_inline_work_unit.py - 11 tests for inline work unit creation
