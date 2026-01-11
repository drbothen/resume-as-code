"""Configuration command for Resume as Code."""

from __future__ import annotations

import click
from rich.table import Table

from resume_as_code.config import get_config, get_config_sources, reset_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.utils.console import console


@click.command("config")
@click.pass_context
def config_command(ctx: click.Context) -> None:
    """Display current effective configuration with sources."""
    # Reset config to ensure fresh load with current environment
    reset_config()

    config = get_config()
    sources = get_config_sources()

    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="config",
            data={
                "config": config.model_dump(mode="json"),
                "sources": {k: v.model_dump() for k, v in sources.items()},
            },
        )
        click.echo(response.to_json())
        return

    if ctx.obj.quiet:
        return

    # Rich table output
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Source", style="yellow")

    config_dict = config.model_dump()
    for key, value in config_dict.items():
        source = sources.get(key)
        source_str: str = source.source if source else "unknown"
        if source and source.path:
            source_str = f"{source.source} ({source.path})"
        table.add_row(key, str(value), source_str)

    console.print(table)
