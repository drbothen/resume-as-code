# Story 7.7: Evidence Model Enhancement

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **job seeker**,
I want **to store evidence without requiring URLs**,
So that **I can reference local artifacts, file hashes, and narrative descriptions**.

## Acceptance Criteria

1. **Given** evidence with only description (no URL)
   **When** I create a work unit
   **Then** validation passes
   **And** evidence is stored with type "narrative"

2. **Given** evidence with a URL
   **When** I create a work unit
   **Then** validation passes
   **And** evidence type is inferred (github, metrics, etc.)

3. **Given** evidence with file hash
   **When** I create a work unit
   **Then** it stores hash and optional local path
   **And** can be verified later

4. **Given** evidence types
   **When** I inspect the discriminated union
   **Then** supported types are:
   - `git_repo` - GitHub/GitLab repository (existing)
   - `metrics` - Dashboard/analytics URL (existing)
   - `document` - Publication with URL (existing)
   - `artifact` - Local file with optional hash (enhanced)
   - `narrative` - Text description only (new)
   - `link` - Generic HTTP/HTTPS link (new)

## Tasks / Subtasks

- [x] Task 1: Add NarrativeEvidence type (AC: #1)
  - [x] 1.1 Create `NarrativeEvidence` class with description-only field
  - [x] 1.2 Add to discriminated union
  - [x] 1.3 Update EvidenceType enum
  - [x] 1.4 Add unit tests for narrative evidence

- [x] Task 2: Add LinkEvidence type (AC: #2)
  - [x] 2.1 Create `LinkEvidence` class for generic URLs
  - [x] 2.2 Add to discriminated union
  - [x] 2.3 Update EvidenceType enum
  - [x] 2.4 Add unit tests for link evidence

- [x] Task 3: Enhance ArtifactEvidence (AC: #3)
  - [x] 3.1 Make `url` optional on ArtifactEvidence
  - [x] 3.2 Add `sha256: str | None` field for file hash
  - [x] 3.3 Add `local_path: str | None` field
  - [x] 3.4 Add validator requiring at least one of url, sha256, or local_path
  - [x] 3.5 Add unit tests for enhanced artifact evidence

- [x] Task 4: Ensure backward compatibility (AC: #2, #4)
  - [x] 4.1 Verify existing work units with URL-based evidence still validate
  - [x] 4.2 Update JSON schema generation (auto via Story 7.1)
  - [x] 4.3 Add migration notes for any breaking changes

- [x] Task 5: Add tests and quality checks
  - [x] 5.1 Unit tests for all new evidence types
  - [x] 5.2 Integration tests with WorkUnit model
  - [x] 5.3 Run `ruff check` and `mypy --strict`

## Dev Notes

### Current State Analysis

**Existing Implementation (work_unit.py:70-142):**

```python
# Current evidence types - ALL require URL
class EvidenceType(str, Enum):
    GIT_REPO = "git_repo"
    METRICS = "metrics"
    DOCUMENT = "document"
    ARTIFACT = "artifact"
    OTHER = "other"

class GitRepoEvidence(BaseModel):
    type: Literal["git_repo"] = "git_repo"
    url: HttpUrl  # REQUIRED
    branch: str | None = None
    commit_sha: str | None = None
    description: str | None = None

class ArtifactEvidence(BaseModel):
    type: Literal["artifact"] = "artifact"
    url: HttpUrl  # REQUIRED - this is the problem
    artifact_type: str | None = None
    description: str | None = None

# Discriminated union - no narrative option
Evidence = Annotated[
    GitRepoEvidence | MetricsEvidence | DocumentEvidence | ArtifactEvidence | OtherEvidence,
    Field(discriminator="type"),
]
```

**Gap:** Cannot store evidence for:
- Internal achievements without public URLs
- Local files/artifacts not hosted anywhere
- Verbal feedback or testimonials
- Conference talks before slides are published

### Implementation Pattern

**Enhanced EvidenceType Enum:**
```python
# models/work_unit.py
class EvidenceType(str, Enum):
    """Types of supporting evidence."""

    GIT_REPO = "git_repo"
    METRICS = "metrics"
    DOCUMENT = "document"
    ARTIFACT = "artifact"
    LINK = "link"        # NEW: generic URL
    NARRATIVE = "narrative"  # NEW: description-only
    OTHER = "other"  # DEPRECATED: use link or narrative
```

**New NarrativeEvidence Class:**
```python
class NarrativeEvidence(BaseModel):
    """Evidence based on narrative description only.

    Use for internal achievements, verbal feedback, or evidence
    that cannot be linked externally.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["narrative"] = "narrative"
    description: str = Field(
        ...,
        min_length=10,
        description="Narrative description of the evidence",
    )
    source: str | None = Field(
        default=None,
        description="Source of evidence (e.g., 'Manager feedback', 'Internal review')",
    )
    date_recorded: date | None = Field(
        default=None,
        description="When the evidence was recorded",
    )
```

**New LinkEvidence Class:**
```python
class LinkEvidence(BaseModel):
    """Evidence from a generic web link.

    Use for any HTTP/HTTPS URL that doesn't fit specific categories.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["link"] = "link"
    url: HttpUrl
    title: str | None = Field(
        default=None,
        description="Link title or label",
    )
    description: str | None = None
```

**Enhanced ArtifactEvidence Class:**
```python
class ArtifactEvidence(BaseModel):
    """Evidence from an artifact or release (package, binary, deployment).

    Can reference artifacts via URL, local path, or content hash.
    At least one of url, local_path, or sha256 must be provided.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["artifact"] = "artifact"
    url: HttpUrl | None = None  # NOW OPTIONAL
    local_path: str | None = Field(
        default=None,
        description="Local file path (relative to project root)",
    )
    sha256: str | None = Field(
        default=None,
        pattern=r"^[a-fA-F0-9]{64}$",
        description="SHA-256 hash of artifact for verification",
    )
    artifact_type: str | None = Field(
        default=None,
        description="Type of artifact (e.g., 'wheel', 'docker', 'pdf')",
    )
    description: str | None = None

    @model_validator(mode="after")
    def validate_at_least_one_reference(self) -> "ArtifactEvidence":
        """Ensure at least one reference method is provided."""
        if not any([self.url, self.local_path, self.sha256]):
            raise ValueError(
                "ArtifactEvidence requires at least one of: url, local_path, or sha256"
            )
        return self
```

**Updated Discriminated Union:**
```python
# Updated Evidence union with new types
Evidence = Annotated[
    GitRepoEvidence
    | MetricsEvidence
    | DocumentEvidence
    | ArtifactEvidence
    | LinkEvidence
    | NarrativeEvidence
    | OtherEvidence,
    Field(discriminator="type"),
]
```

### Testing Standards

```python
# tests/unit/models/test_evidence.py
import pytest
from pydantic import ValidationError

from resume_as_code.models.work_unit import (
    NarrativeEvidence,
    LinkEvidence,
    ArtifactEvidence,
    Evidence,
)


class TestNarrativeEvidence:
    """Tests for NarrativeEvidence model."""

    def test_valid_narrative_minimal(self) -> None:
        """Narrative evidence with only description."""
        evidence = NarrativeEvidence(
            description="Received positive feedback from VP of Engineering"
        )
        assert evidence.type == "narrative"
        assert evidence.source is None

    def test_valid_narrative_full(self) -> None:
        """Narrative evidence with all fields."""
        evidence = NarrativeEvidence(
            description="Led team to achieve 99.9% uptime for Q4 2024",
            source="Quarterly review",
            date_recorded="2024-12-15",
        )
        assert evidence.source == "Quarterly review"

    def test_narrative_requires_description(self) -> None:
        """Description is required for narrative evidence."""
        with pytest.raises(ValidationError, match="description"):
            NarrativeEvidence()

    def test_narrative_description_min_length(self) -> None:
        """Description must be at least 10 characters."""
        with pytest.raises(ValidationError, match="min_length"):
            NarrativeEvidence(description="Too short")


class TestLinkEvidence:
    """Tests for LinkEvidence model."""

    def test_valid_link_minimal(self) -> None:
        """Link evidence with only URL."""
        evidence = LinkEvidence(url="https://example.com/article")
        assert evidence.type == "link"
        assert evidence.title is None

    def test_valid_link_full(self) -> None:
        """Link evidence with all fields."""
        evidence = LinkEvidence(
            url="https://medium.com/@user/article-title",
            title="My Published Article",
            description="Article about microservices patterns",
        )
        assert evidence.title == "My Published Article"

    def test_link_requires_url(self) -> None:
        """URL is required for link evidence."""
        with pytest.raises(ValidationError, match="url"):
            LinkEvidence()


class TestArtifactEvidenceEnhanced:
    """Tests for enhanced ArtifactEvidence model."""

    def test_artifact_with_url_only(self) -> None:
        """Artifact evidence with URL only (backward compatible)."""
        evidence = ArtifactEvidence(url="https://pypi.org/project/mypackage")
        assert evidence.type == "artifact"
        assert evidence.sha256 is None

    def test_artifact_with_local_path_only(self) -> None:
        """Artifact evidence with local path only."""
        evidence = ArtifactEvidence(
            local_path="artifacts/report.pdf",
            artifact_type="pdf",
        )
        assert evidence.local_path == "artifacts/report.pdf"
        assert evidence.url is None

    def test_artifact_with_sha256_only(self) -> None:
        """Artifact evidence with SHA-256 hash only."""
        sha = "a" * 64  # Valid SHA-256 hex string
        evidence = ArtifactEvidence(
            sha256=sha,
            description="Deployment package",
        )
        assert evidence.sha256 == sha

    def test_artifact_with_all_references(self) -> None:
        """Artifact evidence with URL, path, and hash."""
        evidence = ArtifactEvidence(
            url="https://releases.example.com/v1.0.0.tar.gz",
            local_path="releases/v1.0.0.tar.gz",
            sha256="b" * 64,
            artifact_type="tarball",
        )
        assert evidence.url is not None
        assert evidence.local_path is not None

    def test_artifact_requires_at_least_one_reference(self) -> None:
        """Must provide at least one of url, local_path, or sha256."""
        with pytest.raises(ValidationError, match="at least one"):
            ArtifactEvidence(description="Missing all references")

    def test_artifact_sha256_format_validation(self) -> None:
        """SHA-256 must be valid 64-character hex string."""
        with pytest.raises(ValidationError, match="pattern"):
            ArtifactEvidence(sha256="invalid-hash")

        with pytest.raises(ValidationError, match="pattern"):
            ArtifactEvidence(sha256="abc123")  # Too short


class TestEvidenceDiscriminatedUnion:
    """Tests for Evidence discriminated union."""

    def test_narrative_in_union(self) -> None:
        """Narrative evidence works in union."""
        from pydantic import TypeAdapter

        adapter = TypeAdapter(Evidence)
        data = {"type": "narrative", "description": "Internal achievement documented"}
        evidence = adapter.validate_python(data)
        assert isinstance(evidence, NarrativeEvidence)

    def test_link_in_union(self) -> None:
        """Link evidence works in union."""
        from pydantic import TypeAdapter

        adapter = TypeAdapter(Evidence)
        data = {"type": "link", "url": "https://example.com"}
        evidence = adapter.validate_python(data)
        assert isinstance(evidence, LinkEvidence)

    def test_artifact_without_url_in_union(self) -> None:
        """Enhanced artifact evidence works in union."""
        from pydantic import TypeAdapter

        adapter = TypeAdapter(Evidence)
        data = {
            "type": "artifact",
            "local_path": "artifacts/build.log",
            "description": "Build log",
        }
        evidence = adapter.validate_python(data)
        assert isinstance(evidence, ArtifactEvidence)
        assert evidence.url is None
```

### Example Work Unit with New Evidence Types

```yaml
# work-units/wu-2024-06-15-internal-achievement.yaml
id: wu-2024-06-15-internal-achievement
title: "Led infrastructure cost optimization initiative"
position_id: pos-acme-senior-engineer

problem:
  statement: "Cloud infrastructure costs exceeded budget by 40%"
  context: "Growing startup with aggressive expansion"

actions:
  - "Analyzed AWS cost explorer data across all accounts"
  - "Identified underutilized resources and right-sizing opportunities"
  - "Implemented automated scaling policies"

outcome:
  result: "Reduced monthly cloud spend by $150K"
  quantified_impact: "35% cost reduction within 3 months"

evidence:
  # Narrative evidence - no URL needed
  - type: narrative
    description: "Recognized in company all-hands for cost savings initiative"
    source: "CEO presentation Q3 2024"

  # Local artifact with hash
  - type: artifact
    local_path: "artifacts/cost-analysis-report.pdf"
    sha256: "a3f2b8c9d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1"
    artifact_type: "pdf"
    description: "Internal cost analysis report"

  # Generic link to blog post
  - type: link
    url: "https://company-blog.example.com/cost-optimization"
    title: "How We Cut Cloud Costs by 35%"
    description: "Public blog post about the initiative"
```

### Project Context Rules

From `project-context.md`:
- Run `ruff check` and `mypy --strict` before completing
- Use Rich console for CLI output, never `print()`
- Type hints required on all public functions
- Use `|` union syntax (Python 3.10+)
- Use `model_config = ConfigDict(extra="forbid")` on all Pydantic models

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-7-schema-data-model-refactoring.md#Story 7.7]
- [Source: src/resume_as_code/models/work_unit.py:70-142 - existing Evidence models]
- [Source: src/resume_as_code/models/work_unit.py:138-142 - Evidence discriminated union]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- ✅ Added `NarrativeEvidence` class with description (min 10 chars), source, and date_recorded fields
- ✅ Added `LinkEvidence` class with url (required), title, and description fields
- ✅ Enhanced `ArtifactEvidence` with optional url, local_path, and sha256 fields
- ✅ Added model_validator to ensure at least one reference (url, local_path, or sha256) is provided
- ✅ Updated EvidenceType enum to include LINK and NARRATIVE
- ✅ Updated Evidence discriminated union to include all 7 types
- ✅ JSON schema auto-regenerated via scripts/generate_schemas.py
- ✅ All 36 evidence-specific tests pass (including path validation)
- ✅ All 1880 project tests pass (no regressions)
- ✅ Backward compatibility verified - existing URL-only ArtifactEvidence still works
- ✅ ruff check: All checks passed
- ✅ mypy --strict: no issues found

**Migration Notes:** No breaking changes. Existing work units with URL-based evidence continue to work. New evidence types (narrative, link) and enhanced artifact fields are purely additive.

**Code Review Fixes Applied:**
- Added `local_path` validation to reject absolute paths (Unix `/`, `~`, Windows `C:\`)
- Added 4 tests for path validation (unix, home dir, windows, relative paths)
- Added deprecation note to `OtherEvidence` docstring
- Improved `LinkEvidence` documentation with examples and usage guidance
- Fixed `Field()` wrapper consistency on `ArtifactEvidence.description` and `LinkEvidence.description`

### File List

- src/resume_as_code/models/work_unit.py (modified - added NarrativeEvidence, LinkEvidence, enhanced ArtifactEvidence, added local_path validation)
- tests/unit/models/test_evidence.py (new - 36 tests for evidence types including path validation)
- tests/unit/test_work_unit_schema.py (modified - updated evidence type tests)
- schemas/work-unit.schema.json (regenerated - includes new evidence types)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified - story status tracking)

