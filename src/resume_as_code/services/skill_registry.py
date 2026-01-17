"""SkillRegistry service for skill name normalization and alias lookup."""

from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from pathlib import Path

    from resume_as_code.models.config import ONetConfig
    from resume_as_code.models.skill_entry import SkillEntry
    from resume_as_code.services.onet_service import ONetService

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Registry for skill name normalization and alias lookup.

    Maps skill aliases to canonical names for consistent resume rendering
    and improved JD matching. Supports passthrough for unknown skills.

    Example:
        >>> registry = SkillRegistry.load_default()
        >>> registry.normalize("k8s")
        'Kubernetes'
        >>> registry.get_aliases("ts")
        {'typescript', 'ts'}

    """

    def __init__(
        self,
        entries: list[SkillEntry],
        onet_service: ONetService | None = None,
        user_skills_path: Path | None = None,
    ) -> None:
        """Initialize registry with skill entries.

        Args:
            entries: List of SkillEntry objects.
            onet_service: Optional O*NET service for external skill lookup.
            user_skills_path: Optional path to user skills file for persistence.

        """
        self._entries = entries
        self._onet_service = onet_service
        self._user_skills_path = user_skills_path
        self._by_alias: dict[str, SkillEntry] = {}

        for entry in entries:
            # Map canonical name (lowercase) to entry
            canonical_lower = entry.canonical.lower()
            if canonical_lower in self._by_alias:
                existing = self._by_alias[canonical_lower].canonical
                warnings.warn(
                    f"Skill alias collision: '{canonical_lower}' maps to both "
                    f"'{existing}' and '{entry.canonical}'. Using '{entry.canonical}'.",
                    UserWarning,
                    stacklevel=2,
                )
            self._by_alias[canonical_lower] = entry
            # Map all aliases to entry
            for alias in entry.aliases:
                alias_lower = alias.lower()
                if alias_lower in self._by_alias:
                    existing = self._by_alias[alias_lower].canonical
                    if existing != entry.canonical:
                        warnings.warn(
                            f"Skill alias collision: '{alias_lower}' maps to both "
                            f"'{existing}' and '{entry.canonical}'. Using '{entry.canonical}'.",
                            UserWarning,
                            stacklevel=2,
                        )
                self._by_alias[alias_lower] = entry

    @property
    def has_onet_service(self) -> bool:
        """Check if O*NET service is configured for skill discovery.

        Returns:
            True if O*NET service is available, False otherwise.
        """
        return self._onet_service is not None

    def normalize(self, skill: str) -> str:
        """Normalize skill name to canonical form.

        Args:
            skill: Skill name or alias.

        Returns:
            Canonical name if found, otherwise original string (passthrough).

        """
        entry = self._by_alias.get(skill.lower())
        return entry.canonical if entry else skill

    def get_aliases(self, skill: str) -> set[str]:
        """Get all aliases for a skill including canonical name.

        Args:
            skill: Skill name or alias.

        Returns:
            Set of all names (canonical + aliases) in lowercase,
            or {skill.lower()} if not found.

        """
        entry = self._by_alias.get(skill.lower())
        if entry:
            return {entry.canonical.lower()} | set(entry.aliases)
        return {skill.lower()}

    def get_onet_code(self, skill: str) -> str | None:
        """Get O*NET code for a skill.

        Args:
            skill: Skill name or alias.

        Returns:
            O*NET element ID if mapped, otherwise None.

        """
        entry = self._by_alias.get(skill.lower())
        return entry.onet_code if entry else None

    def lookup_and_cache(self, skill: str) -> SkillEntry | None:
        """Lookup skill in O*NET and cache result.

        Only called for skills not in local registry. If found in O*NET,
        creates a new SkillEntry and adds it to the registry.

        Args:
            skill: Skill name to lookup.

        Returns:
            SkillEntry if found (either existing or from O*NET), None otherwise.

        """
        from resume_as_code.models.skill_entry import SkillEntry

        # Check if already in registry
        existing = self._by_alias.get(skill.lower())
        if existing is not None:
            return existing

        # No O*NET service configured
        if self._onet_service is None:
            return None

        # Search O*NET for occupations matching skill
        occupations = self._onet_service.search_occupations(skill)
        if not occupations:
            logger.debug(f"O*NET: no occupations found for '{skill}'")
            return None

        # Get skills from top occupation
        top_occ = occupations[0]
        onet_skills = self._onet_service.get_occupation_skills(top_occ.code)

        # Find best match - skill name contains query
        skill_lower = skill.lower()
        for onet_skill in onet_skills:
            if skill_lower in onet_skill.name.lower():
                # Create new entry
                aliases: list[str] = []
                if skill_lower != onet_skill.name.lower():
                    aliases.append(skill_lower)

                entry = SkillEntry(
                    canonical=onet_skill.name,
                    aliases=aliases,
                    onet_code=onet_skill.id,
                )
                self._add_entry(entry)
                logger.info(
                    f"O*NET: discovered skill '{onet_skill.name}' "
                    f"(code: {onet_skill.id}) for query '{skill}'"
                )
                return entry

        logger.debug(f"O*NET: no matching skill found in '{top_occ.title}' for '{skill}'")
        return None

    def _add_entry(self, entry: SkillEntry, persist: bool = True) -> None:
        """Add a skill entry to the registry.

        Args:
            entry: SkillEntry to add.
            persist: Whether to persist to user skills file (default True).

        """
        self._entries.append(entry)

        # Map canonical name
        canonical_lower = entry.canonical.lower()
        self._by_alias[canonical_lower] = entry

        # Map all aliases
        for alias in entry.aliases:
            alias_lower = alias.lower()
            self._by_alias[alias_lower] = entry

        # Persist to user skills file if configured (AC #5: persist for future use)
        if persist and self._user_skills_path is not None:
            self._persist_entry(entry)

    def _persist_entry(self, entry: SkillEntry) -> None:
        """Persist a single skill entry to user skills file.

        Appends the entry to the user's skills.yaml file, creating it if needed.
        Uses ruamel.yaml to preserve formatting and comments.

        Args:
            entry: SkillEntry to persist.

        """
        from ruamel.yaml import YAML

        path = self._user_skills_path
        if path is None:
            return

        yaml_handler = YAML()
        yaml_handler.preserve_quotes = True
        yaml_handler.default_flow_style = False

        # Load existing data or create new structure
        if path.exists():
            try:
                with path.open() as f:
                    data = yaml_handler.load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to read user skills file '{path}': {e}")
                data = {}
        else:
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {}

        # Ensure skills list exists
        if "skills" not in data:
            data["skills"] = []

        # Add entry as dict (exclude None values for cleaner YAML)
        entry_dict: dict[str, str | list[str] | None] = {
            "canonical": entry.canonical,
        }
        if entry.aliases:
            entry_dict["aliases"] = entry.aliases
        if entry.category:
            entry_dict["category"] = entry.category
        if entry.onet_code:
            entry_dict["onet_code"] = entry.onet_code

        data["skills"].append(entry_dict)

        # Write back
        try:
            with path.open("w") as f:
                yaml_handler.dump(data, f)
            logger.info(f"Persisted skill '{entry.canonical}' to '{path}'")
        except Exception as e:
            logger.warning(f"Failed to persist skill to '{path}': {e}")

    @classmethod
    def load_from_yaml(cls, path: Path) -> SkillRegistry:
        """Load registry from YAML file.

        Args:
            path: Path to skills.yaml file.

        Returns:
            SkillRegistry instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the YAML file is malformed or invalid.

        """
        from pathlib import Path as PathType

        from resume_as_code.models.skill_entry import SkillEntry

        # Ensure path is a Path object for runtime
        if not isinstance(path, PathType):
            path = PathType(path)

        try:
            with path.open() as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in skills file '{path}': {e}") from e

        if data is None:
            data = {}

        entries = [SkillEntry(**entry) for entry in data.get("skills", [])]
        return cls(entries)

    @classmethod
    def load_default(cls) -> SkillRegistry:
        """Load the bundled default skills registry.

        Uses importlib.resources to access package data files,
        which works across all installation methods.

        Returns:
            SkillRegistry with default skills.

        """
        import importlib.resources

        from resume_as_code.models.skill_entry import SkillEntry

        # Access bundled data file using importlib.resources
        data_file = importlib.resources.files("resume_as_code") / "data" / "skills.yaml"
        content = data_file.read_text()
        data = yaml.safe_load(content)

        entries = [SkillEntry(**entry) for entry in data.get("skills", [])]
        return cls(entries)

    @classmethod
    def load_with_onet(
        cls,
        onet_config: ONetConfig | None = None,
    ) -> SkillRegistry:
        """Load registry with optional O*NET service for skill discovery.

        Factory method that creates a SkillRegistry with O*NET integration
        when configured. Falls back to local-only registry when O*NET is
        unavailable or not configured.

        If no config is provided, automatically checks for ONET_API_KEY
        environment variable and enables O*NET if present.

        Args:
            onet_config: O*NET configuration with API key. If None, creates
                default config that checks ONET_API_KEY env var.

        Returns:
            SkillRegistry with O*NET service if configured, otherwise
            local-only registry.

        Example:
            >>> from resume_as_code.config import get_config
            >>> config = get_config()
            >>> registry = SkillRegistry.load_with_onet(config.onet)
            >>> registry.normalize("k8s")
            'Kubernetes'

        """
        import importlib.resources
        from pathlib import Path

        from resume_as_code.models.skill_entry import SkillEntry
        from resume_as_code.services.onet_service import ONetService

        # Load bundled default skills
        data_file = importlib.resources.files("resume_as_code") / "data" / "skills.yaml"
        content = data_file.read_text()
        data = yaml.safe_load(content)
        entries = [SkillEntry(**entry) for entry in data.get("skills", [])]

        # Create O*NET service if configured
        # If no config provided, create default which picks up ONET_API_KEY env var
        from resume_as_code.models.config import ONetConfig

        effective_config = onet_config if onet_config is not None else ONetConfig()

        onet_service: ONetService | None = None
        user_skills_path: Path | None = None

        if effective_config.is_configured:
            onet_service = ONetService(effective_config)
            # Set up user skills persistence path
            user_skills_path = Path.home() / ".config" / "resume-as-code" / "user-skills.yaml"
            logger.info("O*NET service enabled for skill discovery")
        else:
            logger.debug("O*NET not configured, using local registry only")

        return cls(entries, onet_service=onet_service, user_skills_path=user_skills_path)
