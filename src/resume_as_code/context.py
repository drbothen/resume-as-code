"""Click context object for Resume as Code CLI.

This module provides the Context class and pass_context decorator used by
commands. It's separated from cli.py to avoid circular imports when commands
import these objects.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from resume_as_code.models.config import ResumeConfig


class Context:
    """Click context object for storing global options and configuration.

    Attributes:
        json_output: Whether to output JSON format.
        verbose: Whether to show verbose debug output.
        quiet: Whether to suppress all output.
        config_path: Custom config file path (overrides default .resume.yaml).
    """

    def __init__(self) -> None:
        self.json_output: bool = False
        self.verbose: bool = False
        self.quiet: bool = False
        self.config_path: Path | None = None  # Custom config file path
        self._config: ResumeConfig | None = None

    @property
    def config(self) -> ResumeConfig:
        """Get the effective configuration, loading it lazily if needed."""
        if self._config is None:
            # Import inline to avoid circular import: context.py <- cli.py <- config.py
            # This module is imported by cli.py which is imported by config commands,
            # so config.py cannot be imported at module level here.
            from resume_as_code.config import get_config

            self._config = get_config(project_config_path=self.config_path)
        return self._config

    @property
    def effective_config_path(self) -> Path:
        """Get the effective config path (custom or default).

        Returns resolved (normalized) path to prevent path traversal issues.
        """
        return (self.config_path or Path.cwd() / ".resume.yaml").resolve()

    def set_config(self, config: ResumeConfig) -> None:
        """Set the configuration (used for testing or CLI overrides)."""
        self._config = config


pass_context = click.make_pass_decorator(Context, ensure=True)
