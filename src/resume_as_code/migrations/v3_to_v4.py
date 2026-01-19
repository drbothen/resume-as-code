"""Migration from v3.0.0 to v4.0.0.

Story 12.1: Add Required Archetype Field with Inference Migration

This migration:
- Detects work units without archetype field
- Infers archetype from work unit content using rule-based classification
- Adds archetype field to each work unit YAML file
- Updates schema_version to 4.0.0 in .resume.yaml

Breaking Change: archetype is now a required field on all work units.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from resume_as_code.migrations.base import Migration, MigrationContext, MigrationResult
from resume_as_code.migrations.registry import register_migration
from resume_as_code.migrations.yaml_handler import load_yaml_preserve, save_yaml_preserve
from resume_as_code.services.archetype_inference import infer_archetype


def _load_work_unit_data(path: Path) -> dict[str, Any]:
    """Load work unit YAML as dict (not Pydantic model).

    We load as raw dict to avoid validation errors from missing
    archetype field during migration.

    Args:
        path: Path to work unit YAML file.

    Returns:
        Work unit data as dictionary.
    """
    data = load_yaml_preserve(path)
    return dict(data) if data else {}


@register_migration
class MigrationV3ToV4(Migration):
    """Migration from v3.0.0 to v4.0.0.

    Changes:
    - Adds required archetype field to all work units via inference
    - Updates schema_version to 4.0.0
    """

    from_version = "3.0.0"
    to_version = "4.0.0"
    description = "Add required archetype field to work units via inference"

    def _get_work_units_dir(self, ctx: MigrationContext) -> Path | None:
        """Get work-units directory if it exists.

        Args:
            ctx: Migration context.

        Returns:
            Path to work-units directory or None if not found.
        """
        wu_dir = ctx.project_path / "work-units"
        if wu_dir.exists() and wu_dir.is_dir():
            return wu_dir
        return None

    def _find_work_units_without_archetype(self, wu_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
        """Find work unit files that need archetype added.

        Args:
            wu_dir: Path to work-units directory.

        Returns:
            List of (file_path, data) tuples for work units missing archetype.
        """
        needs_migration: list[tuple[Path, dict[str, Any]]] = []

        for wu_file in wu_dir.glob("*.yaml"):
            data = _load_work_unit_data(wu_file)
            if not data:
                continue

            # Check if archetype is missing or empty
            if "archetype" not in data or not data.get("archetype"):
                needs_migration.append((wu_file, data))

        return needs_migration

    def check_applicable(self, ctx: MigrationContext) -> bool:
        """Check if project needs this migration.

        Returns True if:
        - .resume.yaml exists with schema_version < 4.0.0
        - OR any work units exist without archetype field
        """
        config_path = ctx.project_path / ".resume.yaml"
        if not config_path.exists():
            return False

        data = load_yaml_preserve(config_path)
        version = data.get("schema_version")

        # Already at v4.0.0+
        if version is not None and str(version) >= "4.0.0":
            return False

        # At v3.0.0, check for work units without archetype
        wu_dir = self._get_work_units_dir(ctx)
        if wu_dir is None:
            # No work units to migrate, but still need version bump
            return str(version) == "3.0.0" if version else True

        needs_migration = self._find_work_units_without_archetype(wu_dir)
        return len(needs_migration) > 0 or str(version) == "3.0.0"

    def preview(self, ctx: MigrationContext) -> list[str]:
        """Preview changes that would be made.

        Shows inferred archetype and confidence for each work unit.
        """
        changes: list[str] = []

        config_path = ctx.project_path / ".resume.yaml"
        if not config_path.exists():
            return changes

        data = load_yaml_preserve(config_path)

        # Check work units
        wu_dir = self._get_work_units_dir(ctx)
        if wu_dir is not None:
            needs_migration = self._find_work_units_without_archetype(wu_dir)

            for wu_file, wu_data in needs_migration:
                inference = infer_archetype(wu_data)
                changes.append(
                    f"{wu_file.name}: archetype={inference.archetype.value} "
                    f"(confidence={inference.confidence:.2f})"
                )

                # Show matched signals if any
                if inference.matched_signals:
                    signals_str = ", ".join(
                        f"{k}: {v}" for k, v in inference.matched_signals.items()
                    )
                    changes.append(f"  Matched: {signals_str}")

        # Version update
        current_version = data.get("schema_version", "3.0.0")
        if str(current_version) != "4.0.0":
            changes.append(f"Update schema_version: {current_version} → 4.0.0")

        return changes

    def apply(self, ctx: MigrationContext) -> MigrationResult:
        """Apply migration - add archetype to work units via inference."""
        result = MigrationResult(success=True)

        config_path = ctx.project_path / ".resume.yaml"
        if not config_path.exists():
            result.warnings.append(".resume.yaml not found, nothing to migrate")
            return result

        # Load config preserving comments
        config_data = load_yaml_preserve(config_path)

        # Idempotency check
        version = config_data.get("schema_version")
        if version is not None and str(version) >= "4.0.0":
            result.warnings.append("Already at v4.0.0+, skipping")
            return result

        # Process work units
        wu_dir = self._get_work_units_dir(ctx)
        if wu_dir is not None:
            needs_migration = self._find_work_units_without_archetype(wu_dir)

            for wu_file, _wu_data in needs_migration:
                # Reload with ruamel.yaml to preserve comments
                wu_preserved = load_yaml_preserve(wu_file)

                # Run inference on the data
                inference = infer_archetype(dict(wu_preserved))

                # Add archetype field after outcome (or at end if outcome not found)
                if not ctx.dry_run:
                    # Insert archetype after outcome
                    if "outcome" in wu_preserved:
                        # Get all keys in order
                        keys = list(wu_preserved.keys())
                        outcome_idx = keys.index("outcome")

                        # Create new map with archetype inserted after outcome
                        from ruamel.yaml.comments import CommentedMap

                        new_data = CommentedMap()
                        for i, key in enumerate(keys):
                            new_data[key] = wu_preserved[key]
                            if i == outcome_idx:
                                new_data["archetype"] = inference.archetype.value

                        wu_preserved = new_data
                    else:
                        wu_preserved["archetype"] = inference.archetype.value

                    # Update schema_version in work unit if present
                    if "schema_version" in wu_preserved:
                        wu_preserved["schema_version"] = "4.0.0"

                    save_yaml_preserve(wu_file, wu_preserved)
                    result.files_modified.append(wu_file)

                result.warnings.append(
                    f"{wu_file.name}: archetype={inference.archetype.value} "
                    f"(confidence={inference.confidence:.2f})"
                )

        # Update schema_version in config
        if "schema_version" in config_data:
            config_data["schema_version"] = self.to_version
        else:
            config_data.insert(0, "schema_version", self.to_version)

        # Save updated config
        if not ctx.dry_run:
            save_yaml_preserve(config_path, config_data)
            if config_path not in result.files_modified:
                result.files_modified.append(config_path)

        return result
