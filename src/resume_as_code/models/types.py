"""Reusable annotated types for consistent validation across models.

This module provides standardized date types that eliminate duplicate validators
across Position, Education, Certification, BoardRole, and Publication models.

Usage:
    from resume_as_code.models.types import YearMonth, Year

    class Position(BaseModel):
        start_date: YearMonth
        end_date: YearMonth | None = None

    class Education(BaseModel):
        graduation_year: Year | None = None
"""

from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import BeforeValidator, WithJsonSchema


def _normalize_year_month(v: Any) -> str | None:
    """Normalize input to YYYY-MM format.

    Accepts:
    - "2024-01" -> "2024-01"
    - "2024-01-15" -> "2024-01" (truncates day)
    - None -> None (for optional fields)

    Args:
        v: Input value (string expected, or None).

    Returns:
        Normalized YYYY-MM string, or None.

    Raises:
        ValueError: If format is invalid (non-None, non-matching).
    """
    # CRITICAL: BeforeValidator runs on ALL values including None
    # Return None to let Pydantic's type system enforce required vs optional
    if v is None:
        return None
    v_str = str(v).strip()
    # Accept YYYY-MM or YYYY-MM-DD, normalize to YYYY-MM
    if re.match(r"^\d{4}-\d{2}(-\d{2})?$", v_str):
        return v_str[:7]
    raise ValueError(f"Date must be in YYYY-MM format, got: {v_str!r}")


def _normalize_year(v: Any) -> str | None:
    """Normalize input to YYYY format.

    Accepts:
    - 2024 (int) -> "2024"
    - "2024" -> "2024"
    - "2024-01" -> "2024" (truncates month)
    - None -> None (for optional fields)

    Args:
        v: Input value (string or int, or None).

    Returns:
        Normalized YYYY string, or None.

    Raises:
        ValueError: If format is invalid (non-None, non-matching).
    """
    # CRITICAL: BeforeValidator runs on ALL values including None
    if v is None:
        return None
    v_str = str(v).strip()
    if re.match(r"^\d{4}", v_str):
        return v_str[:4]
    raise ValueError(f"Year must be in YYYY format, got: {v_str!r}")


# Type aliases for use in model definitions
# NOTE: WithJsonSchema overrides schema to include pattern constraint
YearMonth = Annotated[
    str,
    BeforeValidator(_normalize_year_month),
    WithJsonSchema(
        {
            "type": "string",
            "pattern": r"^\d{4}-\d{2}$",
            "description": "Date in YYYY-MM format",
        }
    ),
]
"""Date type for YYYY-MM format strings.

Used for:
- Position.start_date, Position.end_date
- Certification.date, Certification.expires
- BoardRole.start_date, BoardRole.end_date
- Publication.date
"""

Year = Annotated[
    str,
    BeforeValidator(_normalize_year),
    WithJsonSchema(
        {
            "type": "string",
            "pattern": r"^\d{4}$",
            "description": "Year in YYYY format",
        }
    ),
]
"""Year type for YYYY format strings.

Accepts both int and str input, normalizes to 4-digit string.

Used for:
- Education.graduation_year
"""
