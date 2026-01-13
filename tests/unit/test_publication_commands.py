"""Tests for Publication Management Commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main
from resume_as_code.services.publication_service import PublicationService


class TestPublicationTitleMatching:
    """Tests for publication title matching in PublicationService."""

    def test_find_publications_by_title_exact_match(self, tmp_path: Path) -> None:
        """Should find publication by exact title match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Securing Industrial Control Systems"
    type: "conference"
    venue: "DEF CON 30"
    date: "2022-08"
  - title: "Zero Trust Architecture Guide"
    type: "article"
    venue: "IEEE Security"
    date: "2023-03"
"""
        )
        service = PublicationService(config_path=config_path)
        matches = service.find_publications_by_title("Zero Trust Architecture Guide")

        assert len(matches) == 1
        assert matches[0].title == "Zero Trust Architecture Guide"

    def test_find_publications_by_title_partial_match(self, tmp_path: Path) -> None:
        """Should find publication by partial title match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Securing Industrial Control Systems at Scale"
    type: "conference"
    venue: "DEF CON"
    date: "2022-08"
  - title: "Securing Cloud Infrastructure"
    type: "article"
    venue: "Tech Blog"
    date: "2023-03"
"""
        )
        service = PublicationService(config_path=config_path)
        matches = service.find_publications_by_title("Securing")

        assert len(matches) == 2

    def test_find_publications_by_title_case_insensitive(self, tmp_path: Path) -> None:
        """Should match case-insensitively."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Zero Trust Architecture"
    type: "whitepaper"
    venue: "Company Blog"
    date: "2023-06"
"""
        )
        service = PublicationService(config_path=config_path)
        matches = service.find_publications_by_title("zero trust")

        assert len(matches) == 1
        assert matches[0].title == "Zero Trust Architecture"

    def test_find_publications_by_title_no_match(self, tmp_path: Path) -> None:
        """Should return empty list when no match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Cloud Security Best Practices"
    type: "article"
    venue: "Blog"
    date: "2023-01"
"""
        )
        service = PublicationService(config_path=config_path)
        matches = service.find_publications_by_title("nonexistent")

        assert len(matches) == 0

    def test_find_publications_empty_config(self, tmp_path: Path) -> None:
        """Should handle empty publications list."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\n")
        service = PublicationService(config_path=config_path)
        matches = service.find_publications_by_title("Test")

        assert len(matches) == 0


class TestRemovePublicationService:
    """Tests for remove_publication in PublicationService."""

    def test_remove_publication_success(self, tmp_path: Path) -> None:
        """Should remove publication successfully."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Talk at Conference"
    type: "conference"
    venue: "DEF CON"
    date: "2022-08"
  - title: "Security Article"
    type: "article"
    venue: "Blog"
    date: "2023-01"
"""
        )
        service = PublicationService(config_path=config_path)
        result = service.remove_publication("Security Article")

        assert result is True

        # Verify removal
        pubs = service.load_publications()
        assert len(pubs) == 1
        assert pubs[0].title == "Talk at Conference"

    def test_remove_publication_not_found(self, tmp_path: Path) -> None:
        """Should return False when publication not found."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Existing Publication"
    type: "article"
    venue: "Blog"
    date: "2023-01"
"""
        )
        service = PublicationService(config_path=config_path)
        result = service.remove_publication("nonexistent")

        assert result is False

    def test_remove_publication_no_config_file(self, tmp_path: Path) -> None:
        """Should return False when config file doesn't exist."""
        config_path = tmp_path / ".resume.yaml"
        service = PublicationService(config_path=config_path)
        result = service.remove_publication("Test")

        assert result is False

    def test_remove_publication_partial_match(self, tmp_path: Path) -> None:
        """Should remove by partial title match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Securing Industrial Control Systems at Scale"
    type: "conference"
    venue: "DEF CON"
    date: "2022-08"
"""
        )
        service = PublicationService(config_path=config_path)
        result = service.remove_publication("Industrial Control")

        assert result is True

        # Verify removal
        pubs = service.load_publications()
        assert len(pubs) == 0


class TestNewPublicationCommand:
    """Tests for `resume new publication` command."""

    def test_new_publication_non_interactive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create publication in non-interactive mode."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "publication",
                "--title",
                "My Conference Talk",
                "--type",
                "conference",
                "--venue",
                "DEF CON 30",
                "--date",
                "2022-08",
            ],
        )

        assert result.exit_code == 0
        assert "Publication created" in result.output or "My Conference Talk" in result.output

        # Verify file was created
        config_path = tmp_path / ".resume.yaml"
        assert config_path.exists()

    def test_new_publication_pipe_separated(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create publication from pipe-separated format."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "publication",
                "Security Talk|conference|DEF CON|2022-08|https://example.com/talk",
            ],
        )

        assert result.exit_code == 0
        assert "Security Talk" in result.output

    def test_new_publication_pipe_separated_no_url(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create publication from pipe-separated format without URL."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "publication",
                "Security Article|article|Tech Blog|2023-06",
            ],
        )

        assert result.exit_code == 0
        assert "Security Article" in result.output

    def test_new_publication_json_output(
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
                "publication",
                "--title",
                "Test Publication",
                "--type",
                "article",
                "--venue",
                "Test Blog",
                "--date",
                "2024-01",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["publication_created"] is True

    def test_new_publication_duplicate_detection(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should detect duplicate publications."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Existing Talk"
    type: "conference"
    venue: "DEF CON"
    date: "2022-08"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "publication",
                "--title",
                "Existing Talk",
                "--type",
                "conference",
                "--venue",
                "DEF CON",
                "--date",
                "2022-08",
            ],
        )

        # Should indicate already exists (not an error, just info)
        assert "already exists" in result.output

    def test_new_publication_empty_title_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should reject empty publication title."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "publication",
                "--title",
                "",
                "--type",
                "conference",
                "--venue",
                "DEF CON",
                "--date",
                "2022-08",
            ],
        )

        assert result.exit_code != 0
        assert "cannot be empty" in result.output.lower()

    def test_new_publication_invalid_type_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should reject invalid publication type."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "publication",
                "--title",
                "Test Talk",
                "--type",
                "invalid_type",
                "--venue",
                "Conference",
                "--date",
                "2022-08",
            ],
        )

        assert result.exit_code != 0

    def test_new_publication_invalid_date_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should reject invalid date format."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main,
            [
                "new",
                "publication",
                "--title",
                "Test Talk",
                "--type",
                "conference",
                "--venue",
                "DEF CON",
                "--date",
                "invalid-date",
            ],
        )

        assert result.exit_code != 0
        assert "YYYY-MM" in result.output

    def test_new_publication_all_types(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should accept all valid publication types."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        valid_types = ["conference", "article", "whitepaper", "book", "podcast", "webinar"]

        for i, pub_type in enumerate(valid_types):
            result = runner.invoke(
                main,
                [
                    "new",
                    "publication",
                    "--title",
                    f"Test {pub_type} {i}",
                    "--type",
                    pub_type,
                    "--venue",
                    "Test Venue",
                    "--date",
                    f"2024-0{i + 1}",
                ],
            )
            assert result.exit_code == 0, f"Failed for type: {pub_type}"


class TestListPublicationsCommand:
    """Tests for `resume list publications` command."""

    def test_list_publications_table_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should display publications in table format."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Security Talk at DEF CON"
    type: "conference"
    venue: "DEF CON 30"
    date: "2022-08"
  - title: "Zero Trust Guide"
    type: "whitepaper"
    venue: "Company Blog"
    date: "2023-03"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "publications"])

        assert result.exit_code == 0
        assert "Security Talk at DEF CON" in result.output
        assert "Zero Trust Guide" in result.output
        assert "Publications" in result.output

    def test_list_publications_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should handle empty publications list."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["list", "publications"])

        assert result.exit_code == 0
        assert "No publications found" in result.output

    def test_list_publications_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON with publication data."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Test Talk"
    type: "conference"
    venue: "Conference"
    date: "2022-08"
    url: "https://example.com/talk"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "list", "publications"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert len(data["data"]["publications"]) == 1
        assert data["data"]["publications"][0]["type"] == "conference"
        assert data["data"]["publications"][0]["url"] == "https://example.com/talk"

    def test_list_publications_json_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output empty JSON list when no publications."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "list", "publications"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["count"] == 0
        assert data["data"]["publications"] == []

    def test_list_publications_returns_all(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should list all publications from config."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Old Talk"
    type: "conference"
    venue: "Old Conf"
    date: "2020-01"
  - title: "Recent Talk"
    type: "conference"
    venue: "New Conf"
    date: "2024-06"
  - title: "Middle Talk"
    type: "conference"
    venue: "Mid Conf"
    date: "2022-06"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "list", "publications"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        pubs = data["data"]["publications"]
        # Should return all 3 publications
        assert len(pubs) == 3
        titles = [p["title"] for p in pubs]
        assert "Old Talk" in titles
        assert "Recent Talk" in titles
        assert "Middle Talk" in titles


class TestShowPublicationCommand:
    """Tests for `resume show publication` command."""

    def test_show_publication_by_title(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should display publication details by title."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Securing Industrial Control Systems at Scale"
    type: "conference"
    venue: "DEF CON 30"
    date: "2022-08"
    url: "https://example.com/talk"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "publication", "Securing Industrial"])

        assert result.exit_code == 0
        assert "Securing Industrial Control Systems at Scale" in result.output
        assert "DEF CON 30" in result.output
        assert "2022-08" in result.output
        assert "conference" in result.output.lower()

    def test_show_publication_partial_match(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should find publication by partial title match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Zero Trust Architecture Implementation Guide"
    type: "whitepaper"
    venue: "Company Technical Blog"
    date: "2023-03"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "publication", "Zero Trust"])

        assert result.exit_code == 0
        assert "Zero Trust Architecture" in result.output
        assert "Company Technical Blog" in result.output

    def test_show_publication_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when publication not found."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Existing Publication"
    type: "article"
    venue: "Blog"
    date: "2023-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "publication", "nonexistent"])

        assert result.exit_code == 4  # NOT_FOUND
        assert "not found" in result.output.lower()

    def test_show_publication_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON with all publication fields."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Cloud Security Best Practices"
    type: "article"
    venue: "IEEE Security & Privacy"
    date: "2021-06"
    url: "https://example.com/article"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["--json", "show", "publication", "Cloud Security"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["command"] == "show publication"
        assert data["data"]["title"] == "Cloud Security Best Practices"
        assert data["data"]["type"] == "article"
        assert data["data"]["venue"] == "IEEE Security & Privacy"
        assert data["data"]["date"] == "2021-06"
        assert "example.com/article" in data["data"]["url"]

    def test_show_publication_multiple_matches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show first match with warning when multiple match."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Security Talk Part 1"
    type: "conference"
    venue: "DEF CON"
    date: "2022-08"
  - title: "Security Talk Part 2"
    type: "conference"
    venue: "Black Hat"
    date: "2023-08"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["show", "publication", "Security Talk"])

        assert result.exit_code == 0
        assert "Multiple matches" in result.output
        # Should show first match
        assert "Part 1" in result.output or "Part 2" in result.output


class TestRemovePublicationCommand:
    """Tests for `resume remove publication` command."""

    def test_remove_publication_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should remove publication with --yes flag."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Talk to Remove"
    type: "conference"
    venue: "Conference"
    date: "2022-08"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "publication", "Talk to Remove", "--yes"])

        assert result.exit_code == 0
        assert "Removed publication" in result.output

    def test_remove_publication_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should error when publication not found."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Existing Publication"
    type: "article"
    venue: "Blog"
    date: "2023-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "publication", "nonexistent", "--yes"])

        assert result.exit_code == 4  # NOT_FOUND
        assert "No publication found" in result.output

    def test_remove_publication_multiple_matches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show warning when multiple publications match and remove first."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Security Talk One"
    type: "conference"
    venue: "DEF CON"
    date: "2022-08"
  - title: "Security Talk Two"
    type: "conference"
    venue: "Black Hat"
    date: "2023-08"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(main, ["remove", "publication", "Security Talk", "--yes"])

        assert result.exit_code == 0
        assert "Multiple publications match" in result.output
        # Should remove first match
        assert "Removed publication" in result.output

    def test_remove_publication_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON on successful removal."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Publication to Delete"
    type: "article"
    venue: "Blog"
    date: "2023-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            main, ["--json", "remove", "publication", "Publication to Delete", "--yes"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["publication_removed"] is True
        assert data["data"]["title"] == "Publication to Delete"

    def test_remove_publication_interactive_confirm(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should prompt for confirmation in interactive mode."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Interactive Test"
    type: "conference"
    venue: "Conf"
    date: "2022-08"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Simulate user typing 'y' for confirmation
        result = runner.invoke(main, ["remove", "publication", "Interactive Test"], input="y\n")

        assert result.exit_code == 0
        assert "Removed publication" in result.output

    def test_remove_publication_interactive_cancel(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should cancel when user declines confirmation."""
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text(
            """
publications:
  - title: "Keep This Publication"
    type: "article"
    venue: "Blog"
    date: "2023-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()

        # Simulate user typing 'n' to decline
        result = runner.invoke(main, ["remove", "publication", "Keep This"], input="n\n")

        assert result.exit_code == 0
        assert "cancelled" in result.output.lower()

        # Verify publication was not removed
        service = PublicationService(config_path=config_path)
        pubs = service.load_publications()
        assert len(pubs) == 1
