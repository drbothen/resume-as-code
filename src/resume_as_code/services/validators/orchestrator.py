"""Validation orchestrator for running all resource validators.

Story 11.5: Coordinates validation across all resource types
and aggregates results for unified reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from resume_as_code.services.validators.base import (
    ResourceValidationResult,
    ResourceValidator,
)


@dataclass
class AggregatedValidationResult:
    """Aggregated result from running all validators."""

    results: list[ResourceValidationResult] = field(default_factory=list)

    @property
    def total_errors(self) -> int:
        """Total error count across all resource types."""
        return sum(r.invalid_count for r in self.results) + sum(len(r.errors) for r in self.results)

    @property
    def total_warnings(self) -> int:
        """Total warning count across all resource types."""
        return sum(r.warning_count for r in self.results)

    @property
    def is_valid(self) -> bool:
        """Check if all validations passed (no errors)."""
        return all(r.is_valid for r in self.results)

    @property
    def valid_resource_count(self) -> int:
        """Count of resource types with no errors."""
        return sum(1 for r in self.results if r.is_valid)

    @property
    def total_resource_count(self) -> int:
        """Total number of resource types validated."""
        return len(self.results)


class ValidationOrchestrator:
    """Orchestrates validation across all resource types."""

    def __init__(self, validators: list[ResourceValidator] | None = None) -> None:
        """Initialize orchestrator with validators.

        Args:
            validators: List of validators to run. If None, uses all
                       registered validators.
        """
        self._validators = validators or self._get_default_validators()

    def _get_default_validators(self) -> list[ResourceValidator]:
        """Get the default set of all validators."""
        # Import here to avoid circular imports
        from resume_as_code.services.validators.board_role_validator import (
            BoardRoleValidator,
        )
        from resume_as_code.services.validators.certification_validator import (
            CertificationValidator,
        )
        from resume_as_code.services.validators.config_validator import ConfigValidator
        from resume_as_code.services.validators.education_validator import (
            EducationValidator,
        )
        from resume_as_code.services.validators.highlight_validator import (
            HighlightValidator,
        )
        from resume_as_code.services.validators.position_validator import (
            PositionValidator,
        )
        from resume_as_code.services.validators.publication_validator import (
            PublicationValidator,
        )
        from resume_as_code.services.validators.work_unit_validator import (
            WorkUnitValidator,
        )

        return [
            WorkUnitValidator(),
            PositionValidator(),
            CertificationValidator(),
            EducationValidator(),
            PublicationValidator(),
            BoardRoleValidator(),
            HighlightValidator(),
            ConfigValidator(),
        ]

    def validate_all(self, project_path: Path) -> AggregatedValidationResult:
        """Run all validators and aggregate results.

        Args:
            project_path: Project root directory.

        Returns:
            Aggregated validation result.
        """
        results: list[ResourceValidationResult] = []

        for validator in self._validators:
            result = validator.validate(project_path)
            results.append(result)

        return AggregatedValidationResult(results=results)

    def validate_single(
        self, project_path: Path, resource_key: str
    ) -> ResourceValidationResult | None:
        """Run a single validator by resource key.

        Args:
            project_path: Project root directory.
            resource_key: Resource key (e.g., 'positions', 'certifications').

        Returns:
            Validation result, or None if resource key not found.
        """
        for validator in self._validators:
            if validator.resource_key == resource_key:
                return validator.validate(project_path)
        return None

    def get_validator_keys(self) -> list[str]:
        """Get list of all available validator keys.

        Returns:
            List of resource keys (e.g., ['work_units', 'positions', ...]).
        """
        return [v.resource_key for v in self._validators]
