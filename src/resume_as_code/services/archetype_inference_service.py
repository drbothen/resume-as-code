"""Archetype inference service for classifying work units.

Story 12.3: Archetype Inference Service

Provides CLI-friendly inference with regex-based pattern matching.
Uses higher confidence threshold (0.5) for more conservative suggestions.
Returns simple tuple for easy CLI integration.

For migration purposes, see archetype_inference.py (Story 12.1) which
uses multi-signal fusion with 0.3 threshold.
"""

from __future__ import annotations

import re
from typing import Any

from resume_as_code.models.work_unit import WorkUnit, WorkUnitArchetype

# Keyword patterns for each archetype (case-insensitive regex)
ARCHETYPE_PATTERNS: dict[WorkUnitArchetype, list[str]] = {
    WorkUnitArchetype.INCIDENT: [
        r"\bp[12]\b",
        r"outage",
        r"incident",
        r"breach",
        r"detected",
        r"triaged",
        r"mitigated",
        r"resolved.*production",
        r"mttr",
        r"security\s+event",
        r"escalation",
        r"on-?call",
    ],
    WorkUnitArchetype.GREENFIELD: [
        r"built\s+(?:new|a)",
        r"designed\s+(?:and\s+)?(?:built|implemented)",
        r"architected",
        r"launched",
        r"from\s+scratch",
        r"pioneered",
        r"new\s+(?:system|feature|product|platform)",
        r"ground-?up",
    ],
    WorkUnitArchetype.MIGRATION: [
        r"migrat(?:ed|ion)",
        r"upgraded",
        r"transitioned",
        r"legacy\s+(?:replacement|system)",
        r"cloud\s+migration",
        r"database\s+migration",
        r"platform\s+(?:upgrade|migration)",
    ],
    WorkUnitArchetype.OPTIMIZATION: [
        r"optimiz(?:ed|ation)",
        r"reduced\s+(?:latency|cost|time)",
        r"improv(?:ed|ing)\s+performance",
        r"profiled",
        r"cost\s+(?:reduction|savings)",
        r"latency\s+reduction",
        r"resource\s+(?:optimization|rightsizing)",
    ],
    WorkUnitArchetype.LEADERSHIP: [
        r"mentor(?:ed|ing)",
        r"coach(?:ed|ing)",
        r"aligned\s+stakeholders",
        r"championed",
        r"unified\s+teams",
        r"cross-?team",
        r"organizational\s+(?:change|impact)",
        r"built\s+(?:the\s+)?team",
    ],
    WorkUnitArchetype.STRATEGIC: [
        r"strateg(?:y|ic)",
        r"market\s+(?:analysis|positioning)",
        r"competitive",
        r"positioned",
        r"partnership",
        r"market\s+share",
        r"business\s+development",
    ],
    WorkUnitArchetype.TRANSFORMATION: [
        r"transformation",
        r"digital\s+transformation",
        r"enterprise-?wide",
        r"board-?level",
        r"organizational\s+change",
        r"company-?wide",
        r"global\s+(?:initiative|rollout)",
    ],
    WorkUnitArchetype.CULTURAL: [
        r"culture",
        r"talent\s+development",
        r"engagement",
        r"attrition",
        r"retention",
        r"cultivated",
        r"dei|diversity",
        r"employee\s+experience",
    ],
}

# Minimum confidence to suggest non-minimal archetype
MIN_CONFIDENCE_THRESHOLD = 0.5


def extract_text_content(work_unit: WorkUnit | dict[str, Any]) -> str:
    """Extract all text content from work unit for analysis.

    Combines title, problem statement, actions, outcome, and tags
    into a single lowercase string for pattern matching.

    Args:
        work_unit: WorkUnit object or raw dict from YAML.

    Returns:
        Combined lowercase text from all fields.
    """
    if isinstance(work_unit, WorkUnit):
        parts = [
            work_unit.title,
            work_unit.problem.statement,
            " ".join(work_unit.actions),
            work_unit.outcome.result,
            " ".join(work_unit.tags),
        ]
        if work_unit.outcome.quantified_impact:
            parts.append(work_unit.outcome.quantified_impact)
        if work_unit.outcome.business_value:
            parts.append(work_unit.outcome.business_value)
    else:
        # Handle dict (raw YAML)
        parts = [
            str(work_unit.get("title", "")),
        ]

        # Extract problem statement
        problem = work_unit.get("problem", {})
        if isinstance(problem, dict):
            parts.append(str(problem.get("statement", "")))
        elif isinstance(problem, str):
            parts.append(problem)

        # Extract actions
        actions = work_unit.get("actions", [])
        if isinstance(actions, list):
            parts.append(" ".join(str(a) for a in actions))

        # Extract outcome fields
        outcome = work_unit.get("outcome", {})
        if isinstance(outcome, dict):
            parts.append(str(outcome.get("result", "")))
            if qi := outcome.get("quantified_impact"):
                parts.append(str(qi))
            if bv := outcome.get("business_value"):
                parts.append(str(bv))
        elif isinstance(outcome, str):
            parts.append(outcome)

        # Extract tags
        tags = work_unit.get("tags", [])
        if isinstance(tags, list):
            parts.append(" ".join(str(t) for t in tags))

    return " ".join(parts).lower()


def score_archetype(text: str, archetype: WorkUnitArchetype) -> float:
    """Score how well text matches an archetype's patterns.

    Uses regex pattern matching for more precise detection than
    simple substring matching.

    Args:
        text: Lowercase text to search.
        archetype: Archetype to score against.

    Returns:
        Score from 0.0 to 1.0 based on pattern match ratio.
    """
    patterns = ARCHETYPE_PATTERNS.get(archetype, [])
    if not patterns:
        return 0.0

    # Note: text is already lowercased by extract_text_content()
    matches = sum(1 for p in patterns if re.search(p, text))
    return matches / len(patterns)


def infer_archetype(
    work_unit: WorkUnit | dict[str, Any],
    threshold: float = MIN_CONFIDENCE_THRESHOLD,
) -> tuple[WorkUnitArchetype, float]:
    """Infer archetype from work unit content.

    Uses regex-based pattern matching to classify work units into
    archetypes. Returns MINIMAL when confidence is below threshold.

    Args:
        work_unit: WorkUnit object or raw dict from YAML.
        threshold: Minimum confidence to return non-minimal archetype.
            Defaults to MIN_CONFIDENCE_THRESHOLD (0.5).

    Returns:
        Tuple of (archetype, confidence) where confidence is 0.0-1.0.
    """
    text = extract_text_content(work_unit)

    scores: dict[WorkUnitArchetype, float] = {}
    for archetype in WorkUnitArchetype:
        if archetype == WorkUnitArchetype.MINIMAL:
            continue  # Don't score minimal - it's the fallback
        scores[archetype] = score_archetype(text, archetype)

    if not scores:
        return (WorkUnitArchetype.MINIMAL, 0.0)

    best_archetype = max(scores, key=lambda k: scores[k])
    best_score = scores[best_archetype]

    if best_score < threshold:
        return (WorkUnitArchetype.MINIMAL, best_score)

    return (best_archetype, best_score)
