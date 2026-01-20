"""Click CLI application for Resume as Code."""

from __future__ import annotations

from pathlib import Path

import click

from resume_as_code import __version__

# Import Context and pass_context from context module for backwards compatibility
from resume_as_code.context import Context, pass_context
from resume_as_code.utils.console import configure_output, err_console
from resume_as_code.utils.errors import handle_errors

# Re-export for backwards compatibility
__all__ = ["Context", "main", "pass_context"]


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="resume")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to config file (overrides .resume.yaml). "
    "Example: --config ~/.resume-profiles/executive.yaml",
)
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.option("-v", "--verbose", is_flag=True, help="Show verbose debug output")
@click.option("-q", "--quiet", is_flag=True, help="Suppress all output, exit code only")
@click.pass_context
@handle_errors
def main(
    ctx: click.Context,
    config_path: Path | None,
    json_output: bool,
    verbose: bool,
    quiet: bool,
) -> None:
    """Resume as Code - CLI tool for git-native resume generation.

    All commands are designed for non-interactive operation, suitable for
    CI/CD pipelines and AI agent automation. No interactive prompts are used;
    all required input must come from flags, environment variables, or config files.
    """
    ctx.ensure_object(Context)
    ctx.obj.config_path = config_path
    ctx.obj.json_output = json_output
    ctx.obj.verbose = verbose
    ctx.obj.quiet = quiet

    # Warn if conflicting flags are used (Issue #4)
    if json_output and quiet:
        err_console.print(
            "[yellow]⚠[/yellow] Both --json and --quiet specified; --quiet takes precedence"
        )

    # Configure output mode for console helpers (Issue #2, #3)
    configure_output(ctx.obj)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def _register_commands() -> None:
    """Register all CLI commands."""
    from resume_as_code.commands.build import build_command
    from resume_as_code.commands.cache import cache_group
    from resume_as_code.commands.config_cmd import config_command
    from resume_as_code.commands.infer import infer_archetypes_command
    from resume_as_code.commands.init import init_command
    from resume_as_code.commands.list_cmd import list_command
    from resume_as_code.commands.migrate import migrate_command
    from resume_as_code.commands.new import new_group
    from resume_as_code.commands.plan import plan_command
    from resume_as_code.commands.remove import remove_group
    from resume_as_code.commands.show import show_group
    from resume_as_code.commands.test_errors import test_errors
    from resume_as_code.commands.test_output import test_output
    from resume_as_code.commands.validate import validate_command

    main.add_command(build_command)
    main.add_command(cache_group)
    main.add_command(config_command)
    main.add_command(infer_archetypes_command)
    main.add_command(init_command)
    main.add_command(list_command)
    main.add_command(migrate_command)
    main.add_command(new_group)
    main.add_command(plan_command)
    main.add_command(remove_group)
    main.add_command(show_group)
    main.add_command(test_errors)
    main.add_command(test_output)
    main.add_command(validate_command)


_register_commands()


if __name__ == "__main__":
    main()
