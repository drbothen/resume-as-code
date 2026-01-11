"""Click CLI application for Resume as Code."""

from __future__ import annotations

import click

from resume_as_code import __version__
from resume_as_code.utils.console import configure_output, err_console


class Context:
    """Click context object for storing global options."""

    def __init__(self) -> None:
        self.json_output: bool = False
        self.verbose: bool = False
        self.quiet: bool = False


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="resume")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.option("-v", "--verbose", is_flag=True, help="Show verbose debug output")
@click.option("-q", "--quiet", is_flag=True, help="Suppress all output, exit code only")
@click.pass_context
def main(ctx: click.Context, json_output: bool, verbose: bool, quiet: bool) -> None:
    """Resume as Code - CLI tool for git-native resume generation."""
    ctx.ensure_object(Context)
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
    from resume_as_code.commands.test_output import test_output

    main.add_command(test_output)


_register_commands()


if __name__ == "__main__":
    main()
