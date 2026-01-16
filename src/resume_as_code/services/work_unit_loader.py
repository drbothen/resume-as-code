"""Work Unit loader service with position validation and attachment.

Provides centralized loading of work units with position reference validation
and efficient Position object attachment for direct access.
"""

from __future__ import annotations

import logging
from difflib import get_close_matches
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError as PydanticValidationError
from ruamel.yaml import YAML

from resume_as_code.models.errors import ValidationError
from resume_as_code.models.work_unit import WorkUnit

if TYPE_CHECKING:
    from resume_as_code.models.position import Position

logger = logging.getLogger(__name__)


class WorkUnitLoader:
    """Loads and validates Work Units from YAML files.

    Provides methods to load work units with optional position validation
    and attachment for efficient access.
    """

    def __init__(self, work_units_dir: Path) -> None:
        """Initialize loader.

        Args:
            work_units_dir: Directory containing work unit YAML files.
        """
        self.work_units_dir = work_units_dir
        self._yaml = YAML()
        self._yaml.preserve_quotes = True

    def load_all(self) -> list[WorkUnit]:
        """Load all work units from directory.

        Returns:
            List of WorkUnit objects sorted alphabetically by file path.

        Raises:
            ValidationError: If any work unit fails schema validation.
        """
        work_units: list[WorkUnit] = []

        if not self.work_units_dir.exists():
            logger.debug("Work units directory does not exist: %s", self.work_units_dir)
            return work_units

        for yaml_file in sorted(self.work_units_dir.glob("*.yaml")):
            if yaml_file.name.startswith("."):
                logger.debug("Skipping hidden file: %s", yaml_file.name)
                continue

            logger.debug("Loading work unit: %s", yaml_file.name)
            with yaml_file.open() as f:
                data = self._yaml.load(f)

            try:
                wu = WorkUnit.model_validate(data)
                work_units.append(wu)
            except PydanticValidationError as e:
                raise ValidationError(
                    message=f"Invalid work unit schema: {e}",
                    path=str(yaml_file),
                    suggestion="Check the work unit YAML file for schema errors",
                ) from e

        logger.info("Loaded %d work units from %s", len(work_units), self.work_units_dir)
        return work_units

    def load_with_positions(
        self,
        positions: dict[str, Position],
    ) -> list[WorkUnit]:
        """Load work units with position validation and attachment.

        Args:
            positions: Dictionary of position_id -> Position.

        Returns:
            List of WorkUnit objects with Position attached where applicable.

        Raises:
            ValidationError: If any position_id references an invalid position.
        """
        work_units = self.load_all()
        invalid_refs: list[tuple[str, str]] = []  # (wu_id, position_id)

        for wu in work_units:
            if wu.position_id is None:
                continue

            if wu.position_id not in positions:
                invalid_refs.append((wu.id, wu.position_id))
            else:
                wu.attach_position(positions[wu.position_id])
                logger.debug("Attached position %s to work unit %s", wu.position_id, wu.id)

        if invalid_refs:
            # Build helpful error message with suggestions
            suggestions = self._suggest_positions(invalid_refs, set(positions.keys()))
            msg_parts = ["Invalid position_id references found:"]

            for wu_id, pos_id in invalid_refs:
                msg = f"\n  - {wu_id}: position_id={pos_id!r}"
                if pos_id in suggestions:
                    msg += f" (did you mean: {suggestions[pos_id]}?)"
                msg_parts.append(msg)

            msg_parts.append("\n\nRun 'resume list positions' to see valid position IDs")
            msg_parts.append("\nOr create a new position with 'resume new position'")

            raise ValidationError(
                message="".join(msg_parts),
                suggestion="Fix position_id references or create missing positions",
            )

        return work_units

    def _suggest_positions(
        self,
        invalid_refs: list[tuple[str, str]],
        valid_ids: set[str],
    ) -> dict[str, str]:
        """Suggest similar position IDs for invalid references.

        Uses difflib's get_close_matches for simple string similarity.

        Args:
            invalid_refs: List of (wu_id, invalid_position_id) tuples.
            valid_ids: Set of valid position IDs.

        Returns:
            Dictionary mapping invalid_id -> suggested_id (if found).
        """
        suggestions: dict[str, str] = {}

        if not valid_ids:
            return suggestions

        for _, pos_id in invalid_refs:
            matches = get_close_matches(pos_id, list(valid_ids), n=1, cutoff=0.6)
            if matches:
                suggestions[pos_id] = matches[0]
                logger.debug("Suggested %s as alternative for %s", matches[0], pos_id)

        return suggestions

    def validate_position_references(
        self,
        positions: dict[str, Position],
    ) -> tuple[bool, list[tuple[str, str]]]:
        """Validate position_id references without attaching positions.

        Useful for early validation before proceeding with dictionary-based flow.

        Args:
            positions: Dictionary of position_id -> Position.

        Returns:
            Tuple of (is_valid, invalid_refs) where invalid_refs is list of
            (work_unit_id, invalid_position_id) tuples.
        """
        work_units = self.load_all()
        invalid_refs: list[tuple[str, str]] = []

        for wu in work_units:
            if wu.position_id is not None and wu.position_id not in positions:
                invalid_refs.append((wu.id, wu.position_id))

        return (len(invalid_refs) == 0, invalid_refs)
