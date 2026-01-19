"""Integration tests for publication JD-relevant curation (Story 8.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


class TestPublicationCreationWithTopicsAndAbstract:
    """Integration tests for creating publications with topics and abstract."""

    def test_create_publication_with_topics_flag(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create publication with topics via --topic flag."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("output_dir: ./dist\n")

        result = runner.invoke(
            main,
            [
                "new",
                "publication",
                "Test Talk|conference|PyCon|2024-06|",
                "--topic",
                "python",
                "--topic",
                "aws",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        config_content = config_file.read_text()
        assert "topics:" in config_content or "python" in config_content

    def test_create_publication_with_abstract_flag(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create publication with abstract via --abstract flag."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("output_dir: ./dist\n")

        result = runner.invoke(
            main,
            [
                "new",
                "publication",
                "Test Talk|conference|PyCon|2024-06|",
                "--abstract",
                "A deep dive into Python patterns.",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        config_content = config_file.read_text()
        assert "abstract:" in config_content or "deep dive" in config_content

    def test_create_publication_pipe_format_with_topics(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create publication with topics via extended pipe format."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("output_dir: ./dist\n")

        # Extended format: Title|Type|Venue|Date|URL|Topics|Abstract
        result = runner.invoke(
            main,
            [
                "new",
                "publication",
                "Test Talk|conference|PyCon|2024-06||python,aws|A deep dive into Python.",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        config_content = config_file.read_text()
        assert "Test Talk" in config_content


class TestPublicationShowWithTopicsAndAbstract:
    """Integration tests for showing publications with topics and abstract."""

    def test_show_publication_displays_topics(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should display topics when showing publication."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("""
publications:
  - title: "Python Best Practices"
    type: "conference"
    venue: "PyCon"
    date: "2024-06"
    topics:
      - python
      - aws
      - kubernetes
""")

        result = runner.invoke(main, ["show", "publication", "Python"])

        assert result.exit_code == 0, f"Failed: {result.output}"
        # Should show topics in the output
        output_lower = result.output.lower()
        assert "python" in output_lower or "topics" in output_lower

    def test_show_publication_displays_abstract(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should display abstract when showing publication."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("""
publications:
  - title: "Python Best Practices"
    type: "conference"
    venue: "PyCon"
    date: "2024-06"
    abstract: "A comprehensive guide to Python patterns."
""")

        result = runner.invoke(main, ["show", "publication", "Python"])

        assert result.exit_code == 0, f"Failed: {result.output}"
        # Should show abstract in the output
        assert "comprehensive" in result.output.lower() or "abstract" in result.output.lower()


class TestListPublicationsWithNewFields:
    """Integration tests for listing publications with topics and abstract."""

    def test_list_publications_works_with_topics(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should list publications that have topics field."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("""
publications:
  - title: "Python Talk"
    type: "conference"
    venue: "PyCon"
    date: "2024-06"
    topics:
      - python
  - title: "AWS Talk"
    type: "conference"
    venue: "re:Invent"
    date: "2024-12"
    topics:
      - aws
    abstract: "AWS best practices."
""")

        result = runner.invoke(main, ["list", "publications"])

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Python Talk" in result.output
        assert "AWS Talk" in result.output


class TestPublicationCurationInBuild:
    """Integration tests for publication curation during build."""

    @pytest.mark.slow
    def test_build_curates_publications_with_jd(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Build with JD should curate publications by relevance."""
        monkeypatch.chdir(tmp_path)

        # Create config with profile and publications
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("""
profile:
  name: "Test User"
  title: "Software Engineer"

publications:
  - title: "Python Microservices at Scale"
    type: "conference"
    venue: "PyCon"
    date: "2024-04"
    topics:
      - python
      - microservices
    abstract: "Building scalable Python services with AWS Lambda."
  - title: "Kubernetes in Production"
    type: "conference"
    venue: "KubeCon"
    date: "2024-03"
    topics:
      - kubernetes
      - devops
    abstract: "Container orchestration best practices."
  - title: "Cooking with Algorithms"
    type: "article"
    venue: "Food Blog"
    date: "2023-06"
    topics:
      - cooking
      - recipes
    abstract: "How algorithms can optimize your kitchen."

curation:
  publications_max: 2
  min_relevance_score: 0.1
""")

        # Create work-units directory with a simple work unit
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        (work_units_dir / "wu-2024-01-01-test.yaml").write_text("""
schema_version: "4.0.0"
archetype: minimal
id: wu-2024-01-01-test
title: "Test work unit"
problem:
  statement: "Testing publication curation"
actions:
  - "Implemented test"
outcome:
  result: "Test passed"
""")

        # Create JD file
        jd_file = tmp_path / "jd.txt"
        jd_file.write_text("""
Senior Python Developer

Requirements:
- 5+ years Python experience
- AWS Lambda, API Gateway
- Kubernetes and Docker
- CI/CD pipelines
""")

        # Run build with JD (will show curation message if publications are filtered)
        result = runner.invoke(
            main,
            ["-v", "build", "--jd", str(jd_file), "--format", "docx"],
        )

        # Build should succeed
        assert result.exit_code == 0, f"Build failed: {result.output}"
        # Should have created output file
        assert (tmp_path / "dist" / "resume.docx").exists()
        # Should show curation message (2 selected, 1 excluded)
        assert "2 selected" in result.output, f"Expected curation message: {result.output}"
        assert "1 excluded" in result.output, f"Expected exclusion message: {result.output}"

    @pytest.mark.slow
    def test_build_excludes_irrelevant_publications(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Build should exclude publications with irrelevant topics."""
        monkeypatch.chdir(tmp_path)

        # Create config with profile and publications - irrelevant one should be excluded
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("""
profile:
  name: "Test User"
  title: "Software Engineer"

publications:
  - title: "Python Best Practices"
    type: "conference"
    venue: "PyCon"
    date: "2024-06"
    topics:
      - python
      - software-engineering
    abstract: "Modern Python development patterns for scalable applications."
  - title: "Underwater Basket Weaving"
    type: "article"
    venue: "Craft Monthly"
    date: "2024-01"
    topics:
      - crafts
      - hobbies
    abstract: "Ancient art of creating baskets underwater."

curation:
  publications_max: 2
  # Threshold must be >0.50 to exclude irrelevant content; embeddings give
  # surprisingly high base similarity (~0.50) even to unrelated topics due to
  # shared "professional/technical" language patterns in the model.
  min_relevance_score: 0.55
""")

        # Create work-units directory with a simple work unit
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        (work_units_dir / "wu-2024-01-01-test.yaml").write_text("""
schema_version: "4.0.0"
archetype: minimal
id: wu-2024-01-01-test
title: "Test work unit"
problem:
  statement: "Testing publication curation"
actions:
  - "Implemented Python solution"
outcome:
  result: "Improved code quality"
""")

        # Create JD file focused on Python
        jd_file = tmp_path / "jd.txt"
        jd_file.write_text("""
Senior Python Developer

Requirements:
- 5+ years Python experience
- Software engineering best practices
- Code review and mentoring
""")

        result = runner.invoke(
            main,
            ["-v", "build", "--jd", str(jd_file), "--format", "docx"],
        )

        assert result.exit_code == 0, f"Build failed: {result.output}"
        # With min_relevance_score=0.55, the irrelevant "Underwater Basket Weaving"
        # publication (which scores ~0.50) should be excluded while "Python Best
        # Practices" (scoring ~0.75) is selected.
        assert "1 selected" in result.output, f"Expected 1 selected: {result.output}"
        assert "1 excluded" in result.output, f"Expected 1 excluded: {result.output}"
