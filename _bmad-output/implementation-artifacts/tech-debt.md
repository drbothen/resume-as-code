# Technical Debt Tracking

This file tracks identified technical debt and performance improvements to be addressed in future sprints.

---

## Performance Optimizations

### TD-001: Batch Embedding for Certifications
**Identified:** 2026-01-16
**Story:** 7-14 (JD-Relevant Content Curation)
**Severity:** LOW
**Location:** `src/resume_as_code/services/content_curator.py:214-232`

**Problem:**
For each certification, a new embedding is computed via `embed_query()`. With many certifications (e.g., 20+), this could become slow since each call is a separate model inference.

**Current Behavior:**
```python
for cert in candidates:
    cert_text = f"{cert.name} {cert.issuer or ''}"
    cert_emb = self.embedder.embed_query(cert_text)  # Individual call per cert
    semantic_score = self._cosine_similarity(cert_emb, jd_embedding)
```

**Proposed Fix:**
1. Add `embed_queries_batch()` method to EmbeddingService that accepts a list of strings
2. Compute all certification embeddings in a single batch call
3. Apply same optimization to board_roles and highlights if they exceed a threshold (e.g., 10+ items)

**Impact:**
- Would reduce N embedding calls to 1 batch call
- Estimated 5-10x speedup for users with 20+ certifications
- Not blocking any features, purely performance improvement

---

## Code Quality

*(No items currently)*

---

## Architecture

*(No items currently)*
