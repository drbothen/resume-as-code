"""Cache management commands."""

from __future__ import annotations

from pathlib import Path

import click

from resume_as_code.models.output import JSONResponse
from resume_as_code.utils.console import console, info, json_output, success
from resume_as_code.utils.errors import handle_errors


@click.group("cache")
def cache_group() -> None:
    """Manage embedding cache."""


@cache_group.command("clear")
@click.option(
    "--all",
    "clear_all",
    is_flag=True,
    help="Clear all entries (not just stale ones)",
)
@click.pass_context
@handle_errors
def cache_clear(ctx: click.Context, clear_all: bool) -> None:
    """Clear stale embedding cache entries.

    By default, only clears entries from outdated model versions.
    Use --all to clear everything.
    """
    cache_dir = Path(".resume-cache")

    if not cache_dir.exists():
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="cache clear",
                data={"cleared": 0, "message": "No cache directory found"},
            )
            json_output(response.to_json())
        elif not ctx.obj.quiet:
            info("No cache directory found. Nothing to clear.")
        return

    # Initialize service to get model hash
    from resume_as_code.services.embedder import EmbeddingService

    service = EmbeddingService(cache_dir=cache_dir)

    if clear_all:
        cleared = service.cache.clear_all()
        message = f"Cleared all {cleared} cache entries"
    else:
        cleared = service.cache.clear_stale()
        message = f"Cleared {cleared} stale cache entries"

    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="cache clear",
            data={"cleared": cleared},
        )
        json_output(response.to_json())
    elif not ctx.obj.quiet:
        success(message)


@cache_group.command("stats")
@click.pass_context
@handle_errors
def cache_stats(ctx: click.Context) -> None:
    """Show embedding cache statistics."""
    cache_dir = Path(".resume-cache")

    if not cache_dir.exists():
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="cache stats",
                data={"exists": False},
            )
            json_output(response.to_json())
        elif not ctx.obj.quiet:
            info("No cache directory found.")
        return

    from resume_as_code.services.embedder import EmbeddingService

    service = EmbeddingService(cache_dir=cache_dir)
    stats = service.cache.stats()

    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="cache stats",
            data=stats,
        )
        json_output(response.to_json())
    elif not ctx.obj.quiet:
        console.print("[bold]Cache Statistics[/bold]")
        console.print(f"  Total entries: {stats['total_entries']}")
        console.print(f"  Current model: {stats['current_model_entries']}")
        console.print(f"  Stale entries: {stats['stale_entries']}")
        console.print(f"  Model hash: {stats['model_hash']}")
