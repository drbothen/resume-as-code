"""Services package for resume-as-code."""

from __future__ import annotations

from resume_as_code.services.jd_parser import parse_jd_file, parse_jd_text

__all__ = [
    "parse_jd_file",
    "parse_jd_text",
]
