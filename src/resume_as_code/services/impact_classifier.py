"""Impact classification for work unit outcomes.

Story 7.13: Impact Category Classification

Classifies work unit outcomes into impact categories (financial, operational,
talent, customer, organizational, technical) and matches against role types
for relevance scoring.

Research Basis: Resume best practices emphasize matching achievement types
to role expectations. Studies show quantified impacts are 78% more compelling
to recruiters than qualitative claims.
"""

from __future__ import annotations

import re
from typing import Literal, NamedTuple

# Impact category type
ImpactCategory = Literal[
    "financial",
    "operational",
    "talent",
    "customer",
    "organizational",
    "technical",
]

# Role type for JD matching
RoleType = Literal[
    "sales",
    "engineering",
    "product",
    "hr",
    "executive",
    "marketing",
    "operations",
    "finance",
    "general",
]


class ImpactMatch(NamedTuple):
    """An impact category match with confidence score.

    Attributes:
        category: The impact category (financial, operational, etc.)
        confidence: Confidence score from 0.0 to 1.0
        matched_patterns: Which regex patterns matched (for debugging)
    """

    category: ImpactCategory
    confidence: float
    matched_patterns: list[str]


# Impact detection patterns (regex)
# Each pattern list is checked against lowercased text
IMPACT_PATTERNS: dict[ImpactCategory, list[str]] = {
    "financial": [
        r"\$[\d,]+[KMB]?",  # Dollar amounts: $500K, $2M, $1,000
        r"\brevenue\b",  # Revenue mentions
        r"\bcost\s*sav",  # Cost savings
        r"\broi\b",  # Return on investment
        r"\bprofit\b",  # Profit mentions
        r"\bbudget\b",  # Budget impact
        r"\bmargin\b",  # Margin improvements
        r"\barr\b",  # Annual recurring revenue
        r"\bmrr\b",  # Monthly recurring revenue
    ],
    "operational": [
        r"\d+%\s*(?:reduc|improv|increas|faster|efficiency)",  # Percentage improvements
        r"\bautomat",  # Automation
        r"\bstreamlin",  # Streamlining
        r"\boptimiz",  # Optimization
        r"\blatency\b",  # Latency reduction
        r"\buptime\b",  # Uptime improvements
        r"\bthroughput\b",  # Throughput gains
        r"\bdeployment\b",  # Deployment improvements
        r"\bdowntime\b",  # Downtime reduction
        r"\bsla\b",  # SLA improvements
        r"\d+x\s*(?:faster|improvement)",  # Multiplier improvements
    ],
    "talent": [
        r"\bhired?\s+\d+",  # Hiring: "hired 15"
        r"\bmentor",  # Mentoring
        r"\bteam\s+of\s+\d+",  # Team size: "team of 20"
        r"\bretention\b",  # Retention (also in customer)
        r"\bonboard",  # Onboarding
        r"\btrain",  # Training
        r"\bcoach",  # Coaching
        r"\bdeveloped\s+\d+\s+engineer",  # Career development
        r"\bpromot",  # Promotions
    ],
    "customer": [
        r"\bnps\b",  # Net Promoter Score
        r"\bcsat\b",  # Customer satisfaction
        r"\bcustomer\s+satisfaction",  # Customer satisfaction
        r"\buser\s+growth\b",  # User growth
        r"\bchurn\b",  # Churn reduction
        r"\bacquisition\b",  # Customer acquisition
        r"\bcustomer\s+retention",  # Customer retention
        r"\bconversion\b",  # Conversion rate
        r"\bdau\b|\bmau\b",  # Daily/Monthly active users
        r"\buser\s+engagement",  # User engagement
    ],
    "organizational": [
        r"\btransform",  # Transformation
        r"\bculture\b",  # Culture change
        r"\bstrateg",  # Strategic initiatives
        r"\brestructur",  # Restructuring
        r"\bmerger\b",  # Mergers
        r"\binitiative\b",  # Initiatives
        r"\bchange\s+management",  # Change management
        r"\breorganiz",  # Reorganization
        r"\bvision\b",  # Vision setting
    ],
    "technical": [
        r"\barchitect",  # Architecture
        r"\bimplement",  # Implementation
        r"\bdeploy",  # Deployment
        r"\bscale\b",  # Scaling
        r"\bmigrat",  # Migration
        r"\binfrastructure\b",  # Infrastructure
        r"\brefactor",  # Refactoring
        r"\bintegrat",  # Integration
        r"\bapi\b",  # API development
        r"\bmicroservices?\b",  # Microservices
    ],
}


def classify_impact(outcome_text: str) -> list[ImpactMatch]:
    """Classify outcome text into impact categories with confidence scores.

    Args:
        outcome_text: The outcome text to classify (result + quantified_impact + business_value)

    Returns:
        List of ImpactMatch tuples, sorted by confidence (highest first).
        Empty list if no patterns match.
    """
    text = outcome_text.lower()
    results: list[ImpactMatch] = []

    for category, patterns in IMPACT_PATTERNS.items():
        matched_patterns: list[str] = []

        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matched_patterns.append(pattern)

        if matched_patterns:
            # Confidence based on number of pattern matches
            # 1 match = 0.3, 2 matches = 0.6, 3+ matches = 0.9, cap at 1.0
            confidence = min(1.0, len(matched_patterns) * 0.3)
            results.append(
                ImpactMatch(
                    category=category,
                    confidence=confidence,
                    matched_patterns=matched_patterns,
                )
            )

    # Sort by confidence, highest first
    return sorted(results, key=lambda x: -x.confidence)


def has_quantified_impact(outcome_text: str) -> bool:
    """Check if outcome contains quantified metrics.

    Looks for patterns like:
    - Percentages: 40%, 50%
    - Dollar amounts: $500K, $2M, $1,000,000
    - Multipliers: 10x, 3x
    - Time metrics: 2 hours, 3 days, 50% faster

    Args:
        outcome_text: Text to check for quantification

    Returns:
        True if quantified metrics are present
    """
    patterns = [
        r"\d+%",  # Percentages
        r"\$[\d,]+[KMB]?",  # Dollar amounts
        r"\d+x\b",  # Multipliers (10x, 3x)
        r"\d+\s*(?:hours?|days?|weeks?|months?)",  # Time metrics
        r"(?:reduced|improved|increased)\s+.*?\d+",  # Action + number
    ]

    return any(re.search(pattern, outcome_text, re.IGNORECASE) for pattern in patterns)


# Title patterns to role types (first match wins)
# Order matters: more specific patterns checked first
ROLE_TYPE_PATTERNS: list[tuple[RoleType, list[str]]] = [
    (
        "executive",
        [
            r"\bcto\b",
            r"\bceo\b",
            r"\bcfo\b",
            r"\bcoo\b",
            r"\bcio\b",
            r"\bvp\b",
            r"\bvice president\b",
            r"\bchief\b",
            r"\bdirector\b",
            r"\bhead of\b",
            r"\bgeneral manager\b",
        ],
    ),
    (
        "sales",
        [
            r"\bsales\b",
            r"\baccount\s+(?:executive|manager)\b",
            r"\bbusiness\s+development\b",
            r"\bsdr\b",
            r"\bbdr\b",
            r"\brevenue\b",
            r"\bpartnership\b",
        ],
    ),
    (
        "marketing",
        [
            r"\bmarketing\b",
            r"\bgrowth\b",
            r"\bbrand\b",
            r"\bcontent\b",
            r"\bseo\b",
            r"\bsem\b",
            r"\bdemand\s+gen\b",
        ],
    ),
    (
        "product",
        [
            r"\bproduct\s+(?:manager|owner|lead)\b",
            r"\bpm\b",
            r"\bux\b",
            r"\bui\b",
            r"\bdesigner\b",
        ],
    ),
    (
        "hr",
        [
            r"\bhr\b",
            r"\bhuman\s+resources\b",
            r"\bpeople\s+(?:ops|operations)\b",
            r"\btalent\b",
            r"\brecruit",
        ],
    ),
    (
        "finance",
        [
            r"\bfinance\b",
            r"\baccounting\b",
            r"\bcontroller\b",
            r"\bfp&a\b",
            r"\btreasury\b",
        ],
    ),
    (
        "operations",
        [
            r"\boperations\b",
            r"\bops\b",
            r"\bsupply\s+chain\b",
            r"\blogistics\b",
            r"\bprocurement\b",
        ],
    ),
    (
        "engineering",
        [
            r"\bengineer",
            r"\bdeveloper\b",
            r"\bsoftware\b",
            r"\bsre\b",
            r"\bdevops\b",
            r"\barchitect\b",
            r"\bplatform\b",
            r"\bdata\b",
            r"\bbackend\b",
            r"\bfrontend\b",
            r"\bfull\s*stack\b",
        ],
    ),
]


# Role type to prioritized impact categories
ROLE_IMPACT_PRIORITY: dict[RoleType, list[ImpactCategory]] = {
    "sales": ["financial", "customer"],
    "engineering": ["operational", "technical"],
    "product": ["customer", "operational"],
    "hr": ["talent", "organizational"],
    "executive": ["organizational", "financial"],
    "marketing": ["customer", "financial"],
    "operations": ["operational", "financial"],
    "finance": ["financial", "operational"],
    "general": ["operational", "technical"],  # Default fallback
}


def infer_role_type(jd_title: str | None) -> RoleType:
    """Infer role type from job description title.

    Args:
        jd_title: The job title from the JD

    Returns:
        Inferred RoleType, defaults to "general" if no match
    """
    if not jd_title:
        return "general"

    title_lower = jd_title.lower()

    for role_type, patterns in ROLE_TYPE_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, title_lower):
                return role_type

    return "general"


def calculate_impact_alignment(
    work_unit_impacts: list[ImpactMatch],
    role_type: RoleType,
    is_quantified: bool,
    quantified_boost: float = 1.25,
) -> float:
    """Calculate alignment score between work unit impacts and role expectations.

    Args:
        work_unit_impacts: Classified impacts from the work unit
        role_type: Inferred role type from JD
        is_quantified: Whether the outcome has quantified metrics
        quantified_boost: Multiplier for quantified impacts (default 1.25 = 25% boost)

    Returns:
        Alignment score between 0.0 and 1.0
    """
    if not work_unit_impacts:
        # No detected impacts - neutral score
        return 0.5

    expected_impacts = ROLE_IMPACT_PRIORITY.get(role_type, [])
    if not expected_impacts:
        return 0.5

    alignment_score = 0.0

    for impact in work_unit_impacts:
        if impact.category in expected_impacts:
            # Primary impact match (first in list) gets full weight
            # Secondary impact match gets half weight
            if impact.category == expected_impacts[0]:
                alignment_score += impact.confidence * 1.0
            else:
                alignment_score += impact.confidence * 0.5

    # Apply quantified boost (default 25%)
    if is_quantified:
        alignment_score *= quantified_boost

    # Cap at 1.0
    return min(1.0, alignment_score)
