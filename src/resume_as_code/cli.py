"""Click CLI application for Resume as Code."""

from __future__ import annotations

import click

from resume_as_code import __version__


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="resume")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Resume as Code - CLI tool for git-native resume generation."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


if __name__ == "__main__":
    main()
