#!/usr/bin/env python3
"""Generate JSON schemas from Pydantic models.

This script auto-generates JSON Schema 2020-12 compliant schemas from
Pydantic model definitions, ensuring schemas never drift from implementation.

Usage:
    uv run python scripts/generate_schemas.py           # Generate/update schemas
    uv run python scripts/generate_schemas.py --check   # CI mode: fail if changes needed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import TypeAdapter
from pydantic.json_schema import GenerateJsonSchema
from rich.console import Console

# Import models - these are the authoritative source for schemas
# Import directly from modules to avoid relying on __init__.py exports
from resume_as_code.models.board_role import BoardRole
from resume_as_code.models.certification import Certification
from resume_as_code.models.config import ResumeConfig
from resume_as_code.models.education import Education
from resume_as_code.models.position import Position
from resume_as_code.models.publication import Publication
from resume_as_code.models.work_unit import WorkUnit

console = Console()

# Default schema directory (inside package for proper bundling)
DEFAULT_SCHEMA_DIR = Path(__file__).parent.parent / "src" / "resume_as_code" / "schemas"

# Base URL for schema $id fields
BASE_URL = "https://resume-as-code.dev/schemas"

# Map of schema filename (without .json) to Pydantic model class
MODELS: dict[str, type[Any]] = {
    "work-unit": WorkUnit,
    "positions": Position,
    "config": ResumeConfig,
    "certifications": Certification,
    "education": Education,
    "board-roles": BoardRole,
    "publications": Publication,
}


class ResumeSchemaGenerator(GenerateJsonSchema):
    """Custom JSON Schema generator that adds $schema field.

    Pydantic's default generator doesn't include the $schema field,
    which is required for proper JSON Schema validation tooling.
    """

    def generate(
        self, schema: Any, mode: Literal["validation", "serialization"] = "validation"
    ) -> dict[str, Any]:
        """Generate JSON schema with $schema field.

        Args:
            schema: The Pydantic core schema to convert.
            mode: Generation mode ('validation' or 'serialization').

        Returns:
            JSON Schema dictionary with $schema field added.
        """
        json_schema = super().generate(schema, mode=mode)
        # self.schema_dialect is 'https://json-schema.org/draft/2020-12/schema'
        json_schema["$schema"] = self.schema_dialect
        return json_schema


def generate_schema(name: str, model: type[Any]) -> dict[str, Any]:
    """Generate JSON schema from a Pydantic model.

    Uses serialization mode because our YAML files store serialized output,
    not validation input. This ensures type mappings match storage format
    (e.g., dates serialize as strings, not datetime objects).

    Args:
        name: Schema name (used for $id URL).
        model: Pydantic model class to generate schema from.

    Returns:
        Complete JSON Schema dictionary with $schema and $id fields.
    """
    adapter = TypeAdapter(model)
    schema = adapter.json_schema(
        mode="serialization",  # CRITICAL: Match YAML storage format
        schema_generator=ResumeSchemaGenerator,
    )
    # Add $id URL for schema identification
    schema["$id"] = f"{BASE_URL}/{name}.schema.json"
    return schema


def main(check: bool = False, schema_dir: Path | None = None) -> int:
    """Generate all schemas or check for drift.

    Args:
        check: If True, exit with code 1 if any schema needs updating.
        schema_dir: Directory to write schemas to (defaults to schemas/).

    Returns:
        Exit code: 0 on success, 1 if changes detected in check mode.
    """
    if schema_dir is None:
        schema_dir = DEFAULT_SCHEMA_DIR

    # Ensure output directory exists
    schema_dir.mkdir(parents=True, exist_ok=True)

    changes_detected = False
    updated_schemas: list[str] = []
    created_schemas: list[str] = []

    for name, model in MODELS.items():
        schema_file = schema_dir / f"{name}.schema.json"
        new_schema = generate_schema(name, model)
        new_content = json.dumps(new_schema, indent=2) + "\n"

        # Check if file exists and compare content
        if schema_file.exists():
            existing_content = schema_file.read_text()
            if existing_content != new_content:
                changes_detected = True
                if check:
                    console.print(f"[yellow]⚠[/yellow] Schema drift: {schema_file.name}")
                else:
                    schema_file.write_text(new_content)
                    updated_schemas.append(name)
                    console.print(f"[green]✓[/green] Updated: {schema_file.name}")
            else:
                if not check:
                    console.print(f"[dim]  Unchanged: {schema_file.name}[/dim]")
        else:
            changes_detected = True
            if check:
                console.print(f"[yellow]⚠[/yellow] Missing schema: {schema_file.name}")
            else:
                schema_file.write_text(new_content)
                created_schemas.append(name)
                console.print(f"[green]✓[/green] Created: {schema_file.name}")

    # Summary
    if check:
        if changes_detected:
            console.print(
                "\n[red]✗[/red] Schema drift detected. "
                "Run 'uv run python scripts/generate_schemas.py' to update."
            )
            return 1
        console.print("\n[green]✓[/green] All schemas up to date.")
        return 0

    total_changes = len(updated_schemas) + len(created_schemas)
    if total_changes > 0:
        console.print(f"\n[green]✓[/green] {total_changes} schema(s) updated.")
    else:
        console.print("\n[dim]All schemas already up to date.[/dim]")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate JSON schemas from Pydantic models")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check for schema drift without updating (for CI)",
    )
    args = parser.parse_args()

    sys.exit(main(check=args.check))
