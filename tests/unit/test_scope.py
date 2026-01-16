"""Unit tests for unified Scope model.

Tests the unified Scope model that replaces PositionScope and WorkUnit.Scope:
- Field validation (all optional, non-negative integers)
- Extra field rejection (ConfigDict extra="forbid")
- Model export and imports
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError


class TestScopeModel:
    """Tests for unified Scope Pydantic model."""

    def test_scope_all_fields_optional(self) -> None:
        """Scope model allows all fields to be None."""
        from resume_as_code.models.scope import Scope

        scope = Scope()
        assert scope.revenue is None
        assert scope.team_size is None
        assert scope.direct_reports is None
        assert scope.budget is None
        assert scope.pl_responsibility is None
        assert scope.geography is None
        assert scope.customers is None

    def test_scope_all_fields_populated(self) -> None:
        """Scope model accepts all fields."""
        from resume_as_code.models.scope import Scope

        scope = Scope(
            revenue="$500M",
            team_size=200,
            direct_reports=15,
            budget="$50M",
            pl_responsibility="$100M",
            geography="Global (15 countries)",
            customers="Fortune 500 clients",
        )
        assert scope.revenue == "$500M"
        assert scope.team_size == 200
        assert scope.direct_reports == 15
        assert scope.budget == "$50M"
        assert scope.pl_responsibility == "$100M"
        assert scope.geography == "Global (15 countries)"
        assert scope.customers == "Fortune 500 clients"

    def test_scope_team_size_validates_non_negative(self) -> None:
        """team_size must be >= 0."""
        from resume_as_code.models.scope import Scope

        with pytest.raises(ValidationError) as exc_info:
            Scope(team_size=-1)
        assert "team_size" in str(exc_info.value)

    def test_scope_direct_reports_validates_non_negative(self) -> None:
        """direct_reports must be >= 0."""
        from resume_as_code.models.scope import Scope

        with pytest.raises(ValidationError) as exc_info:
            Scope(direct_reports=-5)
        assert "direct_reports" in str(exc_info.value)

    def test_scope_forbids_extra_fields(self) -> None:
        """Extra fields raise ValidationError."""
        from resume_as_code.models.scope import Scope

        with pytest.raises(ValidationError) as exc_info:
            Scope(extra_field="value")  # type: ignore[call-arg]
        assert "extra" in str(exc_info.value).lower()

    def test_scope_partial_fields(self) -> None:
        """Scope can be created with partial fields."""
        from resume_as_code.models.scope import Scope

        scope = Scope(
            revenue="$200M",
            team_size=50,
        )
        assert scope.revenue == "$200M"
        assert scope.team_size == 50
        assert scope.budget is None
        assert scope.geography is None


class TestScopeExport:
    """Tests for Scope model exports."""

    def test_scope_exported_from_models_init(self) -> None:
        """Scope should be importable from models package."""
        from resume_as_code.models import Scope

        scope = Scope(revenue="$100M")
        assert scope.revenue == "$100M"

    def test_scope_in_all(self) -> None:
        """Scope should be in __all__ list."""
        from resume_as_code import models

        assert "Scope" in models.__all__

    def test_position_scope_alias_exported(self) -> None:
        """PositionScope alias should be importable and identical to Scope.

        Story 7.2: PositionScope is kept as alias for backwards compatibility.
        """
        from resume_as_code.models.position import PositionScope
        from resume_as_code.models.scope import Scope

        assert PositionScope is Scope  # Same class, not just equal


class TestScopeFieldDescriptions:
    """Tests for field descriptions in JSON schema."""

    def test_scope_has_field_descriptions(self) -> None:
        """All fields should have descriptions in JSON schema."""
        from resume_as_code.models.scope import Scope

        schema = Scope.model_json_schema()
        properties = schema.get("properties", {})

        # Check each field has a description
        expected_fields = [
            "revenue",
            "team_size",
            "direct_reports",
            "budget",
            "pl_responsibility",
            "geography",
            "customers",
        ]
        for field in expected_fields:
            assert field in properties, f"Field {field} missing from schema"
            assert "description" in properties[field], f"Field {field} missing description"
