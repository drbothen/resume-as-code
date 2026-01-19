"""Certification validator for validating certifications.

Story 11.5: Validates certification data including Pydantic schema
validation and cross-field validation (date <= expires).
Warns on expired certifications.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError as PydanticValidationError
from pydantic_core import ErrorDetails

from resume_as_code.data_loader import get_storage_mode, load_certifications
from resume_as_code.models.certification import Certification
from resume_as_code.models.errors import StructuredError
from resume_as_code.services.validators.base import (
    ResourceValidationResult,
    ResourceValidator,
)


class CertificationValidator(ResourceValidator):
    """Validator for certifications."""

    @property
    def resource_type(self) -> str:
        return "Certifications"

    @property
    def resource_key(self) -> str:
        return "certifications"

    def validate(self, project_path: Path) -> ResourceValidationResult:
        """Validate all certifications.

        Args:
            project_path: Project root directory.

        Returns:
            Validation result with counts and errors.
        """
        errors: list[StructuredError] = []
        warnings: list[StructuredError] = []
        valid_count = 0
        invalid_count = 0

        # Determine source path
        mode, source_path = get_storage_mode(project_path, "certifications")

        try:
            certs = load_certifications(project_path)
        except PydanticValidationError as e:
            # Convert Pydantic validation errors
            for err in e.errors():
                field_path = ".".join(str(loc) for loc in err["loc"])
                errors.append(
                    StructuredError(
                        code="SCHEMA_VALIDATION_ERROR",
                        message=f"certifications.{field_path}: {err['msg']}",
                        path=str(source_path) if source_path else "certifications",
                        suggestion=self._get_suggestion_for_error(err),
                        recoverable=True,
                    )
                )
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=source_path,
                valid_count=0,
                invalid_count=1,
                errors=errors,
            )
        except Exception as e:
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=source_path,
                valid_count=0,
                invalid_count=1,
                errors=[
                    StructuredError(
                        code="LOAD_ERROR",
                        message=f"Failed to load certifications: {e}",
                        path=str(source_path) if source_path else "certifications",
                        suggestion="Check YAML syntax and field types",
                        recoverable=True,
                    )
                ],
            )

        if not certs:
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=source_path,
                valid_count=0,
                invalid_count=0,
            )

        # Validate each certification
        for i, cert in enumerate(certs):
            cert_errors = self._validate_certification(cert, i, source_path)
            cert_warnings = self._check_warnings(cert, i, source_path)

            if cert_errors:
                invalid_count += 1
                errors.extend(cert_errors)
            else:
                valid_count += 1

            warnings.extend(cert_warnings)

        return ResourceValidationResult(
            resource_type=self.resource_type,
            source_path=source_path,
            valid_count=valid_count,
            invalid_count=invalid_count,
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
        )

    def _validate_certification(
        self,
        cert: Certification,
        index: int,
        source_path: Path | None,
    ) -> list[StructuredError]:
        """Validate cross-field rules for a certification.

        Args:
            cert: Certification to validate.
            index: Index in certifications list.
            source_path: Path to source file for error reporting.

        Returns:
            List of errors (empty if valid).
        """
        errors: list[StructuredError] = []

        # Check date <= expires (if both present) - AC4
        if cert.date and cert.expires and cert.date > cert.expires:
            errors.append(
                StructuredError(
                    code="INVALID_DATE_RANGE",
                    message=(
                        f"Certification '{cert.name}' has date ({cert.date}) "
                        f"after expires ({cert.expires})"
                    ),
                    path=f"certifications[{index}]",
                    suggestion="Ensure date is before or equal to expires",
                    recoverable=True,
                )
            )

        return errors

    def _check_warnings(
        self,
        cert: Certification,
        index: int,
        source_path: Path | None,
    ) -> list[StructuredError]:
        """Check for warning conditions.

        Args:
            cert: Certification to check.
            index: Index in certifications list.
            source_path: Path to source file for warning reporting.

        Returns:
            List of warnings.
        """
        warnings: list[StructuredError] = []

        status = cert.get_status()
        if status == "expired":
            warnings.append(
                StructuredError(
                    code="CERTIFICATION_EXPIRED",
                    message=f"Certification '{cert.name}' expired on {cert.expires}",
                    path=f"certifications[{index}]",
                    suggestion="Update expiration date or set display: false",
                    recoverable=True,
                )
            )
        elif status == "expires_soon":
            warnings.append(
                StructuredError(
                    code="CERTIFICATION_EXPIRES_SOON",
                    message=(
                        f"Certification '{cert.name}' expires within 90 days ({cert.expires})"
                    ),
                    path=f"certifications[{index}]",
                    suggestion="Consider renewing this certification",
                    recoverable=True,
                )
            )

        return warnings

    def _get_suggestion_for_error(self, error: ErrorDetails) -> str:
        """Generate a suggestion for a validation error.

        Args:
            error: Pydantic error dict.

        Returns:
            Helpful suggestion string.
        """
        error_type = error.get("type", "")

        if "missing" in error_type:
            field = error["loc"][-1] if error["loc"] else "field"
            return f"Add the required '{field}' field"

        if "string_type" in error_type:
            return "Value must be a string"

        if "date" in error_type.lower():
            return "Use YYYY-MM format for dates (e.g., '2024-01')"

        return "Check the field value against the schema requirements"
