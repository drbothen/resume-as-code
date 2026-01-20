"""Unit tests for list command filtering logic."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_work_units() -> list[dict]:
    """Sample Work Units for testing."""
    return [
        {
            "id": "wu-2026-01-10-project-a",
            "title": "Project A",
            "confidence": "high",
            "tags": ["python", "aws"],
            "time_started": "2026-01-10",
        },
        {
            "id": "wu-2025-06-15-project-b",
            "title": "Project B",
            "confidence": "medium",
            "tags": ["java", "gcp"],
            "time_started": "2025-06-15",
        },
        {
            "id": "wu-2024-03-20-project-c",
            "title": "Project C",
            "confidence": "low",
            "tags": ["python", "azure"],
            "time_started": "2024-03-20",
        },
    ]


class TestFilterByTag:
    """Tests for tag filtering."""

    def test_filter_by_tag_returns_matching(self, sample_work_units: list[dict]) -> None:
        """Should filter by tag (AC #3)."""
        from resume_as_code.commands.list_cmd import _apply_filter

        result = _apply_filter(sample_work_units, "tag:python")
        assert len(result) == 2
        assert all("python" in wu["tags"] for wu in result)

    def test_filter_by_tag_case_insensitive(self, sample_work_units: list[dict]) -> None:
        """Should be case-insensitive for tags."""
        from resume_as_code.commands.list_cmd import _apply_filter

        result = _apply_filter(sample_work_units, "tag:PYTHON")
        assert len(result) == 2

    def test_filter_by_nonexistent_tag_returns_empty(self, sample_work_units: list[dict]) -> None:
        """Should return empty for nonexistent tag."""
        from resume_as_code.commands.list_cmd import _apply_filter

        result = _apply_filter(sample_work_units, "tag:rust")
        assert len(result) == 0


class TestFilterByConfidence:
    """Tests for confidence filtering."""

    def test_filter_by_confidence_high(self, sample_work_units: list[dict]) -> None:
        """Should filter by confidence level (AC #4)."""
        from resume_as_code.commands.list_cmd import _apply_filter

        result = _apply_filter(sample_work_units, "confidence:high")
        assert len(result) == 1
        assert result[0]["confidence"] == "high"

    def test_filter_by_confidence_case_insensitive(self, sample_work_units: list[dict]) -> None:
        """Should be case-insensitive for confidence."""
        from resume_as_code.commands.list_cmd import _apply_filter

        result = _apply_filter(sample_work_units, "confidence:HIGH")
        assert len(result) == 1

    def test_filter_by_confidence_medium(self, sample_work_units: list[dict]) -> None:
        """Should filter by medium confidence."""
        from resume_as_code.commands.list_cmd import _apply_filter

        result = _apply_filter(sample_work_units, "confidence:medium")
        assert len(result) == 1
        assert result[0]["confidence"] == "medium"


class TestFreeTextSearch:
    """Tests for free text search."""

    def test_search_in_id(self, sample_work_units: list[dict]) -> None:
        """Should search in ID (AC #5)."""
        from resume_as_code.commands.list_cmd import _apply_filter

        result = _apply_filter(sample_work_units, "2026")
        assert len(result) == 1
        assert "2026" in result[0]["id"]

    def test_search_in_title(self, sample_work_units: list[dict]) -> None:
        """Should search in title."""
        from resume_as_code.commands.list_cmd import _apply_filter

        result = _apply_filter(sample_work_units, "Project B")
        assert len(result) == 1
        assert result[0]["title"] == "Project B"

    def test_search_case_insensitive(self, sample_work_units: list[dict]) -> None:
        """Should be case-insensitive for free text."""
        from resume_as_code.commands.list_cmd import _apply_filter

        result = _apply_filter(sample_work_units, "project b")
        assert len(result) == 1

    def test_search_partial_match(self, sample_work_units: list[dict]) -> None:
        """Should match partial text."""
        from resume_as_code.commands.list_cmd import _apply_filter

        result = _apply_filter(sample_work_units, "Project")
        assert len(result) == 3  # All three match "Project"


class TestMultipleFilters:
    """Tests for multiple filters with AND logic (Task 4.5)."""

    def test_multiple_filters_tag_and_confidence(self, sample_work_units: list[dict]) -> None:
        """Should apply multiple filters with AND logic."""
        from resume_as_code.commands.list_cmd import _apply_filter

        # First filter: tag:python (matches Project A and C)
        result = _apply_filter(sample_work_units, "tag:python")
        assert len(result) == 2

        # Second filter: confidence:high (from the 2 results, only Project A matches)
        result = _apply_filter(result, "confidence:high")
        assert len(result) == 1
        assert result[0]["title"] == "Project A"

    def test_multiple_filters_reduces_results(self, sample_work_units: list[dict]) -> None:
        """Each additional filter should narrow results."""
        from resume_as_code.commands.list_cmd import _apply_filter

        # Start with all
        result = sample_work_units.copy()
        assert len(result) == 3

        # Filter by tag:python
        result = _apply_filter(result, "tag:python")
        assert len(result) == 2

        # Further filter by 2024 (only Project C has 2024 in ID)
        result = _apply_filter(result, "2024")
        assert len(result) == 1
        assert result[0]["title"] == "Project C"

    def test_multiple_filters_no_match(self, sample_work_units: list[dict]) -> None:
        """Conflicting filters should return empty."""
        from resume_as_code.commands.list_cmd import _apply_filter

        # Filter by java tag
        result = _apply_filter(sample_work_units, "tag:java")
        assert len(result) == 1  # Only Project B

        # Further filter by python tag (no Java project has python)
        result = _apply_filter(result, "tag:python")
        assert len(result) == 0


class TestMissingFieldEdgeCases:
    """Tests for Work Units with missing optional fields."""

    def test_filter_confidence_when_wu_missing_confidence(self) -> None:
        """Should handle Work Units without confidence field."""
        from resume_as_code.commands.list_cmd import _apply_filter

        work_units = [
            {"id": "wu-2026-01-01-a", "title": "Has Confidence", "confidence": "high", "tags": []},
            {"id": "wu-2026-01-02-b", "title": "No Confidence", "tags": []},  # Missing confidence
        ]
        result = _apply_filter(work_units, "confidence:high")
        assert len(result) == 1
        assert result[0]["title"] == "Has Confidence"

    def test_filter_tag_when_wu_missing_tags(self) -> None:
        """Should handle Work Units without tags field."""
        from resume_as_code.commands.list_cmd import _apply_filter

        work_units = [
            {"id": "wu-2026-01-01-a", "title": "Has Tags", "tags": ["python"]},
            {"id": "wu-2026-01-02-b", "title": "No Tags"},  # Missing tags field entirely
        ]
        result = _apply_filter(work_units, "tag:python")
        assert len(result) == 1
        assert result[0]["title"] == "Has Tags"

    def test_sort_confidence_when_wu_missing_confidence(self) -> None:
        """Should sort Work Units without confidence field to end."""
        from resume_as_code.commands.list_cmd import _apply_sort

        work_units = [
            {"id": "wu-2026-01-01-a", "title": "No Confidence"},  # Missing
            {"id": "wu-2026-01-02-b", "title": "Has High", "confidence": "high"},
            {"id": "wu-2026-01-03-c", "title": "Has Low", "confidence": "low"},
        ]
        result = _apply_sort(work_units, "confidence", reverse=False)
        assert result[0]["title"] == "Has High"
        assert result[-1]["title"] == "No Confidence"


class TestSorting:
    """Tests for sorting."""

    def test_sort_by_date_newest_first_default(self, sample_work_units: list[dict]) -> None:
        """Should sort by date, newest first by default (AC #7)."""
        from resume_as_code.commands.list_cmd import _apply_sort

        result = _apply_sort(sample_work_units, "date", reverse=False)
        assert result[0]["id"].startswith("wu-2026")
        assert result[-1]["id"].startswith("wu-2024")

    def test_sort_by_date_oldest_first_with_reverse(self, sample_work_units: list[dict]) -> None:
        """Should sort by date oldest first when reversed."""
        from resume_as_code.commands.list_cmd import _apply_sort

        result = _apply_sort(sample_work_units, "date", reverse=True)
        assert result[0]["id"].startswith("wu-2024")
        assert result[-1]["id"].startswith("wu-2026")

    def test_sort_by_title_alphabetical(self, sample_work_units: list[dict]) -> None:
        """Should sort by title alphabetically."""
        from resume_as_code.commands.list_cmd import _apply_sort

        result = _apply_sort(sample_work_units, "title", reverse=False)
        assert result[0]["title"] == "Project A"
        assert result[-1]["title"] == "Project C"

    def test_sort_by_confidence_high_first(self, sample_work_units: list[dict]) -> None:
        """Should sort by confidence (high first)."""
        from resume_as_code.commands.list_cmd import _apply_sort

        result = _apply_sort(sample_work_units, "confidence", reverse=False)
        assert result[0]["confidence"] == "high"
        assert result[-1]["confidence"] == "low"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_truncate_short_text(self) -> None:
        """Should return text unchanged if under max length."""
        from resume_as_code.commands.list_cmd import _truncate

        result = _truncate("short", 10)
        assert result == "short"

    def test_truncate_long_text(self) -> None:
        """Should truncate with ellipsis if over max length."""
        from resume_as_code.commands.list_cmd import _truncate

        result = _truncate("this is a very long text", 10)
        assert result == "this is..."
        assert len(result) == 10

    def test_extract_date_from_id(self) -> None:
        """Should extract date from Work Unit ID."""
        from resume_as_code.commands.list_cmd import _extract_date

        wu = {"id": "wu-2026-01-10-test"}
        result = _extract_date(wu)
        assert result == "2026-01-10"

    def test_extract_date_from_time_started(self) -> None:
        """Should prefer time_started over ID."""
        from resume_as_code.commands.list_cmd import _extract_date

        wu = {"id": "wu-2026-01-10-test", "time_started": "2025-06-15"}
        result = _extract_date(wu)
        assert result == "2025-06-15"

    def test_format_tags_empty(self) -> None:
        """Should return dash for empty tags."""
        from resume_as_code.commands.list_cmd import _format_tags

        result = _format_tags([])
        assert result == "-"

    def test_format_tags_few(self) -> None:
        """Should join tags with comma."""
        from resume_as_code.commands.list_cmd import _format_tags

        result = _format_tags(["python", "aws"])
        assert result == "python, aws"

    def test_format_tags_many_truncated(self) -> None:
        """Should truncate to first 3 with count."""
        from resume_as_code.commands.list_cmd import _format_tags

        result = _format_tags(["python", "aws", "docker", "k8s", "terraform"])
        assert result == "python, aws, docker +2"


@pytest.fixture
def sample_work_units_with_archetype() -> list[dict]:
    """Sample Work Units with archetype field for testing."""
    return [
        {
            "id": "wu-2026-01-10-incident-a",
            "title": "Resolved P1 outage",
            "archetype": "incident",
            "confidence": "high",
            "tags": ["python", "aws"],
            "time_started": "2026-01-10",
        },
        {
            "id": "wu-2025-06-15-greenfield-b",
            "title": "Built analytics pipeline",
            "archetype": "greenfield",
            "confidence": "high",
            "tags": ["java", "gcp"],
            "time_started": "2025-06-15",
        },
        {
            "id": "wu-2024-03-20-incident-c",
            "title": "Fixed security breach",
            "archetype": "incident",
            "confidence": "medium",
            "tags": ["python", "azure"],
            "time_started": "2024-03-20",
        },
        {
            "id": "wu-2024-01-05-migration-d",
            "title": "Migrated to cloud",
            "archetype": "migration",
            "confidence": "high",
            "tags": ["aws", "terraform"],
            "time_started": "2024-01-05",
        },
    ]


class TestFilterByArchetype:
    """Tests for archetype filtering (Story 12.5)."""

    def test_filter_by_archetype_returns_matching(
        self, sample_work_units_with_archetype: list[dict]
    ) -> None:
        """Should filter work units by archetype (AC1)."""
        from resume_as_code.commands.list_cmd import _apply_filter

        result = _apply_filter(sample_work_units_with_archetype, "archetype:incident")
        assert len(result) == 2
        assert all(wu["archetype"] == "incident" for wu in result)

    def test_filter_by_archetype_case_insensitive(
        self, sample_work_units_with_archetype: list[dict]
    ) -> None:
        """Should match archetypes case-insensitively (AC5)."""
        from resume_as_code.commands.list_cmd import _apply_filter

        result_lower = _apply_filter(sample_work_units_with_archetype, "archetype:incident")
        result_upper = _apply_filter(sample_work_units_with_archetype, "archetype:INCIDENT")
        result_mixed = _apply_filter(sample_work_units_with_archetype, "archetype:Incident")
        assert len(result_lower) == len(result_upper) == len(result_mixed) == 2

    def test_filter_by_archetype_greenfield(
        self, sample_work_units_with_archetype: list[dict]
    ) -> None:
        """Should filter by greenfield archetype."""
        from resume_as_code.commands.list_cmd import _apply_filter

        result = _apply_filter(sample_work_units_with_archetype, "archetype:greenfield")
        assert len(result) == 1
        assert result[0]["archetype"] == "greenfield"

    def test_filter_by_archetype_nonexistent_returns_empty(
        self, sample_work_units_with_archetype: list[dict]
    ) -> None:
        """Should return empty for nonexistent archetype."""
        from resume_as_code.commands.list_cmd import _apply_filter

        result = _apply_filter(sample_work_units_with_archetype, "archetype:nonexistent")
        assert len(result) == 0

    def test_filter_archetype_when_wu_missing_archetype(self) -> None:
        """Should handle Work Units without archetype field."""
        from resume_as_code.commands.list_cmd import _apply_filter

        work_units = [
            {
                "id": "wu-2026-01-01-a",
                "title": "Has Archetype",
                "archetype": "incident",
                "tags": [],
            },
            {
                "id": "wu-2026-01-02-b",
                "title": "No Archetype",
                "tags": [],
            },  # Missing archetype
        ]
        result = _apply_filter(work_units, "archetype:incident")
        assert len(result) == 1
        assert result[0]["title"] == "Has Archetype"

    def test_filter_archetype_combined_with_tag(
        self, sample_work_units_with_archetype: list[dict]
    ) -> None:
        """Should combine archetype filter with tag filter (AND logic)."""
        from resume_as_code.commands.list_cmd import _apply_filter

        # Filter by archetype:incident (2 results)
        result = _apply_filter(sample_work_units_with_archetype, "archetype:incident")
        assert len(result) == 2

        # Further filter by tag:aws (only 1 incident has aws)
        result = _apply_filter(result, "tag:aws")
        assert len(result) == 1
        assert result[0]["title"] == "Resolved P1 outage"


class TestArchetypeStats:
    """Tests for archetype statistics (Story 12.5 AC3)."""

    def test_stats_counts_archetypes(self, sample_work_units_with_archetype: list[dict]) -> None:
        """Should count work units per archetype correctly."""
        from collections import Counter

        counts = Counter(wu["archetype"] for wu in sample_work_units_with_archetype)

        # Verify expected counts
        assert counts["incident"] == 2
        assert counts["greenfield"] == 1
        assert counts["migration"] == 1
        assert sum(counts.values()) == len(sample_work_units_with_archetype)

    def test_json_output_includes_archetype_field(
        self, sample_work_units_with_archetype: list[dict]
    ) -> None:
        """JSON output should include archetype field (AC4)."""
        import json
        from unittest.mock import patch

        from resume_as_code.commands.list_cmd import _output_json

        captured_output: list[str] = []
        with patch("click.echo", lambda x: captured_output.append(x)):
            _output_json(sample_work_units_with_archetype)

        # Parse the JSON output and verify archetype field is present
        assert len(captured_output) == 1
        response = json.loads(captured_output[0])
        assert "data" in response
        assert "work_units" in response["data"]
        for wu in response["data"]["work_units"]:
            assert "archetype" in wu

    def test_json_output_with_stats_includes_archetype_stats(
        self, sample_work_units_with_archetype: list[dict]
    ) -> None:
        """JSON output with stats should include archetype_stats field."""
        import json
        from unittest.mock import patch

        from resume_as_code.commands.list_cmd import _output_json

        captured_output: list[str] = []
        with patch("click.echo", lambda x: captured_output.append(x)):
            _output_json(sample_work_units_with_archetype, show_stats=True)

        # Parse JSON output and verify archetype_stats is present
        assert len(captured_output) == 1
        response = json.loads(captured_output[0])
        assert "data" in response
        assert "archetype_stats" in response["data"]
        assert response["data"]["archetype_stats"]["incident"] == 2
        assert response["data"]["archetype_stats"]["greenfield"] == 1
        assert response["data"]["archetype_stats"]["migration"] == 1

    def test_output_archetype_stats_function_exists(self) -> None:
        """_output_archetype_stats function should exist and be callable."""
        from resume_as_code.commands.list_cmd import _output_archetype_stats

        assert callable(_output_archetype_stats)

    def test_archetype_stats_handles_missing_archetype(self) -> None:
        """Should handle work units without archetype field."""
        from collections import Counter

        work_units = [
            {"id": "wu-1", "title": "Has Archetype", "archetype": "incident"},
            {"id": "wu-2", "title": "No Archetype"},  # Missing archetype
        ]

        # Count with fallback to "unknown"
        counts = Counter(wu.get("archetype") or "unknown" for wu in work_units)
        assert counts["incident"] == 1
        assert counts["unknown"] == 1
