"""Tests for Work Unit JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


def resolve_ref(schema: dict[str, Any], ref: str) -> dict[str, Any]:
    """Resolve a $ref in a JSON Schema.

    Args:
        schema: Root schema containing $defs.
        ref: Reference string like "#/$defs/Problem".

    Returns:
        The resolved definition.
    """
    if ref.startswith("#/$defs/"):
        def_name = ref.replace("#/$defs/", "")
        return schema["$defs"][def_name]
    return schema


def get_schema_def(schema: dict[str, Any], prop_value: dict[str, Any]) -> dict[str, Any]:
    """Get the schema definition for a property value, resolving $ref if present.

    Handles both direct definitions and $ref or anyOf patterns.

    Args:
        schema: Root schema containing $defs.
        prop_value: Property value that may contain $ref, anyOf, or direct definition.

    Returns:
        The resolved schema definition.
    """
    if "$ref" in prop_value:
        return resolve_ref(schema, prop_value["$ref"])
    if "anyOf" in prop_value:
        # Find the non-null variant
        for variant in prop_value["anyOf"]:
            if variant.get("type") != "null":
                if "$ref" in variant:
                    return resolve_ref(schema, variant["$ref"])
                return variant
    return prop_value


class TestWorkUnitSchemaFile:
    """Test Work Unit JSON Schema file structure."""

    @pytest.fixture
    def schema_path(self) -> Path:
        """Return path to work-unit.schema.json."""
        return (
            Path(__file__).parent.parent.parent
            / "src"
            / "resume_as_code"
            / "schemas"
            / "work-unit.schema.json"
        )

    @pytest.fixture
    def schema(self, schema_path: Path) -> dict[str, Any]:
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

    def test_problem_has_required_statement(self, schema: dict[str, Any]) -> None:
        """Problem object should have statement as required field."""
        problem = get_schema_def(schema, schema["properties"]["problem"])
        assert "statement" in problem.get("required", [])

    def test_problem_has_optional_constraints_context(self, schema: dict[str, Any]) -> None:
        """Problem object should have optional constraints and context."""
        problem = get_schema_def(schema, schema["properties"]["problem"])
        problem_props = problem["properties"]
        assert "constraints" in problem_props
        assert "context" in problem_props

    def test_outcome_has_required_result(self, schema: dict[str, Any]) -> None:
        """Outcome object should have result as required field."""
        outcome = get_schema_def(schema, schema["properties"]["outcome"])
        assert "result" in outcome.get("required", [])

    def test_outcome_has_optional_quantified_impact_business_value(
        self, schema: dict[str, Any]
    ) -> None:
        """Outcome should have optional quantified_impact and business_value."""
        outcome = get_schema_def(schema, schema["properties"]["outcome"])
        outcome_props = outcome["properties"]
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

    def test_scope_has_executive_fields(self, schema: dict[str, Any]) -> None:
        """Scope should have budget_managed, team_size, revenue_influenced, geographic_reach."""
        scope = get_schema_def(schema, schema["properties"]["scope"])
        scope_props = scope["properties"]
        assert "budget_managed" in scope_props
        assert "team_size" in scope_props
        assert "revenue_influenced" in scope_props
        assert "geographic_reach" in scope_props

    def test_impact_category_enum_values(self, schema: dict[str, Any]) -> None:
        """Impact category should support all five business impact types."""
        impact_items = get_schema_def(schema, schema["properties"]["impact_category"]["items"])
        expected = ["financial", "operational", "talent", "customer", "organizational"]
        assert impact_items.get("enum") == expected

    def test_outcome_confidence_enum_values(self, schema: dict[str, Any]) -> None:
        """Outcome confidence should support exact, estimated, approximate, order_of_magnitude."""
        outcome = get_schema_def(schema, schema["properties"]["outcome"])
        outcome_props = outcome["properties"]
        confidence = get_schema_def(schema, outcome_props["confidence"])
        expected = ["exact", "estimated", "approximate", "order_of_magnitude"]
        assert confidence.get("enum") == expected

    def test_outcome_has_confidence_note(self, schema: dict[str, Any]) -> None:
        """Outcome should have optional confidence_note field."""
        outcome = get_schema_def(schema, schema["properties"]["outcome"])
        outcome_props = outcome["properties"]
        assert "confidence_note" in outcome_props

    def test_schema_has_version_field(self, schema: dict) -> None:
        """Schema should have schema_version field."""
        props = schema["properties"]
        assert "schema_version" in props

    def test_metrics_has_baseline_outcome_percentage(self, schema: dict[str, Any]) -> None:
        """Metrics should have baseline, outcome, percentage_change fields."""
        metrics = get_schema_def(schema, schema["properties"]["metrics"])
        metrics_props = metrics["properties"]
        assert "baseline" in metrics_props
        assert "outcome" in metrics_props
        assert "percentage_change" in metrics_props

    def test_framing_has_action_verb_strategic_context(self, schema: dict[str, Any]) -> None:
        """Framing should have action_verb and strategic_context fields."""
        framing = get_schema_def(schema, schema["properties"]["framing"])
        framing_props = framing["properties"]
        assert "action_verb" in framing_props
        assert "strategic_context" in framing_props

    def _get_evidence_variant(self, schema: dict[str, Any], type_name: str) -> dict[str, Any]:
        """Get evidence variant by type, resolving $ref if needed."""
        evidence_items = schema["properties"]["evidence"]["items"]
        for variant in evidence_items["oneOf"]:
            resolved = resolve_ref(schema, variant["$ref"]) if "$ref" in variant else variant
            type_prop = resolved["properties"]["type"]
            if type_prop.get("const") == type_name:
                return resolved
        raise ValueError(f"Evidence type {type_name} not found")

    def test_evidence_has_all_types(self, schema: dict[str, Any]) -> None:
        """Evidence should support all evidence types including link and narrative."""
        evidence_items = schema["properties"]["evidence"]["items"]
        # Evidence uses oneOf for discriminated union
        assert "oneOf" in evidence_items
        type_values = []
        for variant in evidence_items["oneOf"]:
            resolved = resolve_ref(schema, variant["$ref"]) if "$ref" in variant else variant
            type_const = resolved["properties"]["type"].get("const")
            type_values.append(type_const)
        expected = ["git_repo", "metrics", "document", "artifact", "link", "narrative", "other"]
        assert sorted(type_values) == sorted(expected)

    def test_evidence_git_repo_has_type_specific_fields(self, schema: dict[str, Any]) -> None:
        """Git repo evidence should have url, branch, commit_sha fields."""
        git_repo = self._get_evidence_variant(schema, "git_repo")
        props = git_repo["properties"]
        assert "url" in props
        assert "branch" in props
        assert "commit_sha" in props

    def test_evidence_metrics_has_type_specific_fields(self, schema: dict[str, Any]) -> None:
        """Metrics evidence should have url, dashboard_name, metric_names fields."""
        metrics = self._get_evidence_variant(schema, "metrics")
        props = metrics["properties"]
        assert "url" in props
        assert "dashboard_name" in props
        assert "metric_names" in props

    def test_evidence_document_has_type_specific_fields(self, schema: dict[str, Any]) -> None:
        """Document evidence should have url, title, publication_date fields."""
        document = self._get_evidence_variant(schema, "document")
        props = document["properties"]
        assert "url" in props
        assert "title" in props
        assert "publication_date" in props

    def test_evidence_artifact_has_type_specific_fields(self, schema: dict[str, Any]) -> None:
        """Artifact evidence should have url, local_path, sha256, artifact_type fields."""
        artifact = self._get_evidence_variant(schema, "artifact")
        props = artifact["properties"]
        assert "url" in props
        assert "local_path" in props
        assert "sha256" in props
        assert "artifact_type" in props

    def test_evidence_link_has_type_specific_fields(self, schema: dict[str, Any]) -> None:
        """Link evidence should have url, title, description fields."""
        link = self._get_evidence_variant(schema, "link")
        props = link["properties"]
        assert "url" in props
        assert "title" in props
        assert "description" in props

    def test_evidence_narrative_has_type_specific_fields(self, schema: dict[str, Any]) -> None:
        """Narrative evidence should have description, source, date_recorded fields."""
        narrative = self._get_evidence_variant(schema, "narrative")
        props = narrative["properties"]
        assert "description" in props
        assert "source" in props
        assert "date_recorded" in props

    def test_evidence_other_has_type_specific_fields(self, schema: dict[str, Any]) -> None:
        """Other evidence should have url, description fields."""
        other = self._get_evidence_variant(schema, "other")
        props = other["properties"]
        assert "url" in props
        assert "description" in props


class TestSchemaAndPydanticConsistency:
    """Test that JSON Schema and Pydantic models are consistent."""

    @pytest.fixture
    def schema_path(self) -> Path:
        """Return path to work-unit.schema.json."""
        return (
            Path(__file__).parent.parent.parent
            / "src"
            / "resume_as_code"
            / "schemas"
            / "work-unit.schema.json"
        )

    @pytest.fixture
    def schema(self, schema_path: Path) -> dict:
        """Load and return the JSON Schema."""
        with open(schema_path) as f:
            return json.load(f)

    def test_valid_work_unit_passes_both_validations(self, schema: dict) -> None:
        """Valid Work Unit should pass both JSON Schema and Pydantic validation."""
        import jsonschema

        from resume_as_code.models.work_unit import (
            Outcome,
            Problem,
            WorkUnit,
            WorkUnitArchetype,
        )

        # Valid work unit data
        valid_data = {
            "id": "wu-2024-03-15-cloud-migration",
            "title": "Migrated legacy system to cloud",
            "problem": {"statement": "Legacy on-prem system was costly to maintain"},
            "actions": ["Designed architecture", "Migrated databases"],
            "outcome": {"result": "Reduced costs by 40%"},
            "schema_version": "4.0.0",
            "archetype": "migration",
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
            archetype=WorkUnitArchetype.MIGRATION,
        )
        assert wu.id == valid_data["id"]

    def test_missing_required_field_fails_both(self, schema: dict) -> None:
        """Missing required field should fail both validations."""
        import jsonschema
        from pydantic import ValidationError as PydanticValidationError

        from resume_as_code.models.work_unit import Problem, WorkUnit, WorkUnitArchetype

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
                archetype=WorkUnitArchetype.MINIMAL,
            )
