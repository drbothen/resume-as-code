"""Skill coverage and gap analysis service."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from resume_as_code.utils.work_unit_text import extract_work_unit_text


class CoverageLevel(str, Enum):
    """Coverage level for a skill requirement."""

    STRONG = "strong"  # ✓ - Direct match in tags or skills_demonstrated
    WEAK = "weak"  # △ - Mentioned in text but not tagged
    GAP = "gap"  # ✗ - Not found in any Work Unit


@dataclass
class SkillCoverage:
    """Coverage status for a single skill requirement."""

    skill: str
    level: CoverageLevel
    matching_work_units: list[str] = field(default_factory=list)

    @property
    def symbol(self) -> str:
        """Get display symbol for coverage level."""
        return {
            CoverageLevel.STRONG: "✓",
            CoverageLevel.WEAK: "△",
            CoverageLevel.GAP: "✗",
        }[self.level]

    @property
    def color(self) -> str:
        """Get Rich color for coverage level."""
        return {
            CoverageLevel.STRONG: "green",
            CoverageLevel.WEAK: "yellow",
            CoverageLevel.GAP: "red",
        }[self.level]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "skill": self.skill,
            "level": self.level.value,
            "symbol": self.symbol,
            "matching_work_units": self.matching_work_units,
        }


@dataclass
class CoverageReport:
    """Complete coverage analysis report."""

    items: list[SkillCoverage] = field(default_factory=list)

    @property
    def strong_count(self) -> int:
        """Count of strongly covered skills."""
        return sum(1 for item in self.items if item.level == CoverageLevel.STRONG)

    @property
    def weak_count(self) -> int:
        """Count of weakly covered skills."""
        return sum(1 for item in self.items if item.level == CoverageLevel.WEAK)

    @property
    def gap_count(self) -> int:
        """Count of skill gaps."""
        return sum(1 for item in self.items if item.level == CoverageLevel.GAP)

    @property
    def coverage_percentage(self) -> float:
        """Calculate coverage percentage.

        Strong matches count as 1.0, weak as 0.5, gaps as 0.
        Returns 100.0 if no items (no requirements = fully covered).
        """
        if not self.items:
            return 100.0
        covered = self.strong_count + (self.weak_count * 0.5)
        return (covered / len(self.items)) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "items": [item.to_dict() for item in self.items],
            "coverage_percentage": self.coverage_percentage,
            "strong_count": self.strong_count,
            "weak_count": self.weak_count,
            "gap_count": self.gap_count,
        }


def analyze_coverage(
    jd_skills: list[str],
    work_units: list[dict[str, Any]],
) -> CoverageReport:
    """Analyze skill coverage against JD requirements.

    Args:
        jd_skills: Skills extracted from job description.
        work_units: Work Unit dictionaries (selected for the resume).

    Returns:
        CoverageReport with coverage status for each skill.
    """
    items: list[SkillCoverage] = []

    for skill in jd_skills:
        skill_lower = skill.lower()
        matching_wus: list[str] = []
        match_strength = 0

        for wu in work_units:
            wu_id = wu.get("id", "unknown")
            wu_text = extract_work_unit_text(wu).lower()

            # Get tags (normalize to lowercase)
            wu_tags = [str(t).lower() for t in wu.get("tags", [])]

            # Get skills_demonstrated (handle both string and dict formats)
            wu_skills: list[str] = []
            for skill_item in wu.get("skills_demonstrated", []):
                if isinstance(skill_item, dict):
                    if name := skill_item.get("name"):
                        wu_skills.append(str(name).lower())
                elif isinstance(skill_item, str):
                    wu_skills.append(skill_item.lower())

            # Strong match: skill in tags or skills_demonstrated
            if skill_lower in wu_tags or skill_lower in wu_skills:
                if wu_id not in matching_wus:
                    matching_wus.append(wu_id)
                match_strength = max(match_strength, 2)

            # Weak match: skill mentioned anywhere in text
            elif skill_lower in wu_text:
                if wu_id not in matching_wus:
                    matching_wus.append(wu_id)
                match_strength = max(match_strength, 1)

        # Determine coverage level
        if match_strength >= 2:
            level = CoverageLevel.STRONG
        elif match_strength >= 1:
            level = CoverageLevel.WEAK
        else:
            level = CoverageLevel.GAP

        items.append(
            SkillCoverage(
                skill=skill,
                level=level,
                matching_work_units=matching_wus,
            )
        )

    return CoverageReport(items=items)
