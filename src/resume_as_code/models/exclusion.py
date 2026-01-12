"""Exclusion reason models for plan command."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExclusionType(str, Enum):
    """Types of exclusion reasons."""

    LOW_RELEVANCE = "low_relevance"
    BELOW_THRESHOLD = "below_threshold"


@dataclass
class ExclusionReason:
    """Reason why a Work Unit was excluded from selection."""

    type: ExclusionType
    message: str
    suggestion: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        """Convert to dictionary for JSON serialization.

        Returns:
            A dict with keys:
                - type: The ExclusionType value as a string
                - message: The human-readable exclusion message
                - suggestion: Optional improvement suggestion, or None
        """
        return {
            "type": self.type.value,
            "message": self.message,
            "suggestion": self.suggestion,
        }


# Threshold below which a Work Unit is considered "low relevance"
LOW_RELEVANCE_THRESHOLD = 0.2


def get_exclusion_reason(score: float) -> ExclusionReason:
    """Determine why a Work Unit was excluded based on its score.

    Args:
        score: The relevance score (0.0 to 1.0)

    Returns:
        ExclusionReason with appropriate type and message
    """
    if score < LOW_RELEVANCE_THRESHOLD:
        return ExclusionReason(
            type=ExclusionType.LOW_RELEVANCE,
            message=f"Low relevance score ({score:.0%})",
            suggestion="Consider adding JD keywords to this Work Unit",
        )
    return ExclusionReason(
        type=ExclusionType.BELOW_THRESHOLD,
        message=f"Below selection threshold ({score:.0%})",
        suggestion=None,
    )
