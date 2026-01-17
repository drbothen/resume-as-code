# Configuration Reference

All algorithm configuration is in `.resume.yaml` under the `scoring_weights` and `curation` sections.

## Scoring Weights

Controls how Work Units are ranked against the Job Description.

```yaml
scoring_weights:
  # BM25 vs Semantic balance for RRF fusion
  bm25_weight: 1.0              # Range: 0.0-2.0, Default: 1.0
  semantic_weight: 1.0          # Range: 0.0-2.0, Default: 1.0

  # Field-specific BM25 weights
  title_weight: 2.0             # Range: 0.0-10.0, Default: 2.0
  skills_weight: 1.5            # Range: 0.0-10.0, Default: 1.5
  experience_weight: 1.0        # Range: 0.0-10.0, Default: 1.0

  # Recency decay
  recency_half_life: 5.0        # Range: 1.0-20.0, Default: 5.0
  recency_blend: 0.2            # Range: 0.0-0.5, Default: 0.2

  # Section-level semantic matching
  use_sectioned_semantic: false # Default: false
  section_outcome_weight: 0.4   # Range: 0.0-1.0, Default: 0.4
  section_actions_weight: 0.3   # Range: 0.0-1.0, Default: 0.3
  section_skills_weight: 0.2    # Range: 0.0-1.0, Default: 0.2
  section_title_weight: 0.1     # Range: 0.0-1.0, Default: 0.1

  # Seniority matching
  use_seniority_matching: true  # Default: true
  seniority_blend: 0.1          # Range: 0.0-0.3, Default: 0.1

  # Impact alignment
  use_impact_matching: true     # Default: true
  impact_blend: 0.1             # Range: 0.0-0.3, Default: 0.1
  quantified_boost: 1.25        # Range: 1.0-2.0, Default: 1.25
```

### Parameter Details

#### BM25 vs Semantic Balance

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `bm25_weight` | float | 1.0 | 0.0-2.0 | Weight for BM25 (lexical) in RRF fusion |
| `semantic_weight` | float | 1.0 | 0.0-2.0 | Weight for semantic (embeddings) in RRF fusion |

**Usage:**
- Increase `bm25_weight` for keyword-heavy JDs (e.g., technical requirements)
- Increase `semantic_weight` for conceptual matching (e.g., career changers)

#### Field-Specific BM25 Weights

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `title_weight` | float | 2.0 | 0.0-10.0 | Multiplier for title field matches |
| `skills_weight` | float | 1.5 | 0.0-10.0 | Multiplier for skills/tags field matches |
| `experience_weight` | float | 1.0 | 0.0-10.0 | Multiplier for experience body text |

**Research Basis:** HBR 2023 study shows recruiters focus on title and skills in first 7 seconds of resume review.

**Usage:**
- Default weights (2.0/1.5/1.0) work well for most cases
- Set all to 1.0 for equal weighting (standard BM25)
- Increase `skills_weight` for highly technical roles

#### Recency Decay

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `recency_half_life` | float | 5.0 | 1.0-20.0 | Years for experience to decay to 50% weight |
| `recency_blend` | float | 0.2 | 0.0-0.5 | How much recency affects final score |

**Formula:** `recency = e^(-ln(2)/half_life × years_ago)`

**Usage:**
- Shorter half-life (3.0) emphasizes recent experience (fast-moving fields)
- Longer half-life (10.0) values experience longevity (traditional industries)
- Set `recency_half_life: null` to disable decay entirely

#### Section-Level Semantic Matching

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `use_sectioned_semantic` | bool | false | - | Enable section-level matching |
| `section_outcome_weight` | float | 0.4 | 0.0-1.0 | Weight for outcome ↔ JD requirements |
| `section_actions_weight` | float | 0.3 | 0.0-1.0 | Weight for actions ↔ JD requirements |
| `section_skills_weight` | float | 0.2 | 0.0-1.0 | Weight for skills ↔ JD skills |
| `section_title_weight` | float | 0.1 | 0.0-1.0 | Weight for title ↔ JD full text |

**Constraint:** Section weights must sum to 1.0 when `use_sectioned_semantic: true`

**Usage:**
- Enable for more precise matching (slower, more accurate)
- Increase `section_outcome_weight` to emphasize results over actions
- Increase `section_skills_weight` for technical role matching

#### Seniority Matching

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `use_seniority_matching` | bool | true | - | Enable seniority alignment |
| `seniority_blend` | float | 0.1 | 0.0-0.3 | How much seniority affects final score |

**Usage:**
- Disable (`use_seniority_matching: false`) for career changers
- Increase `seniority_blend` for roles where seniority fit is critical

#### Impact Alignment

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `use_impact_matching` | bool | true | - | Enable impact category matching |
| `impact_blend` | float | 0.1 | 0.0-0.3 | How much impact affects final score |
| `quantified_boost` | float | 1.25 | 1.0-2.0 | Multiplier for quantified achievements |

**Usage:**
- Increase `quantified_boost` to 1.5 for data-driven roles
- Increase `impact_blend` for executive positions

---

## Content Curation

Controls section limits and relevance thresholds.

```yaml
curation:
  # Section limits
  career_highlights_max: 4      # Range: 1-10, Default: 4
  certifications_max: 5         # Range: 1-15, Default: 5
  board_roles_max: 3            # Range: 1-10, Default: 3
  board_roles_executive_max: 5  # Range: 1-10, Default: 5
  publications_max: 3           # Range: 1-10, Default: 3
  skills_max: 10                # Range: 1-30, Default: 10

  # Bullets per position
  bullets_per_position:
    recent_years: 3             # Years considered "recent"
    recent_max: 6               # Max bullets for recent positions
    mid_years: 7                # Years considered "mid-career"
    mid_max: 4                  # Max bullets for mid positions
    older_max: 3                # Max bullets for older positions

  # Relevance threshold
  min_relevance_score: 0.2      # Range: 0.0-1.0, Default: 0.2
```

### Parameter Details

#### Section Limits

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `career_highlights_max` | int | 4 | 1-10 | Maximum career highlights |
| `certifications_max` | int | 5 | 1-15 | Maximum certifications |
| `board_roles_max` | int | 3 | 1-10 | Maximum board roles (non-executive) |
| `board_roles_executive_max` | int | 5 | 1-10 | Maximum board roles (executive) |
| `publications_max` | int | 3 | 1-10 | Maximum publications |
| `skills_max` | int | 10 | 1-30 | Maximum skills displayed |

**Research Basis:**
- Career highlights: 3-5 optimal for quick scanning
- Certifications: Focus on most relevant 3-5
- Skills: 6-10 optimal (median 8-9 in successful resumes)

#### Bullets Per Position

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `recent_years` | int | 3 | Years threshold for "recent" |
| `recent_max` | int | 6 | Max bullets for recent positions |
| `mid_years` | int | 7 | Years threshold for "mid-career" |
| `mid_max` | int | 4 | Max bullets for mid positions |
| `older_max` | int | 3 | Max bullets for older positions |

**Position Age Calculation:**
```
age = (today - position.end_date).days / 365.25
```

**Example:**
- Position ended Jan 2024, today is Jan 2026 → age = 2 years → recent
- Position ended Jan 2020, today is Jan 2026 → age = 6 years → mid

#### Relevance Threshold

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `min_relevance_score` | float | 0.2 | 0.0-1.0 | Minimum score for inclusion |

Items scoring below this threshold are excluded entirely, even if space is available.

---

## Embedding Configuration

Controls the embedding model and caching.

```yaml
embedding:
  model: "intfloat/multilingual-e5-large-instruct"
  cache_enabled: true
  cache_path: ".resume_cache/embeddings.db"
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | "intfloat/multilingual-e5-large-instruct" | Sentence transformer model |
| `cache_enabled` | bool | true | Enable embedding cache |
| `cache_path` | string | ".resume_cache/embeddings.db" | Cache database path |

---

## O*NET Configuration

Controls O*NET skill standardization integration.

```yaml
onet:
  enabled: true
  api_key: null                 # Or set ONET_API_KEY env var
  cache_ttl: 86400              # 24 hours
  timeout: 10.0                 # Seconds
  retry_delay_ms: 200           # Minimum delay between retries
```

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `enabled` | bool | true | - | Enable O*NET integration |
| `api_key` | string | null | - | API key (or use env var) |
| `cache_ttl` | int | 86400 | ≥3600 | Cache TTL in seconds |
| `timeout` | float | 10.0 | 1.0-60.0 | Request timeout |
| `retry_delay_ms` | int | 200 | ≥200 | Retry delay (O*NET minimum) |

---

## Complete Example Configuration

```yaml
# .resume.yaml

# Output settings
output_dir: ./dist
default_format: both
default_template: executive

# Work unit settings
work_units_dir: ./work-units
positions_path: ./positions.yaml

# Ranking settings
default_top_k: 8

scoring_weights:
  # Emphasize semantic matching for career changers
  bm25_weight: 0.8
  semantic_weight: 1.2

  # Standard field weights
  title_weight: 2.0
  skills_weight: 1.5
  experience_weight: 1.0

  # Moderate recency decay (10-year half-life for executive)
  recency_half_life: 10.0
  recency_blend: 0.15

  # Enable section-level matching
  use_sectioned_semantic: true
  section_outcome_weight: 0.4
  section_actions_weight: 0.3
  section_skills_weight: 0.2
  section_title_weight: 0.1

  # Seniority matching enabled
  use_seniority_matching: true
  seniority_blend: 0.1

  # Impact alignment for executive
  use_impact_matching: true
  impact_blend: 0.15
  quantified_boost: 1.25

# Content curation
curation:
  career_highlights_max: 4
  certifications_max: 5
  board_roles_max: 5  # Executive-level
  board_roles_executive_max: 5
  publications_max: 3
  skills_max: 12

  bullets_per_position:
    recent_years: 3
    recent_max: 5
    mid_years: 7
    mid_max: 4
    older_max: 2

  min_relevance_score: 0.25  # Slightly stricter threshold

# O*NET integration
onet:
  enabled: true
  cache_ttl: 86400
```

---

## Validation Rules

The configuration model validates:

1. **Section weights sum to 1.0** when `use_sectioned_semantic: true`
2. **Ranges enforced** for all numeric parameters
3. **Career highlights warning** if more than 4 configured
4. **Path expansion** for `~` in file paths

See `models/config.py` for full Pydantic model definitions.
