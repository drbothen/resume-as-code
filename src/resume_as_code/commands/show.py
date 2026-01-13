"""Show command for displaying detailed resource information."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click

from resume_as_code.config import get_config
from resume_as_code.models.errors import NotFoundError
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.position_service import PositionService
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
    related_work_units = _find_work_units_for_position(
        position_id, config.work_units_dir
    )

    # Get promotion chain
    chain = service.get_promotion_chain(position_id)

    if ctx.obj.json_output:
        _output_position_json(position, related_work_units, chain)
    else:
        _output_position_rich(position, related_work_units, chain)


def _find_work_units_for_position(
    position_id: str, work_units_dir: Path
) -> list[dict[str, Any]]:
    """Find work units that reference a position."""
    from ruamel.yaml import YAML

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
    # Position header
    console.print(f"\n[bold cyan]{position.title}[/bold cyan]")
    console.print(f"[green]{position.employer}[/green]")

    if position.location:
        console.print(f"[dim]{position.location}[/dim]")

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
