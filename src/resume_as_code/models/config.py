"""Configuration models for Resume as Code."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ScoringWeights(BaseModel):
    """Weights for ranking algorithm."""

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
