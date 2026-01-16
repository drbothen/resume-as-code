"""Tests for content quality validation."""

from __future__ import annotations

from resume_as_code.services.content_validator import (
    BULLET_CHAR_MAX,
    BULLET_CHAR_MIN,
    WEAK_VERBS,
    ContentWarning,
    validate_content_density,
    validate_content_quality,
    validate_position_reference,
)


class TestContentQuality:
    """Tests for content quality validation."""

    def test_detects_weak_verb_managed(self) -> None:
        """Should detect weak action verb 'managed' (AC #6)."""
        work_unit = {
            "actions": ["Managed a team of engineers"],
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert any(w.code == "WEAK_ACTION_VERB" for w in warnings)
        assert any("managed" in w.message.lower() for w in warnings)

    def test_detects_weak_verb_handled(self) -> None:
        """Should detect weak action verb 'handled' (AC #6)."""
        work_unit = {
            "actions": ["Handled customer complaints daily"],
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert any(w.code == "WEAK_ACTION_VERB" for w in warnings)

    def test_detects_weak_verb_helped(self) -> None:
        """Should detect weak action verb 'helped' (AC #6)."""
        work_unit = {
            "actions": ["Helped the team deliver on time"],
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert any(w.code == "WEAK_ACTION_VERB" for w in warnings)

    def test_detects_weak_verb_worked_on(self) -> None:
        """Should detect weak phrase 'worked on' (AC #6)."""
        work_unit = {
            "actions": ["Worked on improving the deployment process"],
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert any(w.code == "WEAK_ACTION_VERB" for w in warnings)

    def test_detects_weak_verb_responsible_for(self) -> None:
        """Should detect weak phrase 'was responsible for' (AC #6)."""
        work_unit = {
            "actions": ["Was responsible for API development"],
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert any(w.code == "WEAK_ACTION_VERB" for w in warnings)

    def test_suggests_strong_alternatives_for_managed(self) -> None:
        """Should suggest strong verb alternatives for 'managed' (AC #7)."""
        work_unit = {
            "actions": ["Managed a team of engineers"],
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        weak_verb_warnings = [w for w in warnings if w.code == "WEAK_ACTION_VERB"]
        assert len(weak_verb_warnings) > 0
        # Should suggest alternatives from WEAK_VERBS
        suggestion = weak_verb_warnings[0].suggestion.lower()
        assert any(alt in suggestion for alt in ["orchestrated", "directed", "coordinated"])

    def test_suggests_strong_alternatives_for_handled(self) -> None:
        """Should suggest strong verb alternatives for 'handled' (AC #7)."""
        work_unit = {
            "actions": ["Handled customer complaints"],
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        weak_verb_warnings = [w for w in warnings if w.code == "WEAK_ACTION_VERB"]
        assert len(weak_verb_warnings) > 0
        suggestion = weak_verb_warnings[0].suggestion.lower()
        assert any(alt in suggestion for alt in ["resolved", "processed", "executed"])

    def test_detects_verb_repetition(self) -> None:
        """Should detect repeated action verbs (AC #6)."""
        work_unit = {
            "actions": [
                "Implemented new authentication system",
                "Implemented caching layer for API",
                "Implemented monitoring dashboard",
            ],
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert any(w.code == "VERB_REPETITION" for w in warnings)
        repetition_warning = next(w for w in warnings if w.code == "VERB_REPETITION")
        assert "implemented" in repetition_warning.message.lower()
        assert "3" in repetition_warning.message  # Used 3 times

    def test_no_repetition_warning_for_single_use(self) -> None:
        """Should not warn for verbs used only once."""
        work_unit = {
            "actions": [
                "Implemented new authentication system",
                "Designed caching layer architecture",
                "Built monitoring dashboard",
            ],
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert not any(w.code == "VERB_REPETITION" for w in warnings)

    def test_detects_missing_quantification(self) -> None:
        """Should warn about missing metrics in outcome (AC #6)."""
        work_unit = {
            "outcome": {"result": "Improved system performance significantly"},
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert any(w.code == "MISSING_QUANTIFICATION" for w in warnings)

    def test_accepts_percentage_quantification(self) -> None:
        """Should not warn when outcome has percentage metrics."""
        work_unit = {
            "outcome": {"result": "Improved system performance by 40%"},
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert not any(w.code == "MISSING_QUANTIFICATION" for w in warnings)

    def test_accepts_currency_quantification(self) -> None:
        """Should not warn when outcome has currency metrics."""
        work_unit = {
            "outcome": {"result": "Generated $50,000 in cost savings"},
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert not any(w.code == "MISSING_QUANTIFICATION" for w in warnings)

    def test_accepts_multiplier_quantification(self) -> None:
        """Should not warn when outcome has multiplier metrics (e.g., 3x)."""
        work_unit = {
            "outcome": {"result": "Achieved 3x throughput improvement"},
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert not any(w.code == "MISSING_QUANTIFICATION" for w in warnings)

    def test_accepts_time_quantification(self) -> None:
        """Should not warn when outcome has time metrics."""
        work_unit = {
            "outcome": {"result": "Reduced deployment time from 30 min to 5 min"},
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert not any(w.code == "MISSING_QUANTIFICATION" for w in warnings)

    def test_accepts_time_quantification_plurals(self) -> None:
        """Should recognize plural time units (hours, days, mins, secs)."""
        test_cases = [
            "Saved 5 hours per week on manual tasks",
            "Reduced build time by 10 mins",
            "Improved response time by 200 secs",
            "Completed project 3 days ahead of schedule",
        ]
        for result_text in test_cases:
            work_unit = {"outcome": {"result": result_text}}
            warnings = validate_content_quality(work_unit, "test.yaml")
            assert not any(w.code == "MISSING_QUANTIFICATION" for w in warnings), (
                f"Failed to detect quantification in: {result_text}"
            )

    def test_accepts_impact_words_with_metrics(self) -> None:
        """Should accept impact words with metrics like 'reduced by 50%'."""
        work_unit = {
            "outcome": {"result": "Reduced API latency by 50ms and improved response times"},
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert not any(w.code == "MISSING_QUANTIFICATION" for w in warnings)

    def test_missing_quantification_severity_is_info(self) -> None:
        """Missing quantification should be 'info' severity, not 'warning'."""
        work_unit = {
            "outcome": {"result": "Made things better"},
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        quant_warnings = [w for w in warnings if w.code == "MISSING_QUANTIFICATION"]
        assert len(quant_warnings) > 0
        assert quant_warnings[0].severity == "info"

    def test_content_warning_structure(self) -> None:
        """ContentWarning should have all required fields."""
        warning = ContentWarning(
            code="TEST_CODE",
            message="Test message",
            path="test.yaml:actions[0]",
            suggestion="Test suggestion",
        )
        assert warning.code == "TEST_CODE"
        assert warning.message == "Test message"
        assert warning.path == "test.yaml:actions[0]"
        assert warning.suggestion == "Test suggestion"
        assert warning.severity == "warning"  # Default

    def test_handles_empty_actions(self) -> None:
        """Should handle Work Unit with no actions gracefully."""
        work_unit: dict[str, object] = {"actions": []}
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert not any(w.code == "WEAK_ACTION_VERB" for w in warnings)
        assert not any(w.code == "VERB_REPETITION" for w in warnings)

    def test_handles_missing_actions(self) -> None:
        """Should handle Work Unit with missing actions field."""
        work_unit: dict[str, object] = {}
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert not any(w.code == "WEAK_ACTION_VERB" for w in warnings)

    def test_handles_empty_outcome_object(self) -> None:
        """Should handle empty outcome object without error."""
        work_unit: dict[str, object] = {"outcome": {}}
        warnings = validate_content_quality(work_unit, "test.yaml")
        # Empty outcome should not trigger quantification warning (no result to check)
        assert not any(w.code == "MISSING_QUANTIFICATION" for w in warnings)

    def test_handles_non_string_actions(self) -> None:
        """Should skip non-string action items."""
        work_unit: dict[str, object] = {
            "actions": [123, None, "Valid action text"],
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        # Should not crash, and should process valid string actions
        assert isinstance(warnings, list)

    def test_weak_verbs_dictionary_complete(self) -> None:
        """WEAK_VERBS should contain all expected weak verbs."""
        expected_verbs = [
            "managed",
            "handled",
            "helped",
            "worked on",
            "was responsible for",
        ]
        for verb in expected_verbs:
            assert verb in WEAK_VERBS, f"Missing weak verb: {verb}"
            assert len(WEAK_VERBS[verb]) >= 3, f"Not enough alternatives for: {verb}"


class TestContentDensity:
    """Tests for content density validation."""

    def test_short_bullet_warning(self) -> None:
        """Should warn about too-short bullets (AC #8)."""
        work_unit = {
            "actions": ["Did stuff"],  # Very short
        }
        warnings = validate_content_density(work_unit, "test.yaml")
        assert any(w.code == "BULLET_TOO_SHORT" for w in warnings)

    def test_short_bullet_shows_character_count(self) -> None:
        """Warning should show actual and minimum character counts."""
        short_action = "Did stuff"
        work_unit = {"actions": [short_action]}
        warnings = validate_content_density(work_unit, "test.yaml")
        short_warnings = [w for w in warnings if w.code == "BULLET_TOO_SHORT"]
        assert len(short_warnings) == 1
        assert str(len(short_action)) in short_warnings[0].message
        assert str(BULLET_CHAR_MIN) in short_warnings[0].message

    def test_long_bullet_warning(self) -> None:
        """Should warn about too-long bullets (AC #8)."""
        work_unit = {
            "actions": ["x" * 200],  # Very long
        }
        warnings = validate_content_density(work_unit, "test.yaml")
        assert any(w.code == "BULLET_TOO_LONG" for w in warnings)

    def test_long_bullet_shows_character_count(self) -> None:
        """Warning should show actual and maximum character counts."""
        long_action = "x" * 200
        work_unit = {"actions": [long_action]}
        warnings = validate_content_density(work_unit, "test.yaml")
        long_warnings = [w for w in warnings if w.code == "BULLET_TOO_LONG"]
        assert len(long_warnings) == 1
        assert "200" in long_warnings[0].message
        assert str(BULLET_CHAR_MAX) in long_warnings[0].message

    def test_optimal_length_no_warning(self) -> None:
        """Should not warn for optimal length bullets (100-160 chars)."""
        optimal_action = "x" * 130  # Within 100-160 range
        work_unit = {"actions": [optimal_action]}
        warnings = validate_content_density(work_unit, "test.yaml")
        assert not any(w.code in ("BULLET_TOO_SHORT", "BULLET_TOO_LONG") for w in warnings)

    def test_boundary_min_length_no_warning(self) -> None:
        """Should not warn for exactly minimum length bullet."""
        work_unit = {"actions": ["x" * BULLET_CHAR_MIN]}
        warnings = validate_content_density(work_unit, "test.yaml")
        assert not any(w.code == "BULLET_TOO_SHORT" for w in warnings)

    def test_boundary_max_length_no_warning(self) -> None:
        """Should not warn for exactly maximum length bullet."""
        work_unit = {"actions": ["x" * BULLET_CHAR_MAX]}
        warnings = validate_content_density(work_unit, "test.yaml")
        assert not any(w.code == "BULLET_TOO_LONG" for w in warnings)

    def test_handles_empty_actions(self) -> None:
        """Should handle Work Unit with no actions gracefully."""
        work_unit: dict[str, object] = {"actions": []}
        warnings = validate_content_density(work_unit, "test.yaml")
        assert len(warnings) == 0

    def test_handles_missing_actions(self) -> None:
        """Should handle Work Unit with missing actions field."""
        work_unit: dict[str, object] = {}
        warnings = validate_content_density(work_unit, "test.yaml")
        assert len(warnings) == 0

    def test_handles_non_string_actions(self) -> None:
        """Should skip non-string action items."""
        work_unit: dict[str, object] = {
            "actions": [123, None, "x" * 130],
        }
        warnings = validate_content_density(work_unit, "test.yaml")
        # Should not crash, valid string should not trigger warning
        assert not any(w.code in ("BULLET_TOO_SHORT", "BULLET_TOO_LONG") for w in warnings)

    def test_bullet_char_constants_reasonable(self) -> None:
        """Bullet character constants should be reasonable values."""
        assert BULLET_CHAR_MIN == 100
        assert BULLET_CHAR_MAX == 160
        assert BULLET_CHAR_MIN < BULLET_CHAR_MAX


class TestPositionReference:
    """Tests for position reference validation (Story 7.6)."""

    def test_missing_position_id_is_info_level(self) -> None:
        """Missing position_id should be info severity, not error (AC #2)."""
        work_unit: dict[str, object] = {"id": "wu-2024-01-01-test"}
        warnings = validate_position_reference(work_unit, "test.yaml")

        assert len(warnings) == 1
        assert warnings[0].code == "MISSING_POSITION_ID"
        assert warnings[0].severity == "info"

    def test_valid_position_id_no_warning(self) -> None:
        """Valid position_id should not produce warnings."""
        work_unit = {"position_id": "pos-acme-engineer"}
        valid_ids = {"pos-acme-engineer", "pos-other-company"}
        warnings = validate_position_reference(work_unit, "test.yaml", valid_ids)

        assert len(warnings) == 0

    def test_invalid_position_id_is_error_level(self) -> None:
        """Invalid position_id should be error severity (AC #1)."""
        work_unit = {"position_id": "pos-nonexistent"}
        valid_ids = {"pos-acme-engineer"}
        warnings = validate_position_reference(work_unit, "test.yaml", valid_ids)

        assert len(warnings) == 1
        assert warnings[0].code == "INVALID_POSITION_ID"
        assert warnings[0].severity == "error"

    def test_invalid_position_id_includes_value_in_message(self) -> None:
        """Error message should include the invalid position_id value (AC #1)."""
        work_unit = {"position_id": "pos-nonexistent"}
        valid_ids = {"pos-acme-engineer"}
        warnings = validate_position_reference(work_unit, "test.yaml", valid_ids)

        assert "pos-nonexistent" in warnings[0].message

    def test_invalid_position_id_suggests_similar(self) -> None:
        """Error should suggest similar position ID if available (AC #1)."""
        work_unit = {"position_id": "pos-acme-enginee"}  # Typo
        valid_ids = {"pos-acme-engineer", "pos-other-company"}
        warnings = validate_position_reference(work_unit, "test.yaml", valid_ids)

        assert len(warnings) == 1
        # Should suggest the similar ID
        assert "pos-acme-engineer" in warnings[0].suggestion
        assert "Did you mean" in warnings[0].suggestion

    def test_invalid_position_id_suggests_list_command(self) -> None:
        """Error should suggest running 'resume list positions'."""
        work_unit = {"position_id": "pos-totally-different"}
        valid_ids = {"pos-acme-engineer"}
        warnings = validate_position_reference(work_unit, "test.yaml", valid_ids)

        assert "resume list positions" in warnings[0].suggestion

    def test_no_valid_ids_provided_only_checks_missing(self) -> None:
        """Without valid_ids, only missing position_id is checked."""
        work_unit = {"position_id": "pos-any-value"}
        # valid_position_ids is None (not provided)
        warnings = validate_position_reference(work_unit, "test.yaml", None)

        # Should not produce any warnings when valid_ids not provided
        assert len(warnings) == 0
