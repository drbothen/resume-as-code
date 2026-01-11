"""Tests for Work Unit JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestWorkUnitSchemaFile:
    """Test Work Unit JSON Schema file structure."""

    @pytest.fixture
    def schema_path(self) -> Path:
        """Return path to work-unit.schema.json."""
        return Path(__file__).parent.parent.parent / "schemas" / "work-unit.schema.json"

    @pytest.fixture
    def schema(self, schema_path: Path) -> dict:
        """Load and return the JSON Schema."""
        with open(schema_path) as f:
            return json.load(f)

    def test_schema_file_exists(self, schema_path: Path) -> None:
        """Schema file should exist at schemas/work-unit.schema.json."""
        assert schema_path.exists(), f"Schema file not found at {schema_path}"

    def test_schema_is_valid_json(self, schema_path: Path) -> None:
        """Schema file should be valid JSON."""
        with open(schema_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_schema_has_required_fields_defined(self, schema: dict) -> None:
        """Schema should define required fields: id, title, problem, actions, outcome."""
        required = schema.get("required", [])
        assert "id" in required
        assert "title" in required
        assert "problem" in required
        assert "actions" in required
        assert "outcome" in required

    def test_problem_has_required_statement(self, schema: dict) -> None:
        """Problem object should have statement as required field."""
        problem = schema["properties"]["problem"]
        assert "statement" in problem.get("required", [])

    def test_problem_has_optional_constraints_context(self, schema: dict) -> None:
        """Problem object should have optional constraints and context."""
        problem_props = schema["properties"]["problem"]["properties"]
        assert "constraints" in problem_props
        assert "context" in problem_props

    def test_outcome_has_required_result(self, schema: dict) -> None:
        """Outcome object should have result as required field."""
        outcome = schema["properties"]["outcome"]
        assert "result" in outcome.get("required", [])

    def test_outcome_has_optional_quantified_impact_business_value(self, schema: dict) -> None:
        """Outcome should have optional quantified_impact and business_value."""
        outcome_props = schema["properties"]["outcome"]["properties"]
        assert "quantified_impact" in outcome_props
        assert "business_value" in outcome_props

    def test_schema_has_optional_time_fields(self, schema: dict) -> None:
        """Schema should have optional time_started and time_ended fields."""
        props = schema["properties"]
        assert "time_started" in props
        assert "time_ended" in props

    def test_schema_has_optional_metadata_fields(self, schema: dict) -> None:
        """Schema should have optional skills_demonstrated, confidence, tags, evidence."""
        props = schema["properties"]
        assert "skills_demonstrated" in props
        assert "confidence" in props
        assert "tags" in props
        assert "evidence" in props

    def test_schema_has_executive_level_fields(self, schema: dict) -> None:
        """Schema should have optional scope, impact_category, metrics, framing."""
        props = schema["properties"]
        assert "scope" in props
        assert "impact_category" in props
        assert "metrics" in props
        assert "framing" in props

    def test_scope_has_executive_fields(self, schema: dict) -> None:
        """Scope should have budget_managed, team_size, revenue_influenced, geographic_reach."""
        scope_props = schema["properties"]["scope"]["properties"]
        assert "budget_managed" in scope_props
        assert "team_size" in scope_props
        assert "revenue_influenced" in scope_props
        assert "geographic_reach" in scope_props

    def test_impact_category_enum_values(self, schema: dict) -> None:
        """Impact category should support all five business impact types."""
        impact_items = schema["properties"]["impact_category"]["items"]
        expected = ["financial", "operational", "talent", "customer", "organizational"]
        assert impact_items.get("enum") == expected

    def test_outcome_confidence_enum_values(self, schema: dict) -> None:
        """Outcome confidence should support exact, estimated, approximate, order_of_magnitude."""
        outcome_props = schema["properties"]["outcome"]["properties"]
        confidence = outcome_props["confidence"]
        expected = ["exact", "estimated", "approximate", "order_of_magnitude"]
        assert confidence.get("enum") == expected

    def test_outcome_has_confidence_note(self, schema: dict) -> None:
        """Outcome should have optional confidence_note field."""
        outcome_props = schema["properties"]["outcome"]["properties"]
        assert "confidence_note" in outcome_props

    def test_schema_has_version_field(self, schema: dict) -> None:
        """Schema should have schema_version field."""
        props = schema["properties"]
        assert "schema_version" in props

    def test_metrics_has_baseline_outcome_percentage(self, schema: dict) -> None:
        """Metrics should have baseline, outcome, percentage_change fields."""
        metrics_props = schema["properties"]["metrics"]["properties"]
        assert "baseline" in metrics_props
        assert "outcome" in metrics_props
        assert "percentage_change" in metrics_props

    def test_framing_has_action_verb_strategic_context(self, schema: dict) -> None:
        """Framing should have action_verb and strategic_context fields."""
        framing_props = schema["properties"]["framing"]["properties"]
        assert "action_verb" in framing_props
        assert "strategic_context" in framing_props

    def test_evidence_has_five_types(self, schema: dict) -> None:
        """Evidence should support git_repo, metrics, document, artifact, other types."""
        evidence_items = schema["properties"]["evidence"]["items"]
        # Evidence uses oneOf for discriminated union
        assert "oneOf" in evidence_items
        type_values = []
        for variant in evidence_items["oneOf"]:
            type_const = variant["properties"]["type"].get("const")
            type_values.append(type_const)
        expected = ["git_repo", "metrics", "document", "artifact", "other"]
        assert sorted(type_values) == sorted(expected)

    def test_evidence_git_repo_has_type_specific_fields(self, schema: dict) -> None:
        """Git repo evidence should have url, branch, commit_sha fields."""
        evidence_items = schema["properties"]["evidence"]["items"]["oneOf"]
        git_repo = next(v for v in evidence_items if v["properties"]["type"]["const"] == "git_repo")
        props = git_repo["properties"]
        assert "url" in props
        assert "branch" in props
        assert "commit_sha" in props

    def test_evidence_metrics_has_type_specific_fields(self, schema: dict) -> None:
        """Metrics evidence should have url, dashboard_name, metric_names fields."""
        evidence_items = schema["properties"]["evidence"]["items"]["oneOf"]
        metrics = next(v for v in evidence_items if v["properties"]["type"]["const"] == "metrics")
        props = metrics["properties"]
        assert "url" in props
        assert "dashboard_name" in props
        assert "metric_names" in props

    def test_evidence_document_has_type_specific_fields(self, schema: dict) -> None:
        """Document evidence should have url, title, publication_date fields."""
        evidence_items = schema["properties"]["evidence"]["items"]["oneOf"]
        document = next(v for v in evidence_items if v["properties"]["type"]["const"] == "document")
        props = document["properties"]
        assert "url" in props
        assert "title" in props
        assert "publication_date" in props

    def test_evidence_artifact_has_type_specific_fields(self, schema: dict) -> None:
        """Artifact evidence should have url, artifact_type fields."""
        evidence_items = schema["properties"]["evidence"]["items"]["oneOf"]
        artifact = next(v for v in evidence_items if v["properties"]["type"]["const"] == "artifact")
        props = artifact["properties"]
        assert "url" in props
        assert "artifact_type" in props

    def test_evidence_other_has_type_specific_fields(self, schema: dict) -> None:
        """Other evidence should have url, description fields."""
        evidence_items = schema["properties"]["evidence"]["items"]["oneOf"]
        other = next(v for v in evidence_items if v["properties"]["type"]["const"] == "other")
        props = other["properties"]
        assert "url" in props
        assert "description" in props


class TestSchemaAndPydanticConsistency:
    """Test that JSON Schema and Pydantic models are consistent."""

    @pytest.fixture
    def schema_path(self) -> Path:
        """Return path to work-unit.schema.json."""
        return Path(__file__).parent.parent.parent / "schemas" / "work-unit.schema.json"

    @pytest.fixture
    def schema(self, schema_path: Path) -> dict:
        """Load and return the JSON Schema."""
        with open(schema_path) as f:
            return json.load(f)

    def test_valid_work_unit_passes_both_validations(self, schema: dict) -> None:
        """Valid Work Unit should pass both JSON Schema and Pydantic validation."""
        import jsonschema

        from resume_as_code.models.work_unit import Outcome, Problem, WorkUnit

        # Valid work unit data
        valid_data = {
            "id": "wu-2024-03-15-cloud-migration",
            "title": "Migrated legacy system to cloud",
            "problem": {"statement": "Legacy on-prem system was costly to maintain"},
            "actions": ["Designed architecture", "Migrated databases"],
            "outcome": {"result": "Reduced costs by 40%"},
            "schema_version": "1.0.0",
        }

        # Should pass JSON Schema validation
        jsonschema.validate(valid_data, schema)

        # Should pass Pydantic validation
        wu = WorkUnit(
            id=valid_data["id"],
            title=valid_data["title"],
            problem=Problem(statement=valid_data["problem"]["statement"]),
            actions=valid_data["actions"],
            outcome=Outcome(result=valid_data["outcome"]["result"]),
        )
        assert wu.id == valid_data["id"]

    def test_missing_required_field_fails_both(self, schema: dict) -> None:
        """Missing required field should fail both validations."""
        import jsonschema
        from pydantic import ValidationError as PydanticValidationError

        from resume_as_code.models.work_unit import Outcome, Problem, WorkUnit

        # Missing 'outcome' field
        invalid_data = {
            "id": "wu-2024-03-15-test",
            "title": "Test work unit title",
            "problem": {"statement": "This is a problem statement here"},
            "actions": ["Action taken here"],
            # Missing outcome
        }

        # Should fail JSON Schema validation
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid_data, schema)

        # Should fail Pydantic validation
        with pytest.raises(PydanticValidationError):
            WorkUnit(
                id=invalid_data["id"],
                title=invalid_data["title"],
                problem=Problem(statement=invalid_data["problem"]["statement"]),
                actions=invalid_data["actions"],
            )
