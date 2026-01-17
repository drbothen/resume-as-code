"""Hybrid BM25 + Semantic ranker with RRF fusion."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any

import numpy as np
from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]

from resume_as_code.services.impact_classifier import (
    calculate_impact_alignment,
    classify_impact,
    has_quantified_impact,
    infer_role_type,
)
from resume_as_code.services.seniority_inference import (
    calculate_seniority_alignment,
    infer_seniority,
)
from resume_as_code.utils.tokenizer import get_tokenizer
from resume_as_code.utils.work_unit_text import (
    extract_experience_text,
    extract_skills_text,
    extract_title_text,
    extract_work_unit_text,
)

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from resume_as_code.models.config import ScoringWeights
    from resume_as_code.models.job_description import JobDescription
    from resume_as_code.services.embedder import EmbeddingService


@dataclass
class RankingResult:
    """Result of ranking a single Work Unit."""

    work_unit_id: str
    work_unit: dict[str, Any]
    score: float  # 0.0 to 1.0
    bm25_rank: int
    semantic_rank: int
    match_reasons: list[str] = field(default_factory=list)
    seniority_score: float = field(default=1.0)  # 0.0 to 1.0, Story 7.12
    impact_score: float = field(default=0.5)  # 0.0 to 1.0, Story 7.13


@dataclass
class RankingOutput:
    """Complete ranking output."""

    results: list[RankingResult]
    jd_keywords: list[str]

    @property
    def selected(self) -> list[RankingResult]:
        """Get selected (top) results."""
        return self.results

    def top(self, n: int) -> list[RankingResult]:
        """Get top N results."""
        return self.results[:n]


class HybridRanker:
    """Hybrid BM25 + Semantic ranker with RRF fusion.

    Combines lexical (BM25) and semantic (embedding similarity) ranking
    using Reciprocal Rank Fusion for robust relevance scoring.

    Field-Weighted BM25 (Story 7.8):
        When field weights are configured (title_weight, skills_weight,
        experience_weight differ from 1.0), uses field-weighted BM25 scoring.
        Default weights (title=2.0, skills=1.5, experience=1.0) are based on
        HBR 2023 research showing recruiters spend ~7 seconds on initial scan,
        focusing on title and skills first.

        To use standard BM25 (equal field weights), explicitly set all field
        weights to 1.0 in ScoringWeights configuration.
    """

    RRF_K = 60  # RRF constant (standard value)

    # Maximum match reasons to return per Work Unit.
    # Limited to 3 to prevent cognitive overload in UI display.
    # Research suggests 3-5 bullet points optimal for quick scanning.
    _MAX_MATCH_REASONS = 3

    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        """Initialize the ranker.

        Args:
            embedding_service: Optional embedding service (lazy-loaded if not provided).
        """
        self._embedding_service = embedding_service

    @property
    def embedding_service(self) -> EmbeddingService:
        """Lazy-load embedding service."""
        if self._embedding_service is None:
            from resume_as_code.services.embedder import EmbeddingService

            self._embedding_service = EmbeddingService()
        return self._embedding_service

    def rank(
        self,
        work_units: list[dict[str, Any]],
        jd: JobDescription,
        top_k: int = 10,
        scoring_weights: ScoringWeights | None = None,
        positions: dict[str, Any] | None = None,
    ) -> RankingOutput:
        """Rank Work Units against a job description.

        Args:
            work_units: List of Work Unit dictionaries.
            jd: Parsed JobDescription.
            top_k: Number of top results to return.
            scoring_weights: Optional weights for BM25/semantic balance.
            positions: Optional dict of position_id -> Position for seniority inference.

        Returns:
            RankingOutput with sorted results.
        """
        if not work_units:
            return RankingOutput(results=[], jd_keywords=jd.keywords)

        # Extract text from Work Units
        wu_texts = [extract_work_unit_text(wu) for wu in work_units]
        wu_ids = [wu.get("id", f"wu-{i}") for i, wu in enumerate(work_units)]

        # BM25 ranking - use field-weighted if weights differ from default
        if scoring_weights and self._has_field_weights(scoring_weights):
            bm25_ranks = self._bm25_rank_weighted(work_units, jd.text_for_ranking, scoring_weights)
        else:
            bm25_ranks = self._bm25_rank(wu_texts, jd.text_for_ranking)

        # Semantic ranking - use sectioned when enabled (Story 7.11)
        if scoring_weights and scoring_weights.use_sectioned_semantic:
            semantic_ranks = self._semantic_rank_sectioned(work_units, jd, scoring_weights)
        else:
            semantic_ranks = self._semantic_rank(wu_texts, jd.text_for_ranking)

        # RRF fusion with optional weights (AC: #3)
        rrf_scores = self._rrf_fusion(bm25_ranks, semantic_ranks, scoring_weights)

        # Normalize relevance scores to 0.0-1.0
        max_score = max(rrf_scores) if rrf_scores else 1.0
        min_score = min(rrf_scores) if rrf_scores else 0.0

        # Handle edge case: single work unit or all same scores
        if max_score == min_score:
            normalized_relevance = [1.0] * len(rrf_scores)
        else:
            normalized_relevance = [(s - min_score) / (max_score - min_score) for s in rrf_scores]

        # Calculate recency scores for each work unit (Story 7.9)
        recency_scores = [self._calculate_recency_score(wu, scoring_weights) for wu in work_units]

        # Calculate seniority alignment scores (Story 7.12)
        seniority_scores = [
            self._calculate_seniority_score(wu, jd, scoring_weights, positions) for wu in work_units
        ]

        # Calculate impact alignment scores (Story 7.13)
        impact_scores = [self._calculate_impact_score(wu, jd, scoring_weights) for wu in work_units]

        # Blend relevance, recency, seniority, and impact scores
        final_scores = self._blend_scores(
            normalized_relevance, recency_scores, seniority_scores, impact_scores, scoring_weights
        )

        # Sort by final score (higher is better), then by ID for determinism
        sorted_indices = sorted(
            range(len(work_units)),
            key=lambda i: (final_scores[i], wu_ids[i]),
            reverse=True,
        )

        # Build results - return top_k * 2 for exclusion display
        results: list[RankingResult] = []
        for idx in sorted_indices[: top_k * 2]:
            match_reasons = self._extract_match_reasons(
                work_units[idx], jd, seniority_scores[idx], impact_scores[idx], scoring_weights
            )
            results.append(
                RankingResult(
                    work_unit_id=wu_ids[idx],
                    work_unit=work_units[idx],
                    score=final_scores[idx],
                    bm25_rank=bm25_ranks[idx],
                    semantic_rank=semantic_ranks[idx],
                    match_reasons=match_reasons,
                    seniority_score=seniority_scores[idx],
                    impact_score=impact_scores[idx],
                )
            )

        return RankingOutput(results=results, jd_keywords=jd.keywords)

    def _bm25_rank(self, documents: list[str], query: str) -> list[int]:
        """Compute BM25 ranks (1-indexed, lower is better).

        Uses ResumeTokenizer for intelligent tokenization with:
        - Technical abbreviation expansion (ML -> machine learning)
        - Hyphen/slash normalization (CI/CD -> ci cd)
        - Domain stop word filtering (requirements, experience, etc.)
        - Optional spaCy lemmatization (engineering -> engineer)

        Note: Lemmatization is disabled by default for performance since spaCy
        is an optional dependency. Abbreviation expansion and normalization
        provide the majority of matching benefits without the spaCy overhead.
        """
        # Use ResumeTokenizer for intelligent tokenization (Story 7.10)
        tokenizer = get_tokenizer(use_lemmatization=False)

        # Tokenize documents and query with normalization
        tokenized_docs = [tokenizer.tokenize(doc) for doc in documents]
        tokenized_query = tokenizer.tokenize(query)

        # Handle empty documents (add placeholder to avoid BM25 errors)
        tokenized_docs = [doc if doc else ["_empty_"] for doc in tokenized_docs]

        # Build BM25 index
        bm25 = BM25Okapi(tokenized_docs)

        # Get scores
        scores: NDArray[np.float64] = bm25.get_scores(tokenized_query)

        # Compute ranks (1-indexed, lower rank = better match)
        sorted_indices = np.argsort(scores)[::-1]
        ranks = [0] * len(scores)
        for rank, idx in enumerate(sorted_indices, 1):
            ranks[idx] = rank

        return ranks

    def _has_field_weights(self, scoring_weights: ScoringWeights) -> bool:
        """Check if field-specific weights are configured.

        Returns True if any field weight differs from 1.0.
        """
        return (
            scoring_weights.title_weight != 1.0
            or scoring_weights.skills_weight != 1.0
            or scoring_weights.experience_weight != 1.0
        )

    def _bm25_rank_weighted(
        self,
        work_units: list[dict[str, Any]],
        query: str,
        scoring_weights: ScoringWeights,
    ) -> list[int]:
        """Compute field-weighted BM25 ranks.

        Scores title, skills, and experience fields separately with configurable
        weights, then combines for final ranking.

        Uses ResumeTokenizer for intelligent tokenization with:
        - Technical abbreviation expansion (ML -> machine learning)
        - Hyphen/slash normalization (CI/CD -> ci cd)
        - Domain stop word filtering (requirements, experience, etc.)
        - Optional spaCy lemmatization (engineering -> engineer)

        Note: Lemmatization is disabled by default for performance since spaCy
        is an optional dependency. Abbreviation expansion and normalization
        provide the majority of matching benefits without the spaCy overhead.

        Args:
            work_units: List of Work Unit dictionaries.
            query: Query text (JD text_for_ranking).
            scoring_weights: Field weights from config.

        Returns:
            List of ranks (1-indexed, lower is better).
        """
        # Use ResumeTokenizer for intelligent tokenization (Story 7.10)
        tokenizer = get_tokenizer(use_lemmatization=False)

        # Extract field-specific text
        title_texts = [extract_title_text(wu) for wu in work_units]
        skills_texts = [extract_skills_text(wu) for wu in work_units]
        experience_texts = [extract_experience_text(wu) for wu in work_units]

        # Tokenize with normalization
        tokenized_query = tokenizer.tokenize(query) if query else []
        title_corpus = [tokenizer.tokenize(t) if t else ["_empty_"] for t in title_texts]
        skills_corpus = [tokenizer.tokenize(s) if s else ["_empty_"] for s in skills_texts]
        experience_corpus = [tokenizer.tokenize(e) if e else ["_empty_"] for e in experience_texts]

        # Handle empty query
        if not tokenized_query:
            tokenized_query = ["_empty_"]

        # Score each field separately
        title_bm25 = BM25Okapi(title_corpus)
        skills_bm25 = BM25Okapi(skills_corpus)
        experience_bm25 = BM25Okapi(experience_corpus)

        title_scores: NDArray[np.float64] = title_bm25.get_scores(tokenized_query)
        skills_scores: NDArray[np.float64] = skills_bm25.get_scores(tokenized_query)
        experience_scores: NDArray[np.float64] = experience_bm25.get_scores(tokenized_query)

        # Weighted combination
        combined_scores = (
            scoring_weights.title_weight * title_scores
            + scoring_weights.skills_weight * skills_scores
            + scoring_weights.experience_weight * experience_scores
        )

        # Convert to ranks (1-indexed, lower is better)
        sorted_indices = np.argsort(combined_scores)[::-1]
        ranks = [0] * len(combined_scores)
        for rank, idx in enumerate(sorted_indices, 1):
            ranks[idx] = rank

        return ranks

    def _semantic_rank(self, documents: list[str], query: str) -> list[int]:
        """Compute semantic similarity ranks (1-indexed, lower is better)."""
        # Embed documents (as queries since they're Work Units being searched)
        doc_embeddings = self.embedding_service.embed_batch(documents, is_query=True)

        # Embed JD (as passage - the document being matched against)
        query_embedding = self.embedding_service.embed_passage(query)

        # Compute cosine similarity
        scores = self._cosine_similarity(doc_embeddings, query_embedding)

        # Compute ranks (1-indexed, lower rank = better match)
        sorted_indices = np.argsort(scores)[::-1]
        ranks = [0] * len(scores)
        for rank, idx in enumerate(sorted_indices, 1):
            ranks[idx] = rank

        return ranks

    def _semantic_rank_sectioned(
        self,
        work_units: list[dict[str, Any]],
        jd: JobDescription,
        scoring_weights: ScoringWeights,
    ) -> list[int]:
        """Semantic ranking with section-level matching (Story 7.11).

        Computes cross-section similarity:
        - Work unit outcome ↔ JD requirements
        - Work unit actions ↔ JD requirements
        - Work unit skills ↔ JD skills
        - Work unit title ↔ JD full text

        Args:
            work_units: List of Work Unit dictionaries.
            jd: Parsed JobDescription.
            scoring_weights: Weights configuration.

        Returns:
            List of ranks (1-indexed, lower is better).
        """
        # Embed JD sections
        jd_sections = self.embedding_service.embed_jd_sections(jd)
        jd_requirements = jd_sections.get("requirements", jd_sections.get("full"))
        jd_skills = jd_sections.get("skills", jd_sections.get("full"))
        jd_full = jd_sections.get("full")

        # Fallback if no requirements embedding
        if jd_requirements is None:
            jd_requirements = jd_full
        if jd_skills is None:
            jd_skills = jd_full

        scores: list[float] = []

        for wu in work_units:
            wu_sections = self.embedding_service.embed_work_unit_sections(wu)

            # Cross-section matching
            outcome_score = 0.0
            actions_score = 0.0
            skills_score = 0.0
            title_score = 0.0

            # Outcome ↔ Requirements
            if "outcome" in wu_sections and jd_requirements is not None:
                outcome_score = self._cosine_sim_single(wu_sections["outcome"], jd_requirements)

            # Actions ↔ Requirements
            if "actions" in wu_sections and jd_requirements is not None:
                actions_score = self._cosine_sim_single(wu_sections["actions"], jd_requirements)

            # Skills ↔ JD Skills
            if "skills" in wu_sections and jd_skills is not None:
                skills_score = self._cosine_sim_single(wu_sections["skills"], jd_skills)

            # Title ↔ Full JD
            if "title" in wu_sections and jd_full is not None:
                title_score = self._cosine_sim_single(wu_sections["title"], jd_full)

            # Weighted aggregation
            weighted_score = (
                scoring_weights.section_outcome_weight * outcome_score
                + scoring_weights.section_actions_weight * actions_score
                + scoring_weights.section_skills_weight * skills_score
                + scoring_weights.section_title_weight * title_score
            )
            scores.append(weighted_score)

        # Convert to ranks (1-indexed, lower is better)
        sorted_indices = np.argsort(scores)[::-1]
        ranks = [0] * len(scores)
        for rank, idx in enumerate(sorted_indices, 1):
            ranks[idx] = rank

        return ranks

    def _cosine_sim_single(
        self,
        vec1: NDArray[np.float32],
        vec2: NDArray[np.float32],
    ) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            vec1: First embedding vector.
            vec2: Second embedding vector.

        Returns:
            Cosine similarity (0.0 to 1.0, normalized from [-1, 1]).
        """
        # Normalize vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 < 1e-9 or norm2 < 1e-9:
            return 0.0

        similarity = float(np.dot(vec1, vec2) / (norm1 * norm2))

        # Normalize from [-1, 1] to [0, 1]
        return (similarity + 1.0) / 2.0

    def _cosine_similarity(
        self,
        doc_embeddings: NDArray[np.float32],
        query_embedding: NDArray[np.float32],
    ) -> list[float]:
        """Compute cosine similarity between documents and query."""
        # Handle empty case
        if doc_embeddings.size == 0:
            return []

        # Normalize document embeddings
        doc_norms = np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
        doc_normalized = doc_embeddings / (doc_norms + 1e-9)

        # Normalize query embedding
        query_norm = np.linalg.norm(query_embedding)
        query_normalized = query_embedding / (query_norm + 1e-9)

        # Dot product gives cosine similarity (vectors are normalized)
        similarities: NDArray[np.float64] = doc_normalized @ query_normalized

        result: list[float] = similarities.tolist()
        return result

    def _rrf_fusion(
        self,
        bm25_ranks: list[int],
        semantic_ranks: list[int],
        scoring_weights: ScoringWeights | None = None,
    ) -> list[float]:
        """Combine rankings using Reciprocal Rank Fusion.

        RRF_Score(d) = Σ (weight_i / (k + rank_i(d)))

        Where:
            k = RRF_K constant (60)
            rank_i(d) = rank of document d in ranking method i
            weight_i = weight for ranking method i (from scoring_weights)

        Args:
            bm25_ranks: BM25 ranks for each document.
            semantic_ranks: Semantic similarity ranks for each document.
            scoring_weights: Optional weights for BM25/semantic balance.

        Returns:
            List of RRF fusion scores.
        """
        # Get weights (default to 1.0 if not provided)
        bm25_weight = 1.0
        semantic_weight = 1.0
        if scoring_weights is not None:
            bm25_weight = scoring_weights.bm25_weight
            semantic_weight = scoring_weights.semantic_weight

        scores: list[float] = []
        for i in range(len(bm25_ranks)):
            bm25_score = bm25_weight / (self.RRF_K + bm25_ranks[i])
            semantic_score = semantic_weight / (self.RRF_K + semantic_ranks[i])
            rrf_score = bm25_score + semantic_score
            scores.append(rrf_score)
        return scores

    def _extract_match_reasons(
        self,
        work_unit: dict[str, Any],
        jd: JobDescription,
        seniority_score: float = 1.0,
        impact_score: float = 0.5,
        scoring_weights: ScoringWeights | None = None,
    ) -> list[str]:
        """Extract reasons why this Work Unit matched.

        Returns up to 3 reasons explaining the match, with field indication.
        Field types: Title match, Skills match, Experience match, Seniority, Impact.
        """
        reasons: list[str] = []

        # Check for title matches (highest priority) - AC #4
        title_text = extract_title_text(work_unit).lower()
        title_keyword_matches = [kw for kw in jd.keywords[:10] if kw.lower() in title_text]
        if title_keyword_matches:
            reasons.append(f"Title match: {', '.join(title_keyword_matches[:2])}")

        # Check for skill/tag matches - AC #4
        skills_text = extract_skills_text(work_unit).lower()
        matching_skills = [skill for skill in jd.skills if skill.lower() in skills_text]
        if matching_skills:
            reasons.append(f"Skills match: {', '.join(matching_skills[:3])}")

        # Check for experience text matches (body) - AC #4
        experience_text = extract_experience_text(work_unit).lower()
        experience_keyword_matches = [
            kw
            for kw in jd.keywords[:10]
            if kw.lower() in experience_text and kw.lower() not in title_text
        ]
        if experience_keyword_matches:
            reasons.append(f"Experience match: {', '.join(experience_keyword_matches[:3])}")

        # Seniority alignment reason (Story 7.12)
        if scoring_weights and scoring_weights.use_seniority_matching:
            if seniority_score >= 0.9:
                reasons.append("Seniority level matches JD requirements")
            elif seniority_score >= 0.7:
                reasons.append("Seniority level close to JD requirements")
            elif seniority_score < 0.5:
                reasons.append(f"Seniority mismatch (score: {seniority_score:.0%})")

        # Impact alignment reason (Story 7.13 - AC6)
        impact_reason = self._generate_impact_reason(work_unit, jd, impact_score, scoring_weights)
        if impact_reason:
            reasons.append(impact_reason)

        # Limit to max reasons (prevents UI clutter)
        if reasons:
            return reasons[: self._MAX_MATCH_REASONS]

        # Fallback if no explicit matches found
        return ["Semantic similarity"]

    def _calculate_recency_score(
        self,
        work_unit: dict[str, Any],
        scoring_weights: ScoringWeights | None,
    ) -> float:
        """Calculate recency decay score for a work unit.

        Uses exponential decay with configurable half-life.
        Current positions (time_ended=None) receive 100% weight.

        Args:
            work_unit: Work Unit dictionary.
            scoring_weights: Scoring weights with recency config.

        Returns:
            Recency score between 0.0 and 1.0.
        """
        # No decay if disabled
        if scoring_weights is None or scoring_weights.recency_half_life is None:
            return 1.0

        # Get end date (None means current/ongoing)
        time_ended = work_unit.get("time_ended")
        if time_ended is None:
            return 1.0  # Current position gets full weight

        # Parse date if string
        if isinstance(time_ended, str):
            # Handle YYYY-MM-DD or YYYY-MM format
            try:
                if len(time_ended) == 10:  # YYYY-MM-DD
                    end_date = date.fromisoformat(time_ended)
                else:  # YYYY-MM
                    end_date = date.fromisoformat(f"{time_ended}-01")
            except ValueError:
                return 1.0  # Invalid date, default to full weight
        elif isinstance(time_ended, date):
            end_date = time_ended
        else:
            return 1.0  # Unknown format, default to full weight

        # Calculate years ago
        today = date.today()
        years_ago = (today - end_date).days / 365.25

        # Handle future dates (shouldn't happen, but be safe)
        if years_ago < 0:
            return 1.0

        # Exponential decay: score = e^(-λ × years_ago)
        # Where λ = ln(2) / half_life
        half_life = scoring_weights.recency_half_life
        decay_constant = math.log(2) / half_life
        recency_score = math.exp(-decay_constant * years_ago)

        return recency_score

    def _calculate_seniority_score(
        self,
        work_unit: dict[str, Any],
        jd: JobDescription,
        scoring_weights: ScoringWeights | None,
        positions: dict[str, Any] | None = None,
    ) -> float:
        """Calculate seniority alignment score for a work unit.

        Returns 1.0 if seniority matching is disabled.

        Args:
            work_unit: Work Unit dictionary.
            jd: JobDescription with experience_level.
            scoring_weights: Scoring weights with seniority config.
            positions: Optional dict of position_id -> Position for scope lookup.

        Returns:
            Seniority alignment score between 0.0 and 1.0.
        """
        # No seniority matching if disabled or no weights
        if scoring_weights is None or not scoring_weights.use_seniority_matching:
            return 1.0

        # Create a minimal WorkUnit for inference
        from resume_as_code.models.work_unit import WorkUnit

        try:
            # Reconstruct WorkUnit from dict to use seniority_level field
            wu_model = WorkUnit.model_validate(work_unit)
        except Exception:
            # Fall back to title-only inference if validation fails
            from resume_as_code.services.seniority_inference import (
                infer_seniority_from_title,
            )

            wu_level = infer_seniority_from_title(work_unit.get("title", ""))
            return calculate_seniority_alignment(wu_level, jd.experience_level)

        # Look up position from positions dict if available
        position = None
        if positions and wu_model.position_id:
            position = positions.get(wu_model.position_id)

        # Infer work unit seniority
        wu_level = infer_seniority(wu_model, position)

        # Calculate alignment
        return calculate_seniority_alignment(wu_level, jd.experience_level)

    def _calculate_impact_score(
        self,
        work_unit: dict[str, Any],
        jd: JobDescription,
        scoring_weights: ScoringWeights | None,
    ) -> float:
        """Calculate impact alignment score for a work unit (Story 7.13).

        Returns 0.5 (neutral) if impact matching is disabled.

        Args:
            work_unit: Work Unit dictionary.
            jd: JobDescription with title for role inference.
            scoring_weights: Scoring weights with impact config.

        Returns:
            Impact alignment score between 0.0 and 1.0.
        """
        # No impact matching if disabled or no weights
        if scoring_weights is None or not scoring_weights.use_impact_matching:
            return 0.5

        # Build outcome text from all outcome fields
        outcome = work_unit.get("outcome", {})
        if isinstance(outcome, dict):
            outcome_parts = [
                outcome.get("result", ""),
                outcome.get("quantified_impact", ""),
                outcome.get("business_value", ""),
            ]
        else:
            outcome_parts = [str(outcome) if outcome else ""]

        outcome_text = " ".join(filter(None, outcome_parts))

        # Classify work unit impacts
        impacts = classify_impact(outcome_text)

        # Check for quantification
        is_quantified = has_quantified_impact(outcome_text)

        # Infer role type from JD
        role_type = infer_role_type(jd.title)

        # Calculate alignment with configurable quantified boost
        return calculate_impact_alignment(
            impacts,
            role_type,
            is_quantified,
            quantified_boost=scoring_weights.quantified_boost,
        )

    def _generate_impact_reason(
        self,
        work_unit: dict[str, Any],
        jd: JobDescription,
        impact_score: float,
        scoring_weights: ScoringWeights | None,
    ) -> str | None:
        """Generate human-readable impact alignment reason (AC6).

        Args:
            work_unit: Work Unit dictionary.
            jd: JobDescription with title for role inference.
            impact_score: Calculated impact alignment score.
            scoring_weights: Scoring weights with impact config.

        Returns:
            Human-readable reason string, or None if not significant.
        """
        if scoring_weights is None or not scoring_weights.use_impact_matching:
            return None

        # Build outcome text
        outcome = work_unit.get("outcome", {})
        if isinstance(outcome, dict):
            outcome_parts = [
                outcome.get("result", ""),
                outcome.get("quantified_impact", ""),
                outcome.get("business_value", ""),
            ]
        else:
            outcome_parts = [str(outcome) if outcome else ""]

        outcome_text = " ".join(filter(None, outcome_parts))

        impacts = classify_impact(outcome_text)
        role_type = infer_role_type(jd.title)

        if not impacts:
            return None

        top_impact = impacts[0].category.capitalize()
        role_display = role_type.capitalize()

        if impact_score >= 0.7:
            return f"{top_impact} impact aligns with {role_display} role"
        elif impact_score >= 0.4:
            return f"{top_impact} impact partially relevant to {role_display} role"
        else:
            return None  # Low alignment - don't highlight

    def _blend_scores(
        self,
        relevance_scores: list[float],
        recency_scores: list[float],
        seniority_scores: list[float],
        impact_scores: list[float],
        scoring_weights: ScoringWeights | None,
    ) -> list[float]:
        """Blend relevance, recency, seniority, and impact scores.

        Formula: final = relevance × relevance_blend
                       + recency × recency_blend
                       + seniority × seniority_blend
                       + impact × impact_blend

        Where: relevance_blend = 1.0 - recency_blend - seniority_blend - impact_blend

        Args:
            relevance_scores: Normalized relevance scores (0-1).
            recency_scores: Recency decay scores (0-1).
            seniority_scores: Seniority alignment scores (0-1).
            impact_scores: Impact alignment scores (0-1).
            scoring_weights: Weights configuration.

        Returns:
            Blended final scores.
        """
        if scoring_weights is None:
            return relevance_scores

        recency_blend = scoring_weights.recency_blend
        seniority_blend = scoring_weights.seniority_blend
        impact_blend = scoring_weights.impact_blend
        relevance_blend = 1.0 - recency_blend - seniority_blend - impact_blend

        return [
            (relevance_blend * rel)
            + (recency_blend * rec)
            + (seniority_blend * sen)
            + (impact_blend * imp)
            for rel, rec, sen, imp in zip(
                relevance_scores, recency_scores, seniority_scores, impact_scores, strict=True
            )
        ]
