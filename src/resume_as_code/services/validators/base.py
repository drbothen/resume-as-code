"""Base classes for resource validators.

Story 11.5: Provides abstract base class and result dataclass
for all resource validators.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from resume_as_code.models.errors import StructuredError


@dataclass
class ResourceValidationResult:
    """Result of validating a single resource type."""

    resource_type: str  # e.g., "Positions", "Certifications"
    source_path: Path | None  # File/directory path if from dedicated location
    valid_count: int
    invalid_count: int
    warning_count: int = 0
    errors: list[StructuredError] = field(default_factory=list)
    warnings: list[StructuredError] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        """Total number of items validated."""
        return self.valid_count + self.invalid_count

    @property
    def is_valid(self) -> bool:
        """Check if all items passed validation (no errors)."""
        return self.invalid_count == 0


class ResourceValidator(ABC):
    """Base class for resource validators."""

    @property
    @abstractmethod
    def resource_type(self) -> str:
        """Resource type name for display (e.g., 'Positions')."""
        pass

    @property
    @abstractmethod
    def resource_key(self) -> str:
        """Resource key for JSON output (e.g., 'positions')."""
        pass

    @abstractmethod
    def validate(self, project_path: Path) -> ResourceValidationResult:
        """Validate all resources of this type.

        Args:
            project_path: Project root directory.

        Returns:
            Validation result with counts and errors.
        """
        pass
