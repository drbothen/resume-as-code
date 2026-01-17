# Matching Algorithm Documentation

> **Last Updated:** 2026-01-16
> **Version:** 1.0.1

This documentation describes the Resume-as-Code matching algorithm that selects and ranks Work Units based on relevance to a target Job Description (JD).

## Quick Links

### Core Algorithm
| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System overview and data flow diagrams |
| [Scoring Components](scoring-components.md) | BM25, semantic matching, RRF fusion |
| [Content Curation](content-curation.md) | Research-backed section limits |

### Supporting Services
| Document | Description |
|----------|-------------|
| [JD Parsing](jd-parsing.md) | Job description extraction and normalization |
| [Gap Analysis](gap-analysis.md) | Coverage, certification, and education matching |
| [Skill Management](skill-management.md) | Registry, curation, and O*NET integration |

### Reference
| Document | Description |
|----------|-------------|
| [Configuration](configuration.md) | All config options with examples |
| [Tuning Guide](tuning-guide.md) | Use case recommendations |
| [Troubleshooting](troubleshooting.md) | Common issues and debugging |
| [Changelog](changelog.md) | Version history |

## Algorithm at a Glance

The algorithm combines multiple scoring strategies to select the most relevant Work Units for a resume:

```
                    ┌─────────────────────────┐
                    │      INPUT STAGE        │
                    │                         │
                    │  Job Description (JD)   │
                    │  Work Units (YAML)      │
                    │  Positions (YAML)       │
                    └───────────┬─────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                       SCORING STAGE                                │
│                                                                    │
│   ┌─────────────────┐              ┌─────────────────┐            │
│   │ BM25 Scorer     │              │ Semantic Scorer │            │
│   │ (Lexical)       │              │ (Embeddings)    │            │
│   └────────┬────────┘              └────────┬────────┘            │
│            │                                │                      │
│            └────────────┬───────────────────┘                      │
│                         ▼                                          │
│   ┌─────────────────────────────────────────────────────────────┐ │
│   │               RRF FUSION (k=60)                              │ │
│   │         RRF(d) = Σ weight_i / (k + rank_i(d))               │ │
│   └─────────────────────────┬───────────────────────────────────┘ │
│                             │                                      │
│   ┌─────────────────────────▼───────────────────────────────────┐ │
│   │                    SCORE MODIFIERS                           │ │
│   │   Recency Decay + Seniority Match + Impact Alignment        │ │
│   └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                      CURATION STAGE                                │
│                                                                    │
│   Apply research-backed section limits:                           │
│   • Career highlights: max 4                                      │
│   • Certifications: max 5                                         │
│   • Bullets per position: 4-6 recent, 3-4 mid, 2-3 older         │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │        OUTPUT           │
                    │                         │
                    │  Ranked Work Units      │
                    │  with Match Reasons     │
                    └─────────────────────────┘
```

## Core Concepts

### 1. Hybrid Ranking

The algorithm uses **hybrid ranking** that combines:

- **BM25 (Lexical Matching)** - Keyword-based relevance using TF-IDF principles
- **Semantic Matching (Embeddings)** - Conceptual similarity using neural embeddings
- **Reciprocal Rank Fusion (RRF)** - Combines both rankings robustly

### 2. Score Modifiers

After relevance scoring, the algorithm applies modifiers:

- **Recency Decay** - Recent experience weighted higher (5-year half-life)
- **Seniority Matching** - Aligns work unit seniority to JD requirements
- **Impact Alignment** - Matches achievement types to role expectations

### 3. Content Curation

Research-backed limits ensure resumes aren't overloaded:

- 4 career highlights (executive hybrid format)
- 5 certifications maximum
- 4-6 bullets for recent positions, fewer for older

## Final Score Formula

```
final = (relevance × 0.60) +
        (recency × 0.20) +
        (seniority × 0.10) +
        (impact × 0.10)
```

Where `relevance` is the RRF fusion of BM25 and semantic scores.

## Implementation Files

### Ranking Pipeline
| Component | File | Description |
|-----------|------|-------------|
| Hybrid Ranker | `services/ranker.py` | Main ranking orchestration |
| BM25 Scorer | `services/ranker.py` | Lexical scoring with field weights |
| Embedding Service | `services/embedder.py` | Semantic embeddings and caching |
| Tokenizer | `utils/tokenizer.py` | BM25 tokenization with normalization |
| Seniority Inference | `services/seniority_inference.py` | Title→seniority mapping |
| Impact Classifier | `services/impact_classifier.py` | Outcome→impact category |
| Content Curator | `services/content_curator.py` | Section curation logic |

### Input Processing
| Component | File | Description |
|-----------|------|-------------|
| JD Parser | `services/jd_parser.py` | Extracts structured JD data |
| Work Unit Text | `utils/work_unit_text.py` | Field extraction for ranker |

### Gap Analysis
| Component | File | Description |
|-----------|------|-------------|
| Coverage Analyzer | `services/coverage_analyzer.py` | Skill gap detection |
| Certification Matcher | `services/certification_matcher.py` | Cert requirement matching |
| Education Matcher | `services/education_matcher.py` | Degree requirement matching |

### Skill Management
| Component | File | Description |
|-----------|------|-------------|
| Skill Curator | `services/skill_curator.py` | Skill filtering and ranking |
| Skill Registry | `services/skill_registry.py` | Alias normalization |
| O*NET Service | `services/onet_service.py` | External skill standardization |

## Getting Started

1. **Basic Usage**: Run `resume plan --jd job-description.txt` to see rankings
2. **Configuration**: Adjust weights in `.resume.yaml` (see [Configuration](configuration.md))
3. **Tuning**: See [Tuning Guide](tuning-guide.md) for use case recommendations

## Keeping Docs Updated

When modifying the ranking algorithm:

1. Update the relevant documentation section
2. Add an entry to [Changelog](changelog.md)
3. Update version number if significant change
