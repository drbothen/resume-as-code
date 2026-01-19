"""Unit tests for Work Unit archetype system.

Story 12.1: Add Required Archetype Field with Inference Migration

Tests cover:
- WorkUnitArchetype enum values and structure
- WorkUnit model requires archetype field
- Archetype inference service
- Confidence scoring
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from resume_as_code.models.work_unit import (
    Outcome,
    Problem,
    WorkUnit,
    WorkUnitArchetype,
)
from resume_as_code.services.archetype_inference import (
    ARCHETYPE_RULES,
    CONFIDENCE_THRESHOLD,
    ArchetypeInference,
    get_all_archetype_scores,
    infer_archetype,
)


class TestWorkUnitArchetypeEnum:
    """Tests for WorkUnitArchetype enum (Task 7.1)."""

    def test_archetype_enum_has_exactly_9_values(self) -> None:
        """WorkUnitArchetype should have exactly 9 values."""
        assert len(WorkUnitArchetype) == 9

    def test_archetype_enum_values(self) -> None:
        """WorkUnitArchetype should have all expected values."""
        expected = {
            "greenfield",
            "migration",
            "optimization",
            "incident",
            "leadership",
            "strategic",
            "transformation",
            "cultural",
            "minimal",
        }
        actual = {arch.value for arch in WorkUnitArchetype}
        assert actual == expected

    def test_archetype_enum_is_string_enum(self) -> None:
        """WorkUnitArchetype values should be strings."""
        for arch in WorkUnitArchetype:
            assert isinstance(arch.value, str)

    def test_archetype_values_are_lowercase(self) -> None:
        """Archetype values should be lowercase (match template filenames)."""
        for arch in WorkUnitArchetype:
            assert arch.value == arch.value.lower()

    def test_archetype_greenfield(self) -> None:
        """GREENFIELD archetype should exist with correct value."""
        assert WorkUnitArchetype.GREENFIELD.value == "greenfield"

    def test_archetype_migration(self) -> None:
        """MIGRATION archetype should exist with correct value."""
        assert WorkUnitArchetype.MIGRATION.value == "migration"

    def test_archetype_optimization(self) -> None:
        """OPTIMIZATION archetype should exist with correct value."""
        assert WorkUnitArchetype.OPTIMIZATION.value == "optimization"

    def test_archetype_incident(self) -> None:
        """INCIDENT archetype should exist with correct value."""
        assert WorkUnitArchetype.INCIDENT.value == "incident"

    def test_archetype_leadership(self) -> None:
        """LEADERSHIP archetype should exist with correct value."""
        assert WorkUnitArchetype.LEADERSHIP.value == "leadership"

    def test_archetype_strategic(self) -> None:
        """STRATEGIC archetype should exist with correct value."""
        assert WorkUnitArchetype.STRATEGIC.value == "strategic"

    def test_archetype_transformation(self) -> None:
        """TRANSFORMATION archetype should exist with correct value."""
        assert WorkUnitArchetype.TRANSFORMATION.value == "transformation"

    def test_archetype_cultural(self) -> None:
        """CULTURAL archetype should exist with correct value."""
        assert WorkUnitArchetype.CULTURAL.value == "cultural"

    def test_archetype_minimal(self) -> None:
        """MINIMAL archetype should exist with correct value."""
        assert WorkUnitArchetype.MINIMAL.value == "minimal"


class TestWorkUnitRequiresArchetype:
    """Tests for WorkUnit model requiring archetype field (Task 7.2)."""

    def test_work_unit_requires_archetype(self) -> None:
        """WorkUnit should REQUIRE archetype field (fail without it)."""
        with pytest.raises(ValidationError) as exc_info:
            WorkUnit(
                id="wu-2024-03-15-test",
                title="Test work unit title here",
                problem=Problem(statement="This is the problem statement here"),
                actions=["Action taken here for test"],
                outcome=Outcome(result="Result achieved here"),
                # Missing archetype - should fail
            )
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("archetype",)
        assert errors[0]["type"] == "missing"

    def test_work_unit_with_valid_archetype(self) -> None:
        """WorkUnit with valid archetype should pass validation."""
        wu = WorkUnit(
            id="wu-2024-03-15-test",
            title="Test work unit title here",
            problem=Problem(statement="This is the problem statement here"),
            actions=["Action taken here for test"],
            outcome=Outcome(result="Result achieved here"),
            archetype=WorkUnitArchetype.GREENFIELD,
        )
        assert wu.archetype == WorkUnitArchetype.GREENFIELD

    def test_work_unit_accepts_all_archetypes(self) -> None:
        """WorkUnit should accept all valid archetype values."""
        for archetype in WorkUnitArchetype:
            wu = WorkUnit(
                id="wu-2024-03-15-test",
                title="Test work unit title here",
                problem=Problem(statement="This is the problem statement here"),
                actions=["Action taken here for test"],
                outcome=Outcome(result="Result achieved here"),
                archetype=archetype,
            )
            assert wu.archetype == archetype

    def test_work_unit_accepts_archetype_string(self) -> None:
        """WorkUnit should accept archetype as string value."""
        wu = WorkUnit(
            id="wu-2024-03-15-test",
            title="Test work unit title here",
            problem=Problem(statement="This is the problem statement here"),
            actions=["Action taken here for test"],
            outcome=Outcome(result="Result achieved here"),
            archetype="optimization",  # String value
        )
        assert wu.archetype == WorkUnitArchetype.OPTIMIZATION

    def test_work_unit_rejects_invalid_archetype(self) -> None:
        """WorkUnit should reject invalid archetype value."""
        with pytest.raises(ValidationError) as exc_info:
            WorkUnit(
                id="wu-2024-03-15-test",
                title="Test work unit title here",
                problem=Problem(statement="This is the problem statement here"),
                actions=["Action taken here for test"],
                outcome=Outcome(result="Result achieved here"),
                archetype="invalid-archetype",
            )
        errors = exc_info.value.errors()
        assert errors[0]["loc"] == ("archetype",)

    def test_work_unit_schema_version_is_4_0_0(self) -> None:
        """WorkUnit default schema_version should be 4.0.0."""
        wu = WorkUnit(
            id="wu-2024-03-15-test",
            title="Test work unit title here",
            problem=Problem(statement="This is the problem statement here"),
            actions=["Action taken here for test"],
            outcome=Outcome(result="Result achieved here"),
            archetype=WorkUnitArchetype.MINIMAL,
        )
        assert wu.schema_version == "4.0.0"


class TestArchetypeInferenceResult:
    """Tests for ArchetypeInference NamedTuple."""

    def test_archetype_inference_is_namedtuple(self) -> None:
        """ArchetypeInference should be a NamedTuple."""
        result = ArchetypeInference(
            archetype=WorkUnitArchetype.GREENFIELD,
            confidence=0.8,
            matched_signals={"keywords": ["built"]},
        )
        assert result.archetype == WorkUnitArchetype.GREENFIELD
        assert result.confidence == 0.8
        assert result.matched_signals == {"keywords": ["built"]}

    def test_archetype_inference_unpacking(self) -> None:
        """ArchetypeInference should support unpacking."""
        result = ArchetypeInference(
            archetype=WorkUnitArchetype.MIGRATION,
            confidence=0.6,
            matched_signals={},
        )
        archetype, confidence, signals = result
        assert archetype == WorkUnitArchetype.MIGRATION
        assert confidence == 0.6
        assert signals == {}


class TestArchetypeInferenceService:
    """Tests for archetype inference service (Task 7.3)."""

    def test_infer_greenfield_from_keywords(self) -> None:
        """Should infer greenfield from 'built', 'created', 'designed' keywords."""
        work_unit_data = {
            "title": "Built new authentication platform",
            "problem": {"statement": "Need for secure authentication system"},
            "actions": ["Designed architecture", "Built the platform from scratch"],
            "outcome": {"result": "Launched new authentication system"},
            "tags": [],
        }
        result = infer_archetype(work_unit_data)
        assert result.archetype == WorkUnitArchetype.GREENFIELD
        assert result.confidence >= CONFIDENCE_THRESHOLD

    def test_infer_migration_from_keywords(self) -> None:
        """Should infer migration from 'migrated', 'legacy', 'upgraded' keywords."""
        work_unit_data = {
            "title": "Migrated legacy system to cloud",
            "problem": {"statement": "Legacy system was outdated and deprecated"},
            "actions": ["Migrated database", "Transitioned services"],
            "outcome": {"result": "Successfully upgraded infrastructure"},
            "tags": [],
        }
        result = infer_archetype(work_unit_data)
        assert result.archetype == WorkUnitArchetype.MIGRATION
        assert result.confidence >= CONFIDENCE_THRESHOLD

    def test_infer_optimization_from_keywords(self) -> None:
        """Should infer optimization from 'optimized', 'reduced', 'performance' keywords."""
        work_unit_data = {
            "title": "Optimized API response times",
            "problem": {"statement": "Slow performance causing latency issues"},
            "actions": ["Optimized database queries", "Reduced response times"],
            "outcome": {"result": "Improved performance by 60%"},
            "tags": [],
        }
        result = infer_archetype(work_unit_data)
        assert result.archetype == WorkUnitArchetype.OPTIMIZATION
        assert result.confidence >= CONFIDENCE_THRESHOLD

    def test_infer_incident_from_keywords(self) -> None:
        """Should infer incident from 'incident', 'outage', 'vulnerability' keywords."""
        work_unit_data = {
            "title": "Responded to production outage",
            "problem": {"statement": "Security vulnerability discovered in production"},
            "actions": ["Assessed impact", "Remediated the issue"],
            "outcome": {"result": "Incident resolved with no data breach"},
            "tags": [],
        }
        result = infer_archetype(work_unit_data)
        assert result.archetype == WorkUnitArchetype.INCIDENT
        assert result.confidence >= CONFIDENCE_THRESHOLD

    def test_infer_leadership_from_keywords(self) -> None:
        """Should infer leadership from 'led', 'mentored', 'hired' keywords."""
        work_unit_data = {
            "title": "Led engineering team growth",
            "problem": {"statement": "Team gap in capability and talent"},
            "actions": ["Hired 10 engineers", "Mentored junior developers"],
            "outcome": {"result": "Grew team from 5 to 15 engineers"},
            "tags": [],
        }
        result = infer_archetype(work_unit_data)
        assert result.archetype == WorkUnitArchetype.LEADERSHIP
        assert result.confidence >= CONFIDENCE_THRESHOLD

    def test_infer_strategic_from_keywords(self) -> None:
        """Should infer strategic from 'strategy', 'roadmap', 'framework' keywords."""
        work_unit_data = {
            "title": "Developed technical roadmap",
            "problem": {"statement": "Inconsistent standards across organization"},
            "actions": ["Developed framework", "Established governance standards"],
            "outcome": {"result": "Aligned organization on technical vision"},
            "tags": [],
        }
        result = infer_archetype(work_unit_data)
        assert result.archetype == WorkUnitArchetype.STRATEGIC
        assert result.confidence >= CONFIDENCE_THRESHOLD

    def test_infer_transformation_from_keywords(self) -> None:
        """Should infer transformation from 'transformed', 'enterprise', 'scaled' keywords."""
        work_unit_data = {
            "title": "Transformed enterprise architecture",
            "problem": {"statement": "Organizational need for digital transformation"},
            "actions": ["Transformed processes", "Scaled company-wide"],
            "outcome": {"result": "Revolutionized how the enterprise operates"},
            "tags": [],
        }
        result = infer_archetype(work_unit_data)
        assert result.archetype == WorkUnitArchetype.TRANSFORMATION
        assert result.confidence >= CONFIDENCE_THRESHOLD

    def test_infer_cultural_from_keywords(self) -> None:
        """Should infer cultural from 'culture', 'dei', 'engagement' keywords."""
        work_unit_data = {
            "title": "Championed diversity and inclusion",
            "problem": {"statement": "Culture and engagement needed improvement"},
            "actions": ["Fostered inclusive culture", "Promoted DEI initiatives"],
            "outcome": {"result": "Improved employee morale and retention"},
            "tags": [],
        }
        result = infer_archetype(work_unit_data)
        assert result.archetype == WorkUnitArchetype.CULTURAL
        assert result.confidence >= CONFIDENCE_THRESHOLD

    def test_infer_from_tags(self) -> None:
        """Should use tags for inference with 40% weight."""
        work_unit_data = {
            "title": "Project work",
            "problem": {"statement": "Generic problem statement here"},
            "actions": ["Did some work here"],
            "outcome": {"result": "Achieved results"},
            "tags": ["greenfield", "architecture", "launch"],
        }
        result = infer_archetype(work_unit_data)
        assert result.archetype == WorkUnitArchetype.GREENFIELD
        assert "tags" in result.matched_signals

    def test_minimal_fallback_low_confidence(self) -> None:
        """Should fall back to minimal when confidence is below threshold."""
        work_unit_data = {
            "title": "Generic work done",
            "problem": {"statement": "Something needed doing"},
            "actions": ["Did something"],
            "outcome": {"result": "Something happened"},
            "tags": [],
        }
        result = infer_archetype(work_unit_data)
        assert result.archetype == WorkUnitArchetype.MINIMAL
        assert result.confidence < CONFIDENCE_THRESHOLD

    def test_handles_empty_work_unit(self) -> None:
        """Should handle work unit with minimal data."""
        work_unit_data = {}
        result = infer_archetype(work_unit_data)
        assert result.archetype == WorkUnitArchetype.MINIMAL
        assert result.confidence == 0.1  # Default low confidence

    def test_handles_missing_tags(self) -> None:
        """Should handle work unit without tags field."""
        work_unit_data = {
            "title": "Built new system",
            "problem": {"statement": "Needed new capability"},
            "actions": ["Designed and built system"],
            "outcome": {"result": "Launched successfully"},
        }
        result = infer_archetype(work_unit_data)
        assert result.archetype is not None  # Should not crash

    def test_handles_invalid_tags_type(self) -> None:
        """Should handle tags field that is not a list."""
        work_unit_data = {
            "title": "Built new system",
            "tags": "not-a-list",  # Invalid type
        }
        result = infer_archetype(work_unit_data)
        assert result.archetype is not None  # Should not crash


class TestArchetypeConfidenceScoring:
    """Tests for confidence scoring (Task 7.4)."""

    def test_confidence_range_0_to_1(self) -> None:
        """Confidence scores should be between 0.0 and 1.0."""
        # Test with various inputs
        test_cases = [
            {"title": "Built system", "tags": ["greenfield"]},
            {"title": "Generic task", "tags": []},
            {"title": "Migrated database", "tags": ["migration"]},
        ]
        for data in test_cases:
            result = infer_archetype(data)
            assert 0.0 <= result.confidence <= 1.0

    def test_confidence_threshold_constant(self) -> None:
        """CONFIDENCE_THRESHOLD should be 0.3."""
        assert CONFIDENCE_THRESHOLD == 0.3

    def test_high_confidence_multiple_signals(self) -> None:
        """Should have higher confidence with multiple matching signals."""
        # Strong greenfield signals
        work_unit_data = {
            "title": "Built and designed new platform from scratch",
            "problem": {"statement": "Gap in capability, need for new system"},
            "actions": ["Architected the solution", "Engineered the platform", "Created APIs"],
            "outcome": {"result": "Launched new platform"},
            "tags": ["greenfield", "architecture", "platform"],
        }
        result = infer_archetype(work_unit_data)
        assert result.confidence > 0.5  # Strong signals = high confidence

    def test_matched_signals_populated(self) -> None:
        """Should populate matched_signals with what matched."""
        work_unit_data = {
            "title": "Built new authentication platform",
            "problem": {"statement": "Need secure login"},
            "actions": ["Designed architecture"],
            "outcome": {"result": "Launched system"},
            "tags": ["greenfield"],
        }
        result = infer_archetype(work_unit_data)
        assert len(result.matched_signals) > 0
        # Should have either keywords, tags, or signals
        assert any(k in result.matched_signals for k in ["keywords", "tags", "signals"])


class TestArchetypeRules:
    """Tests for archetype classification rules."""

    def test_archetype_rules_defined_for_all_types(self) -> None:
        """ARCHETYPE_RULES should have rules for all archetype types."""
        for archetype in WorkUnitArchetype:
            assert archetype.value in ARCHETYPE_RULES

    def test_each_archetype_has_keywords(self) -> None:
        """Each non-minimal archetype should have keywords."""
        for name, rules in ARCHETYPE_RULES.items():
            if name != "minimal":
                assert "keywords" in rules
                assert len(rules["keywords"]) > 0

    def test_each_archetype_has_tags(self) -> None:
        """Each archetype should have tag rules."""
        for _name, rules in ARCHETYPE_RULES.items():
            assert "tags" in rules

    def test_minimal_has_empty_keywords(self) -> None:
        """Minimal archetype should have empty keywords (fallback)."""
        assert ARCHETYPE_RULES["minimal"]["keywords"] == []


class TestGetAllArchetypeScores:
    """Tests for get_all_archetype_scores helper function."""

    def test_returns_all_archetypes(self) -> None:
        """Should return scores for all archetype types."""
        work_unit_data = {"title": "Test work"}
        scores = get_all_archetype_scores(work_unit_data)
        assert len(scores) == 9  # All archetypes

    def test_sorted_by_score_descending(self) -> None:
        """Scores should be sorted by score descending."""
        work_unit_data = {
            "title": "Built new platform",
            "tags": ["greenfield"],
        }
        scores = get_all_archetype_scores(work_unit_data)
        for i in range(len(scores) - 1):
            assert scores[i][1] >= scores[i + 1][1]

    def test_returns_tuple_of_archetype_and_score(self) -> None:
        """Each item should be (WorkUnitArchetype, float) tuple."""
        work_unit_data = {"title": "Test work"}
        scores = get_all_archetype_scores(work_unit_data)
        for archetype, score in scores:
            assert isinstance(archetype, WorkUnitArchetype)
            assert isinstance(score, float)
