"""Education model for academic credentials."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from resume_as_code.models.types import Year


class Education(BaseModel):
    """Educational credential record.

    Stores education information for resume rendering with support
    for honors, GPA, and display control.
    """

    model_config = ConfigDict(extra="forbid")

    degree: str
    institution: str
    graduation_year: Year | None = None  # YYYY format
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

        if self.graduation_year:
            parts.append(self.graduation_year)

        base = ", ".join(parts)

        if self.honors:
            base += f" - {self.honors}"

        if self.gpa and not self.honors:
            base += f" (GPA: {self.gpa})"

        return base
