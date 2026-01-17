# Algorithm Architecture

This document describes the architecture and data flow of the Resume-as-Code matching algorithm.

## High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           INPUT STAGE                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐         ┌─────────────┐         ┌─────────────┐       │
│  │ Job         │         │ Work Units  │         │ Positions   │       │
│  │ Description │         │ (YAML)      │         │ (YAML)      │       │
│  └──────┬──────┘         └──────┬──────┘         └──────┬──────┘       │
│         │                       │                       │               │
│         ▼                       ▼                       ▼               │
│  ┌─────────────┐         ┌─────────────┐         ┌─────────────┐       │
│  │ JD Parser   │         │ WU Loader   │◄────────│ Position    │       │
│  │             │         │             │ attach  │ Service     │       │
│  └──────┬──────┘         └──────┬──────┘         └─────────────┘       │
│         │                       │                                       │
│         ▼                       ▼                                       │
│  ┌─────────────┐         ┌─────────────┐                               │
│  │ JobDesc     │         │ WorkUnit[]  │                               │
│  │ (structured)│         │ (enriched)  │                               │
│  └──────┬──────┘         └──────┬──────┘                               │
│         │                       │                                       │
└─────────┼───────────────────────┼───────────────────────────────────────┘
          │                       │
          ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          SCORING STAGE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      HYBRID RANKER                                │   │
│  │                                                                   │   │
│  │  ┌─────────────────┐              ┌─────────────────┐            │   │
│  │  │ BM25 Scorer     │              │ Semantic Scorer │            │   │
│  │  │                 │              │                 │            │   │
│  │  │ • Field weights │              │ • Section embeds│            │   │
│  │  │ • Tokenization  │              │ • Cross-matching│            │   │
│  │  │ • Abbrev expand │              │ • Cosine sim    │            │   │
│  │  └────────┬────────┘              └────────┬────────┘            │   │
│  │           │                                │                      │   │
│  │           ▼                                ▼                      │   │
│  │  ┌────────────────────────────────────────────────────────────┐  │   │
│  │  │                  RRF FUSION (k=60)                          │  │   │
│  │  │         RRF(d) = Σ weight_i / (k + rank_i(d))              │  │   │
│  │  └────────────────────────────┬───────────────────────────────┘  │   │
│  │                               │                                   │   │
│  └───────────────────────────────┼───────────────────────────────────┘   │
│                                  │                                       │
│  ┌───────────────────────────────▼───────────────────────────────────┐   │
│  │                      SCORE MODIFIERS                               │   │
│  │                                                                    │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │   │
│  │  │ Recency      │  │ Seniority    │  │ Impact       │            │   │
│  │  │ Decay        │  │ Match        │  │ Alignment    │            │   │
│  │  │              │  │              │  │              │            │   │
│  │  │ e^(-λ×years) │  │ level match  │  │ role→impact  │            │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │   │
│  │                                                                    │   │
│  └────────────────────────────────┬──────────────────────────────────┘   │
│                                   │                                       │
└───────────────────────────────────┼───────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CURATION STAGE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    CONTENT CURATOR                                │   │
│  │                                                                   │   │
│  │  Research-backed limits (2024-2025 resume studies):              │   │
│  │                                                                   │   │
│  │  • Career highlights: max 4                                      │   │
│  │  • Certifications: max 5                                         │   │
│  │  • Board roles: max 3 (5 for executive)                          │   │
│  │  • Bullets per position: 4-6 recent, 3-4 mid, 2-3 older         │   │
│  │  • Quantified boost: 25%                                         │   │
│  │                                                                   │   │
│  └────────────────────────────────┬──────────────────────────────────┘   │
│                                   │                                       │
└───────────────────────────────────┼───────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           OUTPUT                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ RankingOutput:                                                   │    │
│  │   - RankedWorkUnits (sorted by final score)                     │    │
│  │   - MatchReasons (per work unit)                                 │    │
│  │   - JD Keywords                                                  │    │
│  │                                                                  │    │
│  │ CurationResult:                                                  │    │
│  │   - Selected items (by section)                                  │    │
│  │   - Excluded items (with reasons)                                │    │
│  │   - Scores (per item)                                            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### Input Stage

#### JD Parser (`services/jd_parser.py`)

Extracts structured data from job descriptions:

- **Title**: Job title for role type inference
- **Keywords**: Important terms for BM25 matching
- **Skills**: Technical skills list
- **Experience Level**: Inferred seniority (entry, mid, senior, lead, etc.)
- **Requirements Text**: Concatenated requirements for ranking

#### Work Unit Loader (`services/work_unit_loader.py`)

Loads and validates work units from YAML files:

- Parses `work-units/*.yaml` files
- Validates against Pydantic schema
- Attaches position data via `position_id` reference

#### Position Service (`services/position_service.py`)

Manages employment history:

- Loads `positions.yaml`
- Provides position lookup by ID
- Contains scope indicators (team size, P&L, revenue)

### Scoring Stage

#### BM25 Scorer (Lexical)

**File:** `services/ranker.py` (`_bm25_rank`, `_bm25_rank_weighted`)

Field-weighted BM25 scoring:

```
BM25_weighted = title × 2.0 + skills × 1.5 + experience × 1.0
```

Uses `ResumeTokenizer` for preprocessing:
- Abbreviation expansion (ML → machine learning)
- Separator normalization (CI/CD → ci cd)
- Domain stop word filtering

#### Semantic Scorer (Embeddings)

**File:** `services/ranker.py` (`_semantic_rank`, `_semantic_rank_sectioned`)

Two modes:
1. **Standard**: Full text embedding comparison
2. **Sectioned** (Story 7.11): Cross-section matching

Section-level matching:

```
Outcome  ↔ JD Requirements (weight: 0.4)
Actions  ↔ JD Requirements (weight: 0.3)
Skills   ↔ JD Skills       (weight: 0.2)
Title    ↔ JD Full Text    (weight: 0.1)
```

**Embedding Model:** `intfloat/multilingual-e5-large-instruct`

#### RRF Fusion

**File:** `services/ranker.py` (`_rrf_fusion`)

Reciprocal Rank Fusion combines BM25 and semantic rankings:

```
RRF(d) = Σ weight_i / (k + rank_i(d))
```

Where:
- `k = 60` (standard constant)
- `weight_bm25 = 1.0` (default)
- `weight_semantic = 1.0` (default)

### Score Modifiers

#### Recency Decay (Story 7.9)

**File:** `services/ranker.py` (`_calculate_recency_score`)

Exponential decay based on position end date:

```
recency = e^(-λ × years_ago)

where λ = ln(2) / half_life
```

**Default half-life:** 5 years

| Years Ago | Weight |
|-----------|--------|
| 0 (current) | 100% |
| 1 | 87% |
| 3 | 66% |
| 5 | 50% |
| 10 | 25% |

#### Seniority Matching (Story 7.12)

**File:** `services/seniority_inference.py`

Infers seniority from:
1. Explicit `seniority_level` on work unit
2. Position title patterns (CTO → Executive, Senior → Senior)
3. Scope indicators (P&L → Executive, team size → Lead/Staff)

Alignment scoring (asymmetric penalties):

| Mismatch | Score |
|----------|-------|
| Exact match | 100% |
| 1 level overqualified | 90% |
| 1 level underqualified | 80% |
| 2 levels overqualified | 80% |
| 2 levels underqualified | 60% |
| 3+ levels | 30-75% |

#### Impact Alignment (Story 7.13)

**File:** `services/impact_classifier.py`

Classifies outcomes into impact categories:
- Financial, Operational, Talent, Customer, Organizational, Technical

Maps role types to expected impacts:

| Role Type | Prioritized Impacts |
|-----------|---------------------|
| Sales | financial, customer |
| Engineering | operational, technical |
| Product | customer, operational |
| HR | talent, organizational |
| Executive | organizational, financial |

**Quantified Boost:** +25% for achievements with metrics

### Curation Stage

**File:** `services/content_curator.py`

Research-backed section limits:

| Section | Limit | Research Basis |
|---------|-------|----------------|
| Career Highlights | 4 | 3-5 optimal (2024-2025 studies) |
| Certifications | 5 | 3-5 most relevant |
| Board Roles | 3 (5 exec) | 2-3 unless executive |
| Skills | 10 | 6-10 optimal (median 8-9) |

Bullets per position based on recency:

| Recency | Limit |
|---------|-------|
| 0-3 years | 4-6 bullets |
| 3-7 years | 3-4 bullets |
| 7+ years | 2-3 bullets |

## Score Blending

**File:** `services/ranker.py` (`_blend_scores`)

Final score combines all components:

```python
final = (
    relevance_blend × normalized_relevance +
    recency_blend   × recency_score +
    seniority_blend × seniority_score +
    impact_blend    × impact_score
)
```

**Default weights:**
- Relevance: 60% (1.0 - 0.2 - 0.1 - 0.1)
- Recency: 20%
- Seniority: 10%
- Impact: 10%

## Implementation Files Summary

| File | Purpose |
|------|---------|
| `services/ranker.py` | Main `HybridRanker` class |
| `services/embedder.py` | Embedding generation and caching |
| `services/jd_parser.py` | Job description parsing |
| `services/work_unit_loader.py` | Work unit loading |
| `services/position_service.py` | Position management |
| `services/seniority_inference.py` | Title→seniority mapping |
| `services/impact_classifier.py` | Outcome→impact classification |
| `services/content_curator.py` | Section curation logic |
| `utils/tokenizer.py` | BM25 tokenization |
| `utils/work_unit_text.py` | Text extraction helpers |
| `models/config.py` | Configuration models |
