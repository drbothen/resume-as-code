"""Tests for archetype inference service."""

from __future__ import annotations

from resume_as_code.models.work_unit import (
    Outcome,
    Problem,
    WorkUnit,
    WorkUnitArchetype,
)
from resume_as_code.services.archetype_inference_service import (
    MIN_CONFIDENCE_THRESHOLD,
    extract_text_content,
    infer_archetype,
    score_archetype,
)


class TestExtractTextContent:
    """Tests for text extraction."""

    def test_extracts_from_dict(self) -> None:
        """Should extract all text fields from dict."""
        data = {
            "title": "Resolved P1 outage",
            "problem": {"statement": "Database failed"},
            "actions": ["Diagnosed issue", "Fixed config"],
            "outcome": {"result": "Restored in 30 min"},
            "tags": ["incident-response"],
        }
        text = extract_text_content(data)
        assert "resolved p1 outage" in text
        assert "database failed" in text
        assert "incident-response" in text

    def test_extracts_quantified_impact(self) -> None:
        """Should extract quantified_impact from outcome."""
        data = {
            "title": "Cost reduction",
            "problem": {"statement": "High cloud costs"},
            "actions": ["Rightsized instances"],
            "outcome": {
                "result": "Reduced costs",
                "quantified_impact": "40% savings",
            },
            "tags": [],
        }
        text = extract_text_content(data)
        assert "40% savings" in text

    def test_extracts_business_value(self) -> None:
        """Should extract business_value from outcome."""
        data = {
            "title": "Performance improvement",
            "problem": {"statement": "Slow API"},
            "actions": ["Optimized queries"],
            "outcome": {
                "result": "Faster API",
                "business_value": "Improved customer experience",
            },
            "tags": [],
        }
        text = extract_text_content(data)
        assert "improved customer experience" in text

    def test_handles_missing_fields(self) -> None:
        """Should handle missing optional fields gracefully."""
        data = {
            "title": "Simple task",
        }
        text = extract_text_content(data)
        assert "simple task" in text

    def test_extracts_from_work_unit_object(self) -> None:
        """Should extract all text fields from WorkUnit object."""
        work_unit = WorkUnit(
            id="wu-2024-01-15-test-incident",
            title="Resolved P1 database outage",
            problem=Problem(statement="Production database failed unexpectedly"),
            actions=["Diagnosed issue", "Fixed configuration"],
            outcome=Outcome(result="Restored service in 30 minutes"),
            archetype=WorkUnitArchetype.INCIDENT,
            tags=["incident-response", "database"],
        )
        text = extract_text_content(work_unit)
        assert "resolved p1 database outage" in text
        assert "production database failed" in text
        assert "diagnosed issue" in text
        assert "restored service" in text
        assert "incident-response" in text

    def test_extracts_quantified_impact_from_work_unit(self) -> None:
        """Should extract quantified_impact from WorkUnit outcome."""
        work_unit = WorkUnit(
            id="wu-2024-01-15-cost-reduction",
            title="Optimized cloud infrastructure costs",
            problem=Problem(statement="Cloud spending exceeded budget by 40%"),
            actions=["Analyzed resource usage", "Rightsized instances"],
            outcome=Outcome(
                result="Reduced monthly cloud costs",
                quantified_impact="$50K monthly savings",
            ),
            archetype=WorkUnitArchetype.OPTIMIZATION,
            tags=[],
        )
        text = extract_text_content(work_unit)
        assert "$50k monthly savings" in text

    def test_extracts_business_value_from_work_unit(self) -> None:
        """Should extract business_value from WorkUnit outcome."""
        work_unit = WorkUnit(
            id="wu-2024-01-15-perf-improvement",
            title="Improved API response times significantly",
            problem=Problem(statement="API latency exceeded SLA requirements"),
            actions=["Profiled slow endpoints", "Optimized database queries"],
            outcome=Outcome(
                result="Reduced P99 latency by 60%",
                business_value="Improved customer satisfaction scores",
            ),
            archetype=WorkUnitArchetype.OPTIMIZATION,
            tags=[],
        )
        text = extract_text_content(work_unit)
        assert "improved customer satisfaction" in text


class TestScoreArchetype:
    """Tests for archetype scoring."""

    def test_incident_keywords_score_high(self) -> None:
        """Incident keywords should score high for INCIDENT archetype."""
        text = "resolved p1 outage, detected, triaged, mitigated incident"
        score = score_archetype(text, WorkUnitArchetype.INCIDENT)
        assert score > 0.3

    def test_migration_keywords_score_high(self) -> None:
        """Migration keywords should score high for MIGRATION archetype."""
        text = "migrated legacy database to cloud migration"
        score = score_archetype(text, WorkUnitArchetype.MIGRATION)
        assert score > 0.2

    def test_greenfield_keywords_score_high(self) -> None:
        """Greenfield keywords should score high for GREENFIELD archetype."""
        text = "built new system from scratch, designed and implemented"
        score = score_archetype(text, WorkUnitArchetype.GREENFIELD)
        assert score > 0.2

    def test_optimization_keywords_score_high(self) -> None:
        """Optimization keywords should score high for OPTIMIZATION archetype."""
        text = "optimized performance, reduced latency and cost reduction"
        score = score_archetype(text, WorkUnitArchetype.OPTIMIZATION)
        assert score > 0.2

    def test_leadership_keywords_score_high(self) -> None:
        """Leadership keywords should score high for LEADERSHIP archetype."""
        text = "mentored team members, coached engineers, aligned stakeholders"
        score = score_archetype(text, WorkUnitArchetype.LEADERSHIP)
        assert score > 0.2

    def test_strategic_keywords_score_high(self) -> None:
        """Strategic keywords should score high for STRATEGIC archetype."""
        text = "developed strategy, market analysis, competitive positioning"
        score = score_archetype(text, WorkUnitArchetype.STRATEGIC)
        assert score > 0.2

    def test_transformation_keywords_score_high(self) -> None:
        """Transformation keywords should score high for TRANSFORMATION archetype."""
        text = "led digital transformation, enterprise-wide organizational change"
        score = score_archetype(text, WorkUnitArchetype.TRANSFORMATION)
        assert score > 0.2

    def test_cultural_keywords_score_high(self) -> None:
        """Cultural keywords should score high for CULTURAL archetype."""
        text = "improved culture, talent development, employee engagement"
        score = score_archetype(text, WorkUnitArchetype.CULTURAL)
        assert score > 0.2

    def test_minimal_returns_zero(self) -> None:
        """MINIMAL archetype should return 0 score (no patterns)."""
        text = "some generic work was done"
        score = score_archetype(text, WorkUnitArchetype.MINIMAL)
        assert score == 0.0

    def test_no_match_returns_zero(self) -> None:
        """No pattern match should return 0."""
        text = "completely unrelated content about cooking recipes"
        score = score_archetype(text, WorkUnitArchetype.INCIDENT)
        assert score == 0.0


class TestInferArchetype:
    """Tests for archetype inference."""

    def test_infers_incident_from_p1_keywords(self) -> None:
        """Should infer INCIDENT from P1/outage keywords."""
        data = {
            "title": "Resolved P1 database outage affecting 10K users",
            "problem": {"statement": "Production database failed unexpectedly"},
            "actions": ["Detected via alerts", "Triaged impact", "Mitigated issue"],
            "outcome": {"result": "Restored service in 45 minutes"},
            "tags": ["incident-response"],
        }
        archetype, confidence = infer_archetype(data)
        assert archetype == WorkUnitArchetype.INCIDENT
        assert confidence >= 0.5

    def test_infers_greenfield_from_build_keywords(self) -> None:
        """Should infer GREENFIELD from new system keywords."""
        data = {
            "title": "Built new real-time analytics pipeline from scratch",
            "problem": {"statement": "No analytics capability existed in the org"},
            "actions": ["Designed architecture from ground-up", "Built data pipeline"],
            "outcome": {"result": "Launched new analytics platform"},
            "tags": ["new-system"],
        }
        archetype, confidence = infer_archetype(data)
        assert archetype == WorkUnitArchetype.GREENFIELD
        assert confidence >= 0.3

    def test_infers_migration_from_keywords(self) -> None:
        """Should infer MIGRATION from migration keywords."""
        data = {
            "title": "Migrated legacy monolith to cloud microservices",
            "problem": {"statement": "Legacy system was unmaintainable"},
            "actions": ["Transitioned database to AWS", "Upgraded platform"],
            "outcome": {"result": "Completed cloud migration on schedule"},
            "tags": ["cloud-migration"],
        }
        archetype, confidence = infer_archetype(data)
        assert archetype == WorkUnitArchetype.MIGRATION
        assert confidence >= 0.3

    def test_infers_optimization_from_keywords(self) -> None:
        """Should infer OPTIMIZATION from performance keywords."""
        data = {
            "title": "Optimized API performance for high-traffic endpoint",
            "problem": {"statement": "API latency was too high for users"},
            "actions": ["Profiled code", "Reduced latency by caching"],
            "outcome": {"result": "Improved performance by 60%"},
            "tags": ["performance"],
        }
        archetype, confidence = infer_archetype(data)
        assert archetype == WorkUnitArchetype.OPTIMIZATION
        assert confidence >= 0.3

    def test_returns_minimal_for_ambiguous_content(self) -> None:
        """Should return MINIMAL when content is ambiguous."""
        data = {
            "title": "Did some work on the project",
            "problem": {"statement": "There was a problem to solve"},
            "actions": ["Fixed it somehow"],
            "outcome": {"result": "It worked out fine"},
            "tags": [],
        }
        archetype, confidence = infer_archetype(data)
        assert archetype == WorkUnitArchetype.MINIMAL
        assert confidence < 0.5

    def test_custom_threshold_affects_result(self) -> None:
        """Should use custom threshold when provided."""
        data = {
            "title": "Some migration work",
            "problem": {"statement": "Old system needed updating"},
            "actions": ["Migrated the code"],
            "outcome": {"result": "Migration complete"},
            "tags": [],
        }
        # With high threshold, should return minimal
        archetype_high, confidence_high = infer_archetype(data, threshold=0.9)
        assert archetype_high == WorkUnitArchetype.MINIMAL

        # With low threshold, may return specific archetype
        archetype_low, confidence_low = infer_archetype(data, threshold=0.1)
        assert archetype_low in list(WorkUnitArchetype)
        assert confidence_low == confidence_high  # Confidence unchanged

    def test_confidence_always_between_zero_and_one(self) -> None:
        """Confidence should always be in [0.0, 1.0] range."""
        data = {
            "title": "P1 P2 outage incident detected triaged mitigated resolved",
            "problem": {"statement": "Everything broke at once in production"},
            "actions": ["Incident response on-call MTTR security event escalation"],
            "outcome": {"result": "Everything was resolved and mitigated"},
            "tags": ["incident-response", "p1"],
        }
        archetype, confidence = infer_archetype(data)
        assert 0.0 <= confidence <= 1.0


class TestMinConfidenceThreshold:
    """Tests for MIN_CONFIDENCE_THRESHOLD constant."""

    def test_default_threshold_is_half(self) -> None:
        """Default threshold should be 0.5."""
        assert MIN_CONFIDENCE_THRESHOLD == 0.5
