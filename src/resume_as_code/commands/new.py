"""New command for creating Work Units and Positions."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import click

from resume_as_code.config import get_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.models.position import EmploymentType, Position
from resume_as_code.services.archetype_service import list_archetypes
from resume_as_code.services.position_service import PositionService
from resume_as_code.services.work_unit_service import (
    create_work_unit_file,
    generate_id,
)
from resume_as_code.utils.console import console, info, success, warning
from resume_as_code.utils.editor import get_editor, open_in_editor
from resume_as_code.utils.errors import handle_errors
from resume_as_code.utils.slugify import generate_unique_position_id

EMPLOYMENT_TYPES: list[EmploymentType] = [
    "full-time",
    "part-time",
    "contract",
    "consulting",
    "freelance",
]


def _get_archetype_choices() -> list[str]:
    """Get available archetype choices for the CLI option."""
    archetypes = list_archetypes()
    if not archetypes:
        warning("No archetypes found; using 'greenfield' as fallback")
        return ["greenfield"]  # Fallback default
    return archetypes


@click.group("new")
def new_group() -> None:
    """Create new resources."""


@new_group.command("work-unit")
@click.option(
    "--archetype",
    "-a",
    type=click.Choice(_get_archetype_choices()),
    help="Archetype template to use",
)
@click.option(
    "--title",
    "-t",
    help="Work Unit title (used to generate ID slug)",
)
@click.option(
    "--position-id",
    "-p",
    help="Position ID to associate with this work unit",
)
@click.option(
    "--from-memory",
    is_flag=True,
    help="Quick capture mode with minimal template",
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
    position_id: str | None,
    from_memory: bool,
    no_edit: bool,
) -> None:
    """Create a new Work Unit from an archetype template."""
    config = get_config()

    # Quick capture mode - use minimal archetype, skip archetype selection
    if from_memory:
        if archetype is not None and archetype != "minimal" and not ctx.obj.quiet:
            warning(f"--from-memory overrides --archetype={archetype}, using 'minimal'")
        archetype = "minimal"
        if title is None and not ctx.obj.json_output and not ctx.obj.quiet:
            title = click.prompt("Quick title")
        elif title is None:
            title = "quick-capture"
    else:
        # Select archetype (interactive if not provided)
        if archetype is None:
            archetype = _select_archetype_interactive(ctx)

        # Get title (interactive if not provided)
        if title is None:
            title = _prompt_title_interactive(ctx)

    # Position selection (interactive if not provided and not in quiet/json mode)
    if position_id is None and not ctx.obj.json_output and not ctx.obj.quiet:
        position_id = _prompt_position_interactive(ctx, config, from_memory=from_memory)

    # Generate ID and create file
    work_unit_id = generate_id(title, date.today())
    file_path = create_work_unit_file(
        archetype=archetype,
        work_unit_id=work_unit_id,
        title=title,
        work_units_dir=config.work_units_dir,
        position_id=position_id,
    )

    # Output result
    if ctx.obj.json_output:
        data = {
            "id": work_unit_id,
            "file": str(file_path),
            "archetype": archetype,
        }
        if position_id:
            data["position_id"] = position_id
        response = JSONResponse(
            status="success",
            command="new work-unit",
            data=data,
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
    if not archetypes:
        return "greenfield"

    console.print("\n[bold]Select an archetype:[/bold]\n")

    for i, name in enumerate(archetypes, 1):
        console.print(f"  {i}. {name}")

    default_idx = archetypes.index("greenfield") + 1 if "greenfield" in archetypes else 1
    console.print(f"\n  [dim]Default: {archetypes[default_idx - 1]}[/dim]")

    choice: int = click.prompt(
        "Choice",
        type=click.IntRange(1, len(archetypes)),
        default=default_idx,
        show_default=False,
    )

    return archetypes[choice - 1]


def _prompt_title_interactive(ctx: click.Context) -> str:
    """Interactively prompt for title."""
    if ctx.obj.json_output or ctx.obj.quiet:
        # Non-interactive mode - use placeholder
        return "untitled-work-unit"

    title: str = click.prompt("Work Unit title")
    return title


@new_group.command("position")
@click.pass_context
@handle_errors
def new_position(ctx: click.Context) -> None:
    """Create a new employment position interactively."""
    config = get_config()
    service = PositionService(config.positions_path)

    console.print("[bold]Create New Position[/bold]\n")

    # Required fields
    employer: str = click.prompt("Employer name")
    title: str = click.prompt("Job title")

    # Optional location
    location_input: str = click.prompt("Location (city, state/country)", default="")
    location: str | None = location_input if location_input else None

    # Date prompts
    default_date = datetime.now().strftime("%Y-%m")
    start_date: str = click.prompt("Start date (YYYY-MM)", default=default_date)

    # Validate date format
    if not _validate_date_format(start_date):
        console.print("[red]✗ Invalid date format. Use YYYY-MM.[/red]")
        raise SystemExit(1)

    is_current: bool = click.confirm("Is this your current position?", default=True)
    end_date: str | None = None
    if not is_current:
        end_date_input: str = click.prompt("End date (YYYY-MM)")
        if not _validate_date_format(end_date_input):
            console.print("[red]✗ Invalid date format. Use YYYY-MM.[/red]")
            raise SystemExit(1)
        end_date = end_date_input

    # Employment type selection
    console.print("\n[bold]Employment Type:[/bold]")
    for i, emp_type in enumerate(EMPLOYMENT_TYPES, 1):
        console.print(f"  {i}. {emp_type}")

    type_choice: int = click.prompt(
        "Select type",
        type=click.IntRange(1, len(EMPLOYMENT_TYPES)),
        default=1,
    )
    employment_type = EMPLOYMENT_TYPES[type_choice - 1]

    # Promotion check
    promoted_from: str | None = None
    if click.confirm("\nWas this a promotion from a previous position?", default=False):
        positions = service.load_positions()
        if positions:
            console.print("\n[bold]Select previous position:[/bold]")
            pos_list = list(positions.values())
            for i, pos in enumerate(pos_list, 1):
                console.print(f"  {i}. {pos.title} at {pos.employer}")

            prev_choice: int = click.prompt(
                "Select position",
                type=click.IntRange(1, len(pos_list)),
            )
            promoted_from = pos_list[prev_choice - 1].id
        else:
            console.print("[dim]No existing positions to link as promotion source.[/dim]")

    # Generate unique ID
    existing_ids = set(service.load_positions().keys())
    position_id = generate_unique_position_id(employer, title, existing_ids)

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

    service.save_position(position)

    # Output result
    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="new position",
            data={
                "id": position_id,
                "employer": employer,
                "title": title,
                "file": str(config.positions_path),
            },
        )
        click.echo(response.to_json())
    else:
        success(f"Position created: {position_id}")
        info(f"Use this ID in work units: position_id: {position_id}")


def _prompt_position_interactive(
    ctx: click.Context, config: Any, from_memory: bool = False
) -> str | None:
    """Prompt user to select or create a position.

    Args:
        ctx: Click context.
        config: Application configuration.
        from_memory: If True, suggest position based on current date (AC#5).

    Returns:
        Position ID if selected, None if skipped or no positions exist.
    """
    service = PositionService(config.positions_path)
    positions = service.load_positions()

    # Only prompt if positions exist - skip for new projects
    if not positions:
        return None

    # AC#5: Date-based position suggestion for --from-memory mode
    if from_memory:
        today = datetime.now().strftime("%Y-%m")
        suggested = service.suggest_position_for_date(today)
        if suggested:
            console.print(
                f"\n[cyan]Suggested position:[/cyan] {suggested.title} at {suggested.employer}"
            )
            if click.confirm("Use this position?", default=True):
                return suggested.id
            # User declined, fall through to full selection

    options: list[tuple[str, str]] = []

    # Add existing positions sorted by start_date descending
    sorted_positions = sorted(
        positions.values(),
        key=lambda p: p.start_date,
        reverse=True,
    )
    for pos in sorted_positions:
        options.append((pos.id, f"{pos.title} at {pos.employer}"))

    # Add special options
    options.append(("__new__", "Create new position..."))
    options.append(("__none__", "No position (personal project)"))

    console.print("\n[bold]Select Position:[/bold]")
    for i, (_, label) in enumerate(options, 1):
        console.print(f"  {i}. {label}")

    choice: int = click.prompt(
        "Select option",
        type=click.IntRange(1, len(options)),
        default=len(options),  # Default to "No position"
    )
    selected_id, _ = options[choice - 1]

    if selected_id == "__new__":
        # Inline create new position - call the position creation logic
        console.print("\n[bold]Create New Position[/bold]\n")
        return _create_position_inline(ctx, config, service)
    elif selected_id == "__none__":
        return None
    else:
        return selected_id


def _create_position_inline(
    ctx: click.Context, config: Any, service: PositionService
) -> str:
    """Create a position inline during work unit creation."""
    # Required fields
    employer: str = click.prompt("Employer name")
    title: str = click.prompt("Job title")

    # Optional location (consistent with main new position command)
    location_input: str = click.prompt("Location (city, state/country)", default="")
    location: str | None = location_input if location_input else None

    # Date prompts
    default_date = datetime.now().strftime("%Y-%m")
    start_date: str = click.prompt("Start date (YYYY-MM)", default=default_date)

    is_current: bool = click.confirm("Is this your current position?", default=True)
    end_date: str | None = None
    if not is_current:
        end_date = click.prompt("End date (YYYY-MM)")

    # Employment type selection
    console.print("\n[bold]Employment Type:[/bold]")
    for i, emp_type in enumerate(EMPLOYMENT_TYPES, 1):
        console.print(f"  {i}. {emp_type}")

    type_choice: int = click.prompt(
        "Select type",
        type=click.IntRange(1, len(EMPLOYMENT_TYPES)),
        default=1,
    )
    employment_type = EMPLOYMENT_TYPES[type_choice - 1]

    # Generate unique ID
    existing_ids = set(service.load_positions().keys())
    position_id = generate_unique_position_id(employer, title, existing_ids)

    # Create and save position
    position = Position(
        id=position_id,
        employer=employer,
        title=title,
        location=location,
        start_date=start_date,
        end_date=end_date,
        employment_type=employment_type,
    )

    service.save_position(position)
    success(f"Position created: {position_id}")

    return position_id


def _validate_date_format(date_str: str) -> bool:
    """Validate YYYY-MM date format."""
    import re

    return bool(re.match(r"^\d{4}-\d{2}$", date_str))
