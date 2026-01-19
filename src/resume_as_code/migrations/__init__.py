"""Schema evolution and migration system for Resume as Code.

This module provides infrastructure for detecting outdated schemas and
migrating them to the latest version while preserving user data and comments.

Version History:
    1.0.0 - Legacy (no schema_version field)
    2.0.0 - Added schema_version tracking
    3.0.0 - Separated configuration from resume data (Story 9.2)
    4.0.0 - Added required archetype field to work units (Story 12.1)
"""

from __future__ import annotations

# Current schema version (target for migrations)
CURRENT_SCHEMA_VERSION = "4.0.0"

# Version for projects without schema_version field
LEGACY_VERSION = "1.0.0"

# Import migrations to register them via decorator
# Note: Import after constants to avoid circular import
from resume_as_code.migrations import v1_to_v2 as _v1_to_v2  # noqa: F401, E402
from resume_as_code.migrations import v2_to_v3 as _v2_to_v3  # noqa: F401, E402
from resume_as_code.migrations import v3_to_v4 as _v3_to_v4  # noqa: F401, E402

__all__ = ["CURRENT_SCHEMA_VERSION", "LEGACY_VERSION"]
