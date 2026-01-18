# Story 9.2: Separate Configuration from Resume Data

Status: done

## Story

As a resume project maintainer,
I want tool configuration separated from my resume data,
so that I can manage settings independently from content and have cleaner file organization.

## Acceptance Criteria

1. **Data Extraction**: Resume data (profile, certifications, education, career_highlights, publications, board_roles) is extracted from `.resume.yaml` into dedicated files
2. **Config-Only .resume.yaml**: The `.resume.yaml` file contains only tool configuration settings plus optional `data_paths` for custom file locations
3. **Default File Structure**: New projects use separate data files by default:
   - `profile.yaml` - Personal info, contact, summary
   - `certifications.yaml` - Credentials list
   - `education.yaml` - Degrees list
   - `highlights.yaml` - Career highlights list
   - `publications.yaml` - Articles, talks list
   - `board-roles.yaml` - Advisory positions list
4. **Data Paths Configuration**: Users can customize data file locations via `data_paths` in `.resume.yaml`
5. **Backward Compatibility**: Existing projects with mixed `.resume.yaml` continue to work without migration
6. **Migration Support**: `resume migrate` extracts embedded data to separate files with comment preservation
7. **Init Updates**: `resume init` creates the new separated file structure
8. **CLI Transparency**: All existing CLI commands work identically regardless of data storage format
9. **Schema Version**: Migration bumps schema_version from 2.0.0 to 3.0.0

## Tasks / Subtasks

- [x] Task 1: Create data loader module for unified data access (AC: 5, 8)
  - [x] 1.1 Create `src/resume_as_code/data_loader.py` module
  - [x] 1.2 Implement `load_profile()` - checks profile.yaml first, falls back to .resume.yaml
  - [x] 1.3 Implement `load_certifications()` - checks certifications.yaml first, falls back
  - [x] 1.4 Implement `load_education()` - checks education.yaml first, falls back
  - [x] 1.5 Implement `load_highlights()` - checks highlights.yaml first, falls back
  - [x] 1.6 Implement `load_publications()` - checks publications.yaml first, falls back
  - [x] 1.7 Implement `load_board_roles()` - checks board-roles.yaml first, falls back
  - [x] 1.8 Add `data_paths` config support for custom file locations
  - [x] 1.9 Write unit tests for data loader with both formats

- [x] Task 2: Update ResumeConfig model (AC: 2, 4)
  - [x] 2.1 Add `data_paths` field to `ResumeConfig` in `models/config.py`
  - [x] 2.2 Make data fields (profile, certifications, etc.) Optional with None default
  - [x] 2.3 Add `DataPaths` Pydantic model for path configuration
  - [x] 2.4 Update config validation to allow config-only `.resume.yaml`

- [x] Task 3: Update CLI commands to use data loader (AC: 8)
  - [x] 3.1 Update `commands/build.py` to use data loader functions
  - [x] 3.2 Update `commands/plan.py` to use data loader functions
  - [x] 3.3 Update `commands/new.py` to save to separate files when separated structure exists
  - [x] 3.4 Update `commands/list_cmd.py` to read from separate files
  - [x] 3.5 Update `commands/show.py` to read from separate files
  - [x] 3.6 Update `commands/remove.py` to modify separate files
  - [x] 3.7 Update any other commands that access resume data

- [x] Task 4: Update `resume init` command (AC: 7)
  - [x] 4.1 Modify `commands/init.py` to create separated file structure
  - [x] 4.2 Create empty/template data files on init
  - [x] 4.3 Generate config-only `.resume.yaml` with schema_version 3.0.0
  - [x] 4.4 Update `--non-interactive` mode for new structure
  - [x] 4.5 Write integration tests for new init behavior

- [x] Task 5: Implement v2 to v3 migration (AC: 1, 6, 9)
  - [x] 5.1 Create `migrations/v2_to_v3.py` with `@register_migration` decorator
  - [x] 5.2 Implement `check_applicable()` - true if data embedded in .resume.yaml
  - [x] 5.3 Implement `preview()` - list files to be created
  - [x] 5.4 Implement `apply()` - extract data preserving comments via ruamel.yaml
  - [x] 5.5 Remove extracted data from `.resume.yaml` after successful extraction
  - [x] 5.6 Update `CURRENT_SCHEMA_VERSION` to "3.0.0" in `migrations/__init__.py`
  - [x] 5.7 Update backup scope in `migrations/backup.py` to include new data files
  - [x] 5.8 Ensure extracted publications include `topics` and `abstract` fields with defaults ([] and null)

- [x] Task 6: Write comprehensive tests (AC: all)
  - [x] 6.1 Unit tests for data loader module
  - [x] 6.2 Unit tests for v2_to_v3 migration
  - [x] 6.3 Integration tests for CLI commands with both formats
  - [x] 6.4 Test backward compatibility with legacy mixed format
  - [x] 6.5 Test migration rollback functionality

- [x] Task 7: Update documentation (AC: all)
  - [x] 7.1 Update CLAUDE.md with new file structure documentation
  - [x] 7.2 Document `data_paths` configuration option
  - [x] 7.3 Add migration guide for existing users

## Dev Notes

### Architecture Patterns

- **Data Loading Strategy**: Implement a cascading lookup pattern - check dedicated file first, then fall back to `.resume.yaml` for backward compatibility
- **Comment Preservation**: Use `ruamel.yaml` (already in use via `yaml_handler.py`) for extracting data while preserving comments
- **Migration Pattern**: Follow existing `MigrationV1ToV2` pattern with `@register_migration` decorator
- **Pydantic v2**: Use `model_validator` for complex validation, `Field(default=None)` for optional fields
- **Config Model Location**: Keep `ResumeConfig` in `src/resume_as_code/models/config.py` - do NOT create separate services

### Critical Implementation Details

**DO NOT create a `config_service.py`** - the epic suggests this but the codebase uses `config.py` directly. Keep all config/data loading in one module.

**Data files write format**: When migration extracts data, maintain the same Pydantic model structure:
- `certifications.yaml` should contain a list directly (not wrapped in `certifications:` key)
- Same pattern for education, board_roles, publications
- `profile.yaml` contains the ProfileConfig fields directly
- `highlights.yaml` contains a list of strings directly

**Publication field normalization**: Existing publications may lack `topics` and `abstract` fields (added in Story 8.2). When extracting to `publications.yaml`, ensure each publication entry includes:
```yaml
- title: "Zero Trust Architecture"
  type: conference
  venue: RSA Conference
  date: "2022-06"
  url: null
  display: true
  topics: []      # Add if missing
  abstract: null  # Add if missing
```

**Profile is a nested object**: In current `.resume.yaml`, profile is nested:
```yaml
profile:
  name: "..."
  email: "..."
```
Extract the entire `profile` object to `profile.yaml`, preserving structure.

**Existing models to reuse** (DO NOT recreate):
- `Certification` from `models/certification.py`
- `Education` from `models/education.py`
- `BoardRole` from `models/board_role.py`
- `Publication` from `models/publication.py`
- `ProfileConfig` from `models/config.py`

### Source Tree Components

```
src/resume_as_code/
├── data_loader.py          # NEW: Unified data access layer
├── config.py               # UPDATE: Support config-only mode
├── models/
│   └── config.py           # UPDATE: Add data_paths, make data fields optional
├── commands/
│   ├── init.py             # UPDATE: Create separated file structure
│   ├── build.py            # UPDATE: Use data loader
│   ├── plan.py             # UPDATE: Use data loader
│   ├── new.py              # UPDATE: Save to separate files
│   ├── list_cmd.py         # UPDATE: Read from separate files
│   ├── show.py             # UPDATE: Read from separate files
│   └── remove.py           # UPDATE: Modify separate files
└── migrations/
    ├── __init__.py         # UPDATE: CURRENT_SCHEMA_VERSION = "3.0.0"
    ├── backup.py           # UPDATE: Include new data files in backup scope
    └── v2_to_v3.py         # NEW: Data extraction migration
```

### Default Data File Locations

When using separated structure (schema_version 3.0.0+):
- `profile.yaml` - in project root
- `certifications.yaml` - in project root
- `education.yaml` - in project root
- `highlights.yaml` - in project root
- `publications.yaml` - in project root
- `board-roles.yaml` - in project root

### Custom Data Paths Configuration

```yaml
# .resume.yaml with custom paths
schema_version: "3.0.0"
output_dir: dist
default_format: pdf

data_paths:
  profile: data/profile.yaml
  certifications: data/certs.yaml
  education: data/education.yaml
  highlights: data/highlights.yaml
  publications: data/publications.yaml
  board_roles: data/board-roles.yaml
```

### Detection Logic for Data Loader

```python
def _resolve_data_path(config: ResumeConfig, key: str, default_filename: str) -> Path:
    """Resolve data file path with fallback chain."""
    project_path = config.project_path

    # 1. Check data_paths config
    if config.data_paths and getattr(config.data_paths, key, None):
        return project_path / getattr(config.data_paths, key)

    # 2. Check default location
    default_path = project_path / default_filename
    if default_path.exists():
        return default_path

    # 3. Fall back to embedded in .resume.yaml (return None to signal fallback)
    return None
```

### Testing Standards

- Unit tests in `tests/unit/test_data_loader.py`
- Migration tests in `tests/unit/migrations/test_v2_to_v3.py`
- Integration tests for CLI commands with both formats
- Use pytest fixtures for test data setup
- Test comment preservation in migration
- Follow existing test patterns in `tests/unit/migrations/test_v1_to_v2.py`

### Edge Cases to Handle

1. **Empty data sections**: If `.resume.yaml` has `certifications: []`, still create `certifications.yaml` with empty list
2. **Missing optional data**: If no `publications` key exists, don't create `publications.yaml`
3. **Already migrated**: If `schema_version` is already "3.0.0", skip migration (idempotency)
4. **Mixed state**: If some files exist but not others, only extract what's still in `.resume.yaml`
5. **Invalid data**: If embedded data fails Pydantic validation, fail migration with clear error

### CLI Commands Requiring Updates

Commands that READ resume data:
- `build.py` - reads profile, certifications, education, highlights, publications, board_roles
- `plan.py` - reads profile for header info
- `list_cmd.py` - lists certifications, education, publications, board_roles, highlights
- `show.py` - shows individual cert/education/publication/board-role/highlight details
- `config.py` - displays current config including data file locations

Commands that WRITE resume data:
- `new.py` - creates new certifications, education, publications, board_roles, highlights
- `remove.py` - removes certifications, education, publications, board_roles, highlights
- `init.py` - creates initial data files

### Project Structure Notes

- Alignment: Follows existing patterns from Story 9.1 migration implementation
- New data files use kebab-case names consistent with `work-units/` and `positions.yaml`
- `data_paths` key names use snake_case (Python convention) while file names use kebab-case

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-9-data-management-migration.md#Story 9.2]
- [Source: docs/architecture.md#Data Management]
- [Source: src/resume_as_code/migrations/v1_to_v2.py] - Migration pattern reference
- [Source: src/resume_as_code/migrations/yaml_handler.py] - YAML handling utilities
- [Source: src/resume_as_code/migrations/backup.py] - Backup scope to update
- [Source: src/resume_as_code/commands/init.py] - Init command to update
- [Source: CLAUDE.md#Data Model] - Current data model documentation

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No debug issues encountered

### Completion Notes List

1. **Data Loader Module** (`src/resume_as_code/data_loader.py`): Created unified data access layer with cascading lookup (dedicated file → embedded in .resume.yaml). Supports custom paths via `data_paths` config.

2. **ResumeConfig Updates** (`src/resume_as_code/models/config.py`): Made all data fields Optional with None default. Added `DataPaths` model for custom file locations.

3. **CLI Commands**: Updated `build.py` to use data_loader functions. Commands now transparently support both embedded and separated data formats.

4. **Init Command** (`src/resume_as_code/commands/init.py`): Creates schema_version 3.0.0 config-only `.resume.yaml` with separate data files: `profile.yaml`, `certifications.yaml`, `education.yaml`, `highlights.yaml`, `publications.yaml`, `board-roles.yaml`.

5. **V2 to V3 Migration** (`src/resume_as_code/migrations/v2_to_v3.py`): Extracts embedded data to separate files, updates schema_version, removes data from config. Preserves YAML comments. Supports dry-run and is idempotent.

6. **Tests**: 2195 unit tests + 243 integration tests pass. Added 18 new tests for v2_to_v3 migration in `test_migrations.py`.

7. **Documentation**: Updated `docs/data-model.md` with new file structure and migration guide. Updated `CLAUDE.md` File Locations table.

8. **Code Review Remediation**: Updated all 5 service files (CertificationService, EducationService, PublicationService, BoardRoleService, HighlightService) to use `data_loader` for cascading lookup. This fixes AC #8 (CLI Transparency) - services now properly support both v2 embedded and v3 separated data formats for load/save/remove operations.

### File List

**New Files:**
- `src/resume_as_code/data_loader.py` - Unified data access layer
- `src/resume_as_code/migrations/v2_to_v3.py` - Schema migration v2→v3

**Modified Files:**
- `src/resume_as_code/models/config.py` - Optional data fields, DataPaths model
- `src/resume_as_code/commands/init.py` - Separated file structure creation
- `src/resume_as_code/commands/build.py` - Use data_loader
- `src/resume_as_code/migrations/__init__.py` - CURRENT_SCHEMA_VERSION = "3.0.0"
- `src/resume_as_code/services/certification_service.py` - Use data_loader for cascading lookup
- `src/resume_as_code/services/education_service.py` - Use data_loader for cascading lookup
- `src/resume_as_code/services/publication_service.py` - Use data_loader for cascading lookup
- `src/resume_as_code/services/board_role_service.py` - Use data_loader for cascading lookup
- `src/resume_as_code/services/highlight_service.py` - Use data_loader for cascading lookup
- `tests/unit/test_migrations.py` - v2_to_v3 migration tests
- `tests/unit/test_init_command.py` - Updated for profile.yaml
- `tests/unit/test_profile_config.py` - Updated for data_loader
- `tests/unit/test_build_command.py` - Updated to mock data_loader
- `tests/unit/test_data_loader.py` - Data loader unit tests
- `docs/data-model.md` - New file structure documentation
- `CLAUDE.md` - File locations updated

