# System-Level Testability Assessment

**Project:** Resume as Code
**Date:** 2026-01-10
**Assessor:** TEA (Master Test Architect)
**Phase:** System-Level Review (Phase 3 - Pre-Implementation Readiness)

---

## Executive Summary

**Overall Testability Score:** GOOD (7/10)

The Resume as Code architecture is well-suited for testing due to its modular design with clear separation of concerns. The Pydantic-based validation layer, Click CLI framework, and Jinja2 templating engine all have mature testing ecosystems. The primary testability concerns are:

1. **PDF generation** (WeasyPrint) - Requires specialized assertion strategies
2. **External file I/O** - YAML loading needs isolation patterns
3. **Template rendering** - Snapshot testing recommended for complex outputs

**Gate Recommendation:** PASS with CONCERNS - Proceed to implementation readiness with documented mitigation plans for identified risks.

---

## Utility Tree: NFR-Driven Risk Assessment

### Performance (Weight: HIGH)

| Quality Attribute | Stimulus | Response Measure | Risk Score | Test Strategy |
|-------------------|----------|------------------|------------|---------------|
| **Rendering Speed** | User generates PDF from 3-page resume | Complete in <2 seconds | **4** (P:2, I:2) | Unit: Mock WeasyPrint, Integration: Real rendering with timing assertions |
| **Validation Speed** | User loads complex YAML (50+ fields) | Parse + validate in <500ms | **2** (P:1, I:2) | Unit: Pydantic model validation benchmarks |
| **Memory Usage** | Process large template with embedded images | Memory <100MB peak | **3** (P:1, I:3) | Integration: Memory profiling during PDF generation |

### Reliability (Weight: HIGH)

| Quality Attribute | Stimulus | Response Measure | Risk Score | Test Strategy |
|-------------------|----------|------------------|------------|---------------|
| **Validation Errors** | Invalid YAML structure | Clear error with line number | **6** (P:2, I:3) | Unit: Error message format tests, Integration: Full validation pipeline |
| **File Not Found** | Missing YAML or template file | Graceful error, non-zero exit code | **4** (P:2, I:2) | Unit: Error handling tests |
| **Template Errors** | Jinja2 syntax errors in custom templates | Descriptive error message | **6** (P:2, I:3) | Integration: Template validation with error capture |

### Maintainability (Weight: MEDIUM)

| Quality Attribute | Stimulus | Response Measure | Risk Score | Test Strategy |
|-------------------|----------|------------------|------------|---------------|
| **Code Coverage** | New features added | Maintain >80% line coverage | **3** (P:1, I:3) | CI: pytest-cov threshold enforcement |
| **Test Isolation** | Tests run in parallel | No state pollution | **4** (P:2, I:2) | Unit: Fixture-based isolation with tmp_path |

### Usability (Weight: MEDIUM)

| Quality Attribute | Stimulus | Response Measure | Risk Score | Test Strategy |
|-------------------|----------|------------------|------------|---------------|
| **CLI Help** | User runs `--help` | Clear, formatted usage info | **2** (P:1, I:2) | Integration: Click test client help output assertions |
| **Progress Feedback** | Long PDF generation | Visual progress indicator | **3** (P:1, I:3) | Integration: Rich console output capture |

---

## Test Strategy by Level

### Unit Tests (Target: 60% of test effort)

**Scope:** Pure business logic, validators, data transformations

| Component | Test Focus | Recommended Patterns |
|-----------|------------|---------------------|
| `loader.py` | YAML parsing, schema loading | Parametrized tests with valid/invalid fixtures |
| `validator.py` | Pydantic model validation | Boundary tests, error message assertions |
| `renderer.py` | Output format selection, context building | Mock Jinja2 environment, isolated rendering |
| `models/` | Data classes, field validators | Property-based testing with Hypothesis (optional) |

**Example Test Structure:**
```python
# tests/unit/test_validator.py
import pytest
from resume_builder.validator import validate_resume

class TestResumeValidation:
    def test_valid_resume_passes(self, sample_resume_data):
        """Valid resume data should pass validation."""
        result = validate_resume(sample_resume_data)
        assert result.is_valid
        assert result.errors == []

    def test_missing_required_field_fails(self, sample_resume_data):
        """Missing name should fail with clear error."""
        del sample_resume_data["name"]
        result = validate_resume(sample_resume_data)
        assert not result.is_valid
        assert "name" in result.errors[0].field
        assert "required" in result.errors[0].message.lower()

    @pytest.mark.parametrize("email,expected_valid", [
        ("valid@example.com", True),
        ("invalid-email", False),
        ("", False),
    ])
    def test_email_validation(self, sample_resume_data, email, expected_valid):
        """Email field should validate format."""
        sample_resume_data["contact"]["email"] = email
        result = validate_resume(sample_resume_data)
        assert result.is_valid == expected_valid
```

### Integration Tests (Target: 30% of test effort)

**Scope:** Component interactions, file I/O, CLI commands

| Flow | Test Focus | Recommended Patterns |
|------|------------|---------------------|
| YAML → Pydantic → Jinja2 | Full data pipeline | Real files in tmp_path, snapshot assertions |
| CLI → Renderer → Output | End-to-end commands | Click CliRunner, output file verification |
| Template loading | Custom template discovery | Filesystem fixtures, path resolution |

**Example Test Structure:**
```python
# tests/integration/test_cli.py
import pytest
from click.testing import CliRunner
from resume_builder.cli import main

class TestCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_generate_markdown_output(self, runner, tmp_path, sample_yaml_file):
        """CLI should generate markdown from valid YAML."""
        output_file = tmp_path / "resume.md"

        result = runner.invoke(main, [
            "generate",
            str(sample_yaml_file),
            "--format", "markdown",
            "--output", str(output_file)
        ])

        assert result.exit_code == 0
        assert output_file.exists()
        assert "# " in output_file.read_text()  # Markdown heading

    def test_invalid_yaml_returns_error(self, runner, tmp_path):
        """CLI should exit with error for invalid YAML."""
        invalid_yaml = tmp_path / "invalid.yaml"
        invalid_yaml.write_text("invalid: [unclosed")

        result = runner.invoke(main, ["generate", str(invalid_yaml)])

        assert result.exit_code != 0
        assert "error" in result.output.lower()
```

### End-to-End Tests (Target: 10% of test effort)

**Scope:** Critical user journeys, output verification

| Journey | Test Focus | Recommended Patterns |
|---------|------------|---------------------|
| YAML → PDF | PDF generation correctness | Binary comparison OR text extraction |
| Template customization | Custom template rendering | Snapshot testing with approval workflow |

**PDF Testing Strategy:**

Since visual PDF comparison is fragile, use these approaches:

1. **Text extraction assertion** (Recommended)
```python
# tests/e2e/test_pdf_generation.py
import pytest
from pdfminer.high_level import extract_text

def test_pdf_contains_resume_content(generated_pdf_path, expected_name):
    """PDF should contain expected resume content."""
    text = extract_text(generated_pdf_path)
    assert expected_name in text
    assert "Experience" in text or "Work History" in text
```

2. **Structural validation**
```python
def test_pdf_has_expected_pages(generated_pdf_path):
    """PDF should have expected page count."""
    from pypdf import PdfReader
    reader = PdfReader(generated_pdf_path)
    assert 1 <= len(reader.pages) <= 3
```

---

## Risk Register

| ID | Risk | Category | Score | Mitigation | Owner |
|----|------|----------|-------|------------|-------|
| R1 | PDF rendering differences across systems | TECH | **6** | Pin WeasyPrint version, use Docker for CI | Dev Team |
| R2 | Template errors surface at runtime | BUS | **6** | Add template validation CLI command | Dev Team |
| R3 | YAML parsing errors lack line numbers | BUS | **4** | Use ruamel.yaml for better error context | Dev Team |
| R4 | No performance benchmarks defined | PERF | **3** | Add pytest-benchmark for critical paths | TEA |
| R5 | Test data scattered across test files | TECH | **4** | Centralize fixtures in conftest.py | Dev Team |

---

## Testability Recommendations

### Must-Have (Before Implementation)

1. **Fixture Architecture**
   - Create `tests/conftest.py` with shared fixtures
   - Use `tmp_path` for all file operations
   - Implement factory functions for test data

2. **Test Directory Structure**
   ```
   tests/
   ├── conftest.py           # Shared fixtures
   ├── unit/
   │   ├── test_loader.py
   │   ├── test_validator.py
   │   └── test_renderer.py
   ├── integration/
   │   ├── test_cli.py
   │   └── test_pipeline.py
   └── e2e/
       └── test_pdf_generation.py
   ```

3. **CI Quality Gates**
   - Coverage threshold: 80%
   - All tests pass
   - No flaky tests (run 3x in CI)

### Should-Have (During Implementation)

1. **Snapshot Testing** for template outputs
   - Use `pytest-snapshot` or `syrupy`
   - Store expected outputs in `tests/snapshots/`

2. **Error Message Contracts**
   - Define error format schema
   - Test error messages include: field name, line number, suggestion

3. **CLI Output Testing**
   - Capture Rich console output
   - Assert on structured output, not exact formatting

### Nice-to-Have (Post-MVP)

1. **Property-Based Testing** with Hypothesis
   - Generate random valid/invalid YAML structures
   - Find edge cases in validation logic

2. **Performance Benchmarks**
   - pytest-benchmark for rendering times
   - Memory profiling for large resumes

3. **Visual Regression** (if templates become complex)
   - Screenshot comparison for HTML output
   - Not recommended for PDF (too brittle)

---

## Test Framework Recommendations

| Tool | Purpose | Priority |
|------|---------|----------|
| **pytest** | Test runner, fixtures | Required |
| **pytest-cov** | Coverage reporting | Required |
| **Click CliRunner** | CLI testing | Required |
| **tmp_path fixture** | File isolation | Required |
| **pytest-snapshot** | Template output assertions | Recommended |
| **pytest-benchmark** | Performance validation | Optional |
| **Hypothesis** | Property-based testing | Optional |

---

## Coverage Mapping: Epics → Test Strategy

| Epic | Stories | Unit Tests | Integration Tests | E2E Tests |
|------|---------|------------|-------------------|-----------|
| **E1: Core Loading** | YAML parsing, schema validation | High | Medium | Low |
| **E2: Rendering** | Format selection, template execution | Medium | High | Medium |
| **E3: CLI** | Commands, options, error handling | Low | High | Low |
| **E4: Templates** | Custom templates, inheritance | Medium | Medium | Low |

---

## Gate Decision

| Criterion | Status | Notes |
|-----------|--------|-------|
| Architecture supports testing | PASS | Modular design with clear boundaries |
| Test strategy defined | PASS | Unit/Integration/E2E levels documented |
| Risks identified | PASS | 5 risks scored, mitigations assigned |
| Coverage targets set | PASS | 80% threshold defined |
| Framework selected | PASS | pytest + fixtures |

**Final Assessment:** PASS with CONCERNS

**Concerns to Address:**
1. PDF testing strategy needs validation during implementation (R1)
2. Template error handling should be tested early (R2)

**Recommendation:** Proceed to Implementation Readiness Check. The test architecture is sound; concerns are implementation-level details that can be resolved during Epic 1 development.

---

*Generated by TEA (Master Test Architect) | BMAD Method*
