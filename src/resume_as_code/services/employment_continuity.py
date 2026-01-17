"""Employment continuity service for gap detection and timeline management.

Ensures employment timeline continuity in tailored resumes by:
1. Guaranteeing minimum representation per position (minimum_bullet mode)
2. Detecting and warning about employment gaps (allow_gaps mode)

Story 7.20: Employment Continuity & Gap Detection
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from resume_as_code.models.position import Position
    from resume_as_code.models.work_unit import WorkUnit

EmploymentContinuityMode = Literal["minimum_bullet", "allow_gaps"]


@dataclass
class EmploymentGap:
    """Detected gap in employment timeline.

    Attributes:
        start_date: Start of the gap (position start date).
        end_date: End of the gap (position end date).
        duration_months: Duration of the gap in months.
        missing_position_id: ID of the excluded position.
        missing_employer: Employer name for display.
    """

    start_date: date
    end_date: date
    duration_months: int
    missing_position_id: str
    missing_employer: str


class EmploymentContinuityService:
    """Ensure employment timeline continuity in tailored resumes.

    Two modes of operation:
    - minimum_bullet: Always include at least one work unit per position
    - allow_gaps: Pure relevance filtering with gap detection and warnings
    """

    def __init__(
        self,
        mode: EmploymentContinuityMode = "minimum_bullet",
        min_gap_months: int = 3,
    ) -> None:
        """Initialize the service.

        Args:
            mode: Continuity enforcement mode.
            min_gap_months: Minimum gap duration to report (default 3).
        """
        self.mode = mode
        self.min_gap_months = min_gap_months

    def ensure_continuity(
        self,
        positions: list[Position],
        selected_work_units: list[WorkUnit],
        all_work_units: list[WorkUnit],
        scores: dict[str, float] | None = None,
    ) -> list[WorkUnit]:
        """Ensure at least one work unit per position if mode is minimum_bullet.

        Args:
            positions: All positions in timeline.
            selected_work_units: Work units selected by relevance scoring.
            all_work_units: All available work units.
            scores: Optional relevance scores for tiebreaking.

        Returns:
            Updated list of work units with continuity guaranteed.
        """
        if self.mode == "allow_gaps":
            return selected_work_units

        # Find positions with no selected work units
        selected_position_ids = {wu.position_id for wu in selected_work_units if wu.position_id}

        result = list(selected_work_units)

        for position in positions:
            if position.id not in selected_position_ids:
                # Find highest-scoring work unit for this position
                position_wus = [wu for wu in all_work_units if wu.position_id == position.id]
                if position_wus:
                    if scores:
                        best_wu = max(
                            position_wus,
                            key=lambda wu: scores.get(wu.id, 0),
                        )
                    else:
                        best_wu = position_wus[0]
                    result.append(best_wu)

        return result

    def detect_gaps(
        self,
        positions: list[Position],
        selected_work_units: list[WorkUnit],
    ) -> list[EmploymentGap]:
        """Detect employment gaps in the filtered resume.

        Args:
            positions: All positions in timeline.
            selected_work_units: Work units selected for resume.

        Returns:
            List of detected employment gaps >= min_gap_months.
        """
        # Get positions that have work units in the selection
        included_position_ids = {wu.position_id for wu in selected_work_units if wu.position_id}
        excluded_positions = [p for p in positions if p.id not in included_position_ids]

        if not excluded_positions:
            return []

        gaps: list[EmploymentGap] = []

        for excluded in excluded_positions:
            exc_start = self._parse_date(excluded.start_date)
            exc_end = self._parse_date(excluded.end_date) or date.today()

            if exc_start is None:
                continue

            gap_months = self._months_between(exc_start, exc_end)

            if gap_months >= self.min_gap_months:
                gaps.append(
                    EmploymentGap(
                        start_date=exc_start,
                        end_date=exc_end,
                        duration_months=gap_months,
                        missing_position_id=excluded.id,
                        missing_employer=excluded.employer,
                    )
                )

        return gaps

    def format_gap_warning(self, gaps: list[EmploymentGap]) -> str:
        """Format gap warnings for Rich console display.

        Args:
            gaps: List of detected employment gaps.

        Returns:
            Formatted warning string with Rich markup.
        """
        if not gaps:
            return ""

        lines = ["[yellow]⚠️  Employment Gap Detected[/yellow]"]
        for gap in gaps:
            lines.append(
                f"    Missing: [bold]{gap.missing_employer}[/bold] "
                f"({gap.start_date.strftime('%Y-%m')} to {gap.end_date.strftime('%Y-%m')})"
            )
            lines.append(f"    Gap: {gap.duration_months} months")
        lines.append("")
        lines.append(
            "    [dim]Suggestion: Use --no-allow-gaps to include 1 bullet per position[/dim]"
        )

        return "\n".join(lines)

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse YYYY-MM date string to date object.

        Args:
            date_str: Date string in YYYY-MM format, or None.

        Returns:
            Date object set to first of month, or None if input is None.
        """
        if not date_str:
            return None
        year, month = date_str.split("-")
        return date(int(year), int(month), 1)

    def _months_between(self, start: date, end: date) -> int:
        """Calculate months between two dates.

        Args:
            start: Start date.
            end: End date.

        Returns:
            Number of months between dates.
        """
        return (end.year - start.year) * 12 + (end.month - start.month)
