"""Validate command for Work Unit schema validation."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from resume_as_code.config import get_config
from resume_as_code.models.errors import ValidationError
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.validator import ValidationSummary, validate_path
from resume_as_code.utils.console import console, error, info, success
from resume_as_code.utils.errors import handle_errors


@click.command("validate")
@click.argument(
    "path",
    type=click.Path(exists=True, path_type=Path),
    required=False,
)
@click.pass_context
@handle_errors
def validate_command(ctx: click.Context, path: Path | None) -> None:
    """Validate Work Units against the JSON Schema.

    PATH can be a single YAML file or a directory containing Work Units.
    Defaults to work-units/ directory if not specified.
    """
    config = get_config()

    # Default to work-units directory
    if path is None:
        path = config.work_units_dir
        if not path.exists():
            if ctx.obj.json_output:
                response = JSONResponse(
                    status="success",
                    command="validate",
                    data={"valid_count": 0, "invalid_count": 0, "files": []},
                )
                console.print(response.to_json())
            else:
                info("No work-units/ directory found. Nothing to validate.")
            return

    # Run validation
    summary = validate_path(path)

    # Handle empty directory case
    if summary.total_count == 0:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="validate",
                data={"valid_count": 0, "invalid_count": 0, "files": []},
            )
            console.print(response.to_json())
        else:
            info("No YAML files found to validate.")
        return

    # Output results and handle exit code
    if ctx.obj.json_output:
        _output_json(summary)
        # In JSON mode, exit directly to avoid double JSON output from error handler
        if summary.invalid_count > 0:
            sys.exit(ValidationError.exit_code)
    else:
        _output_rich(summary)
        # In Rich mode, raise exception to let error handler format the error
        if summary.invalid_count > 0:
            raise ValidationError(
                message=f"{summary.invalid_count} Work Unit(s) failed validation",
                path=str(path),
            )


def _output_json(summary: ValidationSummary) -> None:
    """Output validation results as JSON."""
    response = JSONResponse(
        status="success" if summary.invalid_count == 0 else "error",
        command="validate",
        data={
            "valid_count": summary.valid_count,
            "invalid_count": summary.invalid_count,
            "files": [
                {
                    "path": str(r.file_path),
                    "valid": r.valid,
                    "errors": [e.to_dict() for e in r.errors],
                }
                for r in summary.results
            ],
        },
    )
    console.print(response.to_json())


def _output_rich(summary: ValidationSummary) -> None:
    """Output validation results with Rich formatting."""
    for result in summary.results:
        if result.valid:
            success(f"{result.file_path}")
        else:
            error(f"{result.file_path}")
            for err in result.errors:
                console.print(f"  [red]->[/red] {err.message}")
                if err.suggestion:
                    console.print(f"    [dim]{err.suggestion}[/dim]")

    # Summary
    console.print()
    if summary.invalid_count == 0:
        success(f"All {summary.valid_count} Work Unit(s) passed validation")
    else:
        error(f"{summary.invalid_count} of {summary.total_count} Work Unit(s) failed validation")
