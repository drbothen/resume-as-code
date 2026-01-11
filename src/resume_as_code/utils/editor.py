"""Editor integration utilities."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from resume_as_code.models.config import ResumeConfig


def get_editor(config: ResumeConfig | None = None) -> str | None:
    """Get the configured editor.

    Priority:
    1. Config file setting
    2. $VISUAL environment variable
    3. $EDITOR environment variable
    4. None (no editor available)
    """
    # Check config
    if config and config.editor:
        return config.editor

    # Check environment
    return os.environ.get("VISUAL") or os.environ.get("EDITOR")


def open_in_editor(path: Path, editor: str) -> None:
    """Open a file in the specified editor.

    Args:
        path: Path to file to open
        editor: Editor command (e.g., "code", "vim", "nano")
    """
    # Handle editors that need special flags
    # timeout=None explicitly documents that we wait indefinitely for editor
    if editor in ("code", "code-insiders"):
        # VS Code: use --wait to block until closed
        subprocess.run([editor, "--wait", str(path)], check=False, timeout=None)
    elif editor in ("subl", "sublime"):
        # Sublime: use --wait
        subprocess.run([editor, "--wait", str(path)], check=False, timeout=None)
    else:
        # Default: just open the file
        subprocess.run([editor, str(path)], check=False, timeout=None)
