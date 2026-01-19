"""Archetype inference for work unit classification.

Story 12.1: Add Required Archetype Field with Inference Migration

Infers work unit archetypes from content using rule-based classification
with confidence scoring. Used during schema migration to populate the
required archetype field for existing work units.

Classification Strategy:
- Rule-based with multi-signal fusion (keywords 40%, tags 40%, signals 20%)
- Confidence scoring from 0.0 to 1.0
- Fallback to 'minimal' when confidence < 0.3
"""

from __future__ import annotations

from typing import Any, NamedTuple

from resume_as_code.models.work_unit import WorkUnitArchetype


class ArchetypeInference(NamedTuple):
    """Result of archetype inference with confidence score.

    Attributes:
        archetype: The inferred WorkUnitArchetype
        confidence: Confidence score from 0.0 to 1.0
        matched_signals: Dictionary of signal types to matched items (for debugging)
    """

    archetype: WorkUnitArchetype
    confidence: float
    matched_signals: dict[str, list[str]]


# Archetype classification rules
# Each archetype has keywords, tags, problem signals, and action signals
ARCHETYPE_RULES: dict[str, dict[str, list[str]]] = {
    "greenfield": {
        "keywords": [
            "built",
            "created",
            "designed",
            "architected",
            "launched",
            "new system",
            "from scratch",
            "greenfield",
            "platform",
            "pioneered",
            "established",
        ],
        "tags": ["greenfield", "architecture", "new-feature", "launch", "platform"],
        "problem_signals": ["need", "gap", "opportunity", "no existing", "required"],
        "action_signals": ["designed", "built", "architected", "engineered", "created"],
    },
    "migration": {
        "keywords": [
            "migrated",
            "upgraded",
            "transitioned",
            "converted",
            "legacy",
            "modernized",
            "refactored",
            "moved to",
            "ported",
        ],
        "tags": ["migration", "upgrade", "modernization", "refactor", "legacy"],
        "problem_signals": [
            "legacy",
            "outdated",
            "end of life",
            "technical debt",
            "deprecated",
        ],
        "action_signals": ["migrated", "transitioned", "converted", "upgraded", "ported"],
    },
    "optimization": {
        "keywords": [
            "optimized",
            "improved",
            "reduced",
            "increased efficiency",
            "performance",
            "cost reduction",
            "streamlined",
            "faster",
            "cheaper",
        ],
        "tags": [
            "optimization",
            "performance",
            "cost-reduction",
            "efficiency",
            "tuning",
        ],
        "problem_signals": ["slow", "expensive", "inefficient", "bottleneck", "latency"],
        "action_signals": ["optimized", "reduced", "improved", "streamlined", "tuned"],
    },
    "incident": {
        "keywords": [
            "incident",
            "outage",
            "vulnerability",
            "security",
            "assessment",
            "penetration",
            "remediated",
            "responded",
            "pentest",
            "audit",
        ],
        "tags": ["incident", "security", "vulnerability", "oncall", "pentest", "audit"],
        "problem_signals": [
            "vulnerability",
            "breach",
            "outage",
            "attack",
            "exploit",
            "risk",
        ],
        "action_signals": [
            "assessed",
            "remediated",
            "responded",
            "discovered",
            "patched",
        ],
    },
    "leadership": {
        "keywords": [
            "led",
            "mentored",
            "hired",
            "built team",
            "grew",
            "managed",
            "coached",
            "developed talent",
            "onboarded",
        ],
        "tags": ["leadership", "team", "hiring", "mentorship", "management", "coaching"],
        "problem_signals": ["team gap", "capability", "talent", "growth", "headcount"],
        "action_signals": ["led", "mentored", "hired", "built", "grew", "coached"],
    },
    "strategic": {
        "keywords": [
            "strategy",
            "roadmap",
            "architecture decision",
            "aligned",
            "framework",
            "standards",
            "governance",
            "vision",
        ],
        "tags": ["strategic", "architecture", "roadmap", "governance", "standards"],
        "problem_signals": [
            "alignment",
            "direction",
            "standards",
            "framework",
            "inconsistent",
        ],
        "action_signals": ["developed", "established", "defined", "aligned", "created"],
    },
    "transformation": {
        "keywords": [
            "transformed",
            "revolutionized",
            "scaled",
            "enterprise",
            "organization-wide",
            "digital transformation",
            "company-wide",
        ],
        "tags": ["transformation", "digital", "enterprise", "scale", "company-wide"],
        "problem_signals": ["organizational", "enterprise", "transformation", "scale"],
        "action_signals": ["transformed", "revolutionized", "scaled", "overhauled"],
    },
    "cultural": {
        "keywords": [
            "culture",
            "dei",
            "engagement",
            "inclusion",
            "diversity",
            "values",
            "employee experience",
            "morale",
        ],
        "tags": ["culture", "dei", "engagement", "inclusion", "diversity", "values"],
        "problem_signals": [
            "culture",
            "engagement",
            "inclusion",
            "morale",
            "retention",
        ],
        "action_signals": ["championed", "fostered", "cultivated", "promoted", "built"],
    },
    "minimal": {
        # Fallback archetype - no specific signals
        "keywords": [],
        "tags": ["minimal", "quick-capture"],
        "problem_signals": [],
        "action_signals": [],
    },
}

# Confidence threshold below which we fall back to 'minimal'
CONFIDENCE_THRESHOLD = 0.3


def _combine_text(work_unit_data: dict[str, Any]) -> str:
    """Combine work unit text fields for keyword matching.

    Extracts and concatenates title, problem statement, actions, and outcome
    into a single searchable string.

    Args:
        work_unit_data: Work unit dictionary with PAR fields

    Returns:
        Combined text from all relevant fields
    """
    parts: list[str] = []

    # Title
    if title := work_unit_data.get("title"):
        parts.append(str(title))

    # Problem statement
    if problem := work_unit_data.get("problem"):
        if isinstance(problem, dict):
            if statement := problem.get("statement"):
                parts.append(str(statement))
            if context := problem.get("context"):
                parts.append(str(context))
        elif isinstance(problem, str):
            parts.append(problem)

    # Actions
    if (actions := work_unit_data.get("actions")) and isinstance(actions, list):
        for action in actions:
            parts.append(str(action))

    # Outcome
    if outcome := work_unit_data.get("outcome"):
        if isinstance(outcome, dict):
            if result := outcome.get("result"):
                parts.append(str(result))
            if business_value := outcome.get("business_value"):
                parts.append(str(business_value))
            if quantified_impact := outcome.get("quantified_impact"):
                parts.append(str(quantified_impact))
        elif isinstance(outcome, str):
            parts.append(outcome)

    return " ".join(parts)


def _count_matches(patterns: list[str], text: str) -> tuple[int, list[str]]:
    """Count how many patterns match in the text.

    Args:
        patterns: List of patterns to search for
        text: Text to search in (case-insensitive)

    Returns:
        Tuple of (match count, list of matched patterns)
    """
    text_lower = text.lower()
    matched: list[str] = []

    for pattern in patterns:
        if pattern.lower() in text_lower:
            matched.append(pattern)

    return len(matched), matched


def _calculate_score(
    rules: dict[str, list[str]],
    text: str,
    tags: list[str],
) -> tuple[float, dict[str, list[str]]]:
    """Calculate archetype score based on multi-signal matching.

    Weight distribution:
    - Keyword matches: 40%
    - Tag matches: 40%
    - Problem/action signal matches: 20%

    Uses threshold-based scoring: hitting a minimum number of matches
    gives full weight for that signal type. This prevents dilution from
    having comprehensive keyword lists.

    Args:
        rules: Archetype rules dictionary with keywords, tags, signals
        text: Combined text from work unit
        tags: Tags from work unit

    Returns:
        Tuple of (score 0.0-1.0, matched signals dict)
    """
    score = 0.0
    matched_signals: dict[str, list[str]] = {}

    # Keyword matches (40% weight) - threshold of 2 for full score
    keywords = rules.get("keywords", [])
    if keywords:
        keyword_hits, keyword_matched = _count_matches(keywords, text)
        # Use threshold: 2+ matches = full score, 1 match = half score
        if keyword_hits >= 2:
            keyword_score = 0.4
        elif keyword_hits == 1:
            keyword_score = 0.2
        else:
            keyword_score = 0.0
        score += keyword_score
        if keyword_matched:
            matched_signals["keywords"] = keyword_matched

    # Tag matches (40% weight) - threshold of 1 for full score
    rule_tags = rules.get("tags", [])
    if rule_tags:
        tag_hits = 0
        tag_matched: list[str] = []
        for tag in tags:
            tag_lower = tag.lower()
            for rule_tag in rule_tags:
                if rule_tag.lower() == tag_lower:
                    tag_hits += 1
                    tag_matched.append(tag)
                    break
        # Direct tag match is strong signal: 1+ matches = full score
        tag_score = 0.4 if tag_hits >= 1 else 0.0
        score += tag_score
        if tag_matched:
            matched_signals["tags"] = tag_matched

    # Problem/action signal matches (20% weight) - threshold of 1 for full score
    problem_signals = rules.get("problem_signals", [])
    action_signals = rules.get("action_signals", [])
    all_signals = problem_signals + action_signals

    if all_signals:
        signal_hits, signal_matched = _count_matches(all_signals, text)
        # 2+ matches = full score, 1 match = half score
        if signal_hits >= 2:
            signal_score = 0.2
        elif signal_hits == 1:
            signal_score = 0.1
        else:
            signal_score = 0.0
        score += signal_score
        if signal_matched:
            matched_signals["signals"] = signal_matched

    return score, matched_signals


def infer_archetype(work_unit_data: dict[str, Any]) -> ArchetypeInference:
    """Infer archetype from work unit content.

    Uses rule-based classification with multi-signal fusion to determine
    the most likely archetype for a work unit. Returns the best matching
    archetype with confidence score.

    Args:
        work_unit_data: Dictionary containing work unit fields
            (title, problem, actions, outcome, tags)

    Returns:
        ArchetypeInference with archetype, confidence (0.0-1.0), and matched signals
    """
    text = _combine_text(work_unit_data)
    tags = work_unit_data.get("tags", [])
    if not isinstance(tags, list):
        tags = []

    scores: dict[str, tuple[float, dict[str, list[str]]]] = {}

    for archetype_name, rules in ARCHETYPE_RULES.items():
        if archetype_name == "minimal":
            continue  # Skip minimal in scoring, use as fallback

        score, matched = _calculate_score(rules, text, tags)
        scores[archetype_name] = (score, matched)

    # Select highest scoring archetype
    if not scores:
        return ArchetypeInference(
            archetype=WorkUnitArchetype.MINIMAL,
            confidence=0.1,
            matched_signals={},
        )

    best_name = max(scores.keys(), key=lambda k: scores[k][0])
    best_score, best_matched = scores[best_name]

    # Fall back to minimal if confidence is too low
    if best_score < CONFIDENCE_THRESHOLD:
        return ArchetypeInference(
            archetype=WorkUnitArchetype.MINIMAL,
            confidence=best_score if best_score > 0 else 0.1,
            matched_signals=best_matched if best_matched else {},
        )

    return ArchetypeInference(
        archetype=WorkUnitArchetype(best_name),
        confidence=best_score,
        matched_signals=best_matched,
    )


def get_all_archetype_scores(
    work_unit_data: dict[str, Any],
) -> list[tuple[WorkUnitArchetype, float]]:
    """Get scores for all archetypes (useful for debugging/display).

    Args:
        work_unit_data: Dictionary containing work unit fields

    Returns:
        List of (archetype, score) tuples sorted by score descending
    """
    text = _combine_text(work_unit_data)
    tags = work_unit_data.get("tags", [])
    if not isinstance(tags, list):
        tags = []

    results: list[tuple[WorkUnitArchetype, float]] = []

    for archetype_name, rules in ARCHETYPE_RULES.items():
        score, _ = _calculate_score(rules, text, tags)
        results.append((WorkUnitArchetype(archetype_name), score))

    # Sort by score descending
    return sorted(results, key=lambda x: -x[1])
