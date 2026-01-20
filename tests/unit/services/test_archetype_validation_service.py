"""Tests for archetype validation service."""

from __future__ import annotations

from resume_as_code.models.work_unit import WorkUnitArchetype
from resume_as_code.services.archetype_validation_service import (
    ARCHETYPE_PAR_PATTERNS,
    ArchetypeValidationResult,
    extract_par_text,
    score_par_section,
    validate_archetype_alignment,
)


class TestExtractParText:
    """Tests for PAR text extraction."""

    def test_extracts_from_dict(self) -> None:
        """Should extract problem, actions, outcome from dict."""
        data = {
            "problem": {
                "statement": "Database crashed",
                "context": "During peak hours",
            },
            "actions": ["Diagnosed issue", "Restored service"],
            "outcome": {
                "result": "Resolved in 30 min",
                "quantified_impact": "Prevented $10K loss",
            },
        }
        problem, actions, outcome = extract_par_text(data)
        assert "database crashed" in problem
        assert "peak hours" in problem
        assert "diagnosed issue" in actions
        assert "resolved in 30 min" in outcome
        assert "prevented" in outcome

    def test_extracts_with_missing_fields(self) -> None:
        """Should handle missing optional fields gracefully."""
        data = {
            "problem": {"statement": "Something went wrong"},
            "actions": ["Fixed it"],
            "outcome": {"result": "It works now"},
        }
        problem, actions, outcome = extract_par_text(data)
        assert "something went wrong" in problem
        assert "fixed it" in actions
        assert "it works now" in outcome

    def test_extracts_business_value(self) -> None:
        """Should include business_value in outcome text."""
        data = {
            "problem": {"statement": "Test problem statement here"},
            "actions": ["Took action"],
            "outcome": {
                "result": "Achieved result",
                "business_value": "Increased revenue",
            },
        }
        _, _, outcome = extract_par_text(data)
        assert "increased revenue" in outcome

    def test_handles_missing_problem_section(self) -> None:
        """Should handle missing problem section gracefully."""
        data: dict[str, object] = {
            "actions": ["Did something"],
            "outcome": {"result": "Got result"},
        }
        problem, actions, outcome = extract_par_text(data)
        assert problem == ""
        assert "did something" in actions
        assert "got result" in outcome

    def test_handles_missing_outcome_section(self) -> None:
        """Should handle missing outcome section gracefully."""
        data: dict[str, object] = {
            "problem": {"statement": "Had a problem"},
            "actions": ["Did something"],
        }
        problem, actions, outcome = extract_par_text(data)
        assert "had a problem" in problem
        assert "did something" in actions
        assert outcome == ""

    def test_handles_empty_actions_list(self) -> None:
        """Should handle empty actions list gracefully."""
        data: dict[str, object] = {
            "problem": {"statement": "Had a problem"},
            "actions": [],
            "outcome": {"result": "Got result"},
        }
        problem, actions, outcome = extract_par_text(data)
        assert "had a problem" in problem
        assert actions == ""
        assert "got result" in outcome

    def test_handles_none_values_in_dict(self) -> None:
        """Should handle None values in dict gracefully."""
        data: dict[str, object] = {
            "problem": {"statement": None, "context": None},
            "actions": None,
            "outcome": {"result": None},
        }
        problem, actions, outcome = extract_par_text(data)
        # Should return "none" strings (from str(None)) or empty
        assert isinstance(problem, str)
        assert isinstance(actions, str)
        assert isinstance(outcome, str)


class TestScoreParSection:
    """Tests for PAR section scoring."""

    def test_high_score_with_many_matches(self) -> None:
        """Should score high when text contains many pattern matches."""
        text = "detected outage, triaged impact, mitigated damage, resolved incident"
        patterns = ["detect", "triage", "mitigat", "resolv", "incident"]
        score = score_par_section(text, patterns)
        assert score >= 0.8

    def test_low_score_with_no_matches(self) -> None:
        """Should score low when text has no pattern matches."""
        text = "did some work on the project"
        patterns = ["detect", "triage", "mitigat", "resolv"]
        score = score_par_section(text, patterns)
        assert score < 0.3

    def test_zero_score_for_empty_patterns(self) -> None:
        """Should return 0 for empty patterns."""
        score = score_par_section("some text", [])
        assert score == 0.0

    def test_zero_score_for_empty_text(self) -> None:
        """Should return 0 for empty text."""
        score = score_par_section("", ["pattern1", "pattern2"])
        assert score == 0.0

    def test_score_capped_at_one(self) -> None:
        """Should cap score at 1.0 even with many matches."""
        text = "detect detect detect detect detect detect detect detect"
        patterns = ["detect"]
        score = score_par_section(text, patterns)
        assert score <= 1.0


class TestValidateArchetypeAlignment:
    """Tests for archetype alignment validation."""

    def test_incident_aligned_work_unit(self) -> None:
        """Well-formed incident work unit should be aligned."""
        data = {
            "archetype": "incident",
            "problem": {
                "statement": "Production database outage affecting 10K users",
                "context": "Critical P1 incident during peak hours",
            },
            "actions": [
                "Detected via monitoring alerts",
                "Triaged impact across services",
                "Mitigated by failing over to replica",
                "Resolved root cause in connection pool",
                "Communicated status to stakeholders",
            ],
            "outcome": {
                "result": "Restored service in 45 minutes",
                "quantified_impact": "MTTR reduced, prevented $50K impact",
            },
        }
        result = validate_archetype_alignment(data)
        assert result.is_aligned
        assert result.problem_score >= 0.3
        assert result.action_score >= 0.3
        assert result.outcome_score >= 0.3
        assert len(result.warnings) == 0

    def test_greenfield_aligned_work_unit(self) -> None:
        """Well-formed greenfield work unit should be aligned."""
        data = {
            "archetype": "greenfield",
            "problem": {
                "statement": "Team needed real-time analytics capability",
                "context": "Gap in observability for customer behavior",
            },
            "actions": [
                "Designed event-driven architecture",
                "Built streaming data pipeline",
                "Deployed to production with CI/CD",
                "Launched beta to internal teams",
            ],
            "outcome": {
                "result": "Delivered analytics platform serving 1M events/day",
                "quantified_impact": "Enabled product team to make data-driven decisions",
            },
        }
        result = validate_archetype_alignment(data)
        assert result.is_aligned
        assert len(result.warnings) == 0

    def test_misaligned_work_unit_generates_warnings(self) -> None:
        """Work unit with wrong archetype should generate warnings."""
        data = {
            "archetype": "incident",  # Wrong archetype for this content
            "problem": {
                "statement": "Team needed new feature for something",
            },
            "actions": ["Built new system", "Deployed to production"],
            "outcome": {
                "result": "Launched new product successfully",
            },
        }
        result = validate_archetype_alignment(data)
        assert not result.is_aligned
        assert len(result.warnings) > 0
        assert any("incident" in w.lower() for w in result.warnings)

    def test_minimal_archetype_always_aligned(self) -> None:
        """Minimal archetype should always be aligned (no validation)."""
        data = {
            "archetype": "minimal",
            "problem": {"statement": "stuff happens sometimes here"},
            "actions": ["did things here today"],
            "outcome": {"result": "it worked out fine"},
        }
        result = validate_archetype_alignment(data)
        assert result.is_aligned
        assert result.problem_score == 1.0
        assert len(result.warnings) == 0
        assert any("specific archetype" in s for s in result.suggestions)

    def test_optimization_checks_for_metrics(self) -> None:
        """Optimization archetype should check for quantified improvements."""
        data = {
            "archetype": "optimization",
            "problem": {
                "statement": "API was slow with high latency",
                "context": "Baseline response time 500ms",
            },
            "actions": [
                "Profiled application to identify bottlenecks",
                "Optimized database queries",
                "Implemented caching layer",
            ],
            "outcome": {
                "result": "Reduced latency by 60%",
                "quantified_impact": "Response time improved from 500ms to 200ms",
            },
        }
        result = validate_archetype_alignment(data)
        assert result.is_aligned
        assert result.outcome_score >= 0.3  # Should detect % improvement

    def test_all_archetypes_have_patterns(self) -> None:
        """Every non-minimal archetype should have validation patterns."""
        for archetype in WorkUnitArchetype:
            if archetype == WorkUnitArchetype.MINIMAL:
                continue
            assert archetype in ARCHETYPE_PAR_PATTERNS, f"Missing patterns for {archetype}"
            patterns = ARCHETYPE_PAR_PATTERNS[archetype]
            assert "problem_patterns" in patterns
            assert "action_patterns" in patterns
            assert "outcome_patterns" in patterns

    def test_migration_archetype_alignment(self) -> None:
        """Migration archetype should validate legacy/transition patterns."""
        data = {
            "archetype": "migration",
            "problem": {
                "statement": "Legacy system was outdated and unsupported",
                "context": "End of life for vendor support",
            },
            "actions": [
                "Planned migration strategy",
                "Transitioned data in parallel",
                "Cutover to new system",
            ],
            "outcome": {
                "result": "Successfully completed migration with zero downtime",
                "quantified_impact": "Decommissioned legacy system, reduced costs",
            },
        }
        result = validate_archetype_alignment(data)
        assert result.is_aligned

    def test_leadership_archetype_alignment(self) -> None:
        """Leadership archetype should validate team/mentoring patterns."""
        data = {
            "archetype": "leadership",
            "problem": {
                "statement": "Team had significant skill gap in cloud",
                "context": "Talent retention was a concern",
            },
            "actions": [
                "Mentored junior engineers",
                "Built hiring pipeline",
                "Developed training program",
            ],
            "outcome": {
                "result": "Grew team from 3 to 12 engineers",
                "quantified_impact": "Improved retention, all mentees promoted",
            },
        }
        result = validate_archetype_alignment(data)
        assert result.is_aligned

    def test_strategic_archetype_alignment(self) -> None:
        """Strategic archetype should validate market/strategy patterns."""
        data = {
            "archetype": "strategic",
            "problem": {
                "statement": "Company needed strategic direction in market",
                "context": "Competitive position was weakening",
            },
            "actions": [
                "Researched market trends",
                "Developed strategy framework",
                "Established key partnerships",
            ],
            "outcome": {
                "result": "Positioned company as market leader",
                "quantified_impact": "Increased market share and revenue growth",
            },
        }
        result = validate_archetype_alignment(data)
        assert result.is_aligned

    def test_transformation_archetype_alignment(self) -> None:
        """Transformation archetype should validate enterprise-wide patterns."""
        data = {
            "archetype": "transformation",
            "problem": {
                "statement": "Enterprise digital transformation was needed",
                "context": "Organization-wide modernization required",
            },
            "actions": [
                "Led transformation initiative",
                "Executed change management",
                "Global rollout to all regions",
            ],
            "outcome": {
                "result": "Transformed enterprise operations",
                "quantified_impact": "Company-wide adoption, millions in savings",
            },
        }
        result = validate_archetype_alignment(data)
        assert result.is_aligned

    def test_cultural_archetype_alignment(self) -> None:
        """Cultural archetype should validate culture/engagement patterns."""
        data = {
            "archetype": "cultural",
            "problem": {
                "statement": "Culture and engagement scores were declining",
                "context": "Retention was at risk, attrition increasing",
            },
            "actions": [
                "Cultivated inclusive environment",
                "Launched program for diversity",
                "Measured engagement through surveys",
            ],
            "outcome": {
                "result": "Improved engagement scores by 25%",
                "quantified_impact": "Retention improved, NPS increased",
            },
        }
        result = validate_archetype_alignment(data)
        assert result.is_aligned

    def test_archetype_override(self) -> None:
        """Should allow archetype parameter to override work unit archetype."""
        data = {
            "archetype": "minimal",
            "problem": {
                "statement": "Production outage affecting users",
            },
            "actions": ["Detected and resolved the incident"],
            "outcome": {
                "result": "Restored service, MTTR improved",
            },
        }
        # Validate with explicit incident archetype override
        result = validate_archetype_alignment(data, archetype=WorkUnitArchetype.INCIDENT)
        assert result.archetype == WorkUnitArchetype.INCIDENT

    def test_result_contains_suggestions_for_low_scores(self) -> None:
        """Should include guidance suggestions when sections score low."""
        data = {
            "archetype": "incident",
            "problem": {"statement": "Something happened but not sure what"},
            "actions": ["Did something about it"],
            "outcome": {"result": "Fixed somehow okay"},
        }
        result = validate_archetype_alignment(data)
        # Should have suggestions because content doesn't match incident patterns
        assert len(result.suggestions) > 0


class TestArchetypeValidationResult:
    """Tests for ArchetypeValidationResult dataclass."""

    def test_result_has_all_fields(self) -> None:
        """Should have all required fields."""
        result = ArchetypeValidationResult(
            archetype=WorkUnitArchetype.INCIDENT,
            is_aligned=True,
            problem_score=0.8,
            action_score=0.7,
            outcome_score=0.9,
            warnings=[],
            suggestions=[],
        )
        assert result.archetype == WorkUnitArchetype.INCIDENT
        assert result.is_aligned is True
        assert result.problem_score == 0.8
        assert result.action_score == 0.7
        assert result.outcome_score == 0.9
        assert result.warnings == []
        assert result.suggestions == []
