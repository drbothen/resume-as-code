"""New command for creating Work Units."""

from __future__ import annotations

from datetime import date

import click

from resume_as_code.config import get_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.archetype_service import list_archetypes
from resume_as_code.services.work_unit_service import (
    create_work_unit_file,
    generate_id,
)
from resume_as_code.utils.console import console, info, success, warning
from resume_as_code.utils.editor import get_editor, open_in_editor
from resume_as_code.utils.errors import handle_errors


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
