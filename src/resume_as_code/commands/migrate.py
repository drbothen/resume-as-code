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


@click.command("migrate")
@click.option("--status", is_flag=True, help="Show migration status only")
@click.option("--dry-run", is_flag=True, help="Preview changes without applying")
@click.option(
    "--rollback",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Restore from backup directory",
)
@pass_context
@handle_errors
def migrate_command(
    ctx: Context,
    status: bool,
    dry_run: bool,
    rollback: Path | None,
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
    """
    project_path = Path.cwd()

    # Handle rollback
    if rollback:
        _handle_rollback(rollback, project_path, ctx)
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

    # Confirm before proceeding (skip in quiet mode or JSON mode)
    if (
        not ctx.quiet
        and not ctx.json_output
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
) -> None:
    """Handle rollback from backup."""
    # Skip confirmation in quiet mode or JSON mode
    if not ctx.quiet and not ctx.json_output and not Confirm.ask(f"Restore from {backup_path}?"):
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
