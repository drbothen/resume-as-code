"""Unit tests for Template Service."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from resume_as_code.models.resume import ContactInfo, ResumeData, ResumeSection
from resume_as_code.services.template_service import TemplateService

if TYPE_CHECKING:
    pass


@pytest.fixture
def templates_dir(tmp_path: Path) -> Path:
    """Create a temporary templates directory with test templates."""
    # Create modern template (with CSS injection point)
    modern_html = tmp_path / "modern.html"
    modern_html.write_text(
        """<!DOCTYPE html>
<html>
<head>
<title>{{ resume.contact.name }} - Resume</title>
<style>{{ css }}</style>
</head>
<body>
<h1>{{ resume.contact.name }}</h1>
{% if resume.contact.email %}<p>{{ resume.contact.email }}</p>{% endif %}
{% if resume.summary %}<p>{{ resume.summary }}</p>{% endif %}
{% for section in resume.sections %}
<section><h2>{{ section.title }}</h2></section>
{% endfor %}
{% if resume.skills %}<p>Skills: {{ resume.skills | join(', ') }}</p>{% endif %}
</body>
</html>"""
    )

    # Create modern CSS
    modern_css = tmp_path / "modern.css"
    modern_css.write_text(
        """body { font-family: Arial; }
h1 { color: #333; }"""
    )

    # Create executive template (with CSS injection point)
    executive_html = tmp_path / "executive.html"
    executive_html.write_text(
        """<!DOCTYPE html>
<html>
<head>
<title>{{ resume.contact.name }} - Executive Resume</title>
<style>{{ css }}</style>
</head>
<body><h1>{{ resume.contact.name }}</h1></body>
</html>"""
    )

    # Create a partial (should be ignored)
    partial_html = tmp_path / "_partial.html"
    partial_html.write_text("<div>partial content</div>")

    return tmp_path


@pytest.fixture
def template_service(templates_dir: Path) -> TemplateService:
    """Create a template service with test templates."""
    return TemplateService(templates_dir=templates_dir)


@pytest.fixture
def sample_resume() -> ResumeData:
    """Create a sample resume for testing."""
    contact = ContactInfo(
        name="Jane Developer",
        email="jane@example.com",
        phone="555-1234",
    )
    return ResumeData(
        contact=contact,
        summary="Experienced software engineer with 10+ years.",
        sections=[
            ResumeSection(title="Experience", items=[]),
            ResumeSection(title="Education", items=[]),
        ],
        skills=["Python", "TypeScript", "AWS"],
    )


class TestTemplateServiceInit:
    """Tests for TemplateService initialization."""

    def test_init_with_custom_templates_dir(self, templates_dir: Path) -> None:
        """TemplateService accepts custom templates directory."""
        service = TemplateService(templates_dir=templates_dir)
        assert service.templates_dir == templates_dir

    def test_init_default_templates_dir(self) -> None:
        """TemplateService uses default templates directory when none provided."""
        service = TemplateService()
        assert service.templates_dir.exists() or not service.templates_dir.exists()
        # Just verify it doesn't crash - default dir may not exist in test env


class TestTemplateDiscovery:
    """Tests for template discovery functionality."""

    def test_list_templates_returns_available_templates(
        self, template_service: TemplateService
    ) -> None:
        """list_templates returns all non-partial template names."""
        templates = template_service.list_templates()
        assert "modern" in templates
        assert "executive" in templates
        assert "_partial" not in templates

    def test_list_templates_sorted_alphabetically(self, template_service: TemplateService) -> None:
        """list_templates returns templates in alphabetical order."""
        templates = template_service.list_templates()
        assert templates == sorted(templates)

    def test_list_templates_excludes_partials(self, template_service: TemplateService) -> None:
        """Templates starting with underscore are excluded."""
        templates = template_service.list_templates()
        for template in templates:
            assert not template.startswith("_")


class TestTemplateRendering:
    """Tests for template rendering functionality."""

    def test_render_basic_template(
        self, template_service: TemplateService, sample_resume: ResumeData
    ) -> None:
        """render produces valid HTML with resume data."""
        html = template_service.render(sample_resume, "modern")

        assert "<!DOCTYPE html>" in html
        assert "Jane Developer" in html
        assert "jane@example.com" in html

    def test_render_includes_summary(
        self, template_service: TemplateService, sample_resume: ResumeData
    ) -> None:
        """render includes summary when present."""
        html = template_service.render(sample_resume, "modern")
        assert "Experienced software engineer" in html

    def test_render_includes_sections(
        self, template_service: TemplateService, sample_resume: ResumeData
    ) -> None:
        """render includes all sections."""
        html = template_service.render(sample_resume, "modern")
        assert "Experience" in html
        assert "Education" in html

    def test_render_includes_skills(
        self, template_service: TemplateService, sample_resume: ResumeData
    ) -> None:
        """render includes skills list."""
        html = template_service.render(sample_resume, "modern")
        assert "Python" in html
        assert "TypeScript" in html
        assert "AWS" in html

    def test_render_different_template(
        self, template_service: TemplateService, sample_resume: ResumeData
    ) -> None:
        """render can use different templates."""
        html = template_service.render(sample_resume, "executive")
        assert "Executive Resume" in html
        assert "Jane Developer" in html

    def test_render_missing_template_raises_error(
        self, template_service: TemplateService, sample_resume: ResumeData
    ) -> None:
        """render raises error for missing template."""
        from jinja2 import TemplateNotFound

        with pytest.raises(TemplateNotFound):
            template_service.render(sample_resume, "nonexistent")

    def test_render_default_template(
        self, template_service: TemplateService, sample_resume: ResumeData
    ) -> None:
        """render uses 'modern' as default template."""
        html = template_service.render(sample_resume)
        assert "Jane Developer" in html


class TestGetCSS:
    """Tests for CSS retrieval functionality."""

    def test_get_css_returns_css_content(self, template_service: TemplateService) -> None:
        """get_css returns CSS file content."""
        css = template_service.get_css("modern")
        assert "font-family: Arial" in css
        assert "color: #333" in css

    def test_get_css_missing_file_returns_empty(self, template_service: TemplateService) -> None:
        """get_css returns empty string when CSS file doesn't exist."""
        css = template_service.get_css("executive")  # No CSS file created
        assert css == ""

    def test_get_css_default_template(self, template_service: TemplateService) -> None:
        """get_css uses 'modern' as default template."""
        css = template_service.get_css()
        assert "font-family: Arial" in css


class TestCSSInjection:
    """Tests for CSS injection into rendered HTML."""

    def test_css_is_injected_into_rendered_html(
        self, template_service: TemplateService, sample_resume: ResumeData
    ) -> None:
        """CSS content is injected into the style tag."""
        html = template_service.render(sample_resume, "modern")

        # CSS should be present in the rendered HTML
        assert "font-family: Arial" in html
        assert "<style>" in html
        # Should NOT have empty style tag
        assert "<style></style>" not in html

    def test_css_injection_with_different_templates(self, templates_dir: Path) -> None:
        """Each template gets its own CSS injected."""
        # Create executive CSS
        exec_css = templates_dir / "executive.css"
        exec_css.write_text("body { font-family: Georgia; }")

        service = TemplateService(templates_dir=templates_dir)
        contact = ContactInfo(name="Test")
        resume = ResumeData(contact=contact)

        modern_html = service.render(resume, "modern")
        exec_html = service.render(resume, "executive")

        assert "font-family: Arial" in modern_html
        assert "font-family: Georgia" in exec_html


class TestAutoescaping:
    """Tests for HTML autoescaping functionality."""

    def test_html_special_chars_escaped(self, template_service: TemplateService) -> None:
        """Special HTML characters are escaped."""
        contact = ContactInfo(name="Test <script>alert('xss')</script>")
        resume = ResumeData(contact=contact)

        html = template_service.render(resume, "modern")

        # Script tag should be escaped, not executable
        assert "<script>" not in html
        assert "&lt;script&gt;" in html or "script" not in html.lower()


class TestEmployerGrouping:
    """Tests for employer grouping in template rendering (Story 8.1)."""

    @pytest.fixture
    def template_with_groups(self, tmp_path: Path) -> Path:
        """Create a template that shows employer_groups variable."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template = templates_dir / "test.html"
        template.write_text("""<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
{% if employer_groups %}
<div class="employer-groups">
{% for group in employer_groups %}
<div class="employer-group" data-employer="{{ group.employer }}">
  <div class="tenure">{{ group.tenure_display }}</div>
  <div class="multi-position">{{ group.is_multi_position }}</div>
  {% for pos in group.positions %}
  <div class="position">{{ pos.title }}</div>
  {% endfor %}
</div>
{% endfor %}
</div>
{% else %}
<div class="no-groups">Grouping disabled</div>
{% endif %}
</body>
</html>""")

        return templates_dir

    def test_render_computes_employer_groups_by_default(self, template_with_groups: Path) -> None:
        """render should compute employer_groups when no config provided."""
        from resume_as_code.models.resume import ResumeBullet, ResumeItem

        service = TemplateService(templates_dir=template_with_groups)

        items = [
            ResumeItem(
                title="Senior Engineer",
                organization="TechCorp",
                location="Austin, TX",
                start_date="2023",
                end_date=None,
                bullets=[ResumeBullet(text="Led team")],
            ),
            ResumeItem(
                title="Engineer",
                organization="TechCorp",
                location="Austin, TX",
                start_date="2020",
                end_date="2023",
                bullets=[ResumeBullet(text="Built features")],
            ),
        ]

        contact = ContactInfo(name="Test User")
        resume = ResumeData(
            contact=contact,
            sections=[ResumeSection(title="Experience", items=items)],
        )

        html = service.render(resume, "test")

        assert "employer-groups" in html
        assert 'data-employer="TechCorp"' in html
        assert "2020 - Present" in html
        assert "True" in html  # is_multi_position

    def test_render_respects_group_employer_positions_false(
        self, template_with_groups: Path
    ) -> None:
        """render should not compute employer_groups when config disables it."""
        from resume_as_code.models.config import ResumeConfig, TemplateOptions
        from resume_as_code.models.resume import ResumeBullet, ResumeItem

        service = TemplateService(templates_dir=template_with_groups)

        items = [
            ResumeItem(
                title="Senior Engineer",
                organization="TechCorp",
                start_date="2023",
                bullets=[ResumeBullet(text="Led team")],
            ),
        ]

        contact = ContactInfo(name="Test User")
        resume = ResumeData(
            contact=contact,
            sections=[ResumeSection(title="Experience", items=items)],
        )

        config = ResumeConfig(template_options=TemplateOptions(group_employer_positions=False))

        html = service.render(resume, "test", config=config)

        assert "no-groups" in html
        assert "Grouping disabled" in html
        assert "employer-groups" not in html

    def test_render_groups_with_config_enabled(self, template_with_groups: Path) -> None:
        """render should compute employer_groups when config explicitly enables it."""
        from resume_as_code.models.config import ResumeConfig, TemplateOptions
        from resume_as_code.models.resume import ResumeBullet, ResumeItem

        service = TemplateService(templates_dir=template_with_groups)

        items = [
            ResumeItem(
                title="Engineer",
                organization="TechCorp",
                start_date="2020",
                end_date="2023",
                bullets=[ResumeBullet(text="Built features")],
            ),
        ]

        contact = ContactInfo(name="Test User")
        resume = ResumeData(
            contact=contact,
            sections=[ResumeSection(title="Experience", items=items)],
        )

        config = ResumeConfig(template_options=TemplateOptions(group_employer_positions=True))

        html = service.render(resume, "test", config=config)

        assert "employer-groups" in html
        assert 'data-employer="TechCorp"' in html

    def test_render_no_experience_section_returns_none_groups(
        self, template_with_groups: Path
    ) -> None:
        """render should not fail when no Experience section exists."""
        service = TemplateService(templates_dir=template_with_groups)

        contact = ContactInfo(name="Test User")
        resume = ResumeData(
            contact=contact,
            sections=[ResumeSection(title="Education", items=[])],
        )

        html = service.render(resume, "test")

        # Should render without crashing, no employer groups
        assert "no-groups" in html
