"""Archetype-aware PAR structure validation service."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from resume_as_code.models.work_unit import WorkUnit, WorkUnitArchetype

# Validation thresholds
ALIGNMENT_THRESHOLD = 0.3  # Minimum score for PAR section to be considered aligned
MIN_MATCHES_FOR_FULL_SCORE = 3  # Minimum pattern matches required for 1.0 score


@dataclass
class ArchetypeValidationResult:
    """Result of archetype alignment validation."""

    archetype: WorkUnitArchetype
    is_aligned: bool
    problem_score: float  # 0.0-1.0
    action_score: float  # 0.0-1.0
    outcome_score: float  # 0.0-1.0
    warnings: list[str]
    suggestions: list[str]


# Validation patterns for each archetype
ARCHETYPE_PAR_PATTERNS: dict[WorkUnitArchetype, dict[str, list[str]]] = {
    WorkUnitArchetype.INCIDENT: {
        "problem_patterns": [
            r"outage",
            r"incident",
            r"failure",
            r"breach",
            r"alert",
            r"degraded",
            r"affecting",
            r"impact",
            r"down",
            r"critical",
        ],
        "action_patterns": [
            r"detect",
            r"triage",
            r"mitigat",
            r"resolv",
            r"respond",
            r"diagnos",
            r"communic",
            r"escalat",
            r"contain",
            r"restor",
        ],
        "outcome_patterns": [
            r"mttr",
            r"restor",
            r"prevent",
            r"reduc.*time",
            r"minutes",
            r"hours",
            r"avoided",
            r"resolved in",
        ],
    },
    WorkUnitArchetype.GREENFIELD: {
        "problem_patterns": [
            r"need",
            r"gap",
            r"opportunit",
            r"no existing",
            r"lack",
            r"require",
            r"demand",
            r"missing",
            r"enable",
        ],
        "action_patterns": [
            r"design",
            r"built",
            r"architect",
            r"launch",
            r"deploy",
            r"implement",
            r"engineer",
            r"pioneer",
            r"create",
            r"develop",
        ],
        "outcome_patterns": [
            r"deliver",
            r"launch",
            r"enabl",
            r"creat",
            r"achiev",
            r"support",
            r"serving",
            r"processing",
            r"scale",
        ],
    },
    WorkUnitArchetype.MIGRATION: {
        "problem_patterns": [
            r"legacy",
            r"outdat",
            r"end of life",
            r"unsupport",
            r"technical debt",
            r"old",
            r"deprecat",
            r"compatibility",
        ],
        "action_patterns": [
            r"migrat",
            r"transition",
            r"upgrad",
            r"convert",
            r"port",
            r"refactor",
            r"plan",
            r"cutover",
            r"parallel",
        ],
        "outcome_patterns": [
            r"complet",
            r"success",
            r"zero downtime",
            r"no data loss",
            r"modern",
            r"reduc.*cost",
            r"improv",
            r"decommission",
        ],
    },
    WorkUnitArchetype.OPTIMIZATION: {
        "problem_patterns": [
            r"slow",
            r"expensive",
            r"inefficient",
            r"bottleneck",
            r"latency",
            r"cost",
            r"resource",
            r"baseline",
        ],
        "action_patterns": [
            r"optimiz",
            r"profil",
            r"analyz",
            r"identif",
            r"implement",
            r"cache",
            r"refactor",
            r"streamlin",
            r"tune",
            r"rightsize",
        ],
        "outcome_patterns": [
            r"\d+%",
            r"reduc",
            r"improv",
            r"faster",
            r"cheaper",
            r"cost sav",
            r"latency",
            r"throughput",
            r"efficiency",
        ],
    },
    WorkUnitArchetype.LEADERSHIP: {
        "problem_patterns": [
            r"team",
            r"capability",
            r"talent",
            r"skill gap",
            r"growth",
            r"retention",
            r"hiring",
            r"alignment",
        ],
        "action_patterns": [
            r"mentor",
            r"coach",
            r"align",
            r"champion",
            r"built.*team",
            r"hired",
            r"develop",
            r"lead",
            r"unified",
            r"cultivat",
        ],
        "outcome_patterns": [
            r"promot",
            r"retent",
            r"grew",
            r"hired",
            r"engag",
            r"team",
            r"capability",
            r"culture",
            r"develop",
        ],
    },
    WorkUnitArchetype.STRATEGIC: {
        "problem_patterns": [
            r"market",
            r"competit",
            r"position",
            r"direction",
            r"strateg",
            r"opportunit",
            r"partner",
            r"growth",
        ],
        "action_patterns": [
            r"research",
            r"analyz",
            r"position",
            r"develop.*strateg",
            r"establish",
            r"partner",
            r"align",
            r"define",
            r"framework",
        ],
        "outcome_patterns": [
            r"market share",
            r"competit",
            r"position",
            r"partner",
            r"revenue",
            r"growth",
            r"advantage",
            r"influence",
        ],
    },
    WorkUnitArchetype.TRANSFORMATION: {
        "problem_patterns": [
            r"enterprise",
            r"organization",
            r"company-wide",
            r"scale",
            r"transform",
            r"digital",
            r"legacy",
            r"moderniz",
        ],
        "action_patterns": [
            r"transform",
            r"lead",
            r"execut",
            r"change manag",
            r"vision",
            r"align",
            r"rollout",
            r"global",
            r"enterprise",
        ],
        "outcome_patterns": [
            r"transform",
            r"enterprise",
            r"company-wide",
            r"scale",
            r"million",
            r"organization",
            r"global",
            r"adopted",
        ],
    },
    WorkUnitArchetype.CULTURAL: {
        "problem_patterns": [
            r"culture",
            r"engagement",
            r"retention",
            r"attrition",
            r"morale",
            r"satisfaction",
            r"diversity",
            r"inclusion",
        ],
        "action_patterns": [
            r"cultivat",
            r"program",
            r"initiative",
            r"champion",
            r"foster",
            r"measur",
            r"survey",
            r"implement",
        ],
        "outcome_patterns": [
            r"engagement",
            r"retention",
            r"nps",
            r"satisfaction",
            r"attrition",
            r"score",
            r"improv",
            r"culture",
        ],
    },
}


def extract_par_text(work_unit: WorkUnit | dict[str, Any]) -> tuple[str, str, str]:
    """Extract Problem, Actions, Result text from work unit.

    Combines relevant fields from each PAR section into searchable text strings.

    Args:
        work_unit: Either a WorkUnit model instance or raw dictionary from YAML.

    Returns:
        Tuple of (problem_text, action_text, outcome_text) all lowercased.
        Returns empty strings for missing sections.
    """
    if isinstance(work_unit, WorkUnit):
        problem_text = work_unit.problem.statement
        if work_unit.problem.context:
            problem_text += " " + work_unit.problem.context
        action_text = " ".join(work_unit.actions)
        outcome_text = work_unit.outcome.result
        if work_unit.outcome.quantified_impact:
            outcome_text += " " + work_unit.outcome.quantified_impact
        if work_unit.outcome.business_value:
            outcome_text += " " + work_unit.outcome.business_value
    else:
        problem = work_unit.get("problem") or {}
        problem_text = str(problem.get("statement") or "")
        if problem.get("context"):
            problem_text += " " + str(problem.get("context") or "")
        actions = work_unit.get("actions") or []
        action_text = " ".join(str(a) for a in actions if a)
        outcome = work_unit.get("outcome") or {}
        outcome_text = str(outcome.get("result") or "")
        if outcome.get("quantified_impact"):
            outcome_text += " " + str(outcome.get("quantified_impact") or "")
        if outcome.get("business_value"):
            outcome_text += " " + str(outcome.get("business_value") or "")

    return problem_text.lower(), action_text.lower(), outcome_text.lower()


def score_par_section(text: str, patterns: list[str]) -> float:
    """Score how well text matches expected patterns (0.0-1.0).

    Args:
        text: The text content to search for pattern matches.
        patterns: List of regex patterns to match against.

    Returns:
        Score from 0.0 to 1.0 based on pattern match density.
    """
    if not patterns or not text:
        return 0.0

    matches = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(1.0, matches / max(MIN_MATCHES_FOR_FULL_SCORE, len(patterns) // 2))


def validate_archetype_alignment(
    work_unit: WorkUnit | dict[str, Any],
    archetype: WorkUnitArchetype | None = None,
) -> ArchetypeValidationResult:
    """Validate work unit PAR structure against archetype expectations.

    Args:
        work_unit: WorkUnit object or raw dict from YAML.
        archetype: Override archetype (uses work_unit.archetype if not provided).

    Returns:
        ArchetypeValidationResult with scores and suggestions.
    """
    if archetype is None:
        if isinstance(work_unit, WorkUnit):
            archetype = work_unit.archetype
        else:
            arch_str = work_unit.get("archetype", "minimal")
            archetype = WorkUnitArchetype(arch_str)

    # Minimal archetype has no specific validation
    if archetype == WorkUnitArchetype.MINIMAL:
        return ArchetypeValidationResult(
            archetype=archetype,
            is_aligned=True,
            problem_score=1.0,
            action_score=1.0,
            outcome_score=1.0,
            warnings=[],
            suggestions=[
                "Consider classifying with a specific archetype for better resume targeting"
            ],
        )

    patterns = ARCHETYPE_PAR_PATTERNS.get(archetype, {})
    problem_text, action_text, outcome_text = extract_par_text(work_unit)

    # Score each PAR section
    problem_score = score_par_section(problem_text, patterns.get("problem_patterns", []))
    action_score = score_par_section(action_text, patterns.get("action_patterns", []))
    outcome_score = score_par_section(outcome_text, patterns.get("outcome_patterns", []))

    warnings: list[str] = []
    suggestions: list[str] = []

    # Generate warnings for low scores
    if problem_score < ALIGNMENT_THRESHOLD:
        warnings.append(
            f"Problem section may not align with {archetype.value} archetype "
            f"(score: {problem_score:.0%})"
        )
        suggestions.append(
            f"For {archetype.value}, problem should describe: {_get_problem_guidance(archetype)}"
        )

    if action_score < ALIGNMENT_THRESHOLD:
        warnings.append(
            f"Actions may not align with {archetype.value} archetype (score: {action_score:.0%})"
        )
        suggestions.append(
            f"For {archetype.value}, actions should include: {_get_action_guidance(archetype)}"
        )

    if outcome_score < ALIGNMENT_THRESHOLD:
        warnings.append(
            f"Outcome may not align with {archetype.value} archetype (score: {outcome_score:.0%})"
        )
        suggestions.append(
            f"For {archetype.value}, outcome should demonstrate: {_get_outcome_guidance(archetype)}"
        )

    # Overall alignment check
    avg_score = (problem_score + action_score + outcome_score) / 3
    is_aligned = avg_score >= ALIGNMENT_THRESHOLD

    if not is_aligned:
        suggestions.append(
            f"Consider if '{archetype.value}' is the best archetype for this work unit. "
            f"Run 'resume infer-archetypes' to see suggestions."
        )

    return ArchetypeValidationResult(
        archetype=archetype,
        is_aligned=is_aligned,
        problem_score=problem_score,
        action_score=action_score,
        outcome_score=outcome_score,
        warnings=warnings,
        suggestions=suggestions,
    )


def _get_problem_guidance(archetype: WorkUnitArchetype) -> str:
    """Get human-readable guidance for problem section."""
    guidance = {
        WorkUnitArchetype.INCIDENT: "the incident/outage, impact scope, and severity",
        WorkUnitArchetype.GREENFIELD: "the need, gap, or opportunity that drove the project",
        WorkUnitArchetype.MIGRATION: "legacy system limitations and modernization drivers",
        WorkUnitArchetype.OPTIMIZATION: "performance baseline, costs, or inefficiencies",
        WorkUnitArchetype.LEADERSHIP: "team/capability gaps or growth opportunities",
        WorkUnitArchetype.STRATEGIC: "market position, competitive challenges, or strategic needs",
        WorkUnitArchetype.TRANSFORMATION: "enterprise-wide challenges requiring transformation",
        WorkUnitArchetype.CULTURAL: "culture, engagement, or retention challenges",
    }
    return guidance.get(archetype, "the challenge or problem")


def _get_action_guidance(archetype: WorkUnitArchetype) -> str:
    """Get human-readable guidance for action section."""
    guidance = {
        WorkUnitArchetype.INCIDENT: "detect, triage, mitigate, resolve, communicate",
        WorkUnitArchetype.GREENFIELD: "design, build, architect, launch, deploy",
        WorkUnitArchetype.MIGRATION: "plan, migrate, transition, validate, cutover",
        WorkUnitArchetype.OPTIMIZATION: "profile, analyze, optimize, implement improvements",
        WorkUnitArchetype.LEADERSHIP: "mentor, coach, align, champion, build team",
        WorkUnitArchetype.STRATEGIC: "research, analyze, position, establish partnerships",
        WorkUnitArchetype.TRANSFORMATION: "lead transformation, execute change, align organization",
        WorkUnitArchetype.CULTURAL: "cultivate, program, measure, foster change",
    }
    return guidance.get(archetype, "relevant actions")


def _get_outcome_guidance(archetype: WorkUnitArchetype) -> str:
    """Get human-readable guidance for outcome section."""
    guidance = {
        WorkUnitArchetype.INCIDENT: "MTTR, restored service, prevented impact",
        WorkUnitArchetype.GREENFIELD: "delivered capability, launched product, enabled users",
        WorkUnitArchetype.MIGRATION: "successful transition, zero downtime, decommissioned legacy",
        WorkUnitArchetype.OPTIMIZATION: "% improvement, cost savings, latency reduction",
        WorkUnitArchetype.LEADERSHIP: "team growth, promotions, retention, capability building",
        WorkUnitArchetype.STRATEGIC: "market share, competitive position, partnerships",
        WorkUnitArchetype.TRANSFORMATION: "enterprise-wide adoption, organizational change",
        WorkUnitArchetype.CULTURAL: "engagement scores, retention rates, culture metrics",
    }
    return guidance.get(archetype, "measurable results")
