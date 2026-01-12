"""Configuration command for Resume as Code."""

from __future__ import annotations

from pathlib import Path

import click
from rich.table import Table
from ruamel.yaml import YAML

from resume_as_code.config import get_config, get_config_sources, reset_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.utils.console import console

# Project config filename
PROJECT_CONFIG_NAME = ".resume.yaml"


@click.command("config")
@click.argument("key", required=False)
@click.argument("value", required=False)
@click.option(
    "--list",
    "-l",
    "list_all",
    is_flag=True,
    help="List all configuration values with sources",
)
@click.pass_context
def config_command(
    ctx: click.Context,
    key: str | None,
    value: str | None,
    list_all: bool,
) -> None:
    """View or set configuration values.

    \b
    Examples:
      resume config                      # Show current configuration
      resume config --list               # List all config values with sources
      resume config output_dir           # Get a specific value
      resume config output_dir ./resumes # Set a value in project config
    """
    # Reset config to ensure fresh load with current environment
    reset_config()

    # Handle set operation (AC: #4)
    if key and value:
        _set_config_value(ctx, key, value)
        return

    # Handle get single value
    if key and not value:
        _get_config_value(ctx, key)
        return

    # Handle list/show all (AC: #5)
    _show_all_config(ctx, list_all)


def _set_config_value(ctx: click.Context, key: str, value: str) -> None:
    """Set a config value in project config file (AC: #4)."""
    project_path = Path.cwd() / PROJECT_CONFIG_NAME

    yaml = YAML()
    yaml.preserve_quotes = True

    # Load existing config or start fresh
    if project_path.exists():
        with open(project_path) as f:
            data = yaml.load(f) or {}
    else:
        data = {}

    # Convert value to appropriate type
    converted_value = _convert_value(value)

    # Handle nested keys (e.g., "scoring_weights.title_weight")
    keys = key.split(".")
    target = data
    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        target = target[k]
    target[keys[-1]] = converted_value

    # Write back
    with open(project_path, "w") as f:
        yaml.dump(data, f)

    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="config",
            data={"key": key, "value": converted_value, "action": "set"},
        )
        click.echo(response.to_json())
        return

    if ctx.obj.quiet:
        return

    console.print(f"[green]✓[/green] Set {key} = {converted_value}")


def _get_config_value(ctx: click.Context, key: str) -> None:
    """Get a single config value."""
    config = get_config()
    sources = get_config_sources()

    config_dict = config.model_dump()

    # Handle nested keys
    keys = key.split(".")
    value = config_dict
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            if ctx.obj.json_output:
                response = JSONResponse(
                    status="error",
                    command="config",
                    errors=[{"code": "CONFIG_KEY_NOT_FOUND", "message": f"Unknown key: {key}"}],
                )
                click.echo(response.to_json())
                return
            if not ctx.obj.quiet:
                console.print(f"[yellow]Unknown config key:[/yellow] {key}")
                console.print("[dim]Use --list to see available keys[/dim]")
            return

    source = sources.get(keys[0])
    source_str = source.source if source else "default"

    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="config",
            data={"key": key, "value": value, "source": source_str},
        )
        click.echo(response.to_json())
        return

    if ctx.obj.quiet:
        return

    console.print(f"{key} = {value}")
    console.print(f"[dim]Source: {source_str}[/dim]")


def _show_all_config(ctx: click.Context, _list_all: bool) -> None:
    """Show all configuration values with sources (AC: #5)."""
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


def _convert_value(value: str) -> str | int | float | bool:
    """Convert string value to appropriate type."""
    # Try integer
    try:
        return int(value)
    except ValueError:
        pass

    # Try float
    try:
        return float(value)
    except ValueError:
        pass

    # Boolean
    if value.lower() in ("true", "yes"):
        return True
    if value.lower() in ("false", "no"):
        return False

    # String
    return value
