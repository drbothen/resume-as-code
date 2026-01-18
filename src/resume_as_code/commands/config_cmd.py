"""Configuration command for Resume as Code."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich.table import Table
from ruamel.yaml import YAML

from resume_as_code.config import get_config, get_config_sources, reset_config
from resume_as_code.data_loader import load_certifications
from resume_as_code.models.output import JSONResponse
from resume_as_code.utils.console import console

if TYPE_CHECKING:
    from resume_as_code.models.config import ResumeConfig

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
@click.option(
    "--show-onet-status",
    is_flag=True,
    help="Show O*NET API integration status (credentials, cache stats)",
)
@click.pass_context
def config_command(
    ctx: click.Context,
    key: str | None,
    value: str | None,
    list_all: bool,
    show_onet_status: bool,
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

    # Handle O*NET status (Story 7.5, AC #6)
    if show_onet_status:
        _show_onet_status(ctx)
        return

    # Handle set operation (AC: #4)
    if key and value:
        _set_config_value(ctx, key, value)
        return

    # Handle get single value
    if key and not value:
        _get_config_value(ctx, key, list_flag=list_all)
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


def _get_config_value(ctx: click.Context, key: str, list_flag: bool = False) -> None:
    """Get a single config value."""
    config = get_config(project_config_path=ctx.obj.config_path)
    sources = get_config_sources()

    # Special handling for certifications with --list flag (Story 6.2, AC #6)
    if key == "certifications" and list_flag:
        _show_certifications_table(ctx, config)
        return

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
    config = get_config(project_config_path=ctx.obj.config_path)
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


def _show_certifications_table(ctx: click.Context, config: ResumeConfig) -> None:
    """Display certifications in a table with status (Story 6.2, AC #6).

    Args:
        ctx: Click context with output options.
        config: ResumeConfig (unused, data loaded via data_loader).
    """
    # Load certifications via data_loader (Story 9.2)
    certifications = load_certifications(Path.cwd())

    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="config",
            data={
                "certifications": [
                    {
                        "name": cert.name,
                        "issuer": cert.issuer,
                        "date": cert.date,
                        "expires": cert.expires,
                        "status": cert.get_status(),
                        "display": cert.display,
                    }
                    for cert in certifications
                ]
            },
        )
        click.echo(response.to_json())
        return

    if ctx.obj.quiet:
        return

    if not certifications:
        console.print("[dim]No certifications configured.[/dim]")
        console.print(
            "[dim]Add certifications to .resume.yaml:[/dim]\n"
            "[dim]  certifications:[/dim]\n"
            "[dim]    - name: 'AWS Solutions Architect'[/dim]\n"
            "[dim]      issuer: 'Amazon Web Services'[/dim]"
        )
        return

    # Rich table output
    table = Table(title="Certifications")
    table.add_column("Name", style="cyan")
    table.add_column("Issuer", style="white")
    table.add_column("Date", style="white")
    table.add_column("Expires", style="white")
    table.add_column("Status", style="bold")

    for cert in certifications:
        status = cert.get_status()
        status_style = {
            "active": "[green]active[/green]",
            "expires_soon": "[yellow]expires_soon[/yellow]",
            "expired": "[red]expired[/red]",
        }.get(status, status)

        table.add_row(
            cert.name,
            cert.issuer or "",
            cert.date or "",
            cert.expires or "",
            status_style,
        )

    console.print(table)


def _mask_api_key(key: str) -> str:
    """Mask API key showing only first 4 and last 2 characters.

    Args:
        key: API key to mask.

    Returns:
        Masked key string.

    """
    if len(key) <= 6:
        return "***"
    return f"{key[:4]}***{key[-2:]}"


def _show_onet_status(ctx: click.Context) -> None:
    """Show O*NET API integration status (Story 7.5, AC #6).

    Displays:
    - Enabled/disabled state
    - API key configured (masked)
    - Cache statistics

    Args:
        ctx: Click context with output options.
    """
    from resume_as_code.models.config import ONetConfig
    from resume_as_code.services.onet_service import ONetService

    config = get_config(project_config_path=ctx.obj.config_path)

    # Get O*NET config (may be None if not configured)
    onet_config = config.onet or ONetConfig()

    # Determine status
    is_enabled = onet_config.enabled
    is_configured = onet_config.is_configured
    api_key = onet_config.api_key
    masked_key = _mask_api_key(api_key) if api_key else None

    # Get cache stats if configured
    cache_stats = {"entries": 0, "size_bytes": 0}
    if is_configured:
        try:
            service = ONetService(onet_config)
            cache_stats = service.get_cache_stats()
        except Exception:
            pass  # Gracefully handle any cache access errors

    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="config",
            data={
                "onet": {
                    "enabled": is_enabled,
                    "configured": is_configured,
                    "api_key_masked": masked_key,
                    "cache": cache_stats,
                    "settings": {
                        "cache_ttl": onet_config.cache_ttl,
                        "timeout": onet_config.timeout,
                        "retry_delay_ms": onet_config.retry_delay_ms,
                    },
                }
            },
        )
        click.echo(response.to_json())
        return

    if ctx.obj.quiet:
        return

    # Rich output
    table = Table(title="O*NET API Status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    # Enabled state
    if is_enabled:
        table.add_row("Status", "[green]Enabled[/green]")
    else:
        table.add_row("Status", "[yellow]Disabled[/yellow]")

    # API key
    if masked_key:
        table.add_row("API Key", f"[green]{masked_key}[/green] (configured)")
    else:
        table.add_row("API Key", "[red]Not configured[/red]")

    # Overall readiness
    if is_configured:
        table.add_row("Ready", "[green]Yes[/green]")
    else:
        table.add_row("Ready", "[yellow]No[/yellow] - set ONET_API_KEY env var")

    # Cache stats
    table.add_row("Cache Entries", str(cache_stats["entries"]))
    size_kb = cache_stats["size_bytes"] / 1024
    table.add_row("Cache Size", f"{size_kb:.1f} KB")

    # Settings
    table.add_row("Cache TTL", f"{onet_config.cache_ttl} seconds")
    table.add_row("Timeout", f"{onet_config.timeout} seconds")
    table.add_row("Retry Delay", f"{onet_config.retry_delay_ms} ms")

    console.print(table)

    # Help text if not configured
    if not is_configured:
        console.print()
        console.print("[dim]To enable O*NET integration:[/dim]")
        console.print("[dim]  1. Get an API key from https://services.onetcenter.org/[/dim]")
        console.print("[dim]  2. Set ONET_API_KEY environment variable[/dim]")
        console.print("[dim]  3. Optionally add to .resume.yaml:[/dim]")
        console.print("[dim]     onet:[/dim]")
        console.print("[dim]       enabled: true[/dim]")
