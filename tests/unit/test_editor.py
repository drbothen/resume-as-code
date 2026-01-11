"""Tests for editor utility."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from resume_as_code.models.config import ResumeConfig
from resume_as_code.utils.editor import get_editor, open_in_editor


class TestGetEditor:
    """Tests for get_editor function."""

    def test_returns_config_editor_when_set(self) -> None:
        """Should return editor from config when set."""
        config = MagicMock(spec=ResumeConfig)
        config.editor = "vim"

        result = get_editor(config)

        assert result == "vim"

    def test_returns_visual_when_config_editor_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return $VISUAL when config.editor is None."""
        monkeypatch.setenv("VISUAL", "code")
        monkeypatch.setenv("EDITOR", "vim")
        config = MagicMock(spec=ResumeConfig)
        config.editor = None

        result = get_editor(config)

        assert result == "code"

    def test_returns_editor_when_visual_not_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return $EDITOR when $VISUAL is not set."""
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.setenv("EDITOR", "nano")
        config = MagicMock(spec=ResumeConfig)
        config.editor = None

        result = get_editor(config)

        assert result == "nano"

    def test_returns_none_when_no_editor_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return None when no editor is configured."""
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.delenv("EDITOR", raising=False)
        config = MagicMock(spec=ResumeConfig)
        config.editor = None

        result = get_editor(config)

        assert result is None

    def test_returns_none_when_config_is_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should check environment when config is None."""
        monkeypatch.setenv("EDITOR", "emacs")
        monkeypatch.delenv("VISUAL", raising=False)

        result = get_editor(None)

        assert result == "emacs"

    def test_visual_takes_priority_over_editor(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """$VISUAL should take priority over $EDITOR."""
        monkeypatch.setenv("VISUAL", "code")
        monkeypatch.setenv("EDITOR", "vim")

        result = get_editor(None)

        assert result == "code"


class TestOpenInEditor:
    """Tests for open_in_editor function."""

    @patch("resume_as_code.utils.editor.subprocess.run")
    def test_vscode_uses_wait_flag(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """VS Code should be called with --wait flag."""
        test_file = tmp_path / "test.yaml"
        test_file.touch()

        open_in_editor(test_file, "code")

        mock_run.assert_called_once_with(
            ["code", "--wait", str(test_file)], check=False, timeout=None
        )

    @patch("resume_as_code.utils.editor.subprocess.run")
    def test_vscode_insiders_uses_wait_flag(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """VS Code Insiders should be called with --wait flag."""
        test_file = tmp_path / "test.yaml"
        test_file.touch()

        open_in_editor(test_file, "code-insiders")

        mock_run.assert_called_once_with(
            ["code-insiders", "--wait", str(test_file)], check=False, timeout=None
        )

    @patch("resume_as_code.utils.editor.subprocess.run")
    def test_sublime_uses_wait_flag(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Sublime Text should be called with --wait flag."""
        test_file = tmp_path / "test.yaml"
        test_file.touch()

        open_in_editor(test_file, "subl")

        mock_run.assert_called_once_with(
            ["subl", "--wait", str(test_file)], check=False, timeout=None
        )

    @patch("resume_as_code.utils.editor.subprocess.run")
    def test_sublime_full_name_uses_wait_flag(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Sublime (full name) should be called with --wait flag."""
        test_file = tmp_path / "test.yaml"
        test_file.touch()

        open_in_editor(test_file, "sublime")

        mock_run.assert_called_once_with(
            ["sublime", "--wait", str(test_file)], check=False, timeout=None
        )

    @patch("resume_as_code.utils.editor.subprocess.run")
    def test_default_editor_no_extra_flags(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Default editors should be called without extra flags."""
        test_file = tmp_path / "test.yaml"
        test_file.touch()

        open_in_editor(test_file, "vim")

        mock_run.assert_called_once_with(["vim", str(test_file)], check=False, timeout=None)

    @patch("resume_as_code.utils.editor.subprocess.run")
    def test_nano_no_extra_flags(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Nano should be called without extra flags."""
        test_file = tmp_path / "test.yaml"
        test_file.touch()

        open_in_editor(test_file, "nano")

        mock_run.assert_called_once_with(["nano", str(test_file)], check=False, timeout=None)
