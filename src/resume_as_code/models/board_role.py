"""Board role model for board and advisory positions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from resume_as_code.models.types import YearMonth

BoardRoleType = Literal["director", "advisory", "committee"]


class BoardRole(BaseModel):
    """Board or advisory role record.

    Stores board and advisory role information for resume rendering
    with support for role type classification and display control.
    """

    organization: str
    role: str
    type: BoardRoleType = "advisory"
    start_date: YearMonth  # YYYY-MM format
    end_date: YearMonth | None = None  # None = current
    focus: str | None = None
    display: bool = Field(default=True)
    priority: Literal["always", "normal", "low"] | None = Field(
        default=None,
        description="Curation priority: 'always' forces inclusion regardless of JD relevance",
    )

    @property
    def is_current(self) -> bool:
        """Check if this is a current role.

        Returns:
            True if end_date is None, indicating an ongoing role.
        """
        return self.end_date is None

    def format_date_range(self) -> str:
        """Format date range for display.

        Returns:
            Formatted date range like "2023 - Present" or "2020 - 2023".
        """
        start_year = self.start_date[:4]
        if self.end_date:
            end_year = self.end_date[:4]
            return f"{start_year} - {end_year}"
        return f"{start_year} - Present"
