# Job Description Parsing

This document explains how Job Descriptions (JDs) are parsed and structured for use by the ranking and matching algorithms.

## Overview

The JD Parser (`services/jd_parser.py`) extracts structured data from raw job description text, enabling precise matching against work units.

**Output:** A `JobDescription` model containing:
- Title
- Skills (normalized)
- Requirements (with required/nice-to-have classification)
- Experience level
- Years of experience
- High-frequency keywords

---

## Parsing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         JD TEXT INPUT                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTRACTION STAGE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │ Title        │  │ Skills       │  │ Requirements │                   │
│  │ Extraction   │  │ Detection    │  │ Extraction   │                   │
│  │              │  │              │  │              │                   │
│  │ First 5 lines│  │ 67 keywords  │  │ Bullet points│                   │
│  │ Role keywords│  │ + variants   │  │ Required vs  │                   │
│  │              │  │              │  │ nice-to-have │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │ Experience   │  │ Years        │  │ Keywords     │                   │
│  │ Level        │  │ Extraction   │  │ Frequency    │                   │
│  │              │  │              │  │              │                   │
│  │ Title + text │  │ Pattern match│  │ Word counter │                   │
│  │ indicators   │  │ "5+ years"   │  │ Top 20 terms │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       JobDescription Model                               │
├─────────────────────────────────────────────────────────────────────────┤
│  raw_text: str           # Original text                                │
│  title: str | None       # Extracted job title                          │
│  skills: list[str]       # Normalized skill names                       │
│  requirements: list[Req] # Bullets with required flag                   │
│  experience_level: Enum  # ENTRY, MID, SENIOR, etc.                     │
│  years_experience: int   # Years required (e.g., 5)                     │
│  keywords: list[str]     # High-frequency terms                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Title Extraction

Searches the first 5 lines for role-indicating keywords.

**Configuration:**
```python
MAX_TITLE_LENGTH = 100      # Skip lines longer than this
MAX_TITLE_SEARCH_LINES = 5  # Only check first N lines
```

**Title Keywords:**
```python
["engineer", "developer", "manager", "analyst", "designer", "architect"]
```

**Algorithm:**
1. Split text into first 5 lines
2. Skip empty lines and headers ("About", "Company", "Location")
3. Return first line < 100 chars containing a title keyword

**Example:**
```
Input:
  Senior Software Engineer
  Acme Corporation - San Francisco, CA
  About the Role...

Output: "Senior Software Engineer"
```

---

## Skill Detection

Detects 67+ technical skills with variant normalization.

### Skill Keywords (67 entries)

```python
SKILL_KEYWORDS = {
    # Languages
    "python", "java", "javascript", "typescript", "go", "golang",
    "rust", "c++", "c#", "ruby", "php", "scala", "kotlin", "swift",

    # Frameworks
    "react", "vue", "angular", "nodejs", "django", "flask",
    "fastapi", "spring", "rails", "express", "nextjs",

    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "jenkins", "github actions", "gitlab", "cicd",

    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",

    # Messaging
    "kafka", "rabbitmq",

    # APIs
    "graphql", "rest", "grpc",

    # Systems
    "linux", "unix", "bash", "shell", "git",

    # Process
    "agile", "scrum", "jira",

    # AI/ML
    "machine learning", "ml", "ai", "deep learning", "nlp",
    "data science", "pandas", "numpy", "tensorflow", "pytorch",

    # General
    "sql", "nosql", "api", "microservices",
}
```

### Skill Normalizations (30+ mappings)

Maps variants to canonical names:

| Variant | Canonical |
|---------|-----------|
| `python 3`, `python3`, `py` | `python` |
| `js`, `ecmascript`, `es6` | `javascript` |
| `node.js`, `node` | `nodejs` |
| `amazon web services` | `aws` |
| `google cloud`, `google cloud platform` | `gcp` |
| `k8s`, `kube` | `kubernetes` |
| `containers` | `docker` |
| `postgres`, `psql` | `postgresql` |
| `mongo` | `mongodb` |
| `ci/cd`, `ci cd`, `continuous integration` | `cicd` |
| `tf` | `terraform` |
| `react.js`, `reactjs` | `react` |

**Algorithm:**
1. Check for direct skill keyword matches (word boundary)
2. Check for variant matches and normalize
3. Return sorted list of unique canonical skill names

---

## Requirements Extraction

Extracts bullet points and classifies as required vs nice-to-have.

**Patterns:**
```python
patterns = [
    r"^[\s]*[-•*]\s+(.+)$",   # Bullet points: - • *
    r"^[\s]*\d+[.)]\s+(.+)$", # Numbered lists: 1. 2)
]
```

**Section Detection:**
```python
nice_to_have_phrases = ["nice to have", "preferred", "bonus", "plus"]
required_phrases = ["required", "must have", "requirements"]
```

**Algorithm:**
1. Track current section (required by default)
2. Switch to nice-to-have when detecting preference phrases
3. Switch back to required when detecting requirement phrases
4. Extract bullet text and classify by current section

**Example:**
```
Requirements:
- 5+ years Python experience         → Requirement(is_required=True)
- Strong communication skills        → Requirement(is_required=True)

Nice to have:
- AWS certification                  → Requirement(is_required=False)
- Experience with GraphQL            → Requirement(is_required=False)
```

---

## Experience Level Detection

Infers seniority from title and text using level indicators.

### Level Indicators

| Pattern | Level |
|---------|-------|
| `junior`, `entry`, `entry-level`, `associate` | ENTRY |
| `mid`, `mid-level`, `intermediate` | MID |
| `senior`, `sr.`, `sr` | SENIOR |
| `staff` | STAFF |
| `lead`, `tech lead`, `team lead` | LEAD |
| `principal`, `architect`, `distinguished` | PRINCIPAL |
| `director`, `vp`, `head of`, `cto` | EXECUTIVE |

**Algorithm:**
1. Check title first (most reliable)
2. Check full text for indicators
3. Default to MID if no indicators found

**Example:**
```
Title: "Senior Platform Engineer"
→ Level: SENIOR (matched "senior" in title)

Title: "Software Developer"
Text: "...looking for an experienced mid-level developer..."
→ Level: MID (matched "mid-level" in text)
```

---

## Years of Experience Extraction

Extracts numeric years requirement using pattern matching.

**Patterns:**
```python
patterns = [
    r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?experience",
    r"experience:\s*(\d+)\+?\s*(?:years?|yrs?)",
    r"minimum\s+(\d+)\s*(?:years?|yrs?)",
]
```

**Examples:**
- `"5+ years of experience"` → 5
- `"minimum 3 years"` → 3
- `"Experience: 7 yrs"` → 7

---

## Keyword Extraction

Identifies high-frequency terms for ranking.

**Configuration:**
```python
MIN_KEYWORD_LENGTH = 3     # Minimum word length
MIN_KEYWORD_FREQUENCY = 2  # Minimum occurrences
MAX_KEYWORDS = 20          # Maximum to return
```

**Stop Words (75 entries):**
Common English words filtered out: `the`, `a`, `an`, `and`, `or`, `but`, `in`, `on`, `at`, `to`, `for`, `of`, `with`, `by`, `from`, `as`, `is`, `was`, `are`, `were`...

**Algorithm:**
1. Extract all words (lowercase, alphabetic)
2. Filter by minimum length (> 3 chars)
3. Remove stop words
4. Count frequency using `Counter`
5. Return top 20 words with frequency >= 2

**Example:**
```
JD Text: "We need a Python engineer with Python experience.
         Strong Python skills and cloud expertise required."

Keywords: ["python", "engineer", "cloud", "experience", "skills"]
```

---

## Configuration Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `MAX_TITLE_LENGTH` | 100 | Skip lines longer than this for title |
| `MAX_TITLE_SEARCH_LINES` | 5 | Only check first N lines for title |
| `MIN_REQUIREMENT_LENGTH` | 10 | Skip requirements shorter than this |
| `MIN_KEYWORD_LENGTH` | 3 | Minimum word length for keywords |
| `MIN_KEYWORD_FREQUENCY` | 2 | Minimum occurrences for keyword |
| `MAX_KEYWORDS` | 20 | Maximum keywords to return |

---

## Usage in Algorithm

The parsed JD feeds into multiple algorithm components:

| Component | JD Fields Used |
|-----------|---------------|
| **HybridRanker** | `raw_text`, `skills`, `keywords` |
| **CoverageAnalyzer** | `skills` |
| **CertificationMatcher** | `raw_text` |
| **EducationMatcher** | `raw_text` |
| **SeniorityInference** | `experience_level` |
| **SkillCurator** | `keywords` |

---

## Worked Example

**Input JD:**
```
Senior Backend Engineer
TechCorp Inc.

About the Role:
We're looking for a Senior Backend Engineer with strong Python and
Kubernetes experience to join our platform team.

Requirements:
- 5+ years experience with Python or Go
- Strong knowledge of Docker and Kubernetes
- Experience with AWS or GCP
- Excellent communication skills

Nice to Have:
- Experience with Kafka
- AWS Solutions Architect certification
```

**Parsed Output:**
```python
JobDescription(
    raw_text="Senior Backend Engineer\nTechCorp Inc...",
    title="Senior Backend Engineer",
    skills=["aws", "docker", "gcp", "go", "kubernetes", "python"],
    requirements=[
        Requirement(text="5+ years experience with Python or Go", is_required=True),
        Requirement(text="Strong knowledge of Docker and Kubernetes", is_required=True),
        Requirement(text="Experience with AWS or GCP", is_required=True),
        Requirement(text="Excellent communication skills", is_required=True),
        Requirement(text="Experience with Kafka", is_required=False),
        Requirement(text="AWS Solutions Architect certification", is_required=False),
    ],
    experience_level=ExperienceLevel.SENIOR,
    years_experience=5,
    keywords=["experience", "senior", "engineer", "backend", "python", ...],
)
```
