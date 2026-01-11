# Hybrid Search Implementation Research

**Date:** 2026-01-10
**Researcher:** Claude (via Perplexity Deep Research)
**Research Type:** Deep Research
**Topics Covered:** RB-047, RB-048, RB-050

---

## Executive Summary

This research provides comprehensive implementation guidance for the hybrid search components of Resume-as-Code. Key findings:

1. **RRF Implementation (RB-047)**: k=60 is the standard parameter; RRF achieves strong results with minimal tuning
2. **e5-large-instruct Model (RB-048)**: 1024-dimensional embeddings, instruction formatting critical ("query:" vs "passage:" prefixes)
3. **Cache Invalidation (RB-050)**: Cache keys must include model hash; SQLite + pickle recommended for CLI tools

---

## RB-047: Reciprocal Rank Fusion (RRF) Implementation Details

### RRF Formula and Parameters

**Core Formula:**
```
RRF_Score(d) = Σ (1 / (k + rank_i(d)))
```

Where:
- `d` = document being scored
- `k` = smoothing parameter (default: 60)
- `rank_i(d)` = position of document `d` in result list `i`

**Parameter k=60 Rationale:**
- Experimentally determined optimal value from extensive testing
- Document at rank 1 contributes: 1/61 ≈ 0.0164
- Document at rank 2 contributes: 1/62 ≈ 0.0161
- Document at rank 60 contributes: 1/120 ≈ 0.0083
- Recommended testing range: [10, 100]

**Key Insight:** RRF is remarkably robust to k value choice. Differences between k=30 and k=100 typically amount to only a few percentage points on NDCG metrics.

### Implementation Pattern for Resume-as-Code

```python
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Tuple, Dict

class HybridSearchSystem:
    def __init__(self,
                 embedding_model_name: str = 'intfloat/multilingual-e5-large-instruct',
                 k_rrf: int = 60):
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.k_rrf = k_rrf
        self.bm25_index = None
        self.embeddings = None
        self.documents = None

    def build_index(self, documents: List[str]):
        """Build both BM25 and embedding indexes."""
        self.documents = documents

        # Build BM25 index
        tokenized_docs = [doc.lower().split() for doc in documents]
        self.bm25_index = BM25Okapi(tokenized_docs)

        # Build embedding index with passage prefix
        prefixed_docs = [f"passage: {doc}" for doc in documents]
        self.embeddings = self.embedding_model.encode(
            prefixed_docs,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

    def _apply_rrf(self, bm25_results: List[Tuple[int, float]],
                   embedding_results: List[Tuple[int, float]]) -> List[Tuple[int, float]]:
        """Apply Reciprocal Rank Fusion."""
        # Create rank dictionaries (rank starts at 1)
        bm25_ranks = {doc_idx: rank + 1 for rank, (doc_idx, _) in enumerate(bm25_results)}
        emb_ranks = {doc_idx: rank + 1 for rank, (doc_idx, _) in enumerate(embedding_results)}

        # Collect all unique documents
        all_doc_indices = set(bm25_ranks.keys()) | set(emb_ranks.keys())

        # Compute RRF scores
        rrf_scores = {}
        for doc_idx in all_doc_indices:
            rrf_score = 0
            if doc_idx in bm25_ranks:
                rrf_score += 1 / (self.k_rrf + bm25_ranks[doc_idx])
            if doc_idx in emb_ranks:
                rrf_score += 1 / (self.k_rrf + emb_ranks[doc_idx])
            rrf_scores[doc_idx] = rrf_score

        # Sort by RRF score descending, then by doc_idx for deterministic ties
        sorted_results = sorted(
            rrf_scores.items(),
            key=lambda x: (-x[1], x[0])
        )
        return sorted_results

    def search(self, query: str, top_k: int = 10, retrieve_limit: int = None) -> List[Dict]:
        """Perform hybrid search with RRF fusion."""
        if retrieve_limit is None:
            retrieve_limit = min(top_k * 2, len(self.documents))

        # BM25 retrieval
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25_index.get_scores(tokenized_query)
        bm25_results = sorted(enumerate(bm25_scores), key=lambda x: x[1], reverse=True)[:retrieve_limit]

        # Semantic retrieval with query prefix
        query_embedding = self.embedding_model.encode(
            f"query: {query}",
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        similarities = np.dot(self.embeddings, query_embedding)
        emb_results = sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)[:retrieve_limit]

        # RRF fusion
        fused_results = self._apply_rrf(bm25_results, emb_results)

        return [
            {'document_index': idx, 'rrf_score': score, 'document_text': self.documents[idx]}
            for idx, score in fused_results[:top_k]
        ]
```

### Best Practices

1. **Retrieve more than you need**: Use `retrieve_limit = top_k * 2` before fusion
2. **Deterministic tie-breaking**: Sort by doc_id as secondary key
3. **Handle missing documents**: Documents in only one list still get partial RRF contribution
4. **Parallel retrieval**: Run BM25 and embedding retrieval concurrently

### Performance Characteristics

- RRF latency overhead: ~2-5ms for fusion of two 100-document lists
- Compared to score-based methods: 1.4-1.6% faster with only 3.9% lower NDCG@10
- k=60 provides robust balance without domain-specific tuning

---

## RB-048: multilingual-e5-large-instruct Model Evaluation

### Model Specifications

| Specification | Value |
|---------------|-------|
| **Architecture** | XLM-RoBERTa-large backbone |
| **Parameters** | ~560 million |
| **Embedding Dimensions** | 1024 |
| **Max Sequence Length** | 512 tokens |
| **Languages Supported** | 100+ |
| **Training Data** | ~1 billion text pairs |

### Memory Requirements

| Precision | VRAM Required | Notes |
|-----------|---------------|-------|
| Float32 | ~2.2 GB | Full precision |
| Float16 | ~1.1 GB | Recommended for production |
| INT8 | ~0.6 GB | Quantized, slight accuracy loss |

### Inference Latency

| Hardware | Latency per Query | Batch Throughput |
|----------|-------------------|------------------|
| RTX 4090 | 30-50ms | 250-400 embeddings/sec |
| A100-40GB | 20-35ms | 400-600 embeddings/sec |
| CPU (modern) | 200-400ms | 15-30 embeddings/sec |

### Critical: Instruction Formatting

**For Resume-as-Code, use these prefixes:**
- Job Descriptions (passages to be indexed): `"passage: {job_description_text}"`
- Resumes (queries for matching): `"query: {resume_text}"`

**Example:**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('intfloat/multilingual-e5-large-instruct')

# Encode job description as passage
job_embedding = model.encode(
    "passage: Senior Python Developer: 5+ years experience with Python, Django/FastAPI...",
    normalize_embeddings=True
)

# Encode resume as query
resume_embedding = model.encode(
    "query: Python developer with 6 years experience in Django and PostgreSQL...",
    normalize_embeddings=True
)

# Compute similarity
similarity = np.dot(job_embedding, resume_embedding)
```

### Benchmark Performance

| Benchmark | Score |
|-----------|-------|
| MTEB Retrieval Average | ~66.9 NDCG@10 |
| vs all-MiniLM-L6-v2 | +10-15% on retrieval tasks |
| ConFit v2 (E5-base) | 84.44% Recall@5, 88.67% nDCG@10 |

### Comparison: e5-large-instruct vs all-MiniLM-L6-v2

| Aspect | e5-large-instruct | all-MiniLM-L6-v2 |
|--------|-------------------|------------------|
| Dimensions | 1024 | 384 |
| Parameters | 560M | 22M |
| Retrieval Accuracy | Higher | Lower (~56% top-5) |
| Inference Speed | Slower (30-50ms) | Faster (~15ms) |
| Memory | Higher (1.1-2.2GB) | Lower (~200MB) |
| Best For | Production quality | Resource-constrained |

### Recommendation for Resume-as-Code

**Primary Model:** `intfloat/multilingual-e5-large-instruct`
- Best accuracy for resume-JD matching
- Instruction-tuned for asymmetric retrieval
- Multilingual support for international resumes

**Fallback Model:** `sentence-transformers/all-MiniLM-L6-v2`
- For resource-constrained environments
- 4-5x faster, 75% smaller
- Accept ~10% accuracy degradation

---

## RB-050: Embedding Cache Invalidation Strategy

### Cache Key Design (Critical)

**Naive approach (WRONG):**
```python
cache_key = hash(input_text)  # Breaks when model changes!
```

**Correct approach:**
```python
import hashlib

def generate_cache_key(model_id: str, model_version: str, model_hash: str, input_text: str) -> str:
    """Generate cache key incorporating model versioning."""
    normalized_text = input_text.strip().lower()
    text_hash = hashlib.sha256(normalized_text.encode()).hexdigest()

    key_components = [model_id, model_version, model_hash, text_hash]
    key_string = "::".join(key_components)

    return hashlib.sha256(key_string.encode()).hexdigest()
```

### Model Hash Computation

```python
import hashlib
from sentence_transformers import SentenceTransformer

def compute_model_hash(model: SentenceTransformer) -> str:
    """Compute SHA-256 hash of model weights for cache key generation."""
    hasher = hashlib.sha256()

    # Iterate through model parameters in sorted order for deterministic hashing
    for name in sorted(model.state_dict().keys()):
        param = model.state_dict()[name]
        hasher.update(param.cpu().numpy().tobytes())

    return hasher.hexdigest()[:16]  # Use first 16 chars for shorter keys
```

**Optimization:** Compute model hash once at initialization, not per-cache-operation.

### Recommended Directory Structure

```
.resume-cache/
├── intfloat_multilingual-e5-large-instruct/
│   ├── v1_abc123def456/           # version_modelhash
│   │   ├── 00/
│   │   │   ├── 00a1b2c3d4e5.pkl
│   │   │   └── 00f6g7h8i9j0.pkl
│   │   ├── 01/
│   │   └── ...
│   ├── metadata.json
│   └── cache.db                   # SQLite index
└── sentence-transformers_all-MiniLM-L6-v2/
    └── ...
```

### SQLite Schema for Cache Management

```sql
CREATE TABLE embeddings (
    cache_key TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    model_hash TEXT NOT NULL,
    input_text TEXT NOT NULL,
    embedding BLOB NOT NULL,
    dtype TEXT NOT NULL,
    shape TEXT NOT NULL,
    timestamp REAL NOT NULL,
    compressed BOOLEAN DEFAULT 0
);

CREATE INDEX idx_model ON embeddings(model_id, model_version, model_hash);
CREATE INDEX idx_timestamp ON embeddings(timestamp);
```

### Serialization Format Recommendation

**For CLI tools (Resume-as-Code):** Pickle
- Fastest for numpy arrays
- Python-only is acceptable for CLI
- Security concerns mitigated by local-only operation

**Compression:** GZIP
- 40-60% compression ratio for embedding data
- Worth the CPU trade-off for storage savings

### Stale Cache Detection Strategies

1. **Model Hash Check:**
   ```python
   cached_model_hash = get_cached_model_hash(cache_key)
   current_model_hash = compute_model_hash(model)
   if cached_model_hash != current_model_hash:
       return None  # Cache miss, recompute
   ```

2. **TTL-Based Expiration (Optional):**
   - Useful for very dynamic content
   - Not typically needed for resume data

3. **Manual Invalidation:**
   - `resume cache clear` command
   - On model version upgrade

### Migration Strategy: MiniLM to e5-large-instruct

**Phase 1: Preparation**
- Deploy e5-large in shadow mode
- Generate new embeddings for all content alongside existing

**Phase 2: Parallel Caching**
- Maintain separate cache directories for each model
- Both models generate embeddings concurrently

**Phase 3: Validation**
- A/B test search quality between models
- Compare relevance scores on representative queries

**Phase 4: Switchover**
- Gradually transition traffic to new model
- Monitor quality metrics

**Phase 5: Cleanup**
- Remove old model cache directories
- Update configuration to use only new model

### Implementation for Resume-as-Code

```python
from pathlib import Path
import pickle
import gzip
import sqlite3
import hashlib
import time
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Optional

class EmbeddingCache:
    def __init__(self, cache_dir: Path, model: SentenceTransformer, model_id: str):
        self.cache_dir = cache_dir
        self.model = model
        self.model_id = model_id
        self.model_hash = self._compute_model_hash()

        # Setup cache structure
        self.model_cache_dir = cache_dir / f"{model_id.replace('/', '_')}"
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.model_cache_dir / "cache.db"
        self._init_database()

    def _compute_model_hash(self) -> str:
        hasher = hashlib.sha256()
        for name in sorted(self.model.state_dict().keys()):
            param = self.model.state_dict()[name]
            hasher.update(param.cpu().numpy().tobytes())
        return hasher.hexdigest()[:16]

    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                cache_key TEXT PRIMARY KEY,
                model_hash TEXT NOT NULL,
                embedding BLOB NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hash ON embeddings(model_hash)')
        conn.commit()
        conn.close()

    def get(self, text: str) -> Optional[np.ndarray]:
        cache_key = self._generate_key(text)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT embedding FROM embeddings WHERE cache_key = ? AND model_hash = ?',
            (cache_key, self.model_hash)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            return pickle.loads(gzip.decompress(result[0]))
        return None

    def put(self, text: str, embedding: np.ndarray):
        cache_key = self._generate_key(text)
        embedding_bytes = gzip.compress(pickle.dumps(embedding))

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO embeddings (cache_key, model_hash, embedding, timestamp) VALUES (?, ?, ?, ?)',
            (cache_key, self.model_hash, embedding_bytes, time.time())
        )
        conn.commit()
        conn.close()

    def _generate_key(self, text: str) -> str:
        normalized = text.strip().lower()
        return hashlib.sha256(f"{self.model_hash}::{normalized}".encode()).hexdigest()

    def clear_stale(self):
        """Remove embeddings from old model versions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM embeddings WHERE model_hash != ?', (self.model_hash,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted
```

---

## Integration Recommendations for Architecture

### Architecture Section 1.3 Updates

Add to Technology Stack:
```
| Embeddings | multilingual-e5-large-instruct | Best accuracy for job matching, instruction-tuned |
| Embeddings (fallback) | all-MiniLM-L6-v2 | CPU-only/resource-constrained environments |
| Ranking Fusion | RRF (k=60) | Standard hybrid search fusion method |
```

### services/ranker.py Implementation

The ranker should implement:
1. BM25 retrieval using `rank-bm25`
2. Semantic retrieval using `sentence-transformers` with e5-large-instruct
3. RRF fusion with k=60
4. Deterministic tie-breaking

### services/embedder.py Implementation

The embedder should implement:
1. Model loading with device detection (CUDA/CPU)
2. Proper prefix formatting (query/passage distinction)
3. Embedding cache integration
4. Model hash computation for cache keys

### Embedding Cache Location

- Default: `.resume-cache/` in project root
- Configurable via `config.yaml`:
  ```yaml
  cache:
    embeddings_dir: .resume-cache
    compression: true
    clear_on_model_change: true
  ```

---

## Performance Targets (NFR Validation)

**NFR1: `resume plan` < 3 seconds**
- BM25 retrieval: ~50-100ms for 100 work units
- Embedding retrieval (cached): ~10ms
- Embedding generation (uncached): ~30-50ms per text
- RRF fusion: ~5ms
- **Achievable with warm cache**

**Recommendation:** Pre-compute embeddings during `resume new work-unit` to ensure plan always has warm cache.

---

## Research Sources Summary

### RB-047 (RRF) Sources
- Milvus RRF documentation
- Microsoft Azure AI Search hybrid ranking
- OpenSearch hybrid search best practices
- MTEB evaluation framework

### RB-048 (e5-large-instruct) Sources
- Hugging Face model card (intfloat/multilingual-e5-large-instruct)
- MTEB leaderboard benchmarks
- Sentence-Transformers documentation
- ConFit v2 resume matching research

### RB-050 (Cache Invalidation) Sources
- Neptune.ai transformers caching
- Python pickle documentation
- Milvus embedding caching FAQ
- Semantic versioning specification

---

*Research completed 2026-01-10*
