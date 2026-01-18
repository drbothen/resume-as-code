"""Migration registry for tracking and applying schema migrations.

This module provides:
- @register_migration decorator for registering migrations
- get_migration_path() for finding migration sequence
- detect_schema_version() for detecting current project version
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ruamel.yaml import YAML

from resume_as_code.migrations import LEGACY_VERSION

if TYPE_CHECKING:
    from resume_as_code.migrations.base import Migration

# Global registry of migration classes
_migrations: list[type[Migration]] = []


def register_migration(cls: type[Migration]) -> type[Migration]:
    """Decorator to register a migration class.

    Registered migrations are sorted by from_version for ordered application.

    Args:
        cls: Migration class to register.

    Returns:
        The registered migration class (unchanged).

    Example:
        @register_migration
        class MigrationV1ToV2(Migration):
            from_version = "1.0.0"
            to_version = "2.0.0"
            ...
    """
    _migrations.append(cls)
    # Sort by from_version for ordered application
    _migrations.sort(key=lambda m: m.from_version)
    return cls


def get_migration_path(from_version: str, to_version: str) -> list[type[Migration]]:
    """Get ordered list of migrations from one version to another.

    Builds a chain of migrations by matching each migration's to_version
    with the next migration's from_version.

    Args:
        from_version: Starting version.
        to_version: Target version.

    Returns:
        List of Migration classes to apply in order.

    Raises:
        ValueError: If no migration path exists between versions.

    Example:
        >>> path = get_migration_path("1.0.0", "2.0.0")
        >>> for migration_cls in path:
        ...     migration = migration_cls()
        ...     migration.apply(ctx)
    """
    path: list[type[Migration]] = []
    current = from_version

    while current != to_version:
        next_migration = next(
            (m for m in _migrations if m.from_version == current),
            None,
        )
        if not next_migration:
            raise ValueError(f"No migration path from {current} to {to_version}")

        path.append(next_migration)
        current = next_migration.to_version

    return path


def detect_schema_version(project_path: Path) -> str:
    """Detect schema version from project config.

    Reads .resume.yaml and extracts the schema_version field.
    If the file doesn't exist or has no schema_version field,
    returns LEGACY_VERSION (1.0.0).

    Args:
        project_path: Path to project root.

    Returns:
        Version string or LEGACY_VERSION if no version found.

    Example:
        >>> version = detect_schema_version(Path("/my/project"))
        >>> if version == LEGACY_VERSION:
        ...     print("Project needs migration")
    """
    config_path = project_path / ".resume.yaml"
    if not config_path.exists():
        return LEGACY_VERSION

    yaml = YAML()
    yaml.preserve_quotes = True

    with config_path.open() as f:
        data = yaml.load(f) or {}

    return str(data.get("schema_version", LEGACY_VERSION))
