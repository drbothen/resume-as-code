# Story 2.1: Work Unit Schema & Pydantic Model

Status: done

> **Note:** This is an **enabling story** that provides infrastructure for user-facing stories 2.3-2.5. It does not deliver direct user value but is required for subsequent stories.

## Story

As a **developer**,
I want **a well-defined Work Unit data structure with validation**,
So that **all Work Units follow a consistent, validated format**.

## Acceptance Criteria

1. **Given** the schemas directory exists
   **When** I inspect `schemas/work-unit.schema.json`
   **Then** I find a valid JSON Schema with required fields: `id`, `title`, `problem`, `actions`, `outcome`
   **And** optional fields include: `time_started`, `time_ended`, `skills_demonstrated`, `confidence`, `tags`, `evidence`

2. **Given** the Work Unit Pydantic model exists
   **When** I create a WorkUnit instance with valid data
   **Then** the model validates successfully
   **And** all fields are properly typed

3. **Given** I create a WorkUnit with missing required fields
   **When** validation runs
   **Then** a ValidationError is raised with specific field information

4. **Given** the Work Unit has a `problem` field
   **When** I inspect the schema
   **Then** `problem` contains `statement` (required) and optional `constraints`, `context`

5. **Given** the Work Unit has an `outcome` field
   **When** I inspect the schema
   **Then** `outcome` contains `result` (required) and optional `quantified_impact`, `business_value`

6. **Given** the Work Unit schema supports executive-level content
   **When** I inspect the schema
   **Then** optional `scope` fields exist: `budget_managed`, `team_size`, `revenue_influenced`, `geographic_reach`
   **And** optional `impact_category` supports: `financial`, `operational`, `talent`, `customer`, `organizational`
   **And** optional `metrics` supports: `baseline`, `outcome`, `percentage_change`
   **And** optional `framing` supports: `action_verb`, `strategic_context`

7. **Given** the Work Unit schema supports confidence for partial recall
   **When** I inspect the schema
   **Then** optional `confidence` field in result supports: `exact`, `estimated`, `approximate`, `order_of_magnitude`
   **And** optional `confidence_note` provides explanation for non-exact values

8. **Given** evidence types require validation
   **When** I inspect the Pydantic model
   **Then** evidence uses discriminated unions with `type` field as discriminator
   **And** each evidence type (git_repo, metrics, document, artifact, other) has type-specific fields

## Tasks / Subtasks

- [x] Task 1: Create JSON Schema file (AC: #1, #4, #5, #6, #7)
  - [x] 1.1: Create `schemas/work-unit.schema.json`
  - [x] 1.2: Define required fields: `id`, `title`, `problem`, `actions`, `outcome`
  - [x] 1.3: Define `problem` object with `statement` (required), `constraints`, `context`
  - [x] 1.4: Define `outcome` object with `result` (required), `quantified_impact`, `business_value`
  - [x] 1.5: Add optional time fields: `time_started`, `time_ended`
  - [x] 1.6: Add optional metadata: `skills_demonstrated`, `confidence`, `tags`, `evidence`
  - [x] 1.7: Add executive-level fields: `scope`, `impact_category`, `metrics`, `framing`
  - [x] 1.8: Add schema version field for future migrations

- [x] Task 2: Create base Pydantic models (AC: #2, #3)
  - [x] 2.1: Create `src/resume_as_code/models/work_unit.py`
  - [x] 2.2: Implement `Problem` model with `statement`, `constraints`, `context`
  - [x] 2.3: Implement `Outcome` model with `result`, `quantified_impact`, `business_value`
  - [x] 2.4: Implement `WorkUnit` model with all required and optional fields
  - [x] 2.5: Add proper type hints using `|` union syntax

- [x] Task 3: Implement evidence discriminated unions (AC: #8)
  - [x] 3.1: Create `EvidenceBase` model with `type` discriminator
  - [x] 3.2: Implement `GitRepoEvidence` with `url`, `branch`, `commit_sha`
  - [x] 3.3: Implement `MetricsEvidence` with `url`, `dashboard_name`, `metric_names`
  - [x] 3.4: Implement `DocumentEvidence` with `url`, `title`, `publication_date`
  - [x] 3.5: Implement `ArtifactEvidence` with `url`, `artifact_type`
  - [x] 3.6: Implement `OtherEvidence` with `url`, `description`
  - [x] 3.7: Create `Evidence` type alias using `Annotated[Union[...], Field(discriminator='type')]`

- [x] Task 4: Implement executive-level fields (AC: #6)
  - [x] 4.1: Create `Scope` model with `budget_managed`, `team_size`, `revenue_influenced`, `geographic_reach`
  - [x] 4.2: Create `ImpactCategory` enum: `financial`, `operational`, `talent`, `customer`, `organizational`
  - [x] 4.3: Create `Metrics` model with `baseline`, `outcome`, `percentage_change`
  - [x] 4.4: Create `Framing` model with `action_verb`, `strategic_context`

- [x] Task 5: Implement confidence fields (AC: #7)
  - [x] 5.1: Create `ConfidenceLevel` enum: `exact`, `estimated`, `approximate`, `order_of_magnitude`
  - [x] 5.2: Add `confidence` field to `Outcome.result`
  - [x] 5.3: Add `confidence_note` optional field

- [x] Task 6: Add field validators (AC: #2, #3)
  - [x] 6.1: Add `@field_validator` for action verb strength checking
  - [x] 6.2: Add `@model_validator(mode='after')` for cross-field validation
  - [x] 6.3: Validate URL format in evidence fields
  - [x] 6.4: Validate date formats in time fields

- [x] Task 7: Code quality verification
  - [x] 7.1: Run `ruff check src tests --fix`
  - [x] 7.2: Run `ruff format src tests`
  - [x] 7.3: Run `mypy src --strict` with zero errors
  - [x] 7.4: Add comprehensive unit tests for model validation
  - [x] 7.5: Test JSON Schema validation matches Pydantic validation

## Dev Notes

### Architecture Compliance

This story creates the core data model that ALL Work Unit operations depend on. The schema must support both basic and executive-level content.

**Source:** [Architecture Section 3.2 - Data Architecture](_bmad-output/planning-artifacts/architecture.md#32-data-architecture)
**Source:** [Architecture Section 1.4 - Content Strategy Standards](_bmad-output/planning-artifacts/architecture.md#14-content-strategy-standards)

### Dependencies

This story REQUIRES:
- Story 1.1 (Project Scaffolding) - Package structure exists

This story ENABLES:
- Story 2.2 (Archetype Templates)
- Story 2.3 (Create Work Unit Command)
- Story 2.4 (Quick Capture Mode)
- Story 2.5 (Work Unit Metadata & Evidence)

### JSON Schema Structure

**`schemas/work-unit.schema.json`:**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://resume-as-code.dev/schemas/work-unit.schema.json",
  "title": "Work Unit",
  "description": "A documented instance of applied capability",
  "type": "object",
  "required": ["id", "title", "problem", "actions", "outcome"],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "1.0.0"
    },
    "id": {
      "type": "string",
      "pattern": "^wu-\\d{4}-\\d{2}-\\d{2}-[a-z0-9-]+$",
      "description": "Unique identifier: wu-YYYY-MM-DD-slug"
    },
    "title": {
      "type": "string",
      "minLength": 10,
      "maxLength": 200
    },
    "problem": {
      "type": "object",
      "required": ["statement"],
      "properties": {
        "statement": { "type": "string", "minLength": 20 },
        "constraints": { "type": "array", "items": { "type": "string" } },
        "context": { "type": "string" }
      }
    },
    "actions": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string", "minLength": 10 }
    },
    "outcome": {
      "type": "object",
      "required": ["result"],
      "properties": {
        "result": { "type": "string", "minLength": 10 },
        "quantified_impact": { "type": "string" },
        "business_value": { "type": "string" },
        "confidence": {
          "type": "string",
          "enum": ["exact", "estimated", "approximate", "order_of_magnitude"]
        },
        "confidence_note": { "type": "string" }
      }
    },
    "time_started": {
      "type": "string",
      "format": "date"
    },
    "time_ended": {
      "type": "string",
      "format": "date"
    },
    "skills_demonstrated": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name"],
        "properties": {
          "name": { "type": "string" },
          "onet_element_id": { "type": "string", "pattern": "^\\d+\\.\\w+(\\.\\d+)*$" },
          "proficiency_level": { "type": "integer", "minimum": 1, "maximum": 7 }
        }
      }
    },
    "confidence": {
      "type": "string",
      "enum": ["high", "medium", "low"]
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" }
    },
    "evidence": {
      "type": "array",
      "items": {
        "oneOf": [
          {
            "type": "object",
            "required": ["type", "url"],
            "properties": {
              "type": { "const": "git_repo" },
              "url": { "type": "string", "format": "uri" },
              "branch": { "type": "string" },
              "commit_sha": { "type": "string" },
              "description": { "type": "string" }
            }
          },
          {
            "type": "object",
            "required": ["type", "url"],
            "properties": {
              "type": { "const": "metrics" },
              "url": { "type": "string", "format": "uri" },
              "dashboard_name": { "type": "string" },
              "metric_names": { "type": "array", "items": { "type": "string" } },
              "description": { "type": "string" }
            }
          },
          {
            "type": "object",
            "required": ["type", "url"],
            "properties": {
              "type": { "const": "document" },
              "url": { "type": "string", "format": "uri" },
              "title": { "type": "string" },
              "publication_date": { "type": "string", "format": "date" },
              "description": { "type": "string" }
            }
          },
          {
            "type": "object",
            "required": ["type", "url"],
            "properties": {
              "type": { "const": "artifact" },
              "url": { "type": "string", "format": "uri" },
              "artifact_type": { "type": "string" },
              "description": { "type": "string" }
            }
          },
          {
            "type": "object",
            "required": ["type", "url"],
            "properties": {
              "type": { "const": "other" },
              "url": { "type": "string", "format": "uri" },
              "description": { "type": "string" }
            }
          }
        ]
      }
    },
    "scope": {
      "type": "object",
      "properties": {
        "budget_managed": { "type": "string" },
        "team_size": { "type": "integer", "minimum": 0 },
        "revenue_influenced": { "type": "string" },
        "geographic_reach": { "type": "string" }
      }
    },
    "impact_category": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["financial", "operational", "talent", "customer", "organizational"]
      }
    },
    "metrics": {
      "type": "object",
      "properties": {
        "baseline": { "type": "string" },
        "outcome": { "type": "string" },
        "percentage_change": { "type": "number" }
      }
    },
    "framing": {
      "type": "object",
      "properties": {
        "action_verb": { "type": "string" },
        "strategic_context": { "type": "string" }
      }
    }
  }
}
```

### Pydantic Model Implementation

**`src/resume_as_code/models/work_unit.py`:**

```python
"""Work Unit Pydantic models for Resume as Code."""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class ConfidenceLevel(str, Enum):
    """Confidence level for metrics and outcomes."""

    EXACT = "exact"
    ESTIMATED = "estimated"
    APPROXIMATE = "approximate"
    ORDER_OF_MAGNITUDE = "order_of_magnitude"


class WorkUnitConfidence(str, Enum):
    """Overall confidence in Work Unit accuracy."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImpactCategory(str, Enum):
    """Category of business impact."""

    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    TALENT = "talent"
    CUSTOMER = "customer"
    ORGANIZATIONAL = "organizational"


class EvidenceType(str, Enum):
    """Types of supporting evidence."""

    GIT_REPO = "git_repo"
    METRICS = "metrics"
    DOCUMENT = "document"
    ARTIFACT = "artifact"
    OTHER = "other"


# Evidence types with discriminated union
class GitRepoEvidence(BaseModel):
    """Evidence from a code repository."""

    type: Literal["git_repo"] = "git_repo"
    url: HttpUrl
    branch: str | None = None
    commit_sha: str | None = None
    description: str | None = None


class MetricsEvidence(BaseModel):
    """Evidence from a metrics dashboard."""

    type: Literal["metrics"] = "metrics"
    url: HttpUrl
    dashboard_name: str | None = None
    metric_names: list[str] = Field(default_factory=list)
    description: str | None = None


class DocumentEvidence(BaseModel):
    """Evidence from a document or publication."""

    type: Literal["document"] = "document"
    url: HttpUrl
    title: str | None = None
    publication_date: date | None = None
    description: str | None = None


class ArtifactEvidence(BaseModel):
    """Evidence from an artifact or release."""

    type: Literal["artifact"] = "artifact"
    url: HttpUrl
    artifact_type: str | None = None
    description: str | None = None


class OtherEvidence(BaseModel):
    """Other types of evidence."""

    type: Literal["other"] = "other"
    url: HttpUrl
    description: str | None = None


# Discriminated union for evidence
Evidence = Annotated[
    GitRepoEvidence | MetricsEvidence | DocumentEvidence | ArtifactEvidence | OtherEvidence,
    Field(discriminator="type"),
]


class Skill(BaseModel):
    """Skill demonstrated in a Work Unit."""

    name: str
    onet_element_id: str | None = None  # O*NET taxonomy ID
    proficiency_level: int | None = Field(default=None, ge=1, le=7)


class Problem(BaseModel):
    """Problem statement for a Work Unit."""

    statement: str = Field(..., min_length=20)
    constraints: list[str] = Field(default_factory=list)
    context: str | None = None


class Outcome(BaseModel):
    """Outcome of a Work Unit."""

    result: str = Field(..., min_length=10)
    quantified_impact: str | None = None
    business_value: str | None = None
    confidence: ConfidenceLevel | None = None
    confidence_note: str | None = None


class Scope(BaseModel):
    """Scope of responsibility for executive-level work."""

    budget_managed: str | None = None
    team_size: int | None = Field(default=None, ge=0)
    revenue_influenced: str | None = None
    geographic_reach: str | None = None


class Metrics(BaseModel):
    """Quantified metrics with before/after context."""

    baseline: str | None = None
    outcome: str | None = None
    percentage_change: float | None = None


class Framing(BaseModel):
    """Strategic framing guidance."""

    action_verb: str | None = None
    strategic_context: str | None = None


class WorkUnit(BaseModel):
    """A documented instance of applied capability."""

    # Required fields
    id: str = Field(..., pattern=r"^wu-\d{4}-\d{2}-\d{2}-[a-z0-9-]+$")
    title: str = Field(..., min_length=10, max_length=200)
    problem: Problem
    actions: list[str] = Field(..., min_length=1)
    outcome: Outcome

    # Optional time fields
    time_started: date | None = None
    time_ended: date | None = None

    # Optional metadata
    skills_demonstrated: list[Skill] = Field(default_factory=list)
    confidence: WorkUnitConfidence | None = None
    tags: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    # Executive-level fields
    scope: Scope | None = None
    impact_category: list[ImpactCategory] = Field(default_factory=list)
    metrics: Metrics | None = None
    framing: Framing | None = None

    # Schema version
    schema_version: str = Field(default="1.0.0")

    @field_validator("actions")
    @classmethod
    def validate_actions_not_empty(cls, v: list[str]) -> list[str]:
        """Ensure actions list has at least one item."""
        if not v:
            raise ValueError("At least one action is required")
        if any(len(action) < 10 for action in v):
            raise ValueError("Each action must be at least 10 characters")
        return v

    @model_validator(mode="after")
    def validate_time_range(self) -> WorkUnit:
        """Ensure time_ended is after time_started if both are set."""
        if self.time_started and self.time_ended:
            if self.time_ended < self.time_started:
                raise ValueError("time_ended must be after time_started")
        return self
```

### Weak Action Verb Detection (Content Strategy)

Per Architecture Section 1.4, these verbs should be flagged:

| Weak Verb | Suggested Alternatives |
|-----------|----------------------|
| managed | orchestrated, spearheaded, directed |
| handled | resolved, addressed, executed |
| helped | enabled, facilitated, empowered |
| worked on | developed, built, engineered |
| was responsible for | led, owned, drove |

```python
WEAK_VERBS = {"managed", "handled", "helped", "worked on", "was responsible for"}
STRONG_VERBS = {
    "orchestrated", "spearheaded", "championed", "transformed",
    "cultivated", "mentored", "mobilized", "aligned", "unified",
    "accelerated", "revolutionized", "catalyzed", "pioneered",
}
```

### Project Structure After This Story

```
src/resume_as_code/
├── models/
│   ├── __init__.py
│   ├── config.py
│   ├── errors.py
│   ├── output.py
│   └── work_unit.py        # NEW: Work Unit models
└── ...

schemas/
├── config.schema.json
└── work-unit.schema.json   # NEW: Work Unit JSON Schema
```

### Testing Requirements

**`tests/unit/test_work_unit.py`:**

```python
"""Tests for Work Unit models."""

from datetime import date

import pytest
from pydantic import ValidationError

from resume_as_code.models.work_unit import (
    ConfidenceLevel,
    Evidence,
    EvidenceType,
    ImpactCategory,
    Outcome,
    Problem,
    GitRepoEvidence,
    WorkUnit,
    WorkUnitConfidence,
)


class TestWorkUnitValidation:
    """Test Work Unit validation rules."""

    def test_valid_work_unit_creates_successfully(self):
        """A complete valid Work Unit should pass validation."""
        wu = WorkUnit(
            id="wu-2024-03-15-cloud-migration",
            title="Migrated legacy system to cloud infrastructure",
            problem=Problem(statement="Legacy on-prem system was costly and hard to scale"),
            actions=["Designed cloud architecture", "Migrated databases", "Updated deployments"],
            outcome=Outcome(result="Reduced infrastructure costs by 40%"),
        )
        assert wu.id == "wu-2024-03-15-cloud-migration"

    def test_missing_required_field_raises_error(self):
        """Missing required fields should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            WorkUnit(
                id="wu-2024-03-15-test",
                title="Test work unit title here",
                problem=Problem(statement="This is the problem statement"),
                actions=["Action taken"],
                # Missing outcome
            )
        assert "outcome" in str(exc_info.value)

    def test_invalid_id_format_raises_error(self):
        """ID must match pattern wu-YYYY-MM-DD-slug."""
        with pytest.raises(ValidationError):
            WorkUnit(
                id="invalid-id",
                title="Test work unit title",
                problem=Problem(statement="This is the problem statement"),
                actions=["Action taken here"],
                outcome=Outcome(result="Result achieved"),
            )

    def test_time_ended_before_started_raises_error(self):
        """time_ended must be after time_started."""
        with pytest.raises(ValidationError):
            WorkUnit(
                id="wu-2024-03-15-test",
                title="Test work unit title",
                problem=Problem(statement="This is the problem statement"),
                actions=["Action taken here"],
                outcome=Outcome(result="Result achieved"),
                time_started=date(2024, 3, 15),
                time_ended=date(2024, 3, 10),  # Before start
            )


class TestEvidenceDiscriminatedUnion:
    """Test evidence type discrimination."""

    def test_git_repo_evidence_type(self):
        """Git repo evidence should have correct type."""
        evidence = GitRepoEvidence(url="https://github.com/org/repo")
        assert evidence.type == "git_repo"

    def test_all_evidence_types_defined(self):
        """All five evidence types should be defined."""
        assert EvidenceType.GIT_REPO.value == "git_repo"
        assert EvidenceType.METRICS.value == "metrics"
        assert EvidenceType.DOCUMENT.value == "document"
        assert EvidenceType.ARTIFACT.value == "artifact"
        assert EvidenceType.OTHER.value == "other"

    def test_evidence_union_discriminates_by_type(self):
        """Evidence union should parse correct type based on discriminator."""
        # This is tested via WorkUnit.evidence field
        pass
```

### Verification Commands

```bash
# Validate JSON Schema syntax
python -c "import json; json.load(open('schemas/work-unit.schema.json'))"

# Test Pydantic models
pytest tests/unit/test_work_unit.py -v

# Code quality
ruff check src tests --fix
ruff format src tests
mypy src --strict
```

### References

- [Source: architecture.md#Section 3.2 - Data Architecture](_bmad-output/planning-artifacts/architecture.md)
- [Source: architecture.md#Section 1.4 - Content Strategy Standards](_bmad-output/planning-artifacts/architecture.md)
- [Source: epics.md#Story 2.1](_bmad-output/planning-artifacts/epics.md)
- [Source: project-context.md](_bmad-output/project-context.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- Created JSON Schema at `schemas/work-unit.schema.json` with full Work Unit structure including required fields, optional metadata, executive-level fields, and discriminated union for evidence types
- Implemented Pydantic models in `src/resume_as_code/models/work_unit.py` with proper type hints, field validators, and model validators
- Evidence types use discriminated union pattern with `type` field as discriminator (GitRepoEvidence, MetricsEvidence, DocumentEvidence, ArtifactEvidence, OtherEvidence)
- Added weak action verb detection via `get_weak_verb_warnings()` method per Content Strategy standards
- Time range validation ensures `time_ended` is after `time_started`
- All 8 Acceptance Criteria satisfied
- 271 tests passing, including 58 new tests for Work Unit schema and models
- Code quality verified: ruff check passes, mypy --strict passes with zero errors

### File List

**New Files:**
- `schemas/work-unit.schema.json` - JSON Schema for Work Unit validation
- `src/resume_as_code/models/work_unit.py` - Pydantic models for Work Unit
- `tests/unit/test_work_unit_schema.py` - Tests for JSON Schema structure (25 tests)
- `tests/unit/test_work_unit_models.py` - Tests for Pydantic models (33 tests)

**Modified Files:**
- None

