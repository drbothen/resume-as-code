"""Slug generation utilities for ID creation.

Provides functions to convert text to URL-friendly slugs and generate
unique position IDs from employer/title combinations.
"""

from __future__ import annotations

import re
import unicodedata


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug.

    Examples:
        slugify("TechCorp Industries") -> "techcorp-industries"
        slugify("Senior Platform Engineer") -> "senior-platform-engineer"
        slugify("O'Reilly & Associates") -> "oreilly-associates"

    Args:
        text: Text to convert to slug.

    Returns:
        Lowercase hyphen-separated slug with special characters removed.
    """
    if not text:
        return ""

    # Normalize unicode characters (e.g., é -> e)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Convert to lowercase
    text = text.lower()

    # Replace spaces and special chars with hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)

    # Remove leading/trailing hyphens
    return text.strip("-")


def generate_position_id(employer: str, title: str) -> str:
    """Generate position ID from employer and title.

    Format: pos-{employer-slug}-{title-slug}
    Example: pos-techcorp-senior-engineer

    Args:
        employer: Employer/company name.
        title: Job title.

    Returns:
        Position ID string.
    """
    employer_slug = slugify(employer)[:20]  # Limit length
    title_slug = slugify(title)[:20]

    return f"pos-{employer_slug}-{title_slug}"


def generate_unique_position_id(
    employer: str,
    title: str,
    existing_ids: set[str],
) -> str:
    """Generate unique position ID, handling duplicates.

    If the base ID already exists, appends -2, -3, etc.

    Args:
        employer: Employer/company name.
        title: Job title.
        existing_ids: Set of existing position IDs to check against.

    Returns:
        Unique position ID string.
    """
    base_id = generate_position_id(employer, title)

    if base_id not in existing_ids:
        return base_id

    # Find next available number
    counter = 2
    while f"{base_id}-{counter}" in existing_ids:
        counter += 1

    return f"{base_id}-{counter}"
