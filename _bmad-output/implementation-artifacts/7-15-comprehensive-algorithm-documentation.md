# Story 7.15: Comprehensive Algorithm Documentation

**Epic:** Epic 7 - Schema & Data Model Refactoring
**Story Points:** 3
**Priority:** P1
**Status:** Done
**Dependencies:** Stories 7.8-7.14 (all ready-for-dev)

---

## User Story

As a **developer or future maintainer**,
I want **complete documentation of the matching algorithm, its components, configuration options, and tuning guidance**,
So that **I can understand, debug, tune, and extend the algorithm with confidence**.

---

## Background

The ranking algorithm has grown significantly through Epic 7:
- **Story 7.8**: Field-weighted BM25 scoring
- **Story 7.9**: Recency decay for work units
- **Story 7.10**: Improved tokenization (lemmatization, abbreviations)
- **Story 7.11**: Section-level semantic embeddings
- **Story 7.12**: Seniority level matching
- **Story 7.13**: Impact category classification
- **Story 7.14**: JD-relevant content curation

Without comprehensive documentation, understanding how all these components interact is challenging. This story consolidates all algorithm knowledge into a single, authoritative reference.

**Existing Documentation:**
- `docs/philosophy.md` - High-level project philosophy
- `docs/data-model.md` - Data model documentation
- `docs/workflow.md` - User workflow documentation
- `docs/diagrams/` - Diagram assets

This story adds `docs/algorithm/` with detailed algorithm documentation.

---

## Acceptance Criteria

### AC1: Architecture overview with data flow
**Given** I am a new developer joining the project
**When** I read the algorithm documentation
**Then** I understand the complete matching pipeline end-to-end
**And** I can trace how a work unit score is calculated

### AC2: Scoring components explained
**Given** the documentation exists
**When** I look for algorithm details
**Then** I find:
- Each scoring component explained (BM25, Semantic, RRF)
- Mathematical formulas with worked examples
- Code references to implementation files

### AC3: Configuration reference
**Given** I want to configure the algorithm
**When** I consult the documentation
**Then** I find:
- All configuration parameters listed
- Default values and valid ranges
- YAML examples for common configurations

### AC4: Tuning guide with use cases
**Given** I want to tune the algorithm for a specific use case
**When** I consult the tuning guide
**Then** I find concrete recommendations for:
- Executive vs IC resumes
- Technical vs non-technical roles
- Career changers vs domain experts
- Entry-level vs senior positions

### AC5: Troubleshooting section
**Given** ranking results seem wrong
**When** I consult troubleshooting
**Then** I find:
- Common issues and solutions
- How to debug scoring
- Logging/verbose mode guidance

### AC6: Changelog for version tracking
**Given** the algorithm changes in the future
**When** developers update the code
**Then** documentation includes a changelog section
**And** version compatibility notes

---

## Technical Design

### Documentation Structure

```
docs/
├── algorithm/
│   ├── README.md              # Main entry point, table of contents
│   ├── architecture.md        # Overview, data flow diagrams
│   ├── scoring-components.md  # BM25, Semantic, RRF, blending
│   ├── content-curation.md    # Section limits, bullet curation
│   ├── configuration.md       # All config options with examples
│   ├── tuning-guide.md        # Use case recommendations
│   ├── troubleshooting.md     # Common issues, debugging
│   └── changelog.md           # Version history
├── philosophy.md              # (existing)
├── data-model.md              # (existing)
└── workflow.md                # (existing)
```

### 1. README.md (Entry Point)

```markdown
# Matching Algorithm Documentation

This documentation describes the Resume-as-Code matching algorithm that selects
and ranks Work Units based on relevance to a target Job Description (JD).

## Quick Links

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System overview and data flow |
| [Scoring Components](scoring-components.md) | BM25, semantic, fusion details |
| [Content Curation](content-curation.md) | Section limits and bullet selection |
| [Configuration](configuration.md) | All config options with examples |
| [Tuning Guide](tuning-guide.md) | Recommendations by use case |
| [Troubleshooting](troubleshooting.md) | Common issues and debugging |
| [Changelog](changelog.md) | Version history |

## Algorithm at a Glance

The algorithm combines:
1. **Lexical matching (BM25)** - Keyword-based relevance
2. **Semantic matching (Embeddings)** - Conceptual similarity
3. **Reciprocal Rank Fusion (RRF)** - Combines both rankings
4. **Modifiers** - Recency decay, seniority matching, impact alignment
5. **Content curation** - Research-backed section limits

Final score formula:
```
final = (relevance × 0.6) + (recency × 0.2) + (seniority × 0.1) + (impact × 0.1)
```

Where `relevance` = RRF fusion of BM25 and semantic scores.
```

### 2. Architecture Overview (architecture.md)

```markdown
# Algorithm Architecture

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
│  │  │         RRF(d) = Σ 1/(k + rank_i(d))                       │  │   │
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
│  │ RankedWorkUnits + CuratedSections + MatchReasons               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Implementation Files

| Component | File | Description |
|-----------|------|-------------|
| JD Parser | `services/jd_parser.py` | Extracts structured JD data |
| Work Unit Loader | `services/work_unit_loader.py` | Loads and validates work units |
| Hybrid Ranker | `services/ranker.py` | Main ranking orchestration |
| BM25 Scorer | `services/ranker.py` | Lexical scoring |
| Embedding Service | `services/embedder.py` | Semantic embeddings |
| Seniority Inference | `services/seniority_inference.py` | Title→seniority mapping |
| Impact Classifier | `services/impact_classifier.py` | Outcome→impact category |
| Content Curator | `services/content_curator.py` | Section curation |
| Tokenizer | `utils/tokenizer.py` | BM25 tokenization |
```

### 3. Scoring Components (scoring-components.md)

```markdown
# Scoring Components

## 1. BM25 (Lexical Matching)

BM25 scores documents based on term frequency and inverse document frequency.

### Formula

```
BM25(wu, jd) = Σ IDF(term) × (tf × (k1 + 1)) / (tf + k1 × (1 - b + b × |D|/avgdl))
```

**Parameters:**
- `k1 = 1.5` - Term frequency saturation
- `b = 0.75` - Length normalization

### Field Weighting (Story 7.8)

Different fields are weighted differently:

```python
title_weight: float = 2.0      # Title matches worth 2x
skills_weight: float = 1.5     # Skills matches worth 1.5x
experience_weight: float = 1.0 # Body text baseline
```

**Example:** If "Kubernetes" appears in:
- Title: contributes `2.0 × base_score`
- Skills: contributes `1.5 × base_score`
- Actions: contributes `1.0 × base_score`

### Tokenization (Story 7.10)

The tokenizer normalizes text before BM25:

1. **Abbreviation expansion**: `ML` → `machine learning`
2. **Separator normalization**: `CI/CD` → `ci cd`
3. **Lemmatization**: `engineering` → `engineer` (optional, requires spaCy)
4. **Stop word removal**: Filters `responsibilities`, `requirements`, etc.

---

## 2. Semantic Matching (Embeddings)

Uses sentence-transformers to compute vector similarity.

### Formula

```
semantic(wu, jd) = cos(embed(wu), embed(jd))
```

**Model:** `intfloat/multilingual-e5-large-instruct` (default)

### Section-Level Embeddings (Story 7.11)

Work units are embedded as multiple sections:

| Section | Content | JD Match Target |
|---------|---------|-----------------|
| `title` | Work unit title | Full JD |
| `outcome` | Result + quantified impact | JD requirements |
| `actions` | Action bullet points | JD requirements |
| `skills` | Tags + demonstrated skills | JD skills list |

**Section Weights:**
```python
section_outcome_weight: 0.4   # Outcomes most important
section_actions_weight: 0.3   # Actions second
section_skills_weight: 0.2    # Skills third
section_title_weight: 0.1     # Title least
```

---

## 3. Reciprocal Rank Fusion (RRF)

Combines BM25 and semantic rankings:

```
RRF(d) = Σ 1/(k + rank_i(d))
```

**Parameter:** `k = 60` (standard)

**Example:**
- Work unit A: BM25 rank=1, Semantic rank=5
- Work unit B: BM25 rank=3, Semantic rank=1

```
RRF(A) = 1/(60+1) + 1/(60+5) = 0.0164 + 0.0154 = 0.0318
RRF(B) = 1/(60+3) + 1/(60+1) = 0.0159 + 0.0164 = 0.0323
```

Work unit B wins despite being rank 3 in BM25 because it's #1 in semantic.

---

## 4. Score Modifiers

### Recency Decay (Story 7.9)

Older experience is weighted less:

```
recency_score = e^(-λ × years_ago)
```

Where `λ = ln(2) / half_life`

**Default:** `half_life = 5.0 years`

| Years Ago | Score |
|-----------|-------|
| 0 (current) | 100% |
| 1 | 87% |
| 3 | 66% |
| 5 | 50% |
| 10 | 25% |

### Seniority Matching (Story 7.12)

Aligns work unit seniority with JD requirements:

| Mismatch | Score |
|----------|-------|
| Exact match | 100% |
| 1 level off | 85% |
| 2 levels off | 65% |
| 3 levels off | 45% |
| 4+ levels off | 30% |

### Impact Alignment (Story 7.13)

Matches achievement type to role type:

| Role Type | Prioritized Impacts |
|-----------|---------------------|
| Sales | financial, customer |
| Engineering | operational, technical |
| Product | customer, operational |
| HR | talent, organizational |
| Executive | organizational, financial |

**Quantified Boost:** +25% for achievements with metrics

---

## 5. Final Score Blending

```python
final = (
    relevance_score × 0.60 +
    recency_score × 0.20 +
    seniority_score × 0.10 +
    impact_score × 0.10
)
```

**Config:**
```yaml
scoring_weights:
  bm25_weight: 0.4
  semantic_weight: 0.6
  recency_blend: 0.2
  seniority_blend: 0.1
  impact_blend: 0.1
```
```

### 4. Configuration Reference (configuration.md)

```markdown
# Configuration Reference

All configuration is in `.resume.yaml`.

## Scoring Weights

```yaml
scoring_weights:
  # BM25 vs Semantic balance
  bm25_weight: 0.4              # Range: 0.0-1.0, default: 0.4
  semantic_weight: 0.6          # Range: 0.0-1.0, default: 0.6

  # Field weights for BM25
  title_weight: 2.0             # Range: 0.5-5.0, default: 2.0
  skills_weight: 1.5            # Range: 0.5-5.0, default: 1.5
  experience_weight: 1.0        # Range: 0.5-5.0, default: 1.0

  # Recency decay
  recency_half_life: 5.0        # Range: 1.0-20.0, default: 5.0
  recency_blend: 0.2            # Range: 0.0-0.5, default: 0.2

  # Seniority matching
  use_seniority_matching: true  # default: true
  seniority_blend: 0.1          # Range: 0.0-0.3, default: 0.1

  # Impact alignment
  use_impact_matching: true     # default: true
  impact_blend: 0.1             # Range: 0.0-0.3, default: 0.1
  quantified_boost: 1.25        # Range: 1.0-2.0, default: 1.25
```

## Content Curation

```yaml
curation:
  career_highlights_max: 4      # Range: 1-10, default: 4
  certifications_max: 5         # Range: 1-15, default: 5
  board_roles_max: 3            # Range: 1-10, default: 3
  board_roles_executive_max: 5  # Range: 1-10, default: 5
  skills_max: 10                # Range: 1-30, default: 10

  bullets_per_position:
    recent_years: 3             # Years considered "recent"
    recent_max: 6               # Bullets for recent positions
    mid_years: 7                # Years considered "mid"
    mid_max: 4                  # Bullets for mid positions
    older_max: 3                # Bullets for older positions

  quantified_boost: 1.25        # Boost for quantified achievements
  min_relevance_score: 0.2      # Minimum score to include
```

## Embedding Configuration

```yaml
embedding:
  model: "intfloat/multilingual-e5-large-instruct"
  cache_enabled: true
  cache_path: ".resume_cache/embeddings.db"
```
```

### 5. Tuning Guide (tuning-guide.md)

```markdown
# Tuning Guide

## Use Case Recommendations

### Executive vs IC Resumes

**Executive (CTO, VP, Director):**
```yaml
scoring_weights:
  seniority_blend: 0.15        # Seniority matters more
  impact_blend: 0.15           # Impact alignment critical
  recency_blend: 0.1           # Experience over recency

curation:
  board_roles_max: 5           # Show governance experience
  career_highlights_max: 4     # Emphasize strategic wins
```

**Individual Contributor:**
```yaml
scoring_weights:
  seniority_blend: 0.05        # Less emphasis on seniority
  impact_blend: 0.1            # Technical impact still matters
  recency_blend: 0.25          # Recent skills more important

curation:
  board_roles_max: 2           # Minimal governance
  skills_max: 12               # More technical skills
```

### Technical vs Non-Technical Roles

**Technical (Engineer, Architect):**
```yaml
scoring_weights:
  skills_weight: 2.0           # Skills critical
  title_weight: 1.5            # Title less important
```

**Non-Technical (PM, Marketing):**
```yaml
scoring_weights:
  skills_weight: 1.0           # Skills less differentiated
  title_weight: 2.5            # Title more important
```

### Career Changers

```yaml
scoring_weights:
  semantic_weight: 0.7         # Conceptual similarity helps
  bm25_weight: 0.3             # Exact keywords less useful
  seniority_blend: 0.05        # Ignore seniority mismatch
  recency_blend: 0.1           # Don't penalize old experience
```

### Entry-Level Positions

```yaml
scoring_weights:
  recency_half_life: 3.0       # Recent education matters
  seniority_blend: 0.0         # No seniority matching

curation:
  bullets_per_position:
    recent_max: 4              # Fewer bullets OK
    mid_max: 3
    older_max: 2
```
```

---

## Files to Create

| File | Description |
|------|-------------|
| `docs/algorithm/README.md` | Entry point with overview |
| `docs/algorithm/architecture.md` | Data flow diagrams |
| `docs/algorithm/scoring-components.md` | BM25, semantic, RRF details |
| `docs/algorithm/content-curation.md` | Section limits, bullet curation |
| `docs/algorithm/configuration.md` | All config options |
| `docs/algorithm/tuning-guide.md` | Use case recommendations |
| `docs/algorithm/troubleshooting.md` | Common issues, debugging |
| `docs/algorithm/changelog.md` | Version history |

---

## Test Cases

### Documentation Validation

```bash
# Verify all links work
uv run python -c "
import re
from pathlib import Path

docs_dir = Path('docs/algorithm')
for md_file in docs_dir.glob('*.md'):
    content = md_file.read_text()
    # Check for broken internal links
    links = re.findall(r'\[.*?\]\((.*?\.md)\)', content)
    for link in links:
        target = docs_dir / link
        assert target.exists(), f'Broken link in {md_file}: {link}'
"

# Verify code references exist
uv run python -c "
from pathlib import Path
# Verify referenced files exist
files = [
    'src/resume_as_code/services/ranker.py',
    'src/resume_as_code/services/embedder.py',
    'src/resume_as_code/services/content_curator.py',
    'src/resume_as_code/services/seniority_inference.py',
    'src/resume_as_code/services/impact_classifier.py',
]
for f in files:
    assert Path(f).exists(), f'Referenced file not found: {f}'
"
```

---

## Definition of Done

- [x] `docs/algorithm/README.md` created with overview and quick links
- [x] `docs/algorithm/architecture.md` with ASCII data flow diagrams
- [x] `docs/algorithm/scoring-components.md` with:
  - [x] BM25 formula and field weights
  - [x] Semantic scoring with section embeddings
  - [x] RRF fusion explanation
  - [x] Score modifiers (recency, seniority, impact)
- [x] `docs/algorithm/content-curation.md` with research-backed limits
- [x] `docs/algorithm/configuration.md` with all params, defaults, ranges
- [x] `docs/algorithm/tuning-guide.md` with use case recommendations
- [x] `docs/algorithm/troubleshooting.md` with common issues
- [x] `docs/algorithm/changelog.md` with initial version entry
- [x] All internal links verified working
- [x] Code references point to existing files
- [x] Formulas include worked examples

---

## Implementation Notes

1. **ASCII Diagrams**: Use box-drawing characters for diagrams that render correctly in both terminal and GitHub markdown.

2. **Code References**: Link to specific files but not line numbers (they change). Use format: `services/ranker.py`.

3. **Worked Examples**: Every formula should have a concrete example with real numbers.

4. **Config Tables**: Show param name, type, default, valid range, and description.

5. **Keep Updated**: Add a note at the top about keeping docs in sync with code changes.

6. **Changelog Format**: Use Keep a Changelog format (https://keepachangelog.com/).

---

## Dev Agent Record

### Implementation Summary

**Completed:** 2026-01-16

All 11 documentation files created in `docs/algorithm/`:

#### Core Algorithm (8 files - original scope)
1. **README.md** - Entry point with ASCII pipeline diagram, quick links table, and algorithm overview
2. **architecture.md** - 4-stage data flow diagrams (Input, Scoring, Curation, Output) with implementation file mappings
3. **scoring-components.md** - Complete formulas for BM25, semantic, RRF with worked examples and score modifier details
4. **content-curation.md** - Research-backed section limits, curation algorithm, quantified boost, and worked examples
5. **configuration.md** - Complete parameter reference with types, defaults, ranges for all scoring/curation/embedding settings
6. **tuning-guide.md** - Use case configurations (Executive, IC, Technical, Non-Technical, Career Changer, Entry-Level, Industry-specific)
7. **troubleshooting.md** - Common issues table with causes/solutions, debugging techniques, error messages
8. **changelog.md** - Version 1.0.0 documenting all Epic 7 features with migration notes

#### Supporting Services (3 files - expanded scope)
9. **jd-parsing.md** - JD Parser with title extraction, 67 skill keywords, 30+ normalizations, experience level detection
10. **gap-analysis.md** - Coverage Analyzer, Certification Matcher (28 patterns), Education Matcher (degree hierarchy)
11. **skill-management.md** - Skill Registry, 5-step Skill Curator pipeline, O*NET API v2.0 integration

### Validation Results

- **Internal links:** All verified (docs cross-reference correctly)
- **Code references:** All 17 implementation files exist
- **Test suite:** 2166 passed, 35 warnings (pre-existing)

### Files Created

| File | Lines | Description |
|------|-------|-------------|
| `docs/algorithm/README.md` | 170 | Entry point with overview (updated) |
| `docs/algorithm/architecture.md` | 126 | Data flow diagrams |
| `docs/algorithm/scoring-components.md` | 340 | Scoring formulas and examples |
| `docs/algorithm/content-curation.md` | 295 | Curation logic and limits |
| `docs/algorithm/configuration.md` | 323 | Complete config reference |
| `docs/algorithm/tuning-guide.md` | 359 | Use case recommendations |
| `docs/algorithm/troubleshooting.md` | 322 | Debugging guide |
| `docs/algorithm/changelog.md` | 165 | Version history (updated) |
| `docs/algorithm/jd-parsing.md` | 280 | JD extraction and normalization |
| `docs/algorithm/gap-analysis.md` | 200 | Coverage/cert/edu matching |
| `docs/algorithm/skill-management.md` | 270 | Registry, curation, O*NET |
