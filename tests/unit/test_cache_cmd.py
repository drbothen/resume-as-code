"""Tests for cache command."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from click.testing import CliRunner

from resume_as_code.cli import main


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


class TestCacheClearCommand:
    """Tests for cache clear command."""

    def test_cache_clear_no_cache_dir(self, cli_runner: CliRunner) -> None:
        """Should handle missing cache directory gracefully."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(main, ["cache", "clear"])
            assert result.exit_code == 0
            assert "No cache directory found" in result.output

    @patch("sentence_transformers.SentenceTransformer")
    def test_cache_clear_clears_stale_entries(
        self, mock_st: MagicMock, cli_runner: CliRunner
    ) -> None:
        """Should clear stale entries and show count."""
        # Mock the model to avoid actual model loading
        mock_model = MagicMock()
        mock_state_dict = {
            "layer1.weight": MagicMock(
                cpu=MagicMock(
                    return_value=MagicMock(
                        numpy=MagicMock(return_value=np.zeros((10, 10), dtype=np.float32))
                    )
                )
            ),
        }
        mock_model._first_module.return_value.auto_model.state_dict.return_value = mock_state_dict
        mock_st.return_value = mock_model

        with cli_runner.isolated_filesystem():
            from resume_as_code.services.embedding_cache import EmbeddingCache

            # Create cache directory with the model-specific subdirectory
            cache_dir = Path(".resume-cache/intfloat_multilingual-e5-large-instruct")
            old_cache = EmbeddingCache(cache_dir, model_hash="old_hash")
            old_cache.put("old text", np.random.rand(384).astype(np.float32))

            result = cli_runner.invoke(main, ["cache", "clear"])

            assert result.exit_code == 0
            # Should clear the entry with old hash
            assert "1" in result.output or "Cleared" in result.output

    @patch("sentence_transformers.SentenceTransformer")
    def test_cache_clear_all_flag(self, mock_st: MagicMock, cli_runner: CliRunner) -> None:
        """Should clear all entries when --all flag is used."""
        # Mock the model
        mock_model = MagicMock()
        mock_state_dict = {
            "layer1.weight": MagicMock(
                cpu=MagicMock(
                    return_value=MagicMock(
                        numpy=MagicMock(return_value=np.zeros((10, 10), dtype=np.float32))
                    )
                )
            ),
        }
        mock_model._first_module.return_value.auto_model.state_dict.return_value = mock_state_dict
        mock_st.return_value = mock_model

        with cli_runner.isolated_filesystem():
            from resume_as_code.services.embedding_cache import EmbeddingCache

            cache_dir = Path(".resume-cache/intfloat_multilingual-e5-large-instruct")
            cache = EmbeddingCache(cache_dir, model_hash="test_hash")
            cache.put("text1", np.random.rand(384).astype(np.float32))
            cache.put("text2", np.random.rand(384).astype(np.float32))

            result = cli_runner.invoke(main, ["cache", "clear", "--all"])

            assert result.exit_code == 0
            assert "2" in result.output  # 2 entries cleared

    def test_cache_clear_json_output(self, cli_runner: CliRunner) -> None:
        """Should output JSON when --json flag is used."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(main, ["--json", "cache", "clear"])
            assert result.exit_code == 0

            data = json.loads(result.output)
            assert data["status"] == "success"
            assert data["command"] == "cache clear"
            assert "cleared" in data["data"]

    def test_cache_clear_quiet_mode(self, cli_runner: CliRunner) -> None:
        """Should produce no output in quiet mode."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(main, ["--quiet", "cache", "clear"])
            assert result.exit_code == 0
            assert result.output == ""


class TestCacheStatsCommand:
    """Tests for cache stats command."""

    def test_cache_stats_no_cache_dir(self, cli_runner: CliRunner) -> None:
        """Should handle missing cache directory gracefully."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(main, ["cache", "stats"])
            assert result.exit_code == 0
            assert "No cache directory found" in result.output

    @patch("sentence_transformers.SentenceTransformer")
    def test_cache_stats_shows_statistics(self, mock_st: MagicMock, cli_runner: CliRunner) -> None:
        """Should show cache statistics."""
        # Mock the model
        mock_model = MagicMock()
        mock_state_dict = {
            "layer1.weight": MagicMock(
                cpu=MagicMock(
                    return_value=MagicMock(
                        numpy=MagicMock(return_value=np.zeros((10, 10), dtype=np.float32))
                    )
                )
            ),
        }
        mock_model._first_module.return_value.auto_model.state_dict.return_value = mock_state_dict
        mock_st.return_value = mock_model

        with cli_runner.isolated_filesystem():
            from resume_as_code.services.embedding_cache import EmbeddingCache

            cache_dir = Path(".resume-cache/intfloat_multilingual-e5-large-instruct")
            cache = EmbeddingCache(cache_dir, model_hash="test_hash")
            cache.put("text1", np.random.rand(384).astype(np.float32))
            cache.put("text2", np.random.rand(384).astype(np.float32))

            result = cli_runner.invoke(main, ["cache", "stats"])

            assert result.exit_code == 0
            assert "2" in result.output  # Total entries

    def test_cache_stats_json_output(self, cli_runner: CliRunner) -> None:
        """Should output JSON when --json flag is used."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(main, ["--json", "cache", "stats"])
            assert result.exit_code == 0

            data = json.loads(result.output)
            assert data["status"] == "success"
            assert data["command"] == "cache stats"
