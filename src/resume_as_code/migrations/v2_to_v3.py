"""Migration from v2.0.0 to v3.0.0.

Story 9.2: Separate Configuration from Resume Data

This migration:
- Extracts profile from .resume.yaml to profile.yaml
- Extracts certifications from .resume.yaml to certifications.yaml
- Extracts education from .resume.yaml to education.yaml
- Extracts career_highlights from .resume.yaml to highlights.yaml
- Extracts publications from .resume.yaml to publications.yaml
- Extracts board_roles from .resume.yaml to board-roles.yaml
- Updates schema_version to 3.0.0
- Removes extracted data from .resume.yaml
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from resume_as_code.migrations.base import Migration, MigrationContext, MigrationResult
from resume_as_code.migrations.registry import register_migration
from resume_as_code.migrations.yaml_handler import load_yaml_preserve, save_yaml_preserve

# Mapping of config keys to output file names
# Note: career_highlights in config maps to highlights.yaml
DATA_FIELDS: dict[str, str] = {
    "profile": "profile.yaml",
    "certifications": "certifications.yaml",
    "education": "education.yaml",
    "career_highlights": "highlights.yaml",
    "publications": "publications.yaml",
    "board_roles": "board-roles.yaml",
}


def _create_yaml_list() -> CommentedSeq:
    """Create an empty YAML list."""
    return CommentedSeq()


def _save_data_file(
    path: Path, data: CommentedMap | CommentedSeq | list[Any] | dict[str, Any]
) -> None:
    """Save data to a YAML file with proper formatting.

    Args:
        path: Path to save to.
        data: Data to save (can be dict/map for profile, list/seq for others).
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    with path.open("w") as f:
        yaml.dump(data, f)


@register_migration
class MigrationV2ToV3(Migration):
    """Migration from v2.0.0 to v3.0.0.

    Changes:
    - Extracts embedded data (profile, certifications, education,
      career_highlights, publications, board_roles) to separate files
    - Updates schema_version to 3.0.0
    - Removes extracted data from .resume.yaml
    """

    from_version = "2.0.0"
    to_version = "3.0.0"
    description = "Separate configuration from resume data into dedicated files"

    def _get_embedded_data_fields(self, data: CommentedMap) -> list[str]:
        """Get list of data fields embedded in config.

        Args:
            data: Config data from .resume.yaml.

        Returns:
            List of field names that have data in the config.
        """
        embedded = []
        for field in DATA_FIELDS:
            value = data.get(field)
            # Check if it's a non-empty profile or non-empty list
            if value is not None and (
                (isinstance(value, dict) and value) or (isinstance(value, list) and value)
            ):
                embedded.append(field)
        return embedded

    def check_applicable(self, ctx: MigrationContext) -> bool:
        """Check if project needs this migration.

        Returns True if:
        - .resume.yaml exists
        - schema_version is 2.0.0 or any data fields are embedded
        """
        config_path = ctx.project_path / ".resume.yaml"
        if not config_path.exists():
            return False

        data = load_yaml_preserve(config_path)
        version = data.get("schema_version")

        # Already at v3+
        if version is not None and str(version) >= "3.0.0":
            return False

        # At v2.0.0, check for embedded data
        embedded = self._get_embedded_data_fields(data)
        return len(embedded) > 0 or version == "2.0.0"

    def preview(self, ctx: MigrationContext) -> list[str]:
        """Preview changes that would be made."""
        changes: list[str] = []

        config_path = ctx.project_path / ".resume.yaml"
        if not config_path.exists():
            return changes

        data = load_yaml_preserve(config_path)

        # Check each data field
        for field, filename in DATA_FIELDS.items():
            value = data.get(field)
            file_path = ctx.project_path / filename

            if value is not None:
                if isinstance(value, dict) and value:
                    changes.append(f"Extract {field} to {filename}")
                    changes.append(f"Remove {field} from .resume.yaml")
                elif isinstance(value, list) and value:
                    count = len(value)
                    changes.append(f"Extract {field} ({count} items) to {filename}")
                    changes.append(f"Remove {field} from .resume.yaml")

            # Note if file already exists
            if file_path.exists():
                changes.append(f"  WARNING: {filename} already exists, will merge data")

        # Version update
        current_version = data.get("schema_version", "2.0.0")
        if str(current_version) != "3.0.0":
            changes.append("Update schema_version: 2.0.0 → 3.0.0")

        return changes

    def apply(self, ctx: MigrationContext) -> MigrationResult:
        """Apply migration - extract data to separate files."""
        result = MigrationResult(success=True)

        config_path = ctx.project_path / ".resume.yaml"
        if not config_path.exists():
            result.warnings.append(".resume.yaml not found, nothing to migrate")
            return result

        # Load config preserving comments
        data = load_yaml_preserve(config_path)

        # Idempotency check
        version = data.get("schema_version")
        if version is not None and str(version) >= "3.0.0":
            result.warnings.append("Already at v3.0.0+, skipping")
            return result

        # Track what fields were extracted for removal
        fields_to_remove: list[str] = []

        # Process each data field
        for field, filename in DATA_FIELDS.items():
            value = data.get(field)
            if value is None:
                continue

            # Skip empty values
            is_empty = False
            if isinstance(value, dict) and not value or isinstance(value, list) and not value:
                is_empty = True

            if is_empty:
                fields_to_remove.append(field)
                continue

            file_path = ctx.project_path / filename

            # Handle existing files - load and merge
            if file_path.exists():
                existing = load_yaml_preserve(file_path)
                if isinstance(value, dict) and isinstance(existing, CommentedMap):
                    # Merge profile - embedded takes precedence
                    for k, v in value.items():
                        existing[k] = v
                    value = existing
                elif isinstance(value, list) and isinstance(existing, (list, CommentedSeq)):
                    # Merge lists - append new items (could be smarter with dedup)
                    combined = list(existing) + list(value)
                    value = combined
                result.warnings.append(f"{filename} existed, merged with embedded data")

            # Save to separate file
            if not ctx.dry_run:
                _save_data_file(file_path, value)
                result.files_modified.append(file_path)

            fields_to_remove.append(field)

        # Remove extracted fields from config
        for field in fields_to_remove:
            if field in data:
                del data[field]

        # Update schema_version
        if "schema_version" in data:
            data["schema_version"] = self.to_version
        else:
            data.insert(0, "schema_version", self.to_version)

        # Save updated config
        if not ctx.dry_run:
            save_yaml_preserve(config_path, data)
            if config_path not in result.files_modified:
                result.files_modified.append(config_path)

        return result
