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
    """

    # BM25 vs Semantic balance for RRF fusion
    bm25_weight: float = Field(default=1.0, ge=0.0, le=2.0)
    semantic_weight: float = Field(default=1.0, ge=0.0, le=2.0)

    # Reserved for future field-specific weighting
    title_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    skills_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    experience_weight: float = Field(default=1.0, ge=0.0, le=10.0)


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
