"""Tests for embedding service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


class TestEmbeddingServiceInit:
    """Tests for EmbeddingService initialization."""

    def test_default_model_name(self) -> None:
        """Should use e5-large-instruct as default model."""
        from resume_as_code.services.embedder import EmbeddingService

        service = EmbeddingService()
        assert service.model_name == "intfloat/multilingual-e5-large-instruct"

    def test_custom_model_name(self) -> None:
        """Should accept custom model name."""
        from resume_as_code.services.embedder import EmbeddingService

        service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")
        assert service.model_name == "sentence-transformers/all-MiniLM-L6-v2"

    def test_default_cache_dir(self) -> None:
        """Should use .resume-cache as default cache directory."""
        from resume_as_code.services.embedder import EmbeddingService

        service = EmbeddingService()
        assert service.cache_dir == Path(".resume-cache")

    def test_custom_cache_dir(self, tmp_path: Path) -> None:
        """Should accept custom cache directory."""
        from resume_as_code.services.embedder import EmbeddingService

        service = EmbeddingService(cache_dir=tmp_path)
        assert service.cache_dir == tmp_path


class TestEmbeddingServiceModelLoading:
    """Tests for model loading functionality."""

    def test_lazy_model_loading(self) -> None:
        """Model should not load until first use."""
        from resume_as_code.services.embedder import EmbeddingService

        service = EmbeddingService()
        assert service._model is None

    @patch("sentence_transformers.SentenceTransformer")
    def test_model_loads_on_access(self, mock_st: MagicMock) -> None:
        """Model should load when accessed."""
        from resume_as_code.services.embedder import EmbeddingService

        # Mock the model with necessary attributes for hash computation
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

        service = EmbeddingService()
        _ = service.model

        mock_st.assert_called_once_with("intfloat/multilingual-e5-large-instruct")

    @patch("sentence_transformers.SentenceTransformer")
    def test_fallback_model_on_error(self, mock_st: MagicMock) -> None:
        """Should fallback to smaller model if default fails."""
        from resume_as_code.services.embedder import EmbeddingService

        # Second call returns a mock with necessary attributes for hash computation
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
        mock_st.side_effect = [OSError("Model not found"), mock_model]

        service = EmbeddingService()
        _ = service.model

        assert mock_st.call_count == 2
        assert service.model_name == "sentence-transformers/all-MiniLM-L6-v2"


class TestEmbeddingServiceModelHash:
    """Tests for model hash computation."""

    @patch("sentence_transformers.SentenceTransformer")
    def test_model_hash_computed_on_load(self, mock_st: MagicMock) -> None:
        """Model hash should be computed when model loads."""
        from resume_as_code.services.embedder import EmbeddingService

        # Mock the model and its state dict
        mock_model = MagicMock()
        mock_state_dict = {
            "layer1.weight": MagicMock(
                cpu=MagicMock(
                    return_value=MagicMock(
                        numpy=MagicMock(return_value=np.zeros((10, 10), dtype=np.float32))
                    )
                )
            ),
            "layer2.weight": MagicMock(
                cpu=MagicMock(
                    return_value=MagicMock(
                        numpy=MagicMock(return_value=np.ones((10, 10), dtype=np.float32))
                    )
                )
            ),
        }
        mock_model._first_module.return_value.auto_model.state_dict.return_value = mock_state_dict
        mock_st.return_value = mock_model

        service = EmbeddingService()
        model_hash = service.model_hash

        assert model_hash is not None
        assert len(model_hash) == 16  # SHA256 truncated to 16 chars
        assert model_hash.isalnum()

    @patch("sentence_transformers.SentenceTransformer")
    def test_model_hash_consistent(self, mock_st: MagicMock) -> None:
        """Same model weights should produce same hash."""
        from resume_as_code.services.embedder import EmbeddingService

        # Mock the model and its state dict
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

        service1 = EmbeddingService()
        service2 = EmbeddingService()

        assert service1.model_hash == service2.model_hash


class TestEmbeddingServiceSanitizeModelName:
    """Tests for model name sanitization."""

    def test_sanitize_model_name_with_slash(self) -> None:
        """Should replace slashes with underscores."""
        from resume_as_code.services.embedder import EmbeddingService

        service = EmbeddingService(model_name="intfloat/multilingual-e5-large-instruct")
        assert service._sanitize_model_name() == "intfloat_multilingual-e5-large-instruct"

    def test_sanitize_model_name_with_backslash(self) -> None:
        """Should replace backslashes with underscores."""
        from resume_as_code.services.embedder import EmbeddingService

        service = EmbeddingService(model_name="some\\model\\path")
        assert service._sanitize_model_name() == "some_model_path"


class TestEmbeddingServiceEmbed:
    """Tests for embedding methods."""

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_returns_cached_result(self, mock_st: MagicMock, tmp_path: Path) -> None:
        """Should return cached embedding on second call."""
        from resume_as_code.services.embedder import EmbeddingService

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
        mock_model.encode.return_value = np.random.rand(384).astype(np.float32)
        mock_st.return_value = mock_model

        service = EmbeddingService(cache_dir=tmp_path)

        # First call computes embedding
        result1 = service.embed("test text")
        assert mock_model.encode.call_count == 1

        # Second call uses cache
        result2 = service.embed("test text")
        assert mock_model.encode.call_count == 1  # Still 1, not recomputed

        np.testing.assert_array_almost_equal(result1, result2)

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_query_adds_prefix_for_e5(self, mock_st: MagicMock, tmp_path: Path) -> None:
        """embed_query should add 'query: ' prefix for e5 models."""
        from resume_as_code.services.embedder import EmbeddingService

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
        mock_model.encode.return_value = np.random.rand(384).astype(np.float32)
        mock_st.return_value = mock_model

        service = EmbeddingService(
            model_name="intfloat/multilingual-e5-large-instruct",
            cache_dir=tmp_path,
        )
        service.embed_query("test query")

        # Check that encode was called with prefixed text
        call_args = mock_model.encode.call_args
        assert call_args[0][0] == "query: test query"

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_passage_adds_prefix_for_e5(self, mock_st: MagicMock, tmp_path: Path) -> None:
        """embed_passage should add 'passage: ' prefix for e5 models."""
        from resume_as_code.services.embedder import EmbeddingService

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
        mock_model.encode.return_value = np.random.rand(384).astype(np.float32)
        mock_st.return_value = mock_model

        service = EmbeddingService(
            model_name="intfloat/multilingual-e5-large-instruct",
            cache_dir=tmp_path,
        )
        service.embed_passage("test passage")

        # Check that encode was called with prefixed text
        call_args = mock_model.encode.call_args
        assert call_args[0][0] == "passage: test passage"

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_query_no_prefix_for_non_e5(self, mock_st: MagicMock, tmp_path: Path) -> None:
        """embed_query should NOT add prefix for non-e5 models."""
        from resume_as_code.services.embedder import EmbeddingService

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
        mock_model.encode.return_value = np.random.rand(384).astype(np.float32)
        mock_st.return_value = mock_model

        service = EmbeddingService(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            cache_dir=tmp_path,
        )
        service.embed_query("test query")

        # Check that encode was called WITHOUT prefix
        call_args = mock_model.encode.call_args
        assert call_args[0][0] == "test query"


class TestEmbeddingServiceEmbedBatch:
    """Tests for batch embedding."""

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_batch_returns_correct_shape(self, mock_st: MagicMock, tmp_path: Path) -> None:
        """embed_batch should return (n_texts, embedding_dim) array."""
        from resume_as_code.services.embedder import EmbeddingService

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
        mock_model.encode.return_value = np.random.rand(3, 384).astype(np.float32)
        mock_st.return_value = mock_model

        service = EmbeddingService(cache_dir=tmp_path)
        texts = ["text1", "text2", "text3"]
        result = service.embed_batch(texts)

        assert result.shape == (3, 384)

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_batch_uses_cache(self, mock_st: MagicMock, tmp_path: Path) -> None:
        """embed_batch should use cache for already computed embeddings."""
        from resume_as_code.services.embedder import EmbeddingService

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

        service = EmbeddingService(cache_dir=tmp_path)

        # First batch
        mock_model.encode.return_value = np.random.rand(2, 384).astype(np.float32)
        service.embed_batch(["text1", "text2"])

        # Second batch with one overlapping text
        mock_model.encode.reset_mock()
        mock_model.encode.return_value = np.random.rand(1, 384).astype(np.float32)
        service.embed_batch(["text1", "text3"])

        # Should only encode "text3" since "text1" is cached
        call_args = mock_model.encode.call_args
        assert len(call_args[0][0]) == 1  # Only one text to compute

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_batch_adds_prefix_for_e5(self, mock_st: MagicMock, tmp_path: Path) -> None:
        """embed_batch should add query/passage prefix for e5 models."""
        from resume_as_code.services.embedder import EmbeddingService

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
        mock_model.encode.return_value = np.random.rand(2, 384).astype(np.float32)
        mock_st.return_value = mock_model

        service = EmbeddingService(
            model_name="intfloat/multilingual-e5-large-instruct",
            cache_dir=tmp_path,
        )

        # Test query mode (default)
        service.embed_batch(["text1", "text2"], is_query=True)
        call_args = mock_model.encode.call_args
        texts = call_args[0][0]
        assert all(t.startswith("query: ") for t in texts)


class TestEmbeddingServiceSimilarity:
    """Tests for similarity computation."""

    @patch("sentence_transformers.SentenceTransformer")
    def test_similarity_returns_float(self, mock_st: MagicMock, tmp_path: Path) -> None:
        """similarity() should return a float between 0 and 1."""
        from resume_as_code.services.embedder import EmbeddingService

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
        # Return normalized vectors for predictable similarity
        mock_model.encode.side_effect = [
            np.array([1.0, 0.0, 0.0], dtype=np.float32),
            np.array([1.0, 0.0, 0.0], dtype=np.float32),
        ]
        mock_st.return_value = mock_model

        service = EmbeddingService(cache_dir=tmp_path)
        result = service.similarity("text1", "text2")

        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    @patch("sentence_transformers.SentenceTransformer")
    def test_similarity_identical_texts(self, mock_st: MagicMock, tmp_path: Path) -> None:
        """Identical texts should have similarity close to 1.0."""
        from resume_as_code.services.embedder import EmbeddingService

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
        # Same embedding for same text
        vec = np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float32)
        mock_model.encode.return_value = vec
        mock_st.return_value = mock_model

        service = EmbeddingService(cache_dir=tmp_path)
        result = service.similarity("same text", "same text")

        assert result == pytest.approx(1.0, abs=0.01)

    @patch("sentence_transformers.SentenceTransformer")
    def test_similarity_orthogonal_texts(self, mock_st: MagicMock, tmp_path: Path) -> None:
        """Orthogonal vectors should have similarity of 0."""
        from resume_as_code.services.embedder import EmbeddingService

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
        # Orthogonal vectors
        mock_model.encode.side_effect = [
            np.array([1.0, 0.0, 0.0], dtype=np.float32),
            np.array([0.0, 1.0, 0.0], dtype=np.float32),
        ]
        mock_st.return_value = mock_model

        service = EmbeddingService(cache_dir=tmp_path)
        result = service.similarity("text1", "text2")

        assert result == pytest.approx(0.0, abs=0.01)

    @patch("sentence_transformers.SentenceTransformer")
    def test_similarity_handles_zero_vector(self, mock_st: MagicMock, tmp_path: Path) -> None:
        """Should return 0 if either vector is zero."""
        from resume_as_code.services.embedder import EmbeddingService

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
        # Zero vector
        mock_model.encode.side_effect = [
            np.array([0.0, 0.0, 0.0], dtype=np.float32),
            np.array([1.0, 0.0, 0.0], dtype=np.float32),
        ]
        mock_st.return_value = mock_model

        service = EmbeddingService(cache_dir=tmp_path)
        result = service.similarity("", "text")

        assert result == 0.0


class TestEmbeddingServiceEdgeCases:
    """Tests for edge cases and error handling."""

    def test_embed_batch_empty_list(self) -> None:
        """embed_batch should handle empty input gracefully."""
        from resume_as_code.services.embedder import EmbeddingService

        service = EmbeddingService()
        result = service.embed_batch([])

        assert result.shape == (0, 0)
        assert result.dtype == np.float32

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_empty_string(self, mock_st: MagicMock, tmp_path: Path) -> None:
        """Should handle empty string input."""
        from resume_as_code.services.embedder import EmbeddingService

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
        mock_model.encode.return_value = np.random.rand(384).astype(np.float32)
        mock_st.return_value = mock_model

        service = EmbeddingService(cache_dir=tmp_path)
        result = service.embed("")

        assert result is not None
        assert result.shape == (384,)

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_very_long_text(self, mock_st: MagicMock, tmp_path: Path) -> None:
        """Should handle very long text input."""
        from resume_as_code.services.embedder import EmbeddingService

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
        mock_model.encode.return_value = np.random.rand(384).astype(np.float32)
        mock_st.return_value = mock_model

        service = EmbeddingService(cache_dir=tmp_path)
        long_text = "word " * 10000  # Very long text
        result = service.embed(long_text)

        assert result is not None
        assert result.shape == (384,)

    @patch("sentence_transformers.SentenceTransformer")
    def test_embed_batch_single_item(self, mock_st: MagicMock, tmp_path: Path) -> None:
        """embed_batch should handle single-item list."""
        from resume_as_code.services.embedder import EmbeddingService

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
        mock_model.encode.return_value = np.random.rand(1, 384).astype(np.float32)
        mock_st.return_value = mock_model

        service = EmbeddingService(cache_dir=tmp_path)
        result = service.embed_batch(["single text"])

        assert result.shape == (1, 384)
