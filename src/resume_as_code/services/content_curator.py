"""Content curation service for JD-relevant resume sections.

Curates career highlights, certifications, board roles, and position bullets
based on job description relevance using a combination of semantic similarity,
keyword matching, and research-backed limits.

Research Basis: 2024-2025 resume studies analyzing 18.4M resumes.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Generic, TypeVar

import numpy as np

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from resume_as_code.models.board_role import BoardRole
    from resume_as_code.models.certification import Certification
    from resume_as_code.models.config import BulletsPerPositionConfig, CurationConfig
    from resume_as_code.models.job_description import ExperienceLevel, JobDescription
    from resume_as_code.models.position import Position
    from resume_as_code.models.publication import Publication
    from resume_as_code.models.work_unit import WorkUnit
    from resume_as_code.services.embedder import EmbeddingService
    from resume_as_code.services.skill_registry import SkillRegistry


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
        metrics: Mapping of action text to quantified_impact from work unit outcomes.
        reason: Human-readable explanation of curation decision.
    """

    selected: list[T]
    excluded: list[T]
    scores: dict[str, float] = field(default_factory=dict)
    metrics: dict[str, str] = field(default_factory=dict)
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
            # Action-level scoring config (Story 7.18)
            self.action_scoring_enabled = config.action_scoring_enabled
            self.min_action_relevance_score = config.min_action_relevance_score
        else:
            self.limits = DEFAULT_SECTION_LIMITS.copy()
            self.min_relevance_score = 0.2
            self.action_scoring_enabled = True
            self.min_action_relevance_score = 0.25

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

        for highlight in highlights:
            # Use content-based key (short hash) for reliable score lookup
            key = self._highlight_key(highlight)

            # Semantic similarity (60% weight)
            highlight_emb = self.embedder.embed_query(highlight)
            semantic_score = self._cosine_similarity(highlight_emb, jd_embedding)

            # Keyword overlap (40% weight)
            keyword_score = self._keyword_overlap(highlight, jd_keywords)

            # Combined score
            scores[key] = (0.6 * semantic_score) + (0.4 * keyword_score)

        # Sort by score descending
        ranked = sorted(highlights, key=lambda h: scores[self._highlight_key(h)], reverse=True)

        # Filter by minimum relevance score
        min_score = self.min_relevance_score
        qualified = [h for h in ranked if scores[self._highlight_key(h)] >= min_score]
        below_threshold = [h for h in ranked if scores[self._highlight_key(h)] < min_score]

        selected = qualified[:max_count]
        excluded = qualified[max_count:] + below_threshold

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

        # Filter by minimum relevance score
        qualified = [c for c in ranked if scores.get(c.name, 0) >= self.min_relevance_score]
        below_threshold = [c for c in ranked if scores.get(c.name, 0) < self.min_relevance_score]

        # Fill remaining slots after always-include
        remaining_slots = max(0, max_count - len(always_include))
        selected = always_include + qualified[:remaining_slots]
        excluded = qualified[remaining_slots:] + below_threshold

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

        # Filter by minimum relevance score
        min_score = self.min_relevance_score
        qualified = [r for r in ranked if scores.get(r.organization, 0) >= min_score]
        below_threshold = [r for r in ranked if scores.get(r.organization, 0) < min_score]

        remaining_slots = max(0, max_count - len(always_include))

        selected = always_include + qualified[:remaining_slots]
        excluded = qualified[remaining_slots:] + below_threshold

        context = "executive" if is_executive_role else "non-executive"
        return CurationResult(
            selected=selected,
            excluded=excluded,
            scores=scores,
            reason=f"Selected {len(selected)} board roles for {context} role",
        )

    def curate_publications(
        self,
        publications: list[Publication],
        jd: JobDescription,
        registry: SkillRegistry | None = None,
        max_count: int | None = None,
    ) -> CurationResult[Publication]:
        """Select most JD-relevant publications and speaking engagements.

        Scoring formula (Story 8.2 AC #3):
        - 40% semantic similarity (abstract + title + venue vs JD)
        - 40% topic overlap with JD skills/keywords (normalized via SkillRegistry)
        - 20% recency bonus (publications in last 3 years preferred)

        Args:
            publications: All publications to consider.
            jd: Job description for matching.
            registry: SkillRegistry for topic normalization.
            max_count: Override default limit.

        Returns:
            CurationResult with selected/excluded publications and scores.
        """
        if not publications:
            return CurationResult(selected=[], excluded=[], reason="No publications configured")

        max_count = max_count or self.limits["publications"]

        # Pre-compute JD embedding with error handling
        jd_embedding = None
        embeddings_available = True
        try:
            jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)
        except Exception as e:
            logger.warning("Failed to embed JD, falling back to non-semantic scoring: %s", e)
            embeddings_available = False

        # Normalize JD skills and keywords for matching
        jd_skills_normalized: set[str] = set()
        for skill in jd.skills:
            normalized = registry.normalize(skill) if registry else skill
            jd_skills_normalized.add(normalized.lower())
        jd_keywords = {kw.lower() for kw in jd.keywords}
        jd_match_terms = jd_skills_normalized | jd_keywords

        today = date.today()
        scores: dict[str, float] = {}

        for pub in publications:
            # Semantic similarity - use abstract + title + venue
            semantic_score = 0.0
            if embeddings_available and jd_embedding is not None:
                try:
                    pub_text = pub.get_text_for_matching()
                    pub_emb = self.embedder.embed_query(pub_text)
                    semantic_score = self._cosine_similarity(pub_emb, jd_embedding)
                except Exception as e:
                    logger.debug("Failed to embed publication '%s': %s", pub.title, e)
                    # Continue with semantic_score = 0.0

            # Topic overlap - normalized via SkillRegistry
            normalized_topics = pub.get_normalized_topics(registry)
            has_topics = bool(normalized_topics)

            if has_topics:
                topic_matches = sum(
                    1 for topic in normalized_topics if topic.lower() in jd_match_terms
                )
                # Normalize: 2+ matches = 1.0
                topic_score = min(1.0, topic_matches / 2)
            else:
                topic_score = 0.0

            # Recency bonus - publications in last 3 years preferred
            # Defensive date parsing (Issue 7)
            try:
                pub_year = int(pub.date[:4]) if len(pub.date) >= 4 else today.year
            except (ValueError, TypeError):
                logger.debug("Invalid date format for publication '%s': %s", pub.title, pub.date)
                pub_year = today.year  # Assume current year if parse fails

            years_ago = today.year - pub_year
            # Decay: 0.1 per year beyond 3 years, minimum 0.5
            recency_score = 1.0 if years_ago <= 3 else max(0.5, 1.0 - (years_ago - 3) * 0.1)

            # Scoring weights (Story 8.2 AC #3):
            # With topics: 40% semantic + 40% topic + 20% recency
            # Without topics: 80% semantic + 20% recency (redistribute topic weight)
            # When embeddings unavailable: 80% topic + 20% recency (or just recency if no topics)
            if embeddings_available:
                if has_topics:
                    final_score = (
                        (0.4 * semantic_score) + (0.4 * topic_score) + (0.2 * recency_score)
                    )
                else:
                    final_score = (0.8 * semantic_score) + (0.2 * recency_score)
            else:
                # Fallback when embeddings unavailable
                if has_topics:
                    final_score = (0.8 * topic_score) + (0.2 * recency_score)
                else:
                    # Only recency available
                    final_score = recency_score

            scores[self._publication_key(pub)] = final_score

        # Rank by score descending
        ranked = sorted(
            publications, key=lambda p: scores.get(self._publication_key(p), 0), reverse=True
        )

        # Filter by minimum relevance score (AC #4)
        qualified = [
            p for p in ranked if scores.get(self._publication_key(p), 0) >= self.min_relevance_score
        ]
        below_threshold = [
            p for p in ranked if scores.get(self._publication_key(p), 0) < self.min_relevance_score
        ]

        selected = qualified[:max_count]
        excluded = qualified[max_count:] + below_threshold

        return CurationResult(
            selected=selected,
            excluded=excluded,
            scores=scores,
            reason=f"Selected top {len(selected)} of {len(publications)} publications by relevance",
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

    def curate_action_bullets(
        self,
        position: Position,
        work_units: list[WorkUnit],
        jd: JobDescription,
    ) -> CurationResult[str]:
        """Select most JD-relevant action bullets for a position.

        Scores individual action bullets (outcome.result + actions) from all work units
        and selects the top N based on JD relevance.

        Bullet limits based on position recency:
        - Recent (0-3 years): 4-6 bullets
        - Mid (3-7 years): 3-4 bullets
        - Older (7+ years): 2-3 bullets

        Args:
            position: The position these work units belong to.
            work_units: Work units containing actions to curate.
            jd: Job description for matching.

        Returns:
            CurationResult with selected/excluded action strings.
        """
        if not work_units:
            return CurationResult(selected=[], excluded=[], reason="No work units for position")

        # Determine bullet limits based on position age
        years_ago = self._position_age_years(position)
        bullet_config = self._get_bullet_config(years_ago)
        max_bullets = int(bullet_config["max"])

        # Pre-compute JD embedding for efficiency
        jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)

        # Extract all action bullets from all work units
        # Each action is stored as (action_text, work_unit_id, source_type)
        all_actions: list[tuple[str, str, str]] = []
        # Build mapping from outcome.result text to quantified_impact
        action_metrics: dict[str, str] = {}
        for wu in work_units:
            # Include outcome.result as primary bullet
            if wu.outcome.result:
                all_actions.append((wu.outcome.result, wu.id, "result"))
                # Preserve quantified_impact for this outcome
                if wu.outcome.quantified_impact:
                    action_metrics[wu.outcome.result] = wu.outcome.quantified_impact
            # Include actions
            for i, action in enumerate(wu.actions):
                all_actions.append((action, wu.id, f"action_{i}"))

        # Score each action
        # Key format: {work_unit_id}:{source_type}
        scores: dict[str, float] = {}
        for action_text, wu_id, source_type in all_actions:
            key = f"{wu_id}:{source_type}"
            scores[key] = self.score_action(action_text, jd, jd_embedding)

        # Filter by minimum threshold (Task 4: Apply minimum threshold filter)
        min_score = self.min_action_relevance_score
        qualified = [
            (action, f"{wu_id}:{source}")
            for action, wu_id, source in all_actions
            if scores.get(f"{wu_id}:{source}", 0) >= min_score
        ]
        below_threshold = [
            (action, f"{wu_id}:{source}")
            for action, wu_id, source in all_actions
            if scores.get(f"{wu_id}:{source}", 0) < min_score
        ]

        # Log excluded count at DEBUG level (Story 7.18 Task 4.2)
        if below_threshold:
            logger.debug(
                "Excluded %d actions below threshold %.2f for position %s",
                len(below_threshold),
                min_score,
                position.id,
            )

        # Rank by score descending
        qualified.sort(key=lambda x: scores.get(x[1], 0), reverse=True)

        # Select top N
        selected = [action for action, _ in qualified[:max_bullets]]
        excluded_qualified = [action for action, _ in qualified[max_bullets:]]
        excluded_threshold = [action for action, _ in below_threshold]

        return CurationResult(
            selected=selected,
            excluded=excluded_qualified + excluded_threshold,
            scores=scores,
            metrics=action_metrics,
            reason=f"Selected {len(selected)} of {len(all_actions)} actions "
            f"by JD relevance for {years_ago:.0f}-year-old position "
            f"(limit: {max_bullets}, {len(below_threshold)} below threshold)",
        )

    def score_action(
        self,
        action: str,
        jd: JobDescription,
        jd_embedding: NDArray[np.float32] | None = None,
    ) -> float:
        """Score individual action bullet against JD relevance.

        Scoring formula (Story 7.18 AC #2):
        - 60% semantic similarity to JD requirements
        - 30% keyword overlap with JD extracted keywords
        - 10% quantified impact boost if action contains metrics

        Args:
            action: Action bullet text.
            jd: Job description for matching.
            jd_embedding: Pre-computed JD embedding (optional, for batch efficiency).

        Returns:
            Relevance score between 0.0 and 1.0.
        """
        if jd_embedding is None:
            jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)

        # Semantic similarity (60% weight)
        action_emb = self.embedder.embed_query(action)
        semantic_score = self._cosine_similarity(action_emb, jd_embedding)

        # Keyword overlap (30% weight)
        jd_keywords = {kw.lower() for kw in jd.keywords}
        keyword_score = self._keyword_overlap(action, jd_keywords)

        # Quantified boost (10% weight) - binary: 1.0 if quantified, 0.0 if not
        quantified_score = 1.0 if self._has_quantified_text(action) else 0.0

        return (0.6 * semantic_score) + (0.3 * keyword_score) + (0.1 * quantified_score)

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

    @staticmethod
    def _highlight_key(highlight: str) -> str:
        """Generate a stable, content-based key for a highlight.

        Uses a short hash to ensure reliable score lookup regardless of
        highlight ordering or filtering.

        Args:
            highlight: The highlight text.

        Returns:
            A stable key string like 'hl_a1b2c3d4'.
        """
        digest = hashlib.md5(highlight.encode(), usedforsecurity=False).hexdigest()[:8]
        return f"hl_{digest}"

    @staticmethod
    def _publication_key(pub: Publication) -> str:
        """Generate a unique key for a publication.

        Uses title + venue + date to ensure uniqueness even for duplicate titles.
        Falls back to hash if needed.

        Args:
            pub: The Publication object.

        Returns:
            A stable key string like 'pub_a1b2c3d4'.
        """
        content = f"{pub.title}|{pub.venue}|{pub.date}"
        digest = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:8]
        return f"pub_{digest}"

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
        return self._has_quantified_text(text)

    def _has_quantified_text(self, text: str) -> bool:
        """Check if text contains quantified metrics.

        Detects common metric patterns:
        - Percentages: 40%, 100%
        - Dollar amounts: $50K, $1M
        - Multipliers: 3x, 10x
        - Time metrics: 2 hours, 5 days
        - People metrics: 500 users, 5 engineers, 10 teams

        Args:
            text: Text to analyze.

        Returns:
            True if quantified metrics found.
        """
        patterns = [
            r"\d+%",  # Percentages
            r"\$[\d,]+[KMB]?",  # Dollar amounts
            r"\d+x\b",  # Multipliers
            r"\d+\s*(?:hours?|minutes?|days?|weeks?|months?)",  # Time metrics
            r"\d+\s*(?:users?|customers?|clients?)",  # People metrics
            r"\d+\s*(?:teams?|engineers?|developers?)",  # Team metrics
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
