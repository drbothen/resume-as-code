"""Tests for archetype inference service.

Story 12.6: Updated for hybrid regex + semantic inference.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from resume_as_code.services.embedder import EmbeddingService

from resume_as_code.models.work_unit import (
    Outcome,
    Problem,
    WorkUnit,
    WorkUnitArchetype,
)
from resume_as_code.services.archetype_inference_service import (
    ARCHETYPE_DESCRIPTIONS,
    ARCHETYPE_PATTERNS_WEIGHTED,
    MIN_CONFIDENCE_THRESHOLD,
    SEMANTIC_CONFIDENCE_THRESHOLD,
    extract_text_content,
    infer_archetype,
    infer_archetype_hybrid,
    score_semantic,
    score_weighted_regex,
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


class TestWeightedRegexScoring:
    """Tests for weighted pattern scoring."""

    def test_strong_signal_scores_higher(self) -> None:
        """P1 (weight 3.0) should contribute more than detected (weight 1.0)."""
        text_p1 = "resolved p1 issue"
        text_detected = "detected an issue"

        score_p1 = score_weighted_regex(text_p1, WorkUnitArchetype.INCIDENT)
        score_detected = score_weighted_regex(text_detected, WorkUnitArchetype.INCIDENT)

        assert score_p1 > score_detected

    def test_multiple_strong_signals_accumulate(self) -> None:
        """Multiple high-weight matches should score higher."""
        text = "resolved p1 outage, triaged and mitigated incident"
        score = score_weighted_regex(text, WorkUnitArchetype.INCIDENT)
        assert score > 0.4

    def test_incident_keywords_score_high(self) -> None:
        """Incident keywords should score high for INCIDENT archetype."""
        text = "resolved p1 outage, detected, triaged, mitigated incident"
        score = score_weighted_regex(text, WorkUnitArchetype.INCIDENT)
        assert score > 0.3

    def test_migration_keywords_score_high(self) -> None:
        """Migration keywords should score high for MIGRATION archetype."""
        text = "migrated legacy database to cloud migration"
        score = score_weighted_regex(text, WorkUnitArchetype.MIGRATION)
        assert score > 0.2

    def test_greenfield_keywords_score_high(self) -> None:
        """Greenfield keywords should score high for GREENFIELD archetype."""
        text = "built new system from scratch, designed and implemented"
        score = score_weighted_regex(text, WorkUnitArchetype.GREENFIELD)
        assert score > 0.2

    def test_optimization_keywords_score_high(self) -> None:
        """Optimization keywords should score high for OPTIMIZATION archetype."""
        text = "optimized performance, reduced latency and cost reduction"
        score = score_weighted_regex(text, WorkUnitArchetype.OPTIMIZATION)
        assert score > 0.2

    def test_leadership_keywords_score_high(self) -> None:
        """Leadership keywords should score high for LEADERSHIP archetype."""
        text = "mentored team members, coached engineers, aligned stakeholders"
        score = score_weighted_regex(text, WorkUnitArchetype.LEADERSHIP)
        assert score > 0.2

    def test_strategic_keywords_score_high(self) -> None:
        """Strategic keywords should score high for STRATEGIC archetype."""
        text = "developed strategy, market analysis, competitive positioning"
        score = score_weighted_regex(text, WorkUnitArchetype.STRATEGIC)
        assert score > 0.2

    def test_transformation_keywords_score_high(self) -> None:
        """Transformation keywords should score high for TRANSFORMATION archetype."""
        text = "led digital transformation, enterprise-wide organizational change"
        score = score_weighted_regex(text, WorkUnitArchetype.TRANSFORMATION)
        assert score > 0.2

    def test_cultural_keywords_score_high(self) -> None:
        """Cultural keywords should score high for CULTURAL archetype."""
        text = "improved culture, talent development, employee engagement"
        score = score_weighted_regex(text, WorkUnitArchetype.CULTURAL)
        assert score > 0.2

    def test_minimal_returns_zero(self) -> None:
        """MINIMAL archetype should return 0 score (no patterns)."""
        text = "some generic work was done"
        score = score_weighted_regex(text, WorkUnitArchetype.MINIMAL)
        assert score == 0.0

    def test_no_match_returns_zero(self) -> None:
        """No pattern match should return 0."""
        text = "completely unrelated content about cooking recipes"
        score = score_weighted_regex(text, WorkUnitArchetype.INCIDENT)
        assert score == 0.0


class TestSemanticScoring:
    """Tests for semantic embedding scoring."""

    @pytest.fixture
    def mock_embedding_service(self) -> MagicMock:
        """Create a mock embedding service."""
        mock = MagicMock()
        # Default similarity returns 0.5
        mock.similarity.return_value = 0.5
        return mock

    def test_calls_embedding_service_similarity(self, mock_embedding_service: MagicMock) -> None:
        """Should call embedding_service.similarity()."""
        text = "some work unit text"
        archetype = WorkUnitArchetype.GREENFIELD

        score_semantic(text, archetype, mock_embedding_service)

        mock_embedding_service.similarity.assert_called_once()
        call_args = mock_embedding_service.similarity.call_args
        assert call_args[0][0] == text
        assert call_args[0][1] == ARCHETYPE_DESCRIPTIONS[archetype]

    def test_returns_similarity_score(self, mock_embedding_service: MagicMock) -> None:
        """Should return the similarity score from embedding service."""
        mock_embedding_service.similarity.return_value = 0.75
        score = score_semantic("test text", WorkUnitArchetype.INCIDENT, mock_embedding_service)
        assert score == 0.75

    def test_returns_zero_for_minimal(self, mock_embedding_service: MagicMock) -> None:
        """Should return 0 for MINIMAL (no description)."""
        score = score_semantic("test text", WorkUnitArchetype.MINIMAL, mock_embedding_service)
        assert score == 0.0
        mock_embedding_service.similarity.assert_not_called()


class TestHybridInference:
    """Tests for hybrid inference."""

    @pytest.fixture
    def mock_embedding_service(self) -> MagicMock:
        """Create a mock embedding service."""
        mock = MagicMock()
        # Default: all semantic scores return 0.4 (above semantic threshold)
        mock.similarity.return_value = 0.4
        return mock

    def test_uses_regex_when_confident(self, mock_embedding_service: MagicMock) -> None:
        """Should use regex result when confidence is high."""
        data = {
            "title": "Resolved P1 database outage affecting production",
            "problem": {"statement": "Critical outage detected"},
            "actions": ["Triaged", "Mitigated", "Resolved"],
            "outcome": {"result": "Restored in 30 min"},
            "tags": ["incident-response"],
        }

        archetype, confidence, method = infer_archetype_hybrid(data, mock_embedding_service)

        assert archetype == WorkUnitArchetype.INCIDENT
        assert method == "regex"
        # Embedding service should not be called when regex is confident
        mock_embedding_service.similarity.assert_not_called()

    def test_falls_back_to_semantic(self, mock_embedding_service: MagicMock) -> None:
        """Should use semantic when regex confidence is low."""

        # Make semantic return high score for greenfield
        def side_effect(text: str, description: str) -> float:
            if "greenfield" in description.lower() or "built new" in description.lower():
                return 0.7
            return 0.2

        mock_embedding_service.similarity.side_effect = side_effect

        data = {
            "title": "Achieved first-attempt ATO for submarine base",
            "problem": {"statement": "Required security authorization"},
            "actions": ["Developed security documentation", "Conducted assessments"],
            "outcome": {"result": "Obtained Authority to Operate"},
            "tags": ["compliance", "cybersecurity"],
        }

        archetype, confidence, method = infer_archetype_hybrid(data, mock_embedding_service)

        # Should use semantic method
        assert method == "semantic"
        # Embedding service should be called for semantic scoring
        assert mock_embedding_service.similarity.call_count > 0

    def test_returns_fallback_when_uncertain(self, mock_embedding_service: MagicMock) -> None:
        """Should return minimal with fallback method when both approaches fail."""
        mock_embedding_service.similarity.return_value = 0.1  # Low semantic score

        data = {
            "title": "Did some work",
            "problem": {"statement": "Had a task"},
            "actions": ["Worked on it"],
            "outcome": {"result": "Completed"},
            "tags": [],
        }

        archetype, confidence, method = infer_archetype_hybrid(
            data,
            mock_embedding_service,
            regex_threshold=0.5,
            semantic_threshold=0.5,
        )

        assert archetype == WorkUnitArchetype.MINIMAL
        assert method == "fallback"

    def test_returns_fallback_when_ambiguous(self, mock_embedding_service: MagicMock) -> None:
        """Should return minimal when semantic scores are too similar (low distinctiveness)."""
        # All archetypes score nearly the same - no clear winner
        mock_embedding_service.similarity.return_value = 0.85  # High but uniform

        data = {
            "title": "Did some general work on the project",
            "problem": {"statement": "There was something to do"},
            "actions": ["Worked on it"],
            "outcome": {"result": "It was completed"},
            "tags": [],
        }

        archetype, confidence, method = infer_archetype_hybrid(
            data,
            mock_embedding_service,
            regex_threshold=0.5,
            semantic_threshold=0.3,
            distinctiveness_gap=0.02,  # 2% gap required
        )

        # Should return minimal because all scores are identical (zero gap)
        assert archetype == WorkUnitArchetype.MINIMAL
        assert method == "fallback"
        # Confidence should be low due to ambiguity
        assert confidence < 0.5


class TestInferArchetypeFunction:
    """Tests for main infer_archetype function."""

    @pytest.fixture
    def mock_embedding_service(self) -> MagicMock:
        """Create a mock embedding service."""
        mock = MagicMock()
        mock.similarity.return_value = 0.4
        return mock

    def test_returns_three_tuple(self, mock_embedding_service: MagicMock) -> None:
        """infer_archetype() should return (archetype, confidence, method)."""
        # Strong migration signals to ensure regex confidence
        data = {
            "title": "Migrated legacy database to cloud migration",
            "problem": {"statement": "Legacy system needed cloud migration"},
            "actions": ["Transitioned to AWS", "Executed database migration cutover"],
            "outcome": {"result": "Completed cloud migration successfully"},
            "tags": ["migration"],
        }

        result = infer_archetype(data, mock_embedding_service)

        assert len(result) == 3
        archetype, confidence, method = result
        assert archetype == WorkUnitArchetype.MIGRATION
        assert isinstance(confidence, float)
        assert method in ("regex", "semantic", "fallback")

    def test_infers_incident_from_p1_keywords(self, mock_embedding_service: MagicMock) -> None:
        """Should infer INCIDENT from P1/outage keywords."""
        data = {
            "title": "Resolved P1 database outage affecting 10K users",
            "problem": {"statement": "Production database failed unexpectedly"},
            "actions": ["Detected via alerts", "Triaged impact", "Mitigated issue"],
            "outcome": {"result": "Restored service in 45 minutes"},
            "tags": ["incident-response"],
        }
        archetype, confidence, method = infer_archetype(data, mock_embedding_service)
        assert archetype == WorkUnitArchetype.INCIDENT
        assert confidence >= 0.5
        assert method == "regex"

    def test_infers_greenfield_from_build_keywords(self, mock_embedding_service: MagicMock) -> None:
        """Should infer GREENFIELD from new system keywords."""
        # Strong signals: "from scratch" (3.0), "built new" (2.5), "architected" (2.0),
        # "pioneered" (2.5), "launched" (2.0), "stood up" (2.0)
        data = {
            "title": "Architected and built new real-time analytics pipeline from scratch",
            "problem": {"statement": "No analytics capability existed - pioneered first solution"},
            "actions": ["Designed architecture from scratch", "Stood up new data pipeline"],
            "outcome": {"result": "Launched new analytics platform successfully"},
            "tags": ["new-system", "greenfield"],
        }
        archetype, confidence, method = infer_archetype(data, mock_embedding_service)
        assert archetype == WorkUnitArchetype.GREENFIELD
        assert confidence >= 0.3

    def test_infers_migration_from_keywords(self, mock_embedding_service: MagicMock) -> None:
        """Should infer MIGRATION from migration keywords."""
        data = {
            "title": "Migrated legacy monolith to cloud microservices",
            "problem": {"statement": "Legacy system was unmaintainable"},
            "actions": ["Transitioned database to AWS", "Upgraded platform"],
            "outcome": {"result": "Completed cloud migration on schedule"},
            "tags": ["cloud-migration"],
        }
        archetype, confidence, method = infer_archetype(data, mock_embedding_service)
        assert archetype == WorkUnitArchetype.MIGRATION
        assert confidence >= 0.3

    def test_infers_optimization_from_keywords(self, mock_embedding_service: MagicMock) -> None:
        """Should infer OPTIMIZATION from performance keywords."""
        # Strong signals: "optimized" (3.0), "reduced latency" (2.5), "cost reduction" (2.5)
        data = {
            "title": "Optimized API performance achieving 60% reduction",
            "problem": {"statement": "High latency causing poor performance"},
            "actions": ["Profiled bottleneck code", "Reduced latency by caching"],
            "outcome": {"result": "Achieved cost reduction and latency reduction"},
            "tags": ["optimization", "performance"],
        }
        archetype, confidence, method = infer_archetype(data, mock_embedding_service)
        assert archetype == WorkUnitArchetype.OPTIMIZATION
        assert confidence >= 0.3

    def test_returns_minimal_for_ambiguous_content(self, mock_embedding_service: MagicMock) -> None:
        """Should return MINIMAL when content is ambiguous."""
        mock_embedding_service.similarity.return_value = 0.1  # Low semantic score

        data = {
            "title": "Did some work on the project",
            "problem": {"statement": "There was a problem to solve"},
            "actions": ["Fixed it somehow"],
            "outcome": {"result": "It worked out fine"},
            "tags": [],
        }
        archetype, confidence, method = infer_archetype(data, mock_embedding_service)
        assert archetype == WorkUnitArchetype.MINIMAL
        assert confidence < 0.5

    def test_custom_threshold_affects_result(self, mock_embedding_service: MagicMock) -> None:
        """Should use custom threshold when provided."""
        mock_embedding_service.similarity.return_value = 0.2

        data = {
            "title": "Some migration work",
            "problem": {"statement": "Old system needed updating"},
            "actions": ["Migrated the code"],
            "outcome": {"result": "Migration complete"},
            "tags": [],
        }
        # With high threshold, should return minimal
        archetype_high, confidence_high, _ = infer_archetype(
            data, mock_embedding_service, threshold=0.9
        )
        assert archetype_high == WorkUnitArchetype.MINIMAL

        # With low threshold, may return specific archetype
        archetype_low, confidence_low, _ = infer_archetype(
            data, mock_embedding_service, threshold=0.1
        )
        assert archetype_low in list(WorkUnitArchetype)

    def test_confidence_always_between_zero_and_one(
        self, mock_embedding_service: MagicMock
    ) -> None:
        """Confidence should always be in [0.0, 1.0] range."""
        data = {
            "title": "P1 P2 outage incident detected triaged mitigated resolved",
            "problem": {"statement": "Everything broke at once in production"},
            "actions": ["Incident response on-call MTTR security event escalation"],
            "outcome": {"result": "Everything was resolved and mitigated"},
            "tags": ["incident-response", "p1"],
        }
        archetype, confidence, method = infer_archetype(data, mock_embedding_service)
        assert 0.0 <= confidence <= 1.0


class TestMinConfidenceThreshold:
    """Tests for MIN_CONFIDENCE_THRESHOLD constant."""

    def test_default_threshold_is_half(self) -> None:
        """Default threshold should be 0.5."""
        assert MIN_CONFIDENCE_THRESHOLD == 0.5

    def test_semantic_threshold_is_lower(self) -> None:
        """Semantic threshold should be lower than regex threshold."""
        assert SEMANTIC_CONFIDENCE_THRESHOLD < MIN_CONFIDENCE_THRESHOLD
        assert SEMANTIC_CONFIDENCE_THRESHOLD == 0.3


class TestArchetypePatterns:
    """Tests for archetype pattern constants."""

    def test_all_archetypes_have_weighted_patterns(self) -> None:
        """All non-MINIMAL archetypes should have weighted patterns."""
        for archetype in WorkUnitArchetype:
            if archetype == WorkUnitArchetype.MINIMAL:
                continue
            assert archetype in ARCHETYPE_PATTERNS_WEIGHTED
            assert len(ARCHETYPE_PATTERNS_WEIGHTED[archetype]) > 0

    def test_all_patterns_have_positive_weights(self) -> None:
        """All pattern weights should be positive."""
        for archetype, patterns in ARCHETYPE_PATTERNS_WEIGHTED.items():
            for pattern, weight in patterns:
                assert weight > 0, f"{archetype}: {pattern} has non-positive weight"


class TestArchetypeDescriptions:
    """Tests for archetype description constants."""

    def test_all_archetypes_have_descriptions(self) -> None:
        """All non-MINIMAL archetypes should have descriptions."""
        for archetype in WorkUnitArchetype:
            if archetype == WorkUnitArchetype.MINIMAL:
                continue
            assert archetype in ARCHETYPE_DESCRIPTIONS
            assert len(ARCHETYPE_DESCRIPTIONS[archetype]) > 0

    def test_descriptions_are_meaningful_length(self) -> None:
        """Descriptions should be meaningful length (>50 chars)."""
        for archetype, description in ARCHETYPE_DESCRIPTIONS.items():
            assert len(description) > 50, f"{archetype} description too short"


class TestAccuracyWithRealEmbeddings:
    """End-to-end accuracy tests using real embedding service.

    These tests verify that the hybrid inference correctly classifies
    known work unit examples. They use the real embedding model.

    Test coverage: 15 cases covering all 8 archetypes + ambiguous cases.
    Target accuracy: 93%+ (14/15 cases correct)
    """

    @pytest.fixture
    def embedding_service(self) -> EmbeddingService:
        """Create a real embedding service."""
        from resume_as_code.services.embedder import EmbeddingService

        return EmbeddingService()

    # === INCIDENT (2 cases) ===

    def test_incident_p1_outage(self, embedding_service: EmbeddingService) -> None:
        """P1 database outage should classify as incident via regex."""
        data = {
            "title": "Resolved P1 database outage affecting production",
            "problem": {"statement": "Critical outage detected in production cluster"},
            "actions": ["Triaged incident", "Mitigated impact", "Resolved root cause"],
            "outcome": {"result": "Restored service in 30 minutes, reduced MTTR"},
            "tags": ["incident-response", "on-call"],
        }
        archetype, confidence, _method = infer_archetype(data, embedding_service)
        assert archetype == WorkUnitArchetype.INCIDENT
        assert confidence >= 0.5

    def test_incident_security_breach(self, embedding_service: EmbeddingService) -> None:
        """Security breach response should classify as incident."""
        data = {
            "title": "Responded to critical security breach and restored operations",
            "problem": {"statement": "Detected unauthorized access to production database"},
            "actions": [
                "Led incident response team in war room for 72 hours",
                "Mitigated breach by isolating affected systems",
                "Conducted root cause analysis and postmortem",
            ],
            "outcome": {"result": "Contained breach in 4 hours, no customer data exfiltrated"},
            "tags": ["incident-response", "security-incident"],
        }
        archetype, confidence, _method = infer_archetype(data, embedding_service)
        assert archetype == WorkUnitArchetype.INCIDENT
        assert confidence >= 0.5

    # === GREENFIELD (2 cases) ===

    def test_greenfield_ato_authorization(self, embedding_service: EmbeddingService) -> None:
        """First-attempt ATO should classify as greenfield."""
        data = {
            "title": "Achieved first-attempt ATO for submarine base security",
            "problem": {
                "statement": "Required Authority to Operate for facility industrial controls"
            },
            "actions": [
                "Developed comprehensive security documentation package",
                "Conducted vulnerability assessments and penetration testing",
                "Implemented RMF compliance controls",
            ],
            "outcome": {"result": "Obtained ATO authorization on first submission"},
            "tags": ["compliance", "cybersecurity", "rmf"],
        }
        archetype, confidence, _method = infer_archetype(data, embedding_service)
        assert archetype == WorkUnitArchetype.GREENFIELD
        assert confidence >= 0.5

    def test_greenfield_new_product(self, embedding_service: EmbeddingService) -> None:
        """New product built from scratch should classify as greenfield."""
        data = {
            "title": "Built new customer self-service portal from scratch",
            "problem": {
                "statement": "Customers had no way to manage accounts without calling support"
            },
            "actions": [
                "Architected new microservices platform from ground-up",
                "Pioneered first customer-facing React application",
                "Launched MVP in 6 months with iterative feature releases",
            ],
            "outcome": {"result": "Portal adopted by 50K customers, reduced support calls by 60%"},
            "tags": ["greenfield", "new-system"],
        }
        archetype, confidence, _method = infer_archetype(data, embedding_service)
        assert archetype == WorkUnitArchetype.GREENFIELD
        assert confidence >= 0.5

    # === MIGRATION (2 cases) ===

    def test_migration_cloud(self, embedding_service: EmbeddingService) -> None:
        """Cloud migration should classify as migration."""
        data = {
            "title": "Migrated legacy on-premise infrastructure to AWS",
            "problem": {"statement": "Aging data center with 200+ servers needed modernization"},
            "actions": [
                "Assessed existing workloads for cloud readiness",
                "Executed lift-and-shift migration with zero downtime cutover",
                "Decommissioned legacy data center",
            ],
            "outcome": {
                "result": "Successfully migrated 200 servers, reduced infrastructure costs 40%"
            },
            "tags": ["migration", "cloud-migration", "aws"],
        }
        archetype, confidence, _method = infer_archetype(data, embedding_service)
        assert archetype == WorkUnitArchetype.MIGRATION
        assert confidence >= 0.5

    def test_migration_database(self, embedding_service: EmbeddingService) -> None:
        """Database migration should classify as migration."""
        data = {
            "title": "Migrated from Oracle to PostgreSQL with zero data loss",
            "problem": {
                "statement": "Oracle licensing costs were $2M/year with end-of-life approaching"
            },
            "actions": [
                "Transitioned 50TB database to PostgreSQL over 6 months",
                "Executed cutover with rollback plan",
                "Decommissioned Oracle infrastructure",
            ],
            "outcome": {"result": "Completed migration saving $1.8M annually in licensing"},
            "tags": ["migration", "database"],
        }
        archetype, confidence, _method = infer_archetype(data, embedding_service)
        assert archetype == WorkUnitArchetype.MIGRATION
        assert confidence >= 0.5

    # === OPTIMIZATION (2 cases) ===

    def test_optimization_latency(self, embedding_service: EmbeddingService) -> None:
        """API latency optimization should classify as optimization."""
        data = {
            "title": "Optimized API latency by 75%",
            "problem": {"statement": "API response times averaging 800ms causing user complaints"},
            "actions": [
                "Profiled application and identified database bottlenecks",
                "Implemented query optimization and caching layer",
                "Added connection pooling and resource rightsizing",
            ],
            "outcome": {"result": "Reduced p99 latency from 800ms to 200ms, 75% improvement"},
            "tags": ["performance", "optimization"],
        }
        archetype, confidence, _method = infer_archetype(data, embedding_service)
        assert archetype == WorkUnitArchetype.OPTIMIZATION
        assert confidence >= 0.5

    def test_optimization_cost(self, embedding_service: EmbeddingService) -> None:
        """Cost optimization should classify as optimization."""
        data = {
            "title": "Reduced cloud infrastructure costs by $500K annually",
            "problem": {"statement": "AWS spending had grown 200% without corresponding value"},
            "actions": [
                "Analyzed resource utilization and identified waste",
                "Implemented cost savings through rightsizing and reserved instances",
                "Established FinOps practices and cost allocation tags",
            ],
            "outcome": {"result": "Achieved 35% reduction in cloud spend, saving $500K/year"},
            "tags": ["cost-reduction", "optimization", "efficiency"],
        }
        archetype, confidence, _method = infer_archetype(data, embedding_service)
        assert archetype == WorkUnitArchetype.OPTIMIZATION
        assert confidence >= 0.5

    # === LEADERSHIP (2 cases) ===

    def test_leadership_team_building(self, embedding_service: EmbeddingService) -> None:
        """Team building and hiring should classify as leadership."""
        data = {
            "title": "Built and led platform engineering team from 0 to 12",
            "problem": {
                "statement": "No dedicated platform team existed to support developer productivity"
            },
            "actions": [
                "Hired 12 engineers across 3 continents",
                "Mentored junior engineers with weekly 1:1s and coaching",
                "Aligned stakeholders on platform roadmap",
            ],
            "outcome": {
                "result": "Grew team from 0 to 12, reduced developer onboarding time by 60%"
            },
            "tags": ["leadership", "team-building", "hiring"],
        }
        archetype, confidence, _method = infer_archetype(data, embedding_service)
        assert archetype == WorkUnitArchetype.LEADERSHIP
        assert confidence >= 0.5

    def test_leadership_cross_functional(self, embedding_service: EmbeddingService) -> None:
        """Cross-functional leadership should classify as leadership."""
        data = {
            "title": "Led cross-functional initiative unifying 4 engineering teams",
            "problem": {
                "statement": "Siloed teams caused duplicate work and inconsistent standards"
            },
            "actions": [
                "Aligned stakeholders across product, engineering, and operations",
                "Mentored tech leads to adopt shared practices",
                "Championed unified tooling and processes",
            ],
            "outcome": {
                "result": "Unified 4 teams under common standards, reduced duplicate effort 50%"
            },
            "tags": ["leadership", "management"],
        }
        archetype, confidence, _method = infer_archetype(data, embedding_service)
        assert archetype == WorkUnitArchetype.LEADERSHIP
        assert confidence >= 0.5

    # === STRATEGIC (1 case) ===

    def test_strategic_roadmap(self, embedding_service: EmbeddingService) -> None:
        """Technology roadmap development should classify as strategic."""
        data = {
            "title": "Developed 3-year technology roadmap for digital products",
            "problem": {"statement": "No unified technology vision across product lines"},
            "actions": [
                "Conducted competitive analysis and market positioning research",
                "Aligned executive stakeholders on strategic direction",
                "Created business case with ROI analysis for board approval",
            ],
            "outcome": {
                "result": "Roadmap approved by board, secured $10M investment for execution"
            },
            "tags": ["strategy", "roadmap", "architecture"],
        }
        archetype, confidence, _method = infer_archetype(data, embedding_service)
        assert archetype == WorkUnitArchetype.STRATEGIC
        assert confidence >= 0.5

    # === TRANSFORMATION (1 case) ===

    def test_transformation_digital(self, embedding_service: EmbeddingService) -> None:
        """Digital transformation should classify as transformation."""
        data = {
            "title": "Led enterprise-wide digital transformation program",
            "problem": {"statement": "Company-wide processes were manual and paper-based"},
            "actions": [
                "Drove organizational change across 5 business units",
                "Managed multi-year program with board-level reporting",
                "Coordinated global rollout to 10,000 employees",
            ],
            "outcome": {
                "result": "Completed digital transformation, 80% reduction in manual processes"
            },
            "tags": ["transformation", "digital-transformation", "enterprise"],
        }
        archetype, confidence, _method = infer_archetype(data, embedding_service)
        assert archetype == WorkUnitArchetype.TRANSFORMATION
        assert confidence >= 0.5

    # === CULTURAL (1 case) ===

    def test_cultural_dei_initiative(self, embedding_service: EmbeddingService) -> None:
        """Culture and DEI initiative should classify as cultural."""
        data = {
            "title": "Improved engineering culture and reduced attrition by 40%",
            "problem": {
                "statement": "High turnover (35%) and low engagement scores in engineering"
            },
            "actions": [
                "Launched DEI initiatives and inclusive hiring practices",
                "Cultivated psychological safety through feedback programs",
                "Implemented retention programs focused on career development",
            ],
            "outcome": {
                "result": "Reduced attrition from 35% to 21%, engagement scores up 25 points"
            },
            "tags": ["culture", "dei", "retention", "engagement"],
        }
        archetype, confidence, _method = infer_archetype(data, embedding_service)
        assert archetype == WorkUnitArchetype.CULTURAL
        assert confidence >= 0.5

    # === MINIMAL / AMBIGUOUS (2 cases) ===

    def test_vague_content_returns_minimal(self, embedding_service: EmbeddingService) -> None:
        """Vague/ambiguous content should return minimal."""
        data = {
            "title": "Did some work on the project",
            "problem": {"statement": "There was something to do"},
            "actions": ["Worked on it"],
            "outcome": {"result": "It was completed"},
            "tags": [],
        }
        archetype, confidence, method = infer_archetype(data, embedding_service)
        assert archetype == WorkUnitArchetype.MINIMAL
        assert method == "fallback"
        assert confidence < 0.5

    def test_ambiguous_mixed_signals(self, embedding_service: EmbeddingService) -> None:
        """Ambiguous content with mixed signals should have low confidence."""
        data = {
            "title": "Improved system reliability while growing team",
            "problem": {"statement": "System had reliability issues and team was understaffed"},
            "actions": [
                "Made some improvements to the system",
                "Worked on hiring and team processes",
            ],
            "outcome": {"result": "Things got better overall"},
            "tags": [],
        }
        archetype, confidence, _method = infer_archetype(data, embedding_service)
        # This is intentionally ambiguous - we just verify low confidence
        # The system may classify it as cultural, leadership, or minimal
        # Key assertion: confidence should be below auto-apply threshold
        assert confidence < 0.5

    def test_aggregate_accuracy_threshold(self, embedding_service: EmbeddingService) -> None:
        """Aggregate accuracy must be >= 90% across all test cases.

        This test runs all archetype inference cases and validates:
        1. Overall accuracy meets minimum threshold (90%)
        2. Reports per-archetype breakdown for debugging
        """
        # Test cases: (data, expected_archetype, description)
        # For ambiguous cases, expected is None (any result OK if low confidence)
        test_cases: list[tuple[dict, WorkUnitArchetype | None, str]] = [
            # Incident cases
            (
                {
                    "title": "Resolved P1 database outage affecting production",
                    "problem": {"statement": "Critical outage detected"},
                    "actions": ["Triaged incident", "Mitigated impact"],
                    "outcome": {"result": "Restored service, reduced MTTR"},
                    "tags": ["incident-response"],
                },
                WorkUnitArchetype.INCIDENT,
                "P1 outage",
            ),
            (
                {
                    "title": "Responded to security breach",
                    "problem": {"statement": "Unauthorized access detected"},
                    "actions": ["Led war room", "Mitigated breach"],
                    "outcome": {"result": "Contained breach"},
                    "tags": ["security-incident"],
                },
                WorkUnitArchetype.INCIDENT,
                "Security breach",
            ),
            # Greenfield cases
            (
                {
                    "title": "Achieved first-attempt ATO authorization",
                    "problem": {"statement": "Required Authority to Operate"},
                    "actions": ["Developed security docs", "Implemented RMF controls"],
                    "outcome": {"result": "Obtained ATO on first submission"},
                    "tags": ["compliance", "rmf"],
                },
                WorkUnitArchetype.GREENFIELD,
                "ATO authorization",
            ),
            (
                {
                    "title": "Built new portal from scratch",
                    "problem": {"statement": "No self-service capability"},
                    "actions": ["Architected from ground-up", "Launched MVP"],
                    "outcome": {"result": "Portal adopted by 50K customers"},
                    "tags": ["greenfield"],
                },
                WorkUnitArchetype.GREENFIELD,
                "New product",
            ),
            # Migration cases
            (
                {
                    "title": "Migrated to AWS cloud",
                    "problem": {"statement": "Aging data center"},
                    "actions": ["Executed migration", "Decommissioned legacy"],
                    "outcome": {"result": "Migrated 200 servers"},
                    "tags": ["cloud-migration"],
                },
                WorkUnitArchetype.MIGRATION,
                "Cloud migration",
            ),
            (
                {
                    "title": "Migrated from Oracle to PostgreSQL",
                    "problem": {"statement": "High licensing costs"},
                    "actions": ["Transitioned database", "Executed cutover"],
                    "outcome": {"result": "Completed migration"},
                    "tags": ["migration"],
                },
                WorkUnitArchetype.MIGRATION,
                "Database migration",
            ),
            # Optimization cases
            (
                {
                    "title": "Optimized API latency by 75%",
                    "problem": {"statement": "Slow API responses"},
                    "actions": ["Profiled bottlenecks", "Implemented caching"],
                    "outcome": {"result": "75% improvement"},
                    "tags": ["optimization"],
                },
                WorkUnitArchetype.OPTIMIZATION,
                "Latency optimization",
            ),
            (
                {
                    "title": "Reduced cloud costs by $500K",
                    "problem": {"statement": "High AWS spend"},
                    "actions": ["Rightsizing", "Reserved instances"],
                    "outcome": {"result": "35% cost reduction"},
                    "tags": ["cost-reduction"],
                },
                WorkUnitArchetype.OPTIMIZATION,
                "Cost optimization",
            ),
            # Leadership cases
            (
                {
                    "title": "Built team from 0 to 12",
                    "problem": {"statement": "No platform team"},
                    "actions": ["Hired engineers", "Mentored with 1:1s"],
                    "outcome": {"result": "Grew team to 12"},
                    "tags": ["leadership", "hiring"],
                },
                WorkUnitArchetype.LEADERSHIP,
                "Team building",
            ),
            (
                {
                    "title": "Led cross-functional initiative",
                    "problem": {"statement": "Siloed teams"},
                    "actions": ["Aligned stakeholders", "Mentored leads"],
                    "outcome": {"result": "Unified 4 teams"},
                    "tags": ["leadership"],
                },
                WorkUnitArchetype.LEADERSHIP,
                "Cross-functional",
            ),
            # Strategic case
            (
                {
                    "title": "Developed 3-year technology roadmap",
                    "problem": {"statement": "No unified vision"},
                    "actions": ["Competitive analysis", "Created business case"],
                    "outcome": {"result": "Roadmap approved by board"},
                    "tags": ["strategy", "roadmap"],
                },
                WorkUnitArchetype.STRATEGIC,
                "Strategic roadmap",
            ),
            # Transformation case
            (
                {
                    "title": "Led enterprise-wide digital transformation",
                    "problem": {"statement": "Manual processes"},
                    "actions": ["Drove organizational change", "Global rollout"],
                    "outcome": {"result": "80% reduction in manual work"},
                    "tags": ["transformation"],
                },
                WorkUnitArchetype.TRANSFORMATION,
                "Digital transformation",
            ),
            # Cultural case
            (
                {
                    "title": "Improved culture, reduced attrition 40%",
                    "problem": {"statement": "High turnover"},
                    "actions": ["DEI initiatives", "Retention programs"],
                    "outcome": {"result": "Attrition down to 21%"},
                    "tags": ["culture", "dei"],
                },
                WorkUnitArchetype.CULTURAL,
                "Culture/DEI",
            ),
            # Ambiguous cases (expected=None means any archetype OK if low confidence)
            (
                {
                    "title": "Did some work",
                    "problem": {"statement": "Something to do"},
                    "actions": ["Worked on it"],
                    "outcome": {"result": "Completed"},
                    "tags": [],
                },
                None,  # Ambiguous - just check low confidence
                "Vague content",
            ),
            (
                {
                    "title": "Improved reliability while growing team",
                    "problem": {"statement": "Issues and understaffed"},
                    "actions": ["Made improvements", "Worked on hiring"],
                    "outcome": {"result": "Things improved"},
                    "tags": [],
                },
                None,  # Ambiguous - just check low confidence
                "Mixed signals",
            ),
        ]

        # Run inference on all cases
        results: list[tuple[str, WorkUnitArchetype | None, WorkUnitArchetype, float, bool]] = []
        correct = 0
        total_actionable = 0  # Cases with expected archetype (not ambiguous)

        per_archetype: dict[str, dict[str, int]] = {}

        for data, expected, description in test_cases:
            archetype, confidence, _method = infer_archetype(data, embedding_service)

            if expected is not None:
                # Definite case - check if correct
                total_actionable += 1
                is_correct = archetype == expected and confidence >= 0.5
                if is_correct:
                    correct += 1

                # Track per-archetype stats
                key = expected.value
                if key not in per_archetype:
                    per_archetype[key] = {"correct": 0, "total": 0}
                per_archetype[key]["total"] += 1
                if is_correct:
                    per_archetype[key]["correct"] += 1
            else:
                # Ambiguous case - correct if low confidence
                is_correct = confidence < 0.5

            results.append((description, expected, archetype, confidence, is_correct))

        # Calculate accuracy
        accuracy = correct / total_actionable if total_actionable > 0 else 0

        # Build failure message with breakdown
        breakdown = "\n".join(
            f"  {arch}: {stats['correct']}/{stats['total']} "
            f"({100 * stats['correct'] / stats['total']:.0f}%)"
            for arch, stats in sorted(per_archetype.items())
        )

        failures = [
            f"  {desc}: expected {exp}, got {got} ({conf:.0%})"
            for desc, exp, got, conf, ok in results
            if not ok and exp is not None
        ]
        failure_details = "\n".join(failures) if failures else "  (none)"

        # Assert minimum accuracy threshold
        assert accuracy >= 0.90, (
            f"Accuracy {accuracy:.1%} below 90% threshold\n\n"
            f"Per-archetype breakdown:\n{breakdown}\n\n"
            f"Failed cases:\n{failure_details}"
        )
