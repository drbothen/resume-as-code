"""Unit tests for executive resume templates.

Tests both the new executive template (sans-serif, modern) and
the executive-classic template (serif, traditional).

Story: 6-4-executive-resume-template
"""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_as_code.models.certification import Certification
from resume_as_code.models.education import Education
from resume_as_code.models.resume import (
    ContactInfo,
    ResumeBullet,
    ResumeData,
    ResumeItem,
    ResumeSection,
)
from resume_as_code.services.template_service import TemplateService


@pytest.fixture
def template_service() -> TemplateService:
    """Create a template service using the real templates directory."""
    return TemplateService()


@pytest.fixture
def executive_resume() -> ResumeData:
    """Create an executive-level resume for testing."""
    contact = ContactInfo(
        name="Jane Executive",
        title="Chief Technology Officer",
        email="jane@example.com",
        phone="555-555-5555",
        location="San Francisco, CA",
        linkedin="https://linkedin.com/in/janeexec",
    )

    experience = [
        ResumeItem(
            title="Chief Technology Officer",
            organization="Tech Innovations Inc.",
            location="San Francisco, CA",
            start_date="2020-01",
            end_date=None,
            scope_line="P&L: $50M ARR | Team: 85 | Budget: $15M",
            bullets=[
                ResumeBullet(
                    text="Led digital transformation initiative across enterprise",
                    metrics="40% cost reduction",
                ),
                ResumeBullet(text="Architected cloud migration strategy for 200+ services"),
                ResumeBullet(text="Built and scaled engineering organization globally"),
            ],
        ),
        ResumeItem(
            title="VP of Engineering",
            organization="StartupCo",
            location="Palo Alto, CA",
            start_date="2016-03",
            end_date="2019-12",
            scope_line="Team: 35 | Budget: $5M",
            bullets=[
                ResumeBullet(
                    text="Grew engineering team from 8 to 35 engineers",
                    metrics="3x team growth",
                ),
            ],
        ),
    ]

    education = [
        Education(
            degree="MBA",
            institution="Stanford Graduate School of Business",
            graduation_year="2015",
        ),
        Education(
            degree="BS Computer Science",
            institution="MIT",
            graduation_year="2008",
        ),
    ]

    certifications = [
        Certification(
            name="AWS Solutions Architect Professional",
            issuer="Amazon Web Services",
            date_earned="2022-06-15",
        ),
        Certification(
            name="PMP",
            issuer="PMI",
            date_earned="2018-03-01",
        ),
    ]

    return ResumeData(
        contact=contact,
        summary="Visionary technology leader with 15+ years driving digital transformation "
        "and building high-performing engineering organizations. Proven track record of "
        "delivering $50M+ in business value through strategic technology initiatives.",
        sections=[ResumeSection(title="Professional Experience", items=experience)],
        skills=[
            "Digital Transformation",
            "Cloud Architecture",
            "Team Leadership",
            "Strategic Planning",
            "Agile/DevOps",
        ],
        education=education,
        certifications=certifications,
    )


@pytest.fixture
def minimal_resume() -> ResumeData:
    """Create a minimal resume for edge case testing."""
    return ResumeData(
        contact=ContactInfo(name="Test User"),
    )


class TestTemplateDiscovery:
    """Tests for template discovery and availability."""

    def test_executive_template_exists(self, template_service: TemplateService) -> None:
        """Executive template should be available."""
        templates = template_service.list_templates()
        assert "executive" in templates

    def test_executive_classic_template_exists(self, template_service: TemplateService) -> None:
        """Executive-classic template should be available (preserved original)."""
        templates = template_service.list_templates()
        assert "executive-classic" in templates

    def test_executive_html_file_exists(self) -> None:
        """executive.html file should exist in templates directory."""
        templates_dir = Path(__file__).parent.parent.parent / "src/resume_as_code/templates"
        assert (templates_dir / "executive.html").exists()

    def test_executive_css_file_exists(self) -> None:
        """executive.css file should exist in templates directory."""
        templates_dir = Path(__file__).parent.parent.parent / "src/resume_as_code/templates"
        assert (templates_dir / "executive.css").exists()

    def test_executive_classic_html_file_exists(self) -> None:
        """executive-classic.html file should exist in templates directory."""
        templates_dir = Path(__file__).parent.parent.parent / "src/resume_as_code/templates"
        assert (templates_dir / "executive-classic.html").exists()

    def test_executive_classic_css_file_exists(self) -> None:
        """executive-classic.css file should exist in templates directory."""
        templates_dir = Path(__file__).parent.parent.parent / "src/resume_as_code/templates"
        assert (templates_dir / "executive-classic.css").exists()


class TestExecutiveTemplateRendering:
    """Tests for executive template rendering functionality."""

    def test_renders_contact_name_prominently(
        self, template_service: TemplateService, executive_resume: ResumeData
    ) -> None:
        """Contact name should be rendered in the template."""
        html = template_service.render(executive_resume, "executive")
        assert "Jane Executive" in html

    def test_renders_professional_title(
        self, template_service: TemplateService, executive_resume: ResumeData
    ) -> None:
        """Professional title should be rendered below name."""
        html = template_service.render(executive_resume, "executive")
        assert "Chief Technology Officer" in html

    def test_renders_contact_line(
        self, template_service: TemplateService, executive_resume: ResumeData
    ) -> None:
        """Contact info should be rendered."""
        html = template_service.render(executive_resume, "executive")
        assert "jane@example.com" in html
        assert "San Francisco, CA" in html

    def test_renders_executive_summary(
        self, template_service: TemplateService, executive_resume: ResumeData
    ) -> None:
        """Executive summary should be rendered when present."""
        html = template_service.render(executive_resume, "executive")
        assert "Visionary technology leader" in html

    def test_renders_skills_section(
        self, template_service: TemplateService, executive_resume: ResumeData
    ) -> None:
        """Skills/Core Competencies section should be rendered."""
        html = template_service.render(executive_resume, "executive")
        assert "Digital Transformation" in html
        assert "Cloud Architecture" in html

    def test_renders_experience_section(
        self, template_service: TemplateService, executive_resume: ResumeData
    ) -> None:
        """Experience section should be rendered."""
        html = template_service.render(executive_resume, "executive")
        assert "Tech Innovations Inc." in html
        assert "StartupCo" in html

    def test_renders_scope_indicators(
        self, template_service: TemplateService, executive_resume: ResumeData
    ) -> None:
        """Scope indicators (budget, team size, revenue) should be rendered."""
        html = template_service.render(executive_resume, "executive")
        # Check that scope data is present
        assert "$15M" in html or "15M" in html
        assert "85" in html
        assert "$50M" in html or "50M" in html

    def test_renders_certifications(
        self, template_service: TemplateService, executive_resume: ResumeData
    ) -> None:
        """Certifications section should be rendered when present."""
        html = template_service.render(executive_resume, "executive")
        assert "AWS Solutions Architect Professional" in html

    def test_renders_education(
        self, template_service: TemplateService, executive_resume: ResumeData
    ) -> None:
        """Education section should be rendered when present."""
        html = template_service.render(executive_resume, "executive")
        assert "Stanford" in html
        assert "MIT" in html

    def test_renders_achievement_bullets(
        self, template_service: TemplateService, executive_resume: ResumeData
    ) -> None:
        """Achievement bullets should be rendered."""
        html = template_service.render(executive_resume, "executive")
        assert "digital transformation" in html.lower()
        assert "40% cost reduction" in html


class TestExecutiveTemplateMinimalData:
    """Tests for graceful handling of minimal/missing data."""

    def test_renders_with_only_name(
        self, template_service: TemplateService, minimal_resume: ResumeData
    ) -> None:
        """Template should render cleanly with only name provided."""
        html = template_service.render(minimal_resume, "executive")
        assert "Test User" in html
        # Should not have empty sections or errors
        assert "<!DOCTYPE html>" in html

    def test_shows_placeholder_when_summary_missing(
        self, template_service: TemplateService, minimal_resume: ResumeData
    ) -> None:
        """Placeholder should be shown when summary not provided (AC#6)."""
        html = template_service.render(minimal_resume, "executive")
        # AC#6: When no summary exists, a placeholder is shown
        assert "Executive Summary" in html
        assert "placeholder" in html.lower()
        assert "not configured" in html.lower()
        assert "Test User" in html

    def test_handles_missing_title(
        self, template_service: TemplateService, minimal_resume: ResumeData
    ) -> None:
        """Template should handle missing professional title gracefully."""
        html = template_service.render(minimal_resume, "executive")
        assert "Test User" in html
        # Should not crash or have undefined errors


class TestExecutiveClassicTemplate:
    """Tests for executive-classic (serif) template."""

    def test_renders_with_executive_classic(
        self, template_service: TemplateService, executive_resume: ResumeData
    ) -> None:
        """Executive-classic template should render successfully."""
        html = template_service.render(executive_resume, "executive-classic")
        assert "Jane Executive" in html
        assert "<!DOCTYPE html>" in html

    def test_executive_classic_has_serif_font(self, template_service: TemplateService) -> None:
        """Executive-classic CSS should specify serif fonts (Georgia)."""
        css = template_service.get_css("executive-classic")
        # Georgia is the primary serif font in executive-classic
        assert "Georgia" in css or "serif" in css


class TestExecutiveTemplateCSS:
    """Tests for executive template CSS styling."""

    def test_executive_has_sans_serif_font(self, template_service: TemplateService) -> None:
        """Executive CSS should specify sans-serif fonts (Calibri/Arial)."""
        css = template_service.get_css("executive")
        # Should have modern sans-serif fonts
        assert "Calibri" in css or "Arial" in css or "sans-serif" in css

    def test_executive_has_one_inch_margins(self, template_service: TemplateService) -> None:
        """Executive CSS should have 1-inch margins for print."""
        css = template_service.get_css("executive")
        assert "1in" in css

    def test_executive_has_accent_color(self, template_service: TemplateService) -> None:
        """Executive CSS should have accent color (#2c3e50)."""
        css = template_service.get_css("executive")
        assert "#2c3e50" in css

    def test_executive_has_page_break_rules(self, template_service: TemplateService) -> None:
        """Executive CSS should have page-break rules."""
        css = template_service.get_css("executive")
        assert "page-break" in css
