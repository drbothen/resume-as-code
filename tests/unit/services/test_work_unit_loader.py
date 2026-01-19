"""Tests for WorkUnitLoader service (Story 7.6)."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from resume_as_code.models.errors import ValidationError
from resume_as_code.models.position import Position
from resume_as_code.services.work_unit_loader import WorkUnitLoader


@pytest.fixture
def temp_work_units_dir() -> Generator[Path, None, None]:
    """Create temporary work units directory with sample files."""
    with TemporaryDirectory() as tmpdir:
        work_units_dir = Path(tmpdir) / "work-units"
        work_units_dir.mkdir()

        # Create valid work unit with position reference
        (work_units_dir / "wu-valid.yaml").write_text(
            """\
id: wu-2024-01-01-valid
title: Valid work unit for testing purposes
position_id: pos-acme-engineer
problem:
  statement: Test problem statement here for validation
actions:
  - First action with enough characters to pass validation
outcome:
  result: Test outcome result here
archetype: minimal
"""
        )

        # Create work unit without position_id (standalone)
        (work_units_dir / "wu-standalone.yaml").write_text(
            """\
id: wu-2024-01-02-standalone
title: Standalone work unit without position
problem:
  statement: Problem statement here for testing purposes
actions:
  - Action with enough characters here for validation
outcome:
  result: Outcome result here
archetype: minimal
"""
        )

        yield work_units_dir


@pytest.fixture
def sample_positions() -> dict[str, Position]:
    """Create dictionary of positions for testing."""
    return {
        "pos-acme-engineer": Position(
            id="pos-acme-engineer",
            employer="Acme Corp",
            title="Software Engineer",
            start_date="2022-01",
        ),
        "pos-acme-senior": Position(
            id="pos-acme-senior",
            employer="Acme Corp",
            title="Senior Engineer",
            start_date="2023-01",
        ),
    }


class TestWorkUnitLoaderLoadAll:
    """Tests for load_all() method."""

    def test_load_all_returns_work_units(self, temp_work_units_dir: Path) -> None:
        """Load all returns list of work units from directory."""
        loader = WorkUnitLoader(temp_work_units_dir)
        work_units = loader.load_all()

        assert len(work_units) == 2
        ids = {wu.id for wu in work_units}
        assert "wu-2024-01-01-valid" in ids
        assert "wu-2024-01-02-standalone" in ids

    def test_load_all_empty_directory(self) -> None:
        """Empty directory returns empty list."""
        with TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / "work-units"
            empty_dir.mkdir()
            loader = WorkUnitLoader(empty_dir)

            work_units = loader.load_all()

            assert work_units == []

    def test_load_all_nonexistent_directory(self) -> None:
        """Non-existent directory returns empty list."""
        loader = WorkUnitLoader(Path("/nonexistent/path"))
        work_units = loader.load_all()
        assert work_units == []

    def test_load_all_skips_hidden_files(self, temp_work_units_dir: Path) -> None:
        """Hidden files (starting with .) are skipped."""
        # Create a hidden file
        (temp_work_units_dir / ".hidden.yaml").write_text(
            """\
id: wu-2024-01-03-hidden
title: Hidden work unit should not load
problem:
  statement: Problem statement here for testing
actions:
  - Action here
outcome:
  result: Result here
archetype: minimal
"""
        )

        loader = WorkUnitLoader(temp_work_units_dir)
        work_units = loader.load_all()

        # Should only have the 2 original files, not the hidden one
        assert len(work_units) == 2
        ids = {wu.id for wu in work_units}
        assert "wu-2024-01-03-hidden" not in ids


class TestWorkUnitLoaderLoadWithPositions:
    """Tests for load_with_positions() method."""

    def test_load_with_positions_attaches_position(
        self, temp_work_units_dir: Path, sample_positions: dict[str, Position]
    ) -> None:
        """Loading with positions attaches Position to WorkUnit."""
        loader = WorkUnitLoader(temp_work_units_dir)
        work_units = loader.load_with_positions(sample_positions)

        # Find the work unit with position_id
        wu_with_pos = next(wu for wu in work_units if wu.id == "wu-2024-01-01-valid")

        assert wu_with_pos.position is not None
        assert wu_with_pos.position.id == "pos-acme-engineer"
        assert wu_with_pos.position.employer == "Acme Corp"

    def test_load_with_positions_standalone_has_no_position(
        self, temp_work_units_dir: Path, sample_positions: dict[str, Position]
    ) -> None:
        """Work units without position_id have None for position."""
        loader = WorkUnitLoader(temp_work_units_dir)
        work_units = loader.load_with_positions(sample_positions)

        # Find the standalone work unit
        wu_standalone = next(wu for wu in work_units if wu.id == "wu-2024-01-02-standalone")

        assert wu_standalone.position_id is None
        assert wu_standalone.position is None

    def test_load_with_positions_invalid_ref_raises_error(self, temp_work_units_dir: Path) -> None:
        """Invalid position_id raises ValidationError with suggestion."""
        loader = WorkUnitLoader(temp_work_units_dir)
        # Provide positions that don't match the referenced ID
        positions = {
            "pos-acme-engineer-senior": Position(
                id="pos-acme-engineer-senior",
                employer="Acme Corp",
                title="Senior Engineer",
                start_date="2022-01",
            )
        }

        with pytest.raises(ValidationError) as exc_info:
            loader.load_with_positions(positions)

        error_msg = str(exc_info.value)
        assert "pos-acme-engineer" in error_msg
        # Should suggest similar IDs or mention how to list positions
        assert "did you mean" in error_msg.lower() or "resume list positions" in error_msg.lower()

    def test_load_with_positions_includes_work_unit_id_in_error(
        self, temp_work_units_dir: Path
    ) -> None:
        """Error message includes the work unit ID for debugging."""
        loader = WorkUnitLoader(temp_work_units_dir)
        # No matching positions at all
        positions: dict[str, Position] = {}

        with pytest.raises(ValidationError) as exc_info:
            loader.load_with_positions(positions)

        error_msg = str(exc_info.value)
        # Should mention which work unit has the invalid reference
        assert "wu-2024-01-01-valid" in error_msg

    def test_load_with_positions_multiple_invalid_refs(self) -> None:
        """Multiple invalid references are all reported."""
        with TemporaryDirectory() as tmpdir:
            work_units_dir = Path(tmpdir) / "work-units"
            work_units_dir.mkdir()

            # Create two work units with different invalid position_ids
            (work_units_dir / "wu-1.yaml").write_text(
                """\
id: wu-2024-01-01-first
title: First work unit with invalid position
position_id: pos-invalid-one
problem:
  statement: Problem statement here for testing
actions:
  - Action with enough characters here
outcome:
  result: Result here
archetype: minimal
"""
            )
            (work_units_dir / "wu-2.yaml").write_text(
                """\
id: wu-2024-01-02-second
title: Second work unit with invalid position
position_id: pos-invalid-two
problem:
  statement: Problem statement here for testing
actions:
  - Action with enough characters here
outcome:
  result: Result here
archetype: minimal
"""
            )

            loader = WorkUnitLoader(work_units_dir)
            positions: dict[str, Position] = {}

            with pytest.raises(ValidationError) as exc_info:
                loader.load_with_positions(positions)

            error_msg = str(exc_info.value)
            # Both invalid IDs should be mentioned
            assert "pos-invalid-one" in error_msg
            assert "pos-invalid-two" in error_msg


class TestWorkUnitLoaderValidatePositionReferences:
    """Tests for validate_position_references() method."""

    def test_validate_position_references_all_valid(
        self, temp_work_units_dir: Path, sample_positions: dict[str, Position]
    ) -> None:
        """Returns (True, []) when all references are valid."""
        loader = WorkUnitLoader(temp_work_units_dir)
        is_valid, invalid_refs = loader.validate_position_references(sample_positions)

        assert is_valid is True
        assert invalid_refs == []

    def test_validate_position_references_with_invalid(self, temp_work_units_dir: Path) -> None:
        """Returns (False, [...]) when references are invalid."""
        loader = WorkUnitLoader(temp_work_units_dir)
        # Provide positions that don't match the referenced ID
        positions: dict[str, Position] = {}

        is_valid, invalid_refs = loader.validate_position_references(positions)

        assert is_valid is False
        # Should include the invalid reference
        assert len(invalid_refs) == 1
        assert invalid_refs[0] == ("wu-2024-01-01-valid", "pos-acme-engineer")

    def test_validate_position_references_standalone_ok(self, temp_work_units_dir: Path) -> None:
        """Work units without position_id are not flagged as invalid."""
        loader = WorkUnitLoader(temp_work_units_dir)
        # Provide only positions not referenced by any work unit
        positions = {
            "pos-acme-engineer": Position(
                id="pos-acme-engineer",
                employer="Acme Corp",
                title="Software Engineer",
                start_date="2022-01",
            )
        }

        is_valid, invalid_refs = loader.validate_position_references(positions)

        # Both work units should be valid (one matches, one has no position_id)
        assert is_valid is True
        assert invalid_refs == []

    def test_validate_position_references_multiple_invalid(self) -> None:
        """Returns all invalid references, not just the first."""
        with TemporaryDirectory() as tmpdir:
            work_units_dir = Path(tmpdir) / "work-units"
            work_units_dir.mkdir()

            (work_units_dir / "wu-1.yaml").write_text(
                """\
id: wu-2024-01-01-first
title: First work unit with invalid position
position_id: pos-invalid-one
problem:
  statement: Problem statement here for testing
actions:
  - Action with enough characters here
outcome:
  result: Result here
archetype: minimal
"""
            )
            (work_units_dir / "wu-2.yaml").write_text(
                """\
id: wu-2024-01-02-second
title: Second work unit with invalid position
position_id: pos-invalid-two
problem:
  statement: Problem statement here for testing
actions:
  - Action with enough characters here
outcome:
  result: Result here
archetype: minimal
"""
            )

            loader = WorkUnitLoader(work_units_dir)
            positions: dict[str, Position] = {}

            is_valid, invalid_refs = loader.validate_position_references(positions)

            assert is_valid is False
            assert len(invalid_refs) == 2
            # Check both are present (order may vary due to glob)
            ids = {ref[1] for ref in invalid_refs}
            assert "pos-invalid-one" in ids
            assert "pos-invalid-two" in ids
