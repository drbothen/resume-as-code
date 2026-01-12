"""Configuration models for Resume as Code."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

from resume_as_code.models.certification import Certification


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


class ResumeConfig(BaseModel):
    """Complete configuration for Resume as Code."""

    # Output settings
    output_dir: Path = Field(default=Path("./dist"))
    default_format: Literal["pdf", "docx", "both"] = Field(default="both")
    default_template: str = Field(default="modern")

    # Work unit settings
    work_units_dir: Path = Field(default=Path("./work-units"))

    # Ranking settings
    scoring_weights: ScoringWeights = Field(default_factory=ScoringWeights)
    default_top_k: int = Field(default=8, ge=1, le=50)

    # Editor settings
    editor: str | None = Field(default=None)  # Falls back to $EDITOR

    # Profile information
    profile: ProfileConfig = Field(default_factory=ProfileConfig)

    # Certifications
    certifications: list[Certification] = Field(default_factory=list)

    # Skills curation
    skills: SkillsConfig = Field(default_factory=SkillsConfig)

    @field_validator("output_dir", "work_units_dir", mode="before")
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
