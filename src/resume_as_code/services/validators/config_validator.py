"""Config validator for validating .resume.yaml.

Story 11.5: Validates configuration file against Pydantic ResumeConfig model,
validates schema_version format, and validates referenced paths exist.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import ValidationError as PydanticValidationError
from pydantic_core import ErrorDetails

from resume_as_code.models.config import ResumeConfig
from resume_as_code.models.errors import StructuredError
from resume_as_code.services.validators.base import (
    ResourceValidationResult,
    ResourceValidator,
)


class ConfigValidator(ResourceValidator):
    """Validator for .resume.yaml configuration."""

    # Semver pattern for schema_version validation
    SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

    @property
    def resource_type(self) -> str:
        return "Config"

    @property
    def resource_key(self) -> str:
        return "config"

    def validate(self, project_path: Path) -> ResourceValidationResult:
        """Validate .resume.yaml configuration.

        Args:
            project_path: Project root directory.

        Returns:
            Validation result with counts and errors.
        """
        config_path = project_path / ".resume.yaml"
        errors: list[StructuredError] = []
        warnings: list[StructuredError] = []

        if not config_path.exists():
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=config_path,
                valid_count=0,
                invalid_count=0,
            )

        # Load YAML
        try:
            with config_path.open() as f:
                raw_data = yaml.safe_load(f)
        except Exception as e:
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=config_path,
                valid_count=0,
                invalid_count=1,
                errors=[
                    StructuredError(
                        code="YAML_PARSE_ERROR",
                        message=f"Failed to parse .resume.yaml: {e}",
                        path=str(config_path),
                        suggestion="Check YAML syntax and formatting",
                        recoverable=True,
                    )
                ],
            )

        if not raw_data or not isinstance(raw_data, dict):
            # Empty config is valid
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=config_path,
                valid_count=1,
                invalid_count=0,
            )

        # Validate against Pydantic model
        try:
            config = ResumeConfig.model_validate(raw_data)
        except PydanticValidationError as e:
            for err in e.errors():
                field_path = ".".join(str(loc) for loc in err["loc"])
                errors.append(
                    StructuredError(
                        code="SCHEMA_VALIDATION_ERROR",
                        message=f".resume.yaml.{field_path}: {err['msg']}",
                        path=str(config_path),
                        suggestion=self._get_suggestion_for_error(err),
                        recoverable=True,
                    )
                )
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=config_path,
                valid_count=0,
                invalid_count=1,
                errors=errors,
            )

        # Validate schema_version format
        if config.schema_version is not None:
            version_errors = self._validate_schema_version(config.schema_version, config_path)
            errors.extend(version_errors)

        # Validate referenced paths exist
        path_warnings = self._validate_paths(config, project_path, config_path)
        warnings.extend(path_warnings)

        if errors:
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=config_path,
                valid_count=0,
                invalid_count=1,
                warning_count=len(warnings),
                errors=errors,
                warnings=warnings,
            )

        return ResourceValidationResult(
            resource_type=self.resource_type,
            source_path=config_path,
            valid_count=1,
            invalid_count=0,
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
        )

    def _validate_schema_version(self, version: str, config_path: Path) -> list[StructuredError]:
        """Validate schema_version format.

        Args:
            version: Schema version string.
            config_path: Path to config file for error reporting.

        Returns:
            List of errors (empty if valid).
        """
        errors: list[StructuredError] = []

        if not self.SEMVER_PATTERN.match(version):
            errors.append(
                StructuredError(
                    code="INVALID_SCHEMA_VERSION",
                    message=f"schema_version '{version}' is not valid semver format",
                    path=str(config_path),
                    suggestion="Use format 'X.Y.Z' (e.g., '2.0.0')",
                    recoverable=True,
                )
            )

        return errors

    def _validate_paths(
        self,
        config: ResumeConfig,
        project_path: Path,
        config_path: Path,
    ) -> list[StructuredError]:
        """Validate that referenced paths exist.

        Args:
            config: Validated ResumeConfig.
            project_path: Project root directory.
            config_path: Path to config file for warning reporting.

        Returns:
            List of warnings for missing paths.
        """
        warnings: list[StructuredError] = []

        # Check work_units_dir
        work_units_path = project_path / config.work_units_dir
        if not work_units_path.exists():
            warnings.append(
                StructuredError(
                    code="PATH_NOT_FOUND",
                    message=f"work_units_dir '{config.work_units_dir}' does not exist",
                    path=str(config_path),
                    suggestion="Create the directory or update the path in config",
                    recoverable=True,
                )
            )

        # Check templates_dir if specified
        if config.templates_dir is not None:
            templates_path = project_path / config.templates_dir
            if not templates_path.exists():
                warnings.append(
                    StructuredError(
                        code="PATH_NOT_FOUND",
                        message=f"templates_dir '{config.templates_dir}' does not exist",
                        path=str(config_path),
                        suggestion="Create the directory or remove the templates_dir setting",
                        recoverable=True,
                    )
                )

        # Check data_paths if specified
        if config.data_paths is not None:
            data_paths = config.data_paths
            path_checks = [
                ("profile", data_paths.profile),
                ("certifications", data_paths.certifications),
                ("education", data_paths.education),
                ("highlights", data_paths.highlights),
                ("publications", data_paths.publications),
                ("board_roles", data_paths.board_roles),
                ("certifications_dir", data_paths.certifications_dir),
                ("education_dir", data_paths.education_dir),
                ("highlights_dir", data_paths.highlights_dir),
                ("publications_dir", data_paths.publications_dir),
                ("board_roles_dir", data_paths.board_roles_dir),
            ]

            for name, path_str in path_checks:
                if path_str is not None:
                    resolved = project_path / path_str
                    if not resolved.exists():
                        warnings.append(
                            StructuredError(
                                code="PATH_NOT_FOUND",
                                message=f"data_paths.{name} '{path_str}' does not exist",
                                path=str(config_path),
                                suggestion="Create the path or remove the setting",
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
        field_loc = error.get("loc", [])

        if "missing" in error_type:
            field = field_loc[-1] if field_loc else "field"
            return f"Add the required '{field}' field"

        if "literal_error" in error_type:
            return "Check valid options in documentation"

        if "int" in error_type or "float" in error_type:
            return "Value must be a number"

        if "bool" in error_type:
            return "Value must be true or false"

        if "path" in str(field_loc).lower():
            return "Provide a valid file or directory path"

        return "Check the field value against the schema requirements"
