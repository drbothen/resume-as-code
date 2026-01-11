"""Job Description model for parsed JD data."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ExperienceLevel(str, Enum):
    """Experience level indicators."""

    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    LEAD = "lead"
    PRINCIPAL = "principal"
    EXECUTIVE = "executive"


class Requirement(BaseModel):
    """A single requirement from the JD."""

    text: str = Field(..., description="The requirement text")
    is_required: bool = Field(
        default=True,
        description="True if required, False if nice-to-have",
    )
    category: str | None = Field(
        default=None,
        description="Category: technical, soft_skill, education, etc.",
    )


class JobDescription(BaseModel):
    """Parsed job description with extracted information."""

    raw_text: str = Field(..., description="Original JD text")
    title: str | None = Field(default=None, description="Job title if detected")
    company: str | None = Field(default=None, description="Company name if detected")

    skills: list[str] = Field(
        default_factory=list,
        description="Normalized list of skills/technologies",
    )

    requirements: list[Requirement] = Field(
        default_factory=list,
        description="Extracted requirements",
    )

    experience_level: ExperienceLevel = Field(
        default=ExperienceLevel.MID,
        description="Detected experience level",
    )

    years_experience: int | None = Field(
        default=None,
        description="Required years of experience if specified",
    )

    keywords: list[str] = Field(
        default_factory=list,
        description="High-frequency keywords for ranking",
    )

    @property
    def text_for_ranking(self) -> str:
        """Get combined text for BM25/semantic ranking."""
        parts = [self.raw_text]
        if self.title:
            parts.insert(0, self.title)
        return " ".join(parts)
