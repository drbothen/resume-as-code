"""Tests for validation message mappings."""

from __future__ import annotations

from resume_as_code.utils.validation_messages import (
    ENUM_FIELDS,
    FIELD_SUGGESTIONS,
    TYPE_EXAMPLES,
    get_enum_values,
    get_suggestion_for_field,
    get_type_example,
)


class TestFieldSuggestions:
    """Tests for field suggestion lookup."""

    def test_exact_match_title(self) -> None:
        """Should return suggestion for exact title field match."""
        suggestion = get_suggestion_for_field("title")
        assert "title" in suggestion.lower()
        assert len(suggestion) > 10  # Should be helpful, not empty

    def test_exact_match_problem_statement(self) -> None:
        """Should return suggestion for problem.statement field."""
        suggestion = get_suggestion_for_field("problem.statement")
        assert "challenge" in suggestion.lower() or "problem" in suggestion.lower()

    def test_exact_match_actions(self) -> None:
        """Should return suggestion for actions field."""
        suggestion = get_suggestion_for_field("actions")
        assert "action" in suggestion.lower()

    def test_exact_match_outcome_result(self) -> None:
        """Should return suggestion for outcome.result field."""
        suggestion = get_suggestion_for_field("outcome.result")
        assert "result" in suggestion.lower() or "impact" in suggestion.lower()

    def test_exact_match_id(self) -> None:
        """Should return suggestion for id field."""
        suggestion = get_suggestion_for_field("id")
        assert "wu-" in suggestion.lower() or "id" in suggestion.lower()

    def test_exact_match_schema_version(self) -> None:
        """Should return suggestion for schema_version field."""
        suggestion = get_suggestion_for_field("schema_version")
        assert "1.0.0" in suggestion or "schema" in suggestion.lower()

    def test_nested_field_partial_match(self) -> None:
        """Should return suggestion for nested field via partial match."""
        # If problem.statement exists in FIELD_SUGGESTIONS, nested paths should match
        suggestion = get_suggestion_for_field("data.problem.statement")
        # Should still match against "problem.statement" or "statement"
        assert len(suggestion) > 10

    def test_unknown_field_returns_generic(self) -> None:
        """Should return generic suggestion for completely unknown fields."""
        suggestion = get_suggestion_for_field("completely_unknown_field_xyz")
        assert "schema" in suggestion.lower()


class TestTypeExamples:
    """Tests for type example lookup."""

    def test_string_type(self) -> None:
        """Should return string example."""
        example = get_type_example("string")
        assert "example" in example.lower() or '"' in example

    def test_array_type(self) -> None:
        """Should return array example."""
        example = get_type_example("array")
        assert "[" in example

    def test_object_type(self) -> None:
        """Should return object example."""
        example = get_type_example("object")
        assert ":" in example or "key" in example.lower()

    def test_number_type(self) -> None:
        """Should return number example."""
        example = get_type_example("number")
        assert any(char.isdigit() for char in example)

    def test_boolean_type(self) -> None:
        """Should return boolean example."""
        example = get_type_example("boolean")
        assert "true" in example.lower() or "false" in example.lower()

    def test_integer_type(self) -> None:
        """Should return integer example."""
        example = get_type_example("integer")
        assert any(char.isdigit() for char in example)

    def test_unknown_type_returns_generic(self) -> None:
        """Should return generic message for unknown types."""
        example = get_type_example("custom_type")
        assert "custom_type" in example


class TestEnumValues:
    """Tests for enum value lookup."""

    def test_confidence_values(self) -> None:
        """Should return confidence enum values."""
        values = get_enum_values("confidence")
        assert values is not None
        assert "high" in values
        assert "medium" in values
        assert "low" in values

    def test_nested_confidence_path(self) -> None:
        """Should match confidence at end of path."""
        values = get_enum_values("work_unit.confidence")
        assert values is not None
        assert "high" in values

    def test_evidence_type_values(self) -> None:
        """Should return evidence type enum values."""
        values = get_enum_values("evidence.type")
        assert values is not None
        assert "git_repo" in values

    def test_impact_category_values(self) -> None:
        """Should return impact_category enum values."""
        values = get_enum_values("impact_category")
        assert values is not None
        assert "financial" in values

    def test_unknown_enum_returns_none(self) -> None:
        """Should return None for fields without known enum values."""
        values = get_enum_values("not_an_enum_field")
        assert values is None


class TestDictConstants:
    """Tests for the exported constant dictionaries."""

    def test_field_suggestions_has_required_fields(self) -> None:
        """FIELD_SUGGESTIONS should include all required Work Unit fields."""
        required_keys = ["title", "problem", "actions", "outcome", "id"]
        for key in required_keys:
            # Key or nested key should be present
            assert any(key in k for k in FIELD_SUGGESTIONS), f"Missing suggestion for {key}"

    def test_type_examples_has_common_types(self) -> None:
        """TYPE_EXAMPLES should include common JSON Schema types."""
        common_types = ["string", "array", "object", "number", "boolean"]
        for t in common_types:
            assert t in TYPE_EXAMPLES, f"Missing example for type {t}"

    def test_enum_fields_has_confidence(self) -> None:
        """ENUM_FIELDS should include the confidence field."""
        # confidence at root level should be covered
        has_confidence = any("confidence" in k for k in ENUM_FIELDS)
        assert has_confidence, "Missing enum values for confidence field"
