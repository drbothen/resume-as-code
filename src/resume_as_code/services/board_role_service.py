"""Board role service for managing board and advisory roles.

Handles loading, saving, and querying board roles from .resume.yaml config.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from resume_as_code.models.board_role import BoardRole


class BoardRoleService:
    """Service for managing board and advisory roles."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the board role service.

        Args:
            config_path: Path to .resume.yaml config file. Defaults to .resume.yaml
                        in current directory.
        """
        self.config_path = config_path or Path(".resume.yaml")
        self._board_roles: list[BoardRole] | None = None

    def load_board_roles(self) -> list[BoardRole]:
        """Load board roles from config file.

        Returns:
            List of BoardRole objects.
            Returns empty list if file doesn't exist or has no board_roles.
        """
        if self._board_roles is not None:
            return self._board_roles

        if not self.config_path.exists():
            self._board_roles = []
            return self._board_roles

        yaml = YAML()
        with open(self.config_path) as f:
            data = yaml.load(f)

        if not data:
            self._board_roles = []
            return self._board_roles

        roles_data = data.get("board_roles", [])
        self._board_roles = []

        for role_data in roles_data:
            # Convert to dict if needed (ruamel returns CommentedMap)
            role_dict = dict(role_data) if hasattr(role_data, "items") else role_data
            self._board_roles.append(BoardRole.model_validate(role_dict))

        return self._board_roles

    def find_board_role(self, organization: str, role: str | None = None) -> BoardRole | None:
        """Find existing board role by organization and optional role title.

        Case-insensitive, whitespace-normalized matching.

        Args:
            organization: Organization name to search for.
            role: Optional role title to match.

        Returns:
            Matching BoardRole if found, None otherwise.
        """
        board_roles = self.load_board_roles()
        org_lower = organization.lower().strip()
        role_lower = role.lower().strip() if role else None

        for br in board_roles:
            if br.organization.lower().strip() == org_lower and (
                role_lower is None or br.role.lower().strip() == role_lower
            ):
                return br

        return None

    def save_board_role(self, board_role: BoardRole) -> None:
        """Save a board role to the config file.

        Creates the file if it doesn't exist, or adds to existing file.

        Args:
            board_role: The BoardRole to save.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        # Load existing data
        if self.config_path.exists():
            with open(self.config_path) as f:
                data = yaml.load(f) or {}
        else:
            data = {}

        if "board_roles" not in data:
            data["board_roles"] = []

        # Add board role (exclude None values and default display)
        role_data = board_role.model_dump(exclude_none=True)
        # Remove 'display' if it's True (default)
        if role_data.get("display") is True:
            del role_data["display"]
        data["board_roles"].append(role_data)

        # Save
        with open(self.config_path, "w") as f:
            yaml.dump(data, f)

        # Clear cache
        self._board_roles = None

    def remove_board_role(self, organization: str) -> bool:
        """Remove a board role by organization (case-insensitive partial match).

        Args:
            organization: Full or partial organization name to match.

        Returns:
            True if board role was removed, False if not found.

        Note:
            Uses case-insensitive partial matching. If multiple board roles
            match, the first match is removed.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        # Load existing data
        if not self.config_path.exists():
            return False

        with open(self.config_path) as f:
            data = yaml.load(f) or {}

        if "board_roles" not in data or not data["board_roles"]:
            return False

        # Find matching board role index
        org_lower = organization.lower().strip()
        remove_idx = None
        for idx, role_data in enumerate(data["board_roles"]):
            role_org = role_data.get("organization", "")
            if org_lower in role_org.lower():
                remove_idx = idx
                break

        if remove_idx is None:
            return False

        # Remove the board role
        del data["board_roles"][remove_idx]

        # Save
        with open(self.config_path, "w") as f:
            yaml.dump(data, f)

        # Clear cache
        self._board_roles = None
        return True

    def find_board_roles_by_organization(self, organization: str) -> list[BoardRole]:
        """Find all board roles matching a partial organization name.

        Case-insensitive partial matching.

        Args:
            organization: Partial organization name to search for.

        Returns:
            List of matching BoardRole objects.
        """
        board_roles = self.load_board_roles()
        org_lower = organization.lower().strip()

        return [br for br in board_roles if org_lower in br.organization.lower()]
