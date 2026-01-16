"""Position model for employment history.

Represents employment positions that work units can reference.
Supports career progression tracking via promoted_from field.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from resume_as_code.models.scope import Scope

EmploymentType = Literal["full-time", "part-time", "contract", "consulting", "freelance"]


# Backwards compatibility alias - PositionScope is deprecated, use Scope instead
PositionScope = Scope


class Position(BaseModel):
    """Employment position record.

    Represents a role at an employer. Work units reference positions
    via position_id to group achievements under employers.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Unique identifier like 'pos-techcorp-senior'")
    employer: str = Field(description="Company/organization name")
    title: str = Field(description="Job title")
    location: str | None = Field(default=None, description="Location (city, state/country)")
    start_date: str = Field(description="Start date in YYYY-MM format")
    end_date: str | None = Field(
        default=None, description="End date in YYYY-MM format, None for current"
    )
    employment_type: EmploymentType | None = Field(default=None, description="Type of employment")
    promoted_from: str | None = Field(
        default=None, description="ID of previous position (for promotions)"
    )
    description: str | None = Field(default=None, description="Optional role summary")
    scope: Scope | None = Field(
        default=None, description="Scope indicators for executive positions"
    )

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate YYYY-MM date format."""
        if v is None:
            return None
        if not re.match(r"^\d{4}-\d{2}$", str(v)):
            raise ValueError("Date must be in YYYY-MM format")
        return v

    @model_validator(mode="after")
    def validate_date_range(self) -> Position:
        """Validate that end_date is not before start_date."""
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError(
                f"end_date ({self.end_date}) must not be before start_date ({self.start_date})"
            )
        return self

    @property
    def is_current(self) -> bool:
        """Check if this is a current position."""
        return self.end_date is None

    def format_date_range(self) -> str:
        """Format date range for display."""
        start_year = self.start_date[:4]
        if self.end_date:
            end_year = self.end_date[:4]
            return f"{start_year} - {end_year}"
        return f"{start_year} - Present"
