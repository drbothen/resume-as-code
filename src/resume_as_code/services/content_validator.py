"""Content quality validation for Work Units."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import get_close_matches
from typing import Any

# Weak verbs with strong alternatives
WEAK_VERBS: dict[str, list[str]] = {
    "managed": ["orchestrated", "directed", "coordinated", "oversaw"],
    "handled": ["resolved", "processed", "executed", "administered"],
    "helped": ["enabled", "facilitated", "supported", "empowered"],
    "worked on": ["developed", "built", "created", "implemented"],
    "was responsible for": ["owned", "led", "drove", "championed"],
    "did": ["executed", "delivered", "accomplished", "achieved"],
    "made": ["produced", "generated", "crafted", "designed"],
    "got": ["secured", "acquired", "obtained", "earned"],
    "used": ["leveraged", "utilized", "applied", "employed"],
    "assisted": ["supported", "enabled", "contributed to", "facilitated"],
}

# Optimal bullet character range
BULLET_CHAR_MIN = 100
BULLET_CHAR_MAX = 160


@dataclass
class ContentWarning:
    """A content quality warning (not an error)."""

    code: str
    message: str
    path: str
    suggestion: str
    severity: str = field(default="warning")  # warning or info


def validate_content_quality(work_unit: dict[str, Any], file_path: str) -> list[ContentWarning]:
    """Validate content quality of a Work Unit.

    Checks for:
    - Weak action verbs (managed, handled, helped, etc.)
    - Verb repetition across actions
    - Missing quantification in outcomes

    Returns warnings (not errors) for content improvements.
    """
    warnings: list[ContentWarning] = []

    # Check actions for weak verbs
    actions = work_unit.get("actions", [])
    verb_usage: dict[str, int] = {}

    for i, action in enumerate(actions):
        if not isinstance(action, str):
            continue

        # Check for weak verbs
        action_lower = action.lower()
        for weak_verb, alternatives in WEAK_VERBS.items():
            if re.search(rf"\b{re.escape(weak_verb)}\b", action_lower):
                warnings.append(
                    ContentWarning(
                        code="WEAK_ACTION_VERB",
                        message=f"Action {i + 1} uses weak verb '{weak_verb}'",
                        path=f"{file_path}:actions[{i}]",
                        suggestion=f"Consider stronger verbs: {', '.join(alternatives[:3])}",
                    )
                )

        # Track verb usage for repetition (first word of action)
        words = action.split()
        if words:
            first_word = words[0].lower()
            verb_usage[first_word] = verb_usage.get(first_word, 0) + 1

    # Check for verb repetition
    for verb, count in verb_usage.items():
        if count > 1 and verb not in ("the", "a", "an", "to", "and", "or", "for", "with", "of"):
            warnings.append(
                ContentWarning(
                    code="VERB_REPETITION",
                    message=f"Verb '{verb}' used {count} times in actions",
                    path=f"{file_path}:actions",
                    suggestion="Vary your action verbs for stronger impact",
                )
            )

    # Check outcome for quantification
    outcome = work_unit.get("outcome", {})
    if isinstance(outcome, dict):
        result = outcome.get("result", "")
        if result and isinstance(result, str) and not _has_quantification(result):
            warnings.append(
                ContentWarning(
                    code="MISSING_QUANTIFICATION",
                    message="Outcome result lacks quantification",
                    path=f"{file_path}:outcome.result",
                    suggestion="Add metrics (%, $, time saved, etc.) to strengthen impact",
                    severity="info",
                )
            )

    return warnings


def validate_content_density(work_unit: dict[str, Any], file_path: str) -> list[ContentWarning]:
    """Validate content density (character counts, etc.).

    Checks that action bullet points are within optimal character range (100-160).

    Returns warnings for bullets that are too short or too long.
    """
    warnings: list[ContentWarning] = []

    actions = work_unit.get("actions", [])
    for i, action in enumerate(actions):
        if not isinstance(action, str):
            continue

        char_count = len(action)
        if char_count < BULLET_CHAR_MIN:
            warnings.append(
                ContentWarning(
                    code="BULLET_TOO_SHORT",
                    message=f"Action {i + 1} is {char_count} chars (min: {BULLET_CHAR_MIN})",
                    path=f"{file_path}:actions[{i}]",
                    suggestion="Expand with more detail about impact or method",
                )
            )
        elif char_count > BULLET_CHAR_MAX:
            warnings.append(
                ContentWarning(
                    code="BULLET_TOO_LONG",
                    message=f"Action {i + 1} is {char_count} chars (max: {BULLET_CHAR_MAX})",
                    path=f"{file_path}:actions[{i}]",
                    suggestion="Consider splitting into multiple focused bullets",
                )
            )

    return warnings


def validate_position_reference(
    work_unit: dict[str, Any],
    file_path: str,
    valid_position_ids: set[str] | None = None,
) -> list[ContentWarning]:
    """Validate position_id reference in a Work Unit.

    Checks for:
    - Missing position_id (info severity - optional field)
    - Invalid position_id that doesn't exist in positions.yaml (error severity)

    Args:
        work_unit: Work Unit data dictionary.
        file_path: Path to the Work Unit file.
        valid_position_ids: Set of valid position IDs from positions.yaml.
            If None, only checks for missing position_id.

    Returns:
        List of ContentWarning objects.
    """
    warnings: list[ContentWarning] = []
    position_id = work_unit.get("position_id")

    if position_id is None:
        # Missing position_id is just an info-level suggestion
        warnings.append(
            ContentWarning(
                code="MISSING_POSITION_ID",
                message="Work unit has no position_id",
                path=file_path,
                suggestion="Add position_id to group under employer in resume output",
                severity="info",
            )
        )
    elif valid_position_ids is not None and position_id not in valid_position_ids:
        # Invalid position_id reference is a serious issue
        # Try to suggest similar position IDs
        suggestion_text = (
            "Run 'resume list positions' to see valid IDs or create with 'resume new position'"
        )
        if valid_position_ids:
            matches = get_close_matches(position_id, list(valid_position_ids), n=1, cutoff=0.6)
            if matches:
                suggestion_text = f"Did you mean '{matches[0]}'? {suggestion_text}"

        warnings.append(
            ContentWarning(
                code="INVALID_POSITION_ID",
                message=f"position_id '{position_id}' not found in positions.yaml",
                path=f"{file_path}:position_id",
                suggestion=suggestion_text,
                severity="error",
            )
        )

    return warnings


def _has_quantification(text: str) -> bool:
    """Check if text contains quantification.

    Looks for:
    - Percentages (40%)
    - Currency ($50,000)
    - Multipliers (3x)
    - Time units (30 min, 5 hours)
    - Abbreviations (50K, 2M)
    - Impact words with metrics (reduced by X, improved X%)
    """
    patterns = [
        r"\d+%",  # Percentages
        r"\$[\d,]+",  # Currency
        r"\d+x",  # Multipliers
        r"\d+\s*(?:ms|secs?|mins?|hours?|days?)",  # Time (with plurals)
        r"\d+[KMB]",  # Abbreviations
        # Impact words must be near numbers/metrics to count as quantification
        r"(?:reduced|increased|improved|saved|generated)\s+(?:by\s+)?\d",
        # Or just any number that looks metric-like
        r"\b\d+(?:\.\d+)?\s*(?:%|x|\$|K|M|B|ms|sec|min|hour|day)\b",
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
