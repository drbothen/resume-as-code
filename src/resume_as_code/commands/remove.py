"""Remove command for deleting resources."""

from __future__ import annotations

from pathlib import Path

import click
from rich.prompt import Confirm

from resume_as_code.config import get_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.certification_service import CertificationService
from resume_as_code.services.position_service import PositionService
from resume_as_code.utils.console import console, info, success, warning
from resume_as_code.utils.errors import handle_errors


@click.group("remove")
def remove_group() -> None:
    """Remove resources."""


@remove_group.command("certification")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
@handle_errors
def remove_certification(ctx: click.Context, name: str, yes: bool) -> None:
    """Remove a certification by name.

    Performs case-insensitive partial matching on the certification name.
    If multiple certifications match, asks for clarification.
    """
    service = CertificationService(config_path=Path.cwd() / ".resume.yaml")

    # Find matching certifications
    matching = service.find_certifications_by_name(name)

    if not matching:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove certification",
                data={"message": f"No certification found matching '{name}'"},
            )
            click.echo(response.to_json())
        else:
            console.print(f"[red]No certification found matching '{name}'[/red]")
        raise SystemExit(4)  # NOT_FOUND

    if len(matching) > 1:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove certification",
                data={
                    "message": f"Multiple certifications match '{name}'",
                    "matches": [cert.name for cert in matching],
                },
            )
            click.echo(response.to_json())
        else:
            console.print(f"[yellow]Multiple certifications match '{name}':[/yellow]")
            for cert in matching:
                console.print(f"  - {cert.name}")
            console.print("[yellow]Please be more specific.[/yellow]")
        raise SystemExit(1)

    cert = matching[0]

    # Confirm removal unless --yes flag is set
    if (
        not yes
        and not ctx.obj.json_output
        and not Confirm.ask(f"Remove certification '[cyan]{cert.name}[/cyan]'?")
    ):
        info("Cancelled.")
        return

    # Remove the certification
    removed = service.remove_certification(cert.name)

    if removed:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="remove certification",
                data={
                    "removed": True,
                    "name": cert.name,
                },
            )
            click.echo(response.to_json())
        else:
            success(f"Removed certification: {cert.name}")
    else:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove certification",
                data={"message": "Failed to remove certification"},
            )
            click.echo(response.to_json())
        else:
            console.print("[red]Failed to remove certification[/red]")
        raise SystemExit(1)


@remove_group.command("position")
@click.argument("position_id_or_query")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
@handle_errors
def remove_position(ctx: click.Context, position_id_or_query: str, yes: bool) -> None:
    """Remove a position by ID or search query.

    Accepts exact position ID or partial match on employer/title.
    If multiple positions match, asks for clarification.
    """
    config = get_config()
    service = PositionService(config.positions_path)

    # Try exact ID match first, then search by query
    position = service.get_position(position_id_or_query)
    matching = [position] if position else service.find_positions_by_query(position_id_or_query)

    if not matching:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove position",
                data={"message": f"No position found matching '{position_id_or_query}'"},
            )
            click.echo(response.to_json())
        else:
            console.print(f"[red]No position found matching '{position_id_or_query}'[/red]")
        raise SystemExit(4)  # NOT_FOUND

    if len(matching) > 1:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove position",
                data={
                    "message": f"Multiple positions match '{position_id_or_query}'",
                    "matches": [p.id for p in matching],
                },
            )
            click.echo(response.to_json())
        else:
            console.print(f"[yellow]Multiple positions match '{position_id_or_query}':[/yellow]")
            for pos in matching:
                console.print(f"  - {pos.id}: {pos.title} at {pos.employer}")
            console.print("[yellow]Please be more specific or use the full position ID.[/yellow]")
        raise SystemExit(1)

    pos = matching[0]

    # Confirm removal unless --yes flag is set
    if (
        not yes
        and not ctx.obj.json_output
        and not Confirm.ask(
            f"Remove position '[cyan]{pos.id}[/cyan]' ({pos.title} at {pos.employer})?"
        )
    ):
        info("Cancelled.")
        return

    # Remove the position
    removed = service.remove_position(pos.id)

    if removed:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="remove position",
                data={
                    "removed": True,
                    "position_id": pos.id,
                    "employer": pos.employer,
                    "title": pos.title,
                },
            )
            click.echo(response.to_json())
        else:
            success(f"Removed position: {pos.id}")
            warning("Work units referencing this position may need updating.")
    else:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove position",
                data={"message": "Failed to remove position"},
            )
            click.echo(response.to_json())
        else:
            console.print("[red]Failed to remove position[/red]")
        raise SystemExit(1)


@remove_group.command("work-unit")
@click.argument("work_unit_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
@handle_errors
def remove_work_unit(ctx: click.Context, work_unit_id: str, yes: bool) -> None:
    """Remove a work unit by ID.

    Deletes the work unit YAML file from the work-units directory.
    """
    config = get_config()

    # Find the work unit file
    work_units_dir = config.work_units_dir

    # Try exact filename match first
    file_path = work_units_dir / f"{work_unit_id}.yaml"

    if not file_path.exists():
        # Search for partial match
        matching_files = list(work_units_dir.glob(f"*{work_unit_id}*.yaml"))

        if not matching_files:
            if ctx.obj.json_output:
                response = JSONResponse(
                    status="error",
                    command="remove work-unit",
                    data={"message": f"No work unit found matching '{work_unit_id}'"},
                )
                click.echo(response.to_json())
            else:
                console.print(f"[red]No work unit found matching '{work_unit_id}'[/red]")
            raise SystemExit(4)  # NOT_FOUND

        if len(matching_files) > 1:
            if ctx.obj.json_output:
                response = JSONResponse(
                    status="error",
                    command="remove work-unit",
                    data={
                        "message": f"Multiple work units match '{work_unit_id}'",
                        "matches": [f.stem for f in matching_files],
                    },
                )
                click.echo(response.to_json())
            else:
                console.print(f"[yellow]Multiple work units match '{work_unit_id}':[/yellow]")
                for f in matching_files:
                    console.print(f"  - {f.stem}")
                console.print("[yellow]Please be more specific.[/yellow]")
            raise SystemExit(1)

        file_path = matching_files[0]

    work_unit_name = file_path.stem

    # Confirm removal unless --yes flag is set
    if (
        not yes
        and not ctx.obj.json_output
        and not Confirm.ask(f"Remove work unit '[cyan]{work_unit_name}[/cyan]'?")
    ):
        info("Cancelled.")
        return

    # Remove the file
    try:
        file_path.unlink()
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="remove work-unit",
                data={
                    "removed": True,
                    "work_unit_id": work_unit_name,
                    "file": str(file_path),
                },
            )
            click.echo(response.to_json())
        else:
            success(f"Removed work unit: {work_unit_name}")
    except OSError as e:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove work-unit",
                data={"message": f"Failed to remove work unit: {e}"},
            )
            click.echo(response.to_json())
        else:
            console.print(f"[red]Failed to remove work unit: {e}[/red]")
        raise SystemExit(1) from e
