"""Position service for managing employment history.

Handles loading, saving, and querying positions from positions.yaml.
Supports grouping by employer and promotion chain detection.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from ruamel.yaml import YAML

from resume_as_code.models.position import Position

if TYPE_CHECKING:
    from collections.abc import Sequence


def format_scope_line(position: Position) -> str | None:
    """Format scope indicators for display in resume.

    Builds a pipe-separated line of leadership metrics.
    Order: P&L first (most important for CTO), then revenue, team size,
    direct reports, budget, geography, customers.

    Args:
        position: Position with optional scope data.

    Returns:
        Formatted scope line (e.g., "$100M P&L | $500M revenue | 200+ engineers")
        or None if no scope data populated.
    """
    if not position.scope:
        return None

    parts: list[str] = []
    scope = position.scope

    # Order: P&L first (AC #3), then revenue, team_size, direct_reports, budget, geography
    if scope.pl_responsibility:
        parts.append(f"{scope.pl_responsibility} P&L")
    if scope.revenue:
        parts.append(f"{scope.revenue} revenue")
    if scope.team_size:
        parts.append(f"{scope.team_size}+ engineers")
    if scope.direct_reports:
        parts.append(f"{scope.direct_reports} direct reports")
    if scope.budget:
        parts.append(f"{scope.budget} budget")
    if scope.geography:
        parts.append(scope.geography)
    if scope.customers:
        parts.append(scope.customers)

    return " | ".join(parts) if parts else None


class PositionService:
    """Service for managing employment positions."""

    def __init__(self, positions_path: Path | None = None) -> None:
        """Initialize the position service.

        Args:
            positions_path: Path to positions.yaml file. Defaults to positions.yaml
                           in current directory.
        """
        self.positions_path = positions_path or Path("positions.yaml")
        self._positions: dict[str, Position] | None = None

    def load_positions(self) -> dict[str, Position]:
        """Load positions from YAML file.

        Returns:
            Dictionary mapping position ID to Position object.
            Returns empty dict if file doesn't exist or is empty.
        """
        if self._positions is not None:
            return self._positions

        if not self.positions_path.exists():
            self._positions = {}
            return self._positions

        yaml = YAML()
        with open(self.positions_path) as f:
            data = yaml.load(f)

        if not data:
            self._positions = {}
            return self._positions

        positions_data = data.get("positions", {})
        self._positions = {}

        for pos_id, pos_data in positions_data.items():
            # Convert to dict if needed (ruamel returns CommentedMap)
            pos_dict = dict(pos_data)
            pos_dict["id"] = pos_id
            self._positions[pos_id] = Position.model_validate(pos_dict)

        return self._positions

    def get_position(self, position_id: str) -> Position | None:
        """Get a position by ID.

        Args:
            position_id: The position ID to look up.

        Returns:
            Position object if found, None otherwise.
        """
        positions = self.load_positions()
        return positions.get(position_id)

    def position_exists(self, position_id: str) -> bool:
        """Check if a position ID exists.

        Args:
            position_id: The position ID to check.

        Returns:
            True if position exists, False otherwise.
        """
        return position_id in self.load_positions()

    def group_by_employer(self, positions: Sequence[Position]) -> dict[str, list[Position]]:
        """Group positions by employer.

        Args:
            positions: Sequence of Position objects to group.

        Returns:
            Dictionary mapping employer name to list of positions,
            sorted by start_date descending within each employer.
        """
        groups: dict[str, list[Position]] = {}

        for pos in positions:
            if pos.employer not in groups:
                groups[pos.employer] = []
            groups[pos.employer].append(pos)

        # Sort positions within each employer by start_date descending
        for positions_list in groups.values():
            positions_list.sort(key=lambda p: p.start_date, reverse=True)

        return groups

    def get_promotion_chain(self, position_id: str) -> list[Position]:
        """Get the promotion chain for a position.

        Traces back through promoted_from references to build
        the complete career progression at an employer.

        Args:
            position_id: The position ID to get chain for.

        Returns:
            List from earliest to most recent position in the chain.
            Empty list if position not found.

        Note:
            Includes cycle detection to prevent infinite loops from
            malformed promoted_from references.
        """
        positions = self.load_positions()
        chain: list[Position] = []
        visited: set[str] = set()

        current_id: str | None = position_id
        while current_id and current_id not in visited:
            pos = positions.get(current_id)
            if not pos:
                break
            visited.add(current_id)
            chain.append(pos)
            current_id = pos.promoted_from

        return list(reversed(chain))

    def suggest_position_for_date(self, target_date: str) -> Position | None:
        """Suggest a position whose date range contains the target date.

        Useful for auto-suggesting positions during work unit creation
        when the work happened within a position's tenure.

        Args:
            target_date: Date string in YYYY-MM or YYYY-MM-DD format.

        Returns:
            Most recent matching Position, or None if no match.
        """
        positions = self.load_positions()
        if not positions:
            return None

        # Normalize to YYYY-MM for comparison
        target_ym = target_date[:7] if len(target_date) >= 7 else target_date

        matching: list[Position] = []
        for pos in positions.values():
            start = pos.start_date
            end = pos.end_date or "9999-12"  # Current positions match any future date

            if start <= target_ym <= end:
                matching.append(pos)

        if not matching:
            return None

        # Return most recent matching position (by start_date descending)
        matching.sort(key=lambda p: p.start_date, reverse=True)
        return matching[0]

    def save_position(self, position: Position) -> None:
        """Save a position to the positions file.

        Creates the file if it doesn't exist, or adds to existing file.

        Args:
            position: The Position to save.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        # Load existing data
        if self.positions_path.exists():
            with open(self.positions_path) as f:
                data = yaml.load(f) or {}
        else:
            data = {"schema_version": "1.0.0", "positions": {}}

        if "positions" not in data:
            data["positions"] = {}

        # Add position (exclude 'id' from stored data, exclude None values)
        pos_data = position.model_dump(exclude={"id"}, exclude_none=True)
        data["positions"][position.id] = pos_data

        # Save
        with open(self.positions_path, "w") as f:
            yaml.dump(data, f)

        # Clear cache
        self._positions = None

    def remove_position(self, position_id: str) -> bool:
        """Remove a position by ID.

        Args:
            position_id: The position ID to remove.

        Returns:
            True if position was removed, False if not found.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        # Load existing data
        if not self.positions_path.exists():
            return False

        with open(self.positions_path) as f:
            data = yaml.load(f) or {}

        if "positions" not in data or position_id not in data["positions"]:
            return False

        # Remove the position
        del data["positions"][position_id]

        # Save
        with open(self.positions_path, "w") as f:
            yaml.dump(data, f)

        # Clear cache
        self._positions = None
        return True

    def find_positions_by_query(self, query: str) -> list[Position]:
        """Find positions matching a query string.

        Searches employer and title fields (case-insensitive partial match).

        Args:
            query: Search string to match against employer or title.

        Returns:
            List of matching Position objects.
        """
        positions = self.load_positions()
        query_lower = query.lower().strip()

        return [
            pos
            for pos in positions.values()
            if query_lower in pos.employer.lower()
            or query_lower in pos.title.lower()
            or query_lower in pos.id.lower()
        ]

    @staticmethod
    def filter_by_years(positions: list[Position], years: int) -> list[Position]:
        """Filter positions to those active within the last N years.

        A position is included if:
        - end_date is None (current position), OR
        - end_date >= (today - years)

        This supports the --years CLI flag (Story 13.2) for limiting
        work history to recent experience.

        Args:
            positions: List of positions to filter.
            years: Number of years to look back from today.

        Returns:
            List of positions that ended within the last N years,
            or are currently active.
        """
        # Calculate cutoff date in YYYY-MM format for comparison
        today = date.today()
        cutoff_year = today.year - years
        cutoff_month = today.month
        cutoff_ym = f"{cutoff_year:04d}-{cutoff_month:02d}"

        return [
            pos
            for pos in positions
            if pos.end_date is None  # Current positions always included
            or pos.end_date >= cutoff_ym  # end_date is YYYY-MM, sortable strings
        ]
