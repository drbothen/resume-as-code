"""Unit tests for exclusion reason models."""

from __future__ import annotations

from resume_as_code.models.exclusion import (
    LOW_RELEVANCE_THRESHOLD,
    ExclusionReason,
    ExclusionType,
    get_exclusion_reason,
)


class TestExclusionType:
    """Tests for ExclusionType enum."""

    def test_low_relevance_value(self) -> None:
        """Should have correct string value for LOW_RELEVANCE."""
        assert ExclusionType.LOW_RELEVANCE.value == "low_relevance"

    def test_below_threshold_value(self) -> None:
        """Should have correct string value for BELOW_THRESHOLD."""
        assert ExclusionType.BELOW_THRESHOLD.value == "below_threshold"

    def test_enum_is_string_subclass(self) -> None:
        """Should be usable as string for JSON serialization."""
        assert isinstance(ExclusionType.LOW_RELEVANCE, str)
        # Verify the value property gives us the raw string
        assert ExclusionType.LOW_RELEVANCE.value == "low_relevance"


class TestExclusionReason:
    """Tests for ExclusionReason dataclass."""

    def test_create_with_required_fields(self) -> None:
        """Should create with type and message."""
        reason = ExclusionReason(
            type=ExclusionType.LOW_RELEVANCE,
            message="Low relevance score (15%)",
        )
        assert reason.type == ExclusionType.LOW_RELEVANCE
        assert reason.message == "Low relevance score (15%)"
        assert reason.suggestion is None

    def test_create_with_suggestion(self) -> None:
        """Should create with optional suggestion."""
        reason = ExclusionReason(
            type=ExclusionType.LOW_RELEVANCE,
            message="Low relevance score (10%)",
            suggestion="Add more keywords",
        )
        assert reason.suggestion == "Add more keywords"

    def test_to_dict_includes_all_fields(self) -> None:
        """Should include type, message, and suggestion in dict output."""
        reason = ExclusionReason(
            type=ExclusionType.BELOW_THRESHOLD,
            message="Below selection threshold (45%)",
            suggestion=None,
        )
        result = reason.to_dict()

        assert result["type"] == "below_threshold"
        assert result["message"] == "Below selection threshold (45%)"
        assert result["suggestion"] is None

    def test_to_dict_with_suggestion(self) -> None:
        """Should include suggestion in dict when present."""
        reason = ExclusionReason(
            type=ExclusionType.LOW_RELEVANCE,
            message="Low relevance score (5%)",
            suggestion="Consider adding JD keywords",
        )
        result = reason.to_dict()

        assert result["suggestion"] == "Consider adding JD keywords"

    def test_to_dict_returns_serializable_dict(self) -> None:
        """Should return a dict that can be JSON serialized."""
        import json

        reason = ExclusionReason(
            type=ExclusionType.LOW_RELEVANCE,
            message="Test message",
            suggestion="Test suggestion",
        )
        result = reason.to_dict()

        # Should not raise
        json_str = json.dumps(result)
        assert isinstance(json_str, str)


class TestGetExclusionReason:
    """Tests for get_exclusion_reason function."""

    def test_low_score_returns_low_relevance(self) -> None:
        """Should return LOW_RELEVANCE for scores below threshold."""
        reason = get_exclusion_reason(0.1)

        assert reason.type == ExclusionType.LOW_RELEVANCE
        assert "Low relevance" in reason.message
        assert "10%" in reason.message
        assert reason.suggestion is not None

    def test_medium_score_returns_below_threshold(self) -> None:
        """Should return BELOW_THRESHOLD for scores at or above threshold."""
        reason = get_exclusion_reason(0.45)

        assert reason.type == ExclusionType.BELOW_THRESHOLD
        assert "Below selection threshold" in reason.message
        assert "45%" in reason.message
        assert reason.suggestion is None

    def test_zero_score_returns_low_relevance(self) -> None:
        """Should handle zero score correctly."""
        reason = get_exclusion_reason(0.0)

        assert reason.type == ExclusionType.LOW_RELEVANCE
        assert "0%" in reason.message

    def test_boundary_at_threshold_returns_below_threshold(self) -> None:
        """Should return BELOW_THRESHOLD when score equals threshold exactly."""
        # Score exactly at threshold (0.2) should be BELOW_THRESHOLD, not LOW_RELEVANCE
        reason = get_exclusion_reason(LOW_RELEVANCE_THRESHOLD)

        assert reason.type == ExclusionType.BELOW_THRESHOLD
        assert "20%" in reason.message

    def test_just_below_threshold_returns_low_relevance(self) -> None:
        """Should return LOW_RELEVANCE for score just below threshold."""
        reason = get_exclusion_reason(0.19)

        assert reason.type == ExclusionType.LOW_RELEVANCE

    def test_just_above_threshold_returns_below_threshold(self) -> None:
        """Should return BELOW_THRESHOLD for score just above threshold."""
        reason = get_exclusion_reason(0.21)

        assert reason.type == ExclusionType.BELOW_THRESHOLD

    def test_high_score_returns_below_threshold(self) -> None:
        """Should return BELOW_THRESHOLD even for high scores (excluded due to top N)."""
        reason = get_exclusion_reason(0.85)

        assert reason.type == ExclusionType.BELOW_THRESHOLD
        assert "85%" in reason.message

    def test_low_relevance_includes_improvement_suggestion(self) -> None:
        """Should include actionable suggestion for low relevance items."""
        reason = get_exclusion_reason(0.05)

        assert reason.suggestion is not None
        assert "keyword" in reason.suggestion.lower()

    def test_below_threshold_no_suggestion(self) -> None:
        """Should not include suggestion for below threshold items."""
        reason = get_exclusion_reason(0.5)

        assert reason.suggestion is None


class TestLowRelevanceThreshold:
    """Tests for threshold constant."""

    def test_threshold_is_20_percent(self) -> None:
        """Should be set to 0.2 (20%)."""
        assert LOW_RELEVANCE_THRESHOLD == 0.2

    def test_threshold_is_float(self) -> None:
        """Should be a float for comparison."""
        assert isinstance(LOW_RELEVANCE_THRESHOLD, float)
