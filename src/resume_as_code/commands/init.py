"""Init command for initializing resume projects.

Story 7.21: Resume Init Command
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import click
import yaml
from rich.prompt import Prompt

from resume_as_code.context import Context, pass_context
from resume_as_code.models.output import JSONResponse
from resume_as_code.utils.console import console, err_console, info, success
from resume_as_code.utils.errors import handle_errors

# Simple URL regex pattern for validation
URL_PATTERN = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
    r"localhost|"  # localhost
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def _is_valid_url(url: str) -> bool:
    """Validate URL format.

    Args:
        url: The URL string to validate.

    Returns:
        True if URL is valid, False otherwise.
    """
    return bool(URL_PATTERN.match(url))


# Story 9.2: Config-only .resume.yaml (no embedded data)
DEFAULT_CONFIG: dict[str, Any] = {
    "schema_version": "3.0.0",
    "output_dir": "./dist",
    "default_format": "both",
    "default_template": "modern",
    "work_units_dir": "./work-units",
    "positions_path": "./positions.yaml",
}

# Default file paths for separated data structure (Story 9.2)
DATA_FILES: dict[str, str] = {
    "profile": "profile.yaml",
    "certifications": "certifications.yaml",
    "education": "education.yaml",
    "highlights": "highlights.yaml",
    "publications": "publications.yaml",
    "board_roles": "board-roles.yaml",
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
            _output_json_error("Configuration already exists: .resume.yaml")
        elif not ctx.quiet:
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
    profile = _get_placeholder_profile() if non_interactive else _prompt_for_profile()

    # Story 9.2: Create config-only .resume.yaml
    config = DEFAULT_CONFIG.copy()
    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
    files_created.append(str(config_path))

    # Story 9.2: Create separate profile.yaml
    profile_data = {k: v for k, v in profile.items() if v is not None}
    profile_path = Path(DATA_FILES["profile"])
    profile_path.write_text(yaml.dump(profile_data, default_flow_style=False, sort_keys=False))
    files_created.append(str(profile_path))

    # Story 9.2: Create empty data files
    for key, filename in DATA_FILES.items():
        if key == "profile":
            continue  # Already created above
        data_path = Path(filename)
        data_path.write_text("[]\n")
        files_created.append(str(data_path))

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


def _prompt_for_url(label: str) -> str | None:
    """Prompt for an optional URL with validation.

    Args:
        label: The label to display for the prompt.

    Returns:
        The validated URL or None if skipped.
    """
    while True:
        value = Prompt.ask(f"{label} URL", default="") or None
        if value is None:
            return None
        if _is_valid_url(value):
            return value
        console.print("[yellow]Invalid URL format. Must start with http:// or https://[/yellow]")


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
    linkedin = _prompt_for_url("LinkedIn")
    github = _prompt_for_url("GitHub")
    website = _prompt_for_url("Website")

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


def _output_json_error(message: str) -> None:
    """Output JSON error response.

    Args:
        message: The error message to include in the response.
    """
    response = JSONResponse(
        status="error",
        command="init",
        errors=[{"code": "CONFIG_EXISTS", "message": message, "recoverable": True}],
    )
    err_console.print(response.model_dump_json(indent=2))
