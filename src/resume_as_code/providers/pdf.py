"""PDF provider using WeasyPrint."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from weasyprint import CSS, HTML  # type: ignore[import-untyped]

from resume_as_code.models.errors import RenderError
from resume_as_code.models.resume import ResumeData
from resume_as_code.services.template_service import TemplateService


@dataclass
class PDFRenderResult:
    """Result of PDF rendering including metadata.

    Attributes:
        output_path: Path to generated PDF file.
        page_count: Number of pages in the generated PDF.
    """

    output_path: Path
    page_count: int


class PDFProvider:
    """Provider for generating PDF resumes using WeasyPrint."""

    def __init__(
        self,
        template_service: TemplateService | None = None,
        template_name: str = "modern",
        templates_dir: Path | None = None,
    ) -> None:
        """Initialize PDF provider.

        Args:
            template_service: Template service for rendering HTML.
            template_name: Name of template to use.
            templates_dir: Optional path to custom templates directory (Story 11.3).
                If provided and template_service is None, creates TemplateService
                with this as custom_templates_dir.
        """
        if template_service is not None:
            self.template_service = template_service
        else:
            self.template_service = TemplateService(custom_templates_dir=templates_dir)
        self.template_name = template_name

    def render(self, resume: ResumeData, output_path: Path) -> PDFRenderResult:
        """Render resume to PDF file.

        Args:
            resume: ResumeData to render.
            output_path: Path for output PDF file.

        Returns:
            PDFRenderResult with path and page count (Story 6.17: AC #6).

        Raises:
            RenderError: If PDF generation fails.
        """
        # Render HTML from template
        html_content = self.template_service.render(resume, self.template_name)

        # Get CSS for the template
        css_content = self.template_service.get_css(self.template_name)

        # Ensure output directory exists (idempotent for build command's mkdir)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate PDF using WeasyPrint
        try:
            html = HTML(string=html_content)
            css = CSS(string=css_content)

            # Render to get Document object with page count (AC #6)
            document = html.render(stylesheets=[css])
            page_count = len(document.pages)

            # Write PDF to file
            document.write_pdf(output_path)

        except OSError as e:
            raise RenderError(
                message=f"PDF generation failed: {e}",
                suggestion="Ensure WeasyPrint dependencies are installed. "
                "On macOS: brew install pango cairo",
            ) from e
        except Exception as e:
            raise RenderError(
                message=f"Failed to render PDF: {e}",
                path=str(output_path),
                suggestion="Check the resume data and template for issues",
            ) from e

        return PDFRenderResult(output_path=output_path, page_count=page_count)

    def render_to_bytes(self, resume: ResumeData) -> bytes:
        """Render resume to PDF bytes.

        Useful for streaming or in-memory processing.

        Args:
            resume: ResumeData to render.

        Returns:
            PDF content as bytes.

        Raises:
            RenderError: If PDF generation fails.
        """
        html_content = self.template_service.render(resume, self.template_name)
        css_content = self.template_service.get_css(self.template_name)

        try:
            html = HTML(string=html_content)
            css = CSS(string=css_content)

            # WeasyPrint returns bytes when no target is specified
            return cast(bytes, html.write_pdf(stylesheets=[css]))
        except OSError as e:
            raise RenderError(
                message=f"PDF generation failed: {e}",
                suggestion="Ensure WeasyPrint dependencies are installed. "
                "On macOS: brew install pango cairo",
            ) from e
        except Exception as e:
            raise RenderError(
                message=f"Failed to render PDF: {e}",
                suggestion="Check the resume data and template for issues",
            ) from e
