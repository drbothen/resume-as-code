"""Resume data models for output generation."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from resume_as_code.models.certification import Certification


class ContactInfo(BaseModel):
    """Contact information for resume header."""

    name: str
    title: str | None = None  # Professional title/headline
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None


class ResumeBullet(BaseModel):
    """A single achievement bullet point."""

    text: str
    metrics: str | None = None


class ResumeItem(BaseModel):
    """A single experience entry (job, project, etc.)."""

    title: str
    organization: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    bullets: list[ResumeBullet] = Field(default_factory=list)

    # Executive fields
    scope_budget: str | None = None
    scope_team_size: int | None = None
    scope_revenue: str | None = None


class ResumeSection(BaseModel):
    """A section of the resume (Experience, Projects, etc.)."""

    title: str
    items: list[ResumeItem] = Field(default_factory=list)


class ResumeData(BaseModel):
    """Complete resume data for rendering."""

    contact: ContactInfo
    summary: str | None = None
    sections: list[ResumeSection] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    education: list[ResumeItem] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)

    def get_active_certifications(self) -> list[Certification]:
        """Get certifications that should be displayed on resume.

        Returns certifications where display=True and not expired.

        Returns:
            List of active, displayable certifications.
        """
        return [
            cert for cert in self.certifications if cert.display and cert.get_status() != "expired"
        ]

    @classmethod
    def from_work_units(
        cls,
        work_units: list[dict[str, Any]],
        contact: ContactInfo,
        summary: str | None = None,
    ) -> ResumeData:
        """Build ResumeData from selected Work Units.

        Transforms Work Units into resume-ready format, converting
        problem/action/outcome into achievement bullets.

        Args:
            work_units: List of Work Unit dictionaries.
            contact: Contact information for the resume.
            summary: Optional professional summary.

        Returns:
            ResumeData instance ready for rendering.
        """
        experience_items: list[ResumeItem] = []

        for wu in work_units:
            bullets = cls._extract_bullets(wu)
            scope = wu.get("scope", {}) or {}
            item = ResumeItem(
                title=wu.get("title", ""),
                organization=wu.get("organization"),
                start_date=cls._format_date(wu.get("time_started")),
                end_date=cls._format_date(wu.get("time_ended")),
                bullets=bullets,
                scope_budget=scope.get("budget_managed"),
                scope_team_size=scope.get("team_size"),
                scope_revenue=scope.get("revenue_influenced"),
            )
            experience_items.append(item)

        sections = [
            ResumeSection(title="Experience", items=experience_items),
        ]

        # Extract skills from all Work Units
        all_skills: set[str] = set()
        for wu in work_units:
            all_skills.update(wu.get("tags", []))
            # Handle skills_demonstrated which may be list of dicts or strings
            for skill in wu.get("skills_demonstrated", []):
                if isinstance(skill, dict):
                    all_skills.add(skill.get("name", ""))
                else:
                    all_skills.add(str(skill))

        return cls(
            contact=contact,
            summary=summary,
            sections=sections,
            skills=sorted(s for s in all_skills if s),
        )

    @staticmethod
    def _extract_bullets(work_unit: dict[str, Any]) -> list[ResumeBullet]:
        """Extract achievement bullets from Work Unit.

        Args:
            work_unit: Work Unit dictionary.

        Returns:
            List of ResumeBullet objects.
        """
        bullets: list[ResumeBullet] = []

        # Main outcome as primary bullet
        outcome = work_unit.get("outcome", {}) or {}
        if result := outcome.get("result"):
            bullets.append(
                ResumeBullet(
                    text=result,
                    metrics=outcome.get("quantified_impact"),
                )
            )

        # Actions as supporting bullets (limit to 3)
        for action in work_unit.get("actions", [])[:3]:
            bullets.append(ResumeBullet(text=action))

        return bullets

    @staticmethod
    def _format_date(d: date | str | None) -> str | None:
        """Format date for display.

        Args:
            d: Date object, string, or None.

        Returns:
            Formatted date string or None.
        """
        if d is None:
            return None
        if isinstance(d, date):
            return d.strftime("%b %Y")
        if isinstance(d, str) and len(d) >= 7:
            return d[:7]  # YYYY-MM
        return str(d)
