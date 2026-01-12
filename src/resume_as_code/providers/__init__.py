"""Output providers for resume generation."""

from resume_as_code.providers.docx import DOCXProvider
from resume_as_code.providers.pdf import PDFProvider

__all__ = ["DOCXProvider", "PDFProvider"]
