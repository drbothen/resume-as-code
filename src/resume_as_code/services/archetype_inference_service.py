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
        (r"first[-\s]+(?:ever|time|attempt)", 2.0),  # Handle hyphens
        # Compliance/certification achievements (greenfield for first-time)
        (r"achieved\s+(?:first|initial)", 2.5),
        (r"first\s+(?:submission|certification|authorization)", 2.5),
        (r"obtained\s+(?:ato|certification|authorization|accreditation)", 2.5),
        (r"initial\s+(?:ato|certification|authorization|approval)", 2.5),
        (r"created\s+(?:first|new|initial)", 2.0),
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
# Each description emphasizes UNIQUE aspects to maximize distinctiveness
ARCHETYPE_DESCRIPTIONS: dict[WorkUnitArchetype, str] = {
    WorkUnitArchetype.INCIDENT: (
        "Resolved critical production incident, security breach, or system outage. "
        "On-call response, triaged and mitigated P1/P2 issues, reduced MTTR. "
        "Emergency response, incident management, service restoration. "
        "Pager duty, war room, postmortem, root cause analysis, service degradation."
    ),
    WorkUnitArchetype.GREENFIELD: (
        "Built new system from scratch, designed and launched new product or platform. "
        "Pioneered new capability, architected greenfield solution. First-time implementation, "
        "stood up new service. Created something that didn't exist before. "
        "Achieved initial certification, first-attempt authorization, ATO approval, "
        "compliance accreditation. Established new program, inaugural launch, "
        "initial deployment, net-new development, zero-to-one initiative."
    ),
    WorkUnitArchetype.MIGRATION: (
        "Migrated legacy system to modern platform, cloud migration, database upgrade. "
        "Transitioned from on-premise to cloud, platform modernization. "
        "Replaced outdated technology, upgraded infrastructure, decommissioned legacy systems. "
        "Lift and shift, re-platforming, cutover, data migration, version upgrade."
    ),
    WorkUnitArchetype.OPTIMIZATION: (
        "Optimized performance, reduced latency and costs. Improved efficiency, "
        "profiled and tuned system, resource rightsizing. Achieved percentage improvements, "
        "cost savings, faster response times, better throughput. "
        "Performance tuning, query optimization, caching, load balancing, capacity planning."
    ),
    WorkUnitArchetype.LEADERSHIP: (
        "Led team, mentored engineers, coached direct reports. Aligned stakeholders, "
        "built and grew team, cross-functional leadership. Managed people, "
        "developed talent, drove organizational change through influence. "
        "Hiring, onboarding, performance reviews, 1:1s, career development, succession planning."
    ),
    WorkUnitArchetype.STRATEGIC: (
        "Developed strategy, market analysis, competitive positioning. Business "
        "development, partnerships, market expansion. Defined roadmap, "
        "created vision, established strategic direction. "
        "Go-to-market, business case, ROI analysis, stakeholder alignment, executive briefing."
    ),
    WorkUnitArchetype.TRANSFORMATION: (
        "Led digital transformation, enterprise-wide change initiative. "
        "Organizational transformation, company-wide rollout, modernization program. "
        "Board-level initiatives, global change management. "
        "Multi-year program, large-scale adoption, paradigm shift, cultural overhaul."
    ),
    WorkUnitArchetype.CULTURAL: (
        "Improved team culture, talent development, employee engagement. "
        "Reduced attrition, DEI initiatives, cultivated inclusive environment. "
        "Employee experience, retention programs, culture change. "
        "Morale, psychological safety, team health, belonging, work-life balance."
    ),
}

# Tag-to-archetype boost mapping
# Tags that strongly suggest certain archetypes get a score boost
TAG_ARCHETYPE_BOOST: dict[str, dict[WorkUnitArchetype, float]] = {
    # Incident-related tags
    "incident": {WorkUnitArchetype.INCIDENT: 0.3},
    "incident-response": {WorkUnitArchetype.INCIDENT: 0.3},
    "on-call": {WorkUnitArchetype.INCIDENT: 0.2},
    "outage": {WorkUnitArchetype.INCIDENT: 0.3},
    "security-incident": {WorkUnitArchetype.INCIDENT: 0.3},
    # Greenfield/compliance tags - boost greenfield, NOT incident
    "greenfield": {WorkUnitArchetype.GREENFIELD: 0.3},
    "new-system": {WorkUnitArchetype.GREENFIELD: 0.2},
    "compliance": {WorkUnitArchetype.GREENFIELD: 0.15},
    "rmf": {WorkUnitArchetype.GREENFIELD: 0.2},
    "ato": {WorkUnitArchetype.GREENFIELD: 0.25},
    "certification": {WorkUnitArchetype.GREENFIELD: 0.2},
    "fedramp": {WorkUnitArchetype.GREENFIELD: 0.2},
    "soc2": {WorkUnitArchetype.GREENFIELD: 0.2},
    "iso27001": {WorkUnitArchetype.GREENFIELD: 0.2},
    "pci-dss": {WorkUnitArchetype.GREENFIELD: 0.2},
    "hipaa": {WorkUnitArchetype.GREENFIELD: 0.15},
    # Migration tags
    "migration": {WorkUnitArchetype.MIGRATION: 0.3},
    "cloud-migration": {WorkUnitArchetype.MIGRATION: 0.3},
    "upgrade": {WorkUnitArchetype.MIGRATION: 0.2},
    "modernization": {WorkUnitArchetype.MIGRATION: 0.2},
    # Optimization tags
    "performance": {WorkUnitArchetype.OPTIMIZATION: 0.2},
    "optimization": {WorkUnitArchetype.OPTIMIZATION: 0.3},
    "cost-reduction": {WorkUnitArchetype.OPTIMIZATION: 0.25},
    "efficiency": {WorkUnitArchetype.OPTIMIZATION: 0.2},
    # Leadership tags
    "leadership": {WorkUnitArchetype.LEADERSHIP: 0.3},
    "mentorship": {WorkUnitArchetype.LEADERSHIP: 0.25},
    "team-building": {WorkUnitArchetype.LEADERSHIP: 0.25},
    "hiring": {WorkUnitArchetype.LEADERSHIP: 0.2},
    "management": {WorkUnitArchetype.LEADERSHIP: 0.2},
    # Strategic tags
    "strategy": {WorkUnitArchetype.STRATEGIC: 0.3},
    "roadmap": {WorkUnitArchetype.STRATEGIC: 0.2},
    "architecture": {WorkUnitArchetype.STRATEGIC: 0.15},
    # Transformation tags
    "transformation": {WorkUnitArchetype.TRANSFORMATION: 0.3},
    "digital-transformation": {WorkUnitArchetype.TRANSFORMATION: 0.3},
    "enterprise": {WorkUnitArchetype.TRANSFORMATION: 0.15},
    # Cultural tags
    "culture": {WorkUnitArchetype.CULTURAL: 0.3},
    "dei": {WorkUnitArchetype.CULTURAL: 0.3},
    "diversity": {WorkUnitArchetype.CULTURAL: 0.25},
    "engagement": {WorkUnitArchetype.CULTURAL: 0.2},
    "retention": {WorkUnitArchetype.CULTURAL: 0.2},
}

# Minimum confidence thresholds
MIN_CONFIDENCE_THRESHOLD = 0.5
SEMANTIC_CONFIDENCE_THRESHOLD = 0.3  # Lower for embeddings (similarity scores differ)

# Distinctiveness: minimum gap between best and second-best semantic scores
# If gap is smaller than this, the result is ambiguous and we return minimal
# Based on testing: real work units have 0.5-3% gaps, truly vague content has ~0% gap
MIN_DISTINCTIVENESS_GAP = 0.005  # 0.5% minimum gap required

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


def extract_tags(work_unit: WorkUnit | dict[str, Any]) -> list[str]:
    """Extract tags from work unit.

    Args:
        work_unit: WorkUnit object or raw dict from YAML.

    Returns:
        List of lowercase tag strings.
    """
    if isinstance(work_unit, WorkUnit):
        return [tag.lower() for tag in work_unit.tags]
    else:
        tags = work_unit.get("tags", [])
        if isinstance(tags, list):
            return [str(t).lower() for t in tags]
        return []


def compute_tag_boost(
    tags: list[str],
) -> dict[WorkUnitArchetype, float]:
    """Compute archetype score boosts based on tags.

    Args:
        tags: List of lowercase tags from work unit.

    Returns:
        Dict mapping archetypes to their cumulative boost (0.0 to 1.0).
    """
    boosts: dict[WorkUnitArchetype, float] = {
        archetype: 0.0 for archetype in WorkUnitArchetype if archetype != WorkUnitArchetype.MINIMAL
    }

    for tag in tags:
        if tag in TAG_ARCHETYPE_BOOST:
            for archetype, boost in TAG_ARCHETYPE_BOOST[tag].items():
                boosts[archetype] = min(boosts[archetype] + boost, 1.0)

    return boosts


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
    distinctiveness_gap: float = MIN_DISTINCTIVENESS_GAP,
) -> tuple[WorkUnitArchetype, float, InferenceMethod]:
    """Infer archetype using hybrid regex + semantic + tag approach.

    First attempts weighted regex matching (with tag boosts). If confidence
    is below threshold, falls back to semantic embedding comparison with
    tag boosts and distinctiveness check.

    Args:
        work_unit: WorkUnit object or raw dict from YAML.
        embedding_service: Service for semantic similarity.
        regex_threshold: Minimum regex confidence to skip semantic.
        semantic_threshold: Minimum semantic confidence to return non-minimal.
        distinctiveness_gap: Minimum gap between best and second-best scores.

    Returns:
        Tuple of (archetype, confidence, method) where method indicates
        which algorithm produced the result.
    """
    text = extract_text_content(work_unit)
    tags = extract_tags(work_unit)
    tag_boosts = compute_tag_boost(tags)

    # Phase 1: Try weighted regex + tag boost
    regex_scores: dict[WorkUnitArchetype, float] = {}
    for archetype in WorkUnitArchetype:
        if archetype == WorkUnitArchetype.MINIMAL:
            continue
        base_score = score_weighted_regex(text, archetype)
        # Add tag boost (weighted at 50% to not overwhelm regex)
        boosted_score = min(base_score + tag_boosts[archetype] * 0.5, 1.0)
        regex_scores[archetype] = boosted_score

    best_regex = max(regex_scores, key=lambda k: regex_scores[k])
    best_regex_score = regex_scores[best_regex]

    if best_regex_score >= regex_threshold:
        return (best_regex, best_regex_score, "regex")

    # Phase 2: Fall back to semantic matching + tag boost with distinctiveness check
    semantic_scores: dict[WorkUnitArchetype, float] = {}
    for archetype in WorkUnitArchetype:
        if archetype == WorkUnitArchetype.MINIMAL:
            continue
        base_score = score_semantic(text, archetype, embedding_service)
        # Add tag boost (weighted at 30% for semantic to preserve similarity ranking)
        boosted_score = min(base_score + tag_boosts[archetype] * 0.3, 1.0)
        semantic_scores[archetype] = boosted_score

    # Sort scores to get best and second-best
    sorted_scores = sorted(semantic_scores.items(), key=lambda x: x[1], reverse=True)
    best_archetype, best_score = sorted_scores[0]
    _second_archetype, second_score = sorted_scores[1]

    # Calculate gap between best and second-best
    gap = best_score - second_score

    # Check distinctiveness: if gap is too small, result is ambiguous
    if gap < distinctiveness_gap:
        # Ambiguous result - return minimal with low confidence
        # Confidence reflects how ambiguous: smaller gap = lower confidence
        ambiguous_confidence = gap / distinctiveness_gap * 0.5  # Scale to 0-0.5
        return (WorkUnitArchetype.MINIMAL, ambiguous_confidence, "fallback")

    # Distinctive result - check absolute threshold
    if best_score >= semantic_threshold:
        # Confidence combines absolute score and distinctiveness
        # Normalize: use gap as confidence indicator (capped at 1.0)
        # A 1.5% gap gives ~0.5 confidence, 3% gap gives ~1.0
        distinctiveness_confidence = min(gap / 0.03, 1.0)
        return (best_archetype, distinctiveness_confidence, "semantic")

    # Neither method confident enough
    return (WorkUnitArchetype.MINIMAL, max(best_regex_score, best_score), "fallback")


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
