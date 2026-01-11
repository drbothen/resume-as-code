"""Tests for embedding cache."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest

from resume_as_code.services.embedding_cache import EmbeddingCache


@pytest.fixture
def cache(tmp_path: Path) -> EmbeddingCache:
    """Create a test cache."""
    return EmbeddingCache(tmp_path, model_hash="test_hash_123")


class TestEmbeddingCacheInit:
    """Tests for EmbeddingCache initialization."""

    def test_creates_cache_directory(self, tmp_path: Path) -> None:
        """Should create cache directory if it doesn't exist."""
        cache_dir = tmp_path / "new_cache"
        assert not cache_dir.exists()

        EmbeddingCache(cache_dir, model_hash="test")
        assert cache_dir.exists()

    def test_creates_database_file(self, tmp_path: Path) -> None:
        """Should create SQLite database file."""
        cache = EmbeddingCache(tmp_path, model_hash="test")
        assert cache.db_path.exists()
        assert cache.db_path.name == "cache.db"

    def test_stores_model_hash(self, tmp_path: Path) -> None:
        """Should store the model hash."""
        cache = EmbeddingCache(tmp_path, model_hash="my_hash_456")
        assert cache.model_hash == "my_hash_456"


class TestEmbeddingCachePutAndGet:
    """Tests for put and get operations."""

    def test_put_and_get_roundtrip(self, cache: EmbeddingCache) -> None:
        """Should store and retrieve embeddings correctly."""
        embedding = np.random.rand(384).astype(np.float32)
        cache.put("test text", embedding)

        retrieved = cache.get("test text")
        assert retrieved is not None
        np.testing.assert_array_almost_equal(embedding, retrieved)

    def test_returns_none_for_missing_key(self, cache: EmbeddingCache) -> None:
        """Should return None for missing entries."""
        result = cache.get("nonexistent text")
        assert result is None

    def test_handles_large_embeddings(self, cache: EmbeddingCache) -> None:
        """Should handle large embedding vectors (1024 dims)."""
        embedding = np.random.rand(1024).astype(np.float32)
        cache.put("large embedding", embedding)

        retrieved = cache.get("large embedding")
        assert retrieved is not None
        assert retrieved.shape == (1024,)
        np.testing.assert_array_almost_equal(embedding, retrieved)

    def test_overwrites_existing_entry(self, cache: EmbeddingCache) -> None:
        """Should overwrite existing entry on duplicate key."""
        embedding1 = np.ones(384, dtype=np.float32)
        embedding2 = np.zeros(384, dtype=np.float32)

        cache.put("same key", embedding1)
        cache.put("same key", embedding2)

        retrieved = cache.get("same key")
        assert retrieved is not None
        np.testing.assert_array_almost_equal(embedding2, retrieved)


class TestEmbeddingCacheCacheKey:
    """Tests for cache key generation."""

    def test_cache_key_uses_sha256(self, cache: EmbeddingCache) -> None:
        """Cache key should be SHA256 hash."""
        key = cache._cache_key("test")
        assert len(key) == 64  # SHA256 produces 64 hex chars

    def test_cache_key_includes_model_hash(self, tmp_path: Path) -> None:
        """Cache key should include model hash for versioning."""
        cache1 = EmbeddingCache(tmp_path, model_hash="hash_v1")
        cache2 = EmbeddingCache(tmp_path, model_hash="hash_v2")

        key1 = cache1._cache_key("same text")
        key2 = cache2._cache_key("same text")

        assert key1 != key2

    def test_cache_key_normalizes_text(self, cache: EmbeddingCache) -> None:
        """Cache key should normalize text (lowercase, strip)."""
        key1 = cache._cache_key("  TEST TEXT  ")
        key2 = cache._cache_key("test text")

        assert key1 == key2


class TestEmbeddingCacheModelVersioning:
    """Tests for model hash versioning."""

    def test_ignores_entries_with_different_model_hash(self, tmp_path: Path) -> None:
        """Should return None for entries with different model hash."""
        # Create cache with old hash
        old_cache = EmbeddingCache(tmp_path, model_hash="old_hash")
        embedding = np.random.rand(384).astype(np.float32)
        old_cache.put("test text", embedding)

        # New cache with different hash should not find the entry
        new_cache = EmbeddingCache(tmp_path, model_hash="new_hash")
        result = new_cache.get("test text")
        assert result is None

    def test_finds_entries_with_same_model_hash(self, tmp_path: Path) -> None:
        """Should find entries with matching model hash."""
        cache1 = EmbeddingCache(tmp_path, model_hash="same_hash")
        embedding = np.random.rand(384).astype(np.float32)
        cache1.put("test text", embedding)

        cache2 = EmbeddingCache(tmp_path, model_hash="same_hash")
        result = cache2.get("test text")
        assert result is not None
        np.testing.assert_array_almost_equal(embedding, result)


class TestEmbeddingCacheClearOperations:
    """Tests for cache clearing operations."""

    def test_clear_stale_removes_old_model_entries(self, tmp_path: Path) -> None:
        """Should remove entries with non-matching model hash."""
        old_cache = EmbeddingCache(tmp_path, model_hash="old_hash")
        old_cache.put("old text", np.random.rand(384).astype(np.float32))

        new_cache = EmbeddingCache(tmp_path, model_hash="new_hash")
        new_cache.put("new text", np.random.rand(384).astype(np.float32))

        cleared = new_cache.clear_stale()
        assert cleared == 1

    def test_clear_stale_keeps_current_model_entries(self, tmp_path: Path) -> None:
        """Should keep entries with matching model hash."""
        cache = EmbeddingCache(tmp_path, model_hash="current_hash")
        cache.put("text1", np.random.rand(384).astype(np.float32))
        cache.put("text2", np.random.rand(384).astype(np.float32))

        cleared = cache.clear_stale()
        assert cleared == 0

        # Verify entries still exist
        assert cache.get("text1") is not None
        assert cache.get("text2") is not None

    def test_clear_all_removes_everything(self, tmp_path: Path) -> None:
        """Should remove all entries regardless of model hash."""
        cache1 = EmbeddingCache(tmp_path, model_hash="hash1")
        cache1.put("text1", np.random.rand(384).astype(np.float32))

        cache2 = EmbeddingCache(tmp_path, model_hash="hash2")
        cache2.put("text2", np.random.rand(384).astype(np.float32))

        cleared = cache2.clear_all()
        assert cleared == 2

    def test_clear_all_returns_count(self, cache: EmbeddingCache) -> None:
        """Should return the number of cleared entries."""
        cache.put("text1", np.random.rand(384).astype(np.float32))
        cache.put("text2", np.random.rand(384).astype(np.float32))
        cache.put("text3", np.random.rand(384).astype(np.float32))

        cleared = cache.clear_all()
        assert cleared == 3


class TestEmbeddingCacheStats:
    """Tests for cache statistics."""

    def test_stats_returns_correct_counts(self, tmp_path: Path) -> None:
        """Should return correct entry counts."""
        # Add entries with different hashes
        old_cache = EmbeddingCache(tmp_path, model_hash="old_hash")
        old_cache.put("old1", np.random.rand(384).astype(np.float32))
        old_cache.put("old2", np.random.rand(384).astype(np.float32))

        new_cache = EmbeddingCache(tmp_path, model_hash="new_hash")
        new_cache.put("new1", np.random.rand(384).astype(np.float32))

        stats = new_cache.stats()
        assert stats["total_entries"] == 3
        assert stats["current_model_entries"] == 1
        assert stats["stale_entries"] == 2
        assert stats["model_hash"] == "new_hash"

    def test_stats_on_empty_cache(self, cache: EmbeddingCache) -> None:
        """Should return zeros for empty cache."""
        stats = cache.stats()
        assert stats["total_entries"] == 0
        assert stats["current_model_entries"] == 0
        assert stats["stale_entries"] == 0


class TestEmbeddingCacheCompression:
    """Tests for gzip compression."""

    def test_embeddings_are_compressed(self, tmp_path: Path) -> None:
        """Stored embeddings should be gzip compressed."""
        import sqlite3

        cache = EmbeddingCache(tmp_path, model_hash="test")
        embedding = np.random.rand(1024).astype(np.float32)
        cache.put("test text", embedding)

        # Read raw blob from database
        with sqlite3.connect(cache.db_path) as conn:
            cursor = conn.execute("SELECT embedding FROM embeddings LIMIT 1")
            blob = cursor.fetchone()[0]

        # Gzip magic number is 1f 8b
        assert blob[:2] == b"\x1f\x8b"

    def test_compression_reduces_size(self, tmp_path: Path) -> None:
        """Compression should reduce storage size."""
        import sqlite3

        cache = EmbeddingCache(tmp_path, model_hash="test")
        # Create a highly compressible embedding (all zeros)
        embedding = np.zeros(1024, dtype=np.float32)
        cache.put("test text", embedding)

        # Read raw blob from database
        with sqlite3.connect(cache.db_path) as conn:
            cursor = conn.execute("SELECT embedding FROM embeddings LIMIT 1")
            blob = cursor.fetchone()[0]

        # Uncompressed size would be 1024 * 4 = 4096 bytes
        # Compressed should be much smaller for zeros
        assert len(blob) < 1024  # At least 75% reduction for zeros


class TestEmbeddingCachePerformance:
    """Performance tests for cache."""

    def test_retrieval_under_10ms(self, cache: EmbeddingCache) -> None:
        """Cache retrieval should be under 10ms (AC #2)."""
        embedding = np.random.rand(1024).astype(np.float32)  # Large embedding
        cache.put("test text", embedding)

        # Warm up
        cache.get("test text")

        # Measure retrieval time
        start = time.perf_counter()
        for _ in range(100):
            cache.get("test text")
        elapsed = (time.perf_counter() - start) / 100 * 1000  # ms per retrieval

        assert elapsed < 10, f"Retrieval took {elapsed:.2f}ms (should be <10ms)"

    def test_handles_concurrent_access(self, tmp_path: Path) -> None:
        """Should handle multiple cache instances accessing same db."""
        cache1 = EmbeddingCache(tmp_path, model_hash="shared_hash")
        cache2 = EmbeddingCache(tmp_path, model_hash="shared_hash")

        embedding = np.random.rand(384).astype(np.float32)
        cache1.put("shared text", embedding)

        # Should be visible to cache2
        result = cache2.get("shared text")
        assert result is not None
        np.testing.assert_array_almost_equal(embedding, result)
