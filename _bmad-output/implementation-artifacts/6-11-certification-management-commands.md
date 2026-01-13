# Story 6.11: Certification Management Commands

Status: done

## Story

As a **user with professional certifications**,
I want **interactive commands to manage my certifications**,
So that **I can easily add, update, and remove credentials without editing YAML**.

## Acceptance Criteria

1. **Given** I run `resume new certification`
   **When** prompted
   **Then** I'm asked for:
     1. Certification name (required)
     2. Issuing organization (optional)
     3. Date obtained (YYYY-MM)
     4. Expiration date (YYYY-MM or blank for no expiration)
     5. Credential ID (optional)
     6. Verification URL (optional)

2. **Given** I complete the certification prompts
   **When** the certification is created
   **Then** it is added to the `certifications` array in `.resume.yaml`
   **And** confirmation shows: "Added certification: AWS Solutions Architect - Professional"

3. **Given** I run `resume list certifications`
   **When** certifications exist
   **Then** a formatted table shows:
   | Name | Issuer | Date | Expires | Status |
   |------|--------|------|---------|--------|
   | AWS Solutions Architect | AWS | 2024-06 | 2027-06 | Active |
   | CISSP | ISC² | 2023-01 | 2026-01 | Expires Soon |

4. **Given** a certification expires within 90 days
   **When** listed
   **Then** status shows "Expires Soon" with yellow highlighting

5. **Given** a certification has expired
   **When** listed
   **Then** status shows "Expired" with red highlighting
   **And** a suggestion: "Consider renewing or hiding with `resume config certifications[0].display false`"

6. **Given** I run `resume remove certification "CISSP"`
   **When** the certification exists
   **Then** it is removed from `.resume.yaml`
   **And** confirmation shows: "Removed certification: CISSP"

7. **Given** I run `resume show certification "AWS Solutions"`
   **When** the certification exists (partial match on name)
   **Then** detailed information displays:
     - Name: AWS Solutions Architect - Professional
     - Issuer: Amazon Web Services
     - Date: 2024-06
     - Expires: 2027-06
     - Credential ID: ABC123XYZ
     - URL: (if present)
     - Status: Active
   **And** JSON output via `--json` includes all fields

8. **Given** I run non-interactively (LLM mode):
   ```bash
   resume new certification \
     --name "AWS Solutions Architect - Professional" \
     --issuer "Amazon Web Services" \
     --date 2024-06 \
     --expires 2027-06 \
     --credential-id "ABC123XYZ"
   ```
   **When** the command executes
   **Then** the certification is added without prompts

9. **Given** I run `resume --json list certifications`
   **When** certifications exist
   **Then** JSON output includes all certification fields
   **And** includes computed `status` field (active/expires_soon/expired)

## Tasks / Subtasks

- [x] Task 1: Create `new certification` subcommand (AC: #1, #2, #7)
  - [x] 1.1: Add `certification` subcommand to `commands/new.py`
  - [x] 1.2: Implement Rich prompts for interactive input
  - [x] 1.3: Add non-interactive flags and pipe-separated format support
  - [x] 1.4: Implement config file update via CertificationService
  - [x] 1.5: Display confirmation message with certification name

- [x] Task 2: Create `list certifications` command (AC: #3, #4, #5, #8)
  - [x] 2.1: Add `list certifications` subcommand to `commands/list_cmd.py`
  - [x] 2.2: Implement Rich table with columns: Name, Issuer, Date, Expires, Status
  - [x] 2.3: Implement status calculation (active/expires_soon/expired)
  - [x] 2.4: Add yellow highlighting for "Expires Soon" status
  - [x] 2.5: Add red highlighting for "Expired" status with tip
  - [x] 2.6: Implement JSON output with computed status field

- [x] Task 3: Create `remove certification` command (AC: #6)
  - [x] 3.1: Create `commands/remove.py` with remove command group
  - [x] 3.2: Accept certification name as argument
  - [x] 3.3: Search certifications by name (case-insensitive partial match)
  - [x] 3.4: Confirm removal in interactive mode (skip with `--yes`)
  - [x] 3.5: Update `.resume.yaml` with certification removed
  - [x] 3.6: Display confirmation message

- [x] Task 4: Register commands in CLI (AC: all)
  - [x] 4.1: Register `new certification` in main CLI group
  - [x] 4.2: Register `list certifications` in main CLI group
  - [x] 4.3: Register `remove certification` via remove_group in main CLI
  - [x] 4.4: Add help text for all commands

- [x] Task 5: CertificationService updates (AC: #2, #6)
  - [x] 5.1: Add `remove_certification()` method to CertificationService
  - [x] 5.2: Add `find_certifications_by_name()` method for partial matching
  - [x] 5.3: Preserve YAML formatting with ruamel.yaml
  - [x] 5.4: Handle missing certifications array (create if needed)

- [x] Task 6: Testing (AC: all)
  - [x] 6.1: Add unit tests for certification name matching
  - [x] 6.2: Add unit tests for remove_certification service
  - [x] 6.3: Add CLI tests for `new certification` (non-interactive + pipe-separated)
  - [x] 6.4: Add CLI tests for `list certifications` (table + JSON + empty)
  - [x] 6.5: Add CLI tests for `remove certification` (success, not found, multiple matches)
  - [x] 6.6: Add tests for JSON output format
  - [x] 6.7: Add tests for interactive confirmation

- [x] Task 7: Code quality verification
  - [x] 7.1: Run `ruff check src tests --fix` - all checks passed
  - [x] 7.2: Run `mypy src --strict` - no issues in 56 source files
  - [x] 7.3: Run `pytest` - 1311 tests pass

## Additional Parity Work (Scope Extension)

During implementation, CLI parity was added for positions and work units:

- [x] Task 8: Position parity
  - [x] 8.1: Add `remove_position()` method to PositionService
  - [x] 8.2: Add `find_positions_by_query()` method for search
  - [x] 8.3: Add `remove position` command to remove.py
  - [x] 8.4: Add tests for position removal

- [x] Task 9: Work Unit parity
  - [x] 9.1: Add `remove work-unit` command (deletes YAML file)
  - [x] 9.2: Add `show work-unit` command for details view
  - [x] 9.3: Add tests for work unit commands

- [x] Task 10: Documentation
  - [x] 10.1: Update CLAUDE.md Quick Reference table
  - [x] 10.2: Add Certification Management section to CLAUDE.md
  - [x] 10.3: Add Work Unit Management section to CLAUDE.md
  - [x] 10.4: Update Position Management section with remove command

- [x] Task 11: Create `show certification` command (AC: #7) - CLI Consistency
  - [x] 11.1: Add `show certification` subcommand to `commands/show.py`
  - [x] 11.2: Support partial name matching via CertificationService
  - [x] 11.3: Rich output with status highlighting
  - [x] 11.4: JSON output with all certification fields
  - [x] 11.5: Add 7 unit tests for show certification
  - [x] 11.6: Update CLAUDE.md Quick Reference and Certification Management sections

## Dev Notes

### Architecture Compliance

This story adds CLI commands for managing certifications stored in `.resume.yaml`. It follows the same patterns established in Story 6.8 (Position Management Commands) for interactive/non-interactive modes.

**Critical Rules from project-context.md:**
- Use Click for CLI commands
- Use Rich for console output and prompts
- Use `|` union syntax for optional fields (Python 3.10+)
- Support both interactive and non-interactive modes
- JSON output for programmatic parsing

### Command Structure

```python
# CLI command structure
resume new certification          # Interactive mode
resume new certification --name "..." --issuer "..." --date 2024-06
resume list certifications        # Table output
resume --json list certifications # JSON output
resume remove certification "CISSP"
```

### Implementation Patterns

#### New Certification Command

```python
# src/resume_as_code/commands/new.py (extend existing)

import click
from rich.prompt import Prompt, Confirm
from rich.console import Console

from resume_as_code.models.certification import Certification
from resume_as_code.services.config_writer import ConfigWriter

console = Console()


@new.command("certification")
@click.option("--name", help="Certification name")
@click.option("--issuer", help="Issuing organization")
@click.option("--date", help="Date obtained (YYYY-MM)")
@click.option("--expires", help="Expiration date (YYYY-MM)")
@click.option("--credential-id", help="Credential ID")
@click.option("--url", help="Verification URL")
@click.pass_context
def new_certification(
    ctx: click.Context,
    name: str | None,
    issuer: str | None,
    date: str | None,
    expires: str | None,
    credential_id: str | None,
    url: str | None,
) -> None:
    """Create a new certification entry."""
    non_interactive = ctx.obj.get("non_interactive", False)

    # Interactive prompts if flags not provided
    if not name:
        if non_interactive:
            raise click.UsageError("--name is required in non-interactive mode")
        name = Prompt.ask("Certification name")

    if not issuer and not non_interactive:
        issuer = Prompt.ask("Issuing organization", default="")
        issuer = issuer or None

    if not date:
        if non_interactive:
            raise click.UsageError("--date is required in non-interactive mode")
        date = Prompt.ask("Date obtained (YYYY-MM)")

    if not expires and not non_interactive:
        expires = Prompt.ask("Expiration date (YYYY-MM, blank for none)", default="")
        expires = expires or None

    if not credential_id and not non_interactive:
        credential_id = Prompt.ask("Credential ID", default="")
        credential_id = credential_id or None

    if not url and not non_interactive:
        url = Prompt.ask("Verification URL", default="")
        url = url or None

    # Create certification
    cert = Certification(
        name=name,
        issuer=issuer,
        date=date,
        expires=expires,
        credential_id=credential_id,
        url=url,
    )

    # Add to config
    writer = ConfigWriter()
    writer.add_certification(cert)

    console.print(f"[green]Added certification: {name}[/green]")
```

#### List Certifications Command

```python
# src/resume_as_code/commands/certifications.py

from datetime import date, timedelta

import click
from rich.console import Console
from rich.table import Table

from resume_as_code.config import get_config
from resume_as_code.models.certification import Certification

console = Console()


def get_certification_status(cert: Certification) -> tuple[str, str]:
    """Get status and style for certification.

    Returns:
        Tuple of (status_text, rich_style)
    """
    if not cert.expires:
        return ("Active", "green")

    # Parse YYYY-MM to date
    year, month = map(int, cert.expires.split("-"))
    expires_date = date(year, month, 1)
    today = date.today()

    if expires_date < today:
        return ("Expired", "red")
    if expires_date < today + timedelta(days=90):
        return ("Expires Soon", "yellow")
    return ("Active", "green")


@click.command("certifications")
@click.pass_context
def list_certifications(ctx: click.Context) -> None:
    """List all certifications."""
    config = get_config()
    json_mode = ctx.obj.get("json_mode", False)

    if not config.certifications:
        if json_mode:
            click.echo('{"status": "success", "data": []}')
        else:
            console.print("[dim]No certifications found.[/dim]")
        return

    if json_mode:
        # JSON output with computed status
        data = []
        for cert in config.certifications:
            status, _ = get_certification_status(cert)
            cert_dict = cert.model_dump()
            cert_dict["status"] = status.lower().replace(" ", "_")
            data.append(cert_dict)
        click.echo(json.dumps({"status": "success", "data": data}, indent=2))
        return

    # Rich table output
    table = Table(title="Certifications")
    table.add_column("Name", style="cyan")
    table.add_column("Issuer")
    table.add_column("Date")
    table.add_column("Expires")
    table.add_column("Status")

    has_expired = False
    for cert in config.certifications:
        status, style = get_certification_status(cert)
        if status == "Expired":
            has_expired = True

        table.add_row(
            cert.name,
            cert.issuer or "-",
            cert.date or "-",
            cert.expires or "Never",
            f"[{style}]{status}[/{style}]",
        )

    console.print(table)

    if has_expired:
        console.print(
            "\n[yellow]Tip: Consider renewing expired certifications or hiding with "
            "`resume config certifications[N].display false`[/yellow]"
        )
```

#### Remove Certification Command

```python
# src/resume_as_code/commands/certifications.py (continued)

@click.command("certification")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def remove_certification(ctx: click.Context, name: str, yes: bool) -> None:
    """Remove a certification by name."""
    config = get_config()

    # Find matching certification (case-insensitive)
    matching = [
        c for c in config.certifications
        if name.lower() in c.name.lower()
    ]

    if not matching:
        console.print(f"[red]No certification found matching '{name}'[/red]")
        raise SystemExit(4)  # NOT_FOUND

    if len(matching) > 1:
        console.print(f"[yellow]Multiple certifications match '{name}':[/yellow]")
        for cert in matching:
            console.print(f"  - {cert.name}")
        console.print("[yellow]Please be more specific.[/yellow]")
        raise SystemExit(1)

    cert = matching[0]

    # Confirm removal
    if not yes:
        if not Confirm.ask(f"Remove certification '{cert.name}'?"):
            console.print("[dim]Cancelled.[/dim]")
            return

    # Remove from config
    writer = ConfigWriter()
    writer.remove_certification(cert.name)

    console.print(f"[green]Removed certification: {cert.name}[/green]")
```

### Config Writer Service

```python
# src/resume_as_code/services/config_writer.py

from pathlib import Path

import yaml

from resume_as_code.models.certification import Certification


class ConfigWriter:
    """Service for updating .resume.yaml configuration."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or Path(".resume.yaml")

    def _load(self) -> dict:
        """Load current config."""
        if not self.config_path.exists():
            return {}
        with open(self.config_path) as f:
            return yaml.safe_load(f) or {}

    def _save(self, data: dict) -> None:
        """Save config with backup."""
        # Create backup
        if self.config_path.exists():
            backup = self.config_path.with_suffix(".yaml.bak")
            backup.write_text(self.config_path.read_text())

        # Write new config
        with open(self.config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def add_certification(self, cert: Certification) -> None:
        """Add certification to config."""
        data = self._load()

        if "certifications" not in data:
            data["certifications"] = []

        # Add certification as dict
        cert_dict = cert.model_dump(exclude_none=True)
        data["certifications"].append(cert_dict)

        self._save(data)

    def remove_certification(self, name: str) -> None:
        """Remove certification by name."""
        data = self._load()

        if "certifications" not in data:
            return

        data["certifications"] = [
            c for c in data["certifications"]
            if c.get("name", "").lower() != name.lower()
        ]

        self._save(data)
```

### Dependencies

This story REQUIRES:
- Story 6.2 (Certifications Model) - Must have Certification Pydantic model
- Story 1.3 (Configuration) - Must have config loading infrastructure
- Story 1.2 (Rich Console) - Must have Rich output formatting

This story ENABLES:
- Complete certification management without YAML editing
- LLM agents to manage certifications programmatically

### Files to Create/Modify

**New Files:**
- `src/resume_as_code/commands/certifications.py` - List and remove commands
- `src/resume_as_code/services/config_writer.py` - Config update utilities
- `tests/unit/test_certification_commands.py` - Unit tests
- `tests/integration/test_certification_commands.py` - Integration tests

**Modified Files:**
- `src/resume_as_code/commands/new.py` - Add `new certification` subcommand
- `src/resume_as_code/cli.py` - Register new commands

### Testing Strategy

```python
# tests/unit/test_certification_commands.py

from datetime import date, timedelta
import pytest

from resume_as_code.commands.certifications import get_certification_status
from resume_as_code.models.certification import Certification


class TestCertificationStatus:
    """Tests for certification status calculation."""

    def test_active_no_expiration(self):
        """Should return active for cert without expiration."""
        cert = Certification(name="Test", date="2024-01")
        status, style = get_certification_status(cert)
        assert status == "Active"
        assert style == "green"

    def test_active_far_future(self):
        """Should return active for cert expiring far in future."""
        future = date.today() + timedelta(days=365)
        cert = Certification(
            name="Test",
            date="2024-01",
            expires=future.strftime("%Y-%m"),
        )
        status, style = get_certification_status(cert)
        assert status == "Active"
        assert style == "green"

    def test_expires_soon(self):
        """Should return expires_soon within 90 days."""
        soon = date.today() + timedelta(days=45)
        cert = Certification(
            name="Test",
            date="2024-01",
            expires=soon.strftime("%Y-%m"),
        )
        status, style = get_certification_status(cert)
        assert status == "Expires Soon"
        assert style == "yellow"

    def test_expired(self):
        """Should return expired for past date."""
        past = date.today() - timedelta(days=30)
        cert = Certification(
            name="Test",
            date="2023-01",
            expires=past.strftime("%Y-%m"),
        )
        status, style = get_certification_status(cert)
        assert status == "Expired"
        assert style == "red"
```

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_certification_commands.py -v
uv run pytest tests/integration/test_certification_commands.py -v

# Manual verification:
# Interactive mode
uv run resume new certification

# Non-interactive mode
uv run resume new certification \
  --name "Test Cert" \
  --issuer "Test Org" \
  --date 2024-01

# List certifications
uv run resume list certifications
uv run resume --json list certifications

# Remove certification
uv run resume remove certification "Test Cert"
```

### References

- [Source: epics.md#Story 6.11](_bmad-output/planning-artifacts/epics.md)
- [Story 6.2: Certifications Model](6-2-certifications-model-storage.md)
- [Story 6.8: Position Management Commands](6-8-position-management-commands.md) - Similar patterns

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No significant debugging required

### Completion Notes List

1. Task 1 (`new certification`) was already implemented in previous work - verified working
2. Used CertificationService pattern instead of separate ConfigWriter
3. Added pipe-separated format support (`Name|Issuer|Date|Expires`) for LLM-friendly input
4. Extended scope to add CLI parity for positions and work units per user request
5. All 1311 tests pass (41 new tests from this story), mypy strict mode clean, ruff checks pass
6. Code review remediation: Updated File List, fixed AC#5 tip, added empty name validation
7. Post-review: Added `show certification` command (Task 11) for CLI consistency pattern - 7 new tests

### File List

**Created:**
- `src/resume_as_code/commands/remove.py` - Remove command group (certification, position, work-unit)
- `tests/unit/test_certification_commands.py` - 48 tests for all commands (41 original + 7 for show certification)

**Modified:**
- `src/resume_as_code/commands/new.py` - Contains `new certification` command (AC#1, #2, #8)
- `src/resume_as_code/commands/list_cmd.py` - Added `list certifications` subcommand (AC#3, #4, #5, #9)
- `src/resume_as_code/commands/show.py` - Added `show work-unit` and `show certification` commands (AC#7)
- `src/resume_as_code/services/certification_service.py` - Added remove_certification, find_certifications_by_name
- `src/resume_as_code/services/position_service.py` - Added remove_position, find_positions_by_query
- `src/resume_as_code/cli.py` - Registered remove_group

**Documentation:**
- `CLAUDE.md` - Updated Quick Reference, added Certification/Work Unit Management sections

**Test Files Modified (pre-existing tests updated for compatibility):**
- `tests/unit/test_inline_certification.py`
- `tests/unit/test_inline_education.py`
- `tests/unit/test_inline_position.py`
- `tests/unit/test_inline_work_unit.py`
- `tests/unit/test_position_commands.py`
- `tests/unit/test_resume_model.py`
- `tests/unit/test_template_certifications.py`

**Example Files (formatting/position_id updates):**
- `examples/work-units/wu-*.yaml` - 8 files updated with position_id references

## Senior Developer Review (AI)

**Reviewer:** Joshua Magady
**Date:** 2026-01-12
**Outcome:** APPROVED (after remediation)

### Findings Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 2 | Fixed |
| MEDIUM | 4 | Fixed |
| LOW | 3 | Fixed |

### Issues Found & Remediated

1. **CRITICAL-1: Story File List Incomplete**
   - Story claimed 8 files modified, git showed 27+
   - **Fix:** Updated File List with all modified files including test files and examples

2. **CRITICAL-2: AC#5 Tip Showed Generic `[N]` Index**
   - AC specified showing actual certification index, code showed `[N]`
   - **Fix:** Updated `list_cmd.py` to track expired indices and show first expired index

3. **MEDIUM-3: Empty Name Validation Missing**
   - `resume new certification --name ""` could create cert with empty name
   - **Fix:** Added validation in `new.py` to reject empty names

4. **LOW-1: Duplicate YAML Import**
   - `show.py` had redundant local import of YAML
   - **Fix:** Removed duplicate import

5. **LOW-2: Test Count Not Documented**
   - Completion notes didn't specify new test count
   - **Fix:** Updated notes to specify "41 new tests from this story"

### Test Added

- `test_new_certification_empty_name_rejected` - validates empty name rejection

### Verification

- `uv run ruff check src tests` - PASSED
- `uv run mypy src --strict` - PASSED (56 source files)
- `uv run pytest tests/unit/` - PASSED (1087 tests)
