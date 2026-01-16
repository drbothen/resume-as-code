"""Publication model for publications and speaking engagements."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

from resume_as_code.models.types import YearMonth

PublicationType = Literal["conference", "article", "whitepaper", "book", "podcast", "webinar"]


class Publication(BaseModel):
    """Publication or speaking engagement record.

    Stores publication and speaking engagement information for resume
    rendering with support for type classification and display control.
    """

    title: str
    type: PublicationType
    venue: str  # Conference name, publisher, blog name
    date: YearMonth  # YYYY-MM format
    url: HttpUrl | None = None
    display: bool = Field(default=True)

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

    def format_display(self) -> str:
        """Format for resume display.

        Speaking engagements: "Venue (Year) - Title"
        Written works: "Title, Venue (Year)"

        Returns:
            Formatted display string.
        """
        if self.is_speaking:
            return f"{self.venue} ({self.year}) - {self.title}"
        return f"{self.title}, {self.venue} ({self.year})"
