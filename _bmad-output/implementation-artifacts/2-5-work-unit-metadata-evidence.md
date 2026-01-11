# Story 2.5: Work Unit Metadata & Evidence

Status: done

## Story

As a **user**,
I want **to enrich Work Units with confidence levels, tags, and evidence links**,
So that **I can indicate certainty and provide proof of my claims**.

## Acceptance Criteria

1. **Given** a Work Unit YAML file
   **When** I set `confidence: high`
   **Then** the value is validated as one of: `high`, `medium`, `low`

2. **Given** a Work Unit YAML file
   **When** I add tags like `tags: [python, incident-response, leadership]`
   **Then** the tags are stored as a list of strings
   **And** they can be used for filtering later

3. **Given** a Work Unit YAML file
   **When** I add evidence links
   **Then** I can specify `evidence` as a list with `type`, `url`, and optional `description`
   **And** valid types include: `git_repo`, `metrics`, `document`, `artifact`, `other`
   **And** each type has type-specific optional fields (branch, commit_sha, dashboard_name, etc.)

4. **Given** I validate a Work Unit with invalid confidence value
   **When** validation runs
   **Then** a clear error message indicates valid options

5. **Given** I validate a Work Unit with evidence
   **When** the evidence has a `url` field
   **Then** basic URL format validation is performed

## Tasks / Subtasks

- [x] Task 1: Update JSON Schema for metadata fields (AC: #1, #2, #3)
  - [x] 1.1: Add `confidence` enum field to `schemas/work-unit.schema.json`
  - [x] 1.2: Add `tags` array of strings field
  - [x] 1.3: Add `evidence` array with object schema (type, url, description)
  - [x] 1.4: Define evidence type enum: `git_repo`, `metrics`, `document`, `artifact`, `other`
  - [x] 1.5: Mark URL format validation for evidence url field

- [x] Task 2: Update Pydantic models (AC: #1, #2, #3, #4, #5)
  - [x] 2.1: Create `ConfidenceLevel` enum (`high`, `medium`, `low`)
  - [x] 2.2: Create `EvidenceType` enum
  - [x] 2.3: Create `Evidence` model with type, url, description
  - [x] 2.4: Add URL validation using `pydantic.HttpUrl` or `@field_validator`
  - [x] 2.5: Add `confidence`, `tags`, `evidence` fields to WorkUnit model
  - [x] 2.6: Make all metadata fields optional with sensible defaults

- [x] Task 3: Update archetype templates (AC: #1, #2, #3)
  - [x] 3.1: Add commented-out metadata examples to all archetypes
  - [x] 3.2: Include confidence field pre-set in minimal archetype
  - [x] 3.3: Add example evidence block with all types documented

- [x] Task 4: Implement validation error messages (AC: #4, #5)
  - [x] 4.1: Create descriptive error for invalid confidence values
  - [x] 4.2: Create descriptive error for invalid evidence types
  - [x] 4.3: Create descriptive error for malformed URLs

- [x] Task 5: Code quality verification
  - [x] 5.1: Run `ruff check src tests --fix`
  - [x] 5.2: Run `ruff format src tests`
  - [x] 5.3: Run `mypy src --strict` with zero errors
  - [x] 5.4: Add unit tests for metadata validation
  - [x] 5.5: Add unit tests for evidence URL validation

## Dev Notes

### Architecture Compliance

This story extends the Work Unit schema with metadata fields for confidence tracking, tagging, and evidence linking. These enable filtering (Story 3.3) and support resume credibility with verifiable evidence.

**Source:** [epics.md#Story 2.5](_bmad-output/planning-artifacts/epics.md)
**Source:** [Architecture Section 3.2 - Data Architecture](_bmad-output/planning-artifacts/architecture.md#32-data-architecture)

### Dependencies

This story REQUIRES:
- Story 2.1 (Work Unit Schema & Pydantic Model) - Base schema and models including evidence types

This story ENABLES:
- Story 3.3 (List Command & Filtering) - Filter by tags and confidence

**Note:** Story 2.1 defines the complete evidence type system with discriminated unions (git_repo, metrics, document, artifact, other). This story adds the confidence and tags fields to complement that foundation.

### Schema Updates

**Update `schemas/work-unit.schema.json`:**

Add the following definitions and properties:

```json
{
  "$defs": {
    "EvidenceType": {
      "type": "string",
      "enum": ["git_repo", "metrics", "document", "artifact", "other"]
    },
    "ConfidenceLevel": {
      "type": "string",
      "enum": ["high", "medium", "low"]
    },
    "Evidence": {
      "type": "object",
      "properties": {
        "type": { "$ref": "#/$defs/EvidenceType" },
        "url": {
          "type": "string",
          "format": "uri"
        },
        "description": {
          "type": "string"
        }
      },
      "required": ["type", "url"]
    }
  },
  "properties": {
    "confidence": {
      "$ref": "#/$defs/ConfidenceLevel",
      "description": "Confidence level in the accuracy of this Work Unit"
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Tags for categorization and filtering"
    },
    "evidence": {
      "type": "array",
      "items": { "$ref": "#/$defs/Evidence" },
      "description": "Links to supporting evidence"
    }
  }
}
```

### Pydantic Model Implementation

**Note:** Story 2.1 already defines the complete evidence type system with discriminated unions (`GitRepoEvidence`, `MetricsEvidence`, `DocumentEvidence`, `ArtifactEvidence`, `OtherEvidence`). This story adds the `WorkUnitConfidence` enum and `tags` validation.

**Add to `src/resume_as_code/models/work_unit.py`:**

```python
"""Work Unit metadata additions - extends Story 2.1 models."""

from __future__ import annotations

from enum import Enum

from pydantic import Field, field_validator


class WorkUnitConfidence(str, Enum):
    """Overall confidence level in Work Unit accuracy."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Add to existing WorkUnit model from Story 2.1:
class WorkUnit(BaseModel):
    """Work Unit with metadata fields."""

    # ... existing fields from Story 2.1 ...

    # Metadata fields added by this story
    confidence: WorkUnitConfidence | None = Field(
        default=None,
        description="Confidence level in accuracy (high, medium, low)",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization and filtering",
    )
    # evidence: list[Evidence] is already defined in Story 2.1

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: list[str]) -> list[str]:
        """Normalize tags to lowercase."""
        return [tag.lower().strip() for tag in v]
```

**EvidenceType enum (reference from Story 2.1):**
```python
class EvidenceType(str, Enum):
    """Types of supporting evidence - defined in Story 2.1."""

    GIT_REPO = "git_repo"
    METRICS = "metrics"
    DOCUMENT = "document"
    ARTIFACT = "artifact"
    OTHER = "other"
```

### Archetype Template Updates

**Example metadata block to add to all archetypes:**

```yaml
# --- Metadata (optional) ---
confidence: high  # high | medium | low - how certain are you about the details?

tags:
  - python
  - incident-response
  - leadership

evidence:
  - type: git_repo
    url: "https://github.com/org/repo"
    description: "Source code for the solution"
  - type: metrics
    url: "https://dashboard.example.com/metrics"
    description: "Performance dashboard showing improvement"
  - type: document
    url: "https://confluence.example.com/page/123"
    description: "Architecture decision record"
```

### Evidence Type Reference

| Type | Use Case | Type-Specific Fields |
|------|----------|---------------------|
| `git_repo` | Code repositories (GitHub, GitLab, Bitbucket) | `branch`, `commit_sha` |
| `metrics` | Dashboards, analytics (Grafana, Datadog, GA4) | `dashboard_name`, `metric_names` |
| `document` | Documentation, articles (Confluence, Notion, blogs) | `title`, `publication_date` |
| `artifact` | Artifacts, releases (S3, package registries) | `artifact_type` |
| `other` | Anything else (Slack threads, email archives) | (none) |

All types share: `url` (required), `description` (optional)

### Testing Requirements

**`tests/unit/test_work_unit_models.py`:**

```python
"""Tests for Work Unit metadata validation."""

import pytest
from pydantic import ValidationError

from resume_as_code.models.work_unit import (
    WorkUnitConfidence,
    GitRepoEvidence,
    EvidenceType,
    Outcome,
    Problem,
    WorkUnit,
)


class TestWorkUnitConfidence:
    """Test confidence level validation."""

    def test_valid_confidence_values(self):
        """Should accept high, medium, low."""
        for level in ["high", "medium", "low"]:
            assert WorkUnitConfidence(level) is not None

    def test_invalid_confidence_value(self):
        """Should reject invalid confidence values."""
        with pytest.raises(ValueError):
            WorkUnitConfidence("super-high")


class TestEvidence:
    """Test evidence validation (types defined in Story 2.1)."""

    def test_valid_git_repo_evidence(self):
        """Should accept valid git repo evidence."""
        evidence = GitRepoEvidence(
            url="https://github.com/org/repo",
            branch="main",
            description="Source code",
        )
        assert evidence.type == "git_repo"
        assert evidence.url.host == "github.com"

    def test_invalid_url(self):
        """Should reject invalid URLs."""
        with pytest.raises(ValidationError):
            GitRepoEvidence(url="not-a-valid-url")

    def test_all_evidence_types(self):
        """Should accept all defined evidence types."""
        for etype in EvidenceType:
            # Verify enum values exist
            assert etype.value in ["git_repo", "metrics", "document", "artifact", "other"]


class TestWorkUnitMetadata:
    """Test Work Unit metadata fields."""

    def test_tags_normalized(self):
        """Tags should be normalized to lowercase."""
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Test work unit title",
            problem=Problem(statement="This is the problem statement"),
            actions=["Action taken here"],
            outcome=Outcome(result="Result achieved"),
            tags=["Python", "AWS", "Incident-Response"],
        )
        assert wu.tags == ["python", "aws", "incident-response"]

    def test_empty_metadata_defaults(self):
        """Metadata fields should have sensible defaults."""
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Test work unit title",
            problem=Problem(statement="This is the problem statement"),
            actions=["Action taken here"],
            outcome=Outcome(result="Result achieved"),
        )
        assert wu.confidence is None
        assert wu.tags == []
        assert wu.evidence == []
```

### Verification Commands

```bash
# Validate a Work Unit with metadata
cat > work-units/wu-test-metadata.yaml << 'EOF'
schema_version: "1.0.0"
id: "wu-2026-01-10-test-metadata"
title: "Test Metadata"

problem:
  statement: "Testing metadata fields"

actions:
  - "Added tests"

outcome:
  result: "All tests pass"

confidence: high
tags:
  - testing
  - metadata
evidence:
  - type: git_repo
    url: "https://github.com/example/repo"
    description: "Test repository"
EOF

# Validate
resume validate work-units/wu-test-metadata.yaml

# Test invalid confidence
sed -i '' 's/confidence: high/confidence: super-high/' work-units/wu-test-metadata.yaml
resume validate work-units/wu-test-metadata.yaml  # Should fail with helpful message

# Code quality
ruff check src tests --fix
mypy src --strict
pytest tests/unit/test_work_unit_metadata.py -v

# Cleanup
rm work-units/wu-test-metadata.yaml
```

### References

- [Source: epics.md#Story 2.5](_bmad-output/planning-artifacts/epics.md)
- [Source: architecture.md#Section 3.2 - Data Architecture](_bmad-output/planning-artifacts/architecture.md)
- [Source: project-context.md](_bmad-output/project-context.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - Implementation completed without issues.

### Completion Notes List

- **Story 2.1 Pre-implementation:** JSON Schema and Pydantic models were already implemented in Story 2.1, including `confidence`, `tags`, `evidence` fields with discriminated union evidence types.
- **Story 2.2 Pre-implementation:** Archetype templates already contain metadata examples (confidence, tags, evidence) from Story 2.2.
- **Tag Normalization:** Added `normalize_tags` field validator to WorkUnit model per AC requirements - normalizes tags to lowercase, strips whitespace, filters empty strings, and deduplicates.
- **Tests Added:** 13 tests in `test_work_unit_models.py`:
  - `TestTagNormalization`: 7 tests for lowercase normalization, whitespace stripping, default empty list, empty string filtering, whitespace-only filtering, deduplication, and order preservation
  - `TestMetadataDefaults`: 3 tests for confidence default (None), evidence default (empty list), and all fields optional
  - `TestMetadataValidation`: 3 tests for invalid confidence, invalid URL, and valid confidence values
- **Code Quality:** All tests pass, mypy --strict passes, ruff check/format passes.
- **Code Review Remediation (2026-01-11):** Fixed tag normalization to filter empty strings and deduplicate; added 4 edge case tests.

### File List

- `src/resume_as_code/models/work_unit.py` - Added `normalize_tags` field validator (updated to filter empty/deduplicate)
- `tests/unit/test_work_unit_models.py` - Added 13 tests (TestTagNormalization: 7, TestMetadataDefaults: 3, TestMetadataValidation: 3)

### Change Log

- 2026-01-11: Implemented Story 2.5 - Added tag normalization validator and comprehensive metadata tests
- 2026-01-11: Code Review Remediation - Fixed normalize_tags to filter empty strings and deduplicate; added 4 edge case tests

