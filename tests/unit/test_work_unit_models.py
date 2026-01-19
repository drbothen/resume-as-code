"""Tests for Work Unit Pydantic models."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from resume_as_code.models.work_unit import (
    STRONG_VERBS,
    WEAK_VERBS,
    ArtifactEvidence,
    ConfidenceLevel,
    DocumentEvidence,
    Framing,
    GitRepoEvidence,
    ImpactCategory,
    LegacyWorkUnitScope,
    Metrics,
    MetricsEvidence,
    OtherEvidence,
    Outcome,
    Problem,
    Skill,
    WorkUnit,
    WorkUnitArchetype,
    WorkUnitConfidence,
)


class TestProblemModel:
    """Test Problem model validation."""

    def test_valid_problem_creates_successfully(self) -> None:
        """Problem with valid statement should pass validation."""
        problem = Problem(statement="This is a valid problem statement that is long enough")
        assert problem.statement == "This is a valid problem statement that is long enough"

    def test_problem_with_constraints_and_context(self) -> None:
        """Problem should accept optional constraints and context."""
        problem = Problem(
            statement="This is a valid problem statement that is long enough",
            constraints=["Time constraint", "Budget constraint"],
            context="Additional context here",
        )
        assert len(problem.constraints) == 2
        assert problem.context == "Additional context here"

    def test_problem_statement_too_short_raises_error(self) -> None:
        """Problem statement under 20 chars should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Problem(statement="Too short")
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("statement",)
        assert errors[0]["type"] == "string_too_short"


class TestOutcomeModel:
    """Test Outcome model validation."""

    def test_valid_outcome_creates_successfully(self) -> None:
        """Outcome with valid result should pass validation."""
        outcome = Outcome(result="Reduced costs by 40%")
        assert outcome.result == "Reduced costs by 40%"

    def test_outcome_with_all_optional_fields(self) -> None:
        """Outcome should accept all optional fields."""
        outcome = Outcome(
            result="Reduced costs by 40%",
            quantified_impact="$2M annual savings",
            business_value="Improved profitability",
            confidence=ConfidenceLevel.EXACT,
            confidence_note="Verified with finance team",
        )
        assert outcome.quantified_impact == "$2M annual savings"
        assert outcome.confidence == ConfidenceLevel.EXACT

    def test_outcome_result_too_short_raises_error(self) -> None:
        """Outcome result under 10 chars should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Outcome(result="Short")
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("result",)
        assert errors[0]["type"] == "string_too_short"


class TestWorkUnitModel:
    """Test WorkUnit model validation."""

    def test_valid_work_unit_creates_successfully(self) -> None:
        """A complete valid Work Unit should pass validation."""
        wu = WorkUnit(
            id="wu-2024-03-15-cloud-migration",
            title="Migrated legacy system to cloud infrastructure",
            problem=Problem(statement="Legacy on-prem system was costly and hard to scale"),
            actions=["Designed cloud architecture", "Migrated databases", "Updated deployments"],
            outcome=Outcome(result="Reduced infrastructure costs by 40%"),
            archetype=WorkUnitArchetype.MIGRATION,
        )
        assert wu.id == "wu-2024-03-15-cloud-migration"
        assert wu.schema_version == "4.0.0"

    def test_missing_required_field_raises_error(self) -> None:
        """Missing required fields should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            WorkUnit(
                id="wu-2024-03-15-test",
                title="Test work unit title here",
                problem=Problem(statement="This is the problem statement here"),
                actions=["Action taken here"],
                archetype=WorkUnitArchetype.MINIMAL,
                # Missing outcome
            )
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("outcome",)
        assert errors[0]["type"] == "missing"

    def test_invalid_id_format_raises_error(self) -> None:
        """ID must match pattern wu-YYYY-MM-DD-slug."""
        with pytest.raises(ValidationError):
            WorkUnit(
                id="invalid-id",
                title="Test work unit title here",
                problem=Problem(statement="This is the problem statement here"),
                actions=["Action taken here for test"],
                outcome=Outcome(result="Result achieved here"),
                archetype=WorkUnitArchetype.MINIMAL,
            )

    def test_time_ended_before_started_raises_error(self) -> None:
        """time_ended must be after time_started."""
        with pytest.raises(ValidationError):
            WorkUnit(
                id="wu-2024-03-15-test",
                title="Test work unit title here",
                problem=Problem(statement="This is the problem statement here"),
                actions=["Action taken here for test"],
                outcome=Outcome(result="Result achieved here"),
                archetype=WorkUnitArchetype.MINIMAL,
                time_started=date(2024, 3, 15),
                time_ended=date(2024, 3, 10),  # Before start
            )

    def test_empty_actions_raises_error(self) -> None:
        """Empty actions list should raise ValidationError."""
        with pytest.raises(ValidationError):
            WorkUnit(
                id="wu-2024-03-15-test",
                title="Test work unit title here",
                problem=Problem(statement="This is the problem statement here"),
                actions=[],  # Empty
                outcome=Outcome(result="Result achieved here"),
                archetype=WorkUnitArchetype.MINIMAL,
            )

    def test_action_too_short_raises_error(self) -> None:
        """Actions under 10 chars should raise ValidationError."""
        with pytest.raises(ValidationError):
            WorkUnit(
                id="wu-2024-03-15-test",
                title="Test work unit title here",
                problem=Problem(statement="This is the problem statement here"),
                actions=["Short"],  # Too short
                outcome=Outcome(result="Result achieved here"),
                archetype=WorkUnitArchetype.MINIMAL,
            )

    def test_work_unit_with_position_id(self) -> None:
        """Work unit should accept optional position_id."""
        wu = WorkUnit(
            id="wu-2024-03-15-cloud-migration",
            title="Migrated legacy system to cloud infrastructure",
            problem=Problem(statement="Legacy on-prem system was costly and hard to scale"),
            actions=["Designed cloud architecture", "Migrated databases"],
            outcome=Outcome(result="Reduced infrastructure costs by 40%"),
            archetype=WorkUnitArchetype.MIGRATION,
            position_id="pos-techcorp-senior",
        )
        assert wu.position_id == "pos-techcorp-senior"

    def test_work_unit_without_position_id(self) -> None:
        """Work unit should work without position_id (for personal projects)."""
        wu = WorkUnit(
            id="wu-2024-03-15-open-source",
            title="Contributed to open source security project",
            problem=Problem(statement="Open source project needed better security tooling"),
            actions=["Implemented feature", "Added documentation"],
            outcome=Outcome(result="Feature merged and used by 1000+ users"),
            archetype=WorkUnitArchetype.GREENFIELD,
        )
        assert wu.position_id is None


class TestEvidenceDiscriminatedUnion:
    """Test evidence type discrimination."""

    def test_git_repo_evidence_type(self) -> None:
        """Git repo evidence should have correct type."""
        evidence = GitRepoEvidence(url="https://github.com/org/repo")
        assert evidence.type == "git_repo"

    def test_metrics_evidence_type(self) -> None:
        """Metrics evidence should have correct type."""
        evidence = MetricsEvidence(url="https://grafana.example.com/dashboard")
        assert evidence.type == "metrics"

    def test_document_evidence_type(self) -> None:
        """Document evidence should have correct type."""
        evidence = DocumentEvidence(url="https://docs.example.com/whitepaper")
        assert evidence.type == "document"

    def test_artifact_evidence_type(self) -> None:
        """Artifact evidence should have correct type."""
        evidence = ArtifactEvidence(url="https://releases.example.com/v1.0")
        assert evidence.type == "artifact"

    def test_other_evidence_type(self) -> None:
        """Other evidence should have correct type."""
        evidence = OtherEvidence(url="https://example.com/other")
        assert evidence.type == "other"

    def test_git_repo_evidence_with_all_fields(self) -> None:
        """Git repo evidence should accept all optional fields."""
        evidence = GitRepoEvidence(
            url="https://github.com/org/repo",
            branch="main",
            commit_sha="abc123",
            description="Main repository",
        )
        assert evidence.branch == "main"
        assert evidence.commit_sha == "abc123"

    def test_metrics_evidence_with_all_fields(self) -> None:
        """Metrics evidence should accept all optional fields."""
        evidence = MetricsEvidence(
            url="https://grafana.example.com/dashboard",
            dashboard_name="Performance Dashboard",
            metric_names=["response_time", "error_rate"],
        )
        assert evidence.dashboard_name == "Performance Dashboard"
        assert len(evidence.metric_names) == 2


class TestEnumValues:
    """Test enum values are correct."""

    def test_confidence_level_values(self) -> None:
        """ConfidenceLevel should have exact, estimated, approximate, order_of_magnitude."""
        assert ConfidenceLevel.EXACT.value == "exact"
        assert ConfidenceLevel.ESTIMATED.value == "estimated"
        assert ConfidenceLevel.APPROXIMATE.value == "approximate"
        assert ConfidenceLevel.ORDER_OF_MAGNITUDE.value == "order_of_magnitude"

    def test_work_unit_confidence_values(self) -> None:
        """WorkUnitConfidence should have high, medium, low."""
        assert WorkUnitConfidence.HIGH.value == "high"
        assert WorkUnitConfidence.MEDIUM.value == "medium"
        assert WorkUnitConfidence.LOW.value == "low"

    def test_impact_category_values(self) -> None:
        """ImpactCategory should have all business impact types."""
        assert ImpactCategory.FINANCIAL.value == "financial"
        assert ImpactCategory.OPERATIONAL.value == "operational"
        assert ImpactCategory.TALENT.value == "talent"
        assert ImpactCategory.CUSTOMER.value == "customer"
        assert ImpactCategory.ORGANIZATIONAL.value == "organizational"


class TestExecutiveLevelFields:
    """Test executive-level model fields."""

    def test_legacy_work_unit_scope_model(self) -> None:
        """LegacyWorkUnitScope should accept legacy executive-level fields."""
        scope = LegacyWorkUnitScope(
            budget_managed="$5M",
            team_size=25,
            revenue_influenced="$50M",
            geographic_reach="North America",
        )
        assert scope.budget_managed == "$5M"
        assert scope.team_size == 25

    def test_metrics_model(self) -> None:
        """Metrics should accept baseline, outcome, percentage_change."""
        metrics = Metrics(
            baseline="50ms response time",
            outcome="20ms response time",
            percentage_change=-60.0,
        )
        assert metrics.baseline == "50ms response time"
        assert metrics.percentage_change == -60.0

    def test_framing_model(self) -> None:
        """Framing should accept action_verb and strategic_context."""
        framing = Framing(
            action_verb="Orchestrated",
            strategic_context="Digital transformation initiative",
        )
        assert framing.action_verb == "Orchestrated"

    def test_skill_model(self) -> None:
        """Skill should accept name and optional fields."""
        skill = Skill(
            name="Python",
            onet_element_id="2.A.1",
            proficiency_level=6,
        )
        assert skill.name == "Python"
        assert skill.onet_element_id == "2.A.1"
        assert skill.proficiency_level == 6

    def test_skill_invalid_onet_id_raises_error(self) -> None:
        """Skill with invalid O*NET element ID pattern should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Skill(name="Python", onet_element_id="invalid-format")
        errors = exc_info.value.errors()
        assert errors[0]["loc"] == ("onet_element_id",)
        assert errors[0]["type"] == "string_pattern_mismatch"

    def test_skill_proficiency_bounds(self) -> None:
        """Skill proficiency should be between 1 and 7."""
        with pytest.raises(ValidationError):
            Skill(name="Python", proficiency_level=0)
        with pytest.raises(ValidationError):
            Skill(name="Python", proficiency_level=8)


class TestWorkUnitWithAllFields:
    """Test WorkUnit with all optional fields populated."""

    def test_full_work_unit(self) -> None:
        """WorkUnit with all fields should pass validation."""
        wu = WorkUnit(
            id="wu-2024-03-15-cloud-migration",
            title="Migrated legacy system to cloud infrastructure",
            problem=Problem(
                statement="Legacy on-prem system was costly and hard to scale",
                constraints=["6-month deadline", "Zero downtime"],
                context="Part of digital transformation",
            ),
            actions=[
                "Designed cloud architecture",
                "Migrated databases with zero downtime",
                "Updated CI/CD pipelines",
            ],
            outcome=Outcome(
                result="Reduced infrastructure costs by 40%",
                quantified_impact="$2M annual savings",
                business_value="Improved scalability",
                confidence=ConfidenceLevel.EXACT,
            ),
            archetype=WorkUnitArchetype.MIGRATION,
            time_started=date(2024, 1, 1),
            time_ended=date(2024, 3, 15),
            skills_demonstrated=[
                Skill(name="AWS", proficiency_level=7),
                Skill(name="Terraform"),
            ],
            confidence=WorkUnitConfidence.HIGH,
            tags=["cloud", "infrastructure", "cost-reduction"],
            evidence=[
                GitRepoEvidence(url="https://github.com/org/infra"),
                MetricsEvidence(url="https://grafana.example.com/costs"),
            ],
            scope=LegacyWorkUnitScope(budget_managed="$5M", team_size=12),
            impact_category=[ImpactCategory.FINANCIAL, ImpactCategory.OPERATIONAL],
            metrics=Metrics(baseline="$5M/year", outcome="$3M/year", percentage_change=-40.0),
            framing=Framing(action_verb="Orchestrated"),
        )
        assert wu.id == "wu-2024-03-15-cloud-migration"
        assert len(wu.skills_demonstrated) == 2
        assert len(wu.evidence) == 2
        assert len(wu.impact_category) == 2


class TestWeakVerbDetection:
    """Test weak action verb detection per Content Strategy standards."""

    def test_weak_verbs_constant_defined(self) -> None:
        """WEAK_VERBS constant should be defined with known weak verbs."""
        assert "managed" in WEAK_VERBS
        assert "handled" in WEAK_VERBS
        assert "helped" in WEAK_VERBS
        assert "worked on" in WEAK_VERBS
        assert "was responsible for" in WEAK_VERBS

    def test_strong_verbs_constant_defined(self) -> None:
        """STRONG_VERBS constant should be defined with recommended alternatives."""
        assert "orchestrated" in STRONG_VERBS
        assert "spearheaded" in STRONG_VERBS
        assert "championed" in STRONG_VERBS
        assert "transformed" in STRONG_VERBS

    def test_work_unit_detects_weak_verbs_in_actions(self) -> None:
        """WorkUnit should detect weak verbs in actions."""
        wu = WorkUnit(
            id="wu-2024-03-15-test-weak",
            title="Test work unit with weak verbs",
            problem=Problem(statement="This is the problem statement here"),
            actions=["Managed the team during project", "Handled customer complaints"],
            outcome=Outcome(result="Result achieved here"),
            archetype=WorkUnitArchetype.LEADERSHIP,
        )
        warnings = wu.get_weak_verb_warnings()
        assert len(warnings) > 0
        assert any("managed" in w.lower() for w in warnings)

    def test_work_unit_no_warnings_with_strong_verbs(self) -> None:
        """WorkUnit should have no warnings with strong verbs."""
        wu = WorkUnit(
            id="wu-2024-03-15-test-strong",
            title="Test work unit with strong verbs",
            problem=Problem(statement="This is the problem statement here"),
            actions=["Orchestrated the migration project", "Spearheaded the initiative"],
            outcome=Outcome(result="Result achieved here"),
            archetype=WorkUnitArchetype.MIGRATION,
        )
        warnings = wu.get_weak_verb_warnings()
        assert len(warnings) == 0

    def test_work_unit_detects_weak_verbs_in_framing(self) -> None:
        """WorkUnit should detect weak verbs in framing.action_verb."""
        wu = WorkUnit(
            id="wu-2024-03-15-test-framing",
            title="Test work unit with weak framing",
            problem=Problem(statement="This is the problem statement here"),
            actions=["Designed the architecture solution"],
            outcome=Outcome(result="Result achieved here"),
            archetype=WorkUnitArchetype.GREENFIELD,
            framing=Framing(action_verb="Managed"),
        )
        warnings = wu.get_weak_verb_warnings()
        assert len(warnings) > 0
        assert any("managed" in w.lower() for w in warnings)

    def test_work_unit_detects_weak_verbs_at_end_of_sentence(self) -> None:
        """WorkUnit should detect weak verbs at end of sentence."""
        wu = WorkUnit(
            id="wu-2024-03-15-test-end",
            title="Test work unit with verb at end",
            problem=Problem(statement="This is the problem statement here"),
            actions=["The team managed"],
            outcome=Outcome(result="Result achieved here"),
            archetype=WorkUnitArchetype.LEADERSHIP,
        )
        warnings = wu.get_weak_verb_warnings()
        assert len(warnings) > 0
        assert any("managed" in w.lower() for w in warnings)


class TestTagNormalization:
    """Test tag normalization per Story 2.5 requirements."""

    def test_tags_normalized_to_lowercase(self) -> None:
        """Tags should be normalized to lowercase."""
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Test work unit title",
            problem=Problem(statement="This is the problem statement"),
            actions=["Action taken here"],
            outcome=Outcome(result="Result achieved"),
            archetype=WorkUnitArchetype.MINIMAL,
            tags=["Python", "AWS", "Incident-Response"],
        )
        assert wu.tags == ["python", "aws", "incident-response"]

    def test_tags_whitespace_stripped(self) -> None:
        """Tags should have whitespace stripped."""
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Test work unit title",
            problem=Problem(statement="This is the problem statement"),
            actions=["Action taken here"],
            outcome=Outcome(result="Result achieved"),
            archetype=WorkUnitArchetype.MINIMAL,
            tags=["  python  ", "aws ", " kubernetes"],
        )
        assert wu.tags == ["python", "aws", "kubernetes"]

    def test_empty_tags_default(self) -> None:
        """Empty tags list should be the default."""
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Test work unit title",
            problem=Problem(statement="This is the problem statement"),
            actions=["Action taken here"],
            outcome=Outcome(result="Result achieved"),
            archetype=WorkUnitArchetype.MINIMAL,
        )
        assert wu.tags == []

    def test_empty_string_tags_filtered(self) -> None:
        """Empty string tags should be filtered out."""
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Test work unit title",
            problem=Problem(statement="This is the problem statement"),
            actions=["Action taken here"],
            outcome=Outcome(result="Result achieved"),
            archetype=WorkUnitArchetype.MINIMAL,
            tags=["python", "", "aws"],
        )
        assert wu.tags == ["python", "aws"]

    def test_whitespace_only_tags_filtered(self) -> None:
        """Whitespace-only tags should be filtered out."""
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Test work unit title",
            problem=Problem(statement="This is the problem statement"),
            actions=["Action taken here"],
            outcome=Outcome(result="Result achieved"),
            archetype=WorkUnitArchetype.MINIMAL,
            tags=["python", "   ", "aws"],
        )
        assert wu.tags == ["python", "aws"]

    def test_duplicate_tags_deduplicated(self) -> None:
        """Duplicate tags (case-insensitive) should be deduplicated."""
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Test work unit title",
            problem=Problem(statement="This is the problem statement"),
            actions=["Action taken here"],
            outcome=Outcome(result="Result achieved"),
            archetype=WorkUnitArchetype.MINIMAL,
            tags=["python", "Python", "PYTHON", "aws", "AWS"],
        )
        assert wu.tags == ["python", "aws"]

    def test_duplicate_tags_preserve_first_occurrence_order(self) -> None:
        """Deduplication should preserve order of first occurrence."""
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Test work unit title",
            problem=Problem(statement="This is the problem statement"),
            actions=["Action taken here"],
            outcome=Outcome(result="Result achieved"),
            archetype=WorkUnitArchetype.MINIMAL,
            tags=["AWS", "python", "aws", "kubernetes", "Python"],
        )
        assert wu.tags == ["aws", "python", "kubernetes"]


class TestMetadataDefaults:
    """Test metadata fields have sensible defaults per Story 2.5."""

    def test_confidence_default_none(self) -> None:
        """Confidence should default to None."""
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Test work unit title",
            problem=Problem(statement="This is the problem statement"),
            actions=["Action taken here"],
            outcome=Outcome(result="Result achieved"),
            archetype=WorkUnitArchetype.MINIMAL,
        )
        assert wu.confidence is None

    def test_evidence_default_empty_list(self) -> None:
        """Evidence should default to empty list."""
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Test work unit title",
            problem=Problem(statement="This is the problem statement"),
            actions=["Action taken here"],
            outcome=Outcome(result="Result achieved"),
            archetype=WorkUnitArchetype.MINIMAL,
        )
        assert wu.evidence == []

    def test_all_metadata_fields_optional(self) -> None:
        """All metadata fields (confidence, tags, evidence) should be optional."""
        # Should not raise ValidationError
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Test work unit title",
            problem=Problem(statement="This is the problem statement"),
            actions=["Action taken here"],
            outcome=Outcome(result="Result achieved"),
            archetype=WorkUnitArchetype.MINIMAL,
        )
        assert wu.confidence is None
        assert wu.tags == []
        assert wu.evidence == []


class TestMetadataValidation:
    """Test metadata field validation per Story 2.5."""

    def test_invalid_confidence_value_raises_error(self) -> None:
        """Invalid confidence value should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            WorkUnit(
                id="wu-2024-01-01-test",
                title="Test work unit title",
                problem=Problem(statement="This is the problem statement"),
                actions=["Action taken here"],
                outcome=Outcome(result="Result achieved"),
                archetype=WorkUnitArchetype.MINIMAL,
                confidence="super-high",  # Invalid value
            )
        errors = exc_info.value.errors()
        assert len(errors) == 1
        # Check that error message helps user understand valid options
        assert "confidence" in str(errors[0]["loc"]).lower() or errors[0]["loc"] == ("confidence",)

    def test_invalid_evidence_url_raises_error(self) -> None:
        """Invalid URL in evidence should raise ValidationError."""
        with pytest.raises(ValidationError):
            GitRepoEvidence(url="not-a-valid-url")

    def test_valid_confidence_values_accepted(self) -> None:
        """All valid confidence values should be accepted."""
        for level in [WorkUnitConfidence.HIGH, WorkUnitConfidence.MEDIUM, WorkUnitConfidence.LOW]:
            wu = WorkUnit(
                id="wu-2024-01-01-test",
                title="Test work unit title",
                problem=Problem(statement="This is the problem statement"),
                actions=["Action taken here"],
                outcome=Outcome(result="Result achieved"),
                archetype=WorkUnitArchetype.MINIMAL,
                confidence=level,
            )
            assert wu.confidence == level


class TestWorkUnitScopeDeprecation:
    """Test WorkUnit.scope deprecation (Story 7.2 AC #3)."""

    def test_work_unit_scope_deprecated_warning(self) -> None:
        """Setting WorkUnit.scope emits deprecation warning."""
        with pytest.warns(DeprecationWarning, match="deprecated"):
            wu = WorkUnit(
                id="wu-2024-01-01-test",
                title="Test work unit with deprecated scope",
                problem=Problem(statement="This is the problem statement"),
                actions=["Action taken here"],
                outcome=Outcome(result="Result achieved"),
                archetype=WorkUnitArchetype.LEADERSHIP,
                scope=LegacyWorkUnitScope(team_size=10),  # Deprecated usage
            )
            assert wu.scope is not None

    def test_work_unit_scope_no_warning_when_not_set(self) -> None:
        """No warning when WorkUnit.scope is not set."""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            WorkUnit(
                id="wu-2024-01-01-test",
                title="Test work unit without scope",
                problem=Problem(statement="This is the problem statement"),
                actions=["Action taken here"],
                outcome=Outcome(result="Result achieved"),
                archetype=WorkUnitArchetype.MINIMAL,
            )
            # Should NOT emit deprecation warning
            deprecation_warnings = [
                warning for warning in w if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) == 0


class TestExtraFieldsForbidden:
    def test_work_unit_rejects_extra_fields(self) -> None:
        """WorkUnit should reject extra fields not in schema."""
        with pytest.raises(ValidationError) as exc_info:
            WorkUnit(
                id="wu-2024-03-15-test",
                title="Test work unit title here",
                problem=Problem(statement="This is the problem statement here"),
                actions=["Action taken here for test"],
                outcome=Outcome(result="Result achieved here"),
                archetype=WorkUnitArchetype.MINIMAL,
                extra_field="should not be allowed",
            )
        errors = exc_info.value.errors()
        assert errors[0]["type"] == "extra_forbidden"

    def test_problem_rejects_extra_fields(self) -> None:
        """Problem should reject extra fields not in schema."""
        with pytest.raises(ValidationError) as exc_info:
            Problem(
                statement="This is a valid problem statement here",
                unknown_field="not allowed",
            )
        errors = exc_info.value.errors()
        assert errors[0]["type"] == "extra_forbidden"

    def test_evidence_rejects_extra_fields(self) -> None:
        """Evidence models should reject extra fields not in schema."""
        with pytest.raises(ValidationError) as exc_info:
            GitRepoEvidence(
                url="https://github.com/org/repo",
                invalid_field="not allowed",
            )
        errors = exc_info.value.errors()
        assert errors[0]["type"] == "extra_forbidden"
