"""Tests for version management."""

from __future__ import annotations


def test_version_is_string() -> None:
    """Version should be a string."""
    from resume_as_code.__version__ import __version__

    assert isinstance(__version__, str)


def test_version_follows_semver() -> None:
    """Version should follow semantic versioning format (X.Y.Z)."""
    from resume_as_code.__version__ import __version__

    parts = __version__.split(".")
    assert len(parts) == 3, f"Expected 3 version parts, got {len(parts)}"
    for part in parts:
        assert part.isdigit(), f"Version part '{part}' is not a digit"


def test_version_exported_from_package() -> None:
    """Version should be accessible from main package."""
    from resume_as_code import __version__

    # Verify version is exported and non-empty (format validated by test_version_follows_semver)
    assert __version__
    assert isinstance(__version__, str)


def test_version_source_is_single_location() -> None:
    """Version in package should match version file."""
    from resume_as_code import __version__ as pkg_version
    from resume_as_code.__version__ import __version__ as file_version

    assert pkg_version == file_version
