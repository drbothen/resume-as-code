# Story 11.2: Directory-Based Sharding for Data Files

Status: done

## Story

As a **power user with many certifications, publications, or other data items**,
I want **optional per-item YAML files organized in directories (like work-units/)**,
So that **I get fine-grained version control and avoid merge conflicts**.

## Acceptance Criteria

1. **AC1: Directory mode loading** - Given a `.resume.yaml` with `certifications_dir: ./certifications/`, when loading certifications data, then the system reads all YAML files from the directory and combines them into a single list for processing.

2. **AC2: Precedence rule** - Given both `certifications.yaml` AND `certifications/` directory exist, when loading certifications, then the system uses the directory (directory takes precedence) and logs a warning about the dual configuration.

3. **AC3: Directory mode writing** - Given a user runs `resume new certification` with directory mode enabled, when the certification is created, then it's written to a new file in `certifications/` and the filename follows pattern: `cert-YYYY-MM-{slug}.yaml`.

4. **AC4: Migration command** - Given a project with single-file storage, when running `resume migrate --shard certifications`, then items are extracted to individual files, original file is backed up, and config is updated to use directory mode.

5. **AC5: List command parity** - Given a `resume list certifications` command when in directory mode, then all certifications display identically to single-file mode and source file path is shown with `--verbose` flag.

## Tasks / Subtasks

- [x] Task 1: Extend DataPaths model with directory options (AC: 1, 2)
  - [x] 1.1 Add `certifications_dir`, `publications_dir`, `education_dir`, `board_roles_dir`, `highlights_dir` fields to `DataPaths` model
  - [x] 1.2 Add model validation to ensure both `*_path` and `*_dir` aren't specified simultaneously
  - [x] 1.3 Update JSON schema generation to include new fields

- [x] Task 2: Create generic ShardedLoader class (AC: 1, 3)
  - [x] 2.1 Create `src/resume_as_code/services/sharded_loader.py` following WorkUnitLoader pattern
  - [x] 2.2 Implement `load_all()` method that iterates `*.yaml` files in directory
  - [x] 2.3 Implement `save()` method to write individual item files
  - [x] 2.4 Implement `remove()` method to delete item files
  - [x] 2.5 Add ID generation logic per resource type (see ID Patterns below)

- [x] Task 3: Implement three-tier loading fallback in data_loader.py (AC: 1, 2)
  - [x] 3.1 Update `_resolve_data_path()` to check for `*_dir` config first
  - [x] 3.2 Add `_load_sharded_data()` helper for directory mode loading
  - [x] 3.3 Add warning logging when both directory and single file exist
  - [x] 3.4 Update each `load_*()` function to use three-tier fallback

- [x] Task 4: Update `new` commands for directory mode (AC: 3)
  - [x] 4.1 Update certification service `save_certification()` to check directory mode
  - [x] 4.2 Update publication service to support directory mode
  - [x] 4.3 Update education service to support directory mode
  - [x] 4.4 Update board-role service to support directory mode
  - [x] 4.5 Update highlight service to support directory mode

- [x] Task 5: Update `remove` commands for directory mode (AC: 5)
  - [x] 5.1 Update certification service `remove_certification()` to handle directory mode
  - [x] 5.2 Update other services for directory-based removal

- [x] Task 6: Update `list` commands for verbose source display (AC: 5)
  - [x] 6.1 Add source file tracking to loaded items
  - [x] 6.2 Display source path in `--verbose` output

- [x] Task 7: Implement `migrate --shard` command (AC: 4)
  - [x] 7.1 Add `--shard` option to migrate command accepting resource type
  - [x] 7.2 Implement single-file to directory extraction logic
  - [x] 7.3 Create backup of original file before migration
  - [x] 7.4 Update `.resume.yaml` to enable directory mode after migration

- [x] Task 8: Add tests for sharding functionality
  - [x] 8.1 Unit tests for ShardedLoader class
  - [x] 8.2 Integration tests for three-tier fallback
  - [x] 8.3 Integration tests for migrate --shard command
  - [x] 8.4 Tests for precedence when both directory and file exist

## Dev Notes

### Problem Statement

Currently, data files (certifications, education, publications, board-roles, highlights) are stored as single YAML files containing all items as a list. For users with large collections (20+ items) or teams working on shared resume data, this creates:
- Merge conflicts when multiple people edit the same file
- No per-item version history
- Large files that are harder to navigate
- Inconsistency with the `work-units/` pattern

### Current vs Proposed Structure

**Current (single-file):**
```
certifications.yaml      # Contains all certifications as a list
education.yaml           # Contains all education entries as a list
publications.yaml        # Contains all publications as a list
board-roles.yaml         # Contains all board roles as a list
highlights.yaml          # Contains all highlights as a list
```

**Proposed (optional directory mode):**
```
certifications/
├── cert-2023-06-aws-solutions-architect.yaml
├── cert-2022-11-cissp.yaml
└── cert-2021-03-cka.yaml

publications/
├── pub-2023-10-scaling-engineering-teams.yaml
└── pub-2022-06-zero-trust-architecture.yaml
```

### ID Patterns per Resource Type

| Resource | ID Pattern | Example |
|----------|------------|---------|
| Certifications | `cert-YYYY-MM-{slug}` | `cert-2023-06-aws-solutions-architect.yaml` |
| Publications | `pub-YYYY-MM-{slug}` | `pub-2022-06-zero-trust-architecture.yaml` |
| Education | `edu-YYYY-{institution-slug}` | `edu-2016-stanford-mba.yaml` |
| Board Roles | `board-YYYY-MM-{org-slug}` | `board-2022-03-cybershield-ventures.yaml` |
| Highlights | `hl-NNN-{slug}` | `hl-001-digital-transformation.yaml` |

### Three-Tier Loading Fallback

```
1. Check for *_dir config → load from directory (highest priority)
2. Check for single file → load from file (current behavior)
3. Return empty list (no data found)
```

### Config Options (DataPaths Extension)

```yaml
# .resume.yaml
data_paths:
  # Single file mode (current default)
  certifications: ./certifications.yaml

  # OR Directory mode (new)
  certifications_dir: ./certifications/

  # Same pattern for all resource types:
  publications: ./publications.yaml
  # OR
  publications_dir: ./publications/
```

### WorkUnitLoader Pattern to Follow

Reference: `src/resume_as_code/services/work_unit_loader.py`

```python
class WorkUnitLoader:
    def __init__(self, work_units_dir: Path) -> None:
        self.work_units_dir = work_units_dir
        self._yaml = YAML()
        self._yaml.preserve_quotes = True

    def load_all(self) -> list[WorkUnit]:
        work_units: list[WorkUnit] = []
        if not self.work_units_dir.exists():
            return work_units
        for yaml_file in sorted(self.work_units_dir.glob("*.yaml")):
            if yaml_file.name.startswith("."):
                continue
            with yaml_file.open() as f:
                data = self._yaml.load(f)
            wu = WorkUnit.model_validate(data)
            work_units.append(wu)
        return work_units
```

Key patterns:
- Takes directory Path in constructor
- Skips hidden files (starting with `.`)
- Sorts files alphabetically for deterministic order
- Uses ruamel.yaml with `preserve_quotes = True`
- Validates each item with Pydantic model

### Current data_loader.py Pattern

Reference: `src/resume_as_code/data_loader.py`

Current two-tier fallback:
```python
def _resolve_data_path(project_path, data_paths, key, default_filename):
    # 1. Check data_paths config
    if data_paths is not None:
        custom_path = getattr(data_paths, key, None)
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
```

Needs to become three-tier:
```python
def _resolve_data_path(project_path, data_paths, key, dir_key, default_filename, default_dir):
    # 1. Check *_dir config (highest priority)
    if data_paths is not None:
        dir_path = getattr(data_paths, dir_key, None)
        if dir_path is not None:
            resolved = project_path / dir_path
            if resolved.exists() and resolved.is_dir():
                return ("dir", resolved)

    # 2. Check default directory
    default_dir_path = project_path / default_dir
    if default_dir_path.exists() and default_dir_path.is_dir():
        # Warn if single file also exists
        if (project_path / default_filename).exists():
            logger.warning("Both %s and %s exist; using directory", default_dir, default_filename)
        return ("dir", default_dir_path)

    # 3. Check custom file path
    if data_paths is not None:
        custom_path = getattr(data_paths, key, None)
        if custom_path is not None:
            resolved = project_path / custom_path
            if resolved.exists():
                return ("file", resolved)

    # 4. Check default file
    default_path = project_path / default_filename
    if default_path.exists():
        return ("file", default_path)

    # 5. Fall back to embedded in .resume.yaml
    return ("embedded", None)
```

### DataPaths Model Extension

Reference: `src/resume_as_code/models/config.py:313-326`

Current:
```python
class DataPaths(BaseModel):
    profile: str | None = Field(default=None, description="Path to profile.yaml")
    certifications: str | None = Field(default=None, description="Path to certifications.yaml")
    education: str | None = Field(default=None, description="Path to education.yaml")
    highlights: str | None = Field(default=None, description="Path to highlights.yaml")
    publications: str | None = Field(default=None, description="Path to publications.yaml")
    board_roles: str | None = Field(default=None, description="Path to board-roles.yaml")
```

Add:
```python
    # Directory mode options (TD-005)
    certifications_dir: str | None = Field(default=None, description="Path to certifications directory")
    education_dir: str | None = Field(default=None, description="Path to education directory")
    highlights_dir: str | None = Field(default=None, description="Path to highlights directory")
    publications_dir: str | None = Field(default=None, description="Path to publications directory")
    board_roles_dir: str | None = Field(default=None, description="Path to board-roles directory")

    @model_validator(mode="after")
    def validate_no_dual_config(self) -> DataPaths:
        """Ensure both file and dir aren't specified for same resource."""
        pairs = [
            ("certifications", "certifications_dir"),
            ("education", "education_dir"),
            ("highlights", "highlights_dir"),
            ("publications", "publications_dir"),
            ("board_roles", "board_roles_dir"),
        ]
        for file_key, dir_key in pairs:
            if getattr(self, file_key) and getattr(self, dir_key):
                raise ValueError(f"Cannot specify both {file_key} and {dir_key}")
        return self
```

### CertificationService Current Pattern

Reference: `src/resume_as_code/services/certification_service.py`

Current `_uses_separated_format()` check:
```python
def _uses_separated_format(self) -> bool:
    return (self.project_path / DEFAULT_CERTIFICATIONS_FILE).exists()
```

Needs to become:
```python
def _get_storage_mode(self) -> Literal["dir", "file", "embedded"]:
    # Check directory mode first
    config = self._load_config()
    data_paths = config.get("data_paths", {})

    # Explicit dir config
    if data_paths.get("certifications_dir"):
        return "dir"

    # Default directory exists
    cert_dir = self.project_path / "certifications"
    if cert_dir.exists() and cert_dir.is_dir():
        return "dir"

    # Single file exists
    if (self.project_path / DEFAULT_CERTIFICATIONS_FILE).exists():
        return "file"

    return "embedded"
```

### Migration Command Extension

Reference: `src/resume_as_code/commands/migrate.py`

Add new `--shard` option:
```python
@click.option(
    "--shard",
    type=click.Choice(["certifications", "publications", "education", "board-roles", "highlights"]),
    help="Convert single-file storage to directory mode",
)
```

Migration flow:
1. Load items from single file
2. Create directory (e.g., `certifications/`)
3. Write each item to individual file with generated ID
4. Backup original file (e.g., `certifications.yaml.bak`)
5. Update `.resume.yaml` to add `certifications_dir: ./certifications/`
6. Delete or rename original file

### File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `src/resume_as_code/models/config.py` | Modify | Add `*_dir` fields to DataPaths, add validator |
| `src/resume_as_code/data_loader.py` | Modify | Implement three-tier fallback with directory support |
| `src/resume_as_code/services/sharded_loader.py` | Create | Generic directory loader class |
| `src/resume_as_code/services/certification_service.py` | Modify | Add directory mode support |
| `src/resume_as_code/services/publication_service.py` | Modify | Add directory mode support |
| `src/resume_as_code/services/education_service.py` | Modify | Add directory mode support |
| `src/resume_as_code/services/board_role_service.py` | Modify | Add directory mode support |
| `src/resume_as_code/services/highlight_service.py` | Modify | Add directory mode support |
| `src/resume_as_code/commands/migrate.py` | Modify | Add `--shard` option |
| `src/resume_as_code/commands/list_cmd.py` | Modify | Add source file to verbose output |
| `tests/unit/services/test_sharded_loader.py` | Create | Unit tests |
| `tests/integration/test_sharding.py` | Create | Integration tests |

### Testing Strategy

1. **Unit tests for ShardedLoader:**
   - Load from empty directory
   - Load from directory with multiple files
   - Skip hidden files
   - Handle invalid YAML gracefully
   - Save new item to directory
   - Remove item from directory

2. **Integration tests for three-tier fallback:**
   - Directory takes precedence over file
   - File takes precedence over embedded
   - Warning logged when both directory and file exist

3. **Integration tests for migrate --shard:**
   - Creates directory with correct structure
   - Backs up original file
   - Updates config
   - Generated filenames follow ID patterns

### References

- [Source: _bmad-output/implementation-artifacts/tech-debt.md#TD-005]
- [Source: _bmad-output/planning-artifacts/epics/epic-11-technical-debt-platform-enhancements.md#Story-11.2]
- Work unit loader pattern: `src/resume_as_code/services/work_unit_loader.py`
- Current data loader: `src/resume_as_code/data_loader.py`
- Config model: `src/resume_as_code/models/config.py`

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- All 8 tasks completed successfully
- 15 unit tests for ShardedLoader class
- 16 integration tests for sharding functionality
- 16 unit tests for service directory mode operations
- All acceptance criteria met:
  - AC1: Directory mode loading with three-tier fallback
  - AC2: Precedence rule (directory > file > embedded)
  - AC3: Directory mode writing for all resource types
  - AC4: migrate --shard command with backup and config update
  - AC5: List command parity with --verbose source display

### Code Review Remediation (2026-01-18)

- **Issue #1 (MEDIUM)**: Added comprehensive unit tests for service directory mode save/remove operations in `tests/unit/services/test_service_directory_mode.py` (16 new tests)
- **Issue #2 (LOW)**: Reviewed board_roles key naming - NOT a bug. Python uses underscores internally (`board_roles`), CLI/files use hyphens (`board-roles`). This follows standard Python conventions.
- **Issue #3 (LOW)**: Fixed publication field mismatch in `tests/integration/test_sharding.py` - changed `publication_type` to `type` to match Publication model
- **Issue #4 (LOW)**: Added `SourceTracked` protocol to `sharded_loader.py` for type-safe access to `_source_file` attribute with runtime-checkable support

### Change Log
- 2026-01-18: Story created with comprehensive implementation context
- 2026-01-19: Completed Task 7 (migrate --shard command) and Task 8 (tests)
- 2026-01-19: Story marked completed with all acceptance criteria verified
- 2026-01-18: Code review remediation - fixed 3 issues, added 16 service directory mode tests, added SourceTracked protocol

### File List
- `src/resume_as_code/models/config.py` - Extended DataPaths with *_dir fields
- `src/resume_as_code/data_loader.py` - Implemented three-tier loading fallback
- `src/resume_as_code/services/sharded_loader.py` - New generic directory loader with SourceTracked protocol
- `src/resume_as_code/services/certification_service.py` - Added directory mode
- `src/resume_as_code/services/publication_service.py` - Added directory mode
- `src/resume_as_code/services/education_service.py` - Added directory mode
- `src/resume_as_code/services/board_role_service.py` - Added directory mode
- `src/resume_as_code/services/highlight_service.py` - Added directory mode
- `src/resume_as_code/commands/migrate.py` - Added --shard option
- `src/resume_as_code/commands/list_cmd.py` - Added --verbose flag for source display
- `tests/unit/services/test_sharded_loader.py` - Unit tests for ShardedLoader
- `tests/unit/services/test_service_directory_mode.py` - Unit tests for service directory mode save/remove
- `tests/integration/test_sharding.py` - Integration tests for sharding
