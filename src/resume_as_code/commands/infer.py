"""Infer archetypes for work units.

Story 12.6: Enhanced Archetype Inference with Semantic Embeddings

Provides CLI command for batch inference of work unit archetypes
using a hybrid weighted-regex + semantic embedding approach.
Dry-run by default; use --apply to update files.
"""

from __future__ import annotations

from pathlib import Path

import click
from ruamel.yaml import YAML

from resume_as_code.config import get_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.archetype_inference_service import (
    MIN_CONFIDENCE_THRESHOLD,
    infer_archetype,
)
from resume_as_code.services.embedder import EmbeddingService
from resume_as_code.utils.console import console, info, warning
from resume_as_code.utils.errors import handle_errors


@click.command("infer-archetypes")
@click.option(
    "--apply",
    is_flag=True,
    help="Apply inferred archetypes to work unit files (default: dry-run)",
)
@click.option(
    "--min-confidence",
    type=float,
    default=MIN_CONFIDENCE_THRESHOLD,
    show_default=True,
    help="Minimum confidence to suggest archetype",
)
@click.option(
    "--include-assigned",
    is_flag=True,
    help="Re-infer even for work units that already have archetypes",
)
@click.pass_context
@handle_errors
def infer_archetypes_command(
    ctx: click.Context,
    apply: bool,
    min_confidence: float,
    include_assigned: bool,
) -> None:
    """Infer archetypes for work units using hybrid regex + semantic analysis.

    Uses weighted regex patterns first (strong signals like "P1" score higher).
    Falls back to semantic embedding comparison when regex confidence is low.

    By default, shows suggestions without modifying files.
    Use --apply to update work unit files with inferred archetypes.

    Examples:

        # Preview inferred archetypes
        resume infer-archetypes

        # Apply with lower confidence threshold
        resume infer-archetypes --apply --min-confidence 0.3

        # Re-infer all work units (including those with archetypes)
        resume infer-archetypes --include-assigned

        # JSON output for programmatic use
        resume --json infer-archetypes
    """
    # Use config.work_units_dir for consistency with other commands
    # Note: We check existence before accessing to avoid auto-creation
    config = get_config()
    work_units_dir = Path(config.work_units_dir)

    if not work_units_dir.exists():
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="infer-archetypes",
                data={
                    "results": [],
                    "total": 0,
                    "applied": apply,
                    "min_confidence": min_confidence,
                    "message": "No work-units directory found",
                },
            )
            click.echo(response.to_json())
        elif not ctx.obj.quiet:
            warning("No work-units directory found")
        return

    yaml = YAML()
    yaml.preserve_quotes = True

    # Initialize embedding service (always needed for hybrid approach)
    embedding_service = EmbeddingService()

    results: list[dict[str, str | float | bool | None]] = []

    for yaml_file in sorted(work_units_dir.glob("*.yaml")):
        with yaml_file.open() as f:
            data = yaml.load(f)

        if not data:
            continue

        existing_archetype = data.get("archetype")

        # Skip if already has archetype (unless --include-assigned)
        if existing_archetype and not include_assigned:
            continue

        archetype, confidence, method = infer_archetype(data, embedding_service, min_confidence)

        result: dict[str, str | float | bool | None] = {
            "file": yaml_file.name,
            "id": data.get("id", "unknown"),
            "inferred": archetype.value,
            "confidence": round(confidence, 2),
            "existing": existing_archetype,
            "applied": False,
            "method": method,
        }
        results.append(result)

        if apply and confidence >= min_confidence:
            data["archetype"] = archetype.value
            with yaml_file.open("w") as f:
                yaml.dump(data, f)
            result["applied"] = True

    # Output results
    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="infer-archetypes",
            data={
                "results": results,
                "total": len(results),
                "applied": apply,
                "min_confidence": min_confidence,
            },
        )
        click.echo(response.to_json())
    elif not ctx.obj.quiet:
        if not results:
            info("No work units to analyze (all have archetypes assigned)")
            return

        console.print("\n[bold]Archetype Inference Results[/bold]\n")

        for r in results:
            status = "[green]APPLIED[/green]" if r.get("applied") else "[dim]suggested[/dim]"
            conf = float(r["confidence"]) if r["confidence"] is not None else 0.0
            if conf >= 0.7:
                conf_color = "green"
            elif conf >= 0.5:
                conf_color = "yellow"
            else:
                conf_color = "red"
            method_str = f"[dim]({r['method']})[/dim]"
            console.print(
                f"  {r['file']}: [{conf_color}]{r['inferred']}[/{conf_color}] "
                f"({conf:.0%}) {method_str} {status}"
            )

        console.print(f"\n[dim]Total: {len(results)} | Min confidence: {min_confidence}[/dim]")

        if not apply:
            console.print("\n[dim]Use --apply to update files[/dim]")
