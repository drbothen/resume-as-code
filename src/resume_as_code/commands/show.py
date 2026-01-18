"""Show command for displaying detailed resource information."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click
from ruamel.yaml import YAML

from resume_as_code.config import get_config
from resume_as_code.models.errors import NotFoundError
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.board_role_service import BoardRoleService
from resume_as_code.services.certification_service import CertificationService
from resume_as_code.services.education_service import EducationService
from resume_as_code.services.highlight_service import HighlightService
from resume_as_code.services.position_service import PositionService
from resume_as_code.services.publication_service import PublicationService
from resume_as_code.utils.console import console, json_output
from resume_as_code.utils.errors import handle_errors


@click.group("show")
def show_group() -> None:
    """Show detailed information about resources."""


@show_group.command("position")
@click.argument("position_id")
@click.pass_context
@handle_errors
def show_position(ctx: click.Context, position_id: str) -> None:
    """Show details of a specific position.

    POSITION_ID is the unique position identifier (e.g., pos-techcorp-senior).
    """
    config = get_config()
    service = PositionService(config.positions_path)
    position = service.get_position(position_id)

    if not position:
        raise NotFoundError(f"Position not found: {position_id}")

    # Find related work units
    related_work_units = _find_work_units_for_position(position_id, config.work_units_dir)

    # Get promotion chain
    chain = service.get_promotion_chain(position_id)

    if ctx.obj.json_output:
        _output_position_json(position, related_work_units, chain)
    else:
        _output_position_rich(position, related_work_units, chain)


def _find_work_units_for_position(position_id: str, work_units_dir: Path) -> list[dict[str, Any]]:
    """Find work units that reference a position."""
    if not work_units_dir.exists():
        return []

    yaml = YAML()
    yaml.preserve_quotes = True
    related: list[dict[str, Any]] = []

    for yaml_file in work_units_dir.glob("*.yaml"):
        try:
            with yaml_file.open() as f:
                data = yaml.load(f)
                if data and isinstance(data, dict) and data.get("position_id") == position_id:
                    related.append(data)
        except Exception:
            continue

    return related


def _output_position_json(
    position: Any, work_units: list[dict[str, Any]], chain: list[Any]
) -> None:
    """Output position details as JSON."""
    from resume_as_code.models.position import Position
    from resume_as_code.services.position_service import format_scope_line

    pos_data = {
        "id": position.id,
        "employer": position.employer,
        "title": position.title,
        "location": position.location,
        "start_date": position.start_date,
        "end_date": position.end_date,
        "dates": position.format_date_range(),
        "employment_type": position.employment_type,
        "promoted_from": position.promoted_from,
        "is_current": position.is_current,
        "has_scope": position.scope is not None,
        "scope": position.scope.model_dump(exclude_none=True) if position.scope else None,
        "scope_line": format_scope_line(position) if position.scope else None,
    }

    wu_data = [{"id": wu.get("id"), "title": wu.get("title")} for wu in work_units]

    chain_data = [
        {"id": p.id, "title": p.title, "employer": p.employer}
        for p in chain
        if isinstance(p, Position)
    ]

    response = JSONResponse(
        status="success",
        command="show position",
        data={
            "position": pos_data,
            "work_units": wu_data,
            "work_unit_count": len(wu_data),
            "promotion_chain": chain_data,
        },
    )
    json_output(response.to_json())


def _output_position_rich(
    position: Any, work_units: list[dict[str, Any]], chain: list[Any]
) -> None:
    """Output position details with Rich formatting."""
    from resume_as_code.services.position_service import format_scope_line

    # Position header
    console.print(f"\n[bold cyan]{position.title}[/bold cyan]")
    console.print(f"[green]{position.employer}[/green]")

    if position.location:
        console.print(f"[dim]{position.location}[/dim]")

    # Scope indicators (executive positions)
    if position.scope:
        scope_line = format_scope_line(position)
        if scope_line:
            console.print(f"[italic magenta]{scope_line}[/italic magenta]")

    console.print(f"\n{position.format_date_range()}")

    if position.employment_type:
        console.print(f"Type: {position.employment_type}")

    if position.is_current:
        console.print("[cyan](Current Position)[/cyan]")

    # Work units section
    console.print("")
    if work_units:
        console.print(f"[bold]Work Units ({len(work_units)}):[/bold]")
        for wu in work_units:
            title = str(wu.get("title", ""))[:50]
            console.print(f"  • {wu.get('id')}: {title}...")
    else:
        console.print("[dim]No work units reference this position[/dim]")

    # Promotion chain section
    if len(chain) > 1:
        console.print("")
        console.print("[bold]Career Progression:[/bold]")
        for i, pos in enumerate(chain):
            prefix = "  └─" if i == len(chain) - 1 else "  ├─"
            marker = " [cyan](current)[/cyan]" if pos.id == position.id else ""
            console.print(f"{prefix} {pos.title}{marker}")

    console.print("")


@show_group.command("work-unit")
@click.argument("work_unit_id")
@click.pass_context
@handle_errors
def show_work_unit(ctx: click.Context, work_unit_id: str) -> None:
    """Show details of a specific work unit.

    WORK_UNIT_ID is the work unit identifier (e.g., wu-2024-01-30-project).
    """
    config = get_config()
    work_units_dir = config.work_units_dir

    # Find the work unit file
    file_path = work_units_dir / f"{work_unit_id}.yaml"

    if not file_path.exists():
        # Try partial match
        matching_files = list(work_units_dir.glob(f"*{work_unit_id}*.yaml"))
        if not matching_files:
            raise NotFoundError(f"Work unit not found: {work_unit_id}")
        if len(matching_files) > 1:
            console.print(f"[yellow]Multiple work units match '{work_unit_id}':[/yellow]")
            for match in matching_files:
                console.print(f"  - {match.stem}")
            console.print("[yellow]Please be more specific.[/yellow]")
            raise SystemExit(1)
        file_path = matching_files[0]

    # Load the work unit
    yaml = YAML()
    yaml.preserve_quotes = True
    with file_path.open() as wu_file:
        work_unit = yaml.load(wu_file)

    if not work_unit:
        raise NotFoundError(f"Work unit file is empty: {work_unit_id}")

    if ctx.obj.json_output:
        _output_work_unit_json(work_unit, file_path)
    else:
        _output_work_unit_rich(work_unit, file_path)


def _output_work_unit_json(work_unit: dict[str, Any], file_path: Path) -> None:
    """Output work unit details as JSON."""
    response = JSONResponse(
        status="success",
        command="show work-unit",
        data={
            "work_unit": {
                "id": work_unit.get("id"),
                "title": work_unit.get("title"),
                "position_id": work_unit.get("position_id"),
                "date": work_unit.get("date"),
                "problem": work_unit.get("problem"),
                "actions": work_unit.get("actions", []),
                "result": work_unit.get("result"),
                "skills": work_unit.get("skills", []),
                "tags": work_unit.get("tags", []),
                "archetype": work_unit.get("archetype"),
            },
            "file": str(file_path),
        },
    )
    json_output(response.to_json())


def _output_work_unit_rich(work_unit: dict[str, Any], file_path: Path) -> None:
    """Output work unit details with Rich formatting."""
    # Header
    console.print(f"\n[bold cyan]{work_unit.get('title', 'Untitled')}[/bold cyan]")

    if work_unit.get("id"):
        console.print(f"[dim]ID: {work_unit.get('id')}[/dim]")

    if work_unit.get("position_id"):
        console.print(f"[green]Position: {work_unit.get('position_id')}[/green]")

    if work_unit.get("date"):
        console.print(f"Date: {work_unit.get('date')}")

    if work_unit.get("archetype"):
        console.print(f"Archetype: {work_unit.get('archetype')}")

    # PAR sections
    console.print("")
    if work_unit.get("problem"):
        console.print("[bold]Problem:[/bold]")
        console.print(f"  {work_unit.get('problem')}")

    if work_unit.get("actions"):
        console.print("\n[bold]Actions:[/bold]")
        actions = work_unit.get("actions", [])
        if isinstance(actions, list):
            for action in actions:
                console.print(f"  • {action}")
        else:
            console.print(f"  {actions}")

    if work_unit.get("result"):
        console.print("\n[bold]Result:[/bold]")
        console.print(f"  {work_unit.get('result')}")

    # Skills and tags
    if work_unit.get("skills"):
        console.print("\n[bold]Skills:[/bold]")
        skills = work_unit.get("skills", [])
        console.print(f"  {', '.join(skills)}")

    if work_unit.get("tags"):
        console.print("\n[bold]Tags:[/bold]")
        tags = work_unit.get("tags", [])
        console.print(f"  {', '.join(tags)}")

    console.print(f"\n[dim]File: {file_path}[/dim]")
    console.print("")


@show_group.command("certification")
@click.argument("name")
@click.pass_context
@handle_errors
def show_certification(ctx: click.Context, name: str) -> None:
    """Show details of a specific certification.

    NAME is the certification name (partial match supported).
    """
    service = CertificationService(config_path=ctx.obj.effective_config_path)
    matching = service.find_certifications_by_name(name)

    if not matching:
        raise NotFoundError(f"Certification not found: {name}")

    if len(matching) > 1:
        console.print(f"[yellow]Multiple certifications match '{name}':[/yellow]")
        for cert in matching:
            console.print(f"  - {cert.name}")
        console.print("[yellow]Please be more specific.[/yellow]")
        raise SystemExit(1)

    cert = matching[0]

    if ctx.obj.json_output:
        _output_certification_json(cert)
    else:
        _output_certification_rich(cert)


def _output_certification_json(cert: Any) -> None:
    """Output certification details as JSON."""
    from resume_as_code.models.certification import Certification

    if isinstance(cert, Certification):
        cert_data = {
            "name": cert.name,
            "issuer": cert.issuer,
            "date": cert.date,
            "expires": cert.expires,
            "credential_id": cert.credential_id,
            "url": str(cert.url) if cert.url else None,
            "display": cert.display,
            "status": cert.get_status(),
        }

        response = JSONResponse(
            status="success",
            command="show certification",
            data={"certification": cert_data},
        )
        json_output(response.to_json())


def _output_certification_rich(cert: Any) -> None:
    """Output certification details with Rich formatting."""
    from resume_as_code.models.certification import Certification

    if not isinstance(cert, Certification):
        return

    # Header
    console.print(f"\n[bold cyan]{cert.name}[/bold cyan]")

    if cert.issuer:
        console.print(f"[green]{cert.issuer}[/green]")

    # Dates
    console.print("")
    if cert.date:
        console.print(f"[bold]Obtained:[/bold] {cert.date}")

    if cert.expires:
        console.print(f"[bold]Expires:[/bold] {cert.expires}")
    else:
        console.print("[bold]Expires:[/bold] [dim]Never[/dim]")

    # Status with highlighting
    status = cert.get_status()
    if status == "expired":
        console.print("[bold]Status:[/bold] [red]Expired[/red]")
    elif status == "expires_soon":
        console.print("[bold]Status:[/bold] [yellow]Expires Soon[/yellow]")
    else:
        console.print("[bold]Status:[/bold] [green]Active[/green]")

    # Credential details
    if cert.credential_id:
        console.print(f"\n[bold]Credential ID:[/bold] {cert.credential_id}")

    if cert.url:
        console.print(f"[bold]URL:[/bold] {cert.url}")

    # Display setting
    if not cert.display:
        console.print("\n[dim]Note: This certification is hidden from resume output[/dim]")

    console.print("")


@show_group.command("education")
@click.argument("degree")
@click.pass_context
@handle_errors
def show_education(ctx: click.Context, degree: str) -> None:
    """Show details of a specific education entry.

    DEGREE is the degree name (partial match supported).
    """
    service = EducationService(config_path=ctx.obj.effective_config_path)
    matching = service.find_educations_by_degree(degree)

    if not matching:
        raise NotFoundError(f"Education not found: {degree}")

    if len(matching) > 1:
        console.print(f"[yellow]Multiple education entries match '{degree}':[/yellow]")
        for edu in matching:
            console.print(f"  - {edu.degree}")
        console.print("[yellow]Please be more specific.[/yellow]")
        raise SystemExit(1)

    edu = matching[0]

    if ctx.obj.json_output:
        _output_education_json(edu)
    else:
        _output_education_rich(edu)


def _output_education_json(edu: Any) -> None:
    """Output education details as JSON."""
    from resume_as_code.models.education import Education

    if isinstance(edu, Education):
        edu_data = {
            "degree": edu.degree,
            "institution": edu.institution,
            "graduation_year": edu.graduation_year,
            "honors": edu.honors,
            "gpa": edu.gpa,
            "display": edu.display,
            "formatted": edu.format_display(),
        }

        response = JSONResponse(
            status="success",
            command="show education",
            data={"education": edu_data},
        )
        json_output(response.to_json())


def _output_education_rich(edu: Any) -> None:
    """Output education details with Rich formatting."""
    from resume_as_code.models.education import Education

    if not isinstance(edu, Education):
        return

    # Header
    console.print(f"\n[bold cyan]{edu.degree}[/bold cyan]")
    console.print(f"[green]{edu.institution}[/green]")

    # Graduation Year
    console.print("")
    if edu.graduation_year:
        console.print(f"[bold]Year:[/bold] {edu.graduation_year}")

    # Honors
    if edu.honors:
        console.print(f"[bold]Honors:[/bold] {edu.honors}")

    # GPA
    if edu.gpa:
        console.print(f"[bold]GPA:[/bold] {edu.gpa}")

    # Display setting
    if not edu.display:
        console.print("\n[dim]Note: This education is hidden from resume output[/dim]")

    console.print("")


@show_group.command("highlight")
@click.argument("index", type=int)
@click.pass_context
@handle_errors
def show_highlight(ctx: click.Context, index: int) -> None:
    """Show details of a specific career highlight.

    INDEX is the 0-based index of the highlight (use 'list highlights' to see indices).
    """
    service = HighlightService(config_path=ctx.obj.effective_config_path)
    highlights = service.load_highlights()

    if not highlights:
        raise NotFoundError("No career highlights found")

    if index < 0 or index >= len(highlights):
        console.print(f"[red]Invalid index {index}. Valid range: 0-{len(highlights) - 1}[/red]")
        raise SystemExit(1)

    highlight_text = highlights[index]

    if ctx.obj.json_output:
        _output_highlight_json(index, highlight_text, len(highlights))
    else:
        _output_highlight_rich(index, highlight_text, len(highlights))


def _output_highlight_json(index: int, text: str, total: int) -> None:
    """Output highlight details as JSON."""
    response = JSONResponse(
        status="success",
        command="show highlight",
        data={
            "highlight": {
                "index": index,
                "text": text,
            },
            "total_highlights": total,
        },
    )
    json_output(response.to_json())


def _output_highlight_rich(index: int, text: str, total: int) -> None:
    """Output highlight details with Rich formatting."""
    console.print(f"\n[bold cyan]Career Highlight #{index}[/bold cyan]")
    console.print(f"\n{text}")
    console.print(f"\n[dim]Highlight {index + 1} of {total}[/dim]")
    console.print("")


@show_group.command("board-role")
@click.argument("organization")
@click.pass_context
@handle_errors
def show_board_role(ctx: click.Context, organization: str) -> None:
    """Show details of a specific board role.

    ORGANIZATION is the organization name (partial match supported).
    """
    service = BoardRoleService(config_path=ctx.obj.effective_config_path)
    matching = service.find_board_roles_by_organization(organization)

    if not matching:
        raise NotFoundError(f"Board role not found: {organization}")

    if len(matching) > 1:
        console.print(f"[yellow]Multiple board roles match '{organization}':[/yellow]")
        for br in matching:
            console.print(f"  - {br.organization}: {br.role}")
        console.print("[yellow]Please be more specific.[/yellow]")
        raise SystemExit(1)

    board_role = matching[0]

    if ctx.obj.json_output:
        _output_board_role_json(board_role)
    else:
        _output_board_role_rich(board_role)


def _output_board_role_json(board_role: Any) -> None:
    """Output board role details as JSON."""
    from resume_as_code.models.board_role import BoardRole

    if isinstance(board_role, BoardRole):
        role_data = {
            "organization": board_role.organization,
            "role": board_role.role,
            "type": board_role.type,
            "start_date": board_role.start_date,
            "end_date": board_role.end_date,
            "focus": board_role.focus,
            "display": board_role.display,
            "is_current": board_role.is_current,
            "date_range": board_role.format_date_range(),
        }

        response = JSONResponse(
            status="success",
            command="show board-role",
            data={"board_role": role_data},
        )
        json_output(response.to_json())


def _output_board_role_rich(board_role: Any) -> None:
    """Output board role details with Rich formatting."""
    from resume_as_code.models.board_role import BoardRole

    if not isinstance(board_role, BoardRole):
        return

    # Header
    console.print(f"\n[bold cyan]{board_role.role}[/bold cyan]")
    console.print(f"[green]{board_role.organization}[/green]")

    # Type
    console.print("")
    console.print(f"[bold]Type:[/bold] {board_role.type}")

    # Dates
    console.print(f"[bold]Dates:[/bold] {board_role.format_date_range()}")

    # Status
    if board_role.is_current:
        console.print("[bold]Status:[/bold] [green]Current[/green]")
    else:
        console.print("[bold]Status:[/bold] [dim]Past[/dim]")

    # Focus
    if board_role.focus:
        console.print(f"\n[bold]Focus:[/bold]\n  {board_role.focus}")

    # Display setting
    if not board_role.display:
        console.print("\n[dim]Note: This board role is hidden from resume output[/dim]")

    console.print("")


@show_group.command("publication")
@click.argument("title")
@click.pass_context
@handle_errors
def show_publication(ctx: click.Context, title: str) -> None:
    """Show details of a publication or speaking engagement.

    TITLE is the publication title (partial match supported).
    """
    service = PublicationService(config_path=ctx.obj.effective_config_path)
    matches = service.find_publications_by_title(title)

    if not matches:
        raise NotFoundError(f"Publication not found: {title}")

    if len(matches) > 1 and not ctx.obj.json_output:
        console.print(f"[yellow]Multiple matches found for '{title}':[/yellow]")
        for i, pub in enumerate(matches, 1):
            console.print(f"  {i}. {pub.title} ({pub.venue}, {pub.date})")
        console.print(
            "\n[dim]Showing first match. Be more specific to view a different publication.[/dim]\n"
        )

    publication = matches[0]

    if ctx.obj.json_output:
        _output_publication_json(publication)
    else:
        _output_publication_details(publication)


def _output_publication_json(publication: Any) -> None:
    """Output publication details as JSON."""
    data: dict[str, Any] = {
        "title": publication.title,
        "type": publication.type,
        "venue": publication.venue,
        "date": publication.date,
        "url": str(publication.url) if publication.url else None,
        "display": publication.display,
    }
    # Add new fields if they exist (Story 8.2)
    if hasattr(publication, "topics") and publication.topics:
        data["topics"] = publication.topics
    if hasattr(publication, "abstract") and publication.abstract:
        data["abstract"] = publication.abstract
    response = JSONResponse(
        status="success",
        command="show publication",
        data=data,
    )
    click.echo(response.to_json())


def _output_publication_details(publication: Any) -> None:
    """Output publication details in rich format."""
    console.print(f"[bold cyan]{publication.title}[/bold cyan]")
    console.print(f"[dim]{'─' * 50}[/dim]")

    console.print(f"[bold]Type:[/bold] {publication.type}")
    console.print(f"[bold]Venue:[/bold] {publication.venue}")
    console.print(f"[bold]Date:[/bold] {publication.date}")

    if publication.url:
        console.print(f"[bold]URL:[/bold] {publication.url}")

    # Show topics if present (Story 8.2)
    if hasattr(publication, "topics") and publication.topics:
        console.print(f"[bold]Topics:[/bold] {', '.join(publication.topics)}")

    # Show abstract if present (Story 8.2)
    if hasattr(publication, "abstract") and publication.abstract:
        console.print(f"[bold]Abstract:[/bold] {publication.abstract}")

    # Display setting
    if not publication.display:
        console.print("\n[dim]Note: This publication is hidden from resume output[/dim]")

    console.print("")
