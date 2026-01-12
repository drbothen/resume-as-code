"""Hybrid BM25 + Semantic ranker with RRF fusion."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]

from resume_as_code.utils.work_unit_text import extract_work_unit_text

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
    """

    RRF_K = 60  # RRF constant (standard value)

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
    ) -> RankingOutput:
        """Rank Work Units against a job description.

        Args:
            work_units: List of Work Unit dictionaries.
            jd: Parsed JobDescription.
            top_k: Number of top results to return.
            scoring_weights: Optional weights for BM25/semantic balance.

        Returns:
            RankingOutput with sorted results.
        """
        if not work_units:
            return RankingOutput(results=[], jd_keywords=jd.keywords)

        # Extract text from Work Units
        wu_texts = [extract_work_unit_text(wu) for wu in work_units]
        wu_ids = [wu.get("id", f"wu-{i}") for i, wu in enumerate(work_units)]

        # BM25 ranking
        bm25_ranks = self._bm25_rank(wu_texts, jd.text_for_ranking)

        # Semantic ranking
        semantic_ranks = self._semantic_rank(wu_texts, jd.text_for_ranking)

        # RRF fusion with optional weights (AC: #3)
        rrf_scores = self._rrf_fusion(bm25_ranks, semantic_ranks, scoring_weights)

        # Sort by RRF score (higher is better), then by ID for determinism
        sorted_indices = sorted(
            range(len(work_units)),
            key=lambda i: (rrf_scores[i], wu_ids[i]),
            reverse=True,
        )

        # Normalize scores to 0.0-1.0
        max_score = max(rrf_scores) if rrf_scores else 1.0
        min_score = min(rrf_scores) if rrf_scores else 0.0

        # Handle edge case: single work unit or all same scores
        if max_score == min_score:
            normalized_scores = [1.0] * len(rrf_scores)
        else:
            normalized_scores = [(s - min_score) / (max_score - min_score) for s in rrf_scores]

        # Build results - return top_k * 2 for exclusion display
        results: list[RankingResult] = []
        for idx in sorted_indices[: top_k * 2]:
            match_reasons = self._extract_match_reasons(work_units[idx], jd)
            results.append(
                RankingResult(
                    work_unit_id=wu_ids[idx],
                    work_unit=work_units[idx],
                    score=normalized_scores[idx],
                    bm25_rank=bm25_ranks[idx],
                    semantic_rank=semantic_ranks[idx],
                    match_reasons=match_reasons,
                )
            )

        return RankingOutput(results=results, jd_keywords=jd.keywords)

    def _bm25_rank(self, documents: list[str], query: str) -> list[int]:
        """Compute BM25 ranks (1-indexed, lower is better)."""
        # Tokenize documents and query
        tokenized_docs = [doc.lower().split() for doc in documents]
        tokenized_query = query.lower().split()

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

    def _extract_match_reasons(self, work_unit: dict[str, Any], jd: JobDescription) -> list[str]:
        """Extract reasons why this Work Unit matched.

        Returns up to 3 reasons explaining the match.
        """
        reasons: list[str] = []
        wu_text = extract_work_unit_text(work_unit).lower()

        # Check for skill matches
        matching_skills = [skill for skill in jd.skills if skill.lower() in wu_text]
        if matching_skills:
            reasons.append(f"Skills: {', '.join(matching_skills[:3])}")

        # Check for keyword matches
        matching_keywords = [kw for kw in jd.keywords[:10] if kw.lower() in wu_text]
        if matching_keywords:
            reasons.append(f"Keywords: {', '.join(matching_keywords[:3])}")

        # Check for tag matches against JD skills
        wu_tags = {t.lower() for t in work_unit.get("tags", [])}
        jd_skills_set = {s.lower() for s in jd.skills}
        tag_matches = wu_tags & jd_skills_set
        if tag_matches:
            reasons.append(f"Tags match: {', '.join(list(tag_matches)[:2])}")

        # Limit to top 3 reasons (AC4: 3-5 per Work Unit)
        if reasons:
            return reasons[:3]

        # Fallback if no explicit matches found
        return ["Semantic similarity"]
