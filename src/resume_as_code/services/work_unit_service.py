"""Work Unit service for file operations."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from resume_as_code.services.archetype_service import load_archetype


def generate_slug(title: str) -> str:
    """Generate URL-safe slug from title.

    Examples:
        "Resolved P1 Database Outage" -> "resolved-p1-database-outage"
        "Built ML Pipeline (v2)" -> "built-ml-pipeline-v2"
    """
    if not title:
        return ""

    # Lowercase
    slug = title.lower()

    # Replace special chars with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)

    # Truncate to reasonable length
    if len(slug) > 50:
        slug = slug[:50].rsplit("-", 1)[0]

    return slug


def generate_id(title: str, today: date) -> str:
    """Generate Work Unit ID from title and date.

    Format: wu-YYYY-MM-DD-slug

    Examples:
        generate_id("Database Migration", date(2024, 3, 15))
        -> "wu-2024-03-15-database-migration"
    """
    slug = generate_slug(title)
    date_str = today.strftime("%Y-%m-%d")
    return f"wu-{date_str}-{slug}"


def get_work_units_dir(base_dir: Path | None = None) -> Path:
    """Get the work units directory, creating if needed."""
    if base_dir is None:
        base_dir = Path.cwd() / "work-units"

    if not base_dir.exists():
        base_dir.mkdir(parents=True)

    return base_dir


def _escape_yaml_string(value: str) -> str:
    """Escape a string value for safe YAML double-quoted insertion.

    Escapes backslashes and double quotes to prevent YAML syntax errors.
    """
    # Escape backslashes first, then double quotes
    return value.replace("\\", "\\\\").replace('"', '\\"')


def create_work_unit_file(
    archetype: str,
    work_unit_id: str,
    title: str,
    work_units_dir: Path,
) -> Path:
    """Create a new Work Unit file from archetype.

    Returns:
        Path to the created file.
    """
    # Ensure directory exists
    work_units_dir = get_work_units_dir(work_units_dir)

    # Load archetype content
    content = load_archetype(archetype)

    # Replace ID placeholder
    content = re.sub(
        r'id:\s*"?wu-YYYY-MM-DD-[^"\n]*"?',
        f'id: "{work_unit_id}"',
        content,
        count=1,
    )

    # Replace title placeholder if present
    # Escape special characters to prevent YAML syntax errors
    escaped_title = _escape_yaml_string(title)
    # Use a lambda to prevent re.sub from interpreting backslashes in replacement
    content = re.sub(
        r'title:\s*"[^"]*"',
        lambda _: f'title: "{escaped_title}"',
        content,
        count=1,
    )

    # Write file
    file_path = work_units_dir / f"{work_unit_id}.yaml"
    file_path.write_text(content)

    return file_path


def load_all_work_units(work_units_dir: Path) -> list[dict[str, Any]]:
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
        except (YAMLError, OSError):
            # Skip invalid YAML or unreadable files (caught by validate command)
            continue

    return work_units
