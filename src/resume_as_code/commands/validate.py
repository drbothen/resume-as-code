"""Validate command for comprehensive resource validation.

Story 11.5: Validates all resource types - Work Units, Positions,
Certifications, Education, Publications, Board Roles, Highlights, and Config.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import click
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from ruamel.yaml import YAML

from resume_as_code.config import get_config
from resume_as_code.models.errors import ValidationError
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.content_validator import (
    ContentWarning,
    validate_content_density,
    validate_content_quality,
    validate_position_reference,
)
from resume_as_code.services.validators import ValidationOrchestrator
from resume_as_code.services.validators.base import ResourceValidationResult
from resume_as_code.services.validators.orchestrator import AggregatedValidationResult
from resume_as_code.utils.console import console, info, json_output
from resume_as_code.utils.errors import handle_errors


@click.group("validate", invoke_without_command=True)
@click.pass_context
@handle_errors
def validate_command(ctx: click.Context) -> None:
    """Validate resources against schema and content guidelines.

    Without a subcommand, validates ALL resource types.
    Use 'resume validate <resource>' to validate specific resource types.

    Resource types: work-units, positions, certifications, education,
    publications, board-roles, highlights, config
    """
    # If no subcommand was invoked, validate all resources
    if ctx.invoked_subcommand is None:
        _validate_all(ctx)


def _validate_all(ctx: click.Context) -> None:
    """Validate all resource types using the orchestrator."""
    orchestrator = ValidationOrchestrator()
    result = orchestrator.validate_all(Path.cwd())

    if ctx.obj.json_output:
        _output_all_json(result)
    else:
        _output_all_summary(result)

    # Exit with appropriate code (AC6)
    if not result.is_valid:
        sys.exit(ValidationError.exit_code)


def _output_all_summary(result: AggregatedValidationResult) -> None:
    """Output summary table for all resource validation (AC2)."""
    table = Table(title="Validation Summary")
    table.add_column("Resource Type", style="cyan")
    table.add_column("Valid", style="green", justify="right")
    table.add_column("Invalid", style="red", justify="right")
    table.add_column("Warnings", style="yellow", justify="right")
    table.add_column("Status", justify="center")

    for res in result.results:
        status = "[green]✓[/green]" if res.is_valid else "[red]✗[/red]"
        table.add_row(
            res.resource_type,
            str(res.valid_count),
            str(res.invalid_count),
            str(res.warning_count),
            status,
        )

    console.print(table)
    console.print()

    # Print errors and warnings per resource type
    for res in result.results:
        if res.errors:
            _output_resource_errors(res)
        if res.warnings:
            _output_resource_warnings(res)

    # Final summary panel
    if result.is_valid:
        if result.total_warnings > 0:
            console.print(
                Panel(
                    f"[green]✓ All resources passed validation[/green]\n"
                    f"[yellow]⚠ {result.total_warnings} warning(s)[/yellow]",
                    title="Validation Complete",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    "[green]✓ All resources passed validation[/green]",
                    title="Validation Complete",
                    border_style="green",
                )
            )
    else:
        console.print(
            Panel(
                f"[red]✗ Validation failed with {result.total_errors} error(s)[/red]",
                title="Validation Failed",
                border_style="red",
            )
        )


def _output_resource_errors(res: ResourceValidationResult) -> None:
    """Output errors for a single resource type."""
    console.print(f"\n[red]{res.resource_type} Errors:[/red]")
    for err in res.errors:
        tree = Tree(f"[red]✗[/red] {err.path}")
        error_node = tree.add(f"[red]{err.code}[/red]: {err.message}")
        if err.suggestion:
            error_node.add(f"[dim]💡 {err.suggestion}[/dim]")
        console.print(tree)


def _output_resource_warnings(res: ResourceValidationResult) -> None:
    """Output warnings for a single resource type."""
    console.print(f"\n[yellow]{res.resource_type} Warnings:[/yellow]")
    for warn in res.warnings:
        tree = Tree(f"[yellow]⚠[/yellow] {warn.path}")
        warning_node = tree.add(f"[yellow]{warn.code}[/yellow]: {warn.message}")
        if warn.suggestion:
            warning_node.add(f"[dim]💡 {warn.suggestion}[/dim]")
        console.print(tree)


def _output_all_json(result: AggregatedValidationResult) -> None:
    """Output aggregated validation results as JSON (AC5)."""
    data: dict[str, Any] = {
        "total_valid": sum(r.valid_count for r in result.results),
        "total_invalid": sum(r.invalid_count for r in result.results),
        "total_warnings": result.total_warnings,
        "is_valid": result.is_valid,
        "resources": [
            {
                "type": r.resource_type,
                "source_path": str(r.source_path) if r.source_path else None,
                "valid_count": r.valid_count,
                "invalid_count": r.invalid_count,
                "warning_count": r.warning_count,
                "is_valid": r.is_valid,
                "errors": [e.to_dict() for e in r.errors],
                "warnings": [w.to_dict() for w in r.warnings],
            }
            for r in result.results
        ],
    }

    response = JSONResponse(
        status="error" if not result.is_valid else "success",
        command="validate",
        data=data,
    )
    json_output(response.to_json())


# =============================================================================
# Work Units Subcommand (legacy + enhanced)
# =============================================================================


@validate_command.command("work-units")
@click.argument(
    "path",
    type=click.Path(exists=True, path_type=Path),
    required=False,
)
@click.option(
    "--content-quality",
    is_flag=True,
    help="Check content quality (weak verbs, quantification).",
)
@click.option(
    "--content-density",
    is_flag=True,
    help="Check content density (bullet length).",
)
@click.option(
    "--check-positions",
    is_flag=True,
    help="Validate position_id references exist in positions.yaml.",
)
@click.option(
    "--check-archetype",
    is_flag=True,
    help="Validate PAR structure matches archetype expectations.",
)
@click.pass_context
@handle_errors
def validate_work_units(
    ctx: click.Context,
    path: Path | None,
    content_quality: bool,
    content_density: bool,
    check_positions: bool,
    check_archetype: bool,
) -> None:
    """Validate Work Units against schema and content guidelines.

    PATH can be a single YAML file or a directory containing Work Units.
    Defaults to work-units/ directory if not specified.
    """
    _validate_work_units_impl(
        ctx, path, content_quality, content_density, check_positions, check_archetype
    )


def _validate_work_units_impl(
    ctx: click.Context,
    path: Path | None,
    content_quality: bool,
    content_density: bool,
    check_positions: bool,
    check_archetype: bool,
) -> None:
    """Implementation for work unit validation."""
    from resume_as_code.services.validator import validate_path

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
                json_output(response.to_json())
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
            json_output(response.to_json())
        else:
            info("No YAML files found to validate.")
        return

    # Load position IDs for validation if requested
    valid_position_ids: set[str] | None = None
    if check_positions:
        valid_position_ids = _load_position_ids()

    # Collect content warnings for valid files
    all_warnings: list[ContentWarning] = []
    position_errors: list[ContentWarning] = []
    archetype_warnings: list[ContentWarning] = []
    if content_quality or content_density or check_positions or check_archetype:
        for result in summary.results:
            if result.valid:
                data = _load_yaml(result.file_path)
                if data is not None:
                    if content_quality:
                        all_warnings.extend(validate_content_quality(data, str(result.file_path)))
                    if content_density:
                        all_warnings.extend(validate_content_density(data, str(result.file_path)))
                    if check_positions:
                        position_warnings = validate_position_reference(
                            data, str(result.file_path), valid_position_ids
                        )
                        # Separate errors from warnings
                        for pw in position_warnings:
                            if pw.severity == "error":
                                position_errors.append(pw)
                            else:
                                all_warnings.append(pw)
                    if check_archetype:
                        archetype_warnings.extend(_validate_archetype(data, str(result.file_path)))

    # Output results and handle exit code
    if ctx.obj.json_output:
        _output_work_units_json(summary, all_warnings, position_errors, archetype_warnings)
    else:
        _output_work_units_rich(summary)
        if position_errors:
            _output_position_errors_rich(position_errors)
        if archetype_warnings:
            _output_archetype_warnings_rich(archetype_warnings)
        if all_warnings:
            _output_warnings_rich(all_warnings)

    # Exit with appropriate code
    if summary.invalid_count > 0 or position_errors:
        sys.exit(ValidationError.exit_code)


# =============================================================================
# Individual Resource Subcommands (AC3)
# =============================================================================


@validate_command.command("positions")
@click.pass_context
@handle_errors
def validate_positions(ctx: click.Context) -> None:
    """Validate positions.yaml against schema."""
    _validate_single_resource(ctx, "positions")


@validate_command.command("certifications")
@click.pass_context
@handle_errors
def validate_certifications(ctx: click.Context) -> None:
    """Validate certifications against schema.

    Also checks cross-field rules like date <= expires.
    """
    _validate_single_resource(ctx, "certifications")


@validate_command.command("education")
@click.pass_context
@handle_errors
def validate_education(ctx: click.Context) -> None:
    """Validate education entries against schema."""
    _validate_single_resource(ctx, "education")


@validate_command.command("publications")
@click.pass_context
@handle_errors
def validate_publications(ctx: click.Context) -> None:
    """Validate publications against schema."""
    _validate_single_resource(ctx, "publications")


@validate_command.command("board-roles")
@click.pass_context
@handle_errors
def validate_board_roles(ctx: click.Context) -> None:
    """Validate board roles against schema.

    Also checks cross-field rules like start_date <= end_date.
    """
    _validate_single_resource(ctx, "board_roles")


@validate_command.command("highlights")
@click.pass_context
@handle_errors
def validate_highlights(ctx: click.Context) -> None:
    """Validate career highlights."""
    _validate_single_resource(ctx, "highlights")


@validate_command.command("config")
@click.pass_context
@handle_errors
def validate_config(ctx: click.Context) -> None:
    """Validate .resume.yaml configuration file.

    Checks schema version format and path references.
    """
    _validate_single_resource(ctx, "config")


def _validate_single_resource(ctx: click.Context, resource_key: str) -> None:
    """Validate a single resource type."""
    orchestrator = ValidationOrchestrator()
    result = orchestrator.validate_single(Path.cwd(), resource_key)

    if result is None:
        info(f"Unknown resource type: {resource_key}")
        sys.exit(1)

    if ctx.obj.json_output:
        _output_single_json(result)
    else:
        _output_single_rich(result)

    # Exit with appropriate code (AC6)
    if not result.is_valid:
        sys.exit(ValidationError.exit_code)


def _output_single_rich(result: ResourceValidationResult) -> None:
    """Output single resource validation with Rich formatting."""
    # Show source path if available
    if result.source_path:
        console.print(f"[dim]Source: {result.source_path}[/dim]\n")

    if result.valid_count == 0 and result.invalid_count == 0:
        info(f"No {result.resource_type.lower()} found to validate.")
        return

    # Show counts
    console.print(
        f"Valid: [green]{result.valid_count}[/green]  "
        f"Invalid: [red]{result.invalid_count}[/red]  "
        f"Warnings: [yellow]{result.warning_count}[/yellow]"
    )
    console.print()

    # Show errors
    if result.errors:
        _output_resource_errors(result)

    # Show warnings
    if result.warnings:
        _output_resource_warnings(result)

    # Summary panel
    console.print()
    if result.is_valid:
        if result.warning_count > 0:
            console.print(
                Panel(
                    f"[green]✓ {result.resource_type} passed validation[/green]\n"
                    f"[yellow]⚠ {result.warning_count} warning(s)[/yellow]",
                    title="Validation Complete",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    f"[green]✓ {result.resource_type} passed validation[/green]",
                    title="Validation Complete",
                    border_style="green",
                )
            )
    else:
        console.print(
            Panel(
                f"[red]✗ {result.resource_type} validation failed with "
                f"{result.invalid_count} error(s)[/red]",
                title="Validation Failed",
                border_style="red",
            )
        )


def _output_single_json(result: ResourceValidationResult) -> None:
    """Output single resource validation as JSON."""
    data: dict[str, Any] = {
        "resource_type": result.resource_type,
        "source_path": str(result.source_path) if result.source_path else None,
        "valid_count": result.valid_count,
        "invalid_count": result.invalid_count,
        "warning_count": result.warning_count,
        "is_valid": result.is_valid,
        "errors": [e.to_dict() for e in result.errors],
        "warnings": [w.to_dict() for w in result.warnings],
    }

    response = JSONResponse(
        status="error" if not result.is_valid else "success",
        command="validate",
        data=data,
    )
    json_output(response.to_json())


# =============================================================================
# Helper Functions
# =============================================================================


def _load_yaml(file_path: Path) -> dict[str, Any] | None:
    """Load YAML file and return data, or None on error."""
    yaml = YAML()
    yaml.preserve_quotes = True
    try:
        with file_path.open() as f:
            data: Any = yaml.load(f)
            if isinstance(data, dict):
                return data
            return None
    except Exception:
        return None


def _output_work_units_json(
    summary: Any,
    warnings: list[ContentWarning] | None = None,
    position_errors: list[ContentWarning] | None = None,
    archetype_warnings: list[ContentWarning] | None = None,
) -> None:
    """Output work unit validation results as JSON."""
    # Count position errors as validation failures
    position_error_count = len(position_errors) if position_errors else 0

    data: dict[str, Any] = {
        "valid_count": summary.valid_count,
        "invalid_count": summary.invalid_count + position_error_count,
        "files": [
            {
                "path": str(r.file_path),
                "valid": r.valid,
                "errors": [e.to_dict() for e in r.errors],
            }
            for r in summary.results
        ],
    }
    if warnings:
        data["content_warnings"] = [
            {
                "code": w.code,
                "message": w.message,
                "path": w.path,
                "suggestion": w.suggestion,
                "severity": w.severity,
            }
            for w in warnings
        ]
    if position_errors:
        data["position_errors"] = [
            {
                "code": e.code,
                "message": e.message,
                "path": e.path,
                "suggestion": e.suggestion,
            }
            for e in position_errors
        ]
    if archetype_warnings:
        data["archetype_warnings"] = [
            {
                "code": w.code,
                "message": w.message,
                "path": w.path,
                "suggestion": w.suggestion,
                "severity": w.severity,
            }
            for w in archetype_warnings
        ]
    has_errors = summary.invalid_count > 0 or position_error_count > 0
    response = JSONResponse(
        status="error" if has_errors else "success",
        command="validate",
        data=data,
    )
    json_output(response.to_json())


def _output_work_units_rich(summary: Any) -> None:
    """Output work unit validation results with Rich formatting."""
    for result in summary.results:
        if result.valid:
            console.print(f"[green]✓[/green] {result.file_path}")
        else:
            # Create error tree for this file with clickable path
            file_link = f"[link=file://{result.file_path.absolute()}]{result.file_path}[/link]"
            tree = Tree(f"[red]✗[/red] {file_link}")

            for err in result.errors:
                # Add error node with code and message
                error_node = tree.add(f"[red]{err.code}[/red]: {err.message}")
                if err.suggestion:
                    error_node.add(f"[dim]💡 {err.suggestion}[/dim]")

            console.print(tree)

    # Summary panel
    console.print()
    if summary.invalid_count == 0:
        console.print(
            Panel(
                f"[green]✓ All {summary.valid_count} Work Unit(s) passed validation[/green]",
                title="Validation Complete",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[red]✗ {summary.invalid_count} of {summary.total_count} Work Unit(s) "
                f"failed validation[/red]",
                title="Validation Failed",
                border_style="red",
            )
        )


def _output_warnings_rich(warnings: list[ContentWarning]) -> None:
    """Output content warnings with Rich formatting."""
    console.print()
    console.print("[yellow]Content Suggestions[/yellow]")
    console.print()

    # Group warnings by file
    warnings_by_file: dict[str, list[ContentWarning]] = {}
    for w in warnings:
        # Extract file path (before the colon if present)
        file_path = w.path.split(":")[0]
        if file_path not in warnings_by_file:
            warnings_by_file[file_path] = []
        warnings_by_file[file_path].append(w)

    for file_path, file_warnings in warnings_by_file.items():
        tree = Tree(f"[yellow]⚠[/yellow] {file_path}")
        for w in file_warnings:
            # Color based on severity
            color = "yellow" if w.severity == "warning" else "blue"
            warning_node = tree.add(f"[{color}]{w.code}[/{color}]: {w.message}")
            warning_node.add(f"[dim]💡 {w.suggestion}[/dim]")
        console.print(tree)


def _output_position_errors_rich(errors: list[ContentWarning]) -> None:
    """Output position reference errors with Rich formatting."""
    console.print()
    console.print("[red]Position Reference Errors[/red]")
    console.print()

    # Group errors by file
    errors_by_file: dict[str, list[ContentWarning]] = {}
    for e in errors:
        # Extract file path (before the colon if present)
        file_path = e.path.split(":")[0]
        if file_path not in errors_by_file:
            errors_by_file[file_path] = []
        errors_by_file[file_path].append(e)

    for file_path, file_errors in errors_by_file.items():
        tree = Tree(f"[red]✗[/red] {file_path}")
        for e in file_errors:
            error_node = tree.add(f"[red]{e.code}[/red]: {e.message}")
            error_node.add(f"[dim]💡 {e.suggestion}[/dim]")
        console.print(tree)


def _load_position_ids() -> set[str]:
    """Load valid position IDs from positions.yaml.

    Uses positions_path from configuration.

    Returns:
        Set of valid position IDs, empty set if file doesn't exist or is invalid.
    """
    from resume_as_code.services.position_service import PositionService

    config = get_config()
    positions_path = config.positions_path

    if not positions_path.exists():
        return set()

    try:
        service = PositionService(positions_path)
        positions = service.load_positions()
        return set(positions.keys())
    except Exception as e:
        # Log warning about malformed positions.yaml
        console.print(f"[yellow]⚠ Warning: Could not load positions.yaml: {e}[/yellow]")
        return set()


def _validate_archetype(work_unit: dict[str, Any], file_path: str) -> list[ContentWarning]:
    """Validate work unit PAR structure against archetype expectations.

    Args:
        work_unit: Work unit data dictionary.
        file_path: Path to the work unit file.

    Returns:
        List of ContentWarning objects for archetype misalignment (warnings only).
    """
    from resume_as_code.services.archetype_validation_service import (
        validate_archetype_alignment,
    )

    warnings: list[ContentWarning] = []

    result = validate_archetype_alignment(work_unit)

    # Convert archetype validation result to ContentWarning format
    # Warnings and suggestions are paired by index (problem, action, outcome order)
    for i, warning in enumerate(result.warnings):
        # Use corresponding suggestion if available, otherwise use empty string
        suggestion = result.suggestions[i] if i < len(result.suggestions) else ""
        warnings.append(
            ContentWarning(
                code="ARCHETYPE_MISALIGNMENT",
                message=warning,
                path=file_path,
                suggestion=suggestion,
                severity="warning",
            )
        )

    return warnings


def _output_archetype_warnings_rich(warnings: list[ContentWarning]) -> None:
    """Output archetype alignment warnings with Rich formatting."""
    console.print()
    console.print("[yellow]Archetype Alignment Suggestions[/yellow]")
    console.print()

    # Group warnings by file
    warnings_by_file: dict[str, list[ContentWarning]] = {}
    for w in warnings:
        file_path = w.path.split(":")[0]
        if file_path not in warnings_by_file:
            warnings_by_file[file_path] = []
        warnings_by_file[file_path].append(w)

    for file_path, file_warnings in warnings_by_file.items():
        tree = Tree(f"[yellow]⚠[/yellow] {file_path}")
        for w in file_warnings:
            warning_node = tree.add(f"[yellow]{w.code}[/yellow]: {w.message}")
            if w.suggestion:
                warning_node.add(f"[dim]💡 {w.suggestion}[/dim]")
        console.print(tree)
