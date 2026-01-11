"""CLI commands for Resume as Code.

Commands are registered dynamically in cli.py via _register_commands().
This module provides exports for direct import if needed.
"""

from resume_as_code.commands.test_output import test_output

__all__ = [
    "test_output",
]
