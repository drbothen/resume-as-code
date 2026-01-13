"""Education matcher service for JD requirements analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from resume_as_code.models.education import Education


@dataclass(frozen=True)
class EducationRequirement:
    """Education requirement extracted from JD.

    Attributes:
        degree_level: Required degree level (bachelor, master, doctorate, etc.).
        field: Required field of study.
        is_required: Whether education is required vs preferred.
    """

    degree_level: str | None
    field: str | None
    is_required: bool


@dataclass(frozen=True)
class EducationMatchResult:
    """Result of matching user education against JD requirements.

    Attributes:
        meets_requirements: Whether user meets JD education requirements.
        degree_match: How user's degree level compares ("exceeds", "meets", "below", "unknown").
        field_relevance: How relevant user's field is ("direct", "related", "unrelated", "unknown").
        jd_requirement_text: Formatted JD requirement for display.
        best_match_education: User's best matching education credential.
    """

    meets_requirements: bool
    degree_match: Literal["exceeds", "meets", "below", "unknown"]
    field_relevance: Literal["direct", "related", "unrelated", "unknown"]
    jd_requirement_text: str | None
    best_match_education: str | None


class EducationMatcher:
    """Match user education against JD requirements.

    Extracts education requirements from job descriptions and compares
    against user's education to determine match level.
    """

    # Degree level hierarchy (higher number = higher degree)
    DEGREE_LEVELS: dict[str, int] = {
        "associate": 1,
        "bachelor": 2,
        "bs": 2,
        "ba": 2,
        "bsc": 2,
        "master": 3,
        "ms": 3,
        "ma": 3,
        "mba": 3,
        "msc": 3,
        "doctorate": 4,
        "phd": 4,
        "doctor": 4,
    }

    # Field aliases for matching (canonical name -> aliases)
    FIELD_ALIASES: dict[str, list[str]] = {
        "computer science": [
            "cs",
            "computing",
            "informatics",
            "software",
            "software engineering",
            "computer engineering",
            "information technology",
            "it",
        ],
        "engineering": [
            "electrical",
            "electrical engineering",
            "mechanical",
            "systems engineering",
            "industrial engineering",
        ],
        "cybersecurity": [
            "security",
            "information security",
            "infosec",
            "cyber security",
            "network security",
        ],
        "business": [
            "administration",
            "management",
            "mba",
            "business administration",
            "finance",
            "economics",
        ],
        "mathematics": [
            "math",
            "applied mathematics",
            "statistics",
            "data science",
        ],
    }

    # Patterns to extract education requirements from JD
    _DEGREE_PATTERNS: list[tuple[str, str]] = [
        (r"\bphd\b|\bdoctorate\b|\bdoctoral\b|\bdoctor(?:'?s)?\s+degree\b", "doctorate"),
        (
            r"\bmaster(?:'?s)?\s+degree\b|\bms\b(?!\s+(?:office|word|excel))|\bma\b(?!\s+(?:in\s+)?the)|\bmba\b|\bm\.?s\.?\b(?:\s+in\b)",
            "master",
        ),
        (
            r"\bbachelor(?:'?s)?\s+degree\b|\bbs\b|\bba\b(?!\s+(?:in\s+)?the)|\bb\.?s\.?\b(?:\s+in\b)|\bundergraduate\s+degree\b",
            "bachelor",
        ),
        (r"\bassociate(?:'?s)?\s+degree\b", "associate"),
        # Generic "degree in" without level implies bachelor's
        (r"\bdegree\s+in\s+\w+", "bachelor"),
    ]

    # Patterns to extract field of study
    _FIELD_PATTERNS: list[str] = [
        r"(?:in|of)\s+([A-Za-z\s]+?)(?:\s+or|\s+required|\s+preferred|,|\.|$)",
        r"(?:degree|bs|ba|ms|ma|mba|phd)\s+(?:in\s+)?([A-Za-z\s]+?)(?:\s+or|\s+required|\s+preferred|,|\.|$)",
    ]

    def extract_jd_requirements(self, jd_text: str) -> EducationRequirement | None:
        """Extract education requirements from JD text.

        Args:
            jd_text: Raw job description text.

        Returns:
            EducationRequirement if found, None otherwise.
        """
        jd_lower = jd_text.lower()

        # Extract degree level
        degree_level: str | None = None
        for pattern, level in self._DEGREE_PATTERNS:
            if re.search(pattern, jd_lower):
                degree_level = level
                break

        if degree_level is None:
            return None

        # Extract field of study
        field: str | None = None
        for pattern in self._FIELD_PATTERNS:
            match = re.search(pattern, jd_lower)
            if match:
                field_candidate = match.group(1).strip()
                # Filter out noise words
                if field_candidate and len(field_candidate) > 2:
                    field = self._normalize_field(field_candidate)
                    break

        # Determine if required vs preferred
        is_required = self._is_required(jd_lower)

        return EducationRequirement(
            degree_level=degree_level,
            field=field,
            is_required=is_required,
        )

    def match_education(
        self,
        user_education: list[Education],
        jd_req: EducationRequirement | None,
    ) -> EducationMatchResult:
        """Compare user education to JD requirements.

        Args:
            user_education: List of user's Education objects.
            jd_req: Education requirement from JD (None if no requirement).

        Returns:
            EducationMatchResult with match analysis.
        """
        # No JD requirements = automatic pass
        if jd_req is None:
            best_edu = self._get_best_education(user_education)
            return EducationMatchResult(
                meets_requirements=True,
                degree_match="unknown",
                field_relevance="unknown",
                jd_requirement_text=None,
                best_match_education=best_edu.degree if best_edu else None,
            )

        # No user education = fail
        if not user_education:
            return EducationMatchResult(
                meets_requirements=False,
                degree_match="unknown",
                field_relevance="unknown",
                jd_requirement_text=self._format_requirement(jd_req),
                best_match_education=None,
            )

        # Find best matching education
        best_match = self._find_best_match(user_education, jd_req)
        degree_match = self._compare_degree_level(best_match, jd_req)
        field_relevance = self._compare_field(best_match, jd_req)

        # Determine if requirements are met
        meets_requirements = degree_match in ("meets", "exceeds") and field_relevance in (
            "direct",
            "related",
            "unknown",
        )

        return EducationMatchResult(
            meets_requirements=meets_requirements,
            degree_match=degree_match,
            field_relevance=field_relevance,
            jd_requirement_text=self._format_requirement(jd_req),
            best_match_education=best_match.degree if best_match else None,
        )

    def _normalize_field(self, field: str) -> str:
        """Normalize field name."""
        field = field.lower().strip()
        # Remove common noise words
        noise = ["a", "an", "the", "or", "and", "related", "equivalent", "field"]
        words = [w for w in field.split() if w not in noise]
        return " ".join(words)

    def _is_required(self, jd_lower: str) -> bool:
        """Determine if education is required vs preferred."""
        # Check for preferred indicators first
        preferred_indicators = ["preferred", "nice to have", "bonus", "plus", "desirable"]
        return all(indicator not in jd_lower for indicator in preferred_indicators)

    def _get_best_education(self, education_list: list[Education]) -> Education | None:
        """Get the highest level education from list."""
        if not education_list:
            return None

        best: Education | None = None
        best_level = 0

        for edu in education_list:
            level = self._get_degree_level(edu.degree)
            if level > best_level:
                best_level = level
                best = edu

        return best if best else education_list[0]

    def _find_best_match(
        self, user_education: list[Education], jd_req: EducationRequirement
    ) -> Education | None:
        """Find the best matching education for JD requirement."""
        if not user_education:
            return None

        best_match: Education | None = None
        best_score = -1

        for edu in user_education:
            score = 0

            # Score degree level
            user_level = self._get_degree_level(edu.degree)
            req_level = self.DEGREE_LEVELS.get(jd_req.degree_level or "", 0)

            if user_level >= req_level:
                score += 10
            if user_level == req_level:
                score += 5

            # Score field relevance
            if jd_req.field:
                field_match = self._get_field_relevance(edu.degree, jd_req.field)
                if field_match == "direct":
                    score += 20
                elif field_match == "related":
                    score += 10

            if score > best_score:
                best_score = score
                best_match = edu

        return best_match

    def _get_degree_level(self, degree: str) -> int:
        """Extract degree level from degree string."""
        degree_lower = degree.lower()

        # Check for exact matches first
        for level_name, level_value in self.DEGREE_LEVELS.items():
            if level_name in degree_lower:
                return level_value

        # Check for common patterns
        if re.search(r"\bph\.?d\b", degree_lower):
            return 4
        if re.search(r"\bm\.?s\.?\b|\bmaster", degree_lower):
            return 3
        if re.search(r"\bb\.?s\.?\b|\bb\.?a\.?\b|\bbachelor", degree_lower):
            return 2
        if re.search(r"\ba\.?a\.?\b|\bassociate", degree_lower):
            return 1

        return 0

    def _compare_degree_level(
        self, user_edu: Education | None, jd_req: EducationRequirement
    ) -> Literal["exceeds", "meets", "below", "unknown"]:
        """Compare user's degree level to requirement."""
        if user_edu is None or jd_req.degree_level is None:
            return "unknown"

        user_level = self._get_degree_level(user_edu.degree)
        req_level = self.DEGREE_LEVELS.get(jd_req.degree_level, 0)

        if user_level > req_level:
            return "exceeds"
        if user_level == req_level:
            return "meets"
        if user_level < req_level:
            return "below"

        return "unknown"

    def _compare_field(
        self, user_edu: Education | None, jd_req: EducationRequirement
    ) -> Literal["direct", "related", "unrelated", "unknown"]:
        """Compare user's field of study to requirement."""
        if user_edu is None or jd_req.field is None:
            return "unknown"

        return self._get_field_relevance(user_edu.degree, jd_req.field)

    def _get_field_relevance(
        self, user_degree: str, req_field: str
    ) -> Literal["direct", "related", "unrelated", "unknown"]:
        """Determine relevance of user's field to required field."""
        user_lower = user_degree.lower()
        req_lower = req_field.lower()

        # Direct match - field name appears in degree
        if req_lower in user_lower:
            return "direct"

        # Check canonical field aliases
        for canonical, aliases in self.FIELD_ALIASES.items():
            # Check if requirement matches this canonical field
            req_matches_canonical = canonical in req_lower or any(
                alias in req_lower for alias in aliases
            )

            if req_matches_canonical:
                # Check if user's degree matches same canonical field
                if canonical in user_lower:
                    return "direct"
                if any(alias in user_lower for alias in aliases):
                    return "related"

        # Check for general engineering/science matches
        engineering_fields = ["engineering", "computer", "software", "electrical", "systems"]
        req_is_engineering = any(f in req_lower for f in engineering_fields)
        user_is_engineering = any(f in user_lower for f in engineering_fields)
        if req_is_engineering and user_is_engineering:
            return "related"

        return "unrelated"

    def _format_requirement(self, req: EducationRequirement) -> str:
        """Format requirement for display."""
        parts = []

        if req.degree_level:
            degree_display = req.degree_level.title()
            if req.degree_level == "bachelor":
                degree_display = "Bachelor's"
            elif req.degree_level == "master":
                degree_display = "Master's"
            parts.append(degree_display)

        if req.field:
            parts.append(f"in {req.field.title()}")

        return " ".join(parts) if parts else "Degree"
