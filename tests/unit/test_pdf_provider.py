"""Unit tests for PDF Provider."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from resume_as_code.models.resume import (
    ContactInfo,
    ResumeBullet,
    ResumeData,
    ResumeItem,
    ResumeSection,
)
from resume_as_code.providers.pdf import PDFProvider


@pytest.fixture
def sample_resume() -> ResumeData:
    """Create sample resume for testing."""
    return ResumeData(
        contact=ContactInfo(
            name="John Doe",
            email="john@example.com",
            phone="555-1234",
        ),
        summary="Experienced software engineer with 10+ years in Python",
        skills=["Python", "AWS", "Kubernetes"],
    )


@pytest.fixture
def detailed_resume() -> ResumeData:
    """Create a more detailed resume for comprehensive testing."""
    return ResumeData(
        contact=ContactInfo(
            name="Jane Smith",
            email="jane@example.com",
            phone="555-9876",
            location="San Francisco, CA",
            linkedin="linkedin.com/in/janesmith",
            github="github.com/janesmith",
        ),
        summary="Senior software architect specializing in distributed systems.",
        sections=[
            ResumeSection(
                title="Experience",
                items=[
                    ResumeItem(
                        title="Principal Engineer",
                        organization="TechCorp",
                        location="San Francisco, CA",
                        start_date="Jan 2020",
                        end_date="Present",
                        bullets=[
                            ResumeBullet(
                                text="Led migration to microservices architecture",
                                metrics="Reduced deployment time by 60%",
                            ),
                            ResumeBullet(text="Built distributed cache layer for high-traffic API"),
                        ],
                    ),
                ],
            ),
        ],
        skills=["Python", "Go", "Kubernetes", "AWS", "Terraform"],
        education=[
            ResumeItem(
                title="M.S. Computer Science",
                organization="Stanford University",
                start_date="2010",
                end_date="2012",
            ),
        ],
    )


class TestPDFProviderInit:
    """Tests for PDFProvider initialization."""

    def test_init_default_template(self) -> None:
        """PDFProvider uses 'modern' template by default."""
        provider = PDFProvider()
        assert provider.template_name == "modern"

    def test_init_custom_template(self) -> None:
        """PDFProvider accepts custom template name."""
        provider = PDFProvider(template_name="executive")
        assert provider.template_name == "executive"

    def test_init_custom_template_service(self) -> None:
        """PDFProvider accepts custom template service."""
        from resume_as_code.services.template_service import TemplateService

        service = TemplateService()
        provider = PDFProvider(template_service=service)
        assert provider.template_service is service


class TestPDFGeneration:
    """Tests for PDF generation."""

    def test_generates_pdf_file(self, sample_resume: ResumeData, tmp_path: Path) -> None:
        """Should generate a PDF file."""
        output_path = tmp_path / "resume.pdf"
        provider = PDFProvider()

        result = provider.render(sample_resume, output_path)

        assert result.exists()
        assert result.suffix == ".pdf"

    def test_pdf_has_valid_header(self, sample_resume: ResumeData, tmp_path: Path) -> None:
        """Generated file should be a valid PDF (starts with %PDF)."""
        output_path = tmp_path / "resume.pdf"
        provider = PDFProvider()

        provider.render(sample_resume, output_path)

        with open(output_path, "rb") as f:
            assert f.read(4) == b"%PDF"

    def test_creates_output_directory(self, sample_resume: ResumeData, tmp_path: Path) -> None:
        """Should create output directory if needed."""
        output_path = tmp_path / "nested" / "dir" / "resume.pdf"
        provider = PDFProvider()

        result = provider.render(sample_resume, output_path)

        assert result.exists()

    def test_overwrites_existing_file(self, sample_resume: ResumeData, tmp_path: Path) -> None:
        """Should overwrite existing file gracefully."""
        output_path = tmp_path / "resume.pdf"
        output_path.write_text("old content")

        provider = PDFProvider()
        result = provider.render(sample_resume, output_path)

        assert result.exists()
        with open(result, "rb") as f:
            assert f.read(4) == b"%PDF"

    def test_returns_output_path(self, sample_resume: ResumeData, tmp_path: Path) -> None:
        """Should return the output path."""
        output_path = tmp_path / "resume.pdf"
        provider = PDFProvider()

        result = provider.render(sample_resume, output_path)

        assert result == output_path


class TestPDFContent:
    """Tests for PDF content rendering."""

    def test_pdf_contains_contact_name(self, detailed_resume: ResumeData, tmp_path: Path) -> None:
        """PDF should contain contact name (check via file size/validity)."""
        output_path = tmp_path / "resume.pdf"
        provider = PDFProvider()

        provider.render(detailed_resume, output_path)

        # A valid PDF with content should be larger than minimal
        assert output_path.stat().st_size > 1000

    def test_detailed_resume_renders(self, detailed_resume: ResumeData, tmp_path: Path) -> None:
        """Detailed resume with all sections should render."""
        output_path = tmp_path / "resume.pdf"
        provider = PDFProvider()

        result = provider.render(detailed_resume, output_path)

        assert result.exists()
        with open(result, "rb") as f:
            assert f.read(4) == b"%PDF"


class TestRenderToBytes:
    """Tests for render_to_bytes method."""

    def test_render_to_bytes_returns_pdf_bytes(self, sample_resume: ResumeData) -> None:
        """Should render PDF to bytes."""
        provider = PDFProvider()

        pdf_bytes = provider.render_to_bytes(sample_resume)

        assert pdf_bytes.startswith(b"%PDF")

    def test_render_to_bytes_non_empty(self, sample_resume: ResumeData) -> None:
        """Should return non-empty bytes."""
        provider = PDFProvider()

        pdf_bytes = provider.render_to_bytes(sample_resume)

        assert len(pdf_bytes) > 1000


class TestPDFPerformance:
    """Performance tests for PDF generation."""

    def test_renders_within_5_seconds(self, sample_resume: ResumeData, tmp_path: Path) -> None:
        """NFR2: PDF generation should complete within 5 seconds."""
        output_path = tmp_path / "resume.pdf"
        provider = PDFProvider()

        start = time.perf_counter()
        provider.render(sample_resume, output_path)
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"PDF generation took {elapsed:.2f}s (should be <5s)"

    def test_detailed_resume_within_5_seconds(
        self, detailed_resume: ResumeData, tmp_path: Path
    ) -> None:
        """NFR2: Even detailed resumes should render within 5 seconds."""
        output_path = tmp_path / "resume.pdf"
        provider = PDFProvider()

        start = time.perf_counter()
        provider.render(detailed_resume, output_path)
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"PDF generation took {elapsed:.2f}s (should be <5s)"


class TestPDFTemplates:
    """Tests for PDF with different templates."""

    def test_render_with_executive_template(
        self, sample_resume: ResumeData, tmp_path: Path
    ) -> None:
        """Should render PDF with executive template."""
        output_path = tmp_path / "resume.pdf"
        provider = PDFProvider(template_name="executive")

        result = provider.render(sample_resume, output_path)

        assert result.exists()
        with open(result, "rb") as f:
            assert f.read(4) == b"%PDF"

    def test_render_with_ats_safe_template(self, sample_resume: ResumeData, tmp_path: Path) -> None:
        """Should render PDF with ats-safe template."""
        output_path = tmp_path / "resume.pdf"
        provider = PDFProvider(template_name="ats-safe")

        result = provider.render(sample_resume, output_path)

        assert result.exists()
        with open(result, "rb") as f:
            assert f.read(4) == b"%PDF"


class TestErrorHandling:
    """Tests for PDF provider error handling."""

    def test_invalid_template_raises_error(self, sample_resume: ResumeData, tmp_path: Path) -> None:
        """Should raise TemplateNotFound for nonexistent template."""
        from jinja2 import TemplateNotFound

        output_path = tmp_path / "resume.pdf"
        provider = PDFProvider(template_name="nonexistent_template")

        with pytest.raises(TemplateNotFound):
            provider.render(sample_resume, output_path)

    def test_invalid_template_bytes_raises_error(self, sample_resume: ResumeData) -> None:
        """Should raise TemplateNotFound for nonexistent template in bytes mode."""
        from jinja2 import TemplateNotFound

        provider = PDFProvider(template_name="nonexistent_template")

        with pytest.raises(TemplateNotFound):
            provider.render_to_bytes(sample_resume)


class TestFontHandling:
    """Tests for font handling in PDF generation."""

    def test_renders_special_characters(self, tmp_path: Path) -> None:
        """PDF should render special characters correctly."""
        resume = ResumeData(
            contact=ContactInfo(
                name="José García",
                email="jose@example.com",
            ),
            summary="Expert in résumé writing • 10+ years • naïve → sophisticated",
            skills=["C++", "C#", "naïve Bayes", "über-engineering"],
        )
        output_path = tmp_path / "resume.pdf"
        provider = PDFProvider()

        result = provider.render(resume, output_path)

        assert result.exists()
        with open(result, "rb") as f:
            assert f.read(4) == b"%PDF"

    def test_renders_unicode_symbols(self, tmp_path: Path) -> None:
        """PDF should render unicode symbols."""
        resume = ResumeData(
            contact=ContactInfo(
                name="Test User",
                email="test@example.com",
            ),
            summary="Metrics: ↑50% efficiency, ↓30% costs, ≈100% reliability",
            skills=["Python ≥3.10", "λ-calculus", "∞ scalability"],
        )
        output_path = tmp_path / "resume.pdf"
        provider = PDFProvider()

        result = provider.render(resume, output_path)

        assert result.exists()
        with open(result, "rb") as f:
            assert f.read(4) == b"%PDF"
