"""Validation error message mappings with field-specific suggestions.

This module provides contextual suggestions and examples for schema validation
errors to help users understand and fix issues in their Work Units.
"""

from __future__ import annotations

# Field-specific suggestions for missing required fields
FIELD_SUGGESTIONS: dict[str, str] = {
    "title": (
        "Add a concise title describing your accomplishment (e.g., 'Reduced API latency by 40%')"
    ),
    "problem": "Add a problem section describing the challenge you faced",
    "problem.statement": "Describe the challenge or problem you were solving (min 20 characters)",
    "actions": "List the specific actions you took to solve the problem",
    "outcome": "Add an outcome section describing the results",
    "outcome.result": "Describe what you achieved or the impact of your work (min 10 characters)",
    "id": "Add a unique ID in format: wu-YYYY-MM-DD-slug (e.g., wu-2026-01-10-api-optimization)",
    "schema_version": "Add schema_version: '1.0.0' at the top of the file",
    "statement": "Describe the challenge or problem you were solving",
    "result": "Describe what you achieved or the impact of your work",
    "name": "Add a name for the skill or item",
    "url": "Add a valid URL (e.g., https://example.com)",
    "type": "Specify the type field with a valid value",
}

# Type error examples for JSON Schema types
TYPE_EXAMPLES: dict[str, str] = {
    "string": '"example text"',
    "array": '["item1", "item2"]',
    "object": "key: value",
    "number": "42 or 3.14",
    "boolean": "true or false",
    "integer": "42",
    "null": "null",
}

# Enum field valid values (for clearer error messages)
ENUM_FIELDS: dict[str, list[str]] = {
    "confidence": ["high", "medium", "low"],
    "outcome.confidence": ["exact", "estimated", "approximate", "order_of_magnitude"],
    "evidence.type": ["git_repo", "metrics", "document", "artifact", "other"],
    "impact_category": ["financial", "operational", "talent", "customer", "organizational"],
}


def get_suggestion_for_field(field_path: str) -> str:
    """Get a helpful suggestion for a missing/invalid field.

    Args:
        field_path: The field path (e.g., "problem.statement" or "title")

    Returns:
        A helpful suggestion string for the field.
    """
    # Try exact match first
    if field_path in FIELD_SUGGESTIONS:
        return FIELD_SUGGESTIONS[field_path]

    # Try partial match - check if any key is at the end of the path
    for key, suggestion in FIELD_SUGGESTIONS.items():
        if field_path.endswith(key):
            return suggestion

    # Try partial match - check if key contains the last segment
    last_segment = field_path.split(".")[-1]
    if last_segment in FIELD_SUGGESTIONS:
        return FIELD_SUGGESTIONS[last_segment]

    return "Check the Work Unit schema for the correct format"


def get_type_example(expected_type: str) -> str:
    """Get an example for the expected type.

    Args:
        expected_type: The expected JSON Schema type (e.g., "string", "array")

    Returns:
        An example of the expected type, or a generic message for unknown types.
    """
    return TYPE_EXAMPLES.get(expected_type, f"a valid {expected_type}")


def get_enum_values(field_path: str) -> list[str] | None:
    """Get valid enum values for a field.

    Args:
        field_path: The field path (e.g., "confidence" or "evidence.type")

    Returns:
        List of valid enum values, or None if the field is not an enum.
    """
    # Try exact match first
    if field_path in ENUM_FIELDS:
        return ENUM_FIELDS[field_path]

    # Try partial match - check if any key is at the end of the path
    for key, values in ENUM_FIELDS.items():
        if field_path.endswith(key):
            return values

    # Try matching just the last segment
    last_segment = field_path.split(".")[-1]
    if last_segment in ENUM_FIELDS:
        return ENUM_FIELDS[last_segment]

    return None
