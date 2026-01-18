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

### TD-005: Directory-Based Sharding for Data Files
**Identified:** 2026-01-18
**Story:** Post-9.2 Enhancement
**Severity:** LOW
**Location:** `src/resume_as_code/data_loader.py`, `src/resume_as_code/commands/new.py`

**Problem:**
Currently, data files (certifications, education, publications, board-roles, highlights) are stored as single YAML files containing all items. For users with large collections (20+ items) or those who prefer per-item version control, this can be limiting compared to the work unit sharding pattern.

**Current Behavior:**
```
certifications.yaml      # Contains all certifications as a list
education.yaml           # Contains all education entries as a list
publications.yaml        # Contains all publications as a list
board-roles.yaml         # Contains all board roles as a list
highlights.yaml          # Contains all highlights as a list
```

**Proposed Enhancement:**
Support optional directory-based storage (similar to `work-units/`):

```
certifications/
├── cert-2023-06-aws-solutions-architect.yaml
├── cert-2022-11-cissp.yaml
└── cert-2021-03-cka.yaml

publications/
├── pub-2023-10-scaling-engineering-teams.yaml
├── pub-2022-06-zero-trust-architecture.yaml
└── pub-2021-03-devops-practices.yaml

education/
├── edu-2016-stanford-mba.yaml
└── edu-2012-utaustin-bs-cs.yaml

board-roles/
├── board-2022-03-cybershield-ventures.yaml
└── board-2020-01-techstars-austin.yaml

highlights/
├── hl-001-digital-transformation.yaml
└── hl-002-engineering-org-scaling.yaml
```

**Implementation Requirements:**
1. Add `*_dir` config options: `certifications_dir`, `publications_dir`, `education_dir`, `board_roles_dir`, `highlights_dir`
2. Create generic `DataTypeLoader` class following `WorkUnitLoader` pattern
3. Update `data_loader.py` with three-tier fallback: directory → single file → embedded
4. Update CLI commands (`new`, `list`, `show`, `remove`) to support both modes
5. Add migration support (single file → sharded directory)
6. Define ID patterns per type:
   - Certifications: `cert-YYYY-MM-{slug}.yaml`
   - Publications: `pub-YYYY-MM-{slug}.yaml`
   - Education: `edu-YYYY-{institution-slug}.yaml`
   - Board Roles: `board-YYYY-MM-{org-slug}.yaml`
   - Highlights: `hl-NNN-{slug}.yaml`

**Benefits:**
- Fine-grained version control per item
- Parallel editing friendly (no merge conflicts)
- Natural caching at item level
- Consistent with work unit pattern
- Per-item metadata possible (created_date, modified_date)

**Considerations:**
- Most users have 3-15 items per category (sharding may be overkill)
- Adds complexity to data loading
- Should remain optional, not replace single-file mode

**Impact:**
- Not blocking any features
- Enhancement for power users with large collections
- Aligns data management patterns across all entity types

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
