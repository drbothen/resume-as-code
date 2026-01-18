"""Migrate command for schema evolution.

Story 9.1: Schema Evolution & Migration System

Provides the `resume migrate` command for detecting and applying
schema migrations to update project files to the latest version.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

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
        if not ctx.quiet:
            success(f"Schema is current (v{CURRENT_SCHEMA_VERSION})")
        return

    # Get migration path
    try:
        migrations = get_migration_path(current_version, CURRENT_SCHEMA_VERSION)
    except ValueError as e:
        err_console.print(f"[red]✗[/red] {e}")
        raise SystemExit(1) from e

    # Dry run
    if dry_run:
        _show_dry_run(migrations, project_path)
        return

    # Confirm before proceeding
    if not ctx.quiet and not Confirm.ask(
        f"Apply {len(migrations)} migration(s) from v{current_version} "
        f"to v{CURRENT_SCHEMA_VERSION}?"
    ):
        info("Migration cancelled")
        return

    # Create backup
    backup_path = create_backup(project_path)
    if not ctx.quiet:
        info(f"Created backup at {backup_path}")

    # Apply migrations
    migration_ctx = MigrationContext(
        project_path=project_path,
        backup_path=backup_path,
        dry_run=False,
    )

    for migration_class in migrations:
        migration = migration_class()
        if not ctx.quiet:
            info(f"Applying {migration.from_version} → {migration.to_version}...")

        result = migration.apply(migration_ctx)

        if not result.success:
            err_console.print(f"[red]✗[/red] Migration failed: {result.errors}")
            warning(f"Backup preserved at {backup_path}")
            raise SystemExit(1)

        for f in result.files_modified:
            if not ctx.quiet:
                console.print(f"  [green]✓[/green] Updated {f}")

    if not ctx.quiet:
        success(f"Migration complete! Schema version: {CURRENT_SCHEMA_VERSION}")
        console.print(f"  [dim]Backup preserved at {backup_path}[/dim]")


def _show_status(
    current_version: str,
    project_path: Path,
    ctx: Context,
) -> None:
    """Display migration status."""
    table = Table(title="Schema Migration Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("Current Version", current_version)
    table.add_row("Latest Version", CURRENT_SCHEMA_VERSION)

    if current_version == CURRENT_SCHEMA_VERSION:
        table.add_row("Status", "[green]Up to date[/green]")
    else:
        try:
            migrations = get_migration_path(current_version, CURRENT_SCHEMA_VERSION)
            table.add_row("Status", f"[yellow]{len(migrations)} migration(s) available[/yellow]")
        except ValueError:
            table.add_row("Status", "[red]No migration path available[/red]")

    console.print(table)


def _show_dry_run(
    migrations: list[type[Migration]],
    project_path: Path,
) -> None:
    """Display dry-run preview."""
    console.print(f"\n[bold]Would apply {len(migrations)} migration(s):[/bold]\n")

    migration_ctx = MigrationContext(
        project_path=project_path,
        dry_run=True,
    )

    for i, migration_class in enumerate(migrations, 1):
        migration = migration_class()
        console.print(
            f"[bold cyan]Migration {i}:[/bold cyan] "
            f"{migration.from_version} → {migration.to_version}"
        )
        console.print(f"  [dim]{migration.description}[/dim]")

        changes = migration.preview(migration_ctx)
        for change in changes:
            console.print(f"  • {change}")
        console.print()

    console.print("[dim]Run without --dry-run to apply changes.[/dim]")


def _handle_rollback(
    backup_path: Path,
    project_path: Path,
    ctx: Context,
) -> None:
    """Handle rollback from backup."""
    if not ctx.quiet and not Confirm.ask(f"Restore from {backup_path}?"):
        info("Rollback cancelled")
        return

    restored = restore_from_backup(backup_path, project_path)

    if not ctx.quiet:
        success("Rollback complete!")
        for f in restored:
            console.print(f"  [green]✓[/green] Restored {f}")
