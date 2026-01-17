# Gap Analysis

This document explains the gap analysis features that identify what's missing between your resume and a job description.

## Overview

Gap analysis runs **in parallel** with ranking (not as part of it). While the ranker scores and selects work units, the gap analyzers answer: "What does the JD require that you might be missing?"

**Components:**
- **Coverage Analyzer** - Skill coverage (strong/weak/gap)
- **Certification Matcher** - Required certifications
- **Education Matcher** - Degree requirements

---

## Skill Coverage Analysis

**Implementation:** `services/coverage_analyzer.py`

### Coverage Levels

| Level | Symbol | Color | Meaning |
|-------|--------|-------|---------|
| STRONG | ✓ | Green | Skill in tags or skills_demonstrated |
| WEAK | △ | Yellow | Skill mentioned in text but not tagged |
| GAP | ✗ | Red | Skill not found in any work unit |

### Coverage Formula

```
coverage_percentage = (strong_count + weak_count × 0.5) / total_skills × 100
```

**Rationale:** Strong matches count fully, weak matches count half, gaps count zero.

### Algorithm

```python
def analyze_coverage(jd_skills, work_units):
    for skill in jd_skills:
        for wu in work_units:
            # Strong: skill in tags or skills_demonstrated
            if skill in wu.tags or skill in wu.skills_demonstrated:
                match_strength = 2  # STRONG

            # Weak: skill appears anywhere in WU text
            elif skill in extract_work_unit_text(wu):
                match_strength = 1  # WEAK

            else:
                match_strength = 0  # GAP

        # Classify based on best match found
        level = STRONG if strength >= 2 else WEAK if strength >= 1 else GAP
```

### Worked Example

**JD Skills:** `["python", "kubernetes", "terraform", "graphql"]`

**Work Units:**
```yaml
- id: wu-1
  tags: ["python", "kubernetes"]
  skills_demonstrated: ["Docker"]

- id: wu-2
  title: "Built GraphQL API..."  # mentioned in text only
```

**Coverage Report:**

| Skill | Level | Matching WUs |
|-------|-------|--------------|
| python | ✓ STRONG | wu-1 |
| kubernetes | ✓ STRONG | wu-1 |
| terraform | ✗ GAP | - |
| graphql | △ WEAK | wu-2 |

**Coverage:** (2 + 1×0.5) / 4 × 100 = **62.5%**

---

## Certification Matching

**Implementation:** `services/certification_matcher.py`

### Certification Patterns

The matcher recognizes 28+ certification patterns across categories:

**Security:**
```
CISSP, CISM, CISA, CEH, OSCP, GICSP, GSEC, GCIH, GPEN, Security+
```

**Cloud - AWS:**
```
AWS Solutions Architect, AWS Developer, AWS SysOps, AWS DevOps
```

**Cloud - Azure:**
```
Azure Administrator, Azure Developer, Azure Solutions Architect
```

**Cloud - GCP:**
```
GCP Professional, GCP Associate, Google Cloud Professional
```

**Kubernetes:**
```
CKA, CKAD, CKS
```

**Project Management:**
```
PMP, CAPM, CSM, PSM, SAFe
```

**Networking:**
```
CCNA, CCNP, CCIE
```

### Normalization

Certification names are normalized for matching:

1. Collapse whitespace
2. Convert to uppercase
3. Remove level suffixes (ASSOCIATE, PROFESSIONAL, EXPERT)

**Example:**
```
"AWS Solutions Architect - Professional" → "AWS SOLUTIONS ARCHITECT"
"aws solutions architect" → "AWS SOLUTIONS ARCHITECT"
```

### Match Result

```python
@dataclass
class CertificationMatchResult:
    matched: list[str]      # User certs matching JD
    gaps: list[str]         # JD certs user doesn't have
    additional: list[str]   # User certs not in JD
    match_percentage: int   # matched / jd_certs × 100
```

### Algorithm

```python
def match_certifications(user_certs, jd_certs):
    # Normalize both sets
    user_normalized = {normalize(c.name) for c in user_certs}
    jd_normalized = {normalize(c) for c in jd_certs}

    # Set operations
    matched = user_normalized & jd_normalized
    gaps = jd_normalized - user_normalized
    additional = user_normalized - jd_normalized

    # Percentage (no requirements = 100%)
    percentage = 100 if not jd_certs else len(matched) / len(jd_certs) * 100
```

### Worked Example

**JD Text:**
```
Required: CISSP or CISM, AWS Solutions Architect
Preferred: CKA
```

**User Certifications:**
```yaml
- name: "CISSP"
- name: "AWS Solutions Architect Professional"
- name: "PMP"
```

**Result:**
```python
CertificationMatchResult(
    matched=["AWS SOLUTIONS ARCHITECT", "CISSP"],
    gaps=["CKA", "CISM"],
    additional=["PMP"],
    match_percentage=50  # 2 of 4 (CISSP, CISM, AWS, CKA)
)
```

---

## Education Matching

**Implementation:** `services/education_matcher.py`

### Degree Hierarchy

Education levels scored 1-4:

| Level | Score | Patterns |
|-------|-------|----------|
| Associate | 1 | `associate`, `a.a.` |
| Bachelor | 2 | `bachelor`, `bs`, `ba`, `b.s.`, `undergraduate` |
| Master | 3 | `master`, `ms`, `ma`, `mba`, `m.s.` |
| Doctorate | 4 | `phd`, `doctorate`, `doctoral`, `doctor` |

### Field Aliases

Related fields grouped for matching:

**Computer Science:**
```
cs, computing, informatics, software, software engineering,
computer engineering, information technology, it
```

**Engineering:**
```
electrical, electrical engineering, mechanical,
systems engineering, industrial engineering
```

**Cybersecurity:**
```
security, information security, infosec, cyber security, network security
```

**Business:**
```
administration, management, mba, business administration, finance, economics
```

**Mathematics:**
```
math, applied mathematics, statistics, data science
```

### Match Scoring

```python
def find_best_match(user_education, jd_requirement):
    for edu in user_education:
        score = 0

        # Degree level: +10 if meets/exceeds, +5 bonus for exact
        if user_level >= required_level:
            score += 10
        if user_level == required_level:
            score += 5

        # Field relevance: +20 direct, +10 related
        if field_match == "direct":
            score += 20
        elif field_match == "related":
            score += 10

    return highest_scoring_education
```

### Field Relevance

| Relevance | Meaning | Score Bonus |
|-----------|---------|-------------|
| `direct` | Field name in degree | +20 |
| `related` | Same canonical group | +10 |
| `unrelated` | Different field | +0 |
| `unknown` | No field specified | +0 |

### Match Result

```python
@dataclass
class EducationMatchResult:
    meets_requirements: bool
    degree_match: "exceeds" | "meets" | "below" | "unknown"
    field_relevance: "direct" | "related" | "unrelated" | "unknown"
    jd_requirement_text: str | None
    best_match_education: str | None
```

**Pass Criteria:**
- `degree_match` in ("meets", "exceeds")
- AND `field_relevance` in ("direct", "related", "unknown")

### Worked Example

**JD Text:**
```
Required: Bachelor's degree in Computer Science or related field
```

**User Education:**
```yaml
- degree: "Master of Science in Software Engineering"
  institution: "MIT"

- degree: "Bachelor of Arts in History"
  institution: "UCLA"
```

**Analysis:**

| Education | Degree Score | Field Match | Total |
|-----------|--------------|-------------|-------|
| MS Software Engineering | 15 (level 3 > 2) | related (+10) | 25 |
| BA History | 15 (level 2 = 2) | unrelated (+0) | 15 |

**Result:**
```python
EducationMatchResult(
    meets_requirements=True,
    degree_match="exceeds",      # Master's > Bachelor's
    field_relevance="related",   # Software Eng ∈ CS group
    jd_requirement_text="Bachelor's in Computer Science",
    best_match_education="Master of Science in Software Engineering",
)
```

---

## Integration with Plan Command

The plan command runs all three analyzers and displays results:

```
┌──────────────────────────────────────────────────────────────┐
│                    SKILL COVERAGE                             │
├──────────────────────────────────────────────────────────────┤
│ ✓ python        ✓ kubernetes    △ graphql      ✗ terraform   │
│                                                               │
│ Coverage: 62.5% (2 strong, 1 weak, 1 gap)                    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                 CERTIFICATION MATCH                           │
├──────────────────────────────────────────────────────────────┤
│ ✓ Matched: CISSP, AWS Solutions Architect                    │
│ ✗ Gaps: CKA, CISM                                            │
│ + Additional: PMP                                             │
│                                                               │
│ Match: 50%                                                    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                   EDUCATION MATCH                             │
├──────────────────────────────────────────────────────────────┤
│ Requirement: Bachelor's in Computer Science                   │
│ Your Match: MS Software Engineering (exceeds, related)        │
│                                                               │
│ Status: ✓ Meets Requirements                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Not Part of Ranking

These analyzers are **informational only**. They don't affect work unit scores:

| What Affects Ranking | What Doesn't |
|---------------------|--------------|
| BM25 relevance | Coverage analysis |
| Semantic similarity | Certification gaps |
| Recency decay | Education match |
| Seniority alignment | |
| Impact classification | |

The gap analysis helps you understand what to add or emphasize, but the ranking algorithm independently selects the best work units based on relevance.
