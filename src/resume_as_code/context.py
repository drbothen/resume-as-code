"""Click context object for Resume as Code CLI.

This module provides the Context class and pass_context decorator used by
commands. It's separated from cli.py to avoid circular imports when commands
import these objects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from resume_as_code.models.config import ResumeConfig


class Context:
    """Click context object for storing global options and configuration."""

    def __init__(self) -> None:
        self.json_output: bool = False
        self.verbose: bool = False
        self.quiet: bool = False
        self._config: ResumeConfig | None = None

    @property
    def config(self) -> ResumeConfig:
        """Get the effective configuration, loading it lazily if needed."""
        if self._config is None:
            from resume_as_code.config import get_config

            self._config = get_config()
        return self._config

    def set_config(self, config: ResumeConfig) -> None:
        """Set the configuration (used for testing or CLI overrides)."""
        self._config = config


pass_context = click.make_pass_decorator(Context, ensure=True)
