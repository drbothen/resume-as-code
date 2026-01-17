"""Configuration models for Resume as Code."""

from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from resume_as_code.models.board_role import BoardRole
from resume_as_code.models.certification import Certification
from resume_as_code.models.education import Education
from resume_as_code.models.publication import Publication

logger = logging.getLogger(__name__)


class ProfileConfig(BaseModel):
    """User profile information for resume header.

    All fields are optional to support incremental configuration.
    URL fields use HttpUrl for validation.
    """

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: HttpUrl | None = None
    github: HttpUrl | None = None
    website: HttpUrl | None = None
    title: str | None = None  # Professional title/headline
    summary: str | None = None  # Executive summary template


class SkillsConfig(BaseModel):
    """Configuration for skills curation.

    Controls how skills are deduplicated, filtered, and prioritized
    for resume display.
    """

    max_display: int = Field(default=15, ge=1, le=50)
    exclude: list[str] = Field(default_factory=list)
    prioritize: list[str] = Field(default_factory=list)


class ScoringWeights(BaseModel):
    """Weights for ranking algorithm.

    BM25 vs Semantic weights control the balance in RRF fusion.
    Higher bm25_weight emphasizes keyword matching.
    Higher semantic_weight emphasizes meaning/context matching.

    Recency decay (Story 7.9) uses exponential decay to weight recent
    experience higher than older experience:

        recency_score = e^(-λ × years_ago)

    Where:
        λ = ln(2) / recency_half_life  (decay constant)
        years_ago = (today - time_ended).days / 365.25

    Example with 5-year half-life:
        Current position → 100% weight
        1 year ago → ~87% weight
        5 years ago → 50% weight
        10 years ago → 25% weight

    Final score blends relevance and recency:
        final = (1 - recency_blend) × relevance + recency_blend × recency

    Section-level semantic matching (Story 7.11):
        When use_sectioned_semantic is True, matches work unit sections
        against JD sections with configurable weights:
        - Outcome ↔ JD Requirements: 40% (most predictive of job fit)
        - Actions ↔ JD Requirements: 30% (what candidate did)
        - Skills ↔ JD Skills: 20% (technical alignment)
        - Title ↔ JD Full: 10% (role alignment)
    """

    # BM25 vs Semantic balance for RRF fusion
    bm25_weight: float = Field(default=1.0, ge=0.0, le=2.0)
    semantic_weight: float = Field(default=1.0, ge=0.0, le=2.0)

    # Field-specific BM25 weights (title/skills weighted higher per HBR 2023 research)
    title_weight: float = Field(default=2.0, ge=0.0, le=10.0)
    skills_weight: float = Field(default=1.5, ge=0.0, le=10.0)
    experience_weight: float = Field(default=1.0, ge=0.0, le=10.0)

    # Recency decay (Story 7.9)
    recency_half_life: float | None = Field(
        default=5.0,
        ge=1.0,
        le=20.0,
        description="Years for experience to decay to 50% weight. None disables decay.",
    )
    recency_blend: float = Field(
        default=0.2,
        ge=0.0,
        le=0.5,
        description="Weight of recency in final score (0.2 = 20%).",
    )

    # Section-level semantic weights (Story 7.11)
    use_sectioned_semantic: bool = Field(
        default=False,
        description="Enable section-level semantic matching (more precise but slower).",
    )
    section_outcome_weight: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Weight for outcome section in semantic scoring.",
    )
    section_actions_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for actions section in semantic scoring.",
    )
    section_skills_weight: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Weight for skills section in semantic scoring.",
    )
    section_title_weight: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Weight for title section in semantic scoring.",
    )

    # Seniority matching (Story 7.12)
    use_seniority_matching: bool = Field(
        default=True,
        description="Enable seniority level matching against JD.",
    )
    seniority_blend: float = Field(
        default=0.1,
        ge=0.0,
        le=0.3,
        description="How much seniority alignment affects final score (0.1 = 10%).",
    )

    @model_validator(mode="after")
    def validate_section_weights_sum(self) -> ScoringWeights:
        """Validate section weights sum to ~1.0 when sectioned semantic is enabled."""
        if self.use_sectioned_semantic:
            total = (
                self.section_outcome_weight
                + self.section_actions_weight
                + self.section_skills_weight
                + self.section_title_weight
            )
            if not (0.99 <= total <= 1.01):
                msg = f"Section weights must sum to 1.0, got {total:.2f}"
                raise ValueError(msg)
        return self


class ONetConfig(BaseModel):
    """O*NET API v2.0 configuration.

    API key can be set via config file or ONET_API_KEY environment variable.
    Register at https://services.onetcenter.org/developer/signup

    Attributes:
        enabled: Enable O*NET API integration.
        api_key: O*NET API key (or set ONET_API_KEY env var).
        cache_ttl: Cache TTL in seconds (minimum 1 hour).
        timeout: API request timeout in seconds.
        retry_delay_ms: Minimum delay between retries in milliseconds.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(
        default=True,
        description="Enable O*NET API integration",
    )
    api_key: str | None = Field(
        default=None,
        description="O*NET API key (or set ONET_API_KEY env var)",
    )
    cache_ttl: int = Field(
        default=86400,  # 24 hours
        ge=3600,  # Minimum 1 hour
        description="Cache TTL in seconds",
    )
    timeout: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="API request timeout in seconds",
    )
    retry_delay_ms: int = Field(
        default=200,
        ge=200,  # O*NET documented minimum
        description="Minimum delay between retries in milliseconds",
    )

    @model_validator(mode="after")
    def resolve_env_api_key(self) -> ONetConfig:
        """Resolve API key from environment if not in config."""
        if self.api_key is None:
            self.api_key = os.environ.get("ONET_API_KEY")
        return self

    @property
    def is_configured(self) -> bool:
        """Check if API key is available and enabled."""
        return self.enabled and self.api_key is not None


class ResumeConfig(BaseModel):
    """Complete configuration for Resume as Code."""

    # Output settings
    output_dir: Path = Field(default=Path("./dist"))
    default_format: Literal["pdf", "docx", "both"] = Field(default="both")
    default_template: str = Field(default="modern")

    # Work unit settings
    work_units_dir: Path = Field(default=Path("./work-units"))

    # Employment history settings
    positions_path: Path = Field(default=Path("./positions.yaml"))

    # Ranking settings
    scoring_weights: ScoringWeights = Field(default_factory=ScoringWeights)
    default_top_k: int = Field(default=8, ge=1, le=50)

    # Editor settings
    editor: str | None = Field(default=None)  # Falls back to $EDITOR

    # Profile information
    profile: ProfileConfig = Field(default_factory=ProfileConfig)

    # Certifications
    certifications: list[Certification] = Field(default_factory=list)

    # Education
    education: list[Education] = Field(default_factory=list)

    # Skills curation
    skills: SkillsConfig = Field(default_factory=SkillsConfig)

    # Career highlights (CTO/executive hybrid format)
    career_highlights: list[str] = Field(default_factory=list)

    # Board & Advisory Roles
    board_roles: list[BoardRole] = Field(default_factory=list)

    # Publications & Speaking Engagements
    publications: list[Publication] = Field(default_factory=list)

    # O*NET API configuration
    onet: ONetConfig | None = Field(default=None)

    @field_validator("career_highlights", mode="before")
    @classmethod
    def validate_career_highlights(cls, v: list[str] | None) -> list[str]:
        """Validate career highlights list."""
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("career_highlights must be a list")
        for i, highlight in enumerate(v):
            if not isinstance(highlight, str):
                raise ValueError(f"career_highlights[{i}] must be a string")
            if not highlight.strip():
                raise ValueError(f"career_highlights[{i}] cannot be empty")
            if len(highlight) > 150:
                raise ValueError(
                    f"career_highlights[{i}] exceeds 150 characters ({len(highlight)} chars)"
                )
        return v

    @model_validator(mode="after")
    def warn_excess_highlights(self) -> ResumeConfig:
        """Warn if more than 4 career highlights provided."""
        if len(self.career_highlights) > 4:
            warnings.warn(
                f"Research suggests maximum 4 career highlights for optimal impact. "
                f"You have {len(self.career_highlights)}.",
                UserWarning,
                stacklevel=2,
            )
            logger.warning(
                "More than 4 career highlights configured. Research suggests 4 is optimal."
            )
        return self

    @field_validator("output_dir", "work_units_dir", "positions_path", mode="before")
    @classmethod
    def expand_path(cls, v: str | Path) -> Path:
        """Expand ~ and resolve path."""
        if isinstance(v, str):
            v = Path(v)
        return v.expanduser()


class ConfigSource(BaseModel):
    """Tracks the source of each config value."""

    value: str | int | float | bool | dict[str, object] | list[object] | None
    source: Literal["default", "user", "project", "env", "cli"]
    path: str | None = None  # File path if from file
