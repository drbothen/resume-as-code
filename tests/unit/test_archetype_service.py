"""Tests for archetype service."""

from __future__ import annotations

import pytest

from resume_as_code.services.archetype_service import (
    list_archetypes,
    load_archetype,
    load_archetype_data,
)


class TestListArchetypes:
    """Tests for list_archetypes function."""

    def test_returns_available_archetypes(self) -> None:
        """Should return list of archetype names."""
        archetypes = list_archetypes()
        assert isinstance(archetypes, list)
        assert "incident" in archetypes
        assert "greenfield" in archetypes
        assert "leadership" in archetypes

    def test_includes_executive_archetypes(self) -> None:
        """Should include executive-level archetypes."""
        archetypes = list_archetypes()
        assert "transformation" in archetypes
        assert "cultural" in archetypes
        assert "strategic" in archetypes

    def test_includes_utility_archetypes(self) -> None:
        """Should include utility archetypes."""
        archetypes = list_archetypes()
        assert "migration" in archetypes
        assert "optimization" in archetypes
        assert "minimal" in archetypes


class TestLoadArchetype:
    """Tests for load_archetype function."""

    def test_returns_file_content_as_string(self) -> None:
        """Should return archetype file content as string."""
        content = load_archetype("incident")
        assert isinstance(content, str)
        assert "schema_version" in content
        assert "problem" in content
        assert "actions" in content
        assert "outcome" in content

    def test_preserves_yaml_comments(self) -> None:
        """Should preserve YAML comments in content."""
        content = load_archetype("incident")
        assert "#" in content  # Comments are preserved

    def test_invalid_archetype_raises(self) -> None:
        """Should raise FileNotFoundError for invalid archetype."""
        with pytest.raises(FileNotFoundError, match="Archetype 'nonexistent' not found"):
            load_archetype("nonexistent")


class TestLoadArchetypeData:
    """Tests for load_archetype_data function."""

    def test_returns_parsed_dict(self) -> None:
        """Should return parsed YAML as dict."""
        data = load_archetype_data("incident")
        assert isinstance(data, dict)
        assert "id" in data
        assert "title" in data
        assert "problem" in data
        assert "actions" in data
        assert "outcome" in data

    def test_incident_has_required_structure(self) -> None:
        """Incident archetype should have incident-specific fields."""
        data = load_archetype_data("incident")
        assert data.get("tags") is not None
        # Should have skills_demonstrated for incident response
        assert "skills_demonstrated" in data

    def test_greenfield_has_required_structure(self) -> None:
        """Greenfield archetype should have project-specific fields."""
        data = load_archetype_data("greenfield")
        assert "time_started" in data
        assert "time_ended" in data

    def test_leadership_has_scope_section(self) -> None:
        """Leadership archetype should have scope section."""
        data = load_archetype_data("leadership")
        assert "scope" in data

    def test_transformation_has_executive_fields(self) -> None:
        """Transformation archetype should have executive-level fields."""
        data = load_archetype_data("transformation")
        assert "scope" in data
        assert "impact_category" in data
        assert "metrics" in data
