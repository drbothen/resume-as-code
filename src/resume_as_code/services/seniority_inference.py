"""Seniority level inference from position titles and scope.

This module provides inference of seniority/experience level from:
1. Explicit seniority_level on work units
2. Position title pattern matching
3. Scope indicators (P&L, revenue, team size)
4. Work unit title fallback

Used by the HybridRanker to align work unit seniority with JD requirements.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from resume_as_code.models.job_description import ExperienceLevel

if TYPE_CHECKING:
    from resume_as_code.models.position import Position
    from resume_as_code.models.work_unit import WorkUnit


# Title patterns ordered from most senior to least (first match wins)
# Order matters: "Senior Manager" should match LEAD (manager) not SENIOR
TITLE_SENIORITY_PATTERNS: list[tuple[ExperienceLevel, list[str]]] = [
    (
        ExperienceLevel.EXECUTIVE,
        [
            r"\bcto\b",
            r"\bceo\b",
            r"\bcfo\b",
            r"\bcoo\b",
            r"\bcio\b",
            r"\bciso\b",
            r"\bvp\b",
            r"\bvice president\b",
            r"\bchief\b",
            r"\bevp\b",
            r"\bpresident\b",
            r"\bgeneral manager\b",
        ],
    ),
    (
        ExperienceLevel.PRINCIPAL,
        [
            r"\bprincipal\b",
            r"\bdistinguished\b",
            r"\bfellow\b",
        ],
    ),
    (
        ExperienceLevel.STAFF,
        [
            r"\bstaff\b",
            r"\barchitect\b",
        ],
    ),
    (
        ExperienceLevel.LEAD,
        [
            r"\blead\b",
            r"\btech lead\b",
            r"\bteam lead\b",
            r"\bengineering manager\b",
            r"\bmanager\b",
            r"\bdirector\b",
        ],
    ),
    (
        ExperienceLevel.SENIOR,
        [
            r"\bsenior\b",
            r"\bsr\.?\b",
            r"\bsr\s",
        ],
    ),
    # ENTRY comes BEFORE MID so "Junior Developer" matches ENTRY, not MID
    (
        ExperienceLevel.ENTRY,
        [
            r"\bjunior\b",
            r"\bjr\.?\b",
            r"\bjr\s",
            r"\bassociate\b",
            r"\bintern\b",
            r"\bentry\b",
            r"\bgraduate\b",
        ],
    ),
    (
        ExperienceLevel.MID,
        [
            r"\b(?:ii|iii|2|3)\b",
            r"\bdeveloper\b",
            r"\bengineer\b",
            r"\banalyst\b",
        ],
    ),
]


# Level ranking for comparison
_LEVEL_RANKS: dict[ExperienceLevel, int] = {
    ExperienceLevel.ENTRY: 1,
    ExperienceLevel.MID: 2,
    ExperienceLevel.SENIOR: 3,
    ExperienceLevel.LEAD: 4,
    ExperienceLevel.STAFF: 5,
    ExperienceLevel.PRINCIPAL: 6,
    ExperienceLevel.EXECUTIVE: 7,
}


def infer_seniority_from_title(title: str) -> ExperienceLevel:
    """Infer seniority level from a job title string.

    Patterns are matched in order from most senior to least, so
    "Senior Manager" matches LEAD (manager pattern) before SENIOR.

    Args:
        title: Position or job title to analyze.

    Returns:
        Inferred ExperienceLevel, defaults to MID if no patterns match.
    """
    title_lower = title.lower()

    for level, patterns in TITLE_SENIORITY_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, title_lower):
                return level

    return ExperienceLevel.MID  # Default for unrecognized titles


def infer_seniority(
    work_unit: WorkUnit,
    position: Position | None = None,
) -> ExperienceLevel:
    """Infer seniority level for a work unit.

    Priority order:
    1. Explicit seniority_level on work unit (if set)
    2. Position title analysis
    3. Scope indicators (team size, P&L)
    4. Work unit title analysis
    5. Default to MID

    Args:
        work_unit: The work unit to analyze.
        position: Optional attached position for title/scope data.

    Returns:
        Inferred or explicit ExperienceLevel.
    """
    # Priority 1: Explicit seniority on work unit
    if work_unit.seniority_level is not None:
        return work_unit.seniority_level

    # Priority 2: Position title
    if position and position.title:
        title_level = infer_seniority_from_title(position.title)

        # Priority 3: Scope indicators can boost level
        if position.scope:
            scope = position.scope
            # P&L responsibility = executive
            if scope.pl_responsibility:
                return ExperienceLevel.EXECUTIVE
            # Significant revenue = executive
            if scope.revenue and _parse_currency(scope.revenue) >= 100_000_000:
                return ExperienceLevel.EXECUTIVE
            # Large team = at least staff
            if scope.team_size and scope.team_size >= 50:
                return max(title_level, ExperienceLevel.STAFF, key=_level_rank)
            # Medium team = at least lead
            if scope.team_size and scope.team_size >= 10:
                return max(title_level, ExperienceLevel.LEAD, key=_level_rank)

        return title_level

    # Priority 4: Work unit title
    return infer_seniority_from_title(work_unit.title)


def calculate_seniority_alignment(
    work_unit_level: ExperienceLevel,
    jd_level: ExperienceLevel,
) -> float:
    """Calculate alignment score between work unit and JD seniority.

    Applies asymmetric penalties per AC4:
    - Overqualified (wu > jd): slight penalty (executive applying for senior)
    - Underqualified (wu < jd): larger penalty (entry applying for senior)

    Returns:
        Float between 0.0 and 1.0:
        - 1.0: Perfect match
        - Overqualified: 0.9 (1 level), 0.8 (2), 0.75 (3), 0.7 (4+)
        - Underqualified: 0.8 (1 level), 0.6 (2), 0.4 (3), 0.3 (4+)
    """
    wu_rank = _level_rank(work_unit_level)
    jd_rank = _level_rank(jd_level)

    diff = wu_rank - jd_rank  # Positive = overqualified, negative = underqualified

    if diff == 0:
        return 1.0

    if diff > 0:
        # Overqualified: slight penalty (executive applying for senior role)
        overqualified_scores = {1: 0.9, 2: 0.8, 3: 0.75}
        return overqualified_scores.get(diff, 0.7)
    else:
        # Underqualified: larger penalty (entry applying for senior role)
        underqualified_scores = {-1: 0.8, -2: 0.6, -3: 0.4}
        return underqualified_scores.get(diff, 0.3)


def _parse_currency(value: str) -> int:
    """Parse currency string to integer value.

    Examples:
        "$500M" -> 500_000_000
        "$2.5B" -> 2_500_000_000
        "$50K" -> 50_000

    Args:
        value: Currency string to parse.

    Returns:
        Integer value, or 0 if parsing fails.
    """
    if not value:
        return 0

    # Remove $ and commas
    cleaned = re.sub(r"[$,]", "", value.upper())

    # Extract number and suffix
    match = re.match(r"([\d.]+)\s*([KMB])?", cleaned)
    if not match:
        return 0

    number = float(match.group(1))
    suffix = match.group(2)

    multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    multiplier = multipliers.get(suffix, 1)

    return int(number * multiplier)


def _level_rank(level: ExperienceLevel) -> int:
    """Return numeric rank for level comparison.

    Args:
        level: ExperienceLevel to rank.

    Returns:
        Numeric rank (1-7), defaults to 2 (MID) for unknown.
    """
    return _LEVEL_RANKS.get(level, 2)
