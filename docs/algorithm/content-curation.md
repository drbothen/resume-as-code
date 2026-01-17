# Content Curation

This document explains the content curation logic that applies research-backed limits to resume sections.

## Overview

The Content Curator (`services/content_curator.py`) selects the most JD-relevant items for each resume section while respecting research-backed limits.

**Research Basis:** 2024-2025 resume studies analyzing 18.4M resumes established optimal limits for various sections.

## Default Section Limits

| Section | Default Limit | Research Basis |
|---------|---------------|----------------|
| Career Highlights | 4 | 3-5 optimal for executive summary |
| Certifications | 5 | 3-5 most relevant |
| Board Roles | 3 (5 for exec) | 2-3 unless executive role |
| Publications | 3 | Keep focused |
| Skills | 10 | 6-10 optimal (median 8-9) |

**Implementation:** `services/content_curator.py` (`DEFAULT_SECTION_LIMITS`)

```python
DEFAULT_SECTION_LIMITS = {
    "career_highlights": 4,
    "certifications": 5,
    "board_roles": 3,
    "board_roles_executive": 5,
    "publications": 3,
    "skills": 10,
}
```

## Bullets Per Position

Resume bullets are limited based on position recency:

| Position Age | Bullet Limit | Rationale |
|--------------|--------------|-----------|
| 0-3 years (recent) | 4-6 | Most relevant, detailed context |
| 3-7 years (mid) | 3-4 | Important but less detailed |
| 7+ years (older) | 2-3 | Show progression, less detail |

**Implementation:** `services/content_curator.py` (`BULLETS_PER_POSITION`)

```python
BULLETS_PER_POSITION = {
    "recent": {"years": 3, "min": 4, "max": 6},
    "mid": {"years": 7, "min": 3, "max": 4},
    "older": {"years": float("inf"), "min": 2, "max": 3},
}
```

## Curation Algorithm

Each curation method follows the same pattern:

1. **Separate Priority Items**: Items with `priority="always"` are always included
2. **Score Remaining Items**: Use semantic + keyword matching
3. **Filter by Minimum Score**: Exclude items below threshold (default 0.2)
4. **Rank and Select**: Take top N after priority items

### Scoring Formula

The `ContentCurator` uses a weighted combination:

**Career Highlights:**
```
score = (0.6 × semantic_similarity) + (0.4 × keyword_overlap)
```

**Certifications:**
```
score = (0.5 × skill_match) + (0.3 × semantic_similarity) + (0.2 × recency)
```

Where:
- `skill_match`: Cert name/issuer contains JD skills
- `semantic_similarity`: Embedding cosine similarity
- `recency`: 1.0 if active, 0.5 if expired

**Board Roles:**
```
score = (0.7 × semantic_similarity) + (0.3 × recency)
```

Where:
- `recency`: 1.0 if current, 0.7 if past

**Position Bullets (Work Units):**
```
score = base_score × quantified_boost
```

Where:
- `base_score`: Semantic similarity to JD
- `quantified_boost`: 1.25 if quantified metrics present

## Quantified Achievement Boost

Achievements with quantified metrics receive a 25% boost:

```python
QUANTIFIED_BOOST = 1.25
```

**Detection Patterns:**
```python
patterns = [
    r"\d+%",                                  # Percentages: 40%
    r"\$[\d,]+[KMB]?",                        # Dollars: $500K, $2M
    r"\d+x\b",                                # Multipliers: 10x
    r"\d+\s*(?:hours?|days?|weeks?|months?)", # Time: 2 hours
]
```

**Example:**

Two work units for the same position:

1. "Improved system performance" → base score = 0.70
2. "Reduced latency by 40%, saving $200K annually" → base score = 0.72

After quantified boost:
1. Final score = 0.70
2. Final score = 0.72 × 1.25 = 0.90

Work unit #2 ranked higher despite similar base relevance.

## Minimum Relevance Threshold

Items scoring below the minimum threshold are excluded entirely:

```python
min_relevance_score: float = 0.2
```

This prevents including marginally relevant items just to fill space.

## CurationResult Output

Each curation method returns a `CurationResult`:

```python
@dataclass
class CurationResult(Generic[T]):
    selected: list[T]        # Items selected for inclusion
    excluded: list[T]        # Items not selected
    scores: dict[str, float] # Score per item (keyed by identifier)
    reason: str              # Human-readable explanation
```

**Example:**
```python
result = curator.curate_certifications(certs, jd)
# result.selected = [AWS Solutions Architect, K8s Admin]
# result.excluded = [MS Office Specialist]
# result.scores = {"AWS...": 0.85, "K8s...": 0.72, "MS...": 0.15}
# result.reason = "Selected 2 certifications (0 priority + 2 by relevance)"
```

## Executive Role Detection

Board roles and some limits adjust for executive roles:

```python
def is_executive_level(experience_level: ExperienceLevel) -> bool:
    return experience_level in [ExperienceLevel.EXECUTIVE, ExperienceLevel.PRINCIPAL]
```

**Executive adjustments:**
- Board roles: 5 instead of 3
- Career highlights emphasized in hybrid format

## Worked Example: Certification Curation

**Input:** 8 certifications, JD for "Cloud Architect" role

```yaml
certifications:
  - name: AWS Solutions Architect Professional
    issuer: Amazon
    status: active
  - name: Kubernetes Administrator (CKA)
    issuer: CNCF
    status: active
  - name: Google Cloud Professional Architect
    issuer: Google
    status: active
  - name: PMP
    issuer: PMI
    status: active
  - name: ITIL Foundation
    issuer: Axelos
    status: expired
  - name: CompTIA A+
    issuer: CompTIA
    status: active
  - name: Scrum Master
    issuer: Scrum Alliance
    status: active
  - name: MS Office Specialist
    issuer: Microsoft
    status: active
```

**JD Skills:** `["aws", "kubernetes", "cloud", "architecture", "terraform"]`

**Scoring:**

| Certification | Skill Match | Semantic | Recency | Final Score |
|---------------|-------------|----------|---------|-------------|
| AWS Solutions Architect | 1.0 | 0.85 | 1.0 | 0.865 |
| GCP Professional Architect | 0.5 | 0.80 | 1.0 | 0.59 |
| CKA | 1.0 | 0.75 | 1.0 | 0.825 |
| PMP | 0.0 | 0.45 | 1.0 | 0.335 |
| ITIL | 0.0 | 0.35 | 0.5 | 0.205 |
| CompTIA A+ | 0.0 | 0.30 | 1.0 | 0.290 |
| Scrum Master | 0.0 | 0.40 | 1.0 | 0.320 |
| MS Office | 0.0 | 0.15 | 1.0 | 0.245 |

**With limit=5 and min_score=0.2:**

Selected (top 5 ≥ 0.2):
1. AWS Solutions Architect (0.865)
2. CKA (0.825)
3. GCP Architect (0.59)
4. PMP (0.335)
5. Scrum Master (0.320)

Excluded:
- CompTIA A+ (0.290)
- MS Office (0.245)
- ITIL (0.205) - barely above threshold

## Worked Example: Position Bullets

**Position:** Senior Engineer at TechCorp (ended 1 year ago)

**Work Units for Position:** 8 total

**Limit:** 4-6 bullets (recent = 0-3 years, position is 1 year old → recent)

**JD:** Platform Engineering, Kubernetes focus

| Work Unit | Semantic Score | Quantified | Final Score |
|-----------|----------------|------------|-------------|
| K8s migration, 40% cost reduction | 0.85 | Yes | 1.0625* |
| CI/CD pipeline implementation | 0.72 | Yes | 0.90 |
| Led team of 5 engineers | 0.60 | Yes | 0.75 |
| Security audit and remediation | 0.55 | No | 0.55 |
| Documentation updates | 0.35 | No | 0.35 |
| Bug fixes and maintenance | 0.30 | No | 0.30 |
| Attended conferences | 0.20 | No | 0.20 |
| Internal training | 0.15 | No | 0.15 |

*Capped at 1.0 for final display

**Selected (top 6):**
1. K8s migration (1.0)
2. CI/CD pipeline (0.90)
3. Led team (0.75)
4. Security audit (0.55)
5. Documentation (0.35)
6. Bug fixes (0.30)

**Excluded:**
- Attended conferences (0.20) - at threshold
- Internal training (0.15) - below threshold

## Configuration

All curation settings are configurable in `.resume.yaml`:

```yaml
curation:
  career_highlights_max: 4
  certifications_max: 5
  board_roles_max: 3
  board_roles_executive_max: 5
  publications_max: 3
  skills_max: 10

  bullets_per_position:
    recent_years: 3
    recent_max: 6
    mid_years: 7
    mid_max: 4
    older_max: 3

  min_relevance_score: 0.2
```

See [Configuration](configuration.md) for full parameter reference.
