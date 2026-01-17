# Scoring Components

This document explains each scoring component in detail, including mathematical formulas and worked examples.

## 1. BM25 (Lexical Matching)

BM25 (Best Matching 25) is a ranking function that scores documents based on term frequency and inverse document frequency.

### Formula

```
BM25(wu, jd) = Σ IDF(term) × (tf × (k1 + 1)) / (tf + k1 × (1 - b + b × |D|/avgdl))
```

**Parameters:**
- `k1 = 1.5` - Term frequency saturation (how quickly TF saturates)
- `b = 0.75` - Length normalization (0 = no normalization, 1 = full)
- `tf` - Term frequency in document
- `|D|` - Document length
- `avgdl` - Average document length across corpus

**Implementation:** `services/ranker.py` using `rank_bm25.BM25Okapi`

### Field Weighting (Story 7.8)

Work units are scored across three fields with different weights:

```python
title_weight: float = 2.0      # Title matches worth 2x
skills_weight: float = 1.5     # Skills matches worth 1.5x
experience_weight: float = 1.0 # Body text baseline
```

**Rationale:** Based on HBR 2023 research showing recruiters spend ~7 seconds on initial scan, focusing on title and skills first.

**Combined Score:**
```
BM25_weighted = (title_score × 2.0) + (skills_score × 1.5) + (experience_score × 1.0)
```

### Worked Example

Given a JD seeking "Kubernetes engineer" and a work unit:

```yaml
title: "Led Kubernetes migration project"
tags: ["kubernetes", "docker", "helm"]
actions:
  - "Migrated 50 microservices to Kubernetes"
  - "Reduced deployment time by 80%"
```

Field scores:
- Title field: "kubernetes" found → base score × 2.0
- Skills field: "kubernetes", "docker" found → base score × 1.5
- Experience: "kubernetes", "microservices" → base score × 1.0

Final BM25 score = weighted sum of field scores

### Tokenization (Story 7.10)

**File:** `utils/tokenizer.py`

The `ResumeTokenizer` normalizes text before BM25:

1. **Lowercase**: `Kubernetes` → `kubernetes`
2. **Separator normalization**: `CI/CD` → `ci cd`
3. **Abbreviation expansion**: `ML` → `ml machine learning`
4. **Domain stop word removal**: Filters `responsibilities`, `requirements`, etc.
5. **Lemmatization** (optional): `engineering` → `engineer` (requires spaCy)

**Abbreviation Expansions:**
```python
TECH_EXPANSIONS = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "k8s": "kubernetes",
    "cicd": "continuous integration continuous deployment",
    "aws": "amazon web services",
    # ... 50+ mappings
}
```

---

## 2. Semantic Matching (Embeddings)

Uses neural embeddings to capture conceptual similarity beyond keyword matching.

### Formula

```
semantic(wu, jd) = cos(embed(wu), embed(jd))
```

Where:
```
cos(a, b) = (a · b) / (||a|| × ||b||)
```

**Model:** `intfloat/multilingual-e5-large-instruct` (1024-dimensional embeddings)

**Implementation:** `services/embedder.py`

### Standard Mode

Embeds the full text of work unit and JD, then computes cosine similarity.

```python
doc_embedding = embedding_service.embed_batch(work_unit_texts)
jd_embedding = embedding_service.embed_passage(jd.text_for_ranking)
similarity = cosine_similarity(doc_embedding, jd_embedding)
```

### Section-Level Embeddings (Story 7.11)

For more precise matching, work units and JDs are embedded as separate sections:

**Work Unit Sections:**
| Section | Content | JD Match Target |
|---------|---------|-----------------|
| `title` | Work unit title | Full JD |
| `outcome` | Result + quantified impact | JD requirements |
| `actions` | Action bullet points | JD requirements |
| `skills` | Tags + demonstrated skills | JD skills list |

**Cross-Section Matching:**
```
Outcome  ↔ JD Requirements
Actions  ↔ JD Requirements
Skills   ↔ JD Skills
Title    ↔ JD Full Text
```

**Section Weights:**
```python
section_outcome_weight: 0.4   # Outcomes most important
section_actions_weight: 0.3   # Actions second
section_skills_weight: 0.2    # Skills third
section_title_weight: 0.1     # Title least
```

**Weighted Score:**
```
semantic_sectioned = (0.4 × outcome_sim) + (0.3 × actions_sim) +
                     (0.2 × skills_sim) + (0.1 × title_sim)
```

### Worked Example

Work unit:
```yaml
title: "Reduced infrastructure costs by 40%"
outcome:
  result: "Migrated to Kubernetes, reducing AWS spend"
  quantified_impact: "$2M annual savings"
tags: ["kubernetes", "aws", "cost-optimization"]
```

JD sections:
- Requirements: "Reduce cloud costs through infrastructure optimization"
- Skills: "Kubernetes, AWS, cost management"

Section similarities:
- Outcome ↔ Requirements: 0.85 (high - similar optimization theme)
- Actions ↔ Requirements: 0.72
- Skills ↔ JD Skills: 0.90 (exact skill matches)
- Title ↔ Full JD: 0.65

Final score:
```
semantic = (0.4 × 0.85) + (0.3 × 0.72) + (0.2 × 0.90) + (0.1 × 0.65)
         = 0.34 + 0.216 + 0.18 + 0.065
         = 0.801
```

---

## 3. Reciprocal Rank Fusion (RRF)

Combines BM25 and semantic rankings into a single score. RRF is robust because it uses ranks rather than raw scores.

### Formula

```
RRF(d) = Σ weight_i / (k + rank_i(d))
```

Where:
- `k = 60` (standard constant, reduces impact of outlier ranks)
- `rank_i(d)` = rank of document d in ranking method i (1-indexed)
- `weight_i` = weight for ranking method i

**Implementation:** `services/ranker.py` (`_rrf_fusion`)

### Worked Example

Three work units ranked by BM25 and semantic:

| Work Unit | BM25 Rank | Semantic Rank |
|-----------|-----------|---------------|
| A | 1 | 5 |
| B | 3 | 1 |
| C | 2 | 3 |

With default weights (bm25=1.0, semantic=1.0) and k=60:

**Work Unit A:**
```
RRF(A) = 1.0/(60+1) + 1.0/(60+5)
       = 0.0164 + 0.0154
       = 0.0318
```

**Work Unit B:**
```
RRF(B) = 1.0/(60+3) + 1.0/(60+1)
       = 0.0159 + 0.0164
       = 0.0323
```

**Work Unit C:**
```
RRF(C) = 1.0/(60+2) + 1.0/(60+3)
       = 0.0161 + 0.0159
       = 0.0320
```

**Final RRF Ranking:** B (0.0323) > C (0.0320) > A (0.0318)

Work unit B wins despite being rank 3 in BM25 because it's #1 in semantic.

---

## 4. Score Modifiers

After RRF fusion, three modifiers adjust the relevance score.

### Recency Decay (Story 7.9)

**File:** `services/ranker.py` (`_calculate_recency_score`)

Older experience is weighted less to emphasize recent, relevant work:

```
recency_score = e^(-λ × years_ago)
```

Where:
- `λ = ln(2) / half_life` (decay constant)
- `years_ago = (today - time_ended).days / 365.25`

**Default half-life:** 5.0 years

| Years Ago | Calculation | Score |
|-----------|-------------|-------|
| 0 (current) | e^0 | 100% |
| 1 | e^(-0.139×1) | 87% |
| 3 | e^(-0.139×3) | 66% |
| 5 | e^(-0.139×5) | 50% |
| 10 | e^(-0.139×10) | 25% |
| 15 | e^(-0.139×15) | 12% |

**Note:** Positions with `time_ended = null` (current) receive 100% weight.

### Seniority Matching (Story 7.12)

**File:** `services/seniority_inference.py`

Aligns work unit seniority with JD requirements.

**Seniority Levels (ranked 1-7):**
1. Entry
2. Mid
3. Senior
4. Lead
5. Staff
6. Principal
7. Executive

**Inference Priority:**
1. Explicit `seniority_level` on work unit
2. Position title patterns (CTO → Executive, Senior → Senior)
3. Scope indicators:
   - P&L responsibility → Executive
   - Revenue ≥ $100M → Executive
   - Team ≥ 50 → Staff
   - Team ≥ 10 → Lead

**Alignment Scoring (Asymmetric):**

| Mismatch | Score | Rationale |
|----------|-------|-----------|
| Exact match | 1.00 | Perfect fit |
| 1 level overqualified | 0.90 | Slight penalty (executive for senior) |
| 2 levels overqualified | 0.80 | May be overqualified |
| 3 levels overqualified | 0.75 | Likely overqualified |
| 1 level underqualified | 0.80 | Growth potential |
| 2 levels underqualified | 0.60 | Significant gap |
| 3 levels underqualified | 0.40 | Major gap |
| 4+ levels underqualified | 0.30 | Probably unqualified |

**Asymmetric rationale:** Being slightly overqualified (executive applying for senior) is less penalized than being significantly underqualified (entry applying for senior).

### Impact Alignment (Story 7.13)

**File:** `services/impact_classifier.py`

Matches achievement types to role expectations.

**Impact Categories:**
- `financial` - Revenue, cost savings, ROI
- `operational` - Automation, efficiency, uptime
- `talent` - Hiring, mentoring, team building
- `customer` - NPS, CSAT, user growth
- `organizational` - Strategy, transformation, culture
- `technical` - Architecture, implementation, scaling

**Role Type Priorities:**

| Role Type | Primary Impact | Secondary Impact |
|-----------|----------------|------------------|
| Sales | financial | customer |
| Engineering | operational | technical |
| Product | customer | operational |
| HR | talent | organizational |
| Executive | organizational | financial |
| Marketing | customer | financial |
| Operations | operational | financial |
| Finance | financial | operational |

**Alignment Score:**
```python
for impact in work_unit_impacts:
    if impact.category == primary_impact:
        score += impact.confidence × 1.0  # Full weight
    elif impact.category == secondary_impact:
        score += impact.confidence × 0.5  # Half weight

if is_quantified:
    score *= 1.25  # 25% boost for quantified achievements
```

**Quantification Patterns:**
- Percentages: `40%`, `50% reduction`
- Dollar amounts: `$500K`, `$2M ARR`
- Multipliers: `10x`, `3x improvement`
- Time metrics: `2 hours`, `50% faster`

---

## 5. Final Score Blending

**File:** `services/ranker.py` (`_blend_scores`)

All scores are combined with configurable weights:

```python
final = (
    relevance_blend  × normalized_relevance +
    recency_blend    × recency_score +
    seniority_blend  × seniority_score +
    impact_blend     × impact_score
)
```

**Default Weights:**
```python
relevance_blend  = 0.60  # (1.0 - 0.20 - 0.10 - 0.10)
recency_blend    = 0.20
seniority_blend  = 0.10
impact_blend     = 0.10
```

### Complete Worked Example

Work unit:
```yaml
id: wu-2024-01-15-k8s-migration
title: "Led Kubernetes migration reducing costs 40%"
position_id: pos-techcorp-senior-engineer
time_ended: "2025-01"  # 1 year ago
outcome:
  result: "Migrated infrastructure to Kubernetes"
  quantified_impact: "$2M annual savings"
tags: ["kubernetes", "aws", "infrastructure"]
```

JD: Senior Site Reliability Engineer (seniority: SENIOR)

**Step 1: BM25 Ranking**
- Ranks #2 out of 20 work units (strong keyword match)

**Step 2: Semantic Ranking**
- Ranks #1 out of 20 work units (infrastructure optimization theme matches)

**Step 3: RRF Fusion**
```
RRF = 1.0/(60+2) + 1.0/(60+1) = 0.0161 + 0.0164 = 0.0325
```
Normalized relevance = 0.95 (highest score = 1.0)

**Step 4: Recency Score**
```
years_ago = 1.0
recency = e^(-0.139 × 1.0) = 0.87
```

**Step 5: Seniority Score**
- Work unit seniority: Senior (from position title)
- JD seniority: Senior
- Match: Exact → 1.0

**Step 6: Impact Score**
- Impact categories: financial (0.9 confidence), operational (0.6)
- Role type: Engineering → expects operational, technical
- operational is secondary → 0.6 × 0.5 = 0.30
- quantified = True → 0.30 × 1.25 = 0.375

**Step 7: Final Score**
```
final = (0.60 × 0.95) + (0.20 × 0.87) + (0.10 × 1.0) + (0.10 × 0.375)
      = 0.570 + 0.174 + 0.100 + 0.0375
      = 0.8815
```

Final score: **88.15%** - Very strong match!
