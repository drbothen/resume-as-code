"""Board role model for board and advisory positions."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

BoardRoleType = Literal["director", "advisory", "committee"]


class BoardRole(BaseModel):
    """Board or advisory role record.

    Stores board and advisory role information for resume rendering
    with support for role type classification and display control.
    """

    organization: str
    role: str
    type: BoardRoleType = "advisory"
    start_date: str  # YYYY-MM format
    end_date: str | None = None  # None = current
    focus: str | None = None
    display: bool = Field(default=True)

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate YYYY-MM date format.

        Args:
            v: Date string or None.

        Returns:
            Validated date string or None.

        Raises:
            ValueError: If date format is invalid.
        """
        if v is None:
            return None
        if not re.match(r"^\d{4}-\d{2}$", str(v)):
            raise ValueError("Date must be in YYYY-MM format")
        return v

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
