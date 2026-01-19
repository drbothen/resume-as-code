"""Unit tests for seniority inference service."""

from __future__ import annotations

import pytest

from resume_as_code.models.job_description import ExperienceLevel
from resume_as_code.services.seniority_inference import (
    calculate_seniority_alignment,
    infer_seniority,
    infer_seniority_from_title,
)


class TestInferSeniorityFromTitle:
    """Test title pattern matching."""

    @pytest.mark.parametrize(
        ("title", "expected"),
        [
            # Executive level
            ("CTO", ExperienceLevel.EXECUTIVE),
            ("VP of Engineering", ExperienceLevel.EXECUTIVE),
            ("Chief Technology Officer", ExperienceLevel.EXECUTIVE),
            ("EVP, Product", ExperienceLevel.EXECUTIVE),
            ("President of Operations", ExperienceLevel.EXECUTIVE),
            ("General Manager, APAC", ExperienceLevel.EXECUTIVE),
            ("CISO", ExperienceLevel.EXECUTIVE),
            # Principal level
            ("Principal Engineer", ExperienceLevel.PRINCIPAL),
            ("Distinguished Engineer", ExperienceLevel.PRINCIPAL),
            ("Fellow", ExperienceLevel.PRINCIPAL),
            # Staff level
            ("Staff Software Engineer", ExperienceLevel.STAFF),
            ("Solutions Architect", ExperienceLevel.STAFF),
            ("Staff Engineer", ExperienceLevel.STAFF),
            # Lead level
            ("Engineering Manager", ExperienceLevel.LEAD),
            ("Tech Lead", ExperienceLevel.LEAD),
            ("Team Lead", ExperienceLevel.LEAD),
            ("Director of Engineering", ExperienceLevel.LEAD),
            ("Lead Developer", ExperienceLevel.LEAD),
            # Senior level
            ("Senior Software Engineer", ExperienceLevel.SENIOR),
            ("Sr. Developer", ExperienceLevel.SENIOR),
            ("Senior Platform Engineer", ExperienceLevel.SENIOR),
            ("Sr Backend Engineer", ExperienceLevel.SENIOR),
            # Mid level
            ("Software Engineer II", ExperienceLevel.MID),
            ("Developer", ExperienceLevel.MID),
            ("Software Engineer", ExperienceLevel.MID),
            ("Analyst", ExperienceLevel.MID),
            # Entry level
            ("Junior Developer", ExperienceLevel.ENTRY),
            ("Jr. Engineer", ExperienceLevel.ENTRY),
            ("Associate Engineer", ExperienceLevel.ENTRY),
            ("Software Engineering Intern", ExperienceLevel.ENTRY),
            ("Graduate Software Developer", ExperienceLevel.ENTRY),
        ],
    )
    def test_title_pattern_matching(self, title: str, expected: ExperienceLevel) -> None:
        """Test various title patterns map to correct seniority levels."""
        assert infer_seniority_from_title(title) == expected

    def test_unknown_title_defaults_to_mid(self) -> None:
        """Unknown titles should default to MID level."""
        assert infer_seniority_from_title("Specialist") == ExperienceLevel.MID
        assert infer_seniority_from_title("Consultant") == ExperienceLevel.MID
        assert infer_seniority_from_title("Coordinator") == ExperienceLevel.MID

    def test_case_insensitive_matching(self) -> None:
        """Title matching should be case insensitive."""
        assert infer_seniority_from_title("SENIOR ENGINEER") == ExperienceLevel.SENIOR
        assert infer_seniority_from_title("cto") == ExperienceLevel.EXECUTIVE
        assert infer_seniority_from_title("Staff ENGINEER") == ExperienceLevel.STAFF


class TestSeniorityAlignment:
    """Test alignment score calculation with asymmetric penalties.

    Per AC4: overqualified gets slight penalty, underqualified gets larger penalty.
    """

    def test_exact_match(self) -> None:
        """Exact match should return 1.0."""
        assert calculate_seniority_alignment(ExperienceLevel.SENIOR, ExperienceLevel.SENIOR) == 1.0
        assert (
            calculate_seniority_alignment(ExperienceLevel.EXECUTIVE, ExperienceLevel.EXECUTIVE)
            == 1.0
        )
        assert calculate_seniority_alignment(ExperienceLevel.ENTRY, ExperienceLevel.ENTRY) == 1.0

    def test_overqualified_one_level(self) -> None:
        """Overqualified by one level should get slight penalty (0.9)."""
        # LEAD (rank 4) applying for SENIOR (rank 3) job
        assert calculate_seniority_alignment(ExperienceLevel.LEAD, ExperienceLevel.SENIOR) == 0.9

    def test_underqualified_one_level(self) -> None:
        """Underqualified by one level should get moderate penalty (0.8)."""
        # SENIOR (rank 3) applying for LEAD (rank 4) job
        assert calculate_seniority_alignment(ExperienceLevel.SENIOR, ExperienceLevel.LEAD) == 0.8

    def test_overqualified_two_levels(self) -> None:
        """Overqualified by two levels should get penalty (0.8)."""
        # STAFF (rank 5) applying for SENIOR (rank 3) job
        assert calculate_seniority_alignment(ExperienceLevel.STAFF, ExperienceLevel.SENIOR) == 0.8

    def test_underqualified_two_levels(self) -> None:
        """Underqualified by two levels should get larger penalty (0.6)."""
        # MID (rank 2) applying for LEAD (rank 4) job
        assert calculate_seniority_alignment(ExperienceLevel.MID, ExperienceLevel.LEAD) == 0.6

    def test_overqualified_three_levels(self) -> None:
        """Overqualified by three levels should get penalty (0.75)."""
        # PRINCIPAL (rank 6) applying for SENIOR (rank 3) job
        assert (
            calculate_seniority_alignment(ExperienceLevel.PRINCIPAL, ExperienceLevel.SENIOR) == 0.75
        )

    def test_underqualified_three_levels(self) -> None:
        """Underqualified by three levels should get significant penalty (0.4)."""
        # SENIOR (rank 3) applying for PRINCIPAL (rank 6) job
        assert (
            calculate_seniority_alignment(ExperienceLevel.SENIOR, ExperienceLevel.PRINCIPAL) == 0.4
        )

    def test_major_overqualified(self) -> None:
        """Major overqualified (4+ levels) should return 0.7."""
        # EXECUTIVE (rank 7) applying for ENTRY (rank 1) job
        assert (
            calculate_seniority_alignment(ExperienceLevel.EXECUTIVE, ExperienceLevel.ENTRY) == 0.7
        )

    def test_major_underqualified(self) -> None:
        """Major underqualified (4+ levels) should return 0.3."""
        # ENTRY (rank 1) applying for EXECUTIVE (rank 7) job
        assert (
            calculate_seniority_alignment(ExperienceLevel.ENTRY, ExperienceLevel.EXECUTIVE) == 0.3
        )

    def test_asymmetric_penalty(self) -> None:
        """Overqualified should have less penalty than underqualified at same distance."""
        # Both 2 levels apart, but different directions
        overqualified = calculate_seniority_alignment(ExperienceLevel.STAFF, ExperienceLevel.SENIOR)
        underqualified = calculate_seniority_alignment(ExperienceLevel.MID, ExperienceLevel.LEAD)
        assert overqualified > underqualified  # 0.8 > 0.6


class TestParseCurrency:
    """Test currency string parsing."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("$500M", 500_000_000),
            ("$2.5B", 2_500_000_000),
            ("$50K", 50_000),
            ("$1,000,000", 1_000_000),
            ("100M", 100_000_000),
            ("$10.5M", 10_500_000),
            ("", 0),
        ],
    )
    def test_currency_parsing(self, value: str, expected: int) -> None:
        """Test various currency formats are parsed correctly."""
        from resume_as_code.services.seniority_inference import _parse_currency

        assert _parse_currency(value) == expected


class TestInferSeniority:
    """Test full seniority inference with work units and positions."""

    def test_explicit_seniority_takes_priority(self) -> None:
        """Explicit seniority_level on work unit should be used."""
        from resume_as_code.models.work_unit import WorkUnit, WorkUnitArchetype

        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Junior task with explicit seniority override",
            problem={"statement": "This is a test problem statement"},
            actions=["Action taken to resolve the issue"],
            outcome={"result": "Successful outcome achieved"},
            archetype=WorkUnitArchetype.MINIMAL,
            seniority_level=ExperienceLevel.EXECUTIVE,  # Explicit override
        )
        assert infer_seniority(wu, None) == ExperienceLevel.EXECUTIVE

    def test_position_title_inference(self) -> None:
        """Position title should be used when no explicit seniority."""
        from resume_as_code.models.position import Position
        from resume_as_code.models.work_unit import WorkUnit, WorkUnitArchetype

        position = Position(
            id="pos-acme-vp-engineering",
            employer="Acme Corp",
            title="VP of Engineering",
            start_date="2020-01",
        )
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Led strategic initiative",
            problem={"statement": "This is a test problem statement"},
            actions=["Action taken to resolve the issue"],
            outcome={"result": "Successful outcome achieved"},
            archetype=WorkUnitArchetype.STRATEGIC,
            position_id="pos-acme-vp-engineering",
        )
        assert infer_seniority(wu, position) == ExperienceLevel.EXECUTIVE

    def test_scope_pl_boosts_to_executive(self) -> None:
        """P&L responsibility should boost to executive level."""
        from resume_as_code.models.position import Position
        from resume_as_code.models.scope import Scope
        from resume_as_code.models.work_unit import WorkUnit, WorkUnitArchetype

        position = Position(
            id="pos-acme-engineer",
            employer="Acme Corp",
            title="Software Engineer",  # Would normally be MID
            start_date="2020-01",
            scope=Scope(pl_responsibility="$100M"),
        )
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Managed engineering budget",
            problem={"statement": "This is a test problem statement"},
            actions=["Action taken to resolve the issue"],
            outcome={"result": "Successful outcome achieved"},
            archetype=WorkUnitArchetype.LEADERSHIP,
            position_id="pos-acme-engineer",
        )
        assert infer_seniority(wu, position) == ExperienceLevel.EXECUTIVE

    def test_large_revenue_boosts_to_executive(self) -> None:
        """Revenue >= $100M should boost to executive level."""
        from resume_as_code.models.position import Position
        from resume_as_code.models.scope import Scope
        from resume_as_code.models.work_unit import WorkUnit, WorkUnitArchetype

        position = Position(
            id="pos-acme-engineer",
            employer="Acme Corp",
            title="Software Engineer",
            start_date="2020-01",
            scope=Scope(revenue="$500M"),
        )
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Revenue-impacting project",
            problem={"statement": "This is a test problem statement"},
            actions=["Action taken to resolve the issue"],
            outcome={"result": "Successful outcome achieved"},
            archetype=WorkUnitArchetype.STRATEGIC,
            position_id="pos-acme-engineer",
        )
        assert infer_seniority(wu, position) == ExperienceLevel.EXECUTIVE

    def test_large_team_boosts_to_staff(self) -> None:
        """Team size >= 50 should boost to at least STAFF level."""
        from resume_as_code.models.position import Position
        from resume_as_code.models.scope import Scope
        from resume_as_code.models.work_unit import WorkUnit, WorkUnitArchetype

        position = Position(
            id="pos-acme-engineer",
            employer="Acme Corp",
            title="Software Engineer",  # Would normally be MID
            start_date="2020-01",
            scope=Scope(team_size=75),
        )
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Team leadership initiative",
            problem={"statement": "This is a test problem statement"},
            actions=["Action taken to resolve the issue"],
            outcome={"result": "Successful outcome achieved"},
            archetype=WorkUnitArchetype.LEADERSHIP,
            position_id="pos-acme-engineer",
        )
        assert infer_seniority(wu, position) == ExperienceLevel.STAFF

    def test_medium_team_boosts_to_lead(self) -> None:
        """Team size >= 10 should boost to at least LEAD level."""
        from resume_as_code.models.position import Position
        from resume_as_code.models.scope import Scope
        from resume_as_code.models.work_unit import WorkUnit, WorkUnitArchetype

        position = Position(
            id="pos-acme-engineer",
            employer="Acme Corp",
            title="Software Engineer",  # Would normally be MID
            start_date="2020-01",
            scope=Scope(team_size=15),
        )
        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Team project work",
            problem={"statement": "This is a test problem statement"},
            actions=["Action taken to resolve the issue"],
            outcome={"result": "Successful outcome achieved"},
            archetype=WorkUnitArchetype.LEADERSHIP,
            position_id="pos-acme-engineer",
        )
        assert infer_seniority(wu, position) == ExperienceLevel.LEAD

    def test_fallback_to_work_unit_title(self) -> None:
        """Should fall back to work unit title if no position."""
        from resume_as_code.models.work_unit import WorkUnit, WorkUnitArchetype

        wu = WorkUnit(
            id="wu-2024-01-01-test",
            title="Senior engineer led migration project",
            problem={"statement": "This is a test problem statement"},
            actions=["Action taken to resolve the issue"],
            outcome={"result": "Successful outcome achieved"},
            archetype=WorkUnitArchetype.MIGRATION,
        )
        # Should match "senior" in the title
        assert infer_seniority(wu, None) == ExperienceLevel.SENIOR
