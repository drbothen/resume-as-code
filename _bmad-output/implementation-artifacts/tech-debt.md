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

---

## CI/CD

### TD-002: GitHub Actions Slow Test Timeout
**Identified:** 2026-01-18
**Story:** 10-1 (PyPI Package Distribution)
**Severity:** MEDIUM
**Location:** `.github/workflows/ci.yml`, `.github/workflows/release.yml`

**Problem:**
GitHub Actions runners are being shutdown during test execution, particularly during integration tests (`test_plan_command.py`, `test_build_command.py`). Current workaround skips these tests in CI entirely.

**Current Behavior:**
```yaml
run: uv run pytest -v -m "not slow" --ignore=tests/integration/test_plan_command.py --ignore=tests/integration/test_build_command.py
```

**Proposed Fix:**
1. Investigate why runners are being terminated (resource limits, timeouts)
2. Consider splitting integration tests into smaller, faster units
3. Add test parallelization with pytest-xdist
4. Configure appropriate timeouts per test category
5. Re-enable full test suite in CI once stable

**Impact:**
- Integration tests only run locally, not in CI
- Reduced confidence in PR validation
- Potential for regressions in plan/build commands

---

### TD-003: TestPyPI Trusted Publisher Configuration
**Identified:** 2026-01-18
**Story:** 10-1 (PyPI Package Distribution)
**Severity:** LOW
**Location:** `.github/workflows/release.yml`, TestPyPI account settings

**Problem:**
TestPyPI trusted publisher needs to be configured for `resume-as-code-ng` (same name as PyPI). Currently TestPyPI publish step fails in release workflow.

**Current Behavior:**
Release workflow publishes to PyPI successfully but TestPyPI step fails, causing smoke test to be skipped.

**Proposed Fix:**
1. Configure trusted publisher on TestPyPI for `resume-as-code-ng`:
   - Owner: `drbothen`
   - Repository: `resume-as-code`
   - Workflow: `release.yml`
   - Environment: `testpypi`
2. Verify with next release (0.1.1+)

**Impact:**
- No pre-release smoke testing on TestPyPI
- Reduced confidence before PyPI publish
- Not blocking releases since PyPI publish works

---

### TD-004: PyPI Logo Not Displaying
**Identified:** 2026-01-18
**Story:** 10-1 (PyPI Package Distribution)
**Severity:** LOW
**Location:** `README.md`, `pyproject.toml`

**Problem:**
Project logo is not displaying correctly on the PyPI package page.

**Current Behavior:**
Logo either missing or broken on https://pypi.org/project/resume-as-code-ng/

**Proposed Fix:**
1. Ensure logo image is accessible via absolute URL (not relative path)
2. Use raw GitHub URL for the image: `https://raw.githubusercontent.com/drbothen/resume-as-code/main/docs/assets/logo.png`
3. Verify image format is supported (PNG/SVG recommended)
4. Check README.md renders correctly with `python -m readme_renderer README.md`

**Impact:**
- Reduced visual appeal on PyPI
- Less professional appearance
- Purely cosmetic, not blocking functionality
