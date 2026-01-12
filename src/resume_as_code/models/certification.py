"""Certification model for professional certifications."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Certification(BaseModel):
    """Professional certification record.

    Stores certification information for resume rendering with support
    for expiration tracking and display control.
    """

    name: str
    issuer: str | None = None
    date: str | None = None  # YYYY-MM format
    expires: str | None = None  # YYYY-MM format
    credential_id: str | None = None
    url: HttpUrl | None = None
    display: bool = Field(default=True)  # Allow hiding without deleting

    @field_validator("date", "expires", mode="before")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate and normalize date to YYYY-MM format.

        Accepts YYYY-MM or YYYY-MM-DD formats, normalizes to YYYY-MM.

        Args:
            v: Date string or None.

        Returns:
            Normalized YYYY-MM date string or None.

        Raises:
            ValueError: If date format is invalid.
        """
        if v is None:
            return None
        if not re.match(r"^\d{4}-\d{2}(-\d{2})?$", v):
            raise ValueError("Date must be in YYYY-MM or YYYY-MM-DD format")
        return v[:7]  # Normalize to YYYY-MM

    def get_status(self) -> Literal["active", "expires_soon", "expired"]:
        """Calculate certification status based on expiration.

        Returns:
            Status string: "active", "expires_soon", or "expired".
        """
        if not self.expires:
            return "active"

        # Parse YYYY-MM to first day of month
        expires_date = datetime.strptime(self.expires, "%Y-%m").date()
        today = date.today()

        if expires_date < today:
            return "expired"

        # Check if expires within 90 days
        if expires_date < today + timedelta(days=90):
            return "expires_soon"

        return "active"

    def format_display(self) -> str:
        """Format certification for resume display.

        Returns:
            Formatted string like "CISSP (ISC2, 2023 - expires 2026)".
        """
        parts = [self.name]
        if self.issuer:
            issuer_part = f"({self.issuer}"
            if self.date:
                issuer_part += f", {self.date[:4]}"  # Year only
            if self.expires:
                issuer_part += f" - expires {self.expires[:4]}"
            issuer_part += ")"
            parts.append(issuer_part)
        elif self.date:
            parts.append(f"({self.date[:4]})")
        return " ".join(parts)
