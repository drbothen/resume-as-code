"""List command for browsing Work Units, Positions, and Certifications."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import click
from rich.table import Table
from ruamel.yaml import YAML

from resume_as_code.config import get_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.board_role_service import BoardRoleService
from resume_as_code.services.certification_service import CertificationService
from resume_as_code.services.education_service import EducationService
from resume_as_code.services.highlight_service import HighlightService
from resume_as_code.services.position_service import PositionService
from resume_as_code.services.publication_service import PublicationService
from resume_as_code.utils.console import console, info, json_output
from resume_as_code.utils.errors import handle_errors

SortField = Literal["date", "title", "confidence"]


@click.group("list", invoke_without_command=True)
@click.option(
    "--filter",
    "-f",
    "filter_strs",
    multiple=True,
    help="Filter (tag:, confidence:, archetype: prefix or free text). Repeatable.",
)
@click.option(
    "--sort",
    "-s",
    type=click.Choice(["date", "title", "confidence"]),
    default="date",
    help="Sort field (default: date)",
)
@click.option(
    "--reverse",
    "-r",
    is_flag=True,
    help="Reverse sort order (ascending)",
)
@click.option(
    "--stats",
    is_flag=True,
    help="Show archetype distribution statistics",
)
@click.pass_context
@handle_errors
def list_command(
    ctx: click.Context,
    filter_strs: tuple[str, ...],
    sort: SortField,
    reverse: bool,
    stats: bool,
) -> None:
    """List resources (work-units by default, or use subcommands).

    Without a subcommand, lists Work Units.
    Use 'resume list positions' to list employment positions.

    Filter syntax for work units:
      tag:<value>        - Filter by tag
      confidence:<value> - Filter by confidence level
      archetype:<value>  - Filter by archetype (e.g., incident, greenfield)
      <text>             - Free text search in ID, title, date

    Multiple --filter options use AND logic (all must match).
    """
    # If no subcommand was invoked, list work units (backward compatible)
    if ctx.invoked_subcommand is None:
        _list_work_units(ctx, filter_strs, sort, reverse, stats)


def _list_work_units(
    ctx: click.Context,
    filter_strs: tuple[str, ...],
    sort: SortField,
    reverse: bool,
    stats: bool = False,
) -> None:
    """List work units with filtering and sorting."""
    config = get_config()

    # Load all Work Units
    work_units = _load_all_work_units(config.work_units_dir)

    # Handle empty state
    if not work_units:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="list",
                data={"work_units": [], "count": 0},
            )
            json_output(response.to_json())
        else:
            info("No Work Units found. Run `resume new work-unit` to create one.")
        return

    # Apply filters (AND logic - each filter must match)
    for filter_str in filter_strs:
        work_units = _apply_filter(work_units, filter_str)

    # Apply sort
    work_units = _apply_sort(work_units, sort, reverse)

    # Output
    if ctx.obj.json_output:
        _output_json(work_units, show_stats=stats)
    else:
        _output_table(work_units)
        if stats:
            _output_archetype_stats(work_units)


@list_command.command("positions")
@click.pass_context
@handle_errors
def list_positions(ctx: click.Context) -> None:
    """List all employment positions."""
    config = get_config()
    service = PositionService(config.positions_path)
    positions = service.load_positions()

    if not positions:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="list positions",
                data={"positions": [], "count": 0},
            )
            json_output(response.to_json())
        else:
            info("No positions found.")
            console.print("[dim]Create one with: resume new position[/dim]")
        return

    # Sort by start_date descending (most recent first)
    sorted_positions = sorted(
        positions.values(),
        key=lambda p: p.start_date,
        reverse=True,
    )

    if ctx.obj.json_output:
        _output_positions_json(sorted_positions)
    else:
        _output_positions_table(sorted_positions)


@list_command.command("certifications")
@click.option(
    "--verbose",
    "-v",
    "verbose",
    is_flag=True,
    help="Show source file paths (Story 11.2)",
)
@click.pass_context
@handle_errors
def list_certifications(ctx: click.Context, verbose: bool) -> None:
    """List all certifications with expiration status."""
    service = CertificationService(config_path=ctx.obj.effective_config_path)
    certifications = service.load_certifications()

    if not certifications:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="list certifications",
                data={"certifications": [], "count": 0},
            )
            json_output(response.to_json())
        else:
            info("No certifications found.")
            console.print("[dim]Create one with: resume new certification[/dim]")
        return

    if ctx.obj.json_output:
        _output_certifications_json(certifications, verbose=verbose)
    else:
        _output_certifications_table(certifications, verbose=verbose)


@list_command.command("education")
@click.option(
    "--verbose",
    "-v",
    "verbose",
    is_flag=True,
    help="Show source file paths (Story 11.2)",
)
@click.pass_context
@handle_errors
def list_education(ctx: click.Context, verbose: bool) -> None:
    """List all education entries."""
    service = EducationService(config_path=ctx.obj.effective_config_path)
    education = service.load_education()

    if not education:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="list education",
                data={"education": [], "count": 0},
            )
            json_output(response.to_json())
        else:
            info("No education entries found.")
            console.print("[dim]Create one with: resume new education[/dim]")
        return

    if ctx.obj.json_output:
        _output_education_json(education, verbose=verbose)
    else:
        _output_education_table(education, verbose=verbose)


@list_command.command("highlights")
@click.option(
    "--verbose",
    "-v",
    "verbose",
    is_flag=True,
    help="Show source file paths (Story 11.2)",
)
@click.pass_context
@handle_errors
def list_highlights(ctx: click.Context, verbose: bool) -> None:
    """List all career highlights."""
    service = HighlightService(config_path=ctx.obj.effective_config_path)
    highlights = service.load_highlights()

    if not highlights:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="list highlights",
                data={"highlights": [], "count": 0},
            )
            json_output(response.to_json())
        else:
            info("No career highlights found.")
            console.print("[dim]Create one with: resume new highlight[/dim]")
        return

    if ctx.obj.json_output:
        _output_highlights_json(highlights, verbose=verbose, service=service)
    else:
        _output_highlights_table(highlights, verbose=verbose, service=service)


@list_command.command("board-roles")
@click.option(
    "--verbose",
    "-v",
    "verbose",
    is_flag=True,
    help="Show source file paths (Story 11.2)",
)
@click.pass_context
@handle_errors
def list_board_roles(ctx: click.Context, verbose: bool) -> None:
    """List all board and advisory roles."""
    service = BoardRoleService(config_path=ctx.obj.effective_config_path)
    board_roles = service.load_board_roles()

    if not board_roles:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="list board-roles",
                data={"board_roles": [], "count": 0},
            )
            json_output(response.to_json())
        else:
            info("No board roles found.")
            console.print("[dim]Create one with: resume new board-role[/dim]")
        return

    if ctx.obj.json_output:
        _output_board_roles_json(board_roles, verbose=verbose)
    else:
        _output_board_roles_table(board_roles, verbose=verbose)


def _output_highlights_json(
    highlights: list[str],
    verbose: bool = False,
    service: HighlightService | None = None,
) -> None:
    """Output highlights as JSON.

    Args:
        highlights: List of highlight strings.
        verbose: If True, include source file paths (Story 11.2).
        service: HighlightService to get source info from.
    """
    from resume_as_code.data_loader import get_storage_mode

    highlight_data = [{"index": idx, "text": text} for idx, text in enumerate(highlights)]

    # Add storage mode info in verbose mode
    storage_info = None
    if verbose and service:
        mode, path = get_storage_mode(service.project_path, "highlights")
        storage_info = {
            "mode": mode,
            "path": str(path) if path else None,
        }

    response = JSONResponse(
        status="success",
        command="list highlights",
        data={
            "highlights": highlight_data,
            "count": len(highlight_data),
            **({"storage": storage_info} if storage_info else {}),
        },
    )
    json_output(response.to_json())


def _output_highlights_table(
    highlights: list[str],
    verbose: bool = False,
    service: HighlightService | None = None,
) -> None:
    """Output highlights as Rich table.

    Args:
        highlights: List of highlight strings.
        verbose: If True, show storage mode info (Story 11.2).
        service: HighlightService to get source info from.
    """
    from resume_as_code.data_loader import get_storage_mode

    table = Table(title="Career Highlights")
    table.add_column("#", style="dim", width=3)
    table.add_column("Highlight", style="cyan")

    for idx, highlight in enumerate(highlights):
        table.add_row(str(idx), highlight)

    console.print(table)
    console.print(f"\n[dim]{len(highlights)} Career Highlight(s)[/dim]")

    # Show storage info in verbose mode (Story 11.2)
    if verbose and service:
        mode, path = get_storage_mode(service.project_path, "highlights")
        if mode == "dir" and path:
            console.print(f"[dim]Source: {path}/[/dim]")
        elif mode == "file" and path:
            console.print(f"[dim]Source: {path}[/dim]")
        else:
            console.print("[dim]Source: embedded in .resume.yaml[/dim]")

    if len(highlights) > 4:
        console.print(
            "\n[yellow]Tip: Research suggests a maximum of 4 career highlights "
            "for optimal impact.[/yellow]"
        )


def _output_board_roles_json(board_roles: list[Any], verbose: bool = False) -> None:
    """Output board roles as JSON.

    Args:
        board_roles: List of BoardRole objects.
        verbose: If True, include source file paths (Story 11.2).
    """
    from resume_as_code.models.board_role import BoardRole

    role_data = []
    for role in board_roles:
        if isinstance(role, BoardRole):
            data: dict[str, Any] = {
                "organization": role.organization,
                "role": role.role,
                "type": role.type,
                "start_date": role.start_date,
                "end_date": role.end_date,
                "focus": role.focus,
                "display": role.display,
                "is_current": role.is_current,
                "date_range": role.format_date_range(),
            }
            # Add source file in verbose mode (Story 11.2)
            if verbose:
                source_file = getattr(role, "_source_file", None)
                data["source_file"] = str(source_file) if source_file else None
            role_data.append(data)

    response = JSONResponse(
        status="success",
        command="list board-roles",
        data={"board_roles": role_data, "count": len(role_data)},
    )
    json_output(response.to_json())


def _output_board_roles_table(board_roles: list[Any], verbose: bool = False) -> None:
    """Output board roles as Rich table.

    Args:
        board_roles: List of BoardRole objects.
        verbose: If True, show source file paths (Story 11.2).
    """
    from resume_as_code.models.board_role import BoardRole

    table = Table(title="Board & Advisory Roles")
    table.add_column("Organization", style="cyan", no_wrap=True)
    table.add_column("Role")
    table.add_column("Type", style="dim")
    table.add_column("Dates")
    table.add_column("Status")
    if verbose:
        table.add_column("Source", style="dim")

    for role in board_roles:
        if isinstance(role, BoardRole):
            status_display = "[green]Current[/green]" if role.is_current else "[dim]Past[/dim]"

            row = [
                role.organization,
                role.role,
                role.type,
                role.format_date_range(),
                status_display,
            ]

            if verbose:
                source_file = getattr(role, "_source_file", None)
                source_display = source_file.name if source_file else "-"
                row.append(source_display)

            table.add_row(*row)

    console.print(table)
    console.print(f"\n[dim]{len(board_roles)} Board Role(s)[/dim]")


def _output_education_json(education: list[Any], verbose: bool = False) -> None:
    """Output education as JSON.

    Args:
        education: List of Education objects.
        verbose: If True, include source file paths (Story 11.2).
    """
    from resume_as_code.models.education import Education

    edu_data = []
    for edu in education:
        if isinstance(edu, Education):
            data: dict[str, Any] = {
                "degree": edu.degree,
                "institution": edu.institution,
                "graduation_year": edu.graduation_year,
                "honors": edu.honors,
                "gpa": edu.gpa,
                "display": edu.display,
            }
            # Add source file in verbose mode (Story 11.2)
            if verbose:
                source_file = getattr(edu, "_source_file", None)
                data["source_file"] = str(source_file) if source_file else None
            edu_data.append(data)

    response = JSONResponse(
        status="success",
        command="list education",
        data={"education": edu_data, "count": len(edu_data)},
    )
    json_output(response.to_json())


def _output_education_table(education: list[Any], verbose: bool = False) -> None:
    """Output education as Rich table.

    Args:
        education: List of Education objects.
        verbose: If True, show source file paths (Story 11.2).
    """
    from resume_as_code.models.education import Education

    table = Table(title="Education")
    table.add_column("Degree", style="cyan", no_wrap=True)
    table.add_column("Institution")
    table.add_column("Year")
    table.add_column("Honors")
    if verbose:
        table.add_column("Source", style="dim")

    for edu in education:
        if isinstance(edu, Education):
            row = [
                edu.degree,
                edu.institution,
                edu.graduation_year or "-",
                edu.honors or "-",
            ]

            if verbose:
                source_file = getattr(edu, "_source_file", None)
                source_display = source_file.name if source_file else "-"
                row.append(source_display)

            table.add_row(*row)

    console.print(table)
    console.print(f"\n[dim]{len(education)} Education Entry(ies)[/dim]")


def _output_certifications_json(certifications: list[Any], verbose: bool = False) -> None:
    """Output certifications as JSON with computed status.

    Args:
        certifications: List of Certification objects.
        verbose: If True, include source file paths (Story 11.2).
    """
    from resume_as_code.models.certification import Certification

    cert_data = []
    for cert in certifications:
        if isinstance(cert, Certification):
            data: dict[str, Any] = {
                "name": cert.name,
                "issuer": cert.issuer,
                "date": cert.date,
                "expires": cert.expires,
                "credential_id": cert.credential_id,
                "url": str(cert.url) if cert.url else None,
                "display": cert.display,
                "status": cert.get_status(),
            }
            # Add source file in verbose mode (Story 11.2)
            if verbose:
                source_file = getattr(cert, "_source_file", None)
                data["source_file"] = str(source_file) if source_file else None
            cert_data.append(data)

    response = JSONResponse(
        status="success",
        command="list certifications",
        data={"certifications": cert_data, "count": len(cert_data)},
    )
    json_output(response.to_json())


def _output_certifications_table(certifications: list[Any], verbose: bool = False) -> None:
    """Output certifications as Rich table with status highlighting.

    Args:
        certifications: List of Certification objects.
        verbose: If True, show source file paths (Story 11.2).
    """
    from resume_as_code.models.certification import Certification

    table = Table(title="Certifications")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Issuer")
    table.add_column("Date")
    table.add_column("Expires")
    table.add_column("Status")
    if verbose:
        table.add_column("Source", style="dim")

    expired_indices: list[int] = []
    for idx, cert in enumerate(certifications):
        if isinstance(cert, Certification):
            status = cert.get_status()

            # Determine status display and style
            if status == "expired":
                expired_indices.append(idx)
                status_display = "[red]Expired[/red]"
            elif status == "expires_soon":
                status_display = "[yellow]Expires Soon[/yellow]"
            else:
                status_display = "[green]Active[/green]"

            row = [
                cert.name,
                cert.issuer or "-",
                cert.date or "-",
                cert.expires or "Never",
                status_display,
            ]

            if verbose:
                source_file = getattr(cert, "_source_file", None)
                source_display = source_file.name if source_file else "-"
                row.append(source_display)

            table.add_row(*row)

    console.print(table)
    console.print(f"\n[dim]{len(certifications)} Certification(s)[/dim]")

    if expired_indices:
        # Show tip with actual index of first expired certification (AC#5)
        console.print(
            f"\n[yellow]Tip: Consider renewing expired certifications or hiding with "
            f"`resume config certifications[{expired_indices[0]}].display false`[/yellow]"
        )


def _output_positions_json(positions: list[Any]) -> None:
    """Output positions as JSON."""
    from resume_as_code.models.position import Position

    pos_data = [
        {
            "id": pos.id,
            "employer": pos.employer,
            "title": pos.title,
            "location": pos.location,
            "dates": pos.format_date_range(),
            "employment_type": pos.employment_type,
            "promoted_from": pos.promoted_from,
            "has_scope": pos.scope is not None,
            "scope": pos.scope.model_dump(exclude_none=True) if pos.scope else None,
        }
        for pos in positions
        if isinstance(pos, Position)
    ]

    response = JSONResponse(
        status="success",
        command="list positions",
        data={"positions": pos_data, "count": len(pos_data)},
    )
    json_output(response.to_json())


def _output_positions_table(positions: list[Any]) -> None:
    """Output positions as Rich table."""
    from resume_as_code.models.position import Position

    table = Table(title="Employment Positions")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Employer", style="green")
    table.add_column("Title")
    table.add_column("Dates")
    table.add_column("Type", style="dim")
    table.add_column("Scope", style="magenta", justify="center")

    for pos in positions:
        if isinstance(pos, Position):
            scope_indicator = "✓" if pos.scope else "-"
            table.add_row(
                pos.id,
                pos.employer,
                pos.title,
                pos.format_date_range(),
                pos.employment_type or "",
                scope_indicator,
            )

    console.print(table)
    console.print(f"\n[dim]{len(positions)} Position(s)[/dim]")


def _load_all_work_units(work_units_dir: Path) -> list[dict[str, Any]]:
    """Load all Work Units from directory.

    Args:
        work_units_dir: Path to work-units directory.

    Returns:
        List of Work Unit dictionaries.
    """
    if not work_units_dir.exists():
        return []

    yaml = YAML()
    yaml.preserve_quotes = True
    work_units: list[dict[str, Any]] = []

    for yaml_file in sorted(work_units_dir.glob("*.yaml")):
        try:
            with yaml_file.open() as f:
                data = yaml.load(f)
                if data and isinstance(data, dict):
                    work_units.append(data)
        except Exception:
            # Skip invalid files (they'll be caught by validate)
            continue

    return work_units


def _apply_filter(work_units: list[dict[str, Any]], filter_str: str) -> list[dict[str, Any]]:
    """Apply filter to Work Units.

    Supports:
      - tag:<value> - Filter by tag
      - confidence:<value> - Filter by confidence
      - <text> - Free text search
    """
    filtered: list[dict[str, Any]] = []

    for wu in work_units:
        # Parse filter
        if filter_str.startswith("tag:"):
            tag_value = filter_str[4:].lower()
            tags = [str(t).lower() for t in wu.get("tags", [])]
            if tag_value in tags:
                filtered.append(wu)

        elif filter_str.startswith("confidence:"):
            conf_value = filter_str[11:].lower()
            wu_conf = wu.get("confidence")
            if wu_conf is not None and str(wu_conf).lower() == conf_value:
                filtered.append(wu)

        elif filter_str.lower().startswith("archetype:"):
            archetype_value = filter_str[10:].strip().lower()
            wu_archetype = wu.get("archetype")
            if wu_archetype is not None and str(wu_archetype).lower() == archetype_value:
                filtered.append(wu)

        else:
            # Free text search
            search_text = filter_str.lower()
            searchable = " ".join(
                [
                    str(wu.get("id", "")),
                    str(wu.get("title", "")),
                    str(wu.get("time_started", "")),
                    str(wu.get("time_ended", "")),
                ]
            ).lower()

            if search_text in searchable:
                filtered.append(wu)

    return filtered


def _get_sort_key_date(wu: dict[str, Any]) -> str:
    """Get date sort key from Work Unit."""
    # Prefer time_started
    if wu.get("time_started"):
        return str(wu["time_started"])[:10]
    # Fall back to ID
    wu_id = str(wu.get("id", ""))
    if wu_id.startswith("wu-") and len(wu_id) > 13:
        return wu_id[3:13]  # YYYY-MM-DD
    return ""


def _get_sort_key_title(wu: dict[str, Any]) -> str:
    """Get title sort key from Work Unit."""
    return str(wu.get("title", "")).lower()


def _get_sort_key_confidence(wu: dict[str, Any]) -> str:
    """Get confidence sort key from Work Unit."""
    # Order: high > medium > low (a < b < c alphabetically)
    conf_order = {"high": "a", "medium": "b", "low": "c"}
    return conf_order.get(str(wu.get("confidence", "")).lower(), "d")


def _get_sort_key_id(wu: dict[str, Any]) -> str:
    """Get ID sort key from Work Unit."""
    return str(wu.get("id", ""))


def _apply_sort(
    work_units: list[dict[str, Any]],
    sort_field: SortField,
    reverse: bool,
) -> list[dict[str, Any]]:
    """Sort Work Units by field."""
    if sort_field == "date":
        key_func = _get_sort_key_date
        # Default: newest first (descending = reverse=True in sorted)
        # If user passes --reverse, they want oldest first
        actual_reverse = not reverse

    elif sort_field == "title":
        key_func = _get_sort_key_title
        actual_reverse = reverse

    elif sort_field == "confidence":
        key_func = _get_sort_key_confidence
        actual_reverse = reverse

    else:
        # Fallback - shouldn't happen due to Click choices
        key_func = _get_sort_key_id
        actual_reverse = reverse

    return sorted(work_units, key=key_func, reverse=actual_reverse)


def _output_json(work_units: list[dict[str, Any]], show_stats: bool = False) -> None:
    """Output Work Units as JSON."""
    from collections import Counter

    summaries = [
        {
            "id": wu.get("id"),
            "title": wu.get("title"),
            "date": _extract_date(wu),
            "archetype": wu.get("archetype"),
            "confidence": wu.get("confidence"),
            "tags": wu.get("tags", []),
        }
        for wu in work_units
    ]

    data: dict[str, Any] = {"work_units": summaries, "count": len(summaries)}

    # Add archetype stats if requested
    if show_stats:
        archetype_counts = Counter(wu.get("archetype") or "unknown" for wu in work_units)
        data["archetype_stats"] = dict(sorted(archetype_counts.items(), key=lambda x: -x[1]))

    response = JSONResponse(
        status="success",
        command="list",
        data=data,
    )
    json_output(response.to_json())


def _output_table(work_units: list[dict[str, Any]]) -> None:
    """Output Work Units as Rich table."""
    table = Table(title="Work Units", show_lines=False)

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Date", style="green")
    table.add_column("Archetype", style="magenta")
    table.add_column("Confidence", style="yellow")
    table.add_column("Tags", style="blue")

    for wu in work_units:
        table.add_row(
            _truncate(str(wu.get("id", "")), 30),
            _truncate(str(wu.get("title", "")), 40),
            _extract_date(wu),
            str(wu.get("archetype") or "-"),
            str(wu.get("confidence") or "-"),
            _format_tags(wu.get("tags", [])),
        )

    console.print(table)
    console.print(f"\n[dim]{len(work_units)} Work Unit(s)[/dim]")


def _output_archetype_stats(work_units: list[dict[str, Any]]) -> None:
    """Display archetype distribution statistics."""
    from collections import Counter

    archetype_counts = Counter(wu.get("archetype") or "unknown" for wu in work_units)

    console.print("\n[bold]Archetype Distribution[/bold]\n")

    # Sort by count descending
    for archetype, count in sorted(archetype_counts.items(), key=lambda x: -x[1]):
        pct = count / len(work_units) * 100 if work_units else 0
        bar = "█" * int(pct / 5)  # 20 chars max for 100%
        console.print(f"  {archetype:<14} {count:>3} ({pct:5.1f}%) {bar}")

    console.print(f"\n[dim]Total: {len(work_units)} work units[/dim]")


def _truncate(text: str, max_len: int) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _extract_date(wu: dict[str, Any]) -> str:
    """Extract date from Work Unit ID or time_started."""
    # Try time_started first
    if wu.get("time_started"):
        return str(wu["time_started"])[:10]

    # Fall back to ID
    wu_id = str(wu.get("id", ""))
    if wu_id.startswith("wu-") and len(wu_id) > 13:
        return wu_id[3:13]  # YYYY-MM-DD

    return "-"


def _format_tags(tags: list[Any]) -> str:
    """Format tags for display (truncate if too many)."""
    if not tags:
        return "-"
    str_tags = [str(t) for t in tags]
    if len(str_tags) <= 3:
        return ", ".join(str_tags)
    return ", ".join(str_tags[:3]) + f" +{len(str_tags) - 3}"


@list_command.command("publications")
@click.option(
    "--verbose",
    "-v",
    "verbose",
    is_flag=True,
    help="Show source file paths (Story 11.2)",
)
@click.pass_context
@handle_errors
def list_publications(ctx: click.Context, verbose: bool) -> None:
    """List all publications and speaking engagements."""
    service = PublicationService(config_path=ctx.obj.effective_config_path)
    publications = service.load_publications()

    if not publications:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="list publications",
                data={"publications": [], "count": 0},
            )
            click.echo(response.to_json())
        else:
            info("No publications found.")
        return

    if ctx.obj.json_output:
        _output_publications_json(publications, verbose=verbose)
    else:
        _output_publications_table(publications, verbose=verbose)


def _output_publications_json(publications: list[Any], verbose: bool = False) -> None:
    """Output publications as JSON.

    Args:
        publications: List of Publication objects.
        verbose: If True, include source file paths (Story 11.2).
    """
    pub_data = []
    for pub in publications:
        data: dict[str, Any] = {
            "title": pub.title,
            "type": pub.type,
            "venue": pub.venue,
            "date": pub.date,
            "url": str(pub.url) if pub.url else None,
            "display": pub.display,
        }
        # Add source file in verbose mode (Story 11.2)
        if verbose:
            source_file = getattr(pub, "_source_file", None)
            data["source_file"] = str(source_file) if source_file else None
        pub_data.append(data)

    response = JSONResponse(
        status="success",
        command="list publications",
        data={"publications": pub_data, "count": len(pub_data)},
    )
    click.echo(response.to_json())


def _output_publications_table(publications: list[Any], verbose: bool = False) -> None:
    """Output publications as Rich table.

    Args:
        publications: List of Publication objects.
        verbose: If True, show source file paths (Story 11.2).
    """
    table = Table(
        title="Publications & Speaking",
        show_header=True,
        header_style="bold",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="cyan", no_wrap=False, max_width=40)
    table.add_column("Type", style="magenta")
    table.add_column("Venue", style="white")
    table.add_column("Date", style="dim")
    if verbose:
        table.add_column("Source", style="dim")

    # Sort by date descending
    sorted_pubs = sorted(publications, key=lambda p: p.date, reverse=True)

    for idx, pub in enumerate(sorted_pubs):
        # Dim if display is False
        style = "dim" if not pub.display else None
        title = pub.title
        if not pub.display:
            title = f"[dim]{pub.title}[/dim]"

        row = [
            str(idx + 1),
            title,
            pub.type,
            pub.venue,
            pub.date,
        ]

        if verbose:
            source_file = getattr(pub, "_source_file", None)
            source_display = source_file.name if source_file else "-"
            row.append(source_display)

        table.add_row(*row, style=style)

    console.print(table)
    console.print(f"\n[dim]{len(publications)} Publication(s)[/dim]")
