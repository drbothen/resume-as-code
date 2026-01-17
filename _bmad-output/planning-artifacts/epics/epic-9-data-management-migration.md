# Epic 9: Data Management & Migration

**Goal:** Provide robust data management capabilities including schema versioning, migration, and backward compatibility for resume-as-code projects

**User Outcome:** Users can safely upgrade their resume-as-code installation without losing data or manually migrating files when the schema evolves

**Priority:** P2
**Total Points:** 13 (2 stories)

---

## Story 9.1: Schema Evolution & Migration System

As a **resume-as-code user with existing data**,
I want **automatic detection and migration of outdated schemas**,
So that **I can upgrade to new versions without manually editing YAML files or losing data**.

**Story Points:** 8
**Priority:** P2

**Problem Statement:**
As the resume-as-code system evolves, schemas will change:
- New required fields may be added
- Field names may be renamed for clarity
- Field types may change (e.g., string → structured object)
- New sections may be introduced (e.g., publications, board roles)
- Validation rules may become stricter

Without a migration system, users face:
- Cryptic validation errors after upgrading
- Manual file editing across dozens of work units
- Risk of data loss if migrations are done incorrectly
- Barrier to adoption of new features

**Example Scenarios:**

1. **New required field**: `position_id` becomes required on work units
   - Migration: Add `position_id: null` with warning to populate

2. **Field rename**: `employer` → `organization` in positions
   - Migration: Copy value from old field to new field

3. **Type change**: `skills: ["python", "aws"]` → `skills: [{name: "python", level: "expert"}]`
   - Migration: Transform each string to object with defaults

4. **Schema version bump**: v1.0 → v2.0
   - Migration: Run all applicable migrations in sequence

**Acceptance Criteria:**

**Given** a `.resume.yaml` file without a `schema_version` field
**When** running any `resume` command
**Then** the system detects this as v1.0.0 (legacy)
**And** warns the user about available migrations

**Given** a resume project with schema v1.x
**When** running `resume migrate`
**Then** the system shows what migrations are available
**And** asks for confirmation before proceeding
**And** creates backups of all files before modifying

**Given** a migration in progress
**When** a migration step fails
**Then** all changes are rolled back
**And** the user sees a clear error message
**And** backup files are preserved

**Given** a work unit file with outdated schema
**When** running `resume migrate`
**Then** the file is updated to the latest schema
**And** the original formatting is preserved where possible
**And** comments in the YAML are preserved

**Given** multiple files needing migration
**When** running `resume migrate --dry-run`
**Then** the system shows what changes would be made
**And** no files are actually modified

**Given** a successfully migrated project
**When** checking the config
**Then** `schema_version` reflects the current version
**And** all files pass validation

**Technical Notes:**

```python
# src/resume_as_code/migrations/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

@dataclass
class MigrationResult:
    """Result of a single migration."""
    success: bool
    files_modified: list[Path]
    warnings: list[str]
    errors: list[str]

class Migration(ABC):
    """Base class for schema migrations."""

    # Version this migration upgrades FROM
    from_version: str
    # Version this migration upgrades TO
    to_version: str
    # Human-readable description
    description: str

    @abstractmethod
    def check_applicable(self, project_path: Path) -> bool:
        """Check if this migration applies to the project."""
        pass

    @abstractmethod
    def preview(self, project_path: Path) -> list[str]:
        """Return list of changes that would be made (dry-run)."""
        pass

    @abstractmethod
    def apply(self, project_path: Path) -> MigrationResult:
        """Apply the migration. Must be idempotent."""
        pass

    @abstractmethod
    def rollback(self, project_path: Path, backup_path: Path) -> bool:
        """Rollback migration using backup files."""
        pass


# src/resume_as_code/migrations/registry.py

from typing import Type

_migrations: list[Type[Migration]] = []

def register_migration(migration_class: Type[Migration]) -> Type[Migration]:
    """Decorator to register a migration."""
    _migrations.append(migration_class)
    _migrations.sort(key=lambda m: m.from_version)
    return migration_class

def get_migration_path(from_version: str, to_version: str) -> list[Type[Migration]]:
    """Get ordered list of migrations to go from one version to another."""
    path = []
    current = from_version

    while current != to_version:
        # Find migration from current version
        next_migration = next(
            (m for m in _migrations if m.from_version == current),
            None
        )
        if not next_migration:
            raise ValueError(f"No migration path from {current} to {to_version}")

        path.append(next_migration)
        current = next_migration.to_version

    return path


# src/resume_as_code/migrations/v1_to_v2.py

@register_migration
class MigrationV1ToV2(Migration):
    from_version = "1.0.0"
    to_version = "2.0.0"
    description = "Add schema_version field, normalize position references"

    def check_applicable(self, project_path: Path) -> bool:
        config = load_config(project_path)
        return config.get("schema_version") is None

    def preview(self, project_path: Path) -> list[str]:
        changes = []
        changes.append(f"Add schema_version: 2.0.0 to .resume.yaml")

        # Check work units for missing position_id
        for wu_file in (project_path / "work-units").glob("*.yaml"):
            wu = load_yaml(wu_file)
            if "position_id" not in wu:
                changes.append(f"Add position_id field to {wu_file.name}")

        return changes

    def apply(self, project_path: Path) -> MigrationResult:
        # Implementation...
        pass
```

**CLI Commands:**

```bash
# Check migration status
resume migrate --status
# Output:
# Current schema version: 1.0.0
# Latest schema version: 2.1.0
# Available migrations:
#   1.0.0 → 2.0.0: Add schema_version, normalize positions
#   2.0.0 → 2.1.0: Add publications section support

# Preview migrations (dry-run)
resume migrate --dry-run
# Output:
# Would apply 2 migrations:
#
# Migration 1: 1.0.0 → 2.0.0
#   - Add schema_version: 2.0.0 to .resume.yaml
#   - Add position_id field to wu-2024-01-15-cloud-migration.yaml
#   - Add position_id field to wu-2024-02-20-security-audit.yaml
#
# Migration 2: 2.0.0 → 2.1.0
#   - Add publications: [] to .resume.yaml
#
# Run without --dry-run to apply changes.

# Apply migrations
resume migrate
# Output:
# Creating backup at .resume-backup-2026-01-17/...
# Applying migration 1.0.0 → 2.0.0...
#   ✓ Updated .resume.yaml
#   ✓ Updated wu-2024-01-15-cloud-migration.yaml
#   ✓ Updated wu-2024-02-20-security-audit.yaml
# Applying migration 2.0.0 → 2.1.0...
#   ✓ Updated .resume.yaml
#
# ✓ Migration complete! Schema version: 2.1.0
# Backup preserved at .resume-backup-2026-01-17/

# Rollback if something went wrong
resume migrate --rollback .resume-backup-2026-01-17/
```

**Config Schema Version:**
```yaml
# .resume.yaml
schema_version: "2.1.0"  # Added by migration system

# The schema_version field:
# - Tracks which schema version this project uses
# - Enables targeted migrations
# - Allows validation rules to vary by version
```

**Backup Strategy:**
```
.resume-backup-2026-01-17/
├── .resume.yaml
├── positions.yaml
└── work-units/
    ├── wu-2024-01-15-cloud-migration.yaml
    └── wu-2024-02-20-security-audit.yaml
```

**Files to Create/Modify:**
- Create: `src/resume_as_code/migrations/__init__.py`
- Create: `src/resume_as_code/migrations/base.py` (Migration base class)
- Create: `src/resume_as_code/migrations/registry.py` (Migration registry)
- Create: `src/resume_as_code/migrations/v1_to_v2.py` (First migration)
- Create: `src/resume_as_code/commands/migrate.py` (CLI command)
- Modify: `src/resume_as_code/cli.py` (register migrate command)
- Modify: `src/resume_as_code/models/config.py` (add schema_version field)
- Modify: `schemas/config.schema.json` (add schema_version)

**Definition of Done:**
- [ ] Migration base class with preview/apply/rollback interface
- [ ] Migration registry with version path resolution
- [ ] `resume migrate --status` shows current vs latest version
- [ ] `resume migrate --dry-run` previews changes without modifying
- [ ] `resume migrate` applies migrations with confirmation
- [ ] Automatic backup creation before migration
- [ ] `resume migrate --rollback <backup>` restores from backup
- [ ] YAML comment preservation during migration
- [ ] Idempotent migrations (safe to run multiple times)
- [ ] At least one real migration (v1 → v2) implemented
- [ ] Unit tests for migration framework
- [ ] Integration test for full migration cycle

---

## Story 9.2: Separate Configuration from Resume Data

As a **resume-as-code user**,
I want **configuration settings separate from my resume data**,
So that **I can version control, share, and manage them independently**.

**Story Points:** 5
**Priority:** P1

**Problem Statement:**
Currently `.resume.yaml` mixes two concerns:

1. **Configuration** (how the tool behaves):
   - output_dir, default_format, default_template
   - work_units_dir, positions_path
   - Tool settings and preferences

2. **Resume Data** (the actual content):
   - profile (name, email, location, links, summary)
   - certifications (list of credentials)
   - education (list of degrees)
   - career_highlights (list of achievements)
   - publications (list of articles/talks)
   - board_roles (list of advisory positions)

This creates problems:
- Config and data change at different rates
- Sharing templates requires filtering out personal data
- Backup strategies differ (config = project, data = personal)
- The file grows unwieldy (247 lines in current state)
- Harder to validate each concern independently

**Current Structure:**
```
project/
├── .resume.yaml          # Mixed: config + profile + certs + education + highlights + publications
├── positions.yaml        # Data: employment history
└── work-units/           # Data: achievements
    └── *.yaml
```

**Proposed Structure:**
```
project/
├── .resume.yaml          # Config only (small, stable)
├── profile.yaml          # Data: personal info, summary
├── positions.yaml        # Data: employment history (unchanged)
├── certifications.yaml   # Data: credentials
├── education.yaml        # Data: degrees
├── highlights.yaml       # Data: career highlights
├── publications.yaml     # Data: articles, talks
├── board-roles.yaml      # Data: advisory positions
└── work-units/           # Data: achievements (unchanged)
    └── *.yaml
```

**Acceptance Criteria:**

**Given** a new `resume init` project
**When** initialization completes
**Then** `.resume.yaml` contains only configuration settings
**And** `profile.yaml` is created with personal info fields
**And** other data files are created as empty/placeholder

**Given** an existing project with mixed `.resume.yaml`
**When** running `resume migrate`
**Then** data is extracted to separate files
**And** `.resume.yaml` retains only config settings
**And** references are updated (e.g., `profile_path: ./profile.yaml`)

**Given** a project with separate data files
**When** running any `resume` command
**Then** data is loaded from the appropriate files
**And** the system works identically to before

**Given** a missing optional data file (e.g., no publications.yaml)
**When** building a resume
**Then** that section is simply omitted
**And** no error is thrown

**Given** the `--json` flag
**When** running `resume config`
**Then** output shows config settings only
**And** data file paths are shown but not contents

**Technical Notes:**

**New `.resume.yaml` (config only):**
```yaml
# .resume.yaml - Configuration only
schema_version: "2.0.0"

# Output settings
output_dir: ./dist
default_format: both
default_template: executive

# Data file paths (all optional, defaults shown)
data_paths:
  profile: ./profile.yaml
  positions: ./positions.yaml
  certifications: ./certifications.yaml
  education: ./education.yaml
  highlights: ./highlights.yaml
  publications: ./publications.yaml
  board_roles: ./board-roles.yaml
  work_units_dir: ./work-units

# Template options
template_options:
  group_employer_positions: true

# Publication curation
publications:
  max_count: 5
  sort_by: relevance
```

**New `profile.yaml`:**
```yaml
# profile.yaml - Personal information
name: Joshua Magady
email: Josh.Magady@gmail.com
location: Lee's Summit, MO
phone: null  # Optional

# Online presence
linkedin: https://www.linkedin.com/in/joshuamagady/
github: https://github.com/drbothen
website: null  # Optional
twitter: null  # Optional

# Professional summary
summary: >-
  Cybersecurity leader with 20+ years of experience...
```

**New `certifications.yaml`:**
```yaml
# certifications.yaml
certifications:
  - name: OSCP
    issuer: Offensive Security
    date: 2023-06
    expires: null
    credential_id: null

  - name: CISSP
    issuer: (ISC)²
    date: 2020-01
    expires: 2026-01
```

**Migration Implementation:**
```python
# Part of Story 9.1's migration framework

@register_migration
class MigrationSeparateDataFromConfig(Migration):
    from_version = "1.0.0"
    to_version = "2.0.0"
    description = "Separate resume data from configuration"

    def apply(self, project_path: Path) -> MigrationResult:
        config = load_yaml(project_path / ".resume.yaml")

        # Extract data sections
        data_sections = {
            "profile": ["name", "email", "location", "linkedin", "github", "summary", "phone", "website"],
            "certifications": config.pop("certifications", []),
            "education": config.pop("education", []),
            "career_highlights": config.pop("career_highlights", []),
            "publications": config.pop("publications", []),
            "board_roles": config.pop("board_roles", []),
        }

        # Write profile.yaml
        profile_data = {k: config.pop(k, None) for k in data_sections["profile"] if k in config}
        if "profile" in config:
            profile_data = config.pop("profile")
        write_yaml(project_path / "profile.yaml", profile_data)

        # Write other data files
        for name, data in data_sections.items():
            if name != "profile" and data:
                write_yaml(project_path / f"{name.replace('_', '-')}.yaml", {name: data})

        # Add data_paths to config
        config["data_paths"] = {
            "profile": "./profile.yaml",
            "positions": "./positions.yaml",
            "certifications": "./certifications.yaml",
            "education": "./education.yaml",
            "highlights": "./highlights.yaml",
            "publications": "./publications.yaml",
            "board_roles": "./board-roles.yaml",
            "work_units_dir": "./work-units",
        }

        config["schema_version"] = "2.0.0"
        write_yaml(project_path / ".resume.yaml", config)

        return MigrationResult(success=True, ...)
```

**Backward Compatibility:**
- If data is found in `.resume.yaml`, use it (legacy mode)
- If `data_paths` is defined, load from separate files
- Warn users on legacy mode: "Consider running `resume migrate`"

**Files to Create/Modify:**
- Modify: `src/resume_as_code/models/config.py` (add data_paths, remove data fields)
- Create: `src/resume_as_code/models/profile.py` (Profile model)
- Modify: `src/resume_as_code/services/config_service.py` (load from multiple files)
- Modify: `src/resume_as_code/commands/init.py` (create separate files)
- Modify: `src/resume_as_code/migrations/v1_to_v2.py` (implement separation)
- Create: `schemas/profile.schema.json`
- Create: `schemas/certifications.schema.json`
- Update: `schemas/config.schema.json` (remove data, add data_paths)

**Definition of Done:**
- [ ] `.resume.yaml` contains only configuration settings
- [ ] `profile.yaml` holds personal info and summary
- [ ] `certifications.yaml` holds credentials list
- [ ] `education.yaml` holds education entries
- [ ] `highlights.yaml` holds career highlights
- [ ] `publications.yaml` holds publications/speaking
- [ ] `board-roles.yaml` holds board/advisory roles
- [ ] `data_paths` config option for custom file locations
- [ ] `resume init` creates separate data files
- [ ] Migration extracts data from mixed `.resume.yaml`
- [ ] Backward compatibility with legacy mixed format
- [ ] All CLI commands work with new structure
- [ ] JSON schemas for each data file
- [ ] Unit tests for data loading from separate files
- [ ] Integration test for migration

---
