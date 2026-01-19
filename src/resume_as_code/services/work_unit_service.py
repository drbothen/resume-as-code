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
    """Get the work units directory, creating if needed.

    Handles symlinks by resolving to the target and creating that directory.
    """
    if base_dir is None:
        base_dir = Path.cwd() / "work-units"

    # Handle symlinks - resolve to actual target path
    if base_dir.is_symlink():
        # Get the symlink target (may be relative)
        target = base_dir.resolve()
        if not target.exists():
            target.mkdir(parents=True)
    elif not base_dir.exists():
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
    position_id: str | None = None,
) -> Path:
    """Create a new Work Unit file from archetype.

    Args:
        archetype: Name of archetype template to use.
        work_unit_id: Generated work unit ID.
        title: Work unit title.
        work_units_dir: Directory to create file in.
        position_id: Optional position ID to link to.

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

    # Add position_id after title if provided
    if position_id:
        content = re.sub(
            r'(title:\s*"[^"]*")',
            lambda m: f'{m.group(1)}\nposition_id: "{position_id}"',
            content,
            count=1,
        )

    # Ensure archetype field matches the requested archetype
    # Handle both quoted and unquoted values in templates
    if re.search(r"archetype:\s*\S+", content):
        content = re.sub(
            r"archetype:\s*[\"']?\S+[\"']?",
            f"archetype: {archetype}",
            content,
            count=1,
        )
    else:
        # Defensive: add archetype if template lacks it (should not happen)
        content = re.sub(
            r"(schema_version:\s*[\"']?\S+[\"']?)",
            rf"\1\narchetype: {archetype}",
            content,
            count=1,
        )

    # Write file
    file_path = work_units_dir / f"{work_unit_id}.yaml"
    file_path.write_text(content)

    return file_path


def create_work_unit_from_data(
    work_unit_id: str,
    title: str,
    problem_statement: str,
    actions: list[str],
    result: str,
    work_units_dir: Path,
    archetype: str,
    position_id: str | None = None,
    quantified_impact: str | None = None,
    skills: list[str] | None = None,
    tags: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Path:
    """Create a Work Unit file from provided data (inline creation).

    Args:
        work_unit_id: Generated work unit ID.
        title: Work unit title.
        problem_statement: The problem being solved.
        actions: List of actions taken.
        result: The outcome result.
        work_units_dir: Directory to create file in.
        archetype: Work unit archetype (e.g., 'minimal', 'greenfield').
        position_id: Optional position ID to link to.
        quantified_impact: Optional quantified impact string.
        skills: Optional list of skill names.
        tags: Optional list of tags.
        start_date: Optional start date (YYYY-MM-DD or YYYY-MM).
        end_date: Optional end date (YYYY-MM-DD or YYYY-MM).

    Returns:
        Path to the created file.
    """
    # Ensure directory exists
    work_units_dir = get_work_units_dir(work_units_dir)

    yaml = YAML()
    yaml.default_flow_style = False

    # Build the work unit data structure
    data: dict[str, Any] = {
        "id": work_unit_id,
        "title": title,
        "schema_version": "4.0.0",
        "archetype": archetype,
    }

    # Add position_id if provided
    if position_id:
        data["position_id"] = position_id

    # Add time fields if provided
    if start_date:
        data["time_started"] = start_date
    if end_date:
        data["time_ended"] = end_date

    # Add problem
    data["problem"] = {"statement": problem_statement}

    # Add actions
    data["actions"] = actions

    # Add outcome
    outcome: dict[str, str] = {"result": result}
    if quantified_impact:
        outcome["quantified_impact"] = quantified_impact
    data["outcome"] = outcome

    # Add skills if provided
    if skills:
        data["skills_demonstrated"] = [{"name": skill} for skill in skills]

    # Add tags if provided
    if tags:
        data["tags"] = tags

    # Write file
    file_path = work_units_dir / f"{work_unit_id}.yaml"
    with open(file_path, "w") as f:
        yaml.dump(data, f)

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
