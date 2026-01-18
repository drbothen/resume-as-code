"""Backup and restore operations for schema migrations.

This module provides functions for creating and restoring backups
of resume project files during migrations.

Backup Scope:
    The backup includes all core resume data files:
    - .resume.yaml (config, profile, certifications, education, etc.)
    - positions.yaml (employment history)
    - work-units/ (individual achievements)

    Files NOT included in backup (by design):
    - templates/ (user templates are not modified by migrations)
    - dist/ (generated output, can be regenerated)
    - .git/ (version control has its own history)
    - Other project files (README, docs, etc.)
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


def create_backup(project_path: Path) -> Path:
    """Create timestamped backup of project files.

    Creates a backup directory containing:
    - .resume.yaml (if exists)
    - positions.yaml (if exists)
    - work-units/ directory (if exists)

    Args:
        project_path: Path to project root.

    Returns:
        Path to backup directory.

    Raises:
        FileExistsError: If backup directory already exists (extremely unlikely).

    Example:
        >>> backup_path = create_backup(Path("/my/project"))
        >>> print(f"Backup created at: {backup_path}")
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

    Overwrites existing files and directories with backup contents.
    Directories are completely replaced (not merged).

    Args:
        backup_path: Path to backup directory.
        project_path: Path to project root.

    Returns:
        List of restored file paths.

    Example:
        >>> restored = restore_from_backup(backup_path, project_path)
        >>> print(f"Restored {len(restored)} items")
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
