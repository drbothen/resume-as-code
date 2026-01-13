"""Unit tests for CTO Resume Template (Story 6.17).

Tests AC:
- AC #1: CTO template follows best practices layout
- AC #2: Professional typography and styling
- AC #3: Scope indicators appear prominently
- AC #4: Career Highlights after summary, before experience
- AC #5: Board roles after certifications
- AC #6: Page count warning for exceeds 2 pages
- AC #7: CTO and executive share same CSS base
"""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_as_code.models.board_role import BoardRole
from resume_as_code.models.publication import Publication
from resume_as_code.models.resume import ContactInfo, ResumeData, ResumeSection
from resume_as_code.providers.pdf import PDFProvider
from resume_as_code.services.template_service import TemplateService


@pytest.fixture
def cto_resume() -> ResumeData:
    """Create a CTO-style resume with all sections populated."""
    return ResumeData(
        contact=ContactInfo(
            name="Jane Executive",
            title="Chief Technology Officer",
            email="jane@executive.com",
            phone="555-1234",
            location="San Francisco, CA",
            linkedin="linkedin.com/in/janeexec",
        ),
        summary=(
            "Transformational CTO with 20+ years leading technology strategy for Fortune 500 "
            "companies. Expertise in digital transformation, cloud architecture, and building "
            "high-performance engineering teams. Track record of delivering $100M+ cost savings "
            "through technology modernization."
        ),
        career_highlights=[
            "Led digital transformation generating $150M annual revenue",
            "Built engineering organization from 50 to 400+ across 3 continents",
            "Delivered $80M cost savings through cloud migration and automation",
            "Spearheaded AI/ML platform reducing fraud by 40%",
        ],
        sections=[
            ResumeSection(title="Professional Experience", items=[]),
        ],
        skills=["Cloud Architecture", "Digital Transformation", "AI/ML Strategy"],
        board_roles=[
            BoardRole(
                organization="TechStartup Inc",
                role="Board Advisor",
                start_date="2022-01",
                focus="Technology Strategy",
            ),
        ],
    )


@pytest.fixture
def template_service() -> TemplateService:
    """Create template service with real templates."""
    return TemplateService()


class TestCTOTemplateDiscovery:
    """Tests for CTO template being discoverable."""

    def test_cto_template_in_list(self, template_service: TemplateService) -> None:
        """CTO template should be discoverable (AC #1)."""
        templates = template_service.list_templates()
        assert "cto" in templates

    def test_executive_template_in_list(self, template_service: TemplateService) -> None:
        """Executive template should also be listed."""
        templates = template_service.list_templates()
        assert "executive" in templates


class TestCTOTemplateRendering:
    """Tests for CTO template HTML rendering."""

    def test_render_cto_template_with_career_highlights(
        self, template_service: TemplateService, cto_resume: ResumeData
    ) -> None:
        """CTO template renders career highlights with emphasis (AC #4)."""
        html = template_service.render(cto_resume, "cto")

        # Career Highlights section should be present
        assert "Career Highlights" in html
        # CTO emphasis class for prominent styling
        assert "cto-emphasis" in html
        # Actual highlights should render
        assert "$150M annual revenue" in html

    def test_render_cto_template_with_board_roles(
        self, template_service: TemplateService, cto_resume: ResumeData
    ) -> None:
        """CTO template renders board roles (AC #5)."""
        html = template_service.render(cto_resume, "cto")

        assert "Board &amp; Advisory Roles" in html or "Board & Advisory Roles" in html
        assert "TechStartup Inc" in html
        assert "Board Advisor" in html

    def test_cto_template_extends_executive(self, template_service: TemplateService) -> None:
        """CTO template extends executive template structure."""
        # Read the CTO template file
        cto_path = template_service.templates_dir / "cto.html"
        assert cto_path.exists()

        content = cto_path.read_text()
        assert 'extends "executive.html"' in content


class TestCTOCSSInheritance:
    """Tests for CSS inheritance between CTO and executive templates (AC #7)."""

    def test_cto_css_inherits_executive(self, template_service: TemplateService) -> None:
        """CTO CSS should include executive CSS base (AC #7)."""
        cto_css = template_service.get_css("cto")

        # Executive CSS content should be included in CTO CSS
        # Check for key executive styles that come from executive.css
        assert "font-family" in cto_css  # From executive
        assert ".name" in cto_css  # Executive header style
        assert "cto-emphasis" in cto_css  # CTO-specific addition

    def test_cto_has_emphasis_styles(self, template_service: TemplateService) -> None:
        """CTO CSS should have career highlights emphasis styling."""
        cto_css = template_service.get_css("cto")

        assert ".cto-emphasis" in cto_css
        assert "border-left" in cto_css  # CTO emphasis styling

    def test_executive_css_standalone(self, template_service: TemplateService) -> None:
        """Executive CSS should work standalone without CTO additions."""
        executive_css = template_service.get_css("executive")

        # Should have base styles but not CTO-specific
        assert ".name" in executive_css
        assert ".career-highlights" in executive_css
        # Should NOT have CTO emphasis (that's in cto.css only)
        assert ".cto-emphasis" not in executive_css


class TestCTOPDFGeneration:
    """Tests for CTO template PDF generation."""

    def test_generates_valid_pdf(self, cto_resume: ResumeData, tmp_path: Path) -> None:
        """CTO template generates valid PDF (AC #1)."""
        output_path = tmp_path / "cto_resume.pdf"
        provider = PDFProvider(template_name="cto")

        result = provider.render(cto_resume, output_path)

        assert result.output_path.exists()
        with open(result.output_path, "rb") as f:
            assert f.read(4) == b"%PDF"

    def test_returns_page_count(self, cto_resume: ResumeData, tmp_path: Path) -> None:
        """CTO template returns page count for warning system (AC #6)."""
        output_path = tmp_path / "cto_resume.pdf"
        provider = PDFProvider(template_name="cto")

        result = provider.render(cto_resume, output_path)

        # Should have at least 1 page
        assert result.page_count >= 1
        # With minimal content, should be 1-2 pages
        assert result.page_count <= 3


class TestExecutiveTemplateBlocks:
    """Tests for executive template block definitions."""

    def test_executive_has_career_highlights_block(self, template_service: TemplateService) -> None:
        """Executive template defines career_highlights block."""
        exec_path = template_service.templates_dir / "executive.html"
        content = exec_path.read_text()

        assert "{% block career_highlights %}" in content
        assert "{% endblock %}" in content

    def test_executive_has_board_roles_block(self, template_service: TemplateService) -> None:
        """Executive template defines board_roles block."""
        exec_path = template_service.templates_dir / "executive.html"
        content = exec_path.read_text()

        assert "{% block board_roles %}" in content

    def test_executive_has_publications_block(self, template_service: TemplateService) -> None:
        """Executive template defines publications block."""
        exec_path = template_service.templates_dir / "executive.html"
        content = exec_path.read_text()

        assert "{% block publications %}" in content


class TestTemplateComparison:
    """Tests comparing CTO and executive template output (AC #7)."""

    def test_both_render_career_highlights_when_present(
        self, template_service: TemplateService, cto_resume: ResumeData
    ) -> None:
        """Both templates render career highlights when present."""
        cto_html = template_service.render(cto_resume, "cto")
        exec_html = template_service.render(cto_resume, "executive")

        # Both should have career highlights
        assert "Career Highlights" in cto_html
        assert "Career Highlights" in exec_html
        # But CTO should have emphasis class
        assert "cto-emphasis" in cto_html
        assert "cto-emphasis" not in exec_html

    def test_cto_requires_career_highlights_prominence(
        self, template_service: TemplateService, cto_resume: ResumeData
    ) -> None:
        """CTO template has career highlights with prominent styling (AC #4)."""
        cto_html = template_service.render(cto_resume, "cto")

        # CTO should have emphasis styling applied
        assert 'class="career-highlights cto-emphasis"' in cto_html


class TestCTOPublications:
    """Tests for publications rendering in CTO template."""

    def test_cto_template_renders_publications_when_present(
        self, template_service: TemplateService
    ) -> None:
        """CTO template renders publications section when populated."""
        resume_with_publications = ResumeData(
            contact=ContactInfo(
                name="Jane Executive",
                title="Chief Technology Officer",
                email="jane@executive.com",
            ),
            summary="Executive summary",
            publications=[
                Publication(
                    title="Scaling Engineering Teams in the AI Era",
                    type="conference",
                    venue="QCon San Francisco",
                    date="2024-11",
                ),
                Publication(
                    title="Cloud Migration: A CTO's Playbook",
                    type="article",
                    venue="Harvard Business Review",
                    date="2024-06",
                ),
            ],
        )

        html = template_service.render(resume_with_publications, "cto")

        # Publications section should render
        assert "Publications" in html or "Speaking" in html
        # Content should be present
        assert "QCon San Francisco" in html
        assert "Harvard Business Review" in html
        assert "Scaling Engineering Teams" in html
