"""SQLite-based embedding cache with compression."""

from __future__ import annotations

import gzip
import hashlib
import pickle
import sqlite3
import time
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


class EmbeddingCache:
    """SQLite-based cache for embeddings with model versioning."""

    def __init__(self, cache_dir: Path, model_hash: str) -> None:
        """Initialize the cache.

        Args:
            cache_dir: Directory for cache files.
            model_hash: Hash of the current model weights.
        """
        self.cache_dir = cache_dir
        self.model_hash = model_hash
        self.db_path = cache_dir / "cache.db"

        # Ensure directory exists
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    cache_key TEXT PRIMARY KEY,
                    model_hash TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_hash
                ON embeddings(model_hash)
            """)

    def _cache_key(self, text: str) -> str:
        """Generate cache key from model hash and text.

        Args:
            text: Text to generate key for.

        Returns:
            SHA256 hash of model_hash + normalized text.
        """
        normalized = text.strip().lower()
        key_input = f"{self.model_hash}::{normalized}"
        return hashlib.sha256(key_input.encode()).hexdigest()

    def get(self, text: str) -> NDArray[np.float32] | None:
        """Retrieve embedding from cache.

        Args:
            text: Text to look up.

        Returns:
            Cached embedding or None if not found/stale.
        """
        cache_key = self._cache_key(text)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT embedding, model_hash FROM embeddings
                WHERE cache_key = ?
                """,
                (cache_key,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        embedding_blob, stored_hash = row

        # Check model hash matches
        if stored_hash != self.model_hash:
            return None

        # Decompress and unpickle
        try:
            decompressed = gzip.decompress(embedding_blob)
            result: NDArray[np.float32] = pickle.loads(decompressed)  # noqa: S301
            return result
        except (gzip.BadGzipFile, pickle.UnpicklingError, OSError, EOFError):
            # Handle corrupted cache entries gracefully
            return None

    def put(self, text: str, embedding: NDArray[np.float32]) -> None:
        """Store embedding in cache.

        Args:
            text: Text that was embedded.
            embedding: The embedding vector.
        """
        cache_key = self._cache_key(text)

        # Compress and pickle
        pickled = pickle.dumps(embedding)
        compressed = gzip.compress(pickled)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO embeddings
                (cache_key, model_hash, embedding, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (cache_key, self.model_hash, compressed, time.time()),
            )

    def clear_stale(self) -> int:
        """Clear embeddings with stale model hashes.

        Returns:
            Number of entries cleared.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM embeddings
                WHERE model_hash != ?
                """,
                (self.model_hash,),
            )
            return cursor.rowcount

    def clear_all(self) -> int:
        """Clear all cached embeddings.

        Returns:
            Number of entries cleared.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM embeddings")
            return cursor.rowcount

    def stats(self) -> dict[str, int | str]:
        """Get cache statistics.

        Returns:
            Dictionary with total_entries, current_model_entries,
            stale_entries, and model_hash.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
            total = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT COUNT(*) FROM embeddings WHERE model_hash = ?",
                (self.model_hash,),
            )
            current = cursor.fetchone()[0]

        return {
            "total_entries": total,
            "current_model_entries": current,
            "stale_entries": total - current,
            "model_hash": self.model_hash,
        }
