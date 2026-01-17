"""Skill curation service for resume display.

Handles deduplication, JD-based ranking, exclusions, and limiting
to produce a curated list of skills for resume output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from resume_as_code.services.skill_registry import SkillRegistry


@dataclass
class CurationResult:
    """Result of skill curation.

    Attributes:
        included: Skills to display, ordered by relevance.
        excluded: List of (skill, reason) tuples for excluded skills.
        stats: Curation statistics for transparency.
    """

    included: list[str]
    excluded: list[tuple[str, str]]
    stats: dict[str, int]


class SkillCurator:
    """Curates skills for resume display.

    Handles deduplication, JD-based ranking, exclusions, and limiting.
    """

    def __init__(
        self,
        max_count: int = 15,
        exclude: list[str] | None = None,
        prioritize: list[str] | None = None,
        registry: SkillRegistry | None = None,
    ) -> None:
        """Initialize the skill curator.

        Args:
            max_count: Maximum number of skills to include.
            exclude: Skills to always exclude (case-insensitive).
            prioritize: Skills to always prioritize (case-insensitive).
            registry: Optional SkillRegistry for alias normalization.
        """
        self.max_count = max_count
        self.exclude = {s.lower() for s in (exclude or [])}
        self.prioritize = {s.lower() for s in (prioritize or [])}
        self.registry = registry

    def curate(
        self,
        raw_skills: set[str],
        jd_keywords: set[str] | None = None,
    ) -> CurationResult:
        """Curate skills for resume display.

        Args:
            raw_skills: All skills extracted from work units.
            jd_keywords: Keywords from job description (optional).

        Returns:
            CurationResult with included/excluded skills and reasons.
        """
        jd_keywords = jd_keywords or set()
        # Expand JD keywords with registry aliases for better matching
        jd_lower = self._expand_jd_keywords(jd_keywords)

        # Step 1: Normalize and deduplicate (case-insensitive)
        normalized = self._deduplicate(raw_skills)

        # Step 2: Remove excluded skills
        filtered, excluded_by_config = self._filter_excluded(normalized)

        # Step 3: Score by JD relevance
        scored = self._score_skills(filtered, jd_lower)

        # Step 4: Sort by score (prioritized first, then JD matches, then others)
        sorted_skills = self._sort_by_relevance(scored)

        # Step 5: Limit to max_count
        included = sorted_skills[: self.max_count]
        excluded_by_limit = [(s, "exceeded_max_display") for s in sorted_skills[self.max_count :]]

        # Combine exclusions
        all_excluded = excluded_by_config + excluded_by_limit

        return CurationResult(
            included=included,
            excluded=all_excluded,
            stats={
                "total_raw": len(raw_skills),
                "after_dedup": len(normalized),
                "after_filter": len(filtered),
                "included": len(included),
                "excluded": len(all_excluded),
            },
        )

    def _normalize_display_format(self, skill: str) -> str:
        """Normalize skill tags to proper display format.

        Converts hyphenated tags (e.g., "cloud-migration") to proper
        display format (e.g., "Cloud Migration"). Also title-cases
        all-lowercase skills (e.g., "compliance" -> "Compliance").
        Preserves existing casing for mixed-case or uppercase skills
        (e.g., "AWS", "Python", "CI/CD").

        For hyphenated strings:
        - Words ≤3 chars are uppercased (likely acronyms: ci, cd, api, aws, ot)
        - Words >3 chars get title case

        For non-hyphenated strings:
        - All lowercase -> title case (e.g., "compliance" -> "Compliance")
        - Mixed/uppercase -> unchanged (e.g., "AWS", "Python")

        Args:
            skill: Raw skill string

        Returns:
            Normalized display string.
        """
        # Handle hyphenated strings
        if "-" in skill:
            words = skill.replace("-", " ").split()
            result = []
            for word in words:
                if len(word) <= 3:
                    # Short words are likely acronyms (CI, CD, API, AWS, OT, IT, ML)
                    result.append(word.upper())
                else:
                    # Longer words get title case
                    result.append(word.title())
            return " ".join(result)

        # Handle non-hyphenated all-lowercase strings
        # Only title-case if longer than 3 chars (short ones like aws, k8s are likely acronyms)
        if skill.islower() and len(skill) > 3:
            return skill.title()

        # Preserve existing casing (AWS, Python, CI/CD, etc.)
        return skill

    def _deduplicate(self, skills: set[str]) -> dict[str, str]:
        """Deduplicate skills case-insensitively, keeping best casing.

        If registry is set, normalizes aliases to canonical names.
        For unknown skills with O*NET configured, attempts discovery
        via lookup_and_cache() (Story 7.17).

        Returns dict mapping normalized key -> display form.
        Key normalization: lowercase + hyphens converted to spaces.
        This ensures "business-development" and "Business Development" dedupe.
        Display normalization: hyphens to spaces, title case applied.
        Prefers: Title Case > UPPERCASE > lowercase
        Filters out empty and whitespace-only strings.
        """
        normalized: dict[str, str] = {}
        for skill in skills:
            # Skip empty or whitespace-only strings
            if not skill or not skill.strip():
                continue

            # Apply registry normalization if available
            display = skill
            if self.registry:
                normalized_skill = self.registry.normalize(skill)
                # If passthrough (unknown skill) and O*NET available, try lookup
                if normalized_skill == skill and self.registry.has_onet_service:
                    entry = self.registry.lookup_and_cache(skill)
                    display = entry.canonical if entry is not None else skill
                else:
                    display = normalized_skill

            # Normalize display format: hyphens to spaces, title case
            # e.g., "cloud-migration" -> "Cloud Migration"
            display = self._normalize_display_format(display)

            # Normalize key: lowercase + hyphens to spaces for deduplication
            # e.g., "business-development" dedupes with "Business Development"
            lower = display.lower().replace("-", " ")
            if lower not in normalized:
                normalized[lower] = display
            else:
                # Prefer title case, then uppercase, then existing
                existing = normalized[lower]
                prefer_new = display.istitle() and not existing.istitle()
                prefer_new = prefer_new or (display.isupper() and existing.islower())
                if prefer_new:
                    normalized[lower] = display
        return normalized

    def _filter_excluded(
        self, normalized: dict[str, str]
    ) -> tuple[dict[str, str], list[tuple[str, str]]]:
        """Remove excluded skills.

        Returns:
            Tuple of (filtered dict, list of excluded (skill, reason) tuples).
        """
        filtered: dict[str, str] = {}
        excluded: list[tuple[str, str]] = []
        for lower, display in normalized.items():
            if lower in self.exclude:
                excluded.append((display, "config_exclude"))
            else:
                filtered[lower] = display
        return filtered, excluded

    def _score_skills(
        self, skills: dict[str, str], jd_keywords: set[str]
    ) -> dict[str, tuple[str, int]]:
        """Score skills by JD relevance.

        Returns dict mapping lowercase -> (display, score).
        Score: 100 for prioritized, 10 for JD match, 1 for others.
        """
        scored: dict[str, tuple[str, int]] = {}
        for lower, display in skills.items():
            if lower in self.prioritize:
                score = 100
            elif lower in jd_keywords:
                score = 10
            else:
                score = 1
            scored[lower] = (display, score)
        return scored

    def _sort_by_relevance(self, scored: dict[str, tuple[str, int]]) -> list[str]:
        """Sort skills by score descending, then alphabetically."""
        sorted_items = sorted(
            scored.items(),
            key=lambda x: (-x[1][1], x[1][0].lower()),  # -score, then alpha
        )
        return [display for _, (display, _) in sorted_items]

    def _expand_jd_keywords(self, keywords: set[str]) -> set[str]:
        """Expand JD keywords with skill aliases for better matching.

        If registry is available, each keyword is expanded to include
        all its aliases (e.g., "Kubernetes" -> {"kubernetes", "k8s", "kube"}).

        Args:
            keywords: Original JD keywords.

        Returns:
            Expanded set of lowercase keywords including aliases.
        """
        if not self.registry:
            return {k.lower() for k in keywords}

        expanded: set[str] = set()
        for keyword in keywords:
            # Add all aliases including canonical (all lowercase)
            expanded.update(self.registry.get_aliases(keyword))
        return expanded
