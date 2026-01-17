"""Remove command for deleting resources."""

from __future__ import annotations

import click
from rich.prompt import Confirm

from resume_as_code.config import get_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.board_role_service import BoardRoleService
from resume_as_code.services.certification_service import CertificationService
from resume_as_code.services.education_service import EducationService
from resume_as_code.services.highlight_service import HighlightService
from resume_as_code.services.position_service import PositionService
from resume_as_code.services.publication_service import PublicationService
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
    service = CertificationService(config_path=ctx.obj.effective_config_path)

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


@remove_group.command("education")
@click.argument("degree")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
@handle_errors
def remove_education(ctx: click.Context, degree: str, yes: bool) -> None:
    """Remove an education entry by degree name.

    Performs case-insensitive partial matching on the degree name.
    If multiple education entries match, asks for clarification.
    """
    service = EducationService(config_path=ctx.obj.effective_config_path)

    # Find matching education entries
    matching = service.find_educations_by_degree(degree)

    if not matching:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove education",
                data={"message": f"No education entry found matching '{degree}'"},
            )
            click.echo(response.to_json())
        else:
            console.print(f"[red]No education entry found matching '{degree}'[/red]")
        raise SystemExit(4)  # NOT_FOUND

    if len(matching) > 1:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove education",
                data={
                    "message": f"Multiple education entries match '{degree}'",
                    "matches": [edu.degree for edu in matching],
                },
            )
            click.echo(response.to_json())
        else:
            console.print(f"[yellow]Multiple education entries match '{degree}':[/yellow]")
            for edu in matching:
                console.print(f"  - {edu.degree}")
            console.print("[yellow]Please be more specific.[/yellow]")
        raise SystemExit(1)

    edu = matching[0]

    # Confirm removal unless --yes flag is set
    if (
        not yes
        and not ctx.obj.json_output
        and not Confirm.ask(f"Remove education '[cyan]{edu.degree}[/cyan]'?")
    ):
        info("Cancelled.")
        return

    # Remove the education
    removed = service.remove_education(edu.degree)

    if removed:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="remove education",
                data={
                    "removed": True,
                    "degree": edu.degree,
                },
            )
            click.echo(response.to_json())
        else:
            success(f"Removed education: {edu.degree}")
    else:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove education",
                data={"message": "Failed to remove education"},
            )
            click.echo(response.to_json())
        else:
            console.print("[red]Failed to remove education[/red]")
        raise SystemExit(1)


@remove_group.command("highlight")
@click.argument("index", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
@handle_errors
def remove_highlight(ctx: click.Context, index: int, yes: bool) -> None:
    """Remove a career highlight by index (0-indexed).

    Use 'resume list highlights' to see indices.
    """
    service = HighlightService(config_path=ctx.obj.effective_config_path)
    highlights = service.load_highlights()

    if not highlights:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove highlight",
                data={"message": "No career highlights found"},
            )
            click.echo(response.to_json())
        else:
            console.print("[red]No career highlights found[/red]")
        raise SystemExit(4)  # NOT_FOUND

    if index < 0 or index >= len(highlights):
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove highlight",
                data={
                    "message": f"Invalid index {index}. Valid range: 0-{len(highlights) - 1}",
                },
            )
            click.echo(response.to_json())
        else:
            console.print(f"[red]Invalid index {index}. Valid range: 0-{len(highlights) - 1}[/red]")
        raise SystemExit(1)

    highlight_text = highlights[index]

    # Confirm removal unless --yes flag is set
    if (
        not yes
        and not ctx.obj.json_output
        and not Confirm.ask(f"Remove highlight #{index}: '[cyan]{highlight_text}[/cyan]'?")
    ):
        info("Cancelled.")
        return

    # Remove the highlight
    removed = service.remove_highlight(index)

    if removed:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="remove highlight",
                data={
                    "removed": True,
                    "index": index,
                    "text": highlight_text,
                },
            )
            click.echo(response.to_json())
        else:
            success(f"Removed highlight #{index}")
    else:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove highlight",
                data={"message": "Failed to remove highlight"},
            )
            click.echo(response.to_json())
        else:
            console.print("[red]Failed to remove highlight[/red]")
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


@remove_group.command("board-role")
@click.argument("organization")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
@handle_errors
def remove_board_role(ctx: click.Context, organization: str, yes: bool) -> None:
    """Remove a board role by organization name.

    Performs case-insensitive partial matching on the organization name.
    If multiple board roles match, asks for clarification.
    """
    service = BoardRoleService(config_path=ctx.obj.effective_config_path)

    # Find matching board roles
    matching = service.find_board_roles_by_organization(organization)

    if not matching:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove board-role",
                data={"message": f"No board role found matching '{organization}'"},
            )
            click.echo(response.to_json())
        else:
            console.print(f"[red]No board role found matching '{organization}'[/red]")
        raise SystemExit(4)  # NOT_FOUND

    if len(matching) > 1:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove board-role",
                data={
                    "message": f"Multiple board roles match '{organization}'",
                    "matches": [br.organization for br in matching],
                },
            )
            click.echo(response.to_json())
        else:
            console.print(f"[yellow]Multiple board roles match '{organization}':[/yellow]")
            for br in matching:
                console.print(f"  - {br.organization}: {br.role}")
            console.print("[yellow]Please be more specific.[/yellow]")
        raise SystemExit(1)

    board_role = matching[0]

    # Confirm removal unless --yes flag is set
    if (
        not yes
        and not ctx.obj.json_output
        and not Confirm.ask(
            f"Remove board role '[cyan]{board_role.role}[/cyan]' at '{board_role.organization}'?"
        )
    ):
        info("Cancelled.")
        return

    # Remove the board role
    removed = service.remove_board_role(board_role.organization)

    if removed:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="remove board-role",
                data={
                    "removed": True,
                    "organization": board_role.organization,
                    "role": board_role.role,
                },
            )
            click.echo(response.to_json())
        else:
            success(f"Removed board role: {board_role.role}")
    else:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove board-role",
                data={"message": "Failed to remove board role"},
            )
            click.echo(response.to_json())
        else:
            console.print("[red]Failed to remove board role[/red]")
        raise SystemExit(1)


@remove_group.command("publication")
@click.argument("title")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
@handle_errors
def remove_publication(ctx: click.Context, title: str, yes: bool) -> None:
    """Remove a publication by title.

    Performs case-insensitive partial matching on the publication title.
    If multiple publications match, asks for clarification.
    """
    service = PublicationService(config_path=ctx.obj.effective_config_path)

    # Find matching publications
    matching = service.find_publications_by_title(title)

    if not matching:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove publication",
                data={"message": f"No publication found matching '{title}'"},
            )
            click.echo(response.to_json())
        else:
            warning(f"No publication found matching '{title}'")
        raise SystemExit(4)  # NOT_FOUND exit code

    if len(matching) > 1 and not ctx.obj.json_output:
        console.print(f"[yellow]Multiple publications match '{title}':[/yellow]")
        for i, pub in enumerate(matching, 1):
            console.print(f"  {i}. {pub.title} ({pub.venue}, {pub.date})")
        console.print(
            "\n[dim]Removing first match. Be more specific to remove a different publication.[/dim]"
        )

    publication = matching[0]

    # Confirm unless --yes flag
    if not yes:
        if ctx.obj.json_output:
            # In JSON mode, --yes is required for actual deletion
            response = JSONResponse(
                status="error",
                command="remove publication",
                data={
                    "message": "Confirmation required. Use --yes flag to confirm.",
                    "publication": publication.title,
                },
            )
            click.echo(response.to_json())
            raise SystemExit(1)

        if not Confirm.ask(f"Remove publication '{publication.title}'?"):
            info("Operation cancelled")
            return

    # Perform removal
    if service.remove_publication(publication.title):
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="remove publication",
                data={
                    "publication_removed": True,
                    "title": publication.title,
                    "venue": publication.venue,
                },
            )
            click.echo(response.to_json())
        else:
            success(f"Removed publication: {publication.title}")
    else:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="error",
                command="remove publication",
                data={"message": "Failed to remove publication"},
            )
            click.echo(response.to_json())
        else:
            console.print("[red]Failed to remove publication[/red]")
        raise SystemExit(1)
