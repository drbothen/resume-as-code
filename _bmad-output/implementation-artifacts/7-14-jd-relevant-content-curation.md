# Story 7.14: JD-Relevant Content Curation

**Epic:** Epic 7 - Schema & Data Model Refactoring
**Story Points:** 5
**Priority:** P2
**Status:** Complete

---

## User Story

As a **job seeker**,
I want **my career highlights, certifications, and other sections intelligently selected based on JD relevance**,
So that **I can maintain a comprehensive profile while the algorithm surfaces the most appropriate items for each application**.

---

## Background

**Research Basis:** (2024-2025 resume research, 18.4M resumes analyzed)

Cognitive load research confirms working memory limit of 5-7 items before fatigue:
- **Career highlights/Summary**: 3-5 bullet points maximum (research: 2-4 sentences)
- **Bullets per position**: 4-6 recent roles, 2-3 older positions
- **Skills**: 6-10 optimal (median 8-9), up to 12-15 mid-career, 15-20 senior
- **Certifications**: 3-5 most relevant to JD
- **Board roles**: 2-3 unless executive-level position

**Key insight:** Only 10% of resumes include quantified results despite 78% of recruiters citing this as top differentiator. Prioritizing quantified achievements provides massive competitive advantage.

**Existing Infrastructure:**
- `career_highlights`: Stored in `.resume.yaml`, managed by `HighlightService` (`services/highlight_service.py`)
- `Certification`: Model in `models/certification.py` with `display` field
- `BoardRole`: Model in `models/board_role.py` with `display` field
- `EmbeddingService`: Available for semantic matching (`services/embedder.py`)

---

## Acceptance Criteria

### AC1: Career highlights curation
**Given** I have 8 career highlights configured
**When** generating a resume for a specific JD
**Then** the 4 most JD-relevant highlights are selected
**And** selection is based on keyword/semantic matching against JD

### AC2: Certification curation with skill matching
**Given** I have 10 certifications configured
**When** generating a resume for a JD requiring "AWS" and "Kubernetes"
**Then** AWS and Kubernetes certifications rank highest
**And** output limited to configured max (default 5)

### AC3: Board role curation (context-aware)
**Given** I have 6 board roles configured
**When** generating a resume for a non-executive role
**Then** 2-3 most relevant board roles are selected
**And** executive JDs show more board experience (up to 5)

### AC4: Position bullets curation with recency
**Given** a position from 2 years ago with 8 work unit bullets
**When** generating resume output
**Then** only the 4-6 most JD-relevant bullets are selected

**Given** a position from 7 years ago with 6 work unit bullets
**When** generating resume output
**Then** only the 2-3 most JD-relevant bullets are selected

### AC5: Quantified achievement boost
**Given** work units with quantified outcomes ("saved $2M", "40% faster")
**When** selecting bullets
**Then** quantified achievements are boosted 25% in scoring
**And** they are prioritized for inclusion

### AC6: Force-include with priority field
**Given** I set `priority: always` on a certification
**When** curation runs
**Then** it's always included regardless of JD relevance
**And** remaining slots filled with highest-scoring items

### AC7: Plan command shows curation
**Given** `resume plan --jd job.txt` runs
**When** displaying results
**Then** shows which highlights/certs/roles were selected
**And** shows relevance scores for transparency

### AC8: Configurable limits
**Given** curation config in `.resume.yaml`
**When** limits are customized
**Then** curation respects configured maximums
**And** defaults to research-backed limits if not specified

---

## Technical Design

### 1. CurationResult Generic Type

```python
# src/resume_as_code/services/content_curator.py
"""Content curation service for JD-relevant resume sections."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Generic, TypeVar

import numpy as np

if TYPE_CHECKING:
    from resume_as_code.models.board_role import BoardRole
    from resume_as_code.models.certification import Certification
    from resume_as_code.models.job_description import JobDescription
    from resume_as_code.models.position import Position
    from resume_as_code.models.work_unit import WorkUnit
    from resume_as_code.services.embedder import EmbeddingService


T = TypeVar("T")


@dataclass
class CurationResult(Generic[T]):
    """Result of content curation for a section.

    Attributes:
        selected: Items selected for inclusion (ordered by relevance)
        excluded: Items not selected (ordered by relevance)
        scores: Mapping of item identifier to relevance score (0.0 to 1.0)
        reason: Human-readable explanation of curation decision
    """
    selected: list[T]
    excluded: list[T]
    scores: dict[str, float] = field(default_factory=dict)
    reason: str = ""
```

### 2. Research-Backed Limits

```python
# Research-backed section limits (2024-2025 resume studies)
DEFAULT_SECTION_LIMITS = {
    "career_highlights": 4,       # Research: 3-5 optimal
    "certifications": 5,          # Research: 3-5 most relevant
    "board_roles": 3,             # 2-3 unless executive role
    "board_roles_executive": 5,   # Executive roles show more board experience
    "publications": 3,            # Keep focused
    "skills": 10,                 # Research: 6-10 optimal (median 8-9)
}

# Bullets per position based on recency
BULLETS_PER_POSITION = {
    "recent": {"years": 3, "min": 4, "max": 6},    # 0-3 years: 4-6 bullets
    "mid": {"years": 7, "min": 3, "max": 4},       # 3-7 years: 3-4 bullets
    "older": {"years": float("inf"), "min": 2, "max": 3},  # 7+ years: 2-3 bullets
}

# Scoring weights
QUANTIFIED_BOOST = 1.25  # 25% boost for quantified achievements
```

### 3. ContentCurator Service

```python
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
        limits: dict[str, int] | None = None,
        quantified_boost: float = QUANTIFIED_BOOST,
    ):
        """Initialize the content curator.

        Args:
            embedder: Embedding service for semantic matching
            limits: Custom section limits (uses defaults if not specified)
            quantified_boost: Multiplier for quantified achievements
        """
        self.embedder = embedder
        self.limits = {**DEFAULT_SECTION_LIMITS, **(limits or {})}
        self.quantified_boost = quantified_boost

    def curate_highlights(
        self,
        highlights: list[str],
        jd: JobDescription,
        max_count: int | None = None,
    ) -> CurationResult[str]:
        """Select most JD-relevant career highlights.

        Args:
            highlights: All career highlights to consider
            jd: Job description for matching
            max_count: Override default limit

        Returns:
            CurationResult with selected/excluded highlights and scores
        """
        if not highlights:
            return CurationResult(selected=[], excluded=[], reason="No highlights configured")

        max_count = max_count or self.limits["career_highlights"]

        # Pre-compute JD embedding
        jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)
        jd_keywords = set(kw.lower() for kw in jd.keywords)

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

        selected = [highlights[i] for i in ranked_indices[:max_count]]
        excluded = [highlights[i] for i in ranked_indices[max_count:]]

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
            certifications: All certifications to consider
            jd: Job description for matching
            max_count: Override default limit

        Returns:
            CurationResult with selected/excluded certifications
        """
        if not certifications:
            return CurationResult(selected=[], excluded=[], reason="No certifications configured")

        max_count = max_count or self.limits["certifications"]

        # Separate priority items
        always_include = [c for c in certifications if getattr(c, "priority", None) == "always"]
        candidates = [c for c in certifications if c not in always_include]

        # Pre-compute JD data
        jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)
        jd_skills = set(s.lower() for s in jd.skills)

        scores: dict[str, float] = {}

        for cert in candidates:
            # Direct skill match (50% weight) - cert name/issuer contains JD skill
            skill_match_count = sum(
                1 for skill in jd_skills
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

            scores[cert.name] = (
                skill_score * 0.5 +
                semantic_score * 0.3 +
                recency_score * 0.2
            )

        # Rank candidates by score
        ranked = sorted(candidates, key=lambda c: scores.get(c.name, 0), reverse=True)

        # Fill remaining slots after always-include
        remaining_slots = max(0, max_count - len(always_include))
        selected = always_include + ranked[:remaining_slots]
        excluded = ranked[remaining_slots:]

        return CurationResult(
            selected=selected,
            excluded=excluded,
            scores=scores,
            reason=f"Selected {len(selected)} certifications ({len(always_include)} priority + {len(selected) - len(always_include)} by relevance)",
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
            board_roles: All board roles to consider
            jd: Job description for matching
            is_executive_role: Whether JD is for executive position
            max_count: Override default limit

        Returns:
            CurationResult with selected/excluded board roles
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
            position: The position these work units belong to
            work_units: Work units to curate
            jd: Job description for matching

        Returns:
            CurationResult with selected/excluded work units
        """
        if not work_units:
            return CurationResult(selected=[], excluded=[], reason="No work units for position")

        # Determine bullet limits based on position age
        years_ago = self._position_age_years(position)
        bullet_config = self._get_bullet_config(years_ago)
        max_bullets = bullet_config["max"]

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
            reason=f"Selected {len(selected)} of {len(work_units)} bullets for {years_ago:.0f}-year-old position (limit: {max_bullets})",
        )

    # --- Helper Methods ---

    def _cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a = np.array(vec_a)
        b = np.array(vec_b)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

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

    def _get_bullet_config(self, years_ago: float) -> dict:
        """Get bullet limits for position age."""
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
        if hasattr(wu, "tags"):
            parts.append(" ".join(wu.tags))
        return " ".join(filter(None, parts))

    def _has_quantified_impact(self, wu: WorkUnit) -> bool:
        """Check if work unit has quantified metrics."""
        import re
        outcome = wu.outcome
        text = f"{outcome.result} {outcome.quantified_impact or ''}"
        patterns = [
            r'\d+%',                      # Percentages
            r'\$[\d,]+[KMB]?',            # Dollar amounts
            r'\d+x\b',                    # Multipliers
            r'\d+\s*(?:hours?|days?|weeks?|months?)',  # Time metrics
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
```

### 4. Priority Field for Models

Add `priority` field to Certification and BoardRole:

```python
# src/resume_as_code/models/certification.py - add field
from typing import Literal

class Certification(BaseModel):
    # ... existing fields ...

    priority: Literal["always", "normal", "low"] | None = Field(
        default=None,
        description="Curation priority: 'always' forces inclusion regardless of JD relevance"
    )


# src/resume_as_code/models/board_role.py - add field
class BoardRole(BaseModel):
    # ... existing fields ...

    priority: Literal["always", "normal", "low"] | None = Field(
        default=None,
        description="Curation priority: 'always' forces inclusion regardless of JD relevance"
    )
```

### 5. CurationConfig

```python
# src/resume_as_code/models/config.py - add CurationConfig

class BulletsPerPositionConfig(BaseModel):
    """Bullet limits based on position age."""
    recent_years: int = Field(default=3, description="Years considered 'recent'")
    recent_max: int = Field(default=6, description="Max bullets for recent positions")
    mid_years: int = Field(default=7, description="Years considered 'mid-career'")
    mid_max: int = Field(default=4, description="Max bullets for mid positions")
    older_max: int = Field(default=3, description="Max bullets for older positions")


class CurationConfig(BaseModel):
    """Configuration for content curation."""

    career_highlights_max: int = Field(default=4, ge=1, le=10)
    certifications_max: int = Field(default=5, ge=1, le=15)
    board_roles_max: int = Field(default=3, ge=1, le=10)
    board_roles_executive_max: int = Field(default=5, ge=1, le=10)
    publications_max: int = Field(default=3, ge=1, le=10)
    skills_max: int = Field(default=10, ge=1, le=30)

    bullets_per_position: BulletsPerPositionConfig = Field(
        default_factory=BulletsPerPositionConfig
    )

    quantified_boost: float = Field(
        default=1.25,
        ge=1.0,
        le=2.0,
        description="Score multiplier for quantified achievements"
    )

    min_relevance_score: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Minimum score for inclusion (below this, item is excluded even if slots available)"
    )


# Add to ResumeConfig
class ResumeConfig(BaseModel):
    # ... existing fields ...

    curation: CurationConfig = Field(default_factory=CurationConfig)
```

### 6. Plan Command Integration

Update plan command to display curation decisions:

```python
# src/resume_as_code/commands/plan.py - add curation display

@dataclass
class CurationPreview:
    """Preview of curation decisions for plan display."""
    highlights: CurationResult[str] | None
    certifications: CurationResult[Certification] | None
    board_roles: CurationResult[BoardRole] | None


def _get_curation_preview(
    config: ResumeConfig,
    jd: JobDescription,
    embedder: EmbeddingService,
) -> CurationPreview:
    """Generate curation preview for plan display."""
    curator = ContentCurator(
        embedder=embedder,
        limits={
            "career_highlights": config.curation.career_highlights_max,
            "certifications": config.curation.certifications_max,
            "board_roles": config.curation.board_roles_max,
            "board_roles_executive": config.curation.board_roles_executive_max,
        },
        quantified_boost=config.curation.quantified_boost,
    )

    # Load data
    highlights = config.career_highlights
    certs = CertificationService().load_certifications()
    board_roles = BoardRoleService().load_board_roles()

    # Determine if executive role
    is_executive = jd.experience_level in [ExperienceLevel.EXECUTIVE, ExperienceLevel.PRINCIPAL]

    return CurationPreview(
        highlights=curator.curate_highlights(highlights, jd) if highlights else None,
        certifications=curator.curate_certifications(certs, jd) if certs else None,
        board_roles=curator.curate_board_roles(board_roles, jd, is_executive) if board_roles else None,
    )


def _display_curation_preview(preview: CurationPreview) -> None:
    """Display curation decisions in plan output."""
    console = Console()

    if preview.highlights and preview.highlights.selected:
        console.print("\n[bold]Career Highlights (curated):[/bold]")
        for i, h in enumerate(preview.highlights.selected, 1):
            score = preview.highlights.scores.get(f"highlight_{i-1}", 0)
            console.print(f"  {i}. {h[:60]}... [dim]({score:.0%})[/dim]")
        if preview.highlights.excluded:
            console.print(f"  [dim]({len(preview.highlights.excluded)} excluded)[/dim]")

    if preview.certifications and preview.certifications.selected:
        console.print("\n[bold]Certifications (curated):[/bold]")
        for cert in preview.certifications.selected:
            score = preview.certifications.scores.get(cert.name, 0)
            priority_tag = " [green]ALWAYS[/green]" if getattr(cert, "priority", None) == "always" else ""
            console.print(f"  - {cert.name}{priority_tag} [dim]({score:.0%})[/dim]")
        if preview.certifications.excluded:
            console.print(f"  [dim]({len(preview.certifications.excluded)} excluded)[/dim]")

    if preview.board_roles and preview.board_roles.selected:
        console.print("\n[bold]Board Roles (curated):[/bold]")
        for role in preview.board_roles.selected:
            score = preview.board_roles.scores.get(role.organization, 0)
            console.print(f"  - {role.organization}: {role.role} [dim]({score:.0%})[/dim]")
        if preview.board_roles.excluded:
            console.print(f"  [dim]({len(preview.board_roles.excluded)} excluded)[/dim]")
```

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/resume_as_code/services/content_curator.py` | Create | ContentCurator service |
| `src/resume_as_code/models/config.py` | Modify | Add CurationConfig, BulletsPerPositionConfig |
| `src/resume_as_code/models/certification.py` | Modify | Add `priority` field |
| `src/resume_as_code/models/board_role.py` | Modify | Add `priority` field |
| `src/resume_as_code/commands/plan.py` | Modify | Integrate curation preview display |
| `src/resume_as_code/models/resume.py` | Modify | Use curated content in resume building |
| `tests/unit/services/test_content_curator.py` | Create | Unit tests for curation |

---

## Test Cases

### Unit Tests: Content Curator

```python
# tests/unit/services/test_content_curator.py
import pytest
from unittest.mock import MagicMock
from resume_as_code.services.content_curator import ContentCurator, CurationResult


class TestCurateHighlights:
    """Test career highlights curation."""

    def test_selects_top_n_by_relevance(self, mock_embedder):
        curator = ContentCurator(embedder=mock_embedder)
        highlights = [
            "Led cloud migration saving $2M annually",
            "Managed team operations",
            "Implemented Kubernetes at scale",
            "Attended meetings",
            "Built AWS infrastructure",
        ]

        # Mock JD focused on cloud/AWS
        jd = MagicMock()
        jd.text_for_ranking = "AWS cloud engineer Kubernetes"
        jd.keywords = ["aws", "cloud", "kubernetes"]

        result = curator.curate_highlights(highlights, jd, max_count=3)

        assert len(result.selected) == 3
        assert len(result.excluded) == 2
        # Cloud-related highlights should be selected
        assert any("cloud" in h.lower() or "aws" in h.lower() for h in result.selected)

    def test_empty_highlights_returns_empty_result(self, mock_embedder):
        curator = ContentCurator(embedder=mock_embedder)
        result = curator.curate_highlights([], MagicMock())

        assert result.selected == []
        assert result.excluded == []


class TestCurateCertifications:
    """Test certification curation."""

    def test_priority_always_included_first(self, mock_embedder):
        curator = ContentCurator(embedder=mock_embedder)

        # Create certs with one marked as always
        cert_always = MagicMock()
        cert_always.name = "Unrelated Cert"
        cert_always.priority = "always"

        cert_relevant = MagicMock()
        cert_relevant.name = "AWS Solutions Architect"
        cert_relevant.priority = None
        cert_relevant.issuer = "Amazon"

        jd = MagicMock()
        jd.text_for_ranking = "AWS cloud infrastructure"
        jd.skills = ["aws", "cloud"]

        result = curator.curate_certifications([cert_always, cert_relevant], jd, max_count=2)

        # Always-include cert should be in selected
        assert cert_always in result.selected

    def test_skill_match_boosts_score(self, mock_embedder):
        curator = ContentCurator(embedder=mock_embedder)

        cert_match = MagicMock()
        cert_match.name = "AWS Solutions Architect"
        cert_match.issuer = "Amazon"
        cert_match.priority = None

        cert_no_match = MagicMock()
        cert_no_match.name = "Generic Management"
        cert_no_match.issuer = "Unknown"
        cert_no_match.priority = None

        jd = MagicMock()
        jd.text_for_ranking = "AWS cloud"
        jd.skills = ["aws"]

        result = curator.curate_certifications([cert_no_match, cert_match], jd, max_count=1)

        # AWS cert should be selected due to skill match
        assert cert_match in result.selected


class TestCuratePositionBullets:
    """Test position bullets curation with recency."""

    def test_recent_position_gets_more_bullets(self, mock_embedder):
        curator = ContentCurator(embedder=mock_embedder)

        # Recent position (current)
        position = MagicMock()
        position.end_date = None  # Current

        work_units = [MagicMock(id=f"wu_{i}") for i in range(8)]
        for wu in work_units:
            wu.title = "Task"
            wu.outcome = MagicMock(result="Result", quantified_impact=None, business_value=None)
            wu.actions = ["Action"]
            wu.tags = []

        jd = MagicMock()
        jd.text_for_ranking = "Software engineer"

        result = curator.curate_position_bullets(position, work_units, jd)

        # Recent position should allow 4-6 bullets
        assert 4 <= len(result.selected) <= 6

    def test_old_position_gets_fewer_bullets(self, mock_embedder):
        curator = ContentCurator(embedder=mock_embedder)

        # Old position (8 years ago)
        position = MagicMock()
        position.end_date = "2018-01"  # ~8 years ago

        work_units = [MagicMock(id=f"wu_{i}") for i in range(6)]
        for wu in work_units:
            wu.title = "Task"
            wu.outcome = MagicMock(result="Result", quantified_impact=None, business_value=None)
            wu.actions = ["Action"]
            wu.tags = []

        jd = MagicMock()
        jd.text_for_ranking = "Software engineer"

        result = curator.curate_position_bullets(position, work_units, jd)

        # Old position should allow only 2-3 bullets
        assert 2 <= len(result.selected) <= 3

    def test_quantified_achievements_boosted(self, mock_embedder):
        curator = ContentCurator(embedder=mock_embedder)

        position = MagicMock()
        position.end_date = None

        # One quantified, one not
        wu_quantified = MagicMock(id="wu_quantified")
        wu_quantified.title = "Led initiative"
        wu_quantified.outcome = MagicMock(
            result="Saved $2M annually",
            quantified_impact="$2M cost reduction",
            business_value=None
        )
        wu_quantified.actions = ["Analyzed", "Implemented"]
        wu_quantified.tags = []

        wu_qualitative = MagicMock(id="wu_qualitative")
        wu_qualitative.title = "Led initiative"
        wu_qualitative.outcome = MagicMock(
            result="Improved efficiency",
            quantified_impact=None,
            business_value=None
        )
        wu_qualitative.actions = ["Worked", "Helped"]
        wu_qualitative.tags = []

        jd = MagicMock()
        jd.text_for_ranking = "Cost reduction efficiency"

        result = curator.curate_position_bullets(position, [wu_qualitative, wu_quantified], jd)

        # Quantified should score higher
        assert result.scores["wu_quantified"] > result.scores["wu_qualitative"]
```

---

## Definition of Done

- [ ] `content_curator.py` service created with:
  - [ ] `curate_highlights()` method
  - [ ] `curate_certifications()` method
  - [ ] `curate_board_roles()` method
  - [ ] `curate_position_bullets()` method
- [ ] `CurationConfig` added to config.py with research-backed defaults
- [ ] `priority` field added to Certification model
- [ ] `priority` field added to BoardRole model
- [ ] Plan command displays curation decisions with scores
- [ ] Position bullets respect recency limits (4-6 recent, 3-4 mid, 2-3 older)
- [ ] Quantified achievements get 25% score boost
- [ ] Force-include via `priority: always` works
- [ ] Unit tests pass for all curation methods
- [ ] `uv run ruff check` passes
- [ ] `uv run mypy src --strict` passes

---

## Implementation Notes

1. **Lazy Loading**: The curator doesn't preload all embeddings. Each curate_* method computes embeddings on demand to avoid memory overhead for unused sections.

2. **Score Normalization**: All scores are normalized to 0.0-1.0 range for consistency and to support min_relevance_score filtering.

3. **Priority Override**: Items with `priority: always` consume slots first. This can result in fewer JD-relevant items if too many are marked as always.

4. **Position Age Calculation**: Uses end_date to determine age. Current positions (end_date=None) are treated as 0 years ago.

5. **Quantified Detection**: Uses same patterns as Story 7.13's `has_quantified_impact()` - can share code.

6. **Executive Detection**: Uses JD's `experience_level` field (EXECUTIVE or PRINCIPAL) to determine board role limits.
