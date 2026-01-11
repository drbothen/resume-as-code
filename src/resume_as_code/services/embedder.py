"""Embedding service with caching and model versioning."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray
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
    def model(self) -> SentenceTransformer:
        """Lazy-load the embedding model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            try:
                self._model = SentenceTransformer(self.model_name)
            except (OSError, RuntimeError, ValueError):
                # Fallback to smaller model on network/file/model errors
                self._model = SentenceTransformer(self.FALLBACK_MODEL)
                self.model_name = self.FALLBACK_MODEL

            self._model_hash = self._compute_model_hash()

        return self._model

    @property
    def model_hash(self) -> str:
        """Get the model hash (triggers model load if needed)."""
        if self._model_hash is None:
            _ = self.model  # Force load
        assert self._model_hash is not None
        return self._model_hash

    @property
    def cache(self) -> EmbeddingCache:
        """Get the embedding cache."""
        if self._cache is None:
            from resume_as_code.services.embedding_cache import EmbeddingCache

            cache_path = self.cache_dir / self._sanitize_model_name()
            self._cache = EmbeddingCache(cache_path, self.model_hash)
        return self._cache

    def embed_query(self, text: str) -> NDArray[np.float32]:
        """Embed text as a query (for Work Units).

        Uses 'query: ' prefix for e5-instruct models.
        """
        prefixed = f"query: {text}" if "e5" in self.model_name.lower() else text
        return self._embed_with_cache(prefixed)

    def embed_passage(self, text: str) -> NDArray[np.float32]:
        """Embed text as a passage (for Job Descriptions).

        Uses 'passage: ' prefix for e5-instruct models.
        """
        prefixed = f"passage: {text}" if "e5" in self.model_name.lower() else text
        return self._embed_with_cache(prefixed)

    def embed(self, text: str) -> NDArray[np.float32]:
        """Embed text without prefix (generic embedding).

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.
        """
        return self._embed_with_cache(text)

    def embed_batch(
        self,
        texts: list[str],
        is_query: bool = True,
    ) -> NDArray[np.float32]:
        """Embed a batch of texts.

        Args:
            texts: List of texts to embed.
            is_query: If True, use query prefix; else passage prefix.

        Returns:
            Array of embeddings (n_texts, embedding_dim).
        """
        # Handle empty input
        if not texts:
            return np.empty((0, 0), dtype=np.float32)

        if "e5" in self.model_name.lower():
            prefix = "query: " if is_query else "passage: "
            texts = [f"{prefix}{t}" for t in texts]

        # Check cache for each
        embeddings: list[tuple[int, NDArray[np.float32]]] = []
        texts_to_compute: list[tuple[int, str]] = []

        for i, text in enumerate(texts):
            cached = self.cache.get(text)
            if cached is not None:
                embeddings.append((i, cached))
            else:
                texts_to_compute.append((i, text))

        # Compute missing embeddings
        if texts_to_compute:
            indices, uncached_texts = zip(*texts_to_compute, strict=True)
            computed: NDArray[np.float32] = self.model.encode(
                list(uncached_texts),
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            for idx, text, emb in zip(indices, uncached_texts, computed, strict=True):
                self.cache.put(text, emb)
                embeddings.append((idx, emb))

        # Sort by original index and stack
        embeddings.sort(key=lambda x: x[0])
        return np.stack([e for _, e in embeddings])

    def _embed_with_cache(self, text: str) -> NDArray[np.float32]:
        """Embed text with caching."""
        # Check cache
        cached = self.cache.get(text)
        if cached is not None:
            return cached

        # Compute embedding
        embedding: NDArray[np.float32] = self.model.encode(
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

        # Hash model state dict (accessing internal API of SentenceTransformer)
        first_module = self.model._first_module()
        state_dict = first_module.auto_model.state_dict()  # type: ignore[union-attr]
        for name in sorted(state_dict.keys())[:10]:  # Sample first 10 layers
            param = state_dict[name]
            hasher.update(param.cpu().numpy().tobytes()[:1000])  # Sample bytes

        return hasher.hexdigest()[:16]

    def _sanitize_model_name(self) -> str:
        """Convert model name to safe directory name."""
        return self.model_name.replace("/", "_").replace("\\", "_")
