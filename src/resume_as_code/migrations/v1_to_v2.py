"""Migration from v1.0.0 to v2.0.0.

Story 9.1: Schema Evolution & Migration System

This migration:
- Adds schema_version field to .resume.yaml
"""

from __future__ import annotations

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
