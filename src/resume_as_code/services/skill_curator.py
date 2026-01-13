"""Skill curation service for resume display.

Handles deduplication, JD-based ranking, exclusions, and limiting
to produce a curated list of skills for resume output.
"""

from __future__ import annotations

from dataclasses import dataclass


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
    ) -> None:
        """Initialize the skill curator.

        Args:
            max_count: Maximum number of skills to include.
            exclude: Skills to always exclude (case-insensitive).
            prioritize: Skills to always prioritize (case-insensitive).
        """
        self.max_count = max_count
        self.exclude = {s.lower() for s in (exclude or [])}
        self.prioritize = {s.lower() for s in (prioritize or [])}

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
        jd_lower = {k.lower() for k in jd_keywords}

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

    def _deduplicate(self, skills: set[str]) -> dict[str, str]:
        """Deduplicate skills case-insensitively, keeping best casing.

        Returns dict mapping lowercase -> display form.
        Prefers: Title Case > UPPERCASE > lowercase
        Filters out empty and whitespace-only strings.
        """
        normalized: dict[str, str] = {}
        for skill in skills:
            # Skip empty or whitespace-only strings
            if not skill or not skill.strip():
                continue
            lower = skill.lower()
            if lower not in normalized:
                normalized[lower] = skill
            else:
                # Prefer title case, then uppercase, then existing
                existing = normalized[lower]
                prefer_new = skill.istitle() and not existing.istitle()
                prefer_new = prefer_new or (skill.isupper() and existing.islower())
                if prefer_new:
                    normalized[lower] = skill
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
