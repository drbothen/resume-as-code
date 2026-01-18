"""Unified data access layer for Resume as Code.

Story 9.2: Provides functions to load resume data from either dedicated
files or embedded in .resume.yaml for backward compatibility.

The lookup order for each data type is:
1. Custom path from data_paths configuration (if specified)
2. Default dedicated file (e.g., profile.yaml, certifications.yaml)
3. Embedded data in .resume.yaml (legacy/backward compatible)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel, TypeAdapter

from resume_as_code.models.board_role import BoardRole
from resume_as_code.models.certification import Certification
from resume_as_code.models.config import DataPaths, ProfileConfig
from resume_as_code.models.education import Education
from resume_as_code.models.publication import Publication

# Type variable for list data loading
T = TypeVar("T", bound=BaseModel)


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
) -> list[T]:
    """Load list data with cascading lookup.

    Args:
        project_path: Project root directory.
        data_paths_key: Key in DataPaths (e.g., 'certifications').
        default_filename: Default file name (e.g., 'certifications.yaml').
        fallback_key: Key in .resume.yaml for embedded data.
        model_type: Pydantic model type for list items.

    Returns:
        List of validated model instances.
    """
    data_paths = _get_data_paths(project_path)

    # Try dedicated file first
    file_path = _resolve_data_path(project_path, data_paths, data_paths_key, default_filename)

    if file_path is not None:
        data = _load_yaml_safe(file_path)
        if data and isinstance(data, list):
            adapter: TypeAdapter[list[T]] = TypeAdapter(list[model_type])  # type: ignore[valid-type]
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
    """Load certifications with cascading lookup.

    Lookup order:
    1. Custom path from data_paths.certifications
    2. certifications.yaml in project root
    3. certifications section in .resume.yaml

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
    )


def load_education(project_path: Path) -> list[Education]:
    """Load education with cascading lookup.

    Lookup order:
    1. Custom path from data_paths.education
    2. education.yaml in project root
    3. education section in .resume.yaml

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
    )


def load_highlights(project_path: Path) -> list[str]:
    """Load career highlights with cascading lookup.

    Lookup order:
    1. Custom path from data_paths.highlights
    2. highlights.yaml in project root
    3. career_highlights section in .resume.yaml

    Args:
        project_path: Project root directory.

    Returns:
        List of highlight strings.
    """
    data_paths = _get_data_paths(project_path)

    # Try dedicated file first
    file_path = _resolve_data_path(project_path, data_paths, "highlights", "highlights.yaml")

    if file_path is not None:
        data = _load_yaml_safe(file_path)
        if data and isinstance(data, list):
            return [str(h) for h in data]
        return []

    # Fall back to embedded data in .resume.yaml
    config = _load_resume_config(project_path)
    highlights = config.get("career_highlights", [])
    if highlights and isinstance(highlights, list):
        return [str(h) for h in highlights]

    return []


def load_publications(project_path: Path) -> list[Publication]:
    """Load publications with cascading lookup.

    Lookup order:
    1. Custom path from data_paths.publications
    2. publications.yaml in project root
    3. publications section in .resume.yaml

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
    )


def load_board_roles(project_path: Path) -> list[BoardRole]:
    """Load board roles with cascading lookup.

    Lookup order:
    1. Custom path from data_paths.board_roles
    2. board-roles.yaml in project root
    3. board_roles section in .resume.yaml

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
    )
