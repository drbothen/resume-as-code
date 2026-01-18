# Story 9.1: Schema Evolution & Migration System

Status: done

## Story

As a **resume-as-code user with existing data**,
I want **automatic detection and migration of outdated schemas**,
So that **I can upgrade to new versions without manually editing YAML files or losing data**.

## Acceptance Criteria

1. **Given** a `.resume.yaml` file without a `schema_version` field **When** running any `resume` command **Then** the system detects this as v1.0.0 (legacy) **And** warns the user about available migrations

2. **Given** a resume project with schema v1.x **When** running `resume migrate --status` **Then** the system shows current version, latest version, and available migrations

3. **Given** a migration in progress **When** running `resume migrate --dry-run` **Then** the system shows what changes would be made **And** no files are actually modified

4. **Given** `resume migrate` command **When** executing migrations **Then** the system asks for confirmation before proceeding **And** creates backups of all files before modifying **And** applies migrations in order

5. **Given** a migration step fails **When** applying migrations **Then** the backup is preserved for manual rollback **And** the user sees a clear error message with rollback instructions **And** the user can restore using `--rollback <backup-dir>`

6. **Given** a work unit or config file with outdated schema **When** running `resume migrate` **Then** the file is updated to the latest schema **And** YAML comments are preserved **And** original formatting is preserved where possible

7. **Given** a successfully migrated project **When** checking the config **Then** `schema_version` reflects the current version **And** all files pass validation

8. **Given** `resume migrate --rollback <backup>` **When** executed **Then** files are restored from the backup directory

## Tasks / Subtasks

- [x] Task 1: Create migration framework infrastructure (AC: #1, #4, #5)
  - [x] 1.1 Create `src/resume_as_code/migrations/__init__.py` with version constants
  - [x] 1.2 Create `MigrationResult` dataclass in `migrations/base.py`
  - [x] 1.3 Create abstract `Migration` base class with `check_applicable()`, `preview()`, `apply()`, `rollback()` methods
  - [x] 1.4 Create `MigrationContext` for passing config and state to migrations

- [x] Task 2: Create migration registry (AC: #2)
  - [x] 2.1 Create `migrations/registry.py` with `@register_migration` decorator
  - [x] 2.2 Implement `get_migration_path(from_version, to_version)` function
  - [x] 2.3 Implement `detect_schema_version(project_path)` function
  - [x] 2.4 Add `CURRENT_SCHEMA_VERSION` constant (start with "2.0.0")

- [x] Task 3: Implement backup system (AC: #4, #5, #8)
  - [x] 3.1 Create `migrations/backup.py` with `create_backup()` function
  - [x] 3.2 Implement backup naming: `.resume-backup-YYYY-MM-DD-HHMMSS/`
  - [x] 3.3 Implement `restore_from_backup()` function
  - [x] 3.4 Preserve directory structure in backups

- [x] Task 4: Implement YAML comment preservation (AC: #6)
  - [x] 4.1 Create `migrations/yaml_handler.py` using ruamel.yaml
  - [x] 4.2 Implement `load_yaml_preserve()` function
  - [x] 4.3 Implement `save_yaml_preserve()` function
  - [x] 4.4 Add unit tests for comment preservation

- [x] Task 5: Create migrate CLI command (AC: #2, #3, #4, #8)
  - [x] 5.1 Create `commands/migrate.py` with `resume migrate` command
  - [x] 5.2 Implement `--status` flag showing version info
  - [x] 5.3 Implement `--dry-run` flag for preview without changes
  - [x] 5.4 Implement `--rollback <backup>` flag for restoration
  - [x] 5.5 Add confirmation prompt before applying migrations
  - [x] 5.6 Register command in `cli.py`

- [x] Task 6: Add schema_version to config model (AC: #1, #7)
  - [x] 6.1 Add `schema_version: str | None = None` to ResumeConfig
  - [x] 6.2 Update config loading to warn on legacy (no version)
  - [x] 6.3 Update `schemas/config.schema.json` with schema_version field

- [x] Task 7: Implement first migration (v1 → v2) (AC: #1, #6, #7)
  - [x] 7.1 Create `migrations/v1_to_v2.py`
  - [x] 7.2 Implement version detection (no schema_version = v1.0.0)
  - [x] 7.3 Implement adding schema_version field to .resume.yaml
  - [x] 7.4 Add idempotency check (safe to run multiple times)

- [x] Task 8: Add unit tests (AC: #1-7)
  - [x] 8.1 Test Migration base class interface
  - [x] 8.2 Test migration registry and path resolution
  - [x] 8.3 Test backup creation and restoration
  - [x] 8.4 Test YAML comment preservation
  - [x] 8.5 Test version detection
  - [x] 8.6 Test v1 → v2 migration

- [x] Task 9: Add integration tests (AC: #1-8)
  - [x] 9.1 Test `resume migrate --status` output
  - [x] 9.2 Test `resume migrate --dry-run` output
  - [x] 9.3 Test full migration cycle with backup
  - [x] 9.4 Test `resume migrate --rollback` restoration

## Dev Notes

### Project Context Reference

**CRITICAL**: Read `_bmad-output/project-context.md` before implementing. Key rules:
- Use `model_validator(mode='after')` not deprecated `@validator`
- Never use `print()` - use Rich console from `utils/console.py`
- Run `ruff check src tests --fix && ruff format src tests && mypy src --strict` before completing

### Architecture Constraints

1. **YAML Comment Preservation**: MUST use `ruamel.yaml` (not `pyyaml`) for all migration file operations. See pattern in `work_unit_loader.py`:
   ```python
   from ruamel.yaml import YAML
   yaml = YAML()
   yaml.preserve_quotes = True
   ```

2. **Version Scheme**: Semantic versioning - MAJOR.MINOR.PATCH
   - MAJOR: Breaking changes requiring migration
   - MINOR: New features, backward compatible
   - PATCH: Bug fixes

3. **Idempotency**: All migrations MUST be idempotent (safe to run multiple times)

4. **Atomicity**: Migrations must be atomic - either fully apply or fully rollback

### Critical Implementation Details

#### Migration Framework (Task 1, 2)

```python
# src/resume_as_code/migrations/__init__.py

CURRENT_SCHEMA_VERSION = "2.0.0"
LEGACY_VERSION = "1.0.0"

__all__ = ["CURRENT_SCHEMA_VERSION", "LEGACY_VERSION"]


# src/resume_as_code/migrations/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    success: bool
    files_modified: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class MigrationContext:
    """Context passed to migrations."""
    project_path: Path
    backup_path: Path | None = None
    dry_run: bool = False


class Migration(ABC):
    """Base class for schema migrations."""

    # Version this migration upgrades FROM
    from_version: str
    # Version this migration upgrades TO
    to_version: str
    # Human-readable description
    description: str

    @abstractmethod
    def check_applicable(self, ctx: MigrationContext) -> bool:
        """Check if this migration applies to the project.

        Args:
            ctx: Migration context with project path.

        Returns:
            True if migration should run, False otherwise.
        """
        ...

    @abstractmethod
    def preview(self, ctx: MigrationContext) -> list[str]:
        """Return list of changes that would be made (dry-run).

        Args:
            ctx: Migration context with project path.

        Returns:
            List of human-readable change descriptions.
        """
        ...

    @abstractmethod
    def apply(self, ctx: MigrationContext) -> MigrationResult:
        """Apply the migration. Must be idempotent.

        Args:
            ctx: Migration context with project path and backup path.

        Returns:
            MigrationResult with success status and details.
        """
        ...
```

#### Migration Registry (Task 2)

```python
# src/resume_as_code/migrations/registry.py

from pathlib import Path
from typing import Type
from ruamel.yaml import YAML

from resume_as_code.migrations import CURRENT_SCHEMA_VERSION, LEGACY_VERSION
from resume_as_code.migrations.base import Migration

_migrations: list[Type[Migration]] = []


def register_migration(cls: Type[Migration]) -> Type[Migration]:
    """Decorator to register a migration class."""
    _migrations.append(cls)
    # Sort by from_version for ordered application
    _migrations.sort(key=lambda m: m.from_version)
    return cls


def get_migration_path(from_version: str, to_version: str) -> list[Type[Migration]]:
    """Get ordered list of migrations from one version to another.

    Args:
        from_version: Starting version.
        to_version: Target version.

    Returns:
        List of Migration classes to apply in order.

    Raises:
        ValueError: If no migration path exists.
    """
    path: list[Type[Migration]] = []
    current = from_version

    while current != to_version:
        next_migration = next(
            (m for m in _migrations if m.from_version == current),
            None
        )
        if not next_migration:
            raise ValueError(f"No migration path from {current} to {to_version}")

        path.append(next_migration)
        current = next_migration.to_version

    return path


def detect_schema_version(project_path: Path) -> str:
    """Detect schema version from project config.

    Args:
        project_path: Path to project root.

    Returns:
        Version string or LEGACY_VERSION if no version found.
    """
    config_path = project_path / ".resume.yaml"
    if not config_path.exists():
        return LEGACY_VERSION

    yaml = YAML()
    yaml.preserve_quotes = True

    with config_path.open() as f:
        data = yaml.load(f) or {}

    return data.get("schema_version", LEGACY_VERSION)
```

#### Backup System (Task 3)

```python
# src/resume_as_code/migrations/backup.py

import shutil
from datetime import datetime
from pathlib import Path


def create_backup(project_path: Path) -> Path:
    """Create timestamped backup of project files.

    Args:
        project_path: Path to project root.

    Returns:
        Path to backup directory.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    backup_dir = project_path / f".resume-backup-{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)

    # Files to backup
    files_to_backup = [
        ".resume.yaml",
        "positions.yaml",
    ]

    # Backup individual files
    for filename in files_to_backup:
        src = project_path / filename
        if src.exists():
            shutil.copy2(src, backup_dir / filename)

    # Backup work-units directory
    work_units = project_path / "work-units"
    if work_units.exists():
        shutil.copytree(work_units, backup_dir / "work-units")

    return backup_dir


def restore_from_backup(backup_path: Path, project_path: Path) -> list[Path]:
    """Restore project files from backup.

    Args:
        backup_path: Path to backup directory.
        project_path: Path to project root.

    Returns:
        List of restored file paths.
    """
    restored: list[Path] = []

    for item in backup_path.iterdir():
        dest = project_path / item.name

        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

        restored.append(dest)

    return restored
```

#### YAML Comment Preservation (Task 4)

```python
# src/resume_as_code/migrations/yaml_handler.py

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap


def load_yaml_preserve(path: Path) -> CommentedMap:
    """Load YAML file preserving comments and formatting.

    Args:
        path: Path to YAML file.

    Returns:
        CommentedMap with preserved structure.
    """
    yaml = YAML()
    yaml.preserve_quotes = True

    with path.open() as f:
        return yaml.load(f) or CommentedMap()


def save_yaml_preserve(path: Path, data: CommentedMap) -> None:
    """Save YAML file preserving comments and formatting.

    Args:
        path: Path to save to.
        data: CommentedMap data to save.
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    with path.open("w") as f:
        yaml.dump(data, f)
```

#### Migrate CLI Command (Task 5)

```python
# src/resume_as_code/commands/migrate.py

from pathlib import Path

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
        _show_dry_run(migrations, project_path, ctx)
        return

    # Confirm before proceeding
    if not ctx.quiet:
        if not Confirm.ask(
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
    migrations: list[type],
    project_path: Path,
    ctx: Context,
) -> None:
    """Display dry-run preview."""
    console.print(f"\n[bold]Would apply {len(migrations)} migration(s):[/bold]\n")

    migration_ctx = MigrationContext(
        project_path=project_path,
        dry_run=True,
    )

    for i, migration_class in enumerate(migrations, 1):
        migration = migration_class()
        console.print(f"[bold cyan]Migration {i}:[/bold cyan] {migration.from_version} → {migration.to_version}")
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
    if not ctx.quiet:
        if not Confirm.ask(f"Restore from {backup_path}?"):
            info("Rollback cancelled")
            return

    restored = restore_from_backup(backup_path, project_path)

    if not ctx.quiet:
        success("Rollback complete!")
        for f in restored:
            console.print(f"  [green]✓[/green] Restored {f}")
```

#### First Migration (Task 7)

```python
# src/resume_as_code/migrations/v1_to_v2.py

from pathlib import Path

from resume_as_code.migrations import LEGACY_VERSION
from resume_as_code.migrations.base import Migration, MigrationContext, MigrationResult
from resume_as_code.migrations.registry import register_migration
from resume_as_code.migrations.yaml_handler import load_yaml_preserve, save_yaml_preserve


@register_migration
class MigrationV1ToV2(Migration):
    """Migration from v1.0.0 to v2.0.0.

    Changes:
    - Adds schema_version field to .resume.yaml
    """

    from_version = "1.0.0"
    to_version = "2.0.0"
    description = "Add schema_version field to track schema evolution"

    def check_applicable(self, ctx: MigrationContext) -> bool:
        """Check if project needs this migration."""
        config_path = ctx.project_path / ".resume.yaml"
        if not config_path.exists():
            return False

        data = load_yaml_preserve(config_path)
        return data.get("schema_version") is None

    def preview(self, ctx: MigrationContext) -> list[str]:
        """Preview changes."""
        changes: list[str] = []

        config_path = ctx.project_path / ".resume.yaml"
        if config_path.exists():
            data = load_yaml_preserve(config_path)
            if data.get("schema_version") is None:
                changes.append("Add schema_version: 2.0.0 to .resume.yaml")

        return changes

    def apply(self, ctx: MigrationContext) -> MigrationResult:
        """Apply migration."""
        result = MigrationResult(success=True)

        config_path = ctx.project_path / ".resume.yaml"
        if not config_path.exists():
            result.warnings.append(".resume.yaml not found, nothing to migrate")
            return result

        # Load preserving comments
        data = load_yaml_preserve(config_path)

        # Idempotency check
        if data.get("schema_version") is not None:
            result.warnings.append("schema_version already exists, skipping")
            return result

        # Add schema_version at the top
        # ruamel.yaml CommentedMap supports insert
        data.insert(0, "schema_version", self.to_version)

        # Save preserving formatting
        if not ctx.dry_run:
            save_yaml_preserve(config_path, data)
            result.files_modified.append(config_path)

        return result
```

### Files to Create/Modify

| File | Changes |
|------|---------|
| `src/resume_as_code/migrations/__init__.py` | Create: version constants |
| `src/resume_as_code/migrations/base.py` | Create: Migration base class, MigrationResult, MigrationContext |
| `src/resume_as_code/migrations/registry.py` | Create: Migration registry, version detection |
| `src/resume_as_code/migrations/backup.py` | Create: Backup and restore functions |
| `src/resume_as_code/migrations/yaml_handler.py` | Create: YAML comment preservation utilities |
| `src/resume_as_code/migrations/v1_to_v2.py` | Create: First migration implementation |
| `src/resume_as_code/commands/migrate.py` | Create: CLI command |
| `src/resume_as_code/cli.py` | Add: Register migrate command |
| `src/resume_as_code/models/config.py` | Add: schema_version field |
| `src/resume_as_code/config.py` | Add: Legacy version warning |
| `schemas/config.schema.json` | Add: schema_version property |
| `tests/unit/test_migrations.py` | Create: Unit tests |
| `tests/test_cli.py` | Add: Integration tests |

### Existing Code Patterns to Follow

1. **ruamel.yaml usage** - See `work_unit_loader.py:40-41` for preserve_quotes pattern
2. **CLI command structure** - See `commands/init.py` for new command pattern
3. **Rich console output** - See `utils/console.py` for `info`, `success`, `warning`, `err_console`
4. **Click options** - See `commands/build.py` for flag patterns
5. **JSON output mode** - See `commands/config_cmd.py` for `--json` handling

### Testing Requirements

1. **Unit tests** (`tests/unit/test_migrations.py`):
   - `test_migration_result_dataclass`
   - `test_migration_context_dataclass`
   - `test_register_migration_decorator`
   - `test_get_migration_path_single_step`
   - `test_get_migration_path_multi_step`
   - `test_get_migration_path_not_found`
   - `test_detect_schema_version_legacy`
   - `test_detect_schema_version_explicit`
   - `test_create_backup_creates_directory`
   - `test_create_backup_copies_files`
   - `test_restore_from_backup`
   - `test_yaml_comment_preservation`
   - `test_v1_to_v2_check_applicable`
   - `test_v1_to_v2_preview`
   - `test_v1_to_v2_apply`
   - `test_v1_to_v2_idempotent`

2. **Integration tests** (`tests/test_cli.py`):
   - `test_migrate_status_up_to_date`
   - `test_migrate_status_needs_migration`
   - `test_migrate_dry_run`
   - `test_migrate_apply_success`
   - `test_migrate_rollback`
   - `test_migrate_no_config_file`

### Definition of Done

- [x] Migration base class with preview/apply interface
- [x] Migration registry with version path resolution
- [x] `@register_migration` decorator works correctly
- [x] `detect_schema_version()` detects legacy (no version) as v1.0.0
- [x] `resume migrate --status` shows current vs latest version
- [x] `resume migrate --dry-run` previews changes without modifying
- [x] `resume migrate` applies migrations with confirmation
- [x] Automatic backup creation before migration
- [x] `resume migrate --rollback <backup>` restores from backup
- [x] YAML comment preservation during migration (via ruamel.yaml)
- [x] Idempotent migrations (safe to run multiple times)
- [x] MigrationV1ToV2 implemented (adds schema_version field)
- [x] schema_version field added to ResumeConfig model
- [x] Legacy version warning in config loading
- [x] Unit tests for migration framework
- [x] Integration tests for CLI command
- [x] All tests pass: `uv run pytest`
- [x] Type check passes: `uv run mypy src --strict`
- [x] Linting passes: `uv run ruff check src tests --fix && uv run ruff format src tests`

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No debug logs required for this implementation.

### Completion Notes List

- Implementation completed 2026-01-17
- All unit tests (49) and integration tests (12) passing
- Added post-migration validation for config integrity
- Added JSON output support (`--json` flag) for machine-readable output
- Documented backup scope in backup.py module docstring
- Updated legacy warning to use Rich console instead of logger

### File List

**Created:**
- `src/resume_as_code/migrations/__init__.py` - Version constants (CURRENT_SCHEMA_VERSION, LEGACY_VERSION)
- `src/resume_as_code/migrations/base.py` - Migration base class, MigrationResult, MigrationContext
- `src/resume_as_code/migrations/registry.py` - Migration registry, version detection
- `src/resume_as_code/migrations/backup.py` - Backup and restore functions
- `src/resume_as_code/migrations/yaml_handler.py` - YAML comment preservation utilities
- `src/resume_as_code/migrations/v1_to_v2.py` - First migration implementation (v1.0.0 → v2.0.0)
- `src/resume_as_code/commands/migrate.py` - CLI migrate command
- `tests/unit/test_migrations.py` - Unit tests for migration framework

**Modified:**
- `src/resume_as_code/cli.py` - Registered migrate command
- `src/resume_as_code/models/config.py` - Added schema_version field to ResumeConfig
- `src/resume_as_code/config.py` - Added legacy version warning using Rich console
- `schemas/config.schema.json` - Added schema_version property
- `tests/test_cli.py` - Added integration tests for migrate command
- `CLAUDE.md` - Added migrate command documentation
