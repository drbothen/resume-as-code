"""Work Unit text extraction utilities."""

from __future__ import annotations

from typing import Any


def extract_work_unit_text(wu: dict[str, Any]) -> str:
    """Extract all searchable text from a Work Unit.

    Consolidates text from title, problem, actions, outcome, tags,
    and skills_demonstrated fields into a single searchable string.

    Args:
        wu: Work Unit dictionary.

    Returns:
        Space-separated string of all text content.
    """
    parts: list[str] = []

    # Title
    if title := wu.get("title"):
        parts.append(str(title))

    # Problem (handles both dict and string formats)
    if problem := wu.get("problem"):
        if isinstance(problem, dict):
            if stmt := problem.get("statement"):
                parts.append(str(stmt))
            if context := problem.get("context"):
                parts.append(str(context))
        elif isinstance(problem, str):
            parts.append(problem)

    # Actions (handles both list and string formats)
    if actions := wu.get("actions"):
        if isinstance(actions, list):
            parts.extend(str(a) for a in actions)
        elif isinstance(actions, str):
            parts.append(actions)

    # Outcome (handles both dict and string formats)
    if outcome := wu.get("outcome"):
        if isinstance(outcome, dict):
            if result := outcome.get("result"):
                parts.append(str(result))
            if impact := outcome.get("quantified_impact"):
                parts.append(str(impact))
        elif isinstance(outcome, str):
            parts.append(outcome)

    # Tags (also searchable as text)
    if tags := wu.get("tags"):
        parts.extend(str(t) for t in tags)

    # Skills demonstrated (handles both string and dict formats)
    for skill_item in wu.get("skills_demonstrated", []):
        if isinstance(skill_item, dict):
            if name := skill_item.get("name"):
                parts.append(str(name))
        elif isinstance(skill_item, str):
            parts.append(skill_item)

    return " ".join(filter(None, parts))


def extract_title_text(wu: dict[str, Any]) -> str:
    """Extract title text from Work Unit.

    Args:
        wu: Work Unit dictionary.

    Returns:
        Title string, or empty string if not present.
    """
    return str(wu.get("title", "") or "")


def extract_skills_text(wu: dict[str, Any]) -> str:
    """Extract skills and tags text from Work Unit.

    Combines tags and skills_demonstrated fields.

    Args:
        wu: Work Unit dictionary.

    Returns:
        Space-separated string of skills and tags.
    """
    parts: list[str] = []

    # Tags
    if tags := wu.get("tags"):
        parts.extend(str(t) for t in tags)

    # Skills demonstrated
    for skill_item in wu.get("skills_demonstrated", []):
        if isinstance(skill_item, dict):
            if name := skill_item.get("name"):
                parts.append(str(name))
        elif isinstance(skill_item, str):
            parts.append(skill_item)

    return " ".join(filter(None, parts))


def extract_experience_text(wu: dict[str, Any]) -> str:
    """Extract experience text from Work Unit (problem, actions, outcome).

    Args:
        wu: Work Unit dictionary.

    Returns:
        Space-separated string of experience content.
    """
    parts: list[str] = []

    # Problem
    if problem := wu.get("problem"):
        if isinstance(problem, dict):
            if stmt := problem.get("statement"):
                parts.append(str(stmt))
            if context := problem.get("context"):
                parts.append(str(context))
        elif isinstance(problem, str):
            parts.append(problem)

    # Actions
    if actions := wu.get("actions"):
        if isinstance(actions, list):
            parts.extend(str(a) for a in actions)
        elif isinstance(actions, str):
            parts.append(actions)

    # Outcome
    if outcome := wu.get("outcome"):
        if isinstance(outcome, dict):
            if result := outcome.get("result"):
                parts.append(str(result))
            if impact := outcome.get("quantified_impact"):
                parts.append(str(impact))
        elif isinstance(outcome, str):
            parts.append(outcome)

    return " ".join(filter(None, parts))
