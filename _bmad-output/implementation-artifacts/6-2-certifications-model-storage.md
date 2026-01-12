# Story 6.2: Certifications Model & Storage

Status: done

## Story

As a **user**,
I want **to store my professional certifications in configuration**,
So that **they appear on my resume to meet job requirements**.

## Acceptance Criteria

1. **Given** I add certifications to `.resume.yaml`
   **When** the config is:
   ```yaml
   certifications:
     - name: "AWS Solutions Architect - Professional"
       issuer: "Amazon Web Services"
       date: "2024-06"
       credential_id: "ABC123XYZ"
       url: "https://aws.amazon.com/verification/ABC123XYZ"
     - name: "CISSP"
       issuer: "ISC²"
       date: "2023-01"
       expires: "2026-01"
   ```
   **Then** the config loads and validates successfully
   **And** certifications are available for template rendering

2. **Given** certifications exist in config
   **When** I run `resume build --jd file.txt`
   **Then** a "Certifications" section appears in the resume
   **And** each certification shows name, issuer, and date

3. **Given** a certification has an expiration date
   **When** it is rendered
   **Then** the expiration is shown: "CISSP (ISC², 2023 - expires 2026)"

4. **Given** a certification has expired
   **When** it is rendered
   **Then** it is marked or optionally excluded based on config

5. **Given** no certifications exist in config
   **When** the resume is generated
   **Then** no certifications section appears (graceful absence)

6. **Given** I run `resume config certifications --list`
   **When** the command executes
   **Then** all certifications are displayed in a table

## Tasks / Subtasks

- [x] Task 1: Create Certification model (AC: #1)
  - [x] 1.1: Create `Certification` Pydantic model in `models/certification.py`
  - [x] 1.2: Add fields: name, issuer, date, expires, credential_id, url, display
  - [x] 1.3: Use `HttpUrl` type for URL field with validation
  - [x] 1.4: Add date format validation (YYYY-MM)
  - [x] 1.5: Add `certifications: list[Certification]` field to `ResumeConfig`

- [x] Task 2: Update ResumeData model (AC: #2, #5)
  - [x] 2.1: Add `certifications: list[Certification]` to `ResumeData`
  - [x] 2.2: Added `get_active_certifications()` method to filter displayable certs
  - [x] 2.3: Handle empty certifications list gracefully

- [x] Task 3: Update build command (AC: #2, #3, #4, #5)
  - [x] 3.1: Load certifications from config in build command
  - [x] 3.2: Pass certifications to ResumeData
  - [x] 3.3: Add expiration status calculation (active/expires_soon/expired)
  - [x] 3.4: Filter out expired certs if `display: false` or config option set

- [x] Task 4: Update templates (AC: #2, #3)
  - [x] 4.1: Add certifications section to `modern.html` template
  - [x] 4.2: Add Jinja2 conditional: `{% if resume.get_active_certifications() %}`
  - [x] 4.3: Format certification display with issuer and dates
  - [x] 4.4: Handle expiration display format
  - [x] 4.5: Add certifications CSS styling

- [x] Task 5: Update DOCX provider (AC: #2)
  - [x] 5.1: Add `_add_certifications_section()` method to DOCXProvider
  - [x] 5.2: Use Word list formatting for certifications

- [x] Task 6: Config command support (AC: #6)
  - [x] 6.1: Support `resume config certifications --list` for table display
  - [x] 6.2: Display certification status (active/expires_soon/expired)

- [x] Task 7: Testing
  - [x] 7.1: Add unit tests for Certification model validation
  - [x] 7.2: Add tests for certification loading from config
  - [x] 7.3: Add tests for template rendering with certifications
  - [x] 7.4: Add tests for empty certifications handling
  - [x] 7.5: Add tests for expiration status calculation

- [x] Task 8: Code quality verification
  - [x] 8.1: Run `ruff check src tests --fix`
  - [x] 8.2: Run `mypy src --strict` with zero errors
  - [x] 8.3: Run `pytest` - all tests pass (992 tests)

## Dev Notes

### Architecture Compliance

This story adds professional certifications storage following the same patterns established in Story 6.1 (ProfileConfig) and Story 5.6 (Output Configuration). The Certification model follows Pydantic v2 patterns per Architecture Section 1.3.

**Critical Rules from project-context.md:**
- Use `|` union syntax for optional fields (Python 3.10+)
- Use snake_case for all YAML field names
- Never use `print()` - use Rich console
- Templates render gracefully when optional sections missing

### Certification Model Design

```python
# src/resume_as_code/models/certification.py

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Certification(BaseModel):
    """Professional certification record."""

    name: str
    issuer: str | None = None
    date: str | None = None  # YYYY-MM format
    expires: str | None = None  # YYYY-MM format
    credential_id: str | None = None
    url: HttpUrl | None = None
    display: bool = Field(default=True)  # Allow hiding without deleting

    @field_validator("date", "expires", mode="before")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate YYYY-MM date format."""
        if v is None:
            return None
        # Accept YYYY-MM or YYYY-MM-DD
        import re
        if not re.match(r"^\d{4}-\d{2}(-\d{2})?$", v):
            raise ValueError("Date must be in YYYY-MM format")
        return v[:7]  # Normalize to YYYY-MM

    def get_status(self) -> Literal["active", "expires_soon", "expired"]:
        """Calculate certification status based on expiration."""
        if not self.expires:
            return "active"

        from datetime import datetime
        expires_date = datetime.strptime(self.expires, "%Y-%m").date()
        today = date.today()

        if expires_date < today:
            return "expired"
        if expires_date < today.replace(month=today.month + 3):  # ~90 days
            return "expires_soon"
        return "active"

    def format_display(self) -> str:
        """Format certification for resume display."""
        parts = [self.name]
        if self.issuer:
            parts.append(f"({self.issuer}")
            if self.date:
                parts[-1] += f", {self.date[:4]}"  # Year only
            if self.expires:
                parts[-1] += f" - expires {self.expires[:4]}"
            parts[-1] += ")"
        elif self.date:
            parts.append(f"({self.date[:4]})")
        return " ".join(parts)
```

### Updated ResumeConfig

```python
# In models/config.py

from resume_as_code.models.certification import Certification

class ResumeConfig(BaseModel):
    """Complete configuration for Resume as Code."""

    # ... existing fields ...

    # Certifications (NEW)
    certifications: list[Certification] = Field(default_factory=list)
```

### Template Updates

```html
<!-- In templates/modern.html -->

{% if resume.certifications %}
<section class="certifications">
  <h2>Certifications</h2>
  <ul class="cert-list">
    {% for cert in resume.certifications %}
    {% if cert.display %}
    <li>
      <strong>{{ cert.name }}</strong>
      {% if cert.issuer %}, {{ cert.issuer }}{% endif %}
      {% if cert.date %}, {{ cert.date[:4] }}{% endif %}
      {% if cert.expires %} - expires {{ cert.expires[:4] }}{% endif %}
    </li>
    {% endif %}
    {% endfor %}
  </ul>
</section>
{% endif %}
```

### CSS Styling

```css
/* In templates/modern.css */

.certifications {
  margin-top: 1.5em;
}

.cert-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.cert-list li {
  margin-bottom: 0.5em;
}

.cert-list li strong {
  color: #2c3e50;
}
```

### Expiration Status Logic

```python
def get_certification_status(cert: Certification) -> str:
    """Calculate certification status for display."""
    if not cert.expires:
        return "active"

    from datetime import datetime, timedelta
    expires = datetime.strptime(cert.expires, "%Y-%m").date()
    today = datetime.now().date()

    if expires < today:
        return "expired"
    if expires < today + timedelta(days=90):
        return "expires_soon"
    return "active"
```

### Dependencies

This story REQUIRES:
- Story 6.1 (Profile Configuration) - Config pattern established

This story ENABLES:
- Story 6.5 (Template Certifications Section) - Full template integration
- Story 6.11 (Certification Management Commands) - CLI management

### Files to Modify

**New Files:**
- `src/resume_as_code/models/certification.py` - Certification model
- `tests/unit/test_certification.py` - Unit tests

**Modified Files:**
- `src/resume_as_code/models/config.py` - Add certifications list
- `src/resume_as_code/models/resume.py` - Add certifications to ResumeData
- `src/resume_as_code/commands/build.py` - Load and pass certifications
- `src/resume_as_code/templates/modern.html` - Add certifications section
- `src/resume_as_code/templates/modern.css` - Add certifications styling
- `src/resume_as_code/providers/docx.py` - Add certifications to DOCX

### Example .resume.yaml

```yaml
# Professional Certifications
certifications:
  - name: "AWS Solutions Architect - Professional"
    issuer: "Amazon Web Services"
    date: "2024-06"
    expires: "2027-06"
    credential_id: "ABC123XYZ"
    url: "https://aws.amazon.com/verification/ABC123XYZ"

  - name: "CISSP"
    issuer: "ISC²"
    date: "2023-01"
    expires: "2026-01"

  - name: "Kubernetes Administrator (CKA)"
    issuer: "CNCF"
    date: "2024-01"
    expires: "2027-01"

  - name: "PMP"
    issuer: "PMI"
    date: "2020-06"
    display: false  # Hide expired cert
```

### Testing Strategy

```python
# tests/unit/test_certification.py

import pytest
from pydantic import ValidationError

from resume_as_code.models.certification import Certification


class TestCertificationModel:
    """Tests for Certification model."""

    def test_minimal_certification(self):
        """Should create cert with only name."""
        cert = Certification(name="AWS SAP")
        assert cert.name == "AWS SAP"
        assert cert.issuer is None

    def test_full_certification(self):
        """Should create cert with all fields."""
        cert = Certification(
            name="AWS Solutions Architect",
            issuer="Amazon Web Services",
            date="2024-06",
            expires="2027-06",
            credential_id="ABC123",
        )
        assert cert.name == "AWS Solutions Architect"
        assert cert.date == "2024-06"

    def test_date_format_validation(self):
        """Should validate YYYY-MM format."""
        with pytest.raises(ValidationError):
            Certification(name="Test", date="invalid")

    def test_date_normalization(self):
        """Should normalize YYYY-MM-DD to YYYY-MM."""
        cert = Certification(name="Test", date="2024-06-15")
        assert cert.date == "2024-06"

    def test_status_active(self):
        """Should return active for no expiration."""
        cert = Certification(name="Test")
        assert cert.get_status() == "active"

    def test_status_expired(self):
        """Should return expired for past date."""
        cert = Certification(name="Test", expires="2020-01")
        assert cert.get_status() == "expired"

    def test_display_format(self):
        """Should format certification for display."""
        cert = Certification(
            name="CISSP",
            issuer="ISC²",
            date="2023-01",
            expires="2026-01",
        )
        display = cert.format_display()
        assert "CISSP" in display
        assert "ISC²" in display
```

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_certification.py -v

# Manual verification:
# Add certifications to .resume.yaml
uv run resume build --jd examples/job-description.txt
# Check PDF for Certifications section
```

### References

- [Source: epics.md#Story 6.2](_bmad-output/planning-artifacts/epics.md)
- [Related: Story 6.1 Profile Configuration](_bmad-output/implementation-artifacts/6-1-profile-configuration-contact-info.md)
- [Related: Story 6.5 Template Certifications Section](_bmad-output/planning-artifacts/epics.md#story-65)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- All 8 tasks completed successfully
- 992 tests passing
- Code review remediation: Fixed expires display format (year-only per AC #3)

### File List

**New Files:**
- `src/resume_as_code/models/certification.py` - Certification Pydantic model
- `tests/unit/test_certification.py` - Comprehensive unit tests

**Modified Files:**
- `src/resume_as_code/commands/build.py` - Load and pass certifications to ResumeData
- `src/resume_as_code/commands/config_cmd.py` - Add certifications --list support
- `src/resume_as_code/models/__init__.py` - Export Certification model
- `src/resume_as_code/models/config.py` - Add certifications field to ResumeConfig
- `src/resume_as_code/models/manifest.py` - Minor type annotation update
- `src/resume_as_code/models/resume.py` - Add certifications field and get_active_certifications()
- `src/resume_as_code/providers/docx.py` - Add _add_certifications_section() method
- `src/resume_as_code/templates/modern.css` - Add certifications section styling
- `src/resume_as_code/templates/modern.html` - Add certifications template section
- `tests/unit/test_build_command.py` - Add certifications build tests
- `tests/unit/test_config_cmd.py` - Add certifications config command tests
- `tests/unit/test_docx_provider.py` - Add certifications DOCX tests
- `tests/unit/test_profile_config.py` - Update for certifications support
- `tests/unit/test_resume_model.py` - Add certifications model tests
