"""Test output command for verifying CLI output formatting."""

from __future__ import annotations

from pathlib import Path

import click

from resume_as_code.context import Context, pass_context
from resume_as_code.models.output import JSONResponse
from resume_as_code.utils.console import (
    OutputMode,
    error,
    get_output_mode,
    info,
    success,
    verbose,
    verbose_path,
    warning,
)


@click.command("test-output")
@pass_context
def test_output(ctx: Context) -> None:
    """Test command to verify output formatting."""
    mode = get_output_mode(ctx)

    if mode == OutputMode.JSON:
        # In JSON mode, output structured JSON only
        response = JSONResponse(
            status="success",
            command="test-output",
            data={
                "message": "Output formatting test completed",
                "modes_tested": ["rich", "json", "quiet"],
            },
        )
        print(response.to_json())
        return

    # Rich mode (and quiet mode - helpers auto-suppress in quiet mode)
    # Demonstrate all message types
    success("Success message test")
    info("Info message test")
    warning("Warning message test")
    error("Error message test")

    # Demonstrate verbose mode with file path logging (AC #3)
    verbose("Verbose debug message")
    verbose_path(Path("/example/config.yaml"), action="Reading")
    verbose_path("/example/output.pdf", action="Writing")

    success("Output formatting test completed")
