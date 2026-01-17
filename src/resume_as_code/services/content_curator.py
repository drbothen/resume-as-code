"""Content curation service for JD-relevant resume sections.

Curates career highlights, certifications, board roles, and position bullets
based on job description relevance using a combination of semantic similarity,
keyword matching, and research-backed limits.

Research Basis: 2024-2025 resume studies analyzing 18.4M resumes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Generic, TypeVar

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from resume_as_code.models.board_role import BoardRole
    from resume_as_code.models.certification import Certification
    from resume_as_code.models.config import BulletsPerPositionConfig, CurationConfig
    from resume_as_code.models.job_description import ExperienceLevel, JobDescription
    from resume_as_code.models.position import Position
    from resume_as_code.models.work_unit import WorkUnit
    from resume_as_code.services.embedder import EmbeddingService


T = TypeVar("T")


# Research-backed section limits (2024-2025 resume studies)
DEFAULT_SECTION_LIMITS = {
    "career_highlights": 4,  # Research: 3-5 optimal
    "certifications": 5,  # Research: 3-5 most relevant
    "board_roles": 3,  # 2-3 unless executive role
    "board_roles_executive": 5,  # Executive roles show more board experience
    "publications": 3,  # Keep focused
    "skills": 10,  # Research: 6-10 optimal (median 8-9)
}

# Bullets per position based on recency
BULLETS_PER_POSITION: dict[str, dict[str, int | float]] = {
    "recent": {"years": 3, "min": 4, "max": 6},  # 0-3 years: 4-6 bullets
    "mid": {"years": 7, "min": 3, "max": 4},  # 3-7 years: 3-4 bullets
    "older": {"years": float("inf"), "min": 2, "max": 3},  # 7+ years: 2-3 bullets
}

# Scoring weights
QUANTIFIED_BOOST = 1.25  # 25% boost for quantified achievements


@dataclass
class CurationResult(Generic[T]):
    """Result of content curation for a section.

    Attributes:
        selected: Items selected for inclusion (ordered by relevance).
        excluded: Items not selected (ordered by relevance).
        scores: Mapping of item identifier to relevance score (0.0 to 1.0).
        reason: Human-readable explanation of curation decision.
    """

    selected: list[T]
    excluded: list[T]
    scores: dict[str, float] = field(default_factory=dict)
    reason: str = ""


class ContentCurator:
    """Curates resume content based on JD relevance.

    Uses a combination of:
    - Semantic similarity (embeddings)
    - Keyword overlap (BM25-style)
    - Direct skill matching
    - Recency weighting
    - Quantification boost
    """

    def __init__(
        self,
        embedder: EmbeddingService,
        config: CurationConfig | None = None,
        quantified_boost: float = QUANTIFIED_BOOST,
    ) -> None:
        """Initialize the content curator.

        Args:
            embedder: Embedding service for semantic matching.
            config: Curation configuration with section limits.
            quantified_boost: Multiplier for quantified achievements.
        """
        self.embedder = embedder
        self.quantified_boost = quantified_boost
        self.bullets_config: BulletsPerPositionConfig | None = None

        # Build limits from config or use defaults
        if config is not None:
            self.limits = {
                "career_highlights": config.career_highlights_max,
                "certifications": config.certifications_max,
                "board_roles": config.board_roles_max,
                "board_roles_executive": config.board_roles_executive_max,
                "publications": config.publications_max,
                "skills": config.skills_max,
            }
            self.bullets_config = config.bullets_per_position
            self.min_relevance_score = config.min_relevance_score
        else:
            self.limits = DEFAULT_SECTION_LIMITS.copy()
            self.min_relevance_score = 0.2

    def curate_highlights(
        self,
        highlights: list[str],
        jd: JobDescription,
        max_count: int | None = None,
    ) -> CurationResult[str]:
        """Select most JD-relevant career highlights.

        Args:
            highlights: All career highlights to consider.
            jd: Job description for matching.
            max_count: Override default limit.

        Returns:
            CurationResult with selected/excluded highlights and scores.
        """
        if not highlights:
            return CurationResult(selected=[], excluded=[], reason="No highlights configured")

        max_count = max_count or self.limits["career_highlights"]

        # Pre-compute JD embedding
        jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)
        jd_keywords = {kw.lower() for kw in jd.keywords}

        scores: dict[str, float] = {}

        for i, highlight in enumerate(highlights):
            # Semantic similarity (60% weight)
            highlight_emb = self.embedder.embed_query(highlight)
            semantic_score = self._cosine_similarity(highlight_emb, jd_embedding)

            # Keyword overlap (40% weight)
            keyword_score = self._keyword_overlap(highlight, jd_keywords)

            # Combined score
            scores[f"highlight_{i}"] = (0.6 * semantic_score) + (0.4 * keyword_score)

        # Sort by score and select top N
        ranked_indices = sorted(
            range(len(highlights)),
            key=lambda i: scores[f"highlight_{i}"],
            reverse=True,
        )

        # Filter by minimum relevance score
        qualified_indices = [
            i for i in ranked_indices if scores[f"highlight_{i}"] >= self.min_relevance_score
        ]

        selected = [highlights[i] for i in qualified_indices[:max_count]]
        excluded = [highlights[i] for i in qualified_indices[max_count:]] + [
            highlights[i]
            for i in ranked_indices
            if scores[f"highlight_{i}"] < self.min_relevance_score
        ]

        return CurationResult(
            selected=selected,
            excluded=excluded,
            scores=scores,
            reason=f"Selected top {len(selected)} of {len(highlights)} highlights by JD relevance",
        )

    def curate_certifications(
        self,
        certifications: list[Certification],
        jd: JobDescription,
        max_count: int | None = None,
    ) -> CurationResult[Certification]:
        """Select most JD-relevant certifications.

        Priority items (priority='always') are always included.
        Remaining slots filled by highest-scoring items.

        Args:
            certifications: All certifications to consider.
            jd: Job description for matching.
            max_count: Override default limit.

        Returns:
            CurationResult with selected/excluded certifications.
        """
        if not certifications:
            return CurationResult(selected=[], excluded=[], reason="No certifications configured")

        max_count = max_count or self.limits["certifications"]

        # Separate priority items
        always_include = [c for c in certifications if getattr(c, "priority", None) == "always"]
        candidates = [c for c in certifications if c not in always_include]

        # Pre-compute JD data
        jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)
        jd_skills = {s.lower() for s in jd.skills}

        scores: dict[str, float] = {}

        for cert in candidates:
            # Direct skill match (50% weight) - cert name/issuer contains JD skill
            skill_match_count = sum(
                1
                for skill in jd_skills
                if skill in cert.name.lower() or skill in (cert.issuer or "").lower()
            )
            skill_score = min(1.0, skill_match_count * 0.5)

            # Semantic similarity (30% weight)
            cert_text = f"{cert.name} {cert.issuer or ''}"
            cert_emb = self.embedder.embed_query(cert_text)
            semantic_score = self._cosine_similarity(cert_emb, jd_embedding)

            # Recency/status bonus (20% weight) - active certs preferred
            status = cert.get_status() if hasattr(cert, "get_status") else "active"
            recency_score = 1.0 if status == "active" else 0.5

            scores[cert.name] = (skill_score * 0.5) + (semantic_score * 0.3) + (recency_score * 0.2)

        # Rank candidates by score
        ranked = sorted(candidates, key=lambda c: scores.get(c.name, 0), reverse=True)

        # Fill remaining slots after always-include
        remaining_slots = max(0, max_count - len(always_include))
        selected = always_include + ranked[:remaining_slots]
        excluded = ranked[remaining_slots:]

        selected_by_relevance = len(selected) - len(always_include)
        return CurationResult(
            selected=selected,
            excluded=excluded,
            scores=scores,
            reason=f"Selected {len(selected)} certifications "
            f"({len(always_include)} priority + {selected_by_relevance} by relevance)",
        )

    def curate_board_roles(
        self,
        board_roles: list[BoardRole],
        jd: JobDescription,
        is_executive_role: bool = False,
        max_count: int | None = None,
    ) -> CurationResult[BoardRole]:
        """Select most JD-relevant board roles.

        Executive roles get more board role slots.

        Args:
            board_roles: All board roles to consider.
            jd: Job description for matching.
            is_executive_role: Whether JD is for executive position.
            max_count: Override default limit.

        Returns:
            CurationResult with selected/excluded board roles.
        """
        if not board_roles:
            return CurationResult(selected=[], excluded=[], reason="No board roles configured")

        # Executive roles show more board experience
        if max_count is None:
            max_count = (
                self.limits["board_roles_executive"]
                if is_executive_role
                else self.limits["board_roles"]
            )

        # Separate priority items
        always_include = [r for r in board_roles if getattr(r, "priority", None) == "always"]
        candidates = [r for r in board_roles if r not in always_include]

        # Pre-compute JD embedding
        jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)

        scores: dict[str, float] = {}

        for role in candidates:
            # Semantic similarity
            role_text = f"{role.organization} {role.role} {role.focus or ''}"
            role_emb = self.embedder.embed_query(role_text)
            semantic_score = self._cosine_similarity(role_emb, jd_embedding)

            # Recency bonus - current roles preferred
            recency_score = 1.0 if role.is_current else 0.7

            scores[role.organization] = (semantic_score * 0.7) + (recency_score * 0.3)

        # Rank and select
        ranked = sorted(candidates, key=lambda r: scores.get(r.organization, 0), reverse=True)
        remaining_slots = max(0, max_count - len(always_include))

        selected = always_include + ranked[:remaining_slots]
        excluded = ranked[remaining_slots:]

        context = "executive" if is_executive_role else "non-executive"
        return CurationResult(
            selected=selected,
            excluded=excluded,
            scores=scores,
            reason=f"Selected {len(selected)} board roles for {context} role",
        )

    def curate_position_bullets(
        self,
        position: Position,
        work_units: list[WorkUnit],
        jd: JobDescription,
    ) -> CurationResult[WorkUnit]:
        """Select most JD-relevant work units for a position.

        Bullet limits based on position recency:
        - Recent (0-3 years): 4-6 bullets
        - Mid (3-7 years): 3-4 bullets
        - Older (7+ years): 2-3 bullets

        Quantified achievements get 25% boost.

        Args:
            position: The position these work units belong to.
            work_units: Work units to curate.
            jd: Job description for matching.

        Returns:
            CurationResult with selected/excluded work units.
        """
        if not work_units:
            return CurationResult(selected=[], excluded=[], reason="No work units for position")

        # Determine bullet limits based on position age
        years_ago = self._position_age_years(position)
        bullet_config = self._get_bullet_config(years_ago)
        max_bullets = int(bullet_config["max"])

        # Pre-compute JD embedding
        jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)

        scores: dict[str, float] = {}

        for wu in work_units:
            # Extract text for matching
            wu_text = self._extract_work_unit_text(wu)
            wu_emb = self.embedder.embed_query(wu_text)

            # Semantic similarity
            base_score = self._cosine_similarity(wu_emb, jd_embedding)

            # Quantified boost
            if self._has_quantified_impact(wu):
                base_score *= self.quantified_boost

            scores[wu.id] = min(1.0, base_score)

        # Rank and select
        ranked = sorted(work_units, key=lambda wu: scores.get(wu.id, 0), reverse=True)
        selected = ranked[:max_bullets]
        excluded = ranked[max_bullets:]

        return CurationResult(
            selected=selected,
            excluded=excluded,
            scores=scores,
            reason=f"Selected {len(selected)} of {len(work_units)} bullets "
            f"for {years_ago:.0f}-year-old position (limit: {max_bullets})",
        )

    # --- Helper Methods ---

    def _cosine_similarity(
        self,
        vec_a: NDArray[np.float32],
        vec_b: NDArray[np.float32],
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        dot = float(np.dot(vec_a, vec_b))
        norm_a = float(np.linalg.norm(vec_a))
        norm_b = float(np.linalg.norm(vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _keyword_overlap(self, text: str, keywords: set[str]) -> float:
        """Calculate keyword overlap score (0.0 to 1.0)."""
        if not keywords:
            return 0.0
        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw in text_lower)
        # Normalize: 3+ matches = 1.0
        return min(1.0, matches / 3)

    def _position_age_years(self, position: Position) -> float:
        """Calculate position age in years from end date."""
        if position.end_date is None:
            return 0.0  # Current position

        # Parse YYYY-MM format
        year, month = position.end_date.split("-")
        end_date = date(int(year), int(month), 1)
        days_ago = (date.today() - end_date).days
        return days_ago / 365.25

    def _get_bullet_config(self, years_ago: float) -> dict[str, int | float]:
        """Get bullet limits for position age."""
        # Use config if available
        if self.bullets_config is not None:
            if years_ago <= self.bullets_config.recent_years:
                return {
                    "years": self.bullets_config.recent_years,
                    "min": 4,
                    "max": self.bullets_config.recent_max,
                }
            elif years_ago <= self.bullets_config.mid_years:
                return {
                    "years": self.bullets_config.mid_years,
                    "min": 3,
                    "max": self.bullets_config.mid_max,
                }
            else:
                return {
                    "years": float("inf"),
                    "min": 2,
                    "max": self.bullets_config.older_max,
                }

        # Fall back to defaults
        if years_ago <= BULLETS_PER_POSITION["recent"]["years"]:
            return BULLETS_PER_POSITION["recent"]
        elif years_ago <= BULLETS_PER_POSITION["mid"]["years"]:
            return BULLETS_PER_POSITION["mid"]
        else:
            return BULLETS_PER_POSITION["older"]

    def _extract_work_unit_text(self, wu: WorkUnit) -> str:
        """Extract searchable text from work unit."""
        parts = [
            wu.title,
            wu.outcome.result,
            wu.outcome.quantified_impact or "",
            wu.outcome.business_value or "",
            " ".join(wu.actions),
        ]
        if wu.tags:
            parts.append(" ".join(wu.tags))
        return " ".join(filter(None, parts))

    def _has_quantified_impact(self, wu: WorkUnit) -> bool:
        """Check if work unit has quantified metrics."""
        outcome = wu.outcome
        text = f"{outcome.result} {outcome.quantified_impact or ''}"
        patterns = [
            r"\d+%",  # Percentages
            r"\$[\d,]+[KMB]?",  # Dollar amounts
            r"\d+x\b",  # Multipliers
            r"\d+\s*(?:hours?|days?|weeks?|months?)",  # Time metrics
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def is_executive_level(experience_level: ExperienceLevel) -> bool:
    """Check if experience level indicates an executive role.

    Args:
        experience_level: JD's detected experience level.

    Returns:
        True if executive or principal level.
    """
    from resume_as_code.models.job_description import ExperienceLevel

    return experience_level in [ExperienceLevel.EXECUTIVE, ExperienceLevel.PRINCIPAL]
