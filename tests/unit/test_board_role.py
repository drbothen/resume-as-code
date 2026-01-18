"""Tests for BoardRole model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from resume_as_code.models.board_role import BoardRole, BoardRoleType
from resume_as_code.models.config import ResumeConfig
from resume_as_code.models.resume import ContactInfo, ResumeData


class TestBoardRoleModel:
    """Tests for BoardRole model validation and behavior."""

    def test_create_minimal_board_role(self) -> None:
        """Should create board role with minimal required fields."""
        role = BoardRole(
            organization="Tech Nonprofit Foundation",
            role="Board Advisor",
            start_date="2023-01",
        )

        assert role.organization == "Tech Nonprofit Foundation"
        assert role.role == "Board Advisor"
        assert role.start_date == "2023-01"
        assert role.type == "advisory"  # Default
        assert role.end_date is None
        assert role.focus is None
        assert role.display is True

    def test_create_full_board_role(self) -> None:
        """Should create board role with all fields."""
        role = BoardRole(
            organization="Tech Nonprofit Foundation",
            role="Board Director",
            type="director",
            start_date="2022-06",
            end_date="2024-12",
            focus="Technology strategy and digital transformation",
            display=True,
        )

        assert role.organization == "Tech Nonprofit Foundation"
        assert role.role == "Board Director"
        assert role.type == "director"
        assert role.start_date == "2022-06"
        assert role.end_date == "2024-12"
        assert role.focus == "Technology strategy and digital transformation"
        assert role.display is True

    def test_board_role_type_director(self) -> None:
        """Should accept director type."""
        role = BoardRole(
            organization="Company",
            role="Director",
            type="director",
            start_date="2023-01",
        )
        assert role.type == "director"

    def test_board_role_type_advisory(self) -> None:
        """Should accept advisory type."""
        role = BoardRole(
            organization="Company",
            role="Advisor",
            type="advisory",
            start_date="2023-01",
        )
        assert role.type == "advisory"

    def test_board_role_type_committee(self) -> None:
        """Should accept committee type."""
        role = BoardRole(
            organization="Company",
            role="Committee Member",
            type="committee",
            start_date="2023-01",
        )
        assert role.type == "committee"

    def test_board_role_invalid_type(self) -> None:
        """Should reject invalid board role type."""
        with pytest.raises(ValidationError) as exc_info:
            BoardRole(
                organization="Company",
                role="Member",
                type="invalid",  # type: ignore[arg-type]
                start_date="2023-01",
            )
        assert "type" in str(exc_info.value)


class TestBoardRoleDateValidation:
    """Tests for date format validation."""

    def test_valid_start_date_format(self) -> None:
        """Should accept valid YYYY-MM format for start_date."""
        role = BoardRole(
            organization="Company",
            role="Advisor",
            start_date="2023-06",
        )
        assert role.start_date == "2023-06"

    def test_valid_end_date_format(self) -> None:
        """Should accept valid YYYY-MM format for end_date."""
        role = BoardRole(
            organization="Company",
            role="Advisor",
            start_date="2022-01",
            end_date="2023-12",
        )
        assert role.end_date == "2023-12"

    def test_invalid_start_date_format(self) -> None:
        """Should reject invalid start_date format."""
        with pytest.raises(ValidationError) as exc_info:
            BoardRole(
                organization="Company",
                role="Advisor",
                start_date="June 2023",
            )
        assert "YYYY-MM" in str(exc_info.value)

    def test_invalid_end_date_format(self) -> None:
        """Should reject invalid end_date format."""
        with pytest.raises(ValidationError) as exc_info:
            BoardRole(
                organization="Company",
                role="Advisor",
                start_date="2022-01",
                end_date="2023",
            )
        assert "YYYY-MM" in str(exc_info.value)

    def test_null_end_date_for_current_role(self) -> None:
        """Should allow null end_date for current roles."""
        role = BoardRole(
            organization="Company",
            role="Advisor",
            start_date="2023-01",
            end_date=None,
        )
        assert role.end_date is None


class TestBoardRoleIsCurrent:
    """Tests for is_current property."""

    def test_is_current_true_when_no_end_date(self) -> None:
        """Should return True when end_date is None."""
        role = BoardRole(
            organization="Company",
            role="Advisor",
            start_date="2023-01",
            end_date=None,
        )
        assert role.is_current is True

    def test_is_current_false_when_end_date_set(self) -> None:
        """Should return False when end_date is set."""
        role = BoardRole(
            organization="Company",
            role="Advisor",
            start_date="2022-01",
            end_date="2023-12",
        )
        assert role.is_current is False


class TestBoardRoleDateRange:
    """Tests for format_date_range method."""

    def test_format_date_range_current(self) -> None:
        """Should format as 'YYYY - Present' for current roles."""
        role = BoardRole(
            organization="Company",
            role="Advisor",
            start_date="2023-01",
        )
        assert role.format_date_range() == "2023 - Present"

    def test_format_date_range_past(self) -> None:
        """Should format as 'YYYY - YYYY' for past roles."""
        role = BoardRole(
            organization="Company",
            role="Advisor",
            start_date="2020-06",
            end_date="2023-12",
        )
        assert role.format_date_range() == "2020 - 2023"

    def test_format_date_range_same_year(self) -> None:
        """Should format correctly when start and end are same year."""
        role = BoardRole(
            organization="Company",
            role="Advisor",
            start_date="2023-01",
            end_date="2023-06",
        )
        assert role.format_date_range() == "2023 - 2023"


class TestBoardRoleTypeAlias:
    """Tests for BoardRoleType type alias."""

    def test_board_role_type_values(self) -> None:
        """Should define correct Literal values for BoardRoleType."""
        # This is a type check - just verify valid values work
        valid_types: list[BoardRoleType] = ["director", "advisory", "committee"]
        for role_type in valid_types:
            role = BoardRole(
                organization="Company",
                role="Member",
                type=role_type,
                start_date="2023-01",
            )
            assert role.type == role_type


class TestBoardRoleConfigLoading:
    """Tests for loading board roles from config."""

    def test_load_board_roles_from_config(self) -> None:
        """Should load board roles from config dict."""
        config_data = {
            "board_roles": [
                {
                    "organization": "Tech Nonprofit Foundation",
                    "role": "Board Advisor",
                    "type": "advisory",
                    "start_date": "2023-01",
                    "focus": "Technology strategy",
                },
                {
                    "organization": "Startup Accelerator",
                    "role": "Technical Advisory Board Member",
                    "type": "advisory",
                    "start_date": "2021-06",
                    "end_date": "2023-12",
                    "focus": "Technical due diligence",
                },
            ]
        }
        config = ResumeConfig.model_validate(config_data)

        assert len(config.board_roles) == 2
        assert config.board_roles[0].organization == "Tech Nonprofit Foundation"
        assert config.board_roles[0].role == "Board Advisor"
        assert config.board_roles[0].type == "advisory"
        assert config.board_roles[0].is_current is True
        assert config.board_roles[1].end_date == "2023-12"
        assert config.board_roles[1].is_current is False

    def test_load_empty_board_roles(self) -> None:
        """Should default to None when no board_roles in config (Story 9.2).

        Note: Access board roles via data_loader for actual usage.
        """
        config = ResumeConfig.model_validate({})

        assert config.board_roles is None

    def test_load_director_type_board_role(self) -> None:
        """Should load director type board roles."""
        config_data = {
            "board_roles": [
                {
                    "organization": "Public Company",
                    "role": "Independent Board Director",
                    "type": "director",
                    "start_date": "2020-01",
                }
            ]
        }
        config = ResumeConfig.model_validate(config_data)

        assert len(config.board_roles) == 1
        assert config.board_roles[0].type == "director"

    def test_load_committee_type_board_role(self) -> None:
        """Should load committee type board roles."""
        config_data = {
            "board_roles": [
                {
                    "organization": "Industry Association",
                    "role": "Standards Committee Chair",
                    "type": "committee",
                    "start_date": "2022-06",
                }
            ]
        }
        config = ResumeConfig.model_validate(config_data)

        assert len(config.board_roles) == 1
        assert config.board_roles[0].type == "committee"


class TestBoardRoleSorting:
    """Tests for board role sorting in ResumeData."""

    def _make_resume_data(self, board_roles: list[BoardRole]) -> ResumeData:
        """Helper to create ResumeData with board roles."""
        return ResumeData(
            contact=ContactInfo(name="Test User"),
            board_roles=board_roles,
        )

    def test_directors_sorted_before_advisory(self) -> None:
        """Should sort directors before advisory roles."""
        roles = [
            BoardRole(
                organization="Advisory Co",
                role="Advisor",
                type="advisory",
                start_date="2023-01",
            ),
            BoardRole(
                organization="Director Co",
                role="Director",
                type="director",
                start_date="2022-01",
            ),
        ]
        resume = self._make_resume_data(roles)
        sorted_roles = resume.get_sorted_board_roles()

        assert len(sorted_roles) == 2
        assert sorted_roles[0].type == "director"
        assert sorted_roles[1].type == "advisory"

    def test_directors_sorted_before_committee(self) -> None:
        """Should sort directors before committee roles."""
        roles = [
            BoardRole(
                organization="Committee Co",
                role="Committee Chair",
                type="committee",
                start_date="2023-01",
            ),
            BoardRole(
                organization="Director Co",
                role="Director",
                type="director",
                start_date="2022-01",
            ),
        ]
        resume = self._make_resume_data(roles)
        sorted_roles = resume.get_sorted_board_roles()

        assert sorted_roles[0].type == "director"
        assert sorted_roles[1].type == "committee"

    def test_same_type_sorted_by_date_descending(self) -> None:
        """Should sort same type by start_date descending."""
        roles = [
            BoardRole(
                organization="Old Co",
                role="Advisor",
                type="advisory",
                start_date="2020-01",
            ),
            BoardRole(
                organization="New Co",
                role="Advisor",
                type="advisory",
                start_date="2023-01",
            ),
            BoardRole(
                organization="Mid Co",
                role="Advisor",
                type="advisory",
                start_date="2021-06",
            ),
        ]
        resume = self._make_resume_data(roles)
        sorted_roles = resume.get_sorted_board_roles()

        assert sorted_roles[0].organization == "New Co"
        assert sorted_roles[1].organization == "Mid Co"
        assert sorted_roles[2].organization == "Old Co"

    def test_hidden_roles_excluded(self) -> None:
        """Should exclude roles with display=False."""
        roles = [
            BoardRole(
                organization="Visible Co",
                role="Advisor",
                type="advisory",
                start_date="2023-01",
                display=True,
            ),
            BoardRole(
                organization="Hidden Co",
                role="Advisor",
                type="advisory",
                start_date="2022-01",
                display=False,
            ),
        ]
        resume = self._make_resume_data(roles)
        sorted_roles = resume.get_sorted_board_roles()

        assert len(sorted_roles) == 1
        assert sorted_roles[0].organization == "Visible Co"

    def test_complex_sorting(self) -> None:
        """Should handle complex sorting with multiple types and dates."""
        roles = [
            BoardRole(
                organization="Old Advisory",
                role="Advisor",
                type="advisory",
                start_date="2019-01",
            ),
            BoardRole(
                organization="Old Director",
                role="Director",
                type="director",
                start_date="2020-01",
            ),
            BoardRole(
                organization="New Advisory",
                role="Advisor",
                type="advisory",
                start_date="2023-01",
            ),
            BoardRole(
                organization="New Director",
                role="Director",
                type="director",
                start_date="2022-01",
            ),
            BoardRole(
                organization="Committee",
                role="Chair",
                type="committee",
                start_date="2021-01",
            ),
        ]
        resume = self._make_resume_data(roles)
        sorted_roles = resume.get_sorted_board_roles()

        # Expected order: directors (by date desc), then advisory (by date desc), then committee
        assert sorted_roles[0].organization == "New Director"
        assert sorted_roles[1].organization == "Old Director"
        assert sorted_roles[2].organization == "New Advisory"
        assert sorted_roles[3].organization == "Old Advisory"
        assert sorted_roles[4].organization == "Committee"

    def test_empty_board_roles(self) -> None:
        """Should return empty list when no board roles."""
        resume = self._make_resume_data([])
        sorted_roles = resume.get_sorted_board_roles()

        assert sorted_roles == []


class TestBoardRoleTemplateRendering:
    """Tests for board role template rendering."""

    def test_template_renders_board_roles_section(self) -> None:
        """Should render Board & Advisory Roles section when board roles exist."""
        from pathlib import Path

        from jinja2 import Environment, FileSystemLoader

        template_path = Path("src/resume_as_code/templates")
        env = Environment(loader=FileSystemLoader(template_path))
        template = env.get_template("executive.html")

        resume = ResumeData(
            contact=ContactInfo(name="Test User"),
            board_roles=[
                BoardRole(
                    organization="Tech Nonprofit Foundation",
                    role="Board Advisor",
                    type="advisory",
                    start_date="2023-01",
                    focus="Technology strategy",
                ),
            ],
        )

        html = template.render(resume=resume, css="")

        assert "Board & Advisory Roles" in html
        assert "Tech Nonprofit Foundation" in html
        assert "Board Advisor" in html
        assert "Technology strategy" in html
        assert "2023 - Present" in html

    def test_template_hides_board_roles_section_when_empty(self) -> None:
        """Should not render Board & Advisory Roles section when no board roles."""
        from pathlib import Path

        from jinja2 import Environment, FileSystemLoader

        template_path = Path("src/resume_as_code/templates")
        env = Environment(loader=FileSystemLoader(template_path))
        template = env.get_template("executive.html")

        resume = ResumeData(
            contact=ContactInfo(name="Test User"),
            board_roles=[],
        )

        html = template.render(resume=resume, css="")

        assert "Board & Advisory Roles" not in html

    def test_template_renders_multiple_board_roles(self) -> None:
        """Should render multiple board roles in sorted order."""
        from pathlib import Path

        from jinja2 import Environment, FileSystemLoader

        template_path = Path("src/resume_as_code/templates")
        env = Environment(loader=FileSystemLoader(template_path))
        template = env.get_template("executive.html")

        resume = ResumeData(
            contact=ContactInfo(name="Test User"),
            board_roles=[
                BoardRole(
                    organization="Advisory Co",
                    role="Advisor",
                    type="advisory",
                    start_date="2022-01",
                ),
                BoardRole(
                    organization="Director Co",
                    role="Board Director",
                    type="director",
                    start_date="2021-01",
                ),
            ],
        )

        html = template.render(resume=resume, css="")

        assert "Board & Advisory Roles" in html
        assert "Advisory Co" in html
        assert "Director Co" in html
        # Director should appear first in get_sorted_board_roles()
        director_pos = html.find("Director Co")
        advisory_pos = html.find("Advisory Co")
        assert director_pos < advisory_pos

    def test_template_renders_past_role_with_end_date(self) -> None:
        """Should render past board role with end date."""
        from pathlib import Path

        from jinja2 import Environment, FileSystemLoader

        template_path = Path("src/resume_as_code/templates")
        env = Environment(loader=FileSystemLoader(template_path))
        template = env.get_template("executive.html")

        resume = ResumeData(
            contact=ContactInfo(name="Test User"),
            board_roles=[
                BoardRole(
                    organization="Past Org",
                    role="Former Advisor",
                    type="advisory",
                    start_date="2020-01",
                    end_date="2022-12",
                ),
            ],
        )

        html = template.render(resume=resume, css="")

        assert "Past Org" in html
        assert "2020 - 2022" in html
        assert "Present" not in html

    def test_template_excludes_hidden_board_roles(self) -> None:
        """Should not render board roles with display=False."""
        from pathlib import Path

        from jinja2 import Environment, FileSystemLoader

        template_path = Path("src/resume_as_code/templates")
        env = Environment(loader=FileSystemLoader(template_path))
        template = env.get_template("executive.html")

        resume = ResumeData(
            contact=ContactInfo(name="Test User"),
            board_roles=[
                BoardRole(
                    organization="Visible Co",
                    role="Advisor",
                    type="advisory",
                    start_date="2023-01",
                    display=True,
                ),
                BoardRole(
                    organization="Hidden Co",
                    role="Secret Advisor",
                    type="advisory",
                    start_date="2022-01",
                    display=False,
                ),
            ],
        )

        html = template.render(resume=resume, css="")

        assert "Visible Co" in html
        assert "Hidden Co" not in html
        assert "Secret Advisor" not in html
