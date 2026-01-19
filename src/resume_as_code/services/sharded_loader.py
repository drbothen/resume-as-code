"""Generic sharded data loader service (Story 11.2).

Provides directory-based storage for any Pydantic model, enabling per-item
YAML files instead of single-file lists. This addresses TD-005: Directory-Based
Sharding for work-units pattern consistency.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Generic, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from resume_as_code.models.errors import ValidationError

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Generic type for any Pydantic model
T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class SourceTracked(Protocol):
    """Protocol for models that track their source file.

    Models loaded via ShardedLoader will have a _source_file attribute
    set to the Path of the YAML file they were loaded from.

    This protocol enables type-safe access to the source file:

        if isinstance(item, SourceTracked):
            print(f"Loaded from: {item._source_file}")

    Note: The _source_file attribute is dynamically set at runtime
    after model instantiation, not defined in the model class itself.
    """

    _source_file: Path


class ShardedLoader(Generic[T]):
    """Generic loader for directory-based sharded storage.

    Supports loading, saving, and removing individual YAML files from a
    directory. Each file contains a single item serialized as YAML.

    Follows WorkUnitLoader pattern for consistency.

    Attributes:
        directory: Path to the directory containing sharded YAML files.
        model_class: Pydantic model class for validation.
    """

    def __init__(self, directory: Path, model_class: type[T]) -> None:
        """Initialize loader.

        Args:
            directory: Directory containing sharded YAML files.
            model_class: Pydantic model class to use for validation.
        """
        self.directory = directory
        self.model_class = model_class
        self._yaml = YAML()
        self._yaml.preserve_quotes = True
        self._yaml.default_flow_style = False

    def load_all(self) -> list[T]:
        """Load all items from directory.

        Returns:
            List of model instances sorted alphabetically by file path.
            Each item satisfies the SourceTracked protocol with a `_source_file`
            attribute set to its source Path. Use `isinstance(item, SourceTracked)`
            for type-safe access to this attribute.

        Raises:
            ValidationError: If any file fails schema validation or YAML parsing.
        """
        items: list[T] = []

        if not self.directory.exists():
            logger.debug("Directory does not exist: %s", self.directory)
            return items

        for yaml_file in sorted(self.directory.glob("*.yaml")):
            if yaml_file.name.startswith("."):
                logger.debug("Skipping hidden file: %s", yaml_file.name)
                continue

            logger.debug("Loading item: %s", yaml_file.name)
            try:
                with yaml_file.open() as f:
                    data = self._yaml.load(f)
            except YAMLError as e:
                raise ValidationError(
                    message=f"Invalid YAML in {yaml_file.name}: {e}",
                    path=str(yaml_file),
                    suggestion="Check YAML syntax in the file",
                ) from e

            try:
                item = self.model_class.model_validate(data)
                # Attach source file path for tracking (AC5)
                object.__setattr__(item, "_source_file", yaml_file)
                items.append(item)
            except PydanticValidationError as e:
                raise ValidationError(
                    message=f"Invalid schema in {yaml_file.name}: {e}",
                    path=str(yaml_file),
                    suggestion="Check the file for schema errors",
                ) from e

        logger.info("Loaded %d items from %s", len(items), self.directory)
        return items

    def save(self, item: T, item_id: str) -> Path:
        """Save item to a YAML file in the directory.

        Creates the directory if it doesn't exist.

        Args:
            item: Model instance to save.
            item_id: Unique ID for the file (without .yaml extension).

        Returns:
            Path to the saved file.
        """
        # Create directory if needed
        self.directory.mkdir(parents=True, exist_ok=True)

        file_path = self.directory / f"{item_id}.yaml"

        # Convert to dict, excluding None values for cleaner YAML
        data = item.model_dump(exclude_none=True, mode="json")

        with file_path.open("w") as f:
            self._yaml.dump(data, f)

        logger.info("Saved item to %s", file_path)
        return file_path

    def remove(self, item_id: str) -> bool:
        """Remove item file from directory.

        Args:
            item_id: ID of the item (without .yaml extension).

        Returns:
            True if file was removed, False if it didn't exist.
        """
        file_path = self.directory / f"{item_id}.yaml"

        if not file_path.exists():
            logger.debug("File not found for removal: %s", file_path)
            return False

        file_path.unlink()
        logger.info("Removed item file: %s", file_path)
        return True

    def generate_id(self, item: T) -> str:
        """Generate ID for an item based on its type and attributes.

        ID patterns per resource type:
        - Certifications: cert-YYYY-MM-{slug}
        - Publications: pub-YYYY-MM-{slug}
        - Education: edu-YYYY-{institution-slug}
        - Board Roles: board-YYYY-MM-{org-slug}
        - Highlights: hl-NNN-{slug}

        Args:
            item: Model instance to generate ID for.

        Returns:
            Generated ID string.
        """
        model_name = self.model_class.__name__.lower()

        # Extract common fields with safe fallbacks
        name_field = self._get_name_field(item)
        date_field = self._get_date_field(item)

        slug = self._slugify(name_field)

        if model_name == "certification":
            if date_field:
                return f"cert-{date_field}-{slug}"
            return f"cert-{slug}"

        if model_name == "publication":
            if date_field:
                return f"pub-{date_field}-{slug}"
            return f"pub-{slug}"

        if model_name == "education":
            # Use graduation_year and institution
            year = getattr(item, "graduation_year", None)
            institution = getattr(item, "institution", "")
            inst_slug = self._slugify(institution)
            if year:
                return f"edu-{year}-{inst_slug}"
            return f"edu-{inst_slug}"

        if model_name == "boardrole":
            org = getattr(item, "organization", "")
            org_slug = self._slugify(org)
            if date_field:
                return f"board-{date_field}-{org_slug}"
            return f"board-{org_slug}"

        # Generic fallback
        return f"{model_name[:4]}-{slug}"

    def _get_name_field(self, item: T) -> str:
        """Extract name field from item."""
        # Try common name fields
        for field in ("name", "title", "degree", "organization"):
            value = getattr(item, field, None)
            if value:
                return str(value)
        return "unnamed"

    def _get_date_field(self, item: T) -> str | None:
        """Extract date field from item (YYYY-MM format)."""
        for field in ("date", "start_date"):
            value = getattr(item, field, None)
            if value:
                return str(value)
        return None

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug.

        Args:
            text: Input text to slugify.

        Returns:
            Lowercase slug with hyphens.
        """
        # Convert to lowercase
        slug = text.lower()
        # Replace non-alphanumeric with hyphens
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        # Remove leading/trailing hyphens
        slug = slug.strip("-")
        # Collapse multiple hyphens
        slug = re.sub(r"-+", "-", slug)
        return slug
