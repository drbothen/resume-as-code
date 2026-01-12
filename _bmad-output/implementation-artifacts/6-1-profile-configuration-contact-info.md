# Story 6.1: Profile Configuration & Contact Info Loading

Status: done

## Story

As a **user**,
I want **to store my profile information in configuration**,
So that **my resumes include accurate contact details without manual editing**.

## Acceptance Criteria

1. **Given** I add profile fields to `.resume.yaml`
   **When** the config is:
   ```yaml
   profile:
     name: "Joshua Magady"
     email: "joshua@example.com"
     phone: "555-123-4567"
     location: "Austin, TX"
     linkedin: "https://linkedin.com/in/jmagady"
     github: "https://github.com/jmagady"
     title: "Senior Platform Engineer"
   ```
   **Then** the config loads and validates successfully

2. **Given** I run `resume build --jd file.txt`
   **When** the resume is generated
   **Then** the header shows my actual name (not "Your Name")
   **And** contact info appears in the header section
   **And** LinkedIn URL is displayed (optionally as shortened text)

3. **Given** profile is missing from config
   **When** I run `resume build`
   **Then** a warning is displayed: "No profile configured. Run `resume config profile.name 'Your Name'` to set."
   **And** placeholders are used (backward compatible)

4. **Given** I run `resume config profile.name "Jane Doe"`
   **When** the command completes
   **Then** the value is saved to `.resume.yaml`
   **And** subsequent builds use the new name

5. **Given** I run `resume config --json profile`
   **When** the command executes
   **Then** profile data is returned as JSON for scripting

## Tasks / Subtasks

- [x] Task 1: Create ProfileConfig model (AC: #1)
  - [x] 1.1: Create `ProfileConfig` Pydantic model in `models/config.py`
  - [x] 1.2: Add fields: name, email, phone, location, linkedin, github, website, title, summary
  - [x] 1.3: Use `HttpUrl` type for URL fields with proper validation
  - [x] 1.4: Add `profile: ProfileConfig` field to `ResumeConfig`

- [x] Task 2: Update config loader (AC: #1, #4)
  - [x] 2.1: Update `get_config()` in `config.py` to parse profile section
  - [x] 2.2: Support nested config access: `resume config profile.email`
  - [x] 2.3: Handle backward compatibility (no profile = default ProfileConfig)

- [x] Task 3: Update build command (AC: #2, #3)
  - [x] 3.1: Update `_load_contact_info()` to read from `config.profile`
  - [x] 3.2: Map ProfileConfig fields to ContactInfo model
  - [x] 3.3: Add warning when profile.name is not configured
  - [x] 3.4: Fall back to "Your Name" placeholder for backward compatibility

- [x] Task 4: Update config command for profile access (AC: #4, #5)
  - [x] 4.1: Ensure nested key access works (`profile.name`, `profile.email`)
  - [x] 4.2: Add JSON output support for profile section
  - [x] 4.3: Handle setting nested profile values

- [x] Task 5: Testing
  - [x] 5.1: Add unit tests for ProfileConfig validation
  - [x] 5.2: Add tests for profile loading from config file
  - [x] 5.3: Add tests for build command using profile
  - [x] 5.4: Add tests for config command with profile keys
  - [x] 5.5: Add test for warning when profile missing

- [x] Task 6: Code quality verification
  - [x] 6.1: Run `ruff check src tests --fix`
  - [x] 6.2: Run `mypy src --strict` with zero errors
  - [x] 6.3: Run `pytest` - all tests pass

## Dev Notes

### Architecture Compliance

This story extends the configuration system from Epic 1 (Story 1.3) to support profile information per Architecture Section 2.3. The ProfileConfig model follows the same patterns as existing ScoringWeights model.

**Critical Rules from project-context.md:**
- Use `|` union syntax for optional fields (Python 3.10+)
- Use `model_validator(mode='after')` if cross-field validation needed
- Use snake_case for all YAML field names
- Never use `print()` - use Rich console
- Keep commands thin, services thick

### Project Structure Notes

**Files to modify:**
- `src/resume_as_code/models/config.py` - Add ProfileConfig model
- `src/resume_as_code/config.py` - Update config loading
- `src/resume_as_code/commands/build.py` - Update `_load_contact_info()`
- `src/resume_as_code/commands/config_cmd.py` - Ensure nested key support

**Files to create:**
- `tests/unit/test_profile_config.py` - Unit tests for profile

### ProfileConfig Model Design

```python
from pydantic import BaseModel, Field, HttpUrl

class ProfileConfig(BaseModel):
    """User profile information for resume header."""

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: HttpUrl | None = None
    github: HttpUrl | None = None
    website: HttpUrl | None = None
    title: str | None = None  # Professional title/headline
    summary: str | None = None  # Executive summary template
```

### Updated ResumeConfig

```python
class ResumeConfig(BaseModel):
    """Complete configuration for Resume as Code."""

    # ... existing fields ...

    # Profile information (NEW)
    profile: ProfileConfig = Field(default_factory=ProfileConfig)
```

### Updated _load_contact_info

```python
def _load_contact_info(config: ResumeConfig) -> ContactInfo:
    """Load contact info from config profile.

    Args:
        config: Application configuration.

    Returns:
        ContactInfo populated from profile, with warnings for missing data.
    """
    profile = config.profile

    # Warn if name not configured
    if not profile.name:
        console.print(
            "[yellow]Warning:[/] No profile configured. "
            "Run `resume config profile.name 'Your Name'` to set."
        )

    return ContactInfo(
        name=profile.name or "Your Name",
        email=profile.email,
        phone=profile.phone,
        location=profile.location,
        linkedin=str(profile.linkedin) if profile.linkedin else None,
        github=str(profile.github) if profile.github else None,
        website=str(profile.website) if profile.website else None,
    )
```

### Example .resume.yaml with Profile

```yaml
# Resume-as-Code Project Configuration

# Profile information
profile:
  name: "Joshua Magady"
  email: "joshua@example.com"
  phone: "555-123-4567"
  location: "Austin, TX"
  linkedin: "https://linkedin.com/in/jmagady"
  github: "https://github.com/jmagady"
  title: "Senior Platform Engineer"
  summary: |
    Experienced platform engineer with 10+ years building
    scalable infrastructure and leading technical teams.

# Output settings (existing)
output_dir: ./dist
default_template: modern
```

### Dependencies

This story REQUIRES:
- Story 1.3 (Configuration Hierarchy) - Base config system [DONE]
- Story 5.6 (Output Configuration) - Config command pattern [DONE]

This story ENABLES:
- Story 6.4 (Executive Resume Template) - Uses profile.title and profile.summary
- Story 6.2 (Certifications) - Similar config pattern

### Git Intelligence

Recent commits show:
- `feat(config)` pattern for config-related changes
- Story 5.5/5.6 established config extension patterns
- Tests in `tests/unit/test_config*.py`

### Testing Strategy

```python
# tests/unit/test_profile_config.py

class TestProfileConfig:
    """Tests for profile configuration."""

    def test_profile_loads_from_yaml(self, tmp_path):
        """Should load profile from .resume.yaml."""
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("""
profile:
  name: "Test User"
  email: "test@example.com"
""")
        config = get_config(tmp_path)
        assert config.profile.name == "Test User"
        assert config.profile.email == "test@example.com"

    def test_profile_defaults_when_missing(self, tmp_path):
        """Should use defaults when profile not in config."""
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("output_dir: ./dist")

        config = get_config(tmp_path)
        assert config.profile.name is None
        assert config.profile.email is None

    def test_linkedin_url_validation(self, tmp_path):
        """Should validate LinkedIn URL format."""
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("""
profile:
  linkedin: "not-a-url"
""")
        with pytest.raises(ValidationError):
            get_config(tmp_path)
```

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_profile_config.py -v

# Manual verification:
uv run resume config profile.name "Test User"
uv run resume config --list | grep profile
uv run resume build --jd examples/job-description.txt
# Check generated PDF/DOCX for "Test User" instead of "Your Name"
```

### References

- [Source: epics.md#Story 6.1](_bmad-output/planning-artifacts/epics.md)
- [Source: architecture.md#Section 2.3](_bmad-output/planning-artifacts/architecture.md)
- [Related: Story 5.6 Output Configuration](_bmad-output/implementation-artifacts/5-6-output-configuration.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None - implementation proceeded without issues.

### Completion Notes List

- Created `ProfileConfig` Pydantic model with HttpUrl validation for linkedin/github/website fields
- Added `profile: ProfileConfig` field to `ResumeConfig` with default_factory
- Updated `_load_contact_info()` in build command to read from config.profile
- Verified existing config command already supports nested key access (e.g., `profile.name`)
- Added warning when profile.name is not configured (backward compatible fallback to "Your Name")
- Fixed 5 existing test mocks in test_build_command.py that needed profile attribute
- All 944 tests pass, mypy strict passes, ruff passes

### File List

**Modified:**
- src/resume_as_code/models/config.py - Added ProfileConfig model and profile field to ResumeConfig
- src/resume_as_code/commands/build.py - Updated _load_contact_info() to use config.profile
- tests/unit/test_build_command.py - Added profile mock to 5 existing tests

**Created:**
- tests/unit/test_profile_config.py - 19 tests for ProfileConfig, config loading, and build command

**Added tests to:**
- tests/unit/test_config_cmd.py - Added TestConfigNestedAccess class with 3 tests for profile access

## Senior Developer Review (AI)

### Review Date
2026-01-12

### Reviewer
Claude Opus 4.5 (adversarial code review workflow)

### Issues Found and Remediated

**HIGH Severity (2 found, 2 fixed):**

1. **H1: Test claimed to verify warning but didn't assert on output**
   - Location: `tests/unit/test_profile_config.py:155-171`
   - Issue: `capsys` fixture was injected but warning assertion was missing
   - Fix: Added mock for `console.print` and assertion that warning contains expected text

2. **H2: `profile.title` and `profile.summary` fields existed but were unused**
   - Location: `src/resume_as_code/commands/build.py:129-134`
   - Issue: ProfileConfig had title/summary but they weren't mapped to ResumeData
   - Fix: Added title to ContactInfo model, mapped title and summary in build command

**MEDIUM Severity (3 found, 3 fixed):**

1. **M1: No integration test for profile → ResumeData flow**
   - Fix: Added `TestProfileSummaryIntegration` class with end-to-end test

2. **M2: Rich console can't be captured by capsys**
   - Fix: Changed to mocking `console.print` instead of using capsys

3. **M3: ContactInfo model lacked title field**
   - Location: `src/resume_as_code/models/resume.py:11-20`
   - Fix: Added `title: str | None = None` field to ContactInfo

**LOW Severity (2 found, 2 fixed):**

1. **L1: URL normalization behavior undocumented**
   - Fix: Added comment explaining Pydantic HttpUrl trailing slash normalization

2. **L2: Test file untracked in git**
   - Fix: File will be staged with other changes

### Files Modified During Review

- `src/resume_as_code/models/resume.py` - Added title field to ContactInfo
- `src/resume_as_code/commands/build.py` - Map profile.title and profile.summary
- `tests/unit/test_profile_config.py` - Fixed warning test, added integration test (21 tests now)
- `tests/unit/test_build_command.py` - Added title/summary to mock profiles

### Verification

- All 946 tests pass (2 new tests added)
- mypy --strict passes
- ruff check passes

### Outcome

**APPROVED** - All issues remediated, story marked as done.
