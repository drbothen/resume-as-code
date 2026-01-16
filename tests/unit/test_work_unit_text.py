"""Tests for work_unit_text field extraction utilities."""

from __future__ import annotations

from resume_as_code.utils.work_unit_text import (
    extract_experience_text,
    extract_skills_text,
    extract_title_text,
)


class TestExtractTitleText:
    """Tests for extract_title_text function."""

    def test_extract_title_text(self) -> None:
        """Extract title from work unit."""
        wu = {"title": "Led platform migration"}
        assert extract_title_text(wu) == "Led platform migration"

    def test_extract_title_text_missing(self) -> None:
        """Handle missing title gracefully."""
        wu = {"problem": {"statement": "Some problem"}}
        assert extract_title_text(wu) == ""

    def test_extract_title_text_none(self) -> None:
        """Handle None title gracefully."""
        wu = {"title": None}
        assert extract_title_text(wu) == ""

    def test_extract_title_text_empty(self) -> None:
        """Handle empty string title."""
        wu = {"title": ""}
        assert extract_title_text(wu) == ""


class TestExtractSkillsText:
    """Tests for extract_skills_text function."""

    def test_extract_skills_text_tags_and_skills(self) -> None:
        """Extract both tags and skills_demonstrated."""
        wu = {
            "tags": ["python", "aws"],
            "skills_demonstrated": [
                {"name": "Docker"},
                {"name": "Kubernetes"},
            ],
        }
        result = extract_skills_text(wu)
        assert "python" in result
        assert "aws" in result
        assert "Docker" in result
        assert "Kubernetes" in result

    def test_extract_skills_text_string_skills(self) -> None:
        """Handle string-format skills."""
        wu = {
            "tags": ["python"],
            "skills_demonstrated": ["Docker", "K8s"],
        }
        result = extract_skills_text(wu)
        assert "python" in result
        assert "Docker" in result
        assert "K8s" in result

    def test_extract_skills_text_empty(self) -> None:
        """Handle missing tags and skills."""
        wu = {"title": "Some title"}
        assert extract_skills_text(wu) == ""

    def test_extract_skills_text_only_tags(self) -> None:
        """Extract tags when no skills_demonstrated."""
        wu = {"tags": ["python", "aws", "docker"]}
        result = extract_skills_text(wu)
        assert "python" in result
        assert "aws" in result
        assert "docker" in result

    def test_extract_skills_text_only_skills(self) -> None:
        """Extract skills_demonstrated when no tags."""
        wu = {
            "skills_demonstrated": [
                {"name": "Python"},
                {"name": "AWS"},
            ],
        }
        result = extract_skills_text(wu)
        assert "Python" in result
        assert "AWS" in result


class TestExtractExperienceText:
    """Tests for extract_experience_text function."""

    def test_extract_experience_text(self) -> None:
        """Extract problem, actions, and outcome."""
        wu = {
            "problem": {
                "statement": "Legacy system was slow",
                "context": "High traffic website",
            },
            "actions": ["Profiled code", "Optimized queries"],
            "outcome": {
                "result": "50% faster response times",
                "quantified_impact": "Reduced p99 latency from 2s to 1s",
            },
        }
        result = extract_experience_text(wu)
        assert "Legacy system was slow" in result
        assert "High traffic website" in result
        assert "Profiled code" in result
        assert "Optimized queries" in result
        assert "50% faster response times" in result
        assert "Reduced p99 latency" in result

    def test_extract_experience_text_excludes_title_and_skills(self) -> None:
        """Experience text should not include title or skills."""
        wu = {
            "title": "Senior Engineer",
            "tags": ["python"],
            "skills_demonstrated": [{"name": "Docker"}],
            "problem": {"statement": "Problem here"},
            "actions": ["Action here"],
            "outcome": {"result": "Result here"},
        }
        result = extract_experience_text(wu)
        assert "Senior Engineer" not in result
        assert "python" not in result
        assert "Docker" not in result
        assert "Problem here" in result

    def test_extract_experience_text_string_formats(self) -> None:
        """Handle string-format problem, actions, outcome."""
        wu = {
            "problem": "Simple problem statement",
            "actions": "Single action string",
            "outcome": "Simple outcome",
        }
        result = extract_experience_text(wu)
        assert "Simple problem statement" in result
        assert "Single action string" in result
        assert "Simple outcome" in result

    def test_extract_experience_text_empty(self) -> None:
        """Handle missing experience fields."""
        wu = {"title": "Some title", "tags": ["python"]}
        assert extract_experience_text(wu) == ""

    def test_extract_experience_text_partial(self) -> None:
        """Handle partial experience fields."""
        wu = {
            "problem": {"statement": "Only problem"},
            "actions": ["One action"],
        }
        result = extract_experience_text(wu)
        assert "Only problem" in result
        assert "One action" in result
