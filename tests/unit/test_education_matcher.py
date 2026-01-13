"""Tests for EducationMatcher service."""

from __future__ import annotations

from resume_as_code.models.education import Education
from resume_as_code.services.education_matcher import (
    EducationMatcher,
    EducationMatchResult,
    EducationRequirement,
)


class TestEducationMatcherInit:
    """Tests for EducationMatcher initialization."""

    def test_creates_instance(self) -> None:
        """Should create an EducationMatcher instance."""
        matcher = EducationMatcher()
        assert matcher is not None

    def test_has_degree_levels(self) -> None:
        """Should have degree level mappings defined."""
        matcher = EducationMatcher()
        assert hasattr(matcher, "DEGREE_LEVELS")
        assert len(matcher.DEGREE_LEVELS) > 0

    def test_has_field_aliases(self) -> None:
        """Should have field alias mappings defined."""
        matcher = EducationMatcher()
        assert hasattr(matcher, "FIELD_ALIASES")
        assert len(matcher.FIELD_ALIASES) > 0


class TestExtractJDRequirements:
    """Tests for extract_jd_requirements method."""

    def test_extracts_bachelors_degree(self) -> None:
        """Should extract bachelor's degree requirement."""
        matcher = EducationMatcher()
        jd_text = "Bachelor's degree in Computer Science required"
        req = matcher.extract_jd_requirements(jd_text)
        assert req is not None
        assert req.degree_level == "bachelor"

    def test_extracts_masters_degree(self) -> None:
        """Should extract master's degree requirement."""
        matcher = EducationMatcher()
        jd_text = "Master's degree preferred"
        req = matcher.extract_jd_requirements(jd_text)
        assert req is not None
        assert req.degree_level == "master"

    def test_extracts_phd_requirement(self) -> None:
        """Should extract PhD requirement."""
        matcher = EducationMatcher()
        jd_text = "PhD in related field required"
        req = matcher.extract_jd_requirements(jd_text)
        assert req is not None
        assert req.degree_level == "doctorate"

    def test_extracts_bs_abbreviation(self) -> None:
        """Should extract BS abbreviation."""
        matcher = EducationMatcher()
        jd_text = "BS in Computer Science or equivalent"
        req = matcher.extract_jd_requirements(jd_text)
        assert req is not None
        assert req.degree_level == "bachelor"

    def test_extracts_ms_abbreviation(self) -> None:
        """Should extract MS abbreviation."""
        matcher = EducationMatcher()
        jd_text = "MS in Engineering preferred"
        req = matcher.extract_jd_requirements(jd_text)
        assert req is not None
        assert req.degree_level == "master"

    def test_extracts_field_of_study(self) -> None:
        """Should extract field of study."""
        matcher = EducationMatcher()
        jd_text = "Bachelor's degree in Computer Science"
        req = matcher.extract_jd_requirements(jd_text)
        assert req is not None
        assert req.field is not None
        assert "computer science" in req.field.lower()

    def test_detects_required_vs_preferred(self) -> None:
        """Should detect required vs preferred education."""
        matcher = EducationMatcher()

        jd_required = "Bachelor's degree required"
        req = matcher.extract_jd_requirements(jd_required)
        assert req is not None
        assert req.is_required is True

        jd_preferred = "Master's degree preferred"
        req = matcher.extract_jd_requirements(jd_preferred)
        assert req is not None
        assert req.is_required is False

    def test_returns_none_when_no_education_mentioned(self) -> None:
        """Should return None when no education requirements found."""
        matcher = EducationMatcher()
        jd_text = "5+ years of Python experience required"
        req = matcher.extract_jd_requirements(jd_text)
        assert req is None

    def test_extracts_engineering_field(self) -> None:
        """Should extract engineering field."""
        matcher = EducationMatcher()
        jd_text = "Degree in Electrical Engineering or related field"
        req = matcher.extract_jd_requirements(jd_text)
        assert req is not None
        assert req.field is not None

    def test_extracts_business_field(self) -> None:
        """Should extract business field."""
        matcher = EducationMatcher()
        jd_text = "MBA or equivalent business degree preferred"
        req = matcher.extract_jd_requirements(jd_text)
        assert req is not None


class TestMatchEducation:
    """Tests for match_education method."""

    def test_ms_exceeds_bs_requirement(self) -> None:
        """Should identify MS as exceeding BS requirement."""
        matcher = EducationMatcher()
        user_edu = [Education(degree="MS Computer Science", institution="MIT")]
        jd_req = EducationRequirement(
            degree_level="bachelor",
            field="computer science",
            is_required=True,
        )

        result = matcher.match_education(user_edu, jd_req)
        assert result.degree_match == "exceeds"

    def test_bs_meets_bs_requirement(self) -> None:
        """Should identify BS as meeting BS requirement."""
        matcher = EducationMatcher()
        user_edu = [Education(degree="BS Computer Science", institution="Stanford")]
        jd_req = EducationRequirement(
            degree_level="bachelor",
            field="computer science",
            is_required=True,
        )

        result = matcher.match_education(user_edu, jd_req)
        assert result.degree_match == "meets"

    def test_bs_below_ms_requirement(self) -> None:
        """Should identify BS as below MS requirement."""
        matcher = EducationMatcher()
        user_edu = [Education(degree="BS Computer Science", institution="UCLA")]
        jd_req = EducationRequirement(
            degree_level="master",
            field="computer science",
            is_required=True,
        )

        result = matcher.match_education(user_edu, jd_req)
        assert result.degree_match == "below"

    def test_direct_field_match(self) -> None:
        """Should identify direct field match."""
        matcher = EducationMatcher()
        user_edu = [Education(degree="BS Computer Science", institution="MIT")]
        jd_req = EducationRequirement(
            degree_level="bachelor",
            field="computer science",
            is_required=True,
        )

        result = matcher.match_education(user_edu, jd_req)
        assert result.field_relevance == "direct"

    def test_related_field_match(self) -> None:
        """Should identify related field match."""
        matcher = EducationMatcher()
        user_edu = [Education(degree="BS Software Engineering", institution="MIT")]
        jd_req = EducationRequirement(
            degree_level="bachelor",
            field="computer science",
            is_required=True,
        )

        result = matcher.match_education(user_edu, jd_req)
        assert result.field_relevance == "related"

    def test_unrelated_field_match(self) -> None:
        """Should identify unrelated field."""
        matcher = EducationMatcher()
        user_edu = [Education(degree="BS Art History", institution="Yale")]
        jd_req = EducationRequirement(
            degree_level="bachelor",
            field="computer science",
            is_required=True,
        )

        result = matcher.match_education(user_edu, jd_req)
        assert result.field_relevance == "unrelated"

    def test_handles_empty_user_education(self) -> None:
        """Should handle empty user education list."""
        matcher = EducationMatcher()
        user_edu: list[Education] = []
        jd_req = EducationRequirement(
            degree_level="bachelor",
            field="computer science",
            is_required=True,
        )

        result = matcher.match_education(user_edu, jd_req)
        assert result.meets_requirements is False
        assert result.degree_match == "unknown"

    def test_handles_no_jd_requirements(self) -> None:
        """Should handle no JD education requirements."""
        matcher = EducationMatcher()
        user_edu = [Education(degree="BS Computer Science", institution="MIT")]

        result = matcher.match_education(user_edu, None)
        assert result.meets_requirements is True
        assert result.degree_match == "unknown"

    def test_returns_education_match_result(self) -> None:
        """Should return an EducationMatchResult dataclass."""
        matcher = EducationMatcher()
        user_edu = [Education(degree="BS Computer Science", institution="MIT")]
        jd_req = EducationRequirement(
            degree_level="bachelor",
            field="computer science",
            is_required=True,
        )

        result = matcher.match_education(user_edu, jd_req)
        assert isinstance(result, EducationMatchResult)
        assert hasattr(result, "meets_requirements")
        assert hasattr(result, "degree_match")
        assert hasattr(result, "field_relevance")
        assert hasattr(result, "jd_requirement_text")
        assert hasattr(result, "best_match_education")

    def test_includes_jd_requirement_text(self) -> None:
        """Should include JD requirement text in result."""
        matcher = EducationMatcher()
        user_edu = [Education(degree="BS Computer Science", institution="MIT")]
        jd_req = EducationRequirement(
            degree_level="bachelor",
            field="computer science",
            is_required=True,
        )

        result = matcher.match_education(user_edu, jd_req)
        assert result.jd_requirement_text is not None

    def test_includes_best_match_education(self) -> None:
        """Should include best matching education in result."""
        matcher = EducationMatcher()
        user_edu = [
            Education(degree="BS Art History", institution="Yale"),
            Education(degree="MS Computer Science", institution="MIT"),
        ]
        jd_req = EducationRequirement(
            degree_level="bachelor",
            field="computer science",
            is_required=True,
        )

        result = matcher.match_education(user_edu, jd_req)
        assert result.best_match_education is not None
        # Should pick the CS degree as best match
        assert "Computer Science" in result.best_match_education


class TestEducationRequirement:
    """Tests for EducationRequirement dataclass."""

    def test_dataclass_fields(self) -> None:
        """Should have expected fields."""
        req = EducationRequirement(
            degree_level="bachelor",
            field="computer science",
            is_required=True,
        )
        assert req.degree_level == "bachelor"
        assert req.field == "computer science"
        assert req.is_required is True

    def test_optional_fields(self) -> None:
        """Should allow optional fields."""
        req = EducationRequirement(
            degree_level=None,
            field=None,
            is_required=False,
        )
        assert req.degree_level is None
        assert req.field is None


class TestEducationMatchResult:
    """Tests for EducationMatchResult dataclass."""

    def test_dataclass_fields(self) -> None:
        """Should have expected fields."""
        result = EducationMatchResult(
            meets_requirements=True,
            degree_match="meets",
            field_relevance="direct",
            jd_requirement_text="Bachelor's in CS",
            best_match_education="BS Computer Science",
        )
        assert result.meets_requirements is True
        assert result.degree_match == "meets"
        assert result.field_relevance == "direct"
        assert result.jd_requirement_text == "Bachelor's in CS"
        assert result.best_match_education == "BS Computer Science"
