"""Tests for Board Role Management Commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main
from resume_as_code.services.board_role_service import BoardRoleService


class TestBoardRoleServiceMatching:
    """Tests for board role matching in BoardRoleService."""

    def test_find_board_roles_by_organization_exact_match(self, tmp_path: Path) -> None:
        """Should find board role by exact organization match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    start_date: "2023-01"
  - organization: "Startup Accelerator"
    role: "Technical Advisor"
    start_date: "2022-01"
"""
        )
        service = BoardRoleService(config_path=config_path)
        matches = service.find_board_roles_by_organization("Tech Nonprofit Foundation")

        assert len(matches) == 1
        assert matches[0].organization == "Tech Nonprofit Foundation"

    def test_find_board_roles_by_organization_partial_match(self, tmp_path: Path) -> None:
        """Should find board roles by partial organization match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    start_date: "2023-01"
  - organization: "Tech Startup Accelerator"
    role: "Technical Advisor"
    start_date: "2022-01"
"""
        )
        service = BoardRoleService(config_path=config_path)
        matches = service.find_board_roles_by_organization("Tech")

        assert len(matches) == 2

    def test_find_board_roles_by_organization_case_insensitive(self, tmp_path: Path) -> None:
        """Should match case-insensitively."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    start_date: "2023-01"
"""
        )
        service = BoardRoleService(config_path=config_path)
        matches = service.find_board_roles_by_organization("TECH NONPROFIT")

        assert len(matches) == 1
        assert matches[0].organization == "Tech Nonprofit Foundation"

    def test_find_board_roles_by_organization_no_match(self, tmp_path: Path) -> None:
        """Should return empty list when no match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    start_date: "2023-01"
"""
        )
        service = BoardRoleService(config_path=config_path)
        matches = service.find_board_roles_by_organization("nonexistent")

        assert len(matches) == 0

    def test_find_board_roles_empty_config(self, tmp_path: Path) -> None:
        """Should handle empty board_roles list."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\n")
        service = BoardRoleService(config_path=config_path)
        matches = service.find_board_roles_by_organization("Tech")

        assert len(matches) == 0


class TestRemoveBoardRoleService:
    """Tests for remove_board_role in BoardRoleService."""

    def test_remove_board_role_success(self, tmp_path: Path) -> None:
        """Should remove board role successfully."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    start_date: "2023-01"
  - organization: "Startup Accelerator"
    role: "Technical Advisor"
    start_date: "2022-01"
"""
        )
        service = BoardRoleService(config_path=config_path)
        result = service.remove_board_role("Startup Accelerator")

        assert result is True

        # Verify removal
        roles = service.load_board_roles()
        assert len(roles) == 1
        assert roles[0].organization == "Tech Nonprofit Foundation"

    def test_remove_board_role_not_found(self, tmp_path: Path) -> None:
        """Should return False when board role not found."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    start_date: "2023-01"
"""
        )
        service = BoardRoleService(config_path=config_path)
        result = service.remove_board_role("nonexistent")

        assert result is False

    def test_remove_board_role_no_config_file(self, tmp_path: Path) -> None:
        """Should return False when config file doesn't exist."""
        config_path = tmp_path / ".resume.yaml"
        service = BoardRoleService(config_path=config_path)
        result = service.remove_board_role("Tech Nonprofit")

        assert result is False

    def test_remove_board_role_partial_match(self, tmp_path: Path) -> None:
        """Should remove by partial organization match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    start_date: "2023-01"
"""
        )
        service = BoardRoleService(config_path=config_path)
        result = service.remove_board_role("Nonprofit")

        assert result is True

        # Verify removal
        roles = service.load_board_roles()
        assert len(roles) == 0


class TestNewBoardRoleCommand:
    """Tests for `resume new board-role` command."""

    def test_new_board_role_non_interactive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create board role in non-interactive mode."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "board-role",
                "--organization",
                "Tech Nonprofit Foundation",
                "--role",
                "Board Advisor",
                "--type",
                "advisory",
                "--start-date",
                "2023-01",
            ],
        )

        assert result.exit_code == 0
        assert "Board role created" in result.output or "Tech Nonprofit Foundation" in result.output

        # Verify file was created
        config_path = tmp_path / ".resume.yaml"
        assert config_path.exists()

    def test_new_board_role_pipe_separated(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create board role from pipe-separated format."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "board-role",
                "Tech Nonprofit|Board Advisor|advisory|2023-01||Technology strategy",
            ],
        )

        assert result.exit_code == 0
        assert "Tech Nonprofit" in result.output or "Board role created" in result.output

    def test_new_board_role_director_type(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create director type board role."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "board-role",
                "--organization",
                "Public Company",
                "--role",
                "Independent Director",
                "--type",
                "director",
                "--start-date",
                "2022-01",
            ],
        )

        assert result.exit_code == 0

        # Verify type was set correctly
        service = BoardRoleService(config_path=tmp_path / ".resume.yaml")
        roles = service.load_board_roles()
        assert len(roles) == 1
        assert roles[0].type == "director"

    def test_new_board_role_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON in json mode."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "--json",
                "new",
                "board-role",
                "--organization",
                "Test Org",
                "--role",
                "Advisor",
                "--start-date",
                "2023-01",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["board_role_created"] is True

    def test_new_board_role_duplicate_detection(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should detect duplicate board roles."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit"
    role: "Board Advisor"
    start_date: "2023-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "board-role",
                "--organization",
                "Tech Nonprofit",
                "--role",
                "Board Advisor",
                "--start-date",
                "2023-01",
            ],
        )

        # Should indicate already exists (not an error, just info)
        assert "already exists" in result.output

    def test_new_board_role_with_focus(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create board role with focus area."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "board-role",
                "--organization",
                "Accelerator",
                "--role",
                "Technical Advisor",
                "--start-date",
                "2022-06",
                "--focus",
                "Technical due diligence for investments",
            ],
        )

        assert result.exit_code == 0

        # Verify focus was saved
        service = BoardRoleService(config_path=tmp_path / ".resume.yaml")
        roles = service.load_board_roles()
        assert len(roles) == 1
        assert roles[0].focus == "Technical due diligence for investments"

    def test_new_board_role_with_end_date(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create board role with end date."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "board-role",
                "--organization",
                "Past Org",
                "--role",
                "Former Advisor",
                "--start-date",
                "2020-01",
                "--end-date",
                "2022-12",
            ],
        )

        assert result.exit_code == 0

        # Verify end date was saved
        service = BoardRoleService(config_path=tmp_path / ".resume.yaml")
        roles = service.load_board_roles()
        assert len(roles) == 1
        assert roles[0].end_date == "2022-12"
        assert roles[0].is_current is False


class TestListBoardRolesCommand:
    """Tests for `resume list board-roles` command."""

    def test_list_board_roles_table_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should display board roles in table format."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    type: "advisory"
    start_date: "2023-01"
  - organization: "Startup Accelerator"
    role: "Technical Advisor"
    type: "advisory"
    start_date: "2021-06"
    end_date: "2023-12"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "board-roles"])

        assert result.exit_code == 0
        assert "Tech Nonprofit Foundation" in result.output
        assert "Startup Accelerator" in result.output
        assert "Board" in result.output or "Advisory" in result.output

    def test_list_board_roles_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should handle empty board_roles list."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "board-roles"])

        assert result.exit_code == 0
        assert "No board roles found" in result.output

    def test_list_board_roles_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON with all board role fields."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit"
    role: "Board Advisor"
    type: "advisory"
    start_date: "2023-01"
    focus: "Technology strategy"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "list", "board-roles"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert len(data["data"]["board_roles"]) == 1
        assert data["data"]["board_roles"][0]["organization"] == "Tech Nonprofit"
        assert data["data"]["board_roles"][0]["type"] == "advisory"

    def test_list_board_roles_json_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output empty JSON list when no board roles."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "list", "board-roles"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["count"] == 0
        assert data["data"]["board_roles"] == []

    def test_list_board_roles_shows_status(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show Current/Past status for board roles."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Current Org"
    role: "Active Advisor"
    start_date: "2023-01"
  - organization: "Past Org"
    role: "Former Advisor"
    start_date: "2020-01"
    end_date: "2022-12"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "board-roles"])

        assert result.exit_code == 0
        assert "Current" in result.output
        assert "Past" in result.output


class TestRemoveBoardRoleCommand:
    """Tests for `resume remove board-role` command."""

    def test_remove_board_role_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should remove board role with --yes flag."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    start_date: "2023-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "board-role", "Tech Nonprofit", "--yes"])

        assert result.exit_code == 0
        assert "Removed board role" in result.output

    def test_remove_board_role_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when board role not found."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    start_date: "2023-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "board-role", "nonexistent", "--yes"])

        assert result.exit_code == 4  # NOT_FOUND
        assert "No board role found" in result.output

    def test_remove_board_role_multiple_matches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when multiple board roles match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Foundation One"
    role: "Advisor"
    start_date: "2023-01"
  - organization: "Tech Foundation Two"
    role: "Advisor"
    start_date: "2022-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "board-role", "Tech", "--yes"])

        assert result.exit_code == 1
        assert "Multiple board roles match" in result.output

    def test_remove_board_role_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON on successful removal."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    start_date: "2023-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "remove", "board-role", "Tech Nonprofit", "--yes"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["removed"] is True
        assert data["data"]["organization"] == "Tech Nonprofit Foundation"

    def test_remove_board_role_interactive_confirm(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should prompt for confirmation in interactive mode."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    start_date: "2023-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Simulate user typing 'y' for confirmation
        result = runner.invoke(main, ["remove", "board-role", "Tech Nonprofit"], input="y\n")

        assert result.exit_code == 0
        assert "Removed board role" in result.output

    def test_remove_board_role_interactive_cancel(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should cancel when user declines confirmation."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    start_date: "2023-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Simulate user typing 'n' to decline
        result = runner.invoke(main, ["remove", "board-role", "Tech Nonprofit"], input="n\n")

        assert result.exit_code == 0
        assert "Cancelled" in result.output

        # Verify board role was not removed
        service = BoardRoleService(config_path=config_path)
        roles = service.load_board_roles()
        assert len(roles) == 1


class TestShowBoardRoleCommand:
    """Tests for `resume show board-role` command."""

    def test_show_board_role_by_organization(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should display board role details by organization."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    type: "advisory"
    start_date: "2023-01"
    focus: "Technology strategy and digital transformation"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "board-role", "Tech Nonprofit"])

        assert result.exit_code == 0
        assert "Tech Nonprofit Foundation" in result.output
        assert "Board Advisor" in result.output
        assert "advisory" in result.output
        assert "2023" in result.output
        assert "Technology strategy" in result.output

    def test_show_board_role_partial_match(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should find board role by partial organization match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Unique Startup Accelerator"
    role: "Technical Advisory Board Member"
    type: "advisory"
    start_date: "2021-06"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "board-role", "Unique"])

        assert result.exit_code == 0
        assert "Unique Startup Accelerator" in result.output

    def test_show_board_role_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when board role not found."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    start_date: "2023-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "board-role", "nonexistent"])

        assert result.exit_code == 4  # NOT_FOUND
        assert "not found" in result.output.lower()

    def test_show_board_role_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON with all board role fields."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Nonprofit Foundation"
    role: "Board Advisor"
    type: "advisory"
    start_date: "2023-01"
    focus: "Technology strategy"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "show", "board-role", "Tech Nonprofit"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["command"] == "show board-role"
        role = data["data"]["board_role"]
        assert role["organization"] == "Tech Nonprofit Foundation"
        assert role["role"] == "Board Advisor"
        assert role["type"] == "advisory"
        assert role["focus"] == "Technology strategy"

    def test_show_board_role_multiple_matches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when multiple board roles match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Tech Foundation One"
    role: "Advisor"
    start_date: "2023-01"
  - organization: "Tech Foundation Two"
    role: "Advisor"
    start_date: "2022-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "board-role", "Tech"])

        assert result.exit_code == 1
        assert "Multiple board roles match" in result.output

    def test_show_board_role_director_type(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show director type board role."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Public Company Inc"
    role: "Independent Board Director"
    type: "director"
    start_date: "2020-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "board-role", "Public Company"])

        assert result.exit_code == 0
        assert "director" in result.output
        assert "Independent Board Director" in result.output

    def test_show_board_role_current_status(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show Current status for active board role."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Current Org"
    role: "Active Advisor"
    start_date: "2023-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "board-role", "Current Org"])

        assert result.exit_code == 0
        assert "Current" in result.output or "Present" in result.output

    def test_show_board_role_past_status(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show Past status for ended board role."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
board_roles:
  - organization: "Past Org"
    role: "Former Advisor"
    start_date: "2020-01"
    end_date: "2022-12"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "board-role", "Past Org"])

        assert result.exit_code == 0
        assert "2020" in result.output
        assert "2022" in result.output
