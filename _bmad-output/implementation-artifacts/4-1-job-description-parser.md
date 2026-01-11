# Story 4.1: Job Description Parser

Status: done

## Story

As a **developer**,
I want **to extract structured information from job descriptions**,
So that **the ranking algorithm has clean data to work with**.

## Acceptance Criteria

1. **Given** a plain text job description file
   **When** the parser processes it
   **Then** it extracts a list of skills/technologies mentioned
   **And** it extracts key requirements and responsibilities
   **And** it identifies experience level indicators (senior, staff, lead, etc.)

2. **Given** a JD with varied formatting (bullets, paragraphs, sections)
   **When** the parser processes it
   **Then** it handles all formats gracefully
   **And** extracts meaningful content regardless of structure

3. **Given** a JD file path
   **When** I pass it to the parser
   **Then** the file is read and parsed
   **And** a `JobDescription` model is returned with extracted data

4. **Given** the parser extracts skills
   **When** I inspect the output
   **Then** skills are normalized (e.g., "Python 3" → "python", "K8s" → "kubernetes")

## Tasks / Subtasks

- [x] Task 1: Create JobDescription model (AC: #1, #3)
  - [x] 1.1: Create `src/resume_as_code/models/job_description.py`
  - [x] 1.2: Define `JobDescription` Pydantic model with fields
  - [x] 1.3: Add `raw_text` field for original content
  - [x] 1.4: Add `skills` list field for extracted skills
  - [x] 1.5: Add `requirements` list for key requirements
  - [x] 1.6: Add `experience_level` field (entry, mid, senior, staff, lead, principal)
  - [x] 1.7: Add `title` field for job title

- [x] Task 2: Create JD parser service (AC: #1, #2, #3)
  - [x] 2.1: Create `src/resume_as_code/services/jd_parser.py`
  - [x] 2.2: Implement `parse_jd_file(path: Path) -> JobDescription`
  - [x] 2.3: Implement `parse_jd_text(text: str) -> JobDescription`
  - [x] 2.4: Handle various file encodings gracefully
  - [x] 2.5: Extract sections from common JD structures

- [x] Task 3: Implement skill extraction (AC: #1, #4)
  - [x] 3.1: Create skill keyword list (common technologies)
  - [x] 3.2: Implement regex-based skill extraction
  - [x] 3.3: Implement skill normalization mapping
  - [x] 3.4: Handle skill variations and abbreviations

- [x] Task 4: Implement experience level detection (AC: #1)
  - [x] 4.1: Define experience level indicators
  - [x] 4.2: Detect level from job title
  - [x] 4.3: Detect level from requirements section
  - [x] 4.4: Handle ambiguous cases (default to "mid")

- [x] Task 5: Implement requirements extraction (AC: #1, #2)
  - [x] 5.1: Detect common requirement patterns
  - [x] 5.2: Extract bullet points and numbered lists
  - [x] 5.3: Separate "required" vs "nice-to-have" where indicated
  - [x] 5.4: Clean and normalize extracted text

- [x] Task 6: Code quality verification
  - [x] 6.1: Run `ruff check src tests --fix`
  - [x] 6.2: Run `ruff format src tests`
  - [x] 6.3: Run `mypy src --strict` with zero errors
  - [x] 6.4: Add unit tests for skill extraction
  - [x] 6.5: Add unit tests for experience level detection
  - [x] 6.6: Add integration tests with sample JD files

## Dev Notes

### Architecture Compliance

This is an enabling story for the plan command (Story 4.3). It provides the foundation for JD analysis that feeds into the ranking engine.

**Source:** [epics.md#Story 4.1](_bmad-output/planning-artifacts/epics.md)
**Source:** [Architecture Section 3.2 - Data Architecture](_bmad-output/planning-artifacts/architecture.md)

### Dependencies

This story REQUIRES:
- Story 1.1 (Project Scaffolding) - Base project structure
- Story 1.4 (Error Handling) - Exception handling

This story ENABLES:
- Story 4.2 (BM25 Ranking Engine) - Consumes parsed JD
- Story 4.3 (Plan Command) - Uses JD model

### JobDescription Model

**`src/resume_as_code/models/job_description.py`:**

```python
"""Job Description model for parsed JD data."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ExperienceLevel(str, Enum):
    """Experience level indicators."""

    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    LEAD = "lead"
    PRINCIPAL = "principal"
    EXECUTIVE = "executive"


class Requirement(BaseModel):
    """A single requirement from the JD."""

    text: str = Field(..., description="The requirement text")
    is_required: bool = Field(
        default=True,
        description="True if required, False if nice-to-have",
    )
    category: str | None = Field(
        default=None,
        description="Category: technical, soft_skill, education, etc.",
    )


class JobDescription(BaseModel):
    """Parsed job description with extracted information."""

    raw_text: str = Field(..., description="Original JD text")
    title: str | None = Field(default=None, description="Job title if detected")
    company: str | None = Field(default=None, description="Company name if detected")

    skills: list[str] = Field(
        default_factory=list,
        description="Normalized list of skills/technologies",
    )

    requirements: list[Requirement] = Field(
        default_factory=list,
        description="Extracted requirements",
    )

    experience_level: ExperienceLevel = Field(
        default=ExperienceLevel.MID,
        description="Detected experience level",
    )

    years_experience: int | None = Field(
        default=None,
        description="Required years of experience if specified",
    )

    keywords: list[str] = Field(
        default_factory=list,
        description="High-frequency keywords for ranking",
    )

    @property
    def text_for_ranking(self) -> str:
        """Get combined text for BM25/semantic ranking."""
        parts = [self.raw_text]
        if self.title:
            parts.insert(0, self.title)
        return " ".join(parts)
```

### JD Parser Service

**`src/resume_as_code/services/jd_parser.py`:**

```python
"""Job Description parser service."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from resume_as_code.models.errors import NotFoundError
from resume_as_code.models.job_description import (
    ExperienceLevel,
    JobDescription,
    Requirement,
)

# Parser configuration constants
MAX_TITLE_LENGTH = 100  # Skip lines longer than this when detecting title
MAX_TITLE_SEARCH_LINES = 5  # Only check first N lines for title
MIN_REQUIREMENT_LENGTH = 10  # Skip requirements shorter than this
MIN_KEYWORD_LENGTH = 3  # Minimum word length for keyword extraction
MIN_KEYWORD_FREQUENCY = 2  # Minimum occurrences to include as keyword
MAX_KEYWORDS = 20  # Maximum keywords to return

# Skill normalization mapping
SKILL_NORMALIZATIONS: dict[str, str] = {
    # Python variants
    "python 3": "python",
    "python3": "python",
    "py": "python",
    # JavaScript variants
    "javascript": "javascript",
    "js": "javascript",
    "ecmascript": "javascript",
    "es6": "javascript",
    "node.js": "nodejs",
    "node": "nodejs",
    # Cloud
    "amazon web services": "aws",
    "azure": "azure",
    "gcp": "gcp",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    # Kubernetes
    "k8s": "kubernetes",
    "kube": "kubernetes",
    # Containers
    "docker": "docker",
    "containers": "docker",
    # Databases
    "postgres": "postgresql",
    "psql": "postgresql",
    "mysql": "mysql",
    "mongodb": "mongodb",
    "mongo": "mongodb",
    "redis": "redis",
    # Other
    "ci/cd": "cicd",
    "ci cd": "cicd",
    "continuous integration": "cicd",
    "terraform": "terraform",
    "tf": "terraform",
    "react.js": "react",
    "reactjs": "react",
    "vue.js": "vue",
    "vuejs": "vue",
    "angular.js": "angular",
    "angularjs": "angular",
}

# Common technical skills to detect
SKILL_KEYWORDS: set[str] = {
    "python", "java", "javascript", "typescript", "go", "golang", "rust",
    "c++", "c#", "ruby", "php", "scala", "kotlin", "swift",
    "react", "vue", "angular", "nodejs", "django", "flask", "fastapi",
    "spring", "rails", "express", "nextjs",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "jenkins", "github actions", "gitlab", "cicd",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "kafka", "rabbitmq", "graphql", "rest", "grpc",
    "linux", "unix", "bash", "shell",
    "git", "agile", "scrum", "jira",
    "machine learning", "ml", "ai", "deep learning", "nlp",
    "data science", "pandas", "numpy", "tensorflow", "pytorch",
    "sql", "nosql", "api", "microservices",
}

# Experience level indicators
LEVEL_INDICATORS: dict[str, ExperienceLevel] = {
    "junior": ExperienceLevel.ENTRY,
    "entry": ExperienceLevel.ENTRY,
    "entry-level": ExperienceLevel.ENTRY,
    "associate": ExperienceLevel.ENTRY,
    "mid": ExperienceLevel.MID,
    "mid-level": ExperienceLevel.MID,
    "intermediate": ExperienceLevel.MID,
    "senior": ExperienceLevel.SENIOR,
    "sr.": ExperienceLevel.SENIOR,
    "sr": ExperienceLevel.SENIOR,
    "staff": ExperienceLevel.STAFF,
    "lead": ExperienceLevel.LEAD,
    "tech lead": ExperienceLevel.LEAD,
    "team lead": ExperienceLevel.LEAD,
    "principal": ExperienceLevel.PRINCIPAL,
    "architect": ExperienceLevel.PRINCIPAL,
    "distinguished": ExperienceLevel.PRINCIPAL,
    "director": ExperienceLevel.EXECUTIVE,
    "vp": ExperienceLevel.EXECUTIVE,
    "head of": ExperienceLevel.EXECUTIVE,
    "cto": ExperienceLevel.EXECUTIVE,
}


def parse_jd_file(path: Path) -> JobDescription:
    """Parse a job description from a file.

    Args:
        path: Path to the JD file (txt, md, or similar).

    Returns:
        Parsed JobDescription model.

    Raises:
        NotFoundError: If the file doesn't exist.
    """
    if not path.exists():
        raise NotFoundError(f"Job description file not found: {path}")

    # Try common encodings
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            text = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"Unable to decode file: {path}")

    return parse_jd_text(text)


def parse_jd_text(text: str) -> JobDescription:
    """Parse a job description from raw text.

    Args:
        text: Raw JD text.

    Returns:
        Parsed JobDescription model.
    """
    # Extract components
    title = _extract_title(text)
    skills = _extract_skills(text)
    requirements = _extract_requirements(text)
    experience_level = _detect_experience_level(text, title)
    years_experience = _extract_years_experience(text)
    keywords = _extract_keywords(text)

    return JobDescription(
        raw_text=text,
        title=title,
        skills=skills,
        requirements=requirements,
        experience_level=experience_level,
        years_experience=years_experience,
        keywords=keywords,
    )


def _extract_title(text: str) -> str | None:
    """Extract job title from first few lines."""
    lines = text.strip().split("\n")[:5]
    for line in lines:
        line = line.strip()
        # Skip empty lines and common header patterns
        if not line or line.lower().startswith(("about", "company", "location")):
            continue
        # Likely title if short and contains engineer/developer/etc
        if len(line) < 100:
            title_keywords = ["engineer", "developer", "manager", "analyst", "designer", "architect"]
            if any(kw in line.lower() for kw in title_keywords):
                return line
    return None


def _extract_skills(text: str) -> list[str]:
    """Extract and normalize skills from text."""
    text_lower = text.lower()
    found_skills: set[str] = set()

    # Check for direct skill keywords
    for skill in SKILL_KEYWORDS:
        if re.search(rf"\b{re.escape(skill)}\b", text_lower):
            found_skills.add(skill)

    # Check for skill variants and normalize
    for variant, normalized in SKILL_NORMALIZATIONS.items():
        if re.search(rf"\b{re.escape(variant)}\b", text_lower):
            found_skills.add(normalized)

    return sorted(found_skills)


def _extract_requirements(text: str) -> list[Requirement]:
    """Extract requirements from bullet points and lists."""
    requirements: list[Requirement] = []

    # Find bullet points and numbered lists
    patterns = [
        r"^[\s]*[-•*]\s+(.+)$",  # Bullet points
        r"^[\s]*\d+[.)]\s+(.+)$",  # Numbered lists
    ]

    is_nice_to_have_section = False

    for line in text.split("\n"):
        line_lower = line.lower().strip()

        # Detect nice-to-have sections
        if any(phrase in line_lower for phrase in ["nice to have", "preferred", "bonus", "plus"]):
            is_nice_to_have_section = True
        elif any(phrase in line_lower for phrase in ["required", "must have", "requirements"]):
            is_nice_to_have_section = False

        # Extract bullet points
        for pattern in patterns:
            match = re.match(pattern, line, re.MULTILINE)
            if match:
                req_text = match.group(1).strip()
                if len(req_text) > 10:  # Skip very short items
                    requirements.append(
                        Requirement(
                            text=req_text,
                            is_required=not is_nice_to_have_section,
                        )
                    )
                break

    return requirements


def _detect_experience_level(text: str, title: str | None) -> ExperienceLevel:
    """Detect experience level from text and title."""
    text_lower = text.lower()
    title_lower = (title or "").lower()

    # Check title first (most reliable)
    for indicator, level in LEVEL_INDICATORS.items():
        if indicator in title_lower:
            return level

    # Check full text
    for indicator, level in LEVEL_INDICATORS.items():
        if re.search(rf"\b{re.escape(indicator)}\b", text_lower):
            return level

    return ExperienceLevel.MID  # Default


def _extract_years_experience(text: str) -> int | None:
    """Extract years of experience requirement."""
    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?experience",
        r"experience:\s*(\d+)\+?\s*(?:years?|yrs?)",
        r"minimum\s+(\d+)\s*(?:years?|yrs?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))

    return None


def _extract_keywords(text: str) -> list[str]:
    """Extract high-frequency keywords for ranking."""
    # Simple word frequency (exclude common words)
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
        "be", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "shall", "can", "need",
        "this", "that", "these", "those", "it", "its", "you", "your", "we",
        "our", "they", "their", "who", "which", "what", "when", "where", "why",
        "how", "all", "each", "every", "both", "few", "more", "most", "other",
        "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
        "too", "very", "just", "also", "any", "about", "into", "over", "after",
    }

    words = re.findall(r"\b[a-z]+\b", text.lower())
    word_counts = Counter(w for w in words if w not in stop_words and len(w) > 2)

    # Return words that appear 2+ times
    return [word for word, count in word_counts.most_common(20) if count >= 2]
```

### Testing Requirements

**`tests/unit/test_jd_parser.py`:**

```python
"""Tests for JD parser service."""

import pytest

from resume_as_code.models.job_description import ExperienceLevel
from resume_as_code.services.jd_parser import (
    parse_jd_text,
    _extract_skills,
    _detect_experience_level,
    _extract_years_experience,
)


SAMPLE_JD = """
Senior Software Engineer

About the Role:
We're looking for a Senior Software Engineer to join our platform team.
You'll be working with Python, Kubernetes, and AWS to build scalable services.

Requirements:
- 5+ years of experience in software development
- Strong proficiency in Python and Go
- Experience with Docker and Kubernetes
- AWS or GCP cloud experience
- CI/CD pipeline experience

Nice to Have:
- Experience with Terraform
- Knowledge of machine learning
- GraphQL API design
"""


class TestExtractSkills:
    """Tests for skill extraction."""

    def test_extracts_python(self):
        """Should extract Python."""
        skills = _extract_skills("Experience with Python required")
        assert "python" in skills

    def test_normalizes_k8s(self):
        """Should normalize k8s to kubernetes."""
        skills = _extract_skills("K8s deployment experience")
        assert "kubernetes" in skills

    def test_extracts_multiple_skills(self):
        """Should extract multiple skills."""
        skills = _extract_skills(SAMPLE_JD)
        assert "python" in skills
        assert "kubernetes" in skills
        assert "aws" in skills


class TestDetectExperienceLevel:
    """Tests for experience level detection."""

    def test_detects_senior_from_title(self):
        """Should detect senior from job title."""
        level = _detect_experience_level("", "Senior Software Engineer")
        assert level == ExperienceLevel.SENIOR

    def test_detects_staff_from_text(self):
        """Should detect staff from JD text."""
        level = _detect_experience_level("Looking for a Staff Engineer", None)
        assert level == ExperienceLevel.STAFF

    def test_defaults_to_mid(self):
        """Should default to mid level."""
        level = _detect_experience_level("Software Engineer role", None)
        assert level == ExperienceLevel.MID


class TestExtractYearsExperience:
    """Tests for years extraction."""

    def test_extracts_years(self):
        """Should extract years of experience."""
        years = _extract_years_experience("5+ years of experience required")
        assert years == 5

    def test_returns_none_if_not_found(self):
        """Should return None if no years specified."""
        years = _extract_years_experience("Experience preferred")
        assert years is None


class TestParseJDText:
    """Tests for full JD parsing."""

    def test_parses_complete_jd(self):
        """Should parse a complete JD."""
        jd = parse_jd_text(SAMPLE_JD)

        assert jd.title == "Senior Software Engineer"
        assert jd.experience_level == ExperienceLevel.SENIOR
        assert jd.years_experience == 5
        assert "python" in jd.skills
        assert len(jd.requirements) > 0

    def test_separates_required_and_nice_to_have(self):
        """Should separate required vs nice-to-have."""
        jd = parse_jd_text(SAMPLE_JD)

        required = [r for r in jd.requirements if r.is_required]
        nice_to_have = [r for r in jd.requirements if not r.is_required]

        assert len(required) > 0
        assert len(nice_to_have) > 0
```

### Verification Commands

```bash
# Create a sample JD file
cat > sample-jd.txt << 'EOF'
Senior Software Engineer - Platform Team

About Us:
We're building the next generation of cloud infrastructure.

Requirements:
- 5+ years of software engineering experience
- Strong proficiency in Python and Go
- Experience with Kubernetes and Docker
- AWS or GCP cloud experience
- CI/CD pipeline knowledge

Nice to Have:
- Terraform experience
- Machine learning background
EOF

# Test parsing (via Python REPL or test)
python -c "
from pathlib import Path
from resume_as_code.services.jd_parser import parse_jd_file

jd = parse_jd_file(Path('sample-jd.txt'))
print(f'Title: {jd.title}')
print(f'Level: {jd.experience_level}')
print(f'Years: {jd.years_experience}')
print(f'Skills: {jd.skills}')
print(f'Requirements: {len(jd.requirements)}')
"

# Code quality
ruff check src tests --fix
mypy src --strict
pytest tests/unit/test_jd_parser.py -v

# Cleanup
rm sample-jd.txt
```

### References

- [Source: epics.md#Story 4.1](_bmad-output/planning-artifacts/epics.md)
- [Source: architecture.md](_bmad-output/planning-artifacts/architecture.md)
- [Source: project-context.md](_bmad-output/project-context.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- Created JobDescription Pydantic model with ExperienceLevel enum and Requirement model
- Implemented jd_parser.py service with parse_jd_file() and parse_jd_text() functions
- Skill extraction with 100+ common tech skills and normalization mapping (k8s → kubernetes, etc.)
- Experience level detection from job title and body text
- Requirements extraction with bullet/numbered list parsing and nice-to-have detection
- Years of experience extraction from common patterns
- Keyword extraction for ranking purposes
- Full test coverage with 68 total tests (8 model + 40 unit + 20 integration)
- All code quality checks pass: ruff, mypy --strict

**Code Review Fixes (2026-01-11):**
- Added 7 edge case unit tests for title extraction (_extract_title)
- Added 2 file encoding tests (cp1252, binary fallback)
- Added 20 integration tests with 3 sample JD fixture files
- Replaced 6 magic numbers with named constants (MAX_TITLE_LENGTH, etc.)
- Updated File List to include all changed files

### File List

**New Files:**
- src/resume_as_code/models/job_description.py
- src/resume_as_code/services/jd_parser.py
- tests/unit/test_job_description.py
- tests/unit/test_jd_parser.py
- tests/integration/test_jd_parser_integration.py
- tests/fixtures/job_descriptions/senior_engineer.txt
- tests/fixtures/job_descriptions/junior_developer.txt
- tests/fixtures/job_descriptions/staff_engineer_markdown.md

**Modified Files:**
- src/resume_as_code/models/__init__.py (added exports)
- src/resume_as_code/services/__init__.py (added exports)
- tests/integration/test_list_command.py (formatting fix)

