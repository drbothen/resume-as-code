"""List command for browsing Work Units."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import click
from rich.table import Table
from ruamel.yaml import YAML

from resume_as_code.config import get_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.utils.console import console, info, json_output
from resume_as_code.utils.errors import handle_errors

SortField = Literal["date", "title", "confidence"]


@click.command("list")
@click.option(
    "--filter",
    "-f",
    "filter_strs",
    multiple=True,
    help="Filter Work Units (tag:value, confidence:value, or free text). Repeatable.",
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
@click.pass_context
@handle_errors
def list_command(
    ctx: click.Context,
    filter_strs: tuple[str, ...],
    sort: SortField,
    reverse: bool,
) -> None:
    """List all Work Units with optional filtering.

    Filter syntax:
      tag:<value>        - Filter by tag
      confidence:<value> - Filter by confidence level
      <text>             - Free text search in ID, title, date

    Multiple --filter options use AND logic (all must match).
    """
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
        _output_json(work_units)
    else:
        _output_table(work_units)


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


def _output_json(work_units: list[dict[str, Any]]) -> None:
    """Output Work Units as JSON."""
    summaries = [
        {
            "id": wu.get("id"),
            "title": wu.get("title"),
            "date": _extract_date(wu),
            "confidence": wu.get("confidence"),
            "tags": wu.get("tags", []),
        }
        for wu in work_units
    ]

    response = JSONResponse(
        status="success",
        command="list",
        data={"work_units": summaries, "count": len(summaries)},
    )
    json_output(response.to_json())


def _output_table(work_units: list[dict[str, Any]]) -> None:
    """Output Work Units as Rich table."""
    table = Table(title="Work Units", show_lines=False)

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Date", style="green")
    table.add_column("Confidence", style="yellow")
    table.add_column("Tags", style="blue")

    for wu in work_units:
        table.add_row(
            _truncate(str(wu.get("id", "")), 30),
            _truncate(str(wu.get("title", "")), 40),
            _extract_date(wu),
            str(wu.get("confidence") or "-"),
            _format_tags(wu.get("tags", [])),
        )

    console.print(table)
    console.print(f"\n[dim]{len(work_units)} Work Unit(s)[/dim]")


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
