"""PDF provider using WeasyPrint."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from weasyprint import CSS, HTML  # type: ignore[import-untyped]

from resume_as_code.models.errors import RenderError
from resume_as_code.models.resume import ResumeData
from resume_as_code.services.template_service import TemplateService


class PDFProvider:
    """Provider for generating PDF resumes using WeasyPrint."""

    def __init__(
        self,
        template_service: TemplateService | None = None,
        template_name: str = "modern",
    ) -> None:
        """Initialize PDF provider.

        Args:
            template_service: Template service for rendering HTML.
            template_name: Name of template to use.
        """
        self.template_service = template_service or TemplateService()
        self.template_name = template_name

    def render(self, resume: ResumeData, output_path: Path) -> Path:
        """Render resume to PDF file.

        Args:
            resume: ResumeData to render.
            output_path: Path for output PDF file.

        Returns:
            Path to generated PDF.

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

            html.write_pdf(
                output_path,
                stylesheets=[css],
            )
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

        return output_path

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
