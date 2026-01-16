"""Unit tests for unified Scope model and scope formatting.

Tests scope indicator functionality for executive positions:
- Unified Scope model validation (Story 7.2)
- format_scope_line() service function
- Scope rendering in ResumeData

Note: PositionScope is now an alias for the unified Scope model.
"""

from __future__ import annotations

from resume_as_code.models.position import Position
from resume_as_code.models.scope import Scope
from resume_as_code.services.position_service import format_scope_line


class TestUnifiedScopeModel:
    """Tests for unified Scope Pydantic model (Story 7.2)."""

    def test_all_fields_populated(self) -> None:
        """Test scope with all fields populated."""
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

    def test_all_fields_optional(self) -> None:
        """Test that all scope fields are optional."""
        scope = Scope()
        assert scope.revenue is None
        assert scope.team_size is None
        assert scope.direct_reports is None
        assert scope.budget is None
        assert scope.pl_responsibility is None
        assert scope.geography is None
        assert scope.customers is None

    def test_partial_fields(self) -> None:
        """Test scope with only some fields populated."""
        scope = Scope(
            revenue="$200M",
            team_size=50,
        )
        assert scope.revenue == "$200M"
        assert scope.team_size == 50
        assert scope.budget is None
        assert scope.geography is None


class TestPositionWithScope:
    """Tests for Position model with scope field."""

    def test_position_with_scope(self) -> None:
        """Test position can have scope data."""
        position = Position(
            id="pos-acme-cto",
            employer="Acme Corporation",
            title="Chief Technology Officer",
            start_date="2020-01",
            scope=Scope(
                revenue="$500M",
                team_size=200,
                pl_responsibility="$100M",
            ),
        )
        assert position.scope is not None
        assert position.scope.revenue == "$500M"
        assert position.scope.team_size == 200
        assert position.scope.pl_responsibility == "$100M"

    def test_position_without_scope(self) -> None:
        """Test position scope is optional."""
        position = Position(
            id="pos-startup-engineer",
            employer="Startup Inc",
            title="Software Engineer",
            start_date="2018-06",
            end_date="2020-01",
        )
        assert position.scope is None

    def test_position_with_empty_scope(self) -> None:
        """Test position with empty scope object."""
        position = Position(
            id="pos-techcorp-lead",
            employer="TechCorp",
            title="Tech Lead",
            start_date="2019-01",
            scope=Scope(),
        )
        assert position.scope is not None
        assert position.scope.revenue is None


class TestFormatScopeLine:
    """Tests for format_scope_line() service function."""

    def test_format_scope_line_all_fields(self) -> None:
        """Test scope line with all fields populated (AC: #2)."""
        position = Position(
            id="pos-acme-cto",
            employer="Acme Corp",
            title="CTO",
            start_date="2020-01",
            scope=Scope(
                pl_responsibility="$100M",
                revenue="$500M",
                team_size=200,
                budget="$50M",
                geography="Global (15 countries)",
            ),
        )
        result = format_scope_line(position)
        # P&L first (AC: #3)
        assert result is not None
        assert result.startswith("$100M P&L")
        assert "$500M revenue" in result
        assert "200+ engineers" in result
        assert "$50M budget" in result
        assert "Global (15 countries)" in result
        # Pipe-separated (AC: #4)
        assert " | " in result

    def test_format_scope_line_pl_first(self) -> None:
        """Test P&L appears first in scope line (AC: #3)."""
        position = Position(
            id="pos-test",
            employer="Test Corp",
            title="VP",
            start_date="2020-01",
            scope=Scope(
                revenue="$200M",
                pl_responsibility="$50M",
            ),
        )
        result = format_scope_line(position)
        assert result is not None
        assert result.startswith("$50M P&L")

    def test_format_scope_line_partial_fields(self) -> None:
        """Test scope line with only some fields (AC: #4)."""
        position = Position(
            id="pos-test",
            employer="Test Corp",
            title="Director",
            start_date="2021-01",
            scope=Scope(
                team_size=50,
                geography="EMEA",
            ),
        )
        result = format_scope_line(position)
        assert result is not None
        assert "50+ engineers" in result
        assert "EMEA" in result
        # Should NOT contain fields that weren't set
        assert "P&L" not in result
        assert "revenue" not in result
        assert "budget" not in result

    def test_format_scope_line_no_scope(self) -> None:
        """Test position without scope returns None (AC: #4)."""
        position = Position(
            id="pos-engineer",
            employer="Startup",
            title="Engineer",
            start_date="2019-01",
        )
        result = format_scope_line(position)
        assert result is None

    def test_format_scope_line_empty_scope(self) -> None:
        """Test empty scope object returns None (AC: #4)."""
        position = Position(
            id="pos-test",
            employer="Test Corp",
            title="Lead",
            start_date="2020-01",
            scope=Scope(),
        )
        result = format_scope_line(position)
        assert result is None

    def test_format_scope_line_single_field(self) -> None:
        """Test scope line with single field (no pipe separator)."""
        position = Position(
            id="pos-test",
            employer="Test Corp",
            title="Manager",
            start_date="2020-01",
            scope=Scope(team_size=30),
        )
        result = format_scope_line(position)
        assert result == "30+ engineers"
        assert " | " not in result

    def test_format_scope_line_direct_reports(self) -> None:
        """Test direct_reports field formatting."""
        position = Position(
            id="pos-test",
            employer="Test Corp",
            title="VP",
            start_date="2020-01",
            scope=Scope(direct_reports=8),
        )
        result = format_scope_line(position)
        assert result is not None
        assert "8 direct reports" in result

    def test_format_scope_line_customers(self) -> None:
        """Test customers field formatting."""
        position = Position(
            id="pos-test",
            employer="Test Corp",
            title="CTO",
            start_date="2020-01",
            scope=Scope(customers="500K users"),
        )
        result = format_scope_line(position)
        assert result is not None
        assert "500K users" in result


class TestResumeItemScopeLine:
    """Tests for scope_line in ResumeItem (AC: #2, #5)."""

    def test_resume_item_has_scope_line(self) -> None:
        """Test ResumeItem includes scope_line field."""
        from resume_as_code.models.resume import ResumeItem

        item = ResumeItem(
            title="CTO",
            organization="Acme Corp",
            scope_line="$100M P&L | $500M revenue | 200+ engineers",
        )
        assert item.scope_line == "$100M P&L | $500M revenue | 200+ engineers"

    def test_resume_item_scope_line_optional(self) -> None:
        """Test scope_line is optional."""
        from resume_as_code.models.resume import ResumeItem

        item = ResumeItem(
            title="Engineer",
            organization="Startup",
        )
        assert item.scope_line is None


class TestBuildItemFromPosition:
    """Tests for _build_item_from_position with scope data (AC: #2, #5)."""

    def test_build_item_includes_scope_line(self) -> None:
        """Test that position scope is converted to scope_line (AC: #2)."""
        from resume_as_code.models.resume import ResumeData

        position = Position(
            id="pos-acme-cto",
            employer="Acme Corp",
            title="CTO",
            start_date="2020-01",
            scope=Scope(
                pl_responsibility="$100M",
                revenue="$500M",
                team_size=200,
            ),
        )
        work_units: list[dict] = []  # type: ignore[type-arg]

        item = ResumeData._build_item_from_position(position, work_units)

        assert item.scope_line is not None
        assert "$100M P&L" in item.scope_line
        assert "$500M revenue" in item.scope_line
        assert "200+ engineers" in item.scope_line

    def test_build_item_position_scope_only(self) -> None:
        """Test position scope is used exclusively (Story 7.2 - unified model).

        WorkUnit.scope is deprecated - only Position.scope is used for scope_line.
        """
        from resume_as_code.models.resume import ResumeData

        position = Position(
            id="pos-acme-cto",
            employer="Acme Corp",
            title="CTO",
            start_date="2020-01",
            scope=Scope(
                team_size=200,
                revenue="$500M",
            ),
        )
        work_units = [
            {
                "title": "Some achievement",
                # WorkUnit.scope is deprecated and ignored for resume rendering
                "scope": {
                    "team_size": 50,
                    "revenue_influenced": "$100M",
                },
            }
        ]

        item = ResumeData._build_item_from_position(position, work_units)

        # Only position scope is used (Story 7.2 AC #1, #4)
        assert item.scope_line is not None
        assert "200+ engineers" in item.scope_line
        assert "$500M revenue" in item.scope_line
        # Work unit scope values are NOT captured - unified model means position only

    def test_build_item_no_scope_line_when_position_has_no_scope(self) -> None:
        """Test no scope_line when position has no scope data."""
        from resume_as_code.models.resume import ResumeData

        position = Position(
            id="pos-startup-engineer",
            employer="Startup",
            title="Engineer",
            start_date="2019-01",
            end_date="2020-01",
        )
        work_units: list[dict] = []  # type: ignore[type-arg]

        item = ResumeData._build_item_from_position(position, work_units)

        assert item.scope_line is None


class TestPositionCommandScope:
    """Tests for position command scope flags (AC: #6, #7)."""

    def test_build_position_scope_all_fields(self) -> None:
        """Test _build_position_scope with all fields."""
        from resume_as_code.commands.new import _build_position_scope

        scope = _build_position_scope(
            revenue="$500M",
            team_size=200,
            direct_reports=15,
            budget="$50M",
            pl="$100M",
            geography="Global",
        )

        assert scope is not None
        assert scope.revenue == "$500M"
        assert scope.team_size == 200
        assert scope.direct_reports == 15
        assert scope.budget == "$50M"
        assert scope.pl_responsibility == "$100M"
        assert scope.geography == "Global"

    def test_build_position_scope_partial_fields(self) -> None:
        """Test _build_position_scope with partial fields."""
        from resume_as_code.commands.new import _build_position_scope

        scope = _build_position_scope(
            revenue="$200M",
            team_size=50,
            direct_reports=None,
            budget=None,
            pl=None,
            geography="EMEA",
        )

        assert scope is not None
        assert scope.revenue == "$200M"
        assert scope.team_size == 50
        assert scope.geography == "EMEA"
        assert scope.direct_reports is None
        assert scope.budget is None
        assert scope.pl_responsibility is None

    def test_build_position_scope_returns_none_when_empty(self) -> None:
        """Test _build_position_scope returns None when no fields."""
        from resume_as_code.commands.new import _build_position_scope

        scope = _build_position_scope(
            revenue=None,
            team_size=None,
            direct_reports=None,
            budget=None,
            pl=None,
            geography=None,
        )

        assert scope is None


class TestTemplateRendering:
    """Tests for scope_line template rendering (AC: #2)."""

    def test_template_renders_scope_line(self) -> None:
        """Test executive template renders scope_line."""
        from pathlib import Path

        from jinja2 import Environment, FileSystemLoader

        from resume_as_code.models.resume import (
            ContactInfo,
            ResumeData,
            ResumeItem,
            ResumeSection,
        )

        template_dir = Path(__file__).parent.parent.parent / "src" / "resume_as_code" / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("executive.html")

        resume = ResumeData(
            contact=ContactInfo(name="Test User"),
            sections=[
                ResumeSection(
                    title="Experience",
                    items=[
                        ResumeItem(
                            title="CTO",
                            organization="Acme Corp",
                            start_date="2020",
                            scope_line="$100M P&L | $500M revenue | 200+ engineers",
                        )
                    ],
                )
            ],
        )

        html = template.render(resume=resume, css="")

        assert "$100M P&L" in html
        assert "$500M revenue" in html
        assert "200+ engineers" in html
        assert 'class="scope-line"' in html

    def test_template_graceful_without_scope_line(self) -> None:
        """Test template renders gracefully without scope_line."""
        from pathlib import Path

        from jinja2 import Environment, FileSystemLoader

        from resume_as_code.models.resume import (
            ContactInfo,
            ResumeData,
            ResumeItem,
            ResumeSection,
        )

        template_dir = Path(__file__).parent.parent.parent / "src" / "resume_as_code" / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("executive.html")

        resume = ResumeData(
            contact=ContactInfo(name="Test User"),
            sections=[
                ResumeSection(
                    title="Experience",
                    items=[
                        ResumeItem(
                            title="Engineer",
                            organization="Startup",
                            start_date="2019",
                        )
                    ],
                )
            ],
        )

        html = template.render(resume=resume, css="")

        # Should render without error
        assert "Engineer" in html
        assert "Startup" in html
        # scope-line should NOT appear when no scope data
        assert html.count('class="scope-line"') == 0


class TestUnifiedScopeIntegration:
    """Integration tests for unified Scope model (Story 7.2 AC #1).

    Verifies that scope flows from Position to ResumeItem without
    requiring duplication in work units.
    """

    def test_ac1_no_scope_duplication_needed(self) -> None:
        """AC #1: Work units don't need to duplicate scope from position.

        Given a position with scope data
        When I create work units for that position
        Then I don't need to duplicate scope in work units
        And scope from position is used for resume rendering
        """
        from resume_as_code.models.resume import ResumeData

        # Position with executive scope data
        position = Position(
            id="pos-acme-cto",
            employer="Acme Corp",
            title="Chief Technology Officer",
            start_date="2020-01",
            scope=Scope(
                pl_responsibility="$100M",
                revenue="$500M",
                team_size=200,
                budget="$50M",
                geography="Global",
            ),
        )

        # Work units WITHOUT scope (no duplication needed per AC #1)
        work_units = [
            {
                "id": "wu-2024-01-01-achievement-one",
                "title": "Led major platform migration",
                "outcome": {"result": "Reduced costs by 40%"},
                "actions": ["Designed architecture", "Led execution"],
                # Note: NO scope field - using Position.scope instead
            },
            {
                "id": "wu-2024-06-01-achievement-two",
                "title": "Launched new product line",
                "outcome": {"result": "Generated $10M revenue"},
                "actions": ["Built team", "Delivered MVP"],
                # Note: NO scope field - using Position.scope instead
            },
        ]

        # Build ResumeItem from position and work units
        item = ResumeData._build_item_from_position(position, work_units)

        # Verify position scope is rendered (no duplication in work units)
        assert item.scope_line is not None
        assert "$100M P&L" in item.scope_line
        assert "$500M revenue" in item.scope_line
        assert "200+ engineers" in item.scope_line
        assert "$50M budget" in item.scope_line
        assert "Global" in item.scope_line

        # Verify work unit bullets are captured (2 outcomes + 4 actions = 6 total)
        assert len(item.bullets) == 6

    def test_ac1_scope_only_from_position_not_work_unit(self) -> None:
        """Verify scope_line is ONLY derived from Position, never from WorkUnit.

        Even if work units have legacy scope data, it is ignored.
        """
        from resume_as_code.models.resume import ResumeData

        # Position WITH scope
        position = Position(
            id="pos-test-director",
            employer="Test Corp",
            title="Director",
            start_date="2021-01",
            scope=Scope(team_size=50, geography="EMEA"),
        )

        # Work unit with DIFFERENT scope values (should be ignored)
        work_units = [
            {
                "title": "Achievement",
                "outcome": {"result": "Delivered project"},
                "actions": ["Did the work"],
                "scope": {
                    "team_size": 999,  # Different from position - should be ignored
                    "budget_managed": "$999M",  # Not in position - should not appear
                },
            }
        ]

        item = ResumeData._build_item_from_position(position, work_units)

        # Position scope is used
        assert item.scope_line is not None
        assert "50+ engineers" in item.scope_line
        assert "EMEA" in item.scope_line
        # Work unit scope is NOT used
        assert "999" not in item.scope_line
        assert "budget" not in item.scope_line.lower()
