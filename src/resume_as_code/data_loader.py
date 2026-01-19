"""Unified data access layer for Resume as Code.

Story 9.2: Provides functions to load resume data from either dedicated
files or embedded in .resume.yaml for backward compatibility.

Story 11.2: Added three-tier loading fallback with directory mode support.

The lookup order for each data type is:
1. Directory from *_dir config (if specified) - highest priority (Story 11.2)
2. Default directory (e.g., certifications/) - if exists
3. Custom file path from data_paths configuration (if specified)
4. Default dedicated file (e.g., certifications.yaml)
5. Embedded data in .resume.yaml (legacy/backward compatible)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Literal, TypeVar

import yaml
from pydantic import BaseModel, TypeAdapter

from resume_as_code.models.board_role import BoardRole
from resume_as_code.models.certification import Certification
from resume_as_code.models.config import DataPaths, ProfileConfig
from resume_as_code.models.education import Education
from resume_as_code.models.publication import Publication
from resume_as_code.services.sharded_loader import ShardedLoader

logger = logging.getLogger(__name__)

# Type variable for list data loading
T = TypeVar("T", bound=BaseModel)

# Storage mode for three-tier fallback
StorageMode = Literal["dir", "file", "embedded"]


def _load_yaml_safe(path: Path) -> dict[str, Any] | list[Any] | None:
    """Load YAML file safely, returning None if file doesn't exist.

    Args:
        path: Path to YAML file.

    Returns:
        Parsed YAML content or None if file doesn't exist.
    """
    if not path.exists():
        return None
    with path.open() as f:
        result: dict[str, Any] | list[Any] | None = yaml.safe_load(f)
        return result


def _load_resume_config(project_path: Path) -> dict[str, Any]:
    """Load .resume.yaml configuration.

    Args:
        project_path: Project root directory.

    Returns:
        Parsed configuration dict, empty if file doesn't exist.
    """
    config_path = project_path / ".resume.yaml"
    result = _load_yaml_safe(config_path)
    return result if isinstance(result, dict) else {}


def _get_data_paths(project_path: Path) -> DataPaths | None:
    """Get data_paths configuration from .resume.yaml.

    Args:
        project_path: Project root directory.

    Returns:
        DataPaths object if configured, None otherwise.
    """
    config = _load_resume_config(project_path)
    data_paths_dict = config.get("data_paths")
    if data_paths_dict and isinstance(data_paths_dict, dict):
        return DataPaths(**data_paths_dict)
    return None


def _resolve_storage_mode(
    project_path: Path,
    data_paths: DataPaths | None,
    file_key: str,
    dir_key: str,
    default_filename: str,
    default_dir: str,
) -> tuple[StorageMode, Path | None]:
    """Resolve storage mode and path with three-tier fallback (Story 11.2).

    Lookup order:
    1. Directory from *_dir config (highest priority)
    2. Default directory (e.g., certifications/)
    3. Custom file path from data_paths config
    4. Default file (e.g., certifications.yaml)
    5. None (signals fallback to embedded .resume.yaml)

    Args:
        project_path: Project root directory.
        data_paths: Optional DataPaths configuration.
        file_key: Data paths key for file (e.g., 'certifications').
        dir_key: Data paths key for directory (e.g., 'certifications_dir').
        default_filename: Default filename (e.g., 'certifications.yaml').
        default_dir: Default directory name (e.g., 'certifications').

    Returns:
        Tuple of (storage_mode, path) where path is None for embedded mode.
    """
    # 1. Check *_dir config (explicit directory mode - highest priority)
    if data_paths is not None:
        dir_path_str: str | None = getattr(data_paths, dir_key, None)
        if dir_path_str is not None:
            resolved_dir = project_path / dir_path_str
            if resolved_dir.exists() and resolved_dir.is_dir():
                return ("dir", resolved_dir)

    # 2. Check default directory
    default_dir_path = project_path / default_dir
    if default_dir_path.exists() and default_dir_path.is_dir():
        # Warn if single file also exists (AC2)
        default_file_path = project_path / default_filename
        if default_file_path.exists():
            logger.warning(
                "Both %s/ directory and %s file exist; using directory mode",
                default_dir,
                default_filename,
            )
        return ("dir", default_dir_path)

    # 3. Check custom file path from data_paths config
    if data_paths is not None:
        custom_path: str | None = getattr(data_paths, file_key, None)
        if custom_path is not None:
            resolved = project_path / custom_path
            if resolved.exists():
                return ("file", resolved)

    # 4. Check default file location
    default_path = project_path / default_filename
    if default_path.exists():
        return ("file", default_path)

    # 5. Fall back to embedded in .resume.yaml
    return ("embedded", None)


def _resolve_data_path(
    project_path: Path,
    data_paths: DataPaths | None,
    key: str,
    default_filename: str,
) -> Path | None:
    """Resolve data file path with fallback chain.

    Lookup order:
    1. Custom path from data_paths config
    2. Default filename in project root
    3. None (signals fallback to .resume.yaml)

    Args:
        project_path: Project root directory.
        data_paths: Optional DataPaths configuration.
        key: Data paths key (e.g., 'profile', 'certifications').
        default_filename: Default filename (e.g., 'profile.yaml').

    Returns:
        Resolved path if file exists, None to signal fallback.
    """
    # 1. Check data_paths config
    if data_paths is not None:
        custom_path: str | None = getattr(data_paths, key, None)
        if custom_path is not None:
            resolved = project_path / custom_path
            if resolved.exists():
                return resolved

    # 2. Check default location
    default_path = project_path / default_filename
    if default_path.exists():
        return default_path

    # 3. Fall back to embedded in .resume.yaml
    return None


def _load_list_data(
    project_path: Path,
    data_paths_key: str,
    default_filename: str,
    fallback_key: str,
    model_type: type[T],
    *,
    dir_key: str | None = None,
    default_dir: str | None = None,
) -> list[T]:
    """Load list data with three-tier cascading lookup (Story 11.2).

    Args:
        project_path: Project root directory.
        data_paths_key: Key in DataPaths (e.g., 'certifications').
        default_filename: Default file name (e.g., 'certifications.yaml').
        fallback_key: Key in .resume.yaml for embedded data.
        model_type: Pydantic model type for list items.
        dir_key: Key in DataPaths for directory mode (e.g., 'certifications_dir').
        default_dir: Default directory name (e.g., 'certifications').

    Returns:
        List of validated model instances.
    """
    data_paths = _get_data_paths(project_path)

    # Story 11.2: Use three-tier fallback with directory support
    if dir_key is not None and default_dir is not None:
        mode, resolved_path = _resolve_storage_mode(
            project_path,
            data_paths,
            file_key=data_paths_key,
            dir_key=dir_key,
            default_filename=default_filename,
            default_dir=default_dir,
        )

        if mode == "dir" and resolved_path is not None:
            # Load from directory using ShardedLoader
            loader = ShardedLoader(resolved_path, model_type)
            return loader.load_all()

        if mode == "file" and resolved_path is not None:
            data = _load_yaml_safe(resolved_path)
            if data and isinstance(data, list):
                adapter: TypeAdapter[list[T]] = TypeAdapter(list[model_type])  # type: ignore[valid-type]
                return adapter.validate_python(data)
            return []

        # mode == "embedded" - fall through to embedded lookup
    else:
        # Legacy behavior without directory support
        file_path = _resolve_data_path(project_path, data_paths, data_paths_key, default_filename)
        if file_path is not None:
            data = _load_yaml_safe(file_path)
            if data and isinstance(data, list):
                adapter = TypeAdapter(list[model_type])  # type: ignore[valid-type]
                return adapter.validate_python(data)
            return []

    # Fall back to embedded data in .resume.yaml
    config = _load_resume_config(project_path)
    embedded_data = config.get(fallback_key, [])
    if embedded_data and isinstance(embedded_data, list):
        adapter = TypeAdapter(list[model_type])  # type: ignore[valid-type]
        return adapter.validate_python(embedded_data)

    return []


def load_profile(project_path: Path) -> ProfileConfig:
    """Load profile data with cascading lookup.

    Lookup order:
    1. Custom path from data_paths.profile
    2. profile.yaml in project root
    3. profile section in .resume.yaml

    Args:
        project_path: Project root directory.

    Returns:
        ProfileConfig instance (empty if no data found).
    """
    data_paths = _get_data_paths(project_path)

    # Try dedicated file first
    file_path = _resolve_data_path(project_path, data_paths, "profile", "profile.yaml")

    if file_path is not None:
        data = _load_yaml_safe(file_path)
        if data and isinstance(data, dict):
            return ProfileConfig(**data)
        return ProfileConfig()

    # Fall back to embedded data in .resume.yaml
    config = _load_resume_config(project_path)
    profile_data = config.get("profile", {})
    if profile_data and isinstance(profile_data, dict):
        return ProfileConfig(**profile_data)

    return ProfileConfig()


def load_certifications(project_path: Path) -> list[Certification]:
    """Load certifications with three-tier cascading lookup (Story 11.2).

    Lookup order:
    1. certifications_dir config directory
    2. certifications/ directory in project root
    3. Custom path from data_paths.certifications
    4. certifications.yaml in project root
    5. certifications section in .resume.yaml

    Args:
        project_path: Project root directory.

    Returns:
        List of Certification instances.
    """
    return _load_list_data(
        project_path,
        data_paths_key="certifications",
        default_filename="certifications.yaml",
        fallback_key="certifications",
        model_type=Certification,
        dir_key="certifications_dir",
        default_dir="certifications",
    )


def load_education(project_path: Path) -> list[Education]:
    """Load education with three-tier cascading lookup (Story 11.2).

    Lookup order:
    1. education_dir config directory
    2. education/ directory in project root
    3. Custom path from data_paths.education
    4. education.yaml in project root
    5. education section in .resume.yaml

    Args:
        project_path: Project root directory.

    Returns:
        List of Education instances.
    """
    return _load_list_data(
        project_path,
        data_paths_key="education",
        default_filename="education.yaml",
        fallback_key="education",
        model_type=Education,
        dir_key="education_dir",
        default_dir="education",
    )


def load_highlights(project_path: Path) -> list[str]:
    """Load career highlights with three-tier cascading lookup (Story 11.2).

    Lookup order:
    1. highlights_dir config directory
    2. highlights/ directory in project root
    3. Custom path from data_paths.highlights
    4. highlights.yaml in project root
    5. career_highlights section in .resume.yaml

    Note: Directory mode stores each highlight as a separate YAML file with
    a 'text' field containing the highlight string.

    Args:
        project_path: Project root directory.

    Returns:
        List of highlight strings.
    """
    data_paths = _get_data_paths(project_path)

    # Story 11.2: Use three-tier fallback with directory support
    mode, resolved_path = _resolve_storage_mode(
        project_path,
        data_paths,
        file_key="highlights",
        dir_key="highlights_dir",
        default_filename="highlights.yaml",
        default_dir="highlights",
    )

    if mode == "dir" and resolved_path is not None:
        # Load from directory - each file has a 'text' field
        highlights: list[str] = []
        for yaml_file in sorted(resolved_path.glob("*.yaml")):
            if yaml_file.name.startswith("."):
                continue
            data = _load_yaml_safe(yaml_file)
            if data and isinstance(data, dict):
                text = data.get("text")
                if text:
                    highlights.append(str(text))
        return highlights

    if mode == "file" and resolved_path is not None:
        data = _load_yaml_safe(resolved_path)
        if data and isinstance(data, list):
            return [str(h) for h in data]
        return []

    # Fall back to embedded data in .resume.yaml
    config = _load_resume_config(project_path)
    embedded = config.get("career_highlights", [])
    if embedded and isinstance(embedded, list):
        return [str(h) for h in embedded]

    return []


def load_publications(project_path: Path) -> list[Publication]:
    """Load publications with three-tier cascading lookup (Story 11.2).

    Lookup order:
    1. publications_dir config directory
    2. publications/ directory in project root
    3. Custom path from data_paths.publications
    4. publications.yaml in project root
    5. publications section in .resume.yaml

    Args:
        project_path: Project root directory.

    Returns:
        List of Publication instances.
    """
    return _load_list_data(
        project_path,
        data_paths_key="publications",
        default_filename="publications.yaml",
        fallback_key="publications",
        model_type=Publication,
        dir_key="publications_dir",
        default_dir="publications",
    )


def load_board_roles(project_path: Path) -> list[BoardRole]:
    """Load board roles with three-tier cascading lookup (Story 11.2).

    Lookup order:
    1. board_roles_dir config directory
    2. board-roles/ directory in project root
    3. Custom path from data_paths.board_roles
    4. board-roles.yaml in project root
    5. board_roles section in .resume.yaml

    Args:
        project_path: Project root directory.

    Returns:
        List of BoardRole instances.
    """
    return _load_list_data(
        project_path,
        data_paths_key="board_roles",
        default_filename="board-roles.yaml",
        fallback_key="board_roles",
        model_type=BoardRole,
        dir_key="board_roles_dir",
        default_dir="board-roles",
    )


# Resource type configuration for storage mode resolution
_RESOURCE_CONFIG: dict[str, dict[str, str]] = {
    "certifications": {
        "file_key": "certifications",
        "dir_key": "certifications_dir",
        "default_filename": "certifications.yaml",
        "default_dir": "certifications",
    },
    "education": {
        "file_key": "education",
        "dir_key": "education_dir",
        "default_filename": "education.yaml",
        "default_dir": "education",
    },
    "publications": {
        "file_key": "publications",
        "dir_key": "publications_dir",
        "default_filename": "publications.yaml",
        "default_dir": "publications",
    },
    "board_roles": {
        "file_key": "board_roles",
        "dir_key": "board_roles_dir",
        "default_filename": "board-roles.yaml",
        "default_dir": "board-roles",
    },
    "highlights": {
        "file_key": "highlights",
        "dir_key": "highlights_dir",
        "default_filename": "highlights.yaml",
        "default_dir": "highlights",
    },
}


def get_storage_mode(project_path: Path, resource_type: str) -> tuple[StorageMode, Path | None]:
    """Get storage mode and path for a resource type (Story 11.2).

    Public API for services to determine where to save/remove items.

    Args:
        project_path: Project root directory.
        resource_type: Resource type (certifications, education, publications,
                      board_roles, highlights).

    Returns:
        Tuple of (storage_mode, path) where:
        - storage_mode is "dir", "file", or "embedded"
        - path is the directory/file path, or None for embedded mode

    Raises:
        ValueError: If resource_type is not recognized.
    """
    config = _RESOURCE_CONFIG.get(resource_type)
    if config is None:
        raise ValueError(f"Unknown resource type: {resource_type}")

    data_paths = _get_data_paths(project_path)
    return _resolve_storage_mode(
        project_path,
        data_paths,
        file_key=config["file_key"],
        dir_key=config["dir_key"],
        default_filename=config["default_filename"],
        default_dir=config["default_dir"],
    )
