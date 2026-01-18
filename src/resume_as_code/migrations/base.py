"""Base classes and data structures for schema migrations.

This module provides the foundation for all migrations including:
- MigrationResult: Outcome of a migration operation
- MigrationContext: Runtime context passed to migrations
- Migration: Abstract base class for all migrations
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MigrationResult:
    """Result of a migration operation.

    Attributes:
        success: Whether the migration completed successfully.
        files_modified: List of files that were modified.
        warnings: Non-fatal warnings encountered during migration.
        errors: Error messages if migration failed.
    """

    success: bool
    files_modified: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class MigrationContext:
    """Context passed to migrations during execution.

    Attributes:
        project_path: Path to the project root directory.
        backup_path: Path to backup directory (None if no backup created).
        dry_run: If True, preview changes without modifying files.
    """

    project_path: Path
    backup_path: Path | None = None
    dry_run: bool = False


class Migration(ABC):
    """Base class for schema migrations.

    All migrations must inherit from this class and implement:
    - check_applicable(): Determine if migration should run
    - preview(): List changes that would be made (for dry-run)
    - apply(): Execute the migration

    Class Attributes:
        from_version: Version this migration upgrades FROM.
        to_version: Version this migration upgrades TO.
        description: Human-readable description of the migration.
    """

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

        All migrations must be safe to run multiple times.
        If the migration has already been applied, it should
        return success with appropriate warnings.

        Args:
            ctx: Migration context with project path and backup path.

        Returns:
            MigrationResult with success status and details.
        """
        ...
