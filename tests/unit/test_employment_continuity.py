"""Tests for EmploymentContinuityService (Story 7.20)."""

from __future__ import annotations

from datetime import date

import pytest

from resume_as_code.models.position import Position
from resume_as_code.models.work_unit import Outcome, Problem, WorkUnit, WorkUnitArchetype
from resume_as_code.services.employment_continuity import (
    EmploymentContinuityService,
    EmploymentGap,
)

# --- Fixtures ---


@pytest.fixture
def positions() -> list[Position]:
    """Sample positions covering 2020-2024."""
    return [
        Position(
            id="pos-acme-senior",
            employer="Acme Corp",
            title="Senior Engineer",
            start_date="2023-01",
            end_date=None,  # Current position
        ),
        Position(
            id="pos-techcorp-lead",
            employer="TechCorp",
            title="Tech Lead",
            start_date="2021-06",
            end_date="2022-12",
        ),
        Position(
            id="pos-startup-dev",
            employer="Startup Inc",
            title="Software Developer",
            start_date="2020-01",
            end_date="2021-05",
        ),
    ]


@pytest.fixture
def work_units(positions: list[Position]) -> list[WorkUnit]:
    """Sample work units referencing positions."""
    return [
        WorkUnit(
            id="wu-2024-01-01-acme-project",
            title="Led migration to cloud infrastructure at Acme",
            problem=Problem(statement="Legacy infrastructure was slow and expensive"),
            actions=["Designed migration strategy", "Implemented infrastructure as code"],
            outcome=Outcome(result="Reduced costs by 40%"),
            position_id="pos-acme-senior",
            time_ended=date(2024, 1, 15),
            archetype=WorkUnitArchetype.MIGRATION,
        ),
        WorkUnit(
            id="wu-2023-06-01-acme-security",
            title="Implemented security controls at Acme",
            problem=Problem(statement="Security posture needed improvement"),
            actions=["Conducted security audit", "Implemented controls"],
            outcome=Outcome(result="Achieved SOC2 compliance"),
            position_id="pos-acme-senior",
            time_ended=date(2023, 6, 15),
            archetype=WorkUnitArchetype.INCIDENT,
        ),
        WorkUnit(
            id="wu-2022-01-01-techcorp-api",
            title="Redesigned API layer at TechCorp",
            problem=Problem(statement="API was slow and unreliable"),
            actions=["Designed new API", "Migrated clients"],
            outcome=Outcome(result="Improved latency by 60%"),
            position_id="pos-techcorp-lead",
            time_ended=date(2022, 6, 15),
            archetype=WorkUnitArchetype.OPTIMIZATION,
        ),
        WorkUnit(
            id="wu-2020-06-01-startup-mvp",
            title="Built MVP for Startup product",
            problem=Problem(statement="Needed to ship product quickly"),
            actions=["Developed core features", "Set up CI/CD"],
            outcome=Outcome(result="Launched in 3 months"),
            position_id="pos-startup-dev",
            time_ended=date(2020, 8, 15),
            archetype=WorkUnitArchetype.GREENFIELD,
        ),
    ]


# --- EmploymentGap dataclass tests ---


class TestEmploymentGap:
    """Test EmploymentGap dataclass."""

    def test_employment_gap_creation(self) -> None:
        """EmploymentGap should hold gap details."""
        gap = EmploymentGap(
            start_date=date(2021, 6, 1),
            end_date=date(2022, 12, 31),
            duration_months=18,
            missing_position_id="pos-techcorp-lead",
            missing_employer="TechCorp",
        )
        assert gap.start_date == date(2021, 6, 1)
        assert gap.end_date == date(2022, 12, 31)
        assert gap.duration_months == 18
        assert gap.missing_position_id == "pos-techcorp-lead"
        assert gap.missing_employer == "TechCorp"


# --- EnsureContinuity tests ---


class TestEnsureContinuity:
    """Test ensure_continuity method."""

    def test_minimum_bullet_adds_missing_positions(
        self, positions: list[Position], work_units: list[WorkUnit]
    ) -> None:
        """minimum_bullet mode adds work unit for each missing position."""
        service = EmploymentContinuityService(mode="minimum_bullet")

        # Only select work units from first position
        selected = [wu for wu in work_units if wu.position_id == "pos-acme-senior"]
        assert len(selected) == 2  # Two acme work units

        result = service.ensure_continuity(positions, selected, work_units)

        # Should have work units from all 3 positions
        result_position_ids = {wu.position_id for wu in result}
        assert len(result_position_ids) == 3
        assert "pos-acme-senior" in result_position_ids
        assert "pos-techcorp-lead" in result_position_ids
        assert "pos-startup-dev" in result_position_ids

    def test_allow_gaps_returns_unchanged(
        self, positions: list[Position], work_units: list[WorkUnit]
    ) -> None:
        """allow_gaps mode returns selection unchanged."""
        service = EmploymentContinuityService(mode="allow_gaps")
        selected = [work_units[0]]  # Just one work unit

        result = service.ensure_continuity(positions, selected, work_units)

        assert result == selected
        assert len(result) == 1

    def test_minimum_bullet_uses_highest_scoring_work_unit(
        self, positions: list[Position], work_units: list[WorkUnit]
    ) -> None:
        """When adding missing position, selects highest-scoring work unit."""
        service = EmploymentContinuityService(mode="minimum_bullet")

        # Only select from acme
        selected = [work_units[0]]  # One acme work unit

        # Provide scores - techcorp API work unit should be selected
        scores = {
            "wu-2024-01-01-acme-project": 0.9,
            "wu-2023-06-01-acme-security": 0.8,
            "wu-2022-01-01-techcorp-api": 0.7,  # Best for techcorp
            "wu-2020-06-01-startup-mvp": 0.6,  # Best for startup
        }

        result = service.ensure_continuity(positions, selected, work_units, scores)

        # Should have added best work unit from each missing position
        assert len(result) == 3
        result_ids = {wu.id for wu in result}
        assert "wu-2024-01-01-acme-project" in result_ids
        assert "wu-2022-01-01-techcorp-api" in result_ids
        assert "wu-2020-06-01-startup-mvp" in result_ids

    def test_minimum_bullet_with_no_work_units_for_position(
        self, positions: list[Position], work_units: list[WorkUnit]
    ) -> None:
        """Position with no work units is skipped."""
        service = EmploymentContinuityService(mode="minimum_bullet")

        # Add position with no work units
        new_position = Position(
            id="pos-empty",
            employer="Empty Corp",
            title="Ghost Employee",
            start_date="2019-01",
            end_date="2019-12",
        )
        all_positions = positions + [new_position]

        selected = [work_units[0]]
        result = service.ensure_continuity(all_positions, selected, work_units)

        # pos-empty has no work units, so it won't be included
        result_position_ids = {wu.position_id for wu in result}
        assert "pos-empty" not in result_position_ids


# --- DetectGaps tests ---


class TestDetectGaps:
    """Test detect_gaps method."""

    def test_detects_excluded_position(
        self, positions: list[Position], work_units: list[WorkUnit]
    ) -> None:
        """Detects gap when position is excluded."""
        service = EmploymentContinuityService(min_gap_months=3)

        # Exclude TechCorp (18 months long)
        selected = [wu for wu in work_units if wu.position_id != "pos-techcorp-lead"]

        gaps = service.detect_gaps(positions, selected)

        assert len(gaps) == 1
        assert gaps[0].missing_position_id == "pos-techcorp-lead"
        assert gaps[0].missing_employer == "TechCorp"
        assert gaps[0].duration_months >= 18

    def test_ignores_short_gaps(self, work_units: list[WorkUnit]) -> None:
        """Gaps under min_gap_months are not reported."""
        # Create position that's only 2 months long
        short_position = Position(
            id="pos-short",
            employer="Short Corp",
            title="Brief Role",
            start_date="2019-06",
            end_date="2019-07",
        )

        service = EmploymentContinuityService(min_gap_months=3)

        # Exclude the short position
        selected = work_units  # None from short_position
        gaps = service.detect_gaps([short_position], selected)

        # Should not report 2-month gap
        assert len(gaps) == 0

    def test_no_gaps_when_all_positions_included(
        self, positions: list[Position], work_units: list[WorkUnit]
    ) -> None:
        """No gaps when all positions have work units."""
        service = EmploymentContinuityService(min_gap_months=3)

        # All work units included
        gaps = service.detect_gaps(positions, work_units)

        assert len(gaps) == 0

    def test_current_position_gap_uses_today(self, work_units: list[WorkUnit]) -> None:
        """Current positions (no end_date) use today for gap calculation."""
        current_position = Position(
            id="pos-current",
            employer="Current Co",
            title="Current Role",
            start_date="2023-01",
            end_date=None,  # Current
        )

        service = EmploymentContinuityService(min_gap_months=3)

        # Exclude current position
        gaps = service.detect_gaps([current_position], [])

        assert len(gaps) == 1
        assert gaps[0].missing_position_id == "pos-current"
        # Gap should extend to today
        assert gaps[0].end_date >= date.today()


# --- FormatGapWarning tests ---


class TestFormatGapWarning:
    """Test format_gap_warning method."""

    def test_format_single_gap(self) -> None:
        """Formats single gap warning."""
        service = EmploymentContinuityService()

        gaps = [
            EmploymentGap(
                start_date=date(2021, 6, 1),
                end_date=date(2022, 12, 1),
                duration_months=18,
                missing_position_id="pos-techcorp",
                missing_employer="TechCorp",
            )
        ]

        warning = service.format_gap_warning(gaps)

        assert "Employment Gap Detected" in warning
        assert "TechCorp" in warning
        assert "18 months" in warning
        assert "--no-allow-gaps" in warning

    def test_format_multiple_gaps(self) -> None:
        """Formats multiple gap warnings."""
        service = EmploymentContinuityService()

        gaps = [
            EmploymentGap(
                start_date=date(2021, 6, 1),
                end_date=date(2022, 12, 1),
                duration_months=18,
                missing_position_id="pos-a",
                missing_employer="Company A",
            ),
            EmploymentGap(
                start_date=date(2019, 1, 1),
                end_date=date(2020, 6, 1),
                duration_months=17,
                missing_position_id="pos-b",
                missing_employer="Company B",
            ),
        ]

        warning = service.format_gap_warning(gaps)

        assert "Company A" in warning
        assert "Company B" in warning
        assert "18 months" in warning
        assert "17 months" in warning

    def test_format_empty_gaps_returns_empty(self) -> None:
        """Empty gap list returns empty string."""
        service = EmploymentContinuityService()
        warning = service.format_gap_warning([])
        assert warning == ""


# --- Integration tests ---


class TestEmploymentContinuityIntegration:
    """Integration tests for full workflow."""

    def test_full_workflow_minimum_bullet(
        self, positions: list[Position], work_units: list[WorkUnit]
    ) -> None:
        """Full workflow with minimum_bullet mode."""
        service = EmploymentContinuityService(mode="minimum_bullet")

        # Start with only one work unit
        selected = [work_units[0]]

        # Ensure continuity
        result = service.ensure_continuity(positions, selected, work_units)

        # Should have work units from all positions
        assert len(result) == 3

        # No gaps should be detected
        gaps = service.detect_gaps(positions, result)
        assert len(gaps) == 0

    def test_full_workflow_allow_gaps(
        self, positions: list[Position], work_units: list[WorkUnit]
    ) -> None:
        """Full workflow with allow_gaps mode shows warnings."""
        service = EmploymentContinuityService(mode="allow_gaps")

        # Start with only one work unit from acme
        selected = [work_units[0]]

        # Don't modify selection
        result = service.ensure_continuity(positions, selected, work_units)
        assert len(result) == 1

        # Gaps should be detected
        gaps = service.detect_gaps(positions, result)
        assert len(gaps) == 2  # TechCorp and Startup missing

        # Warning should be formatted
        warning = service.format_gap_warning(gaps)
        assert "Employment Gap Detected" in warning
