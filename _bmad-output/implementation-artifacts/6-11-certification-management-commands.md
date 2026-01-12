# Story 6.11: Certification Management Commands

Status: ready-for-dev

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

7. **Given** I run non-interactively (LLM mode):
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

8. **Given** I run `resume --json list certifications`
   **When** certifications exist
   **Then** JSON output includes all certification fields
   **And** includes computed `status` field (active/expires_soon/expired)

## Tasks / Subtasks

- [ ] Task 1: Create `new certification` subcommand (AC: #1, #2, #7)
  - [ ] 1.1: Add `certification` subcommand to `commands/new.py`
  - [ ] 1.2: Implement Rich prompts for interactive input:
    - Name (required, text prompt)
    - Issuer (optional, text prompt)
    - Date obtained (YYYY-MM, validated)
    - Expiration date (optional, YYYY-MM)
    - Credential ID (optional, text)
    - Verification URL (optional, URL validated)
  - [ ] 1.3: Add non-interactive flags: `--name`, `--issuer`, `--date`, `--expires`, `--credential-id`, `--url`
  - [ ] 1.4: Implement config file update: read → modify → write `.resume.yaml`
  - [ ] 1.5: Display confirmation message with certification name

- [ ] Task 2: Create `list certifications` command (AC: #3, #4, #5, #8)
  - [ ] 2.1: Create `commands/certifications.py` module
  - [ ] 2.2: Add `list_certifications()` command function
  - [ ] 2.3: Implement Rich table with columns: Name, Issuer, Date, Expires, Status
  - [ ] 2.4: Implement status calculation logic:
    ```python
    def get_status(cert: Certification) -> str:
        if not cert.expires:
            return "active"
        expires = parse_date(cert.expires)
        if expires < today:
            return "expired"
        if expires < today + timedelta(days=90):
            return "expires_soon"
        return "active"
    ```
  - [ ] 2.5: Add yellow highlighting for "Expires Soon" status
  - [ ] 2.6: Add red highlighting for "Expired" status with suggestion
  - [ ] 2.7: Implement JSON output with computed status field

- [ ] Task 3: Create `remove certification` command (AC: #6)
  - [ ] 3.1: Add `remove_certification()` command function
  - [ ] 3.2: Accept certification name as argument
  - [ ] 3.3: Search certifications by name (case-insensitive partial match)
  - [ ] 3.4: Confirm removal in interactive mode (skip with `--yes`)
  - [ ] 3.5: Update `.resume.yaml` with certification removed
  - [ ] 3.6: Display confirmation message

- [ ] Task 4: Register commands in CLI (AC: all)
  - [ ] 4.1: Register `new certification` in main CLI group
  - [ ] 4.2: Register `list certifications` in main CLI group
  - [ ] 4.3: Register `remove certification` in main CLI group
  - [ ] 4.4: Add help text for all commands

- [ ] Task 5: Config file update utilities (AC: #2, #6)
  - [ ] 5.1: Create/update `services/config_writer.py` for safe YAML updates
  - [ ] 5.2: Implement read-modify-write pattern with backup
  - [ ] 5.3: Preserve YAML comments and formatting where possible
  - [ ] 5.4: Handle missing certifications array (create if needed)

- [ ] Task 6: Testing (AC: all)
  - [ ] 6.1: Add unit tests for status calculation
  - [ ] 6.2: Add unit tests for certification name matching
  - [ ] 6.3: Add integration tests for `new certification` (interactive mock)
  - [ ] 6.4: Add integration tests for `new certification` (non-interactive)
  - [ ] 6.5: Add integration tests for `list certifications`
  - [ ] 6.6: Add integration tests for `remove certification`
  - [ ] 6.7: Add tests for JSON output format
  - [ ] 6.8: Add tests for empty certifications handling

- [ ] Task 7: Code quality verification
  - [ ] 7.1: Run `ruff check src tests --fix`
  - [ ] 7.2: Run `mypy src --strict` with zero errors
  - [ ] 7.3: Run `pytest` - all tests pass

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

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

