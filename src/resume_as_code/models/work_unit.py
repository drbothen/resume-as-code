"""Work Unit Pydantic models for Resume as Code."""

from __future__ import annotations

import re
import warnings
from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    PrivateAttr,
    field_validator,
    model_validator,
)

from resume_as_code.models.job_description import ExperienceLevel

if TYPE_CHECKING:
    from resume_as_code.models.position import Position

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


class WorkUnitArchetype(str, Enum):
    """Work unit archetype classification for PAR structure patterns.

    Each archetype represents a common pattern of professional achievement
    with distinct problem-action-result structures. The archetype guides
    how achievements are categorized, validated, and presented on resumes.

    Values must match archetype template filenames exactly (lowercase).
    """

    GREENFIELD = "greenfield"
    """New system/feature built from scratch. Focus on design decisions,
    technology choices, and delivery of new capabilities."""

    MIGRATION = "migration"
    """System/data migration projects. Focus on planning, risk mitigation,
    and successful transition from legacy to modern systems."""

    OPTIMIZATION = "optimization"
    """Performance or cost improvements. Focus on measurable improvements
    with clear before/after metrics (latency, cost, efficiency)."""

    INCIDENT = "incident"
    """Production incident response or security assessments. Focus on
    rapid response, root cause analysis, and remediation."""

    LEADERSHIP = "leadership"
    """Team building, hiring, and mentorship. Focus on people development,
    team growth, and organizational capability building."""

    STRATEGIC = "strategic"
    """Strategic initiatives and architecture decisions. Focus on long-term
    planning, roadmap definition, and cross-org alignment."""

    TRANSFORMATION = "transformation"
    """Large-scale organizational change. Focus on enterprise-wide impact,
    process overhauls, and digital transformation initiatives."""

    CULTURAL = "cultural"
    """Culture, DEI, and engagement initiatives. Focus on improving
    organizational health, inclusion, and employee experience."""

    MINIMAL = "minimal"
    """Quick capture with basic structure. Used when full PAR details
    are not yet available or for simple achievements."""


class EvidenceType(str, Enum):
    """Types of supporting evidence."""

    GIT_REPO = "git_repo"
    METRICS = "metrics"
    DOCUMENT = "document"
    ARTIFACT = "artifact"
    LINK = "link"
    NARRATIVE = "narrative"
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
    """Evidence from an artifact or release (package, binary, deployment).

    Can reference artifacts via URL, local path, or content hash.
    At least one of url, local_path, or sha256 must be provided.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["artifact"] = "artifact"
    url: HttpUrl | None = None
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
    description: str | None = Field(default=None, description="Artifact description")

    @field_validator("local_path")
    @classmethod
    def validate_local_path_is_relative(cls, v: str | None) -> str | None:
        """Ensure local_path is a relative path, not absolute.

        Rejects paths starting with /, ~, or Windows drive letters (C:, D:, etc.)
        to ensure paths are relative to project root.
        """
        if v is None:
            return v
        # Check for Unix absolute paths
        if v.startswith("/") or v.startswith("~"):
            raise ValueError(f"local_path must be relative to project root, not absolute: {v}")
        # Check for Windows absolute paths (drive letters)
        if len(v) >= 2 and v[1] == ":" and v[0].isalpha():
            raise ValueError(f"local_path must be relative to project root, not absolute: {v}")
        return v

    @model_validator(mode="after")
    def validate_at_least_one_reference(self) -> ArtifactEvidence:
        """Ensure at least one reference method is provided."""
        if not any([self.url, self.local_path, self.sha256]):
            raise ValueError(
                "ArtifactEvidence requires at least one of: url, local_path, or sha256"
            )
        return self


class OtherEvidence(BaseModel):
    """Evidence that doesn't fit other categories.

    DEPRECATED: Prefer LinkEvidence for generic URLs or NarrativeEvidence
    for description-only evidence. This type is maintained for backward
    compatibility with existing work units.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["other"] = "other"
    url: HttpUrl
    description: str | None = None


class LinkEvidence(BaseModel):
    """Evidence from a generic web link.

    Use for any HTTP/HTTPS URL that doesn't fit specific categories
    like git_repo, metrics, document, or artifact. Preferred over
    OtherEvidence for new work units as it supports a title field
    for better labeling.

    Examples:
        - Blog posts
        - News articles
        - External presentations
        - Company announcements
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["link"] = "link"
    url: HttpUrl
    title: str | None = Field(
        default=None,
        description="Link title or label",
    )
    description: str | None = Field(default=None, description="Link description")


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


# Discriminated union for evidence
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


class LegacyWorkUnitScope(BaseModel):
    """Legacy scope model for work units (DEPRECATED).

    This model is kept for backwards compatibility with existing YAML files.
    New work units should use Position.scope instead.

    Field mapping to unified Scope:
    - budget_managed -> budget
    - revenue_influenced -> revenue
    - geographic_reach -> geography
    - team_size -> team_size (same)
    """

    model_config = ConfigDict(extra="forbid")

    budget_managed: str | None = None
    team_size: int | None = Field(default=None, ge=0)
    revenue_influenced: str | None = None
    geographic_reach: str | None = None


# DEPRECATED: LegacyScope alias for backwards compatibility with existing YAML files.
# New code should import Scope from resume_as_code.models.scope instead.
# This alias will be removed in v1.0.
LegacyScope = LegacyWorkUnitScope


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
    archetype: WorkUnitArchetype = Field(
        ...,
        description="Archetype classification for PAR structure patterns. "
        "Must be one of: greenfield, migration, optimization, incident, "
        "leadership, strategic, transformation, cultural, minimal.",
    )

    # Optional time fields
    time_started: date | None = None
    time_ended: date | None = None

    # Position reference for employment history grouping
    position_id: str | None = Field(
        default=None, description="Reference to position in positions.yaml for employer grouping"
    )

    # Seniority level for matching (Story 7.12)
    seniority_level: ExperienceLevel | None = Field(
        default=None,
        description="Seniority level for matching. If not set, inferred from position title.",
    )

    # Optional metadata
    skills_demonstrated: list[Skill] = Field(default_factory=list)
    confidence: WorkUnitConfidence | None = None
    tags: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    # Executive-level fields (DEPRECATED: use Position.scope instead)
    # Note: Deprecation warning emitted by warn_deprecated_scope validator only when set
    scope: LegacyWorkUnitScope | None = None
    impact_category: list[ImpactCategory] = Field(default_factory=list)
    metrics: Metrics | None = None
    framing: Framing | None = None

    # Schema version (4.0.0 adds required archetype field)
    schema_version: str = Field(default="4.0.0")

    # Private attribute for attached Position (not serialized)
    _position: Position | None = PrivateAttr(default=None)

    @property
    def position(self) -> Position | None:
        """Get attached Position object.

        Returns None if position_id is None or Position hasn't been attached.
        Use WorkUnitLoader.load_with_positions() to attach positions.
        """
        return self._position

    def attach_position(self, position: Position) -> None:
        """Attach a Position object to this WorkUnit.

        Args:
            position: Position to attach.

        Raises:
            ValueError: If position.id doesn't match position_id.
        """
        if self.position_id is None:
            raise ValueError("Cannot attach position to WorkUnit without position_id")
        if position.id != self.position_id:
            raise ValueError(
                f"Position ID mismatch: WorkUnit.position_id={self.position_id!r}, "
                f"Position.id={position.id!r}"
            )
        self._position = position

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
        """Normalize tags to lowercase, strip whitespace, remove empty/duplicates.

        Per Story 2.5, tags should be normalized for consistent
        filtering and searching. Empty strings and duplicates are removed
        to ensure clean, filterable tag lists.
        """
        seen: set[str] = set()
        result: list[str] = []
        for tag in v:
            normalized = tag.lower().strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        return result

    @model_validator(mode="after")
    def validate_time_range(self) -> WorkUnit:
        """Ensure time_ended is after time_started if both are set."""
        if self.time_started and self.time_ended and self.time_ended < self.time_started:
            raise ValueError("time_ended must be after time_started")
        return self

    @model_validator(mode="after")
    def warn_deprecated_scope(self) -> WorkUnit:
        """Emit deprecation warning when scope is set.

        Per Story 7.2, WorkUnit.scope is deprecated. Scope should be
        set on Position instead and inherited via position_id reference.
        """
        if self.scope is not None:
            warnings.warn(
                "WorkUnit.scope is deprecated. Set scope on the Position instead. "
                "Will be removed in v1.0.",
                DeprecationWarning,
                stacklevel=2,
            )
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
