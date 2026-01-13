"""Education model for academic credentials."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator


class Education(BaseModel):
    """Educational credential record.

    Stores education information for resume rendering with support
    for honors, GPA, and display control.
    """

    degree: str
    institution: str
    year: str | None = None  # YYYY format
    honors: str | None = None  # e.g., "Magna Cum Laude", "With Distinction"
    gpa: str | None = None  # e.g., "3.8/4.0"
    display: bool = Field(default=True)  # Allow hiding without deleting

    @field_validator("degree", "institution", mode="before")
    @classmethod
    def validate_required_strings(cls, v: str) -> str:
        """Validate that required string fields are not empty.

        Args:
            v: Field value.

        Returns:
            Stripped string value.

        Raises:
            ValueError: If field is empty or whitespace-only.
        """
        if not isinstance(v, str):
            raise ValueError("Field must be a string")
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty")
        return stripped

    @field_validator("year", mode="before")
    @classmethod
    def validate_year_format(cls, v: str | None) -> str | None:
        """Validate and normalize year to YYYY format.

        Accepts YYYY or longer formats (e.g., YYYY-MM), normalizes to YYYY.

        Args:
            v: Year string or None.

        Returns:
            Normalized YYYY year string or None.

        Raises:
            ValueError: If year format is invalid.
        """
        if v is None:
            return None
        v_str = str(v)
        if not re.match(r"^\d{4}", v_str):
            raise ValueError("Year must be in YYYY format")
        return v_str[:4]

    def format_display(self) -> str:
        """Format education for resume display.

        Returns:
            Formatted string like "BS Computer Science, UT Austin, 2012 - Magna Cum Laude".

        Examples:
            - "BS Computer Science, UT Austin, 2012 - Magna Cum Laude"
            - "MS Cybersecurity, Georgia Tech, 2018"
            - "MBA, Harvard Business School"
        """
        parts = [self.degree, self.institution]

        if self.year:
            parts.append(self.year)

        base = ", ".join(parts)

        if self.honors:
            base += f" - {self.honors}"

        if self.gpa and not self.honors:
            base += f" (GPA: {self.gpa})"

        return base
