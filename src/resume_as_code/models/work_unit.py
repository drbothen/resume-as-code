"""Work Unit Pydantic models for Resume as Code."""

from __future__ import annotations

import re
from datetime import date
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

# Weak action verbs to flag per Content Strategy standards
WEAK_VERBS: frozenset[str] = frozenset(
    {
        "managed",
        "handled",
        "helped",
        "worked on",
        "was responsible for",
    }
)

# Strong action verbs recommended as alternatives
STRONG_VERBS: frozenset[str] = frozenset(
    {
        "orchestrated",
        "spearheaded",
        "championed",
        "transformed",
        "cultivated",
        "mentored",
        "mobilized",
        "aligned",
        "unified",
        "accelerated",
        "revolutionized",
        "catalyzed",
        "pioneered",
    }
)


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
    """Evidence from a code repository (GitHub, GitLab, etc.)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["git_repo"] = "git_repo"
    url: HttpUrl
    branch: str | None = None
    commit_sha: str | None = None
    description: str | None = None


class MetricsEvidence(BaseModel):
    """Evidence from a metrics dashboard (Grafana, Datadog, etc.)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["metrics"] = "metrics"
    url: HttpUrl
    dashboard_name: str | None = None
    metric_names: list[str] = Field(default_factory=list)
    description: str | None = None


class DocumentEvidence(BaseModel):
    """Evidence from a document or publication (whitepaper, RFC, etc.)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["document"] = "document"
    url: HttpUrl
    title: str | None = None
    publication_date: date | None = None
    description: str | None = None


class ArtifactEvidence(BaseModel):
    """Evidence from an artifact or release (package, binary, deployment)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["artifact"] = "artifact"
    url: HttpUrl
    artifact_type: str | None = None
    description: str | None = None


class OtherEvidence(BaseModel):
    """Evidence that doesn't fit other categories."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["other"] = "other"
    url: HttpUrl
    description: str | None = None


# Discriminated union for evidence
Evidence = Annotated[
    GitRepoEvidence | MetricsEvidence | DocumentEvidence | ArtifactEvidence | OtherEvidence,
    Field(discriminator="type"),
]


class Skill(BaseModel):
    """Skill demonstrated in a Work Unit with optional O*NET taxonomy mapping."""

    model_config = ConfigDict(extra="forbid")

    name: str
    onet_element_id: str | None = Field(
        default=None, pattern=r"^\d+\.\w+(\.\d+)*$"
    )  # O*NET taxonomy ID
    proficiency_level: int | None = Field(default=None, ge=1, le=7)


class Problem(BaseModel):
    """Problem statement describing the challenge addressed in a Work Unit."""

    model_config = ConfigDict(extra="forbid")

    statement: str = Field(..., min_length=20)
    constraints: list[str] = Field(default_factory=list)
    context: str | None = None


class Outcome(BaseModel):
    """Outcome describing the results achieved in a Work Unit."""

    model_config = ConfigDict(extra="forbid")

    result: str = Field(..., min_length=10)
    quantified_impact: str | None = None
    business_value: str | None = None
    confidence: ConfidenceLevel | None = None
    confidence_note: str | None = None


class Scope(BaseModel):
    """Scope of responsibility for executive-level work (budget, team, reach)."""

    model_config = ConfigDict(extra="forbid")

    budget_managed: str | None = None
    team_size: int | None = Field(default=None, ge=0)
    revenue_influenced: str | None = None
    geographic_reach: str | None = None


class Metrics(BaseModel):
    """Quantified metrics with baseline and outcome for before/after comparison."""

    model_config = ConfigDict(extra="forbid")

    baseline: str | None = None
    outcome: str | None = None
    percentage_change: float | None = None


class Framing(BaseModel):
    """Strategic framing guidance for resume presentation."""

    model_config = ConfigDict(extra="forbid")

    action_verb: str | None = None
    strategic_context: str | None = None


class WorkUnit(BaseModel):
    """A documented instance of applied capability (the core resume building block)."""

    model_config = ConfigDict(extra="forbid")

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
        """Ensure actions list has at least one item with minimum length."""
        if not v:
            raise ValueError("At least one action is required")
        if any(len(action) < 10 for action in v):
            raise ValueError("Each action must be at least 10 characters")
        return v

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: list[str]) -> list[str]:
        """Normalize tags to lowercase and strip whitespace.

        Per Story 2.5, tags should be normalized for consistent
        filtering and searching.
        """
        return [tag.lower().strip() for tag in v]

    @model_validator(mode="after")
    def validate_time_range(self) -> WorkUnit:
        """Ensure time_ended is after time_started if both are set."""
        if self.time_started and self.time_ended and self.time_ended < self.time_started:
            raise ValueError("time_ended must be after time_started")
        return self

    def get_weak_verb_warnings(self) -> list[str]:
        """Check for weak action verbs and return warnings.

        Per Content Strategy standards, weak verbs should be flagged
        so users can consider stronger alternatives. Uses word boundary
        matching to detect verbs at any position in the sentence.

        Returns:
            List of warning messages for detected weak verbs.
        """
        warnings: list[str] = []

        # Check actions for weak verbs using word boundary regex
        for action in self.actions:
            action_lower = action.lower()
            for weak_verb in WEAK_VERBS:
                # Use word boundaries to match verb at start, middle, or end
                pattern = rf"(^|(?<=\s)){re.escape(weak_verb)}($|(?=\s)|(?=[.,!?]))"
                if re.search(pattern, action_lower):
                    warnings.append(
                        f"Action contains weak verb '{weak_verb}': '{action[:50]}...'"
                        if len(action) > 50
                        else f"Action contains weak verb '{weak_verb}': '{action}'"
                    )

        # Check framing.action_verb if present
        if self.framing and self.framing.action_verb:
            verb_lower = self.framing.action_verb.lower()
            if verb_lower in WEAK_VERBS:
                warnings.append(
                    f"Framing uses weak verb '{verb_lower}'. "
                    f"Consider alternatives: {', '.join(list(STRONG_VERBS)[:5])}"
                )

        return warnings
