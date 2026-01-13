"""Validate command for Work Unit schema validation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import click
from rich.panel import Panel
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
from resume_as_code.services.validator import ValidationSummary, validate_path
from resume_as_code.utils.console import console, info, json_output
from resume_as_code.utils.errors import handle_errors


@click.command("validate")
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
@click.pass_context
@handle_errors
def validate_command(
    ctx: click.Context,
    path: Path | None,
    content_quality: bool,
    content_density: bool,
    check_positions: bool,
) -> None:
    """Validate Work Units against schema and content guidelines.

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
    if content_quality or content_density or check_positions:
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

    # Output results and handle exit code
    if ctx.obj.json_output:
        _output_json(summary, all_warnings, position_errors)
    else:
        _output_rich(summary)
        if position_errors:
            _output_position_errors_rich(position_errors)
        if all_warnings:
            _output_warnings_rich(all_warnings)

    # Exit with appropriate code (avoid raising exception to prevent duplicate output)
    # Position errors are validation failures (AC #3: invalid position_id is an error)
    if summary.invalid_count > 0 or position_errors:
        sys.exit(ValidationError.exit_code)


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


def _output_json(
    summary: ValidationSummary,
    warnings: list[ContentWarning] | None = None,
    position_errors: list[ContentWarning] | None = None,
) -> None:
    """Output validation results as JSON."""
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
    has_errors = summary.invalid_count > 0 or position_error_count > 0
    response = JSONResponse(
        status="error" if has_errors else "success",
        command="validate",
        data=data,
    )
    json_output(response.to_json())


def _output_rich(summary: ValidationSummary) -> None:
    """Output validation results with Rich formatting."""
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
        console.print(
            f"[yellow]⚠ Warning: Could not load positions.yaml: {e}[/yellow]"
        )
        return set()
