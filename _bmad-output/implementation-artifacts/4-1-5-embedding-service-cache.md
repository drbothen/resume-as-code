# Story 4.1.5: Embedding Service & Cache

Status: done

## Story

As a **system**,
I want **an embedding service with intelligent caching and model versioning**,
So that **semantic search is fast and embeddings remain valid across model updates**.

> **Note:** This is an enabling story that provides infrastructure for Story 4.2 (BM25 Ranking Engine). It does not deliver direct user value but is required for semantic ranking.

## Acceptance Criteria

1. **Given** the embedding service is initialized
   **When** I load the model
   **Then** the model hash is computed from weights for cache key generation
   **And** the hash is stored for all subsequent cache operations

2. **Given** I request embeddings for text
   **When** the text exists in cache with matching model hash
   **Then** the cached embedding is returned without recomputation
   **And** retrieval completes in <10ms

3. **Given** I request embeddings for text
   **When** the cache miss occurs or model hash differs
   **Then** the embedding is computed fresh
   **And** the result is stored in cache with current model hash

4. **Given** the embedding model is updated
   **When** I request embeddings for previously cached text
   **Then** the old cached embedding is ignored (model hash mismatch)
   **And** a fresh embedding is computed and cached

5. **Given** I run `resume cache clear`
   **When** the command completes
   **Then** embeddings with stale model hashes are removed
   **And** a count of cleared entries is displayed

6. **Given** the embedding service generates embeddings
   **When** I inspect the cache key format
   **Then** it uses: `SHA256(model_hash + "::" + normalized_text)`
   **And** normalized_text is lowercased and stripped

7. **Given** the cache storage format
   **When** I inspect stored embeddings
   **Then** they use SQLite for indexing
   **And** pickle for serialization
   **And** gzip for compression (40-60% size reduction)

## Tasks / Subtasks

- [x] Task 1: Create EmbeddingService class (AC: #1, #2, #3)
  - [x] 1.1: Create `src/resume_as_code/services/embedder.py`
  - [x] 1.2: Implement model loading with sentence-transformers
  - [x] 1.3: Implement model hash computation
  - [x] 1.4: Implement `embed(text: str) -> np.ndarray`
  - [x] 1.5: Implement `embed_batch(texts: list[str]) -> np.ndarray`

- [x] Task 2: Implement embedding cache (AC: #2, #3, #6, #7)
  - [x] 2.1: Create `src/resume_as_code/services/embedding_cache.py`
  - [x] 2.2: Implement SQLite database setup
  - [x] 2.3: Implement cache key generation (SHA256)
  - [x] 2.4: Implement `get(text: str) -> np.ndarray | None`
  - [x] 2.5: Implement `put(text: str, embedding: np.ndarray)`
  - [x] 2.6: Implement gzip compression for embeddings

- [x] Task 3: Implement model hash computation (AC: #1, #4)
  - [x] 3.1: Compute hash from model weights
  - [x] 3.2: Store hash in cache metadata
  - [x] 3.3: Validate hash on cache retrieval
  - [x] 3.4: Handle model updates gracefully

- [x] Task 4: Implement instruction prefixes (AC: #1)
  - [x] 4.1: Add `embed_query(text: str)` for Work Units
  - [x] 4.2: Add `embed_passage(text: str)` for JDs
  - [x] 4.3: Apply correct prefix per embedding type

- [x] Task 5: Create cache clear command (AC: #5)
  - [x] 5.1: Create `src/resume_as_code/commands/cache.py`
  - [x] 5.2: Implement `resume cache clear` command
  - [x] 5.3: Clear stale entries by model hash
  - [x] 5.4: Display count of cleared entries

- [x] Task 6: Code quality verification
  - [x] 6.1: Run `ruff check src tests --fix`
  - [x] 6.2: Run `ruff format src tests`
  - [x] 6.3: Run `mypy src --strict` with zero errors
  - [x] 6.4: Add unit tests for cache operations
  - [x] 6.5: Add unit tests for model hash computation
  - [x] 6.6: Add performance test for cache retrieval (<10ms)

## Dev Notes

### Architecture Compliance

This story implements the embedding cache system per Architecture Section 3.2. The cache enables fast semantic search by avoiding redundant embedding computations.

**Source:** [epics.md#Story 4.1.5](_bmad-output/planning-artifacts/epics.md)
**Source:** [Architecture Section 3.2 - Data Architecture](_bmad-output/planning-artifacts/architecture.md)

### Dependencies

This story REQUIRES:
- Story 1.1 (Project Scaffolding) - Base project structure

This story ENABLES:
- Story 4.2 (BM25 Ranking Engine) - Uses embeddings for semantic similarity

### Model Selection

| Model | Dimensions | Parameters | Use Case |
|-------|------------|------------|----------|
| `intfloat/multilingual-e5-large-instruct` | 1024 | 560M | Primary (better quality) |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | 22M | Fallback (faster, smaller) |

### Instruction Prefixes (CRITICAL)

The e5-large-instruct model requires instruction prefixes:
- **Passages (JDs):** `"passage: {text}"`
- **Queries (Work Units):** `"query: {text}"`

Failing to use these prefixes significantly degrades retrieval quality.

### Cache Directory Structure

```
.resume-cache/
├── intfloat_multilingual-e5-large-instruct/
│   └── cache.db              # SQLite database (stores embeddings + metadata)
└── sentence-transformers_all-MiniLM-L6-v2/
    └── cache.db
```

> **Note:** Metadata (model hash, entry count, timestamps) is stored within the SQLite `embeddings` table rather than a separate JSON file.

### EmbeddingService Implementation

**`src/resume_as_code/services/embedder.py`:**

```python
"""Embedding service with caching and model versioning."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

from resume_as_code.services.embedding_cache import EmbeddingCache


class EmbeddingService:
    """Service for generating and caching text embeddings."""

    DEFAULT_MODEL = "intfloat/multilingual-e5-large-instruct"
    FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(
        self,
        model_name: str | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        """Initialize the embedding service.

        Args:
            model_name: Model to use (default: e5-large-instruct).
            cache_dir: Cache directory (default: .resume-cache/).
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.cache_dir = cache_dir or Path(".resume-cache")

        self._model: SentenceTransformer | None = None
        self._model_hash: str | None = None
        self._cache: EmbeddingCache | None = None

    @property
    def model(self) -> "SentenceTransformer":
        """Lazy-load the embedding model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            try:
                self._model = SentenceTransformer(self.model_name)
            except Exception:
                # Fallback to smaller model
                self._model = SentenceTransformer(self.FALLBACK_MODEL)
                self.model_name = self.FALLBACK_MODEL

            self._model_hash = self._compute_model_hash()

        return self._model

    @property
    def model_hash(self) -> str:
        """Get the model hash (triggers model load if needed)."""
        if self._model_hash is None:
            _ = self.model  # Force load
        return self._model_hash  # type: ignore

    @property
    def cache(self) -> EmbeddingCache:
        """Get the embedding cache."""
        if self._cache is None:
            cache_path = self.cache_dir / self._sanitize_model_name()
            self._cache = EmbeddingCache(cache_path, self.model_hash)
        return self._cache

    def embed_query(self, text: str) -> np.ndarray:
        """Embed text as a query (for Work Units).

        Uses 'query: ' prefix for e5-instruct models.
        """
        prefixed = f"query: {text}" if "e5" in self.model_name.lower() else text
        return self._embed_with_cache(prefixed)

    def embed_passage(self, text: str) -> np.ndarray:
        """Embed text as a passage (for Job Descriptions).

        Uses 'passage: ' prefix for e5-instruct models.
        """
        prefixed = f"passage: {text}" if "e5" in self.model_name.lower() else text
        return self._embed_with_cache(prefixed)

    def embed_batch(
        self,
        texts: list[str],
        is_query: bool = True,
    ) -> np.ndarray:
        """Embed a batch of texts.

        Args:
            texts: List of texts to embed.
            is_query: If True, use query prefix; else passage prefix.

        Returns:
            Array of embeddings (n_texts, embedding_dim).
        """
        if "e5" in self.model_name.lower():
            prefix = "query: " if is_query else "passage: "
            texts = [f"{prefix}{t}" for t in texts]

        # Check cache for each
        embeddings: list[np.ndarray] = []
        texts_to_compute: list[tuple[int, str]] = []

        for i, text in enumerate(texts):
            cached = self.cache.get(text)
            if cached is not None:
                embeddings.append((i, cached))
            else:
                texts_to_compute.append((i, text))

        # Compute missing embeddings
        if texts_to_compute:
            indices, uncached_texts = zip(*texts_to_compute)
            computed = self.model.encode(
                list(uncached_texts),
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            for idx, text, emb in zip(indices, uncached_texts, computed):
                self.cache.put(text, emb)
                embeddings.append((idx, emb))

        # Sort by original index and stack
        embeddings.sort(key=lambda x: x[0])
        return np.stack([e for _, e in embeddings])

    def _embed_with_cache(self, text: str) -> np.ndarray:
        """Embed text with caching."""
        # Check cache
        cached = self.cache.get(text)
        if cached is not None:
            return cached

        # Compute embedding
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        # Store in cache
        self.cache.put(text, embedding)

        return embedding

    def _compute_model_hash(self) -> str:
        """Compute a hash of the model weights."""
        hasher = hashlib.sha256()

        # Hash model state dict
        state_dict = self.model._first_module().auto_model.state_dict()
        for name in sorted(state_dict.keys())[:10]:  # Sample first 10 layers
            param = state_dict[name]
            hasher.update(param.cpu().numpy().tobytes()[:1000])  # Sample bytes

        return hasher.hexdigest()[:16]

    def _sanitize_model_name(self) -> str:
        """Convert model name to safe directory name."""
        return self.model_name.replace("/", "_").replace("\\", "_")
```

### EmbeddingCache Implementation

**`src/resume_as_code/services/embedding_cache.py`:**

```python
"""SQLite-based embedding cache with compression."""

from __future__ import annotations

import gzip
import hashlib
import pickle
import sqlite3
import time
from pathlib import Path

import numpy as np


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
        """Generate cache key from model hash and text."""
        normalized = text.strip().lower()
        key_input = f"{self.model_hash}::{normalized}"
        return hashlib.sha256(key_input.encode()).hexdigest()

    def get(self, text: str) -> np.ndarray | None:
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
            return pickle.loads(decompressed)
        except Exception:
            return None

    def put(self, text: str, embedding: np.ndarray) -> None:
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

    def stats(self) -> dict:
        """Get cache statistics."""
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
```

### Cache Command

**`src/resume_as_code/commands/cache.py`:**

```python
"""Cache management commands."""

from __future__ import annotations

from pathlib import Path

import click

from resume_as_code.models.output import JSONResponse
from resume_as_code.services.embedder import EmbeddingService
from resume_as_code.utils.console import console, success, info
from resume_as_code.utils.errors import handle_errors


@click.group("cache")
def cache_group() -> None:
    """Manage embedding cache."""
    pass


@cache_group.command("clear")
@click.option(
    "--all",
    "clear_all",
    is_flag=True,
    help="Clear all entries (not just stale ones)",
)
@click.pass_context
@handle_errors
def cache_clear(ctx: click.Context, clear_all: bool) -> None:
    """Clear stale embedding cache entries.

    By default, only clears entries from outdated model versions.
    Use --all to clear everything.
    """
    cache_dir = Path(".resume-cache")

    if not cache_dir.exists():
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="cache clear",
                data={"cleared": 0, "message": "No cache directory found"},
            )
            print(response.to_json())
        else:
            info("No cache directory found. Nothing to clear.")
        return

    # Initialize service to get model hash
    service = EmbeddingService(cache_dir=cache_dir)

    if clear_all:
        cleared = service.cache.clear_all()
        message = f"Cleared all {cleared} cache entries"
    else:
        cleared = service.cache.clear_stale()
        message = f"Cleared {cleared} stale cache entries"

    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="cache clear",
            data={"cleared": cleared},
        )
        print(response.to_json())
    else:
        success(message)


@cache_group.command("stats")
@click.pass_context
@handle_errors
def cache_stats(ctx: click.Context) -> None:
    """Show embedding cache statistics."""
    cache_dir = Path(".resume-cache")

    if not cache_dir.exists():
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="cache stats",
                data={"exists": False},
            )
            print(response.to_json())
        else:
            info("No cache directory found.")
        return

    service = EmbeddingService(cache_dir=cache_dir)
    stats = service.cache.stats()

    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="cache stats",
            data=stats,
        )
        print(response.to_json())
    else:
        console.print(f"[bold]Cache Statistics[/bold]")
        console.print(f"  Total entries: {stats['total_entries']}")
        console.print(f"  Current model: {stats['current_model_entries']}")
        console.print(f"  Stale entries: {stats['stale_entries']}")
        console.print(f"  Model hash: {stats['model_hash']}")
```

### CLI Registration

**Update `src/resume_as_code/cli.py`:**

```python
# Add import
from resume_as_code.commands.cache import cache_group

# Register command group
main.add_command(cache_group)
```

### Testing Requirements

**`tests/unit/test_embedding_cache.py`:**

```python
"""Tests for embedding cache."""

import numpy as np
import pytest

from resume_as_code.services.embedding_cache import EmbeddingCache


@pytest.fixture
def cache(tmp_path) -> EmbeddingCache:
    """Create a test cache."""
    return EmbeddingCache(tmp_path, model_hash="test_hash_123")


class TestEmbeddingCache:
    """Tests for EmbeddingCache."""

    def test_put_and_get(self, cache: EmbeddingCache):
        """Should store and retrieve embeddings."""
        embedding = np.random.rand(384).astype(np.float32)
        cache.put("test text", embedding)

        retrieved = cache.get("test text")
        assert retrieved is not None
        np.testing.assert_array_almost_equal(embedding, retrieved)

    def test_returns_none_for_missing(self, cache: EmbeddingCache):
        """Should return None for missing entries."""
        result = cache.get("nonexistent")
        assert result is None

    def test_ignores_stale_model_hash(self, tmp_path):
        """Should ignore entries with different model hash."""
        # Create cache with old hash
        old_cache = EmbeddingCache(tmp_path, model_hash="old_hash")
        embedding = np.random.rand(384).astype(np.float32)
        old_cache.put("test text", embedding)

        # New cache with different hash
        new_cache = EmbeddingCache(tmp_path, model_hash="new_hash")
        result = new_cache.get("test text")
        assert result is None

    def test_clear_stale(self, tmp_path):
        """Should clear stale entries."""
        old_cache = EmbeddingCache(tmp_path, model_hash="old_hash")
        old_cache.put("old text", np.random.rand(384))

        new_cache = EmbeddingCache(tmp_path, model_hash="new_hash")
        new_cache.put("new text", np.random.rand(384))

        cleared = new_cache.clear_stale()
        assert cleared == 1

    def test_stats(self, cache: EmbeddingCache):
        """Should return cache statistics."""
        cache.put("text1", np.random.rand(384))
        cache.put("text2", np.random.rand(384))

        stats = cache.stats()
        assert stats["total_entries"] == 2
        assert stats["current_model_entries"] == 2
        assert stats["stale_entries"] == 0


class TestCachePerformance:
    """Performance tests for cache."""

    def test_retrieval_under_10ms(self, cache: EmbeddingCache):
        """Cache retrieval should be under 10ms."""
        import time

        embedding = np.random.rand(1024).astype(np.float32)  # Large embedding
        cache.put("test text", embedding)

        start = time.perf_counter()
        for _ in range(100):
            cache.get("test text")
        elapsed = (time.perf_counter() - start) / 100 * 1000  # ms per retrieval

        assert elapsed < 10, f"Retrieval took {elapsed:.2f}ms (should be <10ms)"
```

### Verification Commands

```bash
# Test embedding service (requires sentence-transformers)
python -c "
from resume_as_code.services.embedder import EmbeddingService

service = EmbeddingService()
embedding = service.embed_query('Python developer with AWS experience')
print(f'Embedding shape: {embedding.shape}')
print(f'Model hash: {service.model_hash}')
"

# Test cache
resume cache stats

# Clear stale entries
resume cache clear

# Clear all entries
resume cache clear --all

# Code quality
ruff check src tests --fix
mypy src --strict
pytest tests/unit/test_embedding_cache.py -v
```

### References

- [Source: epics.md#Story 4.1.5](_bmad-output/planning-artifacts/epics.md)
- [Source: architecture.md#Section 3.2 - Data Architecture](_bmad-output/planning-artifacts/architecture.md)
- [Source: project-context.md](_bmad-output/project-context.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Implemented EmbeddingService with lazy model loading and automatic fallback to smaller model
- Model hash computed from first 10 layers' weights (sampled bytes) using SHA256 truncated to 16 chars
- EmbeddingCache uses SQLite for indexing with gzip-compressed pickle serialization
- Cache key format: SHA256(model_hash + "::" + normalized_text) where normalized = lowercase + stripped
- E5 instruction prefixes applied: "query: " for Work Units, "passage: " for Job Descriptions
- Cache retrieval verified under 10ms per acceptance criteria
- All 653 tests passing, ruff and mypy --strict clean

### Code Review Fixes (2026-01-11)

**Issues Found & Fixed:**
- **H1:** Fixed empty batch crash - `embed_batch([])` now returns empty array gracefully
- **M1:** Added `@handle_errors` decorator to cache commands for consistent error handling
- **M2:** Updated documentation to reflect SQLite-based metadata storage (removed incorrect `metadata.json` reference)
- **M3:** Added 4 edge case tests for empty batch, empty string, long text, and single-item batch
- **L1:** Changed broad `except Exception:` to specific exceptions (`OSError`, `RuntimeError`, `ValueError`, `gzip.BadGzipFile`, `pickle.UnpicklingError`, `EOFError`)
- **L2:** Reverted unrelated `jd_parser.py` formatting change

### File List

**New Files:**
- `src/resume_as_code/services/embedder.py` - EmbeddingService class with caching and model versioning
- `src/resume_as_code/services/embedding_cache.py` - SQLite-based embedding cache with gzip compression
- `src/resume_as_code/commands/cache.py` - CLI commands for cache management (clear, stats)
- `tests/unit/test_embedding_service.py` - 22 unit tests for EmbeddingService (including edge cases)
- `tests/unit/test_embedding_cache.py` - 22 unit tests for EmbeddingCache
- `tests/unit/test_cache_cmd.py` - 8 unit tests for cache CLI commands

**Modified Files:**
- `src/resume_as_code/cli.py` - Added cache_group registration
