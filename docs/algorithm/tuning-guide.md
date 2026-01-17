# Tuning Guide

This guide provides concrete configuration recommendations for different use cases.

## Use Case Recommendations

### Executive vs IC Resumes

#### Executive (CTO, VP, Director)

Executives benefit from emphasizing organizational impact, strategic achievements, and leadership scope.

```yaml
scoring_weights:
  # Slightly reduce recency emphasis - experience depth matters
  recency_half_life: 10.0
  recency_blend: 0.15

  # Increase seniority and impact emphasis
  seniority_blend: 0.15
  impact_blend: 0.15
  quantified_boost: 1.25

  # Enable sectioned semantic for precise matching
  use_sectioned_semantic: true

curation:
  # Executive gets more board roles
  board_roles_max: 5
  board_roles_executive_max: 5

  # Emphasize career highlights
  career_highlights_max: 4

  # Moderate bullet reduction for older roles
  bullets_per_position:
    recent_years: 3
    recent_max: 5
    mid_years: 7
    mid_max: 3
    older_max: 2
```

**Rationale:**
- Longer recency half-life values broad experience over just recent work
- Higher seniority/impact blend emphasizes leadership achievements
- More board roles appropriate for executive positioning

#### Individual Contributor (Engineer, Analyst)

ICs benefit from emphasizing technical skills, recent projects, and hands-on accomplishments.

```yaml
scoring_weights:
  # Emphasize recent experience
  recency_half_life: 5.0
  recency_blend: 0.25

  # De-emphasize seniority matching
  seniority_blend: 0.05
  impact_blend: 0.10

  # Skills field gets higher weight
  skills_weight: 2.0
  title_weight: 1.5

curation:
  # Fewer board roles for IC
  board_roles_max: 2

  # More skills displayed
  skills_max: 12

  # More bullets for recent positions
  bullets_per_position:
    recent_years: 3
    recent_max: 6
    mid_years: 7
    mid_max: 4
    older_max: 3
```

**Rationale:**
- Recent skills matter more in fast-moving technical fields
- Skills field weight increased for technical role matching
- Lower seniority emphasis allows matching across levels

---

### Technical vs Non-Technical Roles

#### Technical (Engineer, Architect, Data Scientist)

```yaml
scoring_weights:
  # Skills are critical for technical roles
  skills_weight: 2.0
  title_weight: 1.5
  experience_weight: 1.0

  # Strong semantic matching for technical concepts
  semantic_weight: 1.2
  bm25_weight: 0.8

  # Technical roles emphasize operational/technical impact
  impact_blend: 0.12
  quantified_boost: 1.30

curation:
  # More skills for technical roles
  skills_max: 15

  # Technical certs are valuable
  certifications_max: 6
```

**Rationale:**
- Technical skills are the primary filter for engineering roles
- Semantic matching helps match conceptual equivalents (k8s ↔ containerization)
- Higher quantified boost rewards measurable technical achievements

#### Non-Technical (PM, Marketing, Operations)

```yaml
scoring_weights:
  # Title matters more than skills
  title_weight: 2.5
  skills_weight: 1.0
  experience_weight: 1.2

  # Standard BM25/semantic balance
  bm25_weight: 1.0
  semantic_weight: 1.0

  # Seniority matching is important
  seniority_blend: 0.12

curation:
  # Fewer technical skills
  skills_max: 8

  # More emphasis on career narrative
  career_highlights_max: 4
  bullets_per_position:
    recent_max: 5
```

**Rationale:**
- Job titles are more differentiated in non-technical roles
- Seniority alignment matters for role hierarchy
- Career highlights tell the leadership story

---

### Career Changers

Career changers need to emphasize transferable skills and conceptual similarity over exact keyword matches.

```yaml
scoring_weights:
  # Heavy emphasis on semantic (conceptual) matching
  semantic_weight: 1.5
  bm25_weight: 0.5

  # Disable or minimize seniority matching
  use_seniority_matching: false
  # OR: seniority_blend: 0.02

  # Don't penalize old experience
  recency_half_life: 15.0
  recency_blend: 0.10

  # Enable sectioned semantic for transferable skills matching
  use_sectioned_semantic: true
  section_outcome_weight: 0.5  # Emphasize results
  section_skills_weight: 0.3   # Emphasize skills
  section_actions_weight: 0.15
  section_title_weight: 0.05

curation:
  # Lower relevance threshold to include more experience
  min_relevance_score: 0.15
```

**Rationale:**
- Semantic matching finds conceptual equivalents across domains
- Disabling seniority matching prevents level mismatch penalties
- Lower relevance threshold includes broader experience
- Emphasizing outcomes shows transferable achievements

---

### Entry-Level Positions

Entry-level candidates have limited work experience; education and internships matter more.

```yaml
scoring_weights:
  # Recent education and internships matter most
  recency_half_life: 3.0
  recency_blend: 0.30

  # Disable seniority matching (entry-level is expected)
  use_seniority_matching: false

  # Impact matching less relevant for entry-level
  impact_blend: 0.05

curation:
  # Fewer bullets are fine for limited experience
  bullets_per_position:
    recent_years: 3
    recent_max: 4
    mid_years: 7
    mid_max: 3
    older_max: 2

  # Lower relevance threshold
  min_relevance_score: 0.15
```

**Rationale:**
- Short recency half-life emphasizes recent education/internships
- Seniority matching disabled since entry-level is expected
- Lower bullet limits match limited experience

---

### Industry-Specific Tuning

#### Fast-Moving Tech (Startups, AI/ML)

```yaml
scoring_weights:
  recency_half_life: 3.0      # Recent experience critical
  recency_blend: 0.30
  skills_weight: 2.0           # Skills over titles
  quantified_boost: 1.35       # Metrics matter

curation:
  skills_max: 15
  certifications_max: 6
```

#### Traditional Industries (Finance, Legal, Healthcare)

```yaml
scoring_weights:
  recency_half_life: 10.0     # Experience depth valued
  recency_blend: 0.15
  title_weight: 2.5            # Titles and hierarchy matter
  seniority_blend: 0.15        # Level matching important

curation:
  board_roles_max: 4
  publications_max: 4
```

#### Consulting/Professional Services

```yaml
scoring_weights:
  recency_half_life: 7.0
  recency_blend: 0.20
  impact_blend: 0.15           # Client impact matters
  quantified_boost: 1.30

curation:
  career_highlights_max: 5     # Story matters
  skills_max: 10
```

---

## Quick Reference Matrix

| Scenario | BM25:Semantic | Recency HL | Seniority | Impact | Key Adjustments |
|----------|---------------|------------|-----------|--------|-----------------|
| Executive | 1.0:1.0 | 10.0 | 0.15 | 0.15 | More board roles, fewer bullets |
| IC Engineer | 0.8:1.2 | 5.0 | 0.05 | 0.10 | Higher skills weight, more skills |
| Career Changer | 0.5:1.5 | 15.0 | disabled | 0.10 | Semantic emphasis, lower threshold |
| Entry Level | 1.0:1.0 | 3.0 | disabled | 0.05 | Fewer bullets, recent focus |
| Tech Startup | 0.8:1.2 | 3.0 | 0.08 | 0.12 | Skills heavy, recency critical |
| Traditional | 1.0:1.0 | 10.0 | 0.15 | 0.12 | Title emphasis, experience depth |

---

## Tuning Process

### Step 1: Identify Your Scenario

Start with the closest preset above, then adjust based on:
- Target industry and company culture
- Specific JD requirements
- Your unique background

### Step 2: Run Plan with Verbose Output

```bash
resume plan --jd job-description.txt --verbose
```

Review the output:
- Are relevant work units ranking high?
- Are the match reasons sensible?
- Are appropriate items being curated?

### Step 3: Adjust Weights

Common adjustments:
- **Rankings seem off?** Adjust BM25/semantic balance
- **Old experience penalized too much?** Increase recency_half_life
- **Seniority mismatch?** Disable or adjust seniority_blend
- **Wrong items curated?** Adjust min_relevance_score

### Step 4: Validate and Iterate

```bash
resume plan --jd job-description.txt
resume build --jd job-description.txt
```

Review the generated resume and iterate until satisfied.

---

## Common Mistakes

### Over-Tuning

**Problem:** Tweaking weights too aggressively for a single JD.

**Solution:** Use moderate adjustments. The algorithm is designed to work well with defaults; large changes can cause unexpected results.

### Ignoring Defaults

**Problem:** Changing everything at once without understanding the impact.

**Solution:** Start with defaults, change one parameter at a time, observe results.

### Wrong Abstraction Level

**Problem:** Trying to fix content issues with algorithm tuning.

**Solution:** If your work units don't match the JD conceptually, no algorithm tuning will help. Ensure your work units are well-written with strong outcomes and relevant skills.

---

## When to Tune vs. When to Fix Content

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Wrong work units selected | Weak work unit content | Improve work unit titles/outcomes |
| Right work units, wrong order | Algorithm weights | Tune scoring weights |
| Too few items selected | High threshold | Lower min_relevance_score |
| Too many irrelevant items | Low threshold | Raise min_relevance_score |
| Skills not matching | Abbreviation mismatch | Tokenizer handles this; check tags |
| Seniority mismatches | Level inference wrong | Add explicit seniority_level to WU |
