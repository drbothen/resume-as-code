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
    "python",
    "java",
    "javascript",
    "typescript",
    "go",
    "golang",
    "rust",
    "c++",
    "c#",
    "ruby",
    "php",
    "scala",
    "kotlin",
    "swift",
    "react",
    "vue",
    "angular",
    "nodejs",
    "django",
    "flask",
    "fastapi",
    "spring",
    "rails",
    "express",
    "nextjs",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "terraform",
    "jenkins",
    "github actions",
    "gitlab",
    "cicd",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "elasticsearch",
    "kafka",
    "rabbitmq",
    "graphql",
    "rest",
    "grpc",
    "linux",
    "unix",
    "bash",
    "shell",
    "git",
    "agile",
    "scrum",
    "jira",
    "machine learning",
    "ml",
    "ai",
    "deep learning",
    "nlp",
    "data science",
    "pandas",
    "numpy",
    "tensorflow",
    "pytorch",
    "sql",
    "nosql",
    "api",
    "microservices",
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
    text: str | None = None
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            text = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    if text is None:
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
    lines = text.strip().split("\n")[:MAX_TITLE_SEARCH_LINES]
    for line in lines:
        line = line.strip()
        # Skip empty lines and common header patterns
        if not line or line.lower().startswith(("about", "company", "location")):
            continue
        # Likely title if short and contains engineer/developer/etc
        if len(line) < MAX_TITLE_LENGTH:
            title_keywords = [
                "engineer",
                "developer",
                "manager",
                "analyst",
                "designer",
                "architect",
            ]
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
                if len(req_text) > MIN_REQUIREMENT_LENGTH:
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
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "were",
        "been",
        "be",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "need",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "you",
        "your",
        "we",
        "our",
        "they",
        "their",
        "who",
        "which",
        "what",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "also",
        "any",
        "about",
        "into",
        "over",
        "after",
    }

    words = re.findall(r"\b[a-z]+\b", text.lower())
    word_counts = Counter(w for w in words if w not in stop_words and len(w) > MIN_KEYWORD_LENGTH)

    return [
        word
        for word, count in word_counts.most_common(MAX_KEYWORDS)
        if count >= MIN_KEYWORD_FREQUENCY
    ]
