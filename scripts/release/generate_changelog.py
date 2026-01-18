#!/usr/bin/env python3
"""Generate changelog from conventional commits.

This script generates changelog entries from conventional commits
since the last version tag.

Usage:
    python generate_changelog.py --version VERSION [--output-format FORMAT] [--update-file]

Arguments:
    --version VERSION     Version for the changelog entry
    --output-format       Output format: 'text' (default) or 'github' (for Actions)
    --update-file         Update CHANGELOG.md file
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Commit:
    """Parsed conventional commit."""

    type: str
    scope: str | None
    description: str
    breaking: bool
    hash: str


# Commit type display order and labels
COMMIT_TYPES = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "perf": "Performance",
    "refactor": "Refactoring",
    "docs": "Documentation",
    "test": "Tests",
    "build": "Build",
    "ci": "CI/CD",
    "chore": "Chores",
}


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


def get_commits_since_tag(tag: str | None) -> list[tuple[str, str]]:
    """Get commit hashes and messages since the given tag."""
    if tag:
        cmd = ["git", "log", f"{tag}..HEAD", "--pretty=format:%h|%s"]
    else:
        cmd = ["git", "log", "--pretty=format:%h|%s"]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    commits = []
    for line in result.stdout.strip().split("\n"):
        if line and "|" in line:
            hash_val, message = line.split("|", 1)
            commits.append((hash_val, message))
    return commits


def parse_commit(hash_val: str, message: str) -> Commit | None:
    """Parse a conventional commit message."""
    # Pattern: type(scope)!: description or type!: description or type: description
    pattern = r"^(\w+)(?:\(([^)]+)\))?(!)?\s*:\s*(.+)$"
    match = re.match(pattern, message)

    if not match:
        return None

    commit_type, scope, breaking_marker, description = match.groups()

    # Normalize type
    commit_type = commit_type.lower()
    if commit_type not in COMMIT_TYPES:
        return None

    return Commit(
        type=commit_type,
        scope=scope,
        description=description.strip(),
        breaking=breaking_marker == "!",
        hash=hash_val,
    )


def generate_changelog(version: str, commits: list[Commit]) -> str:
    """Generate markdown changelog from commits."""
    # Group by type
    by_type: dict[str, list[Commit]] = defaultdict(list)
    breaking_changes: list[Commit] = []

    for commit in commits:
        by_type[commit.type].append(commit)
        if commit.breaking:
            breaking_changes.append(commit)

    # Build changelog
    lines = [f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}", ""]

    # Breaking changes first
    if breaking_changes:
        lines.append("### BREAKING CHANGES")
        lines.append("")
        for commit in breaking_changes:
            scope = f"**{commit.scope}:** " if commit.scope else ""
            lines.append(f"- {scope}{commit.description}")
        lines.append("")

    # Then by type
    for type_key in COMMIT_TYPES:
        if type_key in by_type:
            lines.append(f"### {COMMIT_TYPES[type_key]}")
            lines.append("")
            for commit in by_type[type_key]:
                scope = f"**{commit.scope}:** " if commit.scope else ""
                lines.append(f"- {scope}{commit.description}")
            lines.append("")

    return "\n".join(lines)


def update_changelog_file(version: str, changelog_content: str) -> None:
    """Update CHANGELOG.md with new version entry."""
    changelog_path = Path(__file__).parent.parent.parent / "CHANGELOG.md"

    if changelog_path.exists():
        existing = changelog_path.read_text()

        # Find insertion point (after header, before first version)
        header_pattern = r"^# Changelog\s*\n+"
        match = re.match(header_pattern, existing, re.MULTILINE)

        if match:
            insert_pos = match.end()
            new_content = existing[:insert_pos] + changelog_content + "\n" + existing[insert_pos:]
        else:
            # No header, prepend everything
            new_content = f"# Changelog\n\n{changelog_content}\n{existing}"
    else:
        new_content = f"# Changelog\n\n{changelog_content}"

    changelog_path.write_text(new_content)
    print(f"Updated {changelog_path}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate changelog from commits")
    parser.add_argument("--version", required=True, help="Version for changelog entry")
    parser.add_argument(
        "--output-format",
        choices=["text", "github"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--update-file",
        action="store_true",
        help="Update CHANGELOG.md file",
    )
    args = parser.parse_args()

    last_tag = get_last_tag()
    raw_commits = get_commits_since_tag(last_tag)

    # Parse commits
    commits = []
    for hash_val, message in raw_commits:
        parsed = parse_commit(hash_val, message)
        if parsed:
            commits.append(parsed)

    if not commits:
        print("No conventional commits found", file=sys.stderr)
        # Generate minimal changelog
        date_str = datetime.now().strftime("%Y-%m-%d")
        changelog = f"## [{args.version}] - {date_str}\n\n- Various updates and improvements\n"
    else:
        changelog = generate_changelog(args.version, commits)

    if args.update_file:
        update_changelog_file(args.version, changelog)

    if args.output_format == "github":
        # Escape for GitHub Actions multiline output
        escaped = changelog.replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")
        print(f"changelog={escaped}")

        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                # Use heredoc syntax for multiline
                f.write(f"changelog<<EOF\n{changelog}\nEOF\n")
    else:
        print(changelog)

    return 0


if __name__ == "__main__":
    sys.exit(main())
