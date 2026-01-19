"""Tests for WorkUnit position attachment functionality (Story 7.6)."""

from __future__ import annotations

import pytest

from resume_as_code.models.position import Position
from resume_as_code.models.work_unit import Outcome, Problem, WorkUnit, WorkUnitArchetype


@pytest.fixture
def sample_work_unit() -> WorkUnit:
    """Create sample work unit with position_id."""
    return WorkUnit(
        id="wu-2024-01-01-test",
        title="Test work unit for position attachment",
        problem=Problem(statement="Test problem statement here for validation"),
        actions=["First action with enough characters to pass validation"],
        outcome=Outcome(result="Test outcome result here"),
        archetype=WorkUnitArchetype.MINIMAL,
        position_id="pos-acme-engineer",
    )


@pytest.fixture
def sample_position() -> Position:
    """Create sample position."""
    return Position(
        id="pos-acme-engineer",
        employer="Acme Corp",
        title="Software Engineer",
        start_date="2022-01",
    )


def test_work_unit_position_property_none_by_default(sample_work_unit: WorkUnit) -> None:
    """Position property returns None before attachment."""
    assert sample_work_unit.position is None


def test_attach_position_success(sample_work_unit: WorkUnit, sample_position: Position) -> None:
    """Attaching matching position succeeds."""
    sample_work_unit.attach_position(sample_position)

    assert sample_work_unit.position is not None
    assert sample_work_unit.position.id == "pos-acme-engineer"
    assert sample_work_unit.position.employer == "Acme Corp"


def test_attach_position_id_mismatch(sample_work_unit: WorkUnit) -> None:
    """Attaching position with wrong ID raises ValueError."""
    wrong_position = Position(
        id="pos-other-company",
        employer="Other Corp",
        title="Developer",
        start_date="2023-01",
    )

    with pytest.raises(ValueError, match="Position ID mismatch"):
        sample_work_unit.attach_position(wrong_position)


def test_attach_position_without_position_id() -> None:
    """Cannot attach position to WorkUnit without position_id."""
    wu = WorkUnit(
        id="wu-2024-01-02-standalone",
        title="Standalone work unit without position",
        problem=Problem(statement="Problem statement here for testing"),
        actions=["Action with enough characters here for validation"],
        outcome=Outcome(result="Outcome result here"),
        archetype=WorkUnitArchetype.MINIMAL,
        # position_id is None
    )

    position = Position(
        id="pos-any",
        employer="Any Corp",
        title="Any Title",
        start_date="2024-01",
    )

    with pytest.raises(ValueError, match="Cannot attach position"):
        wu.attach_position(position)


def test_position_not_serialized(sample_work_unit: WorkUnit, sample_position: Position) -> None:
    """Attached position is not included in model serialization."""
    sample_work_unit.attach_position(sample_position)

    # Serialize to dict
    data = sample_work_unit.model_dump()

    # _position should not be in serialized output
    assert "_position" not in data
    assert "position" not in data  # property is not serialized

    # position_id should be present
    assert data["position_id"] == "pos-acme-engineer"
