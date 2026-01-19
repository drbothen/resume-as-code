"""Board role service for managing board and advisory roles.

Handles loading, saving, and querying board roles.
Story 9.2: Uses data_loader for cascading lookup (separate file or embedded).
Story 11.2: Added directory mode support via ShardedLoader.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from resume_as_code.data_loader import get_storage_mode
from resume_as_code.data_loader import load_board_roles as dl_load_board_roles
from resume_as_code.models.board_role import BoardRole
from resume_as_code.services.sharded_loader import ShardedLoader

# Default filename for separated data structure (Story 9.2)
DEFAULT_BOARD_ROLES_FILE = "board-roles.yaml"
DEFAULT_BOARD_ROLES_DIR = "board-roles"


class BoardRoleService:
    """Service for managing board and advisory roles."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the board role service.

        Args:
            config_path: Path to .resume.yaml config file. Defaults to .resume.yaml
                        in current directory. Used to determine project root.
        """
        self.config_path = config_path or Path(".resume.yaml")
        self.project_path = self.config_path.parent
        self._board_roles: list[BoardRole] | None = None

    def load_board_roles(self) -> list[BoardRole]:
        """Load board roles using data_loader cascading lookup.

        Story 9.2: Supports both separated files and embedded data.

        Returns:
            List of BoardRole objects.
            Returns empty list if no board roles found.
        """
        if self._board_roles is not None:
            return self._board_roles

        # Use data_loader for cascading lookup (Story 9.2)
        self._board_roles = dl_load_board_roles(self.project_path)
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

    def _uses_separated_format(self) -> bool:
        """Check if project uses separated data files (v3 format).

        Returns:
            True if board-roles.yaml exists, False otherwise.
        """
        return (self.project_path / DEFAULT_BOARD_ROLES_FILE).exists()

    def save_board_role(self, board_role: BoardRole) -> Path | None:
        """Save a board role to the appropriate location.

        Story 9.2: Writes to board-roles.yaml if it exists (v3 format),
        otherwise writes to .resume.yaml (v2 format).
        Story 11.2: Supports directory mode with per-item files.

        Args:
            board_role: The BoardRole to save.

        Returns:
            Path to the saved file (directory mode), or None (file/embedded mode).
        """
        mode, path = get_storage_mode(self.project_path, "board_roles")

        if mode == "dir":
            # Story 11.2: Directory mode - save to individual file
            dir_path = path or (self.project_path / DEFAULT_BOARD_ROLES_DIR)
            loader = ShardedLoader(dir_path, BoardRole)
            item_id = loader.generate_id(board_role)
            saved_path = loader.save(board_role, item_id)
            self._board_roles = None
            return saved_path

        # File or embedded mode - use existing logic
        yaml = YAML()
        yaml.default_flow_style = False

        # Prepare board role data
        role_data = board_role.model_dump(exclude_none=True)
        # Remove 'display' if it's True (default)
        if role_data.get("display") is True:
            del role_data["display"]

        if mode == "file":
            # v3 format: write to board-roles.yaml (list format)
            data_path = path or (self.project_path / DEFAULT_BOARD_ROLES_FILE)
            if data_path.exists():
                with open(data_path) as f:
                    roles_list = yaml.load(f) or []
            else:
                roles_list = []

            roles_list.append(role_data)

            with open(data_path, "w") as f:
                yaml.dump(roles_list, f)
        else:
            # Embedded mode: write to .resume.yaml
            if self.config_path.exists():
                with open(self.config_path) as f:
                    data = yaml.load(f) or {}
            else:
                data = {}

            if "board_roles" not in data:
                data["board_roles"] = []

            data["board_roles"].append(role_data)

            with open(self.config_path, "w") as f:
                yaml.dump(data, f)

        # Clear cache
        self._board_roles = None
        return None

    def remove_board_role(self, organization: str) -> bool:
        """Remove a board role by organization (case-insensitive partial match).

        Story 9.2: Removes from board-roles.yaml if it exists (v3 format),
        otherwise removes from .resume.yaml (v2 format).
        Story 11.2: Supports directory mode with per-item files.

        Args:
            organization: Full or partial organization name to match.

        Returns:
            True if board role was removed, False if not found.

        Note:
            Uses case-insensitive partial matching. If multiple board roles
            match, the first match is removed.
        """
        mode, path = get_storage_mode(self.project_path, "board_roles")
        org_lower = organization.lower().strip()

        if mode == "dir":
            # Story 11.2: Directory mode - find and remove file
            dir_path = path or (self.project_path / DEFAULT_BOARD_ROLES_DIR)
            loader = ShardedLoader(dir_path, BoardRole)
            roles = loader.load_all()

            # Find matching board role with its source file
            for role in roles:
                if org_lower in role.organization.lower():
                    source_file = getattr(role, "_source_file", None)
                    if source_file:
                        item_id = source_file.stem
                        if loader.remove(item_id):
                            self._board_roles = None
                            return True
                    return False
            return False

        yaml = YAML()
        yaml.default_flow_style = False

        if mode == "file":
            # v3 format: remove from board-roles.yaml
            data_path = path or (self.project_path / DEFAULT_BOARD_ROLES_FILE)
            if not data_path.exists():
                return False

            with open(data_path) as f:
                roles_list = yaml.load(f) or []

            if not roles_list:
                return False

            # Find matching board role index
            remove_idx = None
            for idx, role_data in enumerate(roles_list):
                role_org = role_data.get("organization", "")
                if org_lower in role_org.lower():
                    remove_idx = idx
                    break

            if remove_idx is None:
                return False

            del roles_list[remove_idx]

            with open(data_path, "w") as f:
                yaml.dump(roles_list, f)
        else:
            # Embedded mode: remove from .resume.yaml
            if not self.config_path.exists():
                return False

            with open(self.config_path) as f:
                data = yaml.load(f) or {}

            if "board_roles" not in data or not data["board_roles"]:
                return False

            # Find matching board role index
            remove_idx = None
            for idx, role_data in enumerate(data["board_roles"]):
                role_org = role_data.get("organization", "")
                if org_lower in role_org.lower():
                    remove_idx = idx
                    break

            if remove_idx is None:
                return False

            del data["board_roles"][remove_idx]

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
