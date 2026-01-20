"""Unit tests for PositionService."""

from __future__ import annotations

from pathlib import Path

from resume_as_code.models.position import Position
from resume_as_code.services.position_service import PositionService


class TestPositionServiceLoad:
    """Tests for loading positions from YAML."""

    def test_load_positions_from_yaml(self, tmp_path: Path) -> None:
        """Should load positions from YAML file."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-techcorp-senior:
    employer: "TechCorp Industries"
    title: "Senior Platform Engineer"
    location: "Austin, TX"
    start_date: "2022-01"
    employment_type: "full-time"
""")
        service = PositionService(positions_file)
        positions = service.load_positions()

        assert "pos-techcorp-senior" in positions
        pos = positions["pos-techcorp-senior"]
        assert pos.id == "pos-techcorp-senior"
        assert pos.employer == "TechCorp Industries"
        assert pos.title == "Senior Platform Engineer"
        assert pos.location == "Austin, TX"
        assert pos.employment_type == "full-time"
        assert pos.is_current is True

    def test_load_positions_multiple(self, tmp_path: Path) -> None:
        """Should load multiple positions from YAML."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-techcorp-senior:
    employer: "TechCorp Industries"
    title: "Senior Engineer"
    start_date: "2022-01"
  pos-techcorp-engineer:
    employer: "TechCorp Industries"
    title: "Engineer"
    start_date: "2020-06"
    end_date: "2021-12"
  pos-acme:
    employer: "Acme Corp"
    title: "Consultant"
    start_date: "2018-01"
    end_date: "2020-05"
""")
        service = PositionService(positions_file)
        positions = service.load_positions()

        assert len(positions) == 3
        assert "pos-techcorp-senior" in positions
        assert "pos-techcorp-engineer" in positions
        assert "pos-acme" in positions

    def test_load_positions_empty_file(self, tmp_path: Path) -> None:
        """Should return empty dict for empty file."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("")

        service = PositionService(positions_file)
        positions = service.load_positions()

        assert positions == {}

    def test_load_positions_file_not_exists(self, tmp_path: Path) -> None:
        """Should return empty dict when file doesn't exist."""
        positions_file = tmp_path / "nonexistent.yaml"

        service = PositionService(positions_file)
        positions = service.load_positions()

        assert positions == {}

    def test_load_positions_cached(self, tmp_path: Path) -> None:
        """Should cache loaded positions."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-test:
    employer: "Test Corp"
    title: "Engineer"
    start_date: "2022-01"
""")
        service = PositionService(positions_file)

        # First load
        positions1 = service.load_positions()
        # Modify file
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-different:
    employer: "Different Corp"
    title: "Developer"
    start_date: "2023-01"
""")
        # Second load should return cached
        positions2 = service.load_positions()

        assert positions1 is positions2
        assert "pos-test" in positions2


class TestPositionServiceGet:
    """Tests for getting individual positions."""

    def test_get_position_exists(self, tmp_path: Path) -> None:
        """Should return position by ID."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-test:
    employer: "Test Corp"
    title: "Engineer"
    start_date: "2022-01"
""")
        service = PositionService(positions_file)
        pos = service.get_position("pos-test")

        assert pos is not None
        assert pos.id == "pos-test"
        assert pos.employer == "Test Corp"

    def test_get_position_not_exists(self, tmp_path: Path) -> None:
        """Should return None for non-existent position ID."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-test:
    employer: "Test Corp"
    title: "Engineer"
    start_date: "2022-01"
""")
        service = PositionService(positions_file)
        pos = service.get_position("pos-nonexistent")

        assert pos is None

    def test_position_exists_true(self, tmp_path: Path) -> None:
        """Should return True when position exists."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-test:
    employer: "Test Corp"
    title: "Engineer"
    start_date: "2022-01"
""")
        service = PositionService(positions_file)

        assert service.position_exists("pos-test") is True

    def test_position_exists_false(self, tmp_path: Path) -> None:
        """Should return False when position doesn't exist."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-test:
    employer: "Test Corp"
    title: "Engineer"
    start_date: "2022-01"
""")
        service = PositionService(positions_file)

        assert service.position_exists("pos-nonexistent") is False


class TestPositionServiceGrouping:
    """Tests for grouping positions by employer."""

    def test_group_by_employer_single(self) -> None:
        """Should group single position under employer."""
        positions = [
            Position(
                id="pos-1",
                employer="TechCorp",
                title="Engineer",
                start_date="2022-01",
            )
        ]
        service = PositionService()
        groups = service.group_by_employer(positions)

        assert len(groups) == 1
        assert "TechCorp" in groups
        assert len(groups["TechCorp"]) == 1

    def test_group_by_employer_multiple_same_employer(self) -> None:
        """Should group multiple positions under same employer."""
        positions = [
            Position(
                id="pos-senior",
                employer="TechCorp",
                title="Senior Engineer",
                start_date="2022-01",
            ),
            Position(
                id="pos-junior",
                employer="TechCorp",
                title="Junior Engineer",
                start_date="2020-01",
                end_date="2021-12",
            ),
        ]
        service = PositionService()
        groups = service.group_by_employer(positions)

        assert len(groups) == 1
        assert "TechCorp" in groups
        assert len(groups["TechCorp"]) == 2

    def test_group_by_employer_multiple_employers(self) -> None:
        """Should group positions under different employers."""
        positions = [
            Position(id="pos-1", employer="TechCorp", title="Engineer", start_date="2022-01"),
            Position(id="pos-2", employer="Acme", title="Developer", start_date="2020-01"),
            Position(id="pos-3", employer="StartupX", title="Founder", start_date="2018-01"),
        ]
        service = PositionService()
        groups = service.group_by_employer(positions)

        assert len(groups) == 3
        assert "TechCorp" in groups
        assert "Acme" in groups
        assert "StartupX" in groups

    def test_group_by_employer_sorted_by_date(self) -> None:
        """Should sort positions within employer by start_date descending."""
        positions = [
            Position(
                id="pos-old",
                employer="TechCorp",
                title="Junior",
                start_date="2018-01",
                end_date="2019-12",
            ),
            Position(
                id="pos-mid",
                employer="TechCorp",
                title="Mid",
                start_date="2020-01",
                end_date="2021-12",
            ),
            Position(
                id="pos-new",
                employer="TechCorp",
                title="Senior",
                start_date="2022-01",
            ),
        ]
        service = PositionService()
        groups = service.group_by_employer(positions)

        techcorp_positions = groups["TechCorp"]
        assert techcorp_positions[0].id == "pos-new"  # Most recent first
        assert techcorp_positions[1].id == "pos-mid"
        assert techcorp_positions[2].id == "pos-old"


class TestPositionServicePromotionChain:
    """Tests for promotion chain detection."""

    def test_get_promotion_chain_single(self, tmp_path: Path) -> None:
        """Should return single position when no promotion history."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-senior:
    employer: "TechCorp"
    title: "Senior Engineer"
    start_date: "2022-01"
""")
        service = PositionService(positions_file)
        chain = service.get_promotion_chain("pos-senior")

        assert len(chain) == 1
        assert chain[0].id == "pos-senior"

    def test_get_promotion_chain_two_levels(self, tmp_path: Path) -> None:
        """Should return chain of two promotions."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-senior:
    employer: "TechCorp"
    title: "Senior Engineer"
    start_date: "2022-01"
    promoted_from: "pos-junior"
  pos-junior:
    employer: "TechCorp"
    title: "Junior Engineer"
    start_date: "2020-01"
    end_date: "2021-12"
""")
        service = PositionService(positions_file)
        chain = service.get_promotion_chain("pos-senior")

        assert len(chain) == 2
        assert chain[0].id == "pos-junior"  # Earliest first
        assert chain[1].id == "pos-senior"  # Most recent last

    def test_get_promotion_chain_three_levels(self, tmp_path: Path) -> None:
        """Should return chain of three promotions."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-director:
    employer: "TechCorp"
    title: "Director"
    start_date: "2023-01"
    promoted_from: "pos-senior"
  pos-senior:
    employer: "TechCorp"
    title: "Senior Engineer"
    start_date: "2021-01"
    end_date: "2022-12"
    promoted_from: "pos-junior"
  pos-junior:
    employer: "TechCorp"
    title: "Junior Engineer"
    start_date: "2019-01"
    end_date: "2020-12"
""")
        service = PositionService(positions_file)
        chain = service.get_promotion_chain("pos-director")

        assert len(chain) == 3
        assert chain[0].id == "pos-junior"
        assert chain[1].id == "pos-senior"
        assert chain[2].id == "pos-director"

    def test_get_promotion_chain_nonexistent(self, tmp_path: Path) -> None:
        """Should return empty list for non-existent position."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-test:
    employer: "TechCorp"
    title: "Engineer"
    start_date: "2022-01"
""")
        service = PositionService(positions_file)
        chain = service.get_promotion_chain("pos-nonexistent")

        assert chain == []

    def test_get_promotion_chain_circular_reference(self, tmp_path: Path) -> None:
        """Should handle circular promoted_from references without infinite loop."""
        positions_file = tmp_path / "positions.yaml"
        # Create circular reference: A -> B -> C -> A
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-a:
    employer: "TechCorp"
    title: "Role A"
    start_date: "2023-01"
    promoted_from: "pos-c"
  pos-b:
    employer: "TechCorp"
    title: "Role B"
    start_date: "2022-01"
    promoted_from: "pos-a"
  pos-c:
    employer: "TechCorp"
    title: "Role C"
    start_date: "2021-01"
    promoted_from: "pos-b"
""")
        service = PositionService(positions_file)

        # Should not hang - cycle detection prevents infinite loop
        # Returns partial chain up to point of cycle detection
        chain = service.get_promotion_chain("pos-a")

        # Should have at most 3 positions (cycle is detected and stops)
        assert len(chain) <= 3
        # Should include pos-a (the requested position)
        assert any(p.id == "pos-a" for p in chain)

    def test_get_promotion_chain_self_reference(self, tmp_path: Path) -> None:
        """Should handle self-referential promoted_from without infinite loop."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-self:
    employer: "TechCorp"
    title: "Self Ref"
    start_date: "2022-01"
    promoted_from: "pos-self"
""")
        service = PositionService(positions_file)

        # Should not hang - returns just the single position
        chain = service.get_promotion_chain("pos-self")

        assert len(chain) == 1
        assert chain[0].id == "pos-self"


class TestPositionServiceSave:
    """Tests for saving positions."""

    def test_save_position_new_file(self, tmp_path: Path) -> None:
        """Should create new file when saving first position."""
        positions_file = tmp_path / "positions.yaml"
        service = PositionService(positions_file)

        position = Position(
            id="pos-test",
            employer="Test Corp",
            title="Engineer",
            start_date="2022-01",
        )
        service.save_position(position)

        assert positions_file.exists()
        content = positions_file.read_text()
        assert "pos-test" in content
        assert "Test Corp" in content

    def test_save_position_existing_file(self, tmp_path: Path) -> None:
        """Should add position to existing file."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-existing:
    employer: "Existing Corp"
    title: "Developer"
    start_date: "2020-01"
""")
        service = PositionService(positions_file)

        position = Position(
            id="pos-new",
            employer="New Corp",
            title="Engineer",
            start_date="2023-01",
        )
        service.save_position(position)

        # Reload and verify both positions exist
        service._positions = None  # Clear cache
        positions = service.load_positions()
        assert "pos-existing" in positions
        assert "pos-new" in positions

    def test_save_position_clears_cache(self, tmp_path: Path) -> None:
        """Should clear cache after saving."""
        positions_file = tmp_path / "positions.yaml"
        service = PositionService(positions_file)

        # Load initial (empty)
        positions1 = service.load_positions()
        assert len(positions1) == 0

        # Save new position
        position = Position(
            id="pos-test",
            employer="Test Corp",
            title="Engineer",
            start_date="2022-01",
        )
        service.save_position(position)

        # Load again - should see new position
        positions2 = service.load_positions()
        assert "pos-test" in positions2

    def test_save_position_excludes_none_values(self, tmp_path: Path) -> None:
        """Should not write None values to YAML."""
        positions_file = tmp_path / "positions.yaml"
        service = PositionService(positions_file)

        position = Position(
            id="pos-test",
            employer="Test Corp",
            title="Engineer",
            start_date="2022-01",
            # location, end_date, employment_type, promoted_from, description are None
        )
        service.save_position(position)

        content = positions_file.read_text()
        assert "location:" not in content
        assert "end_date:" not in content
        assert "promoted_from:" not in content


class TestPositionServiceSuggestForDate:
    """Tests for date-based position suggestion (AC#5)."""

    def test_suggest_current_position_for_today(self, tmp_path: Path) -> None:
        """Should suggest current position for today's date."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-current:
    employer: "Current Corp"
    title: "Senior Engineer"
    start_date: "2022-01"
""")
        service = PositionService(positions_file)
        result = service.suggest_position_for_date("2025-06")

        assert result is not None
        assert result.id == "pos-current"

    def test_suggest_past_position_for_past_date(self, tmp_path: Path) -> None:
        """Should suggest past position for date within its tenure."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-current:
    employer: "Current Corp"
    title: "Senior Engineer"
    start_date: "2023-01"
  pos-past:
    employer: "Past Corp"
    title: "Engineer"
    start_date: "2020-01"
    end_date: "2022-12"
""")
        service = PositionService(positions_file)
        result = service.suggest_position_for_date("2021-06")

        assert result is not None
        assert result.id == "pos-past"

    def test_suggest_returns_most_recent_match(self, tmp_path: Path) -> None:
        """Should return most recent matching position when multiple overlap."""
        positions_file = tmp_path / "positions.yaml"
        # Overlapping positions (e.g., promotion mid-month)
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-senior:
    employer: "TechCorp"
    title: "Senior Engineer"
    start_date: "2022-06"
  pos-junior:
    employer: "TechCorp"
    title: "Junior Engineer"
    start_date: "2020-01"
    end_date: "2022-06"
""")
        service = PositionService(positions_file)
        # Date matches both positions
        result = service.suggest_position_for_date("2022-06")

        assert result is not None
        assert result.id == "pos-senior"  # Most recent start_date

    def test_suggest_returns_none_no_positions(self, tmp_path: Path) -> None:
        """Should return None when no positions exist."""
        positions_file = tmp_path / "nonexistent.yaml"
        service = PositionService(positions_file)
        result = service.suggest_position_for_date("2024-01")

        assert result is None

    def test_suggest_returns_none_date_before_all_positions(self, tmp_path: Path) -> None:
        """Should return None when date is before all positions."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-first:
    employer: "First Corp"
    title: "Engineer"
    start_date: "2020-01"
""")
        service = PositionService(positions_file)
        result = service.suggest_position_for_date("2018-06")

        assert result is None

    def test_suggest_returns_none_date_between_positions(self, tmp_path: Path) -> None:
        """Should return None when date falls in employment gap."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-later:
    employer: "Later Corp"
    title: "Engineer"
    start_date: "2023-01"
  pos-earlier:
    employer: "Earlier Corp"
    title: "Developer"
    start_date: "2020-01"
    end_date: "2021-06"
""")
        service = PositionService(positions_file)
        # Gap from 2021-07 to 2022-12
        result = service.suggest_position_for_date("2022-03")

        assert result is None

    def test_suggest_handles_full_date_format(self, tmp_path: Path) -> None:
        """Should handle YYYY-MM-DD date format."""
        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-test:
    employer: "Test Corp"
    title: "Engineer"
    start_date: "2022-01"
""")
        service = PositionService(positions_file)
        result = service.suggest_position_for_date("2023-06-15")

        assert result is not None
        assert result.id == "pos-test"


def _years_ago_ym(years: int) -> str:
    """Helper to get YYYY-MM format for N years ago from today."""
    from datetime import date

    today = date.today()
    return f"{today.year - years:04d}-{today.month:02d}"


class TestPositionServiceFilterByYears:
    """Tests for filter_by_years method (Story 13.2)."""

    def test_filter_current_position_always_included(self) -> None:
        """Current positions (end_date=None) should always be included."""
        positions = [
            Position(
                id="pos-current",
                employer="TechCorp",
                title="Engineer",
                start_date="2020-01",
                end_date=None,  # Current position
            )
        ]
        result = PositionService.filter_by_years(positions, years=5)

        assert len(result) == 1
        assert result[0].id == "pos-current"

    def test_filter_recent_position_included(self) -> None:
        """Position ending within filter range should be included."""
        # Position ended 2 years ago - should be included in 5-year filter
        end_date = _years_ago_ym(2)

        positions = [
            Position(
                id="pos-recent",
                employer="RecentCorp",
                title="Engineer",
                start_date="2018-01",
                end_date=end_date,
            )
        ]
        result = PositionService.filter_by_years(positions, years=5)

        assert len(result) == 1
        assert result[0].id == "pos-recent"

    def test_filter_old_position_excluded(self) -> None:
        """Position ending before filter range should be excluded."""
        # Position ended 15 years ago - should be excluded from 10-year filter
        end_date = _years_ago_ym(15)

        positions = [
            Position(
                id="pos-ancient",
                employer="AncientCorp",
                title="Developer",
                start_date="2000-01",
                end_date=end_date,
            )
        ]
        result = PositionService.filter_by_years(positions, years=10)

        assert len(result) == 0

    def test_filter_position_at_cutoff_boundary_included(self) -> None:
        """Position ending exactly at cutoff should be included."""
        # Position ending exactly at cutoff (10 years ago)
        end_date = _years_ago_ym(10)

        positions = [
            Position(
                id="pos-boundary",
                employer="BoundaryCorp",
                title="Engineer",
                start_date="2005-01",
                end_date=end_date,
            )
        ]
        result = PositionService.filter_by_years(positions, years=10)

        assert len(result) == 1
        assert result[0].id == "pos-boundary"

    def test_filter_mixed_positions(self) -> None:
        """Should correctly filter mix of current, recent, and old positions."""
        five_years_ago = _years_ago_ym(5)
        twenty_years_ago = _years_ago_ym(20)

        positions = [
            Position(
                id="pos-current",
                employer="CurrentCorp",
                title="Director",
                start_date="2022-01",
                end_date=None,  # Current - should be included
            ),
            Position(
                id="pos-recent",
                employer="RecentCorp",
                title="Manager",
                start_date="2015-01",
                end_date=five_years_ago,  # 5 years ago - included
            ),
            Position(
                id="pos-ancient",
                employer="AncientCorp",
                title="Intern",
                start_date="2000-01",
                end_date=twenty_years_ago,  # 20 years ago - excluded
            ),
        ]
        result = PositionService.filter_by_years(positions, years=10)

        assert len(result) == 2
        result_ids = {p.id for p in result}
        assert "pos-current" in result_ids
        assert "pos-recent" in result_ids
        assert "pos-ancient" not in result_ids

    def test_filter_position_spanning_cutoff_included(self) -> None:
        """Position started before cutoff but ended after should be included (AC6)."""
        # Position started 12 years ago, ended 8 years ago
        start_date = _years_ago_ym(12)
        end_date = _years_ago_ym(8)

        positions = [
            Position(
                id="pos-spanning",
                employer="SpanningCorp",
                title="Engineer",
                start_date=start_date,
                end_date=end_date,
            )
        ]
        result = PositionService.filter_by_years(positions, years=10)

        # end_date (8 years ago) is within range, so position should be included
        assert len(result) == 1
        assert result[0].id == "pos-spanning"

    def test_filter_empty_list(self) -> None:
        """Should return empty list for empty input."""
        result = PositionService.filter_by_years([], years=10)
        assert result == []

    def test_filter_with_one_year(self) -> None:
        """Should work with minimum filter value of 1 year."""
        from datetime import date

        # Use months calculation for sub-year precision
        today = date.today()
        # 6 months ago - compute year/month manually
        if today.month > 6:
            six_months_ago = f"{today.year:04d}-{today.month - 6:02d}"
        else:
            six_months_ago = f"{today.year - 1:04d}-{today.month + 6:02d}"

        two_years_ago = _years_ago_ym(2)

        positions = [
            Position(
                id="pos-6months",
                employer="RecentCorp",
                title="Engineer",
                start_date="2020-01",
                end_date=six_months_ago,  # 6 months ago - included
            ),
            Position(
                id="pos-2years",
                employer="OlderCorp",
                title="Developer",
                start_date="2018-01",
                end_date=two_years_ago,  # 2 years ago - excluded
            ),
        ]
        result = PositionService.filter_by_years(positions, years=1)

        assert len(result) == 1
        assert result[0].id == "pos-6months"
