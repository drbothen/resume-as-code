"""Migrate command for schema evolution.

Story 9.1: Schema Evolution & Migration System

Provides the `resume migrate` command for detecting and applying
schema migrations to update project files to the latest version.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import click
from rich.prompt import Confirm
from rich.table import Table

from resume_as_code.context import Context, pass_context
from resume_as_code.migrations import CURRENT_SCHEMA_VERSION
from resume_as_code.migrations.backup import create_backup, restore_from_backup
from resume_as_code.migrations.base import MigrationContext
from resume_as_code.migrations.registry import (
    detect_schema_version,
    get_migration_path,
)
from resume_as_code.models.output import JSONResponse
from resume_as_code.utils.console import console, err_console, info, success, warning
from resume_as_code.utils.errors import handle_errors

if TYPE_CHECKING:
    from resume_as_code.migrations.base import Migration


SHARD_RESOURCE_TYPES = ["certifications", "publications", "education", "board-roles", "highlights"]


@click.command("migrate")
@click.option("--status", is_flag=True, help="Show migration status only")
@click.option("--dry-run", is_flag=True, help="Preview changes without applying")
@click.option(
    "--rollback",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Restore from backup directory",
)
@click.option(
    "--shard",
    type=click.Choice(SHARD_RESOURCE_TYPES),
    help="Convert single-file storage to directory mode (Story 11.2)",
)
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt")
@pass_context
@handle_errors
def migrate_command(
    ctx: Context,
    status: bool,
    dry_run: bool,
    rollback: Path | None,
    shard: str | None,
    yes: bool,
) -> None:
    """Migrate schema to latest version.

    Detects current schema version and applies necessary migrations.
    Creates automatic backups before modifying files.

    \b
    Example usage:
        resume migrate --status     # Show version info
        resume migrate --dry-run    # Preview changes
        resume migrate              # Apply migrations
        resume migrate --rollback .resume-backup-2026-01-17-123456/
        resume migrate --shard certifications  # Convert to directory mode
    """
    project_path = Path.cwd()

    # Handle sharding (Story 11.2)
    if shard:
        _handle_shard_migration(project_path, shard, ctx, dry_run, yes)
        return

    # Handle rollback
    if rollback:
        _handle_rollback(rollback, project_path, ctx, yes)
        return

    # Detect current version
    current_version = detect_schema_version(project_path)

    # Status only
    if status:
        _show_status(current_version, project_path, ctx)
        return

    # Check if migration needed
    if current_version == CURRENT_SCHEMA_VERSION:
        if ctx.json_output:
            _output_json_success(
                current_version=current_version,
                target_version=CURRENT_SCHEMA_VERSION,
                migrations_applied=0,
                files_modified=[],
                backup_path=None,
                message="Schema is already current",
            )
        elif not ctx.quiet:
            success(f"Schema is current (v{CURRENT_SCHEMA_VERSION})")
        return

    # Get migration path
    try:
        migrations = get_migration_path(current_version, CURRENT_SCHEMA_VERSION)
    except ValueError as e:
        if ctx.json_output:
            _output_json_error(str(e), "NO_MIGRATION_PATH")
        else:
            err_console.print(f"[red]✗[/red] {e}")
        raise SystemExit(1) from e

    # Dry run
    if dry_run:
        _show_dry_run(migrations, project_path, ctx)
        return

    # Confirm before proceeding (skip in quiet mode, JSON mode, or with --yes)
    if (
        not ctx.quiet
        and not ctx.json_output
        and not yes
        and not Confirm.ask(
            f"Apply {len(migrations)} migration(s) from v{current_version} "
            f"to v{CURRENT_SCHEMA_VERSION}?"
        )
    ):
        info("Migration cancelled")
        return

    # Create backup
    backup_path = create_backup(project_path)
    if not ctx.quiet and not ctx.json_output:
        info(f"Created backup at {backup_path}")

    # Apply migrations
    migration_ctx = MigrationContext(
        project_path=project_path,
        backup_path=backup_path,
        dry_run=False,
    )

    all_files_modified: list[str] = []
    for migration_class in migrations:
        migration = migration_class()
        if not ctx.quiet and not ctx.json_output:
            info(f"Applying {migration.from_version} → {migration.to_version}...")

        result = migration.apply(migration_ctx)

        if not result.success:
            if ctx.json_output:
                _output_json_error(
                    f"Migration failed: {result.errors}",
                    "MIGRATION_FAILED",
                    backup_path=str(backup_path),
                )
            else:
                err_console.print(f"[red]✗[/red] Migration failed: {result.errors}")
                warning(f"Backup preserved at {backup_path}")
            raise SystemExit(1)

        for f in result.files_modified:
            all_files_modified.append(str(f))
            if not ctx.quiet and not ctx.json_output:
                console.print(f"  [green]✓[/green] Updated {f}")

    # Post-migration validation: ensure config can be parsed
    validation_error = _validate_migrated_config(project_path)
    if validation_error:
        if ctx.json_output:
            _output_json_error(
                f"Post-migration validation failed: {validation_error}",
                "VALIDATION_FAILED",
                backup_path=str(backup_path),
            )
        else:
            err_console.print(f"[red]✗[/red] Post-migration validation failed: {validation_error}")
            warning(f"Backup preserved at {backup_path} - use --rollback to restore")
        raise SystemExit(1)

    if ctx.json_output:
        _output_json_success(
            current_version=current_version,
            target_version=CURRENT_SCHEMA_VERSION,
            migrations_applied=len(migrations),
            files_modified=all_files_modified,
            backup_path=str(backup_path),
            message="Migration complete",
        )
    elif not ctx.quiet:
        success(f"Migration complete! Schema version: {CURRENT_SCHEMA_VERSION}")
        console.print(f"  [dim]Backup preserved at {backup_path}[/dim]")


def _show_status(
    current_version: str,
    project_path: Path,
    ctx: Context,
) -> None:
    """Display migration status."""
    migrations_available = 0
    status_text = "up_to_date"

    if current_version == CURRENT_SCHEMA_VERSION:
        status_text = "up_to_date"
    else:
        try:
            migrations = get_migration_path(current_version, CURRENT_SCHEMA_VERSION)
            migrations_available = len(migrations)
            status_text = "migrations_available"
        except ValueError:
            status_text = "no_migration_path"

    if ctx.json_output:
        response = JSONResponse(
            status="success",
            command="migrate",
            data={
                "current_version": current_version,
                "latest_version": CURRENT_SCHEMA_VERSION,
                "status": status_text,
                "migrations_available": migrations_available,
            },
        )
        console.print(response.model_dump_json(indent=2))
        return

    table = Table(title="Schema Migration Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("Current Version", current_version)
    table.add_row("Latest Version", CURRENT_SCHEMA_VERSION)

    if status_text == "up_to_date":
        table.add_row("Status", "[green]Up to date[/green]")
    elif status_text == "migrations_available":
        table.add_row("Status", f"[yellow]{migrations_available} migration(s) available[/yellow]")
    else:
        table.add_row("Status", "[red]No migration path available[/red]")

    console.print(table)


def _show_dry_run(
    migrations: list[type[Migration]],
    project_path: Path,
    ctx: Context,
) -> None:
    """Display dry-run preview."""
    migration_ctx = MigrationContext(
        project_path=project_path,
        dry_run=True,
    )

    # Build migration info for both JSON and Rich output
    migration_info: list[dict[str, Any]] = []
    for migration_class in migrations:
        migration = migration_class()
        changes = migration.preview(migration_ctx)
        migration_info.append(
            {
                "from_version": migration.from_version,
                "to_version": migration.to_version,
                "description": migration.description,
                "changes": changes,
            }
        )

    if ctx.json_output:
        response = JSONResponse(
            status="success",
            command="migrate",
            data={
                "dry_run": True,
                "migrations_count": len(migrations),
                "migrations": migration_info,
            },
        )
        console.print(response.model_dump_json(indent=2))
        return

    console.print(f"\n[bold]Would apply {len(migrations)} migration(s):[/bold]\n")

    for i, mig_info in enumerate(migration_info, 1):
        console.print(
            f"[bold cyan]Migration {i}:[/bold cyan] "
            f"{mig_info['from_version']} → {mig_info['to_version']}"
        )
        console.print(f"  [dim]{mig_info['description']}[/dim]")

        for change in mig_info["changes"]:
            console.print(f"  • {change}")
        console.print()

    console.print("[dim]Run without --dry-run to apply changes.[/dim]")


def _handle_rollback(
    backup_path: Path,
    project_path: Path,
    ctx: Context,
    yes: bool = False,
) -> None:
    """Handle rollback from backup."""
    # Skip confirmation in quiet mode, JSON mode, or with --yes
    if (
        not ctx.quiet
        and not ctx.json_output
        and not yes
        and not Confirm.ask(f"Restore from {backup_path}?")
    ):
        info("Rollback cancelled")
        return

    restored = restore_from_backup(backup_path, project_path)

    if ctx.json_output:
        response = JSONResponse(
            status="success",
            command="migrate",
            data={
                "rollback": True,
                "backup_path": str(backup_path),
                "files_restored": [str(f) for f in restored],
            },
        )
        console.print(response.model_dump_json(indent=2))
    elif not ctx.quiet:
        success("Rollback complete!")
        for f in restored:
            console.print(f"  [green]✓[/green] Restored {f}")


def _output_json_success(
    current_version: str,
    target_version: str,
    migrations_applied: int,
    files_modified: list[str],
    backup_path: str | None,
    message: str,
) -> None:
    """Output JSON success response for migration."""
    data: dict[str, object] = {
        "current_version": current_version,
        "target_version": target_version,
        "migrations_applied": migrations_applied,
        "files_modified": files_modified,
        "message": message,
    }
    if backup_path:
        data["backup_path"] = backup_path

    response = JSONResponse(
        status="success",
        command="migrate",
        data=data,
    )
    console.print(response.model_dump_json(indent=2))


def _output_json_error(
    message: str,
    code: str,
    backup_path: str | None = None,
) -> None:
    """Output JSON error response for migration."""
    error_data: dict[str, object] = {
        "code": code,
        "message": message,
        "recoverable": True,
    }
    if backup_path:
        error_data["backup_path"] = backup_path

    response = JSONResponse(
        status="error",
        command="migrate",
        errors=[error_data],
    )
    err_console.print(response.model_dump_json(indent=2))


def _validate_migrated_config(project_path: Path) -> str | None:
    """Validate the migrated config can be parsed.

    Returns:
        None if valid, error message string if invalid.
    """
    from pydantic import ValidationError

    from resume_as_code.models.config import ResumeConfig

    config_path = project_path / ".resume.yaml"
    if not config_path.exists():
        return None  # No config to validate

    try:
        import yaml

        with config_path.open() as f:
            data = yaml.safe_load(f) or {}
        ResumeConfig(**data)
        return None
    except ValidationError as e:
        return f"Config validation error: {e.error_count()} error(s)"
    except yaml.YAMLError as e:
        return f"YAML syntax error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


# Resource type configuration for sharding (Story 11.2)
_SHARD_CONFIG: dict[str, dict[str, str]] = {
    "certifications": {
        "filename": "certifications.yaml",
        "dirname": "certifications",
        "dir_key": "certifications_dir",
        "model": "Certification",
    },
    "publications": {
        "filename": "publications.yaml",
        "dirname": "publications",
        "dir_key": "publications_dir",
        "model": "Publication",
    },
    "education": {
        "filename": "education.yaml",
        "dirname": "education",
        "dir_key": "education_dir",
        "model": "Education",
    },
    "board-roles": {
        "filename": "board-roles.yaml",
        "dirname": "board-roles",
        "dir_key": "board_roles_dir",
        "model": "BoardRole",
    },
    "highlights": {
        "filename": "highlights.yaml",
        "dirname": "highlights",
        "dir_key": "highlights_dir",
        "model": "str",  # Highlights are strings, not models
    },
}


def _handle_shard_migration(
    project_path: Path,
    resource_type: str,
    ctx: Context,
    dry_run: bool,
    yes: bool,
) -> None:
    """Handle migration from single-file to directory mode (Story 11.2).

    Args:
        project_path: Project root directory.
        resource_type: Type of resource to shard.
        ctx: CLI context.
        dry_run: If True, preview changes without applying.
        yes: Skip confirmation prompt.
    """
    import shutil

    import yaml
    from ruamel.yaml import YAML

    config = _SHARD_CONFIG.get(resource_type)
    if not config:
        if ctx.json_output:
            _output_json_error(f"Unknown resource type: {resource_type}", "INVALID_RESOURCE")
        else:
            err_console.print(f"[red]✗[/red] Unknown resource type: {resource_type}")
        raise SystemExit(1)

    source_file = project_path / config["filename"]
    target_dir = project_path / config["dirname"]
    dir_key = config["dir_key"]

    # Check if already in directory mode
    if target_dir.exists() and target_dir.is_dir():
        if ctx.json_output:
            _output_json_error(
                f"Directory {config['dirname']}/ already exists. "
                "Already using directory mode or remove directory first.",
                "ALREADY_DIRECTORY_MODE",
            )
        else:
            warning(f"Directory {config['dirname']}/ already exists.")
            info("If you want to migrate, remove the directory first.")
        raise SystemExit(1)

    # Check if source file exists
    if not source_file.exists():
        if ctx.json_output:
            _output_json_error(
                f"Source file {config['filename']} not found. Nothing to migrate.",
                "NO_SOURCE_FILE",
            )
        else:
            warning(f"Source file {config['filename']} not found.")
        raise SystemExit(1)

    # Load items from source file
    with source_file.open() as f:
        items = yaml.safe_load(f) or []

    if not items:
        if ctx.json_output:
            _output_json_error(
                f"No items found in {config['filename']}. Nothing to migrate.",
                "NO_ITEMS",
            )
        else:
            warning(f"No items found in {config['filename']}.")
        raise SystemExit(1)

    # Import the appropriate loader/model based on resource type
    if resource_type == "highlights":
        # Highlights are strings, handle specially
        files_to_create = _prepare_highlight_shards(items, target_dir)
    else:
        files_to_create = _prepare_model_shards(items, resource_type, target_dir)

    # Dry run: just show what would happen
    if dry_run:
        _show_shard_dry_run(ctx, resource_type, source_file, target_dir, files_to_create, dir_key)
        return

    # Confirm before proceeding
    if (
        not ctx.quiet
        and not ctx.json_output
        and not yes
        and not Confirm.ask(
            f"Migrate {len(items)} {resource_type} from {config['filename']} "
            f"to {config['dirname']}/ directory?"
        )
    ):
        info("Sharding cancelled")
        return

    # Create backup of source file
    backup_file = source_file.with_suffix(".yaml.bak")
    shutil.copy2(source_file, backup_file)
    if not ctx.quiet and not ctx.json_output:
        info(f"Created backup at {backup_file}")

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Write individual files
    ruamel_yaml = YAML()
    ruamel_yaml.default_flow_style = False

    for file_path, data in files_to_create:
        with file_path.open("w") as f:
            ruamel_yaml.dump(data, f)
        if not ctx.quiet and not ctx.json_output:
            console.print(f"  [green]✓[/green] Created {file_path.name}")

    # Update .resume.yaml to use directory mode
    config_path = project_path / ".resume.yaml"
    if config_path.exists():
        with config_path.open() as f:
            resume_config = yaml.safe_load(f) or {}
    else:
        resume_config = {}

    if "data_paths" not in resume_config:
        resume_config["data_paths"] = {}

    resume_config["data_paths"][dir_key] = f"./{config['dirname']}/"

    with config_path.open("w") as f:
        ruamel_yaml = YAML()
        ruamel_yaml.default_flow_style = False
        ruamel_yaml.dump(resume_config, f)

    # Remove original file
    source_file.unlink()

    if ctx.json_output:
        response = JSONResponse(
            status="success",
            command="migrate",
            data={
                "shard": True,
                "resource_type": resource_type,
                "items_migrated": len(items),
                "files_created": [str(fp) for fp, _ in files_to_create],
                "directory": str(target_dir),
                "backup_file": str(backup_file),
            },
        )
        console.print(response.model_dump_json(indent=2))
    elif not ctx.quiet:
        success(f"Sharding complete! Migrated {len(items)} {resource_type}")
        console.print(f"  [dim]Source file backed up to {backup_file}[/dim]")
        console.print(f"  [dim]Now using directory mode: {config['dirname']}/[/dim]")


def _prepare_highlight_shards(
    items: list[Any], target_dir: Path
) -> list[tuple[Path, dict[str, Any]]]:
    """Prepare highlight shards for directory mode.

    Highlights are strings, so we wrap each in a dict with 'text' field.

    Args:
        items: List of highlight strings.
        target_dir: Target directory for shards.

    Returns:
        List of (file_path, data) tuples.
    """
    import re

    files_to_create: list[tuple[Path, dict[str, Any]]] = []

    for idx, highlight in enumerate(items, 1):
        text = str(highlight)
        # Slugify
        slug = text.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")[:40]

        item_id = f"hl-{idx:03d}-{slug}"
        file_path = target_dir / f"{item_id}.yaml"
        files_to_create.append((file_path, {"text": text}))

    return files_to_create


def _prepare_model_shards(
    items: list[Any], resource_type: str, target_dir: Path
) -> list[tuple[Path, dict[str, Any]]]:
    """Prepare model shards for directory mode.

    Args:
        items: List of item dictionaries.
        resource_type: Type of resource.
        target_dir: Target directory for shards.

    Returns:
        List of (file_path, data) tuples.
    """
    from pydantic import BaseModel

    from resume_as_code.models.board_role import BoardRole
    from resume_as_code.models.certification import Certification
    from resume_as_code.models.education import Education
    from resume_as_code.models.publication import Publication

    model_map: dict[str, type[BaseModel]] = {
        "certifications": Certification,
        "publications": Publication,
        "education": Education,
        "board-roles": BoardRole,
    }

    model_class = model_map.get(resource_type)
    if not model_class:
        raise ValueError(f"Unknown resource type: {resource_type}")

    files_to_create: list[tuple[Path, dict[str, Any]]] = []

    for item_data in items:
        # Validate through model
        model: BaseModel | None
        try:
            model = model_class.model_validate(item_data)
        except Exception:
            # If validation fails, just use raw data
            model = None

        # Generate ID based on resource type
        if resource_type == "certifications":
            name = item_data.get("name", "unnamed")
            date = item_data.get("date", "")
            slug = _slugify(name)
            item_id = f"cert-{date}-{slug}" if date else f"cert-{slug}"

        elif resource_type == "publications":
            title = item_data.get("title", "unnamed")
            date = item_data.get("date", "")
            slug = _slugify(title)
            item_id = f"pub-{date}-{slug}" if date else f"pub-{slug}"

        elif resource_type == "education":
            institution = item_data.get("institution", "unknown")
            year = item_data.get("graduation_year", "")
            slug = _slugify(institution)
            item_id = f"edu-{year}-{slug}" if year else f"edu-{slug}"

        elif resource_type == "board-roles":
            organization = item_data.get("organization", "unknown")
            start_date = item_data.get("start_date", "")
            slug = _slugify(organization)
            item_id = f"board-{start_date}-{slug}" if start_date else f"board-{slug}"

        else:
            slug = _slugify(str(item_data.get("name", item_data.get("title", "item"))))
            item_id = f"{resource_type[:4]}-{slug}"

        file_path = target_dir / f"{item_id}.yaml"

        # Use model_dump if we have a valid model, otherwise use raw data
        data = model.model_dump(exclude_none=True, mode="json") if model else item_data

        files_to_create.append((file_path, data))

    return files_to_create


def _slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    import re

    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    slug = re.sub(r"-+", "-", slug)
    return slug[:40]


def _show_shard_dry_run(
    ctx: Context,
    resource_type: str,
    source_file: Path,
    target_dir: Path,
    files_to_create: list[tuple[Path, dict[str, Any]]],
    dir_key: str,
) -> None:
    """Show dry-run preview for sharding migration."""
    if ctx.json_output:
        response = JSONResponse(
            status="success",
            command="migrate",
            data={
                "dry_run": True,
                "shard": True,
                "resource_type": resource_type,
                "source_file": str(source_file),
                "target_directory": str(target_dir),
                "files_to_create": [str(fp) for fp, _ in files_to_create],
                "config_update": {dir_key: f"./{target_dir.name}/"},
            },
        )
        console.print(response.model_dump_json(indent=2))
        return

    console.print(f"\n[bold]Would migrate {resource_type} to directory mode:[/bold]\n")
    console.print(f"  Source: [cyan]{source_file}[/cyan]")
    console.print(f"  Target: [cyan]{target_dir}/[/cyan]")
    console.print(f"\n  Files to create ({len(files_to_create)}):")

    for fp, _ in files_to_create[:5]:  # Show first 5
        console.print(f"    • {fp.name}")
    if len(files_to_create) > 5:
        console.print(f"    [dim]... and {len(files_to_create) - 5} more[/dim]")

    console.print("\n  Config update:")
    console.print(f"    data_paths.{dir_key}: ./{target_dir.name}/")
    console.print(f"\n  Backup: {source_file}.bak")

    console.print("\n[dim]Run without --dry-run to apply changes.[/dim]")
