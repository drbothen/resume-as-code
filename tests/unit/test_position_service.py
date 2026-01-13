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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
schema_version: "1.0.0"
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
