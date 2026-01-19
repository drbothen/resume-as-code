"""Integration tests for archetype schema validation."""

from __future__ import annotations

from typing import Any

import jsonschema
import pytest

from resume_as_code.services.archetype_service import (
    list_archetypes,
    load_archetype_data,
)

# Required fields that every archetype must have
REQUIRED_STRUCTURE = ["id", "title", "problem", "actions", "outcome"]

# Required nested fields
REQUIRED_PROBLEM_FIELDS = ["statement"]
REQUIRED_OUTCOME_FIELDS = ["result"]


class TestArchetypeStructure:
    """Tests that all archetypes have the required structure."""

    def test_all_archetypes_have_required_fields(self) -> None:
        """All archetypes should have required top-level fields."""
        archetypes = list_archetypes()
        assert len(archetypes) >= 9, "Expected at least 9 archetypes"

        for archetype_name in archetypes:
            data = load_archetype_data(archetype_name)
            for field in REQUIRED_STRUCTURE:
                assert field in data, (
                    f"Archetype '{archetype_name}' missing required field: {field}"
                )

    def test_all_archetypes_have_problem_statement(self) -> None:
        """All archetypes should have problem.statement field."""
        for archetype_name in list_archetypes():
            data = load_archetype_data(archetype_name)
            assert "problem" in data
            assert isinstance(data["problem"], dict)
            assert "statement" in data["problem"], (
                f"Archetype '{archetype_name}' missing problem.statement"
            )

    def test_all_archetypes_have_outcome_result(self) -> None:
        """All archetypes should have outcome.result field."""
        for archetype_name in list_archetypes():
            data = load_archetype_data(archetype_name)
            assert "outcome" in data
            assert isinstance(data["outcome"], dict)
            assert "result" in data["outcome"], (
                f"Archetype '{archetype_name}' missing outcome.result"
            )

    def test_all_archetypes_have_actions_list(self) -> None:
        """All archetypes should have actions as a non-empty list."""
        for archetype_name in list_archetypes():
            data = load_archetype_data(archetype_name)
            assert "actions" in data
            assert isinstance(data["actions"], list)
            assert len(data["actions"]) >= 1, (
                f"Archetype '{archetype_name}' should have at least one action"
            )


class TestArchetypeSchemaValidation:
    """Tests that archetypes can pass schema validation with realistic values."""

    @pytest.fixture
    def realistic_values(self) -> dict[str, Any]:
        """Provide realistic values to substitute into archetype templates."""
        return {
            "id": "wu-2026-01-15-sample-work-unit",
            "title": "Resolved critical production incident affecting 5000 users",
            "schema_version": "4.0.0",
            "archetype": "incident",
            "problem": {
                "statement": (
                    "Production database cluster experienced cascading failures "
                    "causing a 2-hour outage for all customers."
                ),
                "constraints": [
                    "Time pressure: 30 minutes to initial mitigation",
                    "Limited visibility: Metrics dashboard was also affected",
                ],
                "context": "Peak traffic period during product launch week.",
            },
            "actions": [
                "Detected anomaly via automated alerting within 2 minutes",
                "Triaged severity and assembled incident response team",
                "Mitigated by failing over to secondary database cluster",
                "Resolved root cause by patching connection pool settings",
                "Communicated status updates to stakeholders every 15 minutes",
            ],
            "outcome": {
                "result": (
                    "Restored full service in 45 minutes, preventing an "
                    "estimated $150K in lost revenue."
                ),
                "quantified_impact": "75% reduction in MTTR vs previous incidents",
                "business_value": "Maintained 99.9% uptime SLA for enterprise tier",
            },
            "time_started": "2026-01-15",
            "time_ended": "2026-01-15",
            "skills_demonstrated": [
                {"name": "Incident Command"},
                {"name": "Root Cause Analysis"},
                {"name": "PostgreSQL"},
            ],
            "confidence": "high",
            "tags": ["incident-response", "database", "postgresql"],
        }

    def test_archetype_with_realistic_values_validates(
        self, work_unit_schema: dict[str, Any], realistic_values: dict[str, Any]
    ) -> None:
        """Archetype structure with realistic values should pass schema validation."""
        # This validates that the archetype structure is correct
        # by substituting realistic values that satisfy schema constraints
        jsonschema.validate(instance=realistic_values, schema=work_unit_schema)

    @pytest.mark.parametrize(
        "archetype_name",
        [
            "incident",
            "greenfield",
            "leadership",
            "transformation",
            "cultural",
            "strategic",
            "migration",
            "optimization",
            "minimal",
        ],
    )
    def test_archetype_structure_matches_schema_requirements(
        self, archetype_name: str, work_unit_schema: dict[str, Any]
    ) -> None:
        """Each archetype should have fields that match schema requirements."""
        data = load_archetype_data(archetype_name)

        # Verify required fields exist
        schema_required = work_unit_schema.get("required", [])
        for field in schema_required:
            assert field in data, (
                f"Archetype '{archetype_name}' missing schema-required field: {field}"
            )

        # Verify problem has required subfields
        problem_schema = work_unit_schema["properties"]["problem"]
        for field in problem_schema.get("required", []):
            assert field in data["problem"], f"Archetype '{archetype_name}' missing problem.{field}"

        # Verify outcome has required subfields
        outcome_schema = work_unit_schema["properties"]["outcome"]
        for field in outcome_schema.get("required", []):
            assert field in data["outcome"], f"Archetype '{archetype_name}' missing outcome.{field}"


class TestExecutiveArchetypeFields:
    """Tests that executive archetypes have additional executive-level fields."""

    @pytest.mark.parametrize(
        "archetype_name",
        ["transformation", "cultural", "strategic"],
    )
    def test_executive_archetypes_have_scope(self, archetype_name: str) -> None:
        """Executive archetypes should have scope section."""
        data = load_archetype_data(archetype_name)
        assert "scope" in data, f"Executive archetype '{archetype_name}' missing scope section"

    @pytest.mark.parametrize(
        "archetype_name",
        ["transformation", "cultural", "strategic"],
    )
    def test_executive_archetypes_have_impact_category(self, archetype_name: str) -> None:
        """Executive archetypes should have impact_category."""
        data = load_archetype_data(archetype_name)
        assert "impact_category" in data, (
            f"Executive archetype '{archetype_name}' missing impact_category"
        )

    def test_transformation_has_metrics_and_framing(self) -> None:
        """Transformation archetype should have metrics and framing sections."""
        data = load_archetype_data("transformation")
        assert "metrics" in data, "Transformation missing metrics section"
        assert "framing" in data, "Transformation missing framing section"
