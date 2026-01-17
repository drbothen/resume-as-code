# Skill Management

This document explains the skill normalization, curation, and standardization pipeline that produces the skills section of your resume.

## Overview

Skills flow through three components before appearing on your resume:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SKILL EXTRACTION                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Work Units → tags[] + skills_demonstrated[] → Raw Skills Set           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      SKILL REGISTRY                                      │
│                   services/skill_registry.py                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Purpose: Normalize aliases to canonical names                          │
│                                                                          │
│  "k8s" → "Kubernetes"                                                   │
│  "ts" → "TypeScript"                                                    │
│  "py" → "Python"                                                        │
│                                                                          │
│  Optional: O*NET lookup for unknown skills                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      SKILL CURATOR                                       │
│                   services/skill_curator.py                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  5-Step Pipeline:                                                        │
│                                                                          │
│  1. Normalize & Deduplicate (case-insensitive)                          │
│  2. Filter Excluded (config-based)                                      │
│  3. Score by Relevance (JD match)                                       │
│  4. Sort by Score (prioritized → JD match → others)                     │
│  5. Limit to Max Count                                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      RESUME OUTPUT                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Skills: Python, Kubernetes, Docker, AWS, Terraform, ...                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Skill Registry

**Implementation:** `services/skill_registry.py`

### Purpose

Maps skill aliases to canonical display names for consistent resume rendering and improved JD matching.

### How It Works

```python
registry = SkillRegistry.load_default()

registry.normalize("k8s")        # → "Kubernetes"
registry.normalize("ts")         # → "TypeScript"
registry.normalize("UnknownLib") # → "UnknownLib" (passthrough)

registry.get_aliases("kubernetes")
# → {"kubernetes", "k8s", "kube"}
```

### Data Structure

Entries stored in `data/skills.yaml`:

```yaml
skills:
  - canonical: "Kubernetes"
    aliases: ["k8s", "kube"]
    category: "DevOps"
    onet_code: "2.A.1.a"

  - canonical: "TypeScript"
    aliases: ["ts"]
    category: "Languages"
```

### Collision Handling

If the same alias maps to multiple canonical names, the registry warns:

```
UserWarning: Skill alias collision: 'ml' maps to both
'Machine Learning' and 'ML Framework'. Using 'ML Framework'.
```

### O*NET Integration

When a skill isn't found locally, the registry can query O*NET:

```python
registry = SkillRegistry(
    entries=local_entries,
    onet_service=ONetService(config),
    user_skills_path=Path("~/.config/resume-as-code/skills.yaml"),
)

entry = registry.lookup_and_cache("data engineering")
# 1. Search O*NET for occupations matching "data engineering"
# 2. Get skills from top occupation
# 3. Create new SkillEntry
# 4. Add to registry
# 5. Persist to user skills file
```

---

## Skill Curator

**Implementation:** `services/skill_curator.py`

### Purpose

Selects which skills appear on the resume based on JD relevance, configuration, and limits.

### 5-Step Pipeline

```python
curator = SkillCurator(
    max_count=15,
    exclude=["Microsoft Office", "Windows"],
    prioritize=["Python", "Kubernetes"],
    registry=skill_registry,
)

result = curator.curate(
    raw_skills={"python", "k8s", "docker", "MS Office", ...},
    jd_keywords={"python", "kubernetes", "aws"},
)
```

#### Step 1: Normalize & Deduplicate

- Apply registry normalization (`k8s` → `Kubernetes`)
- Case-insensitive deduplication
- Prefer: Title Case > UPPERCASE > lowercase

```python
input:  {"python", "Python", "PYTHON"}
output: {"python": "Python"}  # Title case preferred
```

#### Step 2: Filter Excluded

Remove skills in the exclude list:

```python
exclude = {"microsoft office", "windows"}

input:  {"python": "Python", "ms office": "MS Office"}
output: {"python": "Python"}
excluded: [("MS Office", "config_exclude")]
```

#### Step 3: Score by Relevance

```python
scoring:
  - 100 points: prioritized skills
  -  10 points: JD keyword matches
  -   1 point:  all others
```

#### Step 4: Sort by Score

```python
sort_key = (-score, alphabetical)

# Prioritized first, then JD matches, then alphabetical
```

#### Step 5: Limit to Max Count

```python
included = sorted_skills[:max_count]
excluded += [(s, "exceeded_max_display") for s in sorted_skills[max_count:]]
```

### Curation Result

```python
@dataclass
class CurationResult:
    included: list[str]              # Skills to display
    excluded: list[tuple[str, str]]  # (skill, reason) pairs
    stats: dict[str, int]            # Pipeline statistics
```

**Example Output:**
```python
CurationResult(
    included=["Python", "Kubernetes", "Docker", "AWS", ...],
    excluded=[
        ("MS Office", "config_exclude"),
        ("Basic SQL", "exceeded_max_display"),
    ],
    stats={
        "total_raw": 25,
        "after_dedup": 20,
        "after_filter": 18,
        "included": 15,
        "excluded": 3,
    },
)
```

### JD Keyword Expansion

When registry is available, JD keywords are expanded with aliases:

```python
jd_keywords = {"kubernetes"}

# After expansion with registry:
expanded = {"kubernetes", "k8s", "kube"}

# Now "k8s" in raw_skills will match JD requirement
```

---

## O*NET Service

**Implementation:** `services/onet_service.py`

### Purpose

External skill standardization using the U.S. Department of Labor's O*NET database.

### Configuration

```yaml
onet:
  enabled: true
  api_key: null           # Or set ONET_API_KEY env var
  cache_ttl: 86400        # 24 hours
  timeout: 10.0           # Seconds
  retry_delay_ms: 200     # Minimum delay between retries
```

### API v2.0

Uses X-API-Key header authentication:

```python
headers = {"X-API-Key": api_key}
base_url = "https://api-v2.onetcenter.org"
```

### Search Occupations

```python
service = ONetService(config)

occupations = service.search_occupations("python")
# Returns: [ONetOccupation(code="15-1252.00", title="Software Developer", score=95.2)]
```

### Get Occupation Skills

```python
skills = service.get_occupation_skills("15-1252.00")
# Returns: [
#   ONetSkill(id="2.A.2.b", name="Programming", importance=4.5, level=5.2),
#   ONetSkill(id="2.B.3.e", name="Computers and Electronics", ...),
# ]
```

### Caching

Responses cached to disk with configurable TTL:

```
~/.cache/resume-as-code/onet/
├── a1b2c3d4...json  # search:python
├── e5f6g7h8...json  # skills:15-1252.00
```

Cache key: SHA256 of query (first 32 chars)

### Retry with Backoff

O*NET rate limits require minimum 200ms between retries:

```python
retry_delays = [200ms, 400ms, 800ms]  # Exponential backoff
```

Handles:
- 429 (Rate Limited) - Retry with backoff
- 5xx (Server Error) - Retry with backoff
- 4xx (Client Error) - No retry (except 429)
- Timeout - Retry with backoff

### Graceful Degradation

When O*NET is unavailable:
- `search_occupations()` returns `[]`
- `get_occupation_skills()` returns `[]`
- Skill registry falls back to local data only

---

## Configuration Reference

### Skills Config

```yaml
skills:
  max_count: 15          # Maximum skills to display
  exclude:               # Skills to never show
    - "Microsoft Office"
    - "Windows"
  prioritize:            # Skills to always show first
    - "Python"
    - "Kubernetes"
```

### O*NET Config

```yaml
onet:
  enabled: true          # Enable O*NET integration
  api_key: null          # API key (or ONET_API_KEY env)
  cache_ttl: 86400       # Cache TTL in seconds (24h)
  timeout: 10.0          # Request timeout in seconds
  retry_delay_ms: 200    # Minimum retry delay (O*NET requirement)
```

---

## Worked Example

**Input:**
- Raw skills from work units: `{"python", "Python", "k8s", "Docker", "AWS", "MS Office", "Git", "Linux", "React", "GraphQL", "Terraform", "Jenkins", "Ansible", "Chef", "Puppet", "Nagios", "Prometheus"}`
- JD keywords: `{"python", "kubernetes", "aws", "terraform"}`
- Config: `max_count=10, exclude=["MS Office"]`

**Processing:**

| Step | Action | Result |
|------|--------|--------|
| 1 | Normalize | `k8s` → `Kubernetes` |
| 1 | Deduplicate | `python`, `Python` → `Python` |
| 2 | Filter | Remove `MS Office` |
| 3 | Score | Python=100 (prioritized), Kubernetes=10, AWS=10, Terraform=10, Docker=1, ... |
| 4 | Sort | By score desc, then alpha |
| 5 | Limit | Take first 10 |

**Output:**
```
included: [Python, AWS, Kubernetes, Terraform, Ansible, Chef, Docker, Git, Jenkins, Linux]
excluded: [(MS Office, config_exclude), (Nagios, exceeded_max_display), ...]
```

---

## Relationship to Ranking

Skill management is **post-ranking**:

1. **Ranker** selects work units based on JD relevance
2. **Skills extracted** from selected work units
3. **Registry** normalizes skill names
4. **Curator** filters and prioritizes for display

The curator uses JD keywords to prioritize relevant skills, but this doesn't affect which work units were selected.
