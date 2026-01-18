#!/usr/bin/env python3
"""Analyze conventional commits and determine version bump.

This script analyzes commits since the last version tag and determines
the appropriate semantic version bump based on conventional commit types.

Usage:
    python bump_version.py [--version VERSION] [--output-format FORMAT]

Arguments:
    --version VERSION     Override auto-detection with specific version
    --output-format       Output format: 'text' (default) or 'github' (for Actions)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VersionBump:
    """Result of version bump analysis."""

    old_version: str
    new_version: str
    bump_type: str  # major, minor, patch


def get_current_version() -> str:
    """Read current version from __version__.py."""
    version_file = Path(__file__).parent.parent.parent / "src/resume_as_code/__version__.py"
    content = version_file.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError(f"Could not parse version from {version_file}")
    return match.group(1)


def get_last_tag() -> str | None:
    """Get the most recent version tag."""
    result = subprocess.run(
        ["git", "tag", "--list", "v*.*.*", "--sort=-version:refname"],
        capture_output=True,
        text=True,
        check=True,
    )
    tags = result.stdout.strip().split("\n")
    return tags[0] if tags and tags[0] else None


def get_commits_since_tag(tag: str | None) -> list[str]:
    """Get commit messages since the given tag."""
    if tag:
        cmd = ["git", "log", f"{tag}..HEAD", "--pretty=format:%s"]
    else:
        cmd = ["git", "log", "--pretty=format:%s"]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return [line for line in result.stdout.strip().split("\n") if line]


def analyze_commits(commits: list[str]) -> str:
    """Analyze commits and determine bump type.

    Returns: 'major', 'minor', or 'patch'
    """
    has_breaking = False
    has_feat = False

    for commit in commits:
        # Check for breaking changes
        if "BREAKING CHANGE" in commit or re.match(r"^\w+(\(.+\))?!:", commit):
            has_breaking = True

        # Check for features
        if re.match(r"^feat(\(.+\))?:", commit):
            has_feat = True

    if has_breaking:
        return "major"
    if has_feat:
        return "minor"
    return "patch"


def bump_version(version: str, bump_type: str) -> str:
    """Apply version bump."""
    # Parse version (handle pre-release suffixes)
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(-.*)?$", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")

    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))

    if bump_type == "major":
        return f"{major + 1}.0.0"
    if bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Determine version bump from commits")
    parser.add_argument("--version", help="Override version (skip auto-detection)")
    parser.add_argument(
        "--output-format",
        choices=["text", "github"],
        default="text",
        help="Output format",
    )
    args = parser.parse_args()

    current_version = get_current_version()

    if args.version:
        new_version = args.version
        bump_type = "manual"
    else:
        last_tag = get_last_tag()
        commits = get_commits_since_tag(last_tag)

        if not commits:
            print("No commits since last tag", file=sys.stderr)
            return 1

        bump_type = analyze_commits(commits)
        new_version = bump_version(current_version, bump_type)

    if args.output_format == "github":
        print(f"old_version={current_version}")
        print(f"new_version={new_version}")
        print(f"bump_type={bump_type}")
        # Write to GITHUB_OUTPUT if available
        import os

        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                f.write(f"old_version={current_version}\n")
                f.write(f"new_version={new_version}\n")
                f.write(f"bump_type={bump_type}\n")
    else:
        print(f"Current version: {current_version}")
        print(f"Bump type: {bump_type}")
        print(f"New version: {new_version}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
