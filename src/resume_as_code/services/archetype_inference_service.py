"""Archetype inference service with hybrid regex + semantic matching.

Story 12.6: Enhanced Archetype Inference with Semantic Embeddings

Provides CLI-friendly inference using a hybrid approach:
1. Weighted regex patterns (strong signals score higher)
2. Semantic embeddings for conceptual similarity
3. Fallback to minimal when confidence is low
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Literal

from resume_as_code.models.work_unit import WorkUnit, WorkUnitArchetype

if TYPE_CHECKING:
    from resume_as_code.services.embedder import EmbeddingService

# Weighted patterns: (pattern, weight)
# Higher weight = stronger signal for archetype
ARCHETYPE_PATTERNS_WEIGHTED: dict[WorkUnitArchetype, list[tuple[str, float]]] = {
    WorkUnitArchetype.INCIDENT: [
        (r"\bp1\b", 3.0),  # Very strong signal
        (r"\bp2\b", 2.5),
        (r"outage", 2.5),
        (r"incident", 2.0),
        (r"breach", 2.5),
        (r"triaged", 2.0),
        (r"mitigated", 2.0),
        (r"resolved.*production", 2.0),
        (r"mttr", 2.0),
        (r"security\s+event", 2.0),
        (r"escalation", 1.5),
        (r"on-?call", 1.5),
        (r"detected", 1.0),  # Weaker signal
    ],
    WorkUnitArchetype.GREENFIELD: [
        (r"from\s+scratch", 3.0),
        (r"built\s+new", 2.5),
        (r"designed\s+(?:and\s+)?(?:built|implemented)", 2.5),
        (r"architected", 2.0),
        (r"launched", 2.0),
        (r"pioneered", 2.5),
        (r"new\s+(?:system|feature|product|platform)", 2.0),
        (r"ground-?up", 2.5),
        (r"stood\s+up", 2.0),
        (r"established\s+(?:new|first)", 2.0),
        (r"first\s+(?:ever|time|attempt)", 2.0),
    ],
    WorkUnitArchetype.MIGRATION: [
        (r"migrat(?:ed|ion)", 3.0),
        (r"cloud\s+migration", 3.0),
        (r"upgraded", 2.0),
        (r"transitioned", 2.0),
        (r"legacy\s+(?:replacement|system)", 2.5),
        (r"database\s+migration", 2.5),
        (r"platform\s+(?:upgrade|migration)", 2.5),
        (r"cutover", 2.0),
        (r"decommission", 1.5),
    ],
    WorkUnitArchetype.OPTIMIZATION: [
        (r"optimiz(?:ed|ation)", 3.0),
        (r"reduced\s+(?:latency|cost|time)", 2.5),
        (r"\d+%\s+(?:reduction|improvement|faster)", 3.0),
        (r"improv(?:ed|ing)\s+performance", 2.5),
        (r"profiled", 2.0),
        (r"cost\s+(?:reduction|savings)", 2.5),
        (r"latency\s+reduction", 2.5),
        (r"resource\s+(?:optimization|rightsizing)", 2.0),
        (r"bottleneck", 1.5),
    ],
    WorkUnitArchetype.LEADERSHIP: [
        (r"led\s+(?:team|effort|program)", 3.0),
        (r"mentor(?:ed|ing)", 2.5),
        (r"coach(?:ed|ing)", 2.5),
        (r"managed\s+(?:\d+|team)", 2.5),
        (r"aligned\s+stakeholders", 2.0),
        (r"championed", 2.0),
        (r"unified\s+teams", 2.0),
        (r"cross-?(?:team|functional)", 2.0),
        (r"organizational\s+(?:change|impact)", 2.0),
        (r"built\s+(?:the\s+)?team", 2.5),
        (r"hired", 1.5),
        (r"directed", 2.0),
    ],
    WorkUnitArchetype.STRATEGIC: [
        (r"strateg(?:y|ic)", 3.0),
        (r"market\s+(?:analysis|positioning)", 2.5),
        (r"competitive\s+(?:analysis|advantage)", 2.5),
        (r"positioned", 2.0),
        (r"partnership", 2.0),
        (r"market\s+share", 2.5),
        (r"business\s+development", 2.5),
        (r"roadmap", 2.0),
        (r"vision", 1.5),
    ],
    WorkUnitArchetype.TRANSFORMATION: [
        (r"transformation", 3.0),
        (r"digital\s+transformation", 3.0),
        (r"enterprise-?wide", 2.5),
        (r"board-?level", 2.5),
        (r"organizational\s+change", 2.5),
        (r"company-?wide", 2.5),
        (r"global\s+(?:initiative|rollout)", 2.5),
        (r"moderniz(?:ed|ation)", 2.0),
    ],
    WorkUnitArchetype.CULTURAL: [
        (r"culture", 3.0),
        (r"talent\s+development", 2.5),
        (r"engagement", 2.0),
        (r"attrition", 2.0),
        (r"retention", 2.0),
        (r"cultivated", 2.0),
        (r"dei|diversity", 2.5),
        (r"employee\s+experience", 2.5),
        (r"inclusion", 2.0),
    ],
}

# Rich semantic descriptions for embedding comparison
ARCHETYPE_DESCRIPTIONS: dict[WorkUnitArchetype, str] = {
    WorkUnitArchetype.INCIDENT: (
        "Resolved critical production incident, security breach, or system outage. "
        "On-call response, triaged and mitigated P1/P2 issues, reduced MTTR. "
        "Emergency response, incident management, service restoration."
    ),
    WorkUnitArchetype.GREENFIELD: (
        "Built new system from scratch, designed and launched new product or platform. "
        "Pioneered new capability, architected greenfield solution. First-time implementation, "
        "stood up new service, achieved initial certification or authorization. "
        "Created something that didn't exist before."
    ),
    WorkUnitArchetype.MIGRATION: (
        "Migrated legacy system to modern platform, cloud migration, database upgrade. "
        "Transitioned from on-premise to cloud, platform modernization. "
        "Replaced outdated technology, upgraded infrastructure, decommissioned legacy systems."
    ),
    WorkUnitArchetype.OPTIMIZATION: (
        "Optimized performance, reduced latency and costs. Improved efficiency, "
        "profiled and tuned system, resource rightsizing. Achieved percentage improvements, "
        "cost savings, faster response times, better throughput."
    ),
    WorkUnitArchetype.LEADERSHIP: (
        "Led team, mentored engineers, coached direct reports. Aligned stakeholders, "
        "built and grew team, cross-functional leadership. Managed people, "
        "developed talent, drove organizational change through influence."
    ),
    WorkUnitArchetype.STRATEGIC: (
        "Developed strategy, market analysis, competitive positioning. Business "
        "development, partnerships, market expansion. Defined roadmap, "
        "created vision, established strategic direction."
    ),
    WorkUnitArchetype.TRANSFORMATION: (
        "Led digital transformation, enterprise-wide change initiative. "
        "Organizational transformation, company-wide rollout, modernization program. "
        "Board-level initiatives, global change management."
    ),
    WorkUnitArchetype.CULTURAL: (
        "Improved team culture, talent development, employee engagement. "
        "Reduced attrition, DEI initiatives, cultivated inclusive environment. "
        "Employee experience, retention programs, culture change."
    ),
}

# Minimum confidence thresholds
MIN_CONFIDENCE_THRESHOLD = 0.5
SEMANTIC_CONFIDENCE_THRESHOLD = 0.3  # Lower for embeddings (similarity scores differ)

InferenceMethod = Literal["regex", "semantic", "fallback"]


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


def score_weighted_regex(text: str, archetype: WorkUnitArchetype) -> float:
    """Score text against weighted regex patterns.

    Args:
        text: Lowercase text to search.
        archetype: Archetype to score against.

    Returns:
        Score from 0.0 to 1.0 based on weighted pattern match ratio.
    """
    patterns = ARCHETYPE_PATTERNS_WEIGHTED.get(archetype, [])
    if not patterns:
        return 0.0

    total_weight = sum(weight for _, weight in patterns)
    matched_weight = sum(
        weight for pattern, weight in patterns if re.search(pattern, text, re.IGNORECASE)
    )
    return matched_weight / total_weight


def score_semantic(
    text: str,
    archetype: WorkUnitArchetype,
    embedding_service: EmbeddingService,
) -> float:
    """Score text against archetype using semantic similarity.

    Args:
        text: Text to compare.
        archetype: Archetype to score against.
        embedding_service: Service for computing embeddings.

    Returns:
        Cosine similarity score from 0.0 to 1.0.
    """
    description = ARCHETYPE_DESCRIPTIONS.get(archetype, "")
    if not description:
        return 0.0

    return embedding_service.similarity(text, description)


def infer_archetype_hybrid(
    work_unit: WorkUnit | dict[str, Any],
    embedding_service: EmbeddingService,
    regex_threshold: float = MIN_CONFIDENCE_THRESHOLD,
    semantic_threshold: float = SEMANTIC_CONFIDENCE_THRESHOLD,
) -> tuple[WorkUnitArchetype, float, InferenceMethod]:
    """Infer archetype using hybrid regex + semantic approach.

    First attempts weighted regex matching. If confidence is below threshold,
    falls back to semantic embedding comparison.

    Args:
        work_unit: WorkUnit object or raw dict from YAML.
        embedding_service: Service for semantic similarity.
        regex_threshold: Minimum regex confidence to skip semantic.
        semantic_threshold: Minimum semantic confidence to return non-minimal.

    Returns:
        Tuple of (archetype, confidence, method) where method indicates
        which algorithm produced the result.
    """
    text = extract_text_content(work_unit)

    # Phase 1: Try weighted regex
    regex_scores: dict[WorkUnitArchetype, float] = {}
    for archetype in WorkUnitArchetype:
        if archetype == WorkUnitArchetype.MINIMAL:
            continue
        regex_scores[archetype] = score_weighted_regex(text, archetype)

    best_regex = max(regex_scores, key=lambda k: regex_scores[k])
    best_regex_score = regex_scores[best_regex]

    if best_regex_score >= regex_threshold:
        return (best_regex, best_regex_score, "regex")

    # Phase 2: Fall back to semantic matching
    semantic_scores: dict[WorkUnitArchetype, float] = {}
    for archetype in WorkUnitArchetype:
        if archetype == WorkUnitArchetype.MINIMAL:
            continue
        semantic_scores[archetype] = score_semantic(text, archetype, embedding_service)

    best_semantic = max(semantic_scores, key=lambda k: semantic_scores[k])
    best_semantic_score = semantic_scores[best_semantic]

    if best_semantic_score >= semantic_threshold:
        return (best_semantic, best_semantic_score, "semantic")

    # Neither method confident enough
    return (WorkUnitArchetype.MINIMAL, max(best_regex_score, best_semantic_score), "fallback")


def infer_archetype(
    work_unit: WorkUnit | dict[str, Any],
    embedding_service: EmbeddingService,
    threshold: float = MIN_CONFIDENCE_THRESHOLD,
) -> tuple[WorkUnitArchetype, float, InferenceMethod]:
    """Infer archetype using hybrid weighted-regex + semantic approach.

    Args:
        work_unit: WorkUnit object or raw dict from YAML.
        embedding_service: Service for semantic similarity.
        threshold: Minimum confidence for non-minimal result.

    Returns:
        Tuple of (archetype, confidence, method).
    """
    return infer_archetype_hybrid(
        work_unit,
        embedding_service,
        regex_threshold=threshold,
        semantic_threshold=SEMANTIC_CONFIDENCE_THRESHOLD,
    )
