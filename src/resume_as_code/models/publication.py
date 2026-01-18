"""Publication model for publications and speaking engagements."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, HttpUrl

from resume_as_code.models.types import YearMonth

if TYPE_CHECKING:
    from resume_as_code.services.skill_registry import SkillRegistry

PublicationType = Literal["conference", "article", "whitepaper", "book", "podcast", "webinar"]


class Publication(BaseModel):
    """Publication or speaking engagement record.

    Stores publication and speaking engagement information for resume
    rendering with support for type classification and display control.
    Supports JD-relevant curation via topics and abstract fields.
    """

    title: str
    type: PublicationType
    venue: str  # Conference name, publisher, blog name
    date: YearMonth  # YYYY-MM format
    url: HttpUrl | None = None
    display: bool = Field(default=True)
    # New fields for JD-relevant curation (Story 8.2)
    topics: list[str] = Field(
        default_factory=list,
        description="Topic tags for matching (normalized via SkillRegistry)",
    )
    abstract: str | None = Field(
        default=None,
        max_length=500,
        description="Brief description for semantic matching (max 500 chars)",
    )

    @property
    def year(self) -> str:
        """Extract year from date.

        Returns:
            Four-digit year string.
        """
        return self.date[:4]

    @property
    def is_speaking(self) -> bool:
        """Check if this is a speaking engagement.

        Returns:
            True if type is conference, podcast, or webinar.
        """
        return self.type in ("conference", "podcast", "webinar")

    def format_display(self, include_abstract: bool = False) -> str:
        """Format for resume display.

        Speaking engagements: "Venue (Year) - Title"
        Written works: "Title, Venue (Year)"

        Args:
            include_abstract: Include abstract preview if available.

        Returns:
            Formatted display string.
        """
        if self.is_speaking:
            base = f"{self.venue} ({self.year}) - {self.title}"
        else:
            base = f"{self.title}, {self.venue} ({self.year})"

        if include_abstract and self.abstract:
            # Truncate abstract to 100 chars for preview
            preview = self.abstract[:100] + "..." if len(self.abstract) > 100 else self.abstract
            return f"{base}\n  {preview}"
        return base

    def get_normalized_topics(self, registry: SkillRegistry | None = None) -> list[str]:
        """Get topics normalized via SkillRegistry.

        Args:
            registry: Optional SkillRegistry for normalization.
                     If None, returns topics as-is.

        Returns:
            List of normalized topic strings.
        """
        if registry is None:
            return self.topics
        return [registry.normalize(topic) for topic in self.topics]

    def get_text_for_matching(self) -> str:
        """Get combined text for semantic matching.

        Returns:
            Combined title + venue + abstract for embedding.
        """
        parts = [self.title, self.venue]
        if self.abstract:
            parts.append(self.abstract)
        return " ".join(parts)
