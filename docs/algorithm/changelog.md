# Changelog

All notable changes to the matching algorithm are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.1] - 2026-01-16

### Added

- **JD Parsing Documentation** (`jd-parsing.md`)
  - Title extraction algorithm
  - 67 skill keywords with 30+ variant normalizations
  - Requirements extraction with required/nice-to-have classification
  - Experience level detection patterns
  - Keyword frequency analysis

- **Gap Analysis Documentation** (`gap-analysis.md`)
  - Coverage analyzer (strong/weak/gap skill matching)
  - Certification matcher (28+ cert patterns)
  - Education matcher (degree hierarchy, field aliases)

- **Skill Management Documentation** (`skill-management.md`)
  - Skill registry with alias normalization
  - 5-step skill curation pipeline
  - O*NET API v2.0 integration

### Changed

- Reorganized README.md quick links into categories (Core Algorithm, Supporting Services, Reference)
- Expanded Implementation Files table with all algorithm components

---

## [1.0.0] - 2026-01-16

### Added

Initial comprehensive documentation for the Resume-as-Code matching algorithm.

#### Scoring Components (Epic 7 Implementation)

- **Field-Weighted BM25** (Story 7.8)
  - Title field weighted 2.0x
  - Skills field weighted 1.5x
  - Experience field weighted 1.0x
  - Based on HBR 2023 research on recruiter scanning patterns

- **Recency Decay** (Story 7.9)
  - Exponential decay with configurable half-life (default: 5 years)
  - Current positions receive 100% weight
  - Formula: `recency = e^(-λ × years_ago)` where `λ = ln(2) / half_life`

- **Improved Tokenization** (Story 7.10)
  - Technical abbreviation expansion (ML → machine learning)
  - Separator normalization (CI/CD → ci cd)
  - Domain stop word filtering
  - Optional spaCy lemmatization

- **Section-Level Semantic Embeddings** (Story 7.11)
  - Outcome ↔ JD Requirements matching (40% weight)
  - Actions ↔ JD Requirements matching (30% weight)
  - Skills ↔ JD Skills matching (20% weight)
  - Title ↔ JD Full matching (10% weight)
  - Cross-section matching for precise relevance

- **Seniority Level Matching** (Story 7.12)
  - Infers seniority from title patterns and scope indicators
  - Asymmetric penalties (overqualified vs underqualified)
  - Supports explicit `seniority_level` override on work units
  - Seven levels: Entry, Mid, Senior, Lead, Staff, Principal, Executive

- **Impact Category Classification** (Story 7.13)
  - Categories: Financial, Operational, Talent, Customer, Organizational, Technical
  - Role-type to impact priority mapping
  - 25% boost for quantified achievements
  - Pattern-based impact detection

- **JD-Relevant Content Curation** (Story 7.14)
  - Research-backed section limits (2024-2025 studies)
  - Career highlights: max 4
  - Certifications: max 5
  - Board roles: max 3 (5 for executive)
  - Bullets per position: 4-6 recent, 3-4 mid, 2-3 older

#### Core Algorithm

- **Hybrid Ranking**
  - BM25 (lexical) + Semantic (embeddings) combination
  - Reciprocal Rank Fusion (RRF) with k=60
  - Configurable weights for BM25 vs semantic balance

- **Final Score Blending**
  - Relevance: 60% (default)
  - Recency: 20% (default)
  - Seniority: 10% (default)
  - Impact: 10% (default)

#### Documentation

- Algorithm overview and architecture diagrams
- Detailed scoring component explanations with formulas
- Worked examples for each component
- Complete configuration reference
- Use case tuning guide
- Troubleshooting guide

---

## Version Compatibility

| Algorithm Version | Resume-as-Code Version | Notes |
|-------------------|------------------------|-------|
| 1.0.0 | 0.7.x | Initial comprehensive algorithm |

## Migration Notes

### From Pre-1.0.0

The 1.0.0 algorithm introduces several new features that may affect ranking results:

1. **Recency Decay**: Older work units will score lower. To restore previous behavior:
   ```yaml
   scoring_weights:
     recency_half_life: null  # Disable decay
   ```

2. **Seniority Matching**: Work units may be penalized for seniority mismatch. To disable:
   ```yaml
   scoring_weights:
     use_seniority_matching: false
   ```

3. **Impact Alignment**: Achievements are now scored based on role-type alignment. To disable:
   ```yaml
   scoring_weights:
     use_impact_matching: false
   ```

4. **Field-Weighted BM25**: Title and skills fields are now weighted higher. For equal weights:
   ```yaml
   scoring_weights:
     title_weight: 1.0
     skills_weight: 1.0
     experience_weight: 1.0
   ```

## Upcoming Changes

In progress (Epic 7):

- **CLI Config Override** (Story 7.16)
  - `--config` flag for custom configuration paths
  - Environment-based configuration switching

- **O*NET Registry Workflow Wiring** (Story 7.17)
  - Wire O*NET service and Skill Registry into plan/build workflow
  - End-to-end skill standardization

## Contributing

When modifying the algorithm:

1. Update the relevant documentation section
2. Add an entry to this changelog
3. Include before/after examples if behavior changes
4. Update version number for significant changes
