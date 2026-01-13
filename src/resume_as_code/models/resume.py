"""Resume data models for output generation."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from resume_as_code.models.certification import Certification
from resume_as_code.models.education import Education

if TYPE_CHECKING:
    from resume_as_code.models.config import SkillsConfig
    from resume_as_code.models.position import Position


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
    education: list[Education] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    career_highlights: list[str] = Field(default_factory=list)

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
        skills_config: SkillsConfig | None = None,
        jd_keywords: set[str] | None = None,
        positions_path: Path | None = None,
    ) -> ResumeData:
        """Build ResumeData from selected Work Units.

        Transforms Work Units into resume-ready format, converting
        problem/action/outcome into achievement bullets. Groups work units
        by position for proper employer/role hierarchy.

        Args:
            work_units: List of Work Unit dictionaries.
            contact: Contact information for the resume.
            summary: Optional professional summary.
            skills_config: Optional skills curation configuration.
            jd_keywords: Optional JD keywords for skill prioritization.
            positions_path: Optional path to positions.yaml file.

        Returns:
            ResumeData instance ready for rendering.
        """
        # Build experience items with position grouping if positions available
        experience_items = cls._build_experience_items(work_units, positions_path)

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

        # Curate skills if config provided, otherwise use legacy sorting
        if skills_config is not None:
            from resume_as_code.services.skill_curator import SkillCurator

            curator = SkillCurator(
                max_count=skills_config.max_display,
                exclude=skills_config.exclude,
                prioritize=skills_config.prioritize,
            )
            result = curator.curate(all_skills, jd_keywords)
            curated_skills = result.included
        else:
            # Legacy behavior: alphabetical sort
            curated_skills = sorted(s for s in all_skills if s)

        return cls(
            contact=contact,
            summary=summary,
            sections=sections,
            skills=curated_skills,
        )

    @classmethod
    def _build_experience_items(
        cls,
        work_units: list[dict[str, Any]],
        positions_path: Path | None = None,
    ) -> list[ResumeItem]:
        """Build experience items from work units, grouped by position.

        Groups work units by position_id when positions are available,
        otherwise falls back to treating each work unit as standalone entry.

        Args:
            work_units: List of Work Unit dictionaries.
            positions_path: Optional path to positions.yaml file.

        Returns:
            List of ResumeItem objects sorted by date (most recent first).
        """
        from resume_as_code.services.position_service import PositionService

        # Load positions if path provided
        position_service = PositionService(positions_path) if positions_path else None
        positions = position_service.load_positions() if position_service else {}

        # Group work units by position_id
        wu_by_position: dict[str | None, list[dict[str, Any]]] = {}
        for wu in work_units:
            pos_id = wu.get("position_id")
            if pos_id not in wu_by_position:
                wu_by_position[pos_id] = []
            wu_by_position[pos_id].append(wu)

        experience_items: list[ResumeItem] = []

        # Process work units with valid position references
        for pos_id, pos_work_units in wu_by_position.items():
            if pos_id and pos_id in positions:
                # Build item from position with work unit bullets
                pos = positions[pos_id]
                item = cls._build_item_from_position(pos, pos_work_units)
                experience_items.append(item)
            else:
                # Work units without positions or with invalid position_id
                # Treat each as standalone entry
                for wu in pos_work_units:
                    item = cls._build_item_from_work_unit(wu)
                    experience_items.append(item)

        # Sort by start_date descending (most recent first)
        experience_items.sort(
            key=lambda item: item.start_date or "",
            reverse=True,
        )

        return experience_items

    @classmethod
    def _build_item_from_position(
        cls,
        position: Position,
        work_units: list[dict[str, Any]],
    ) -> ResumeItem:
        """Build a ResumeItem from a position with work unit bullets.

        Args:
            position: Position model instance.
            work_units: List of Work Unit dictionaries for this position.

        Returns:
            ResumeItem populated from position and work unit data.
        """
        # Collect all bullets from work units
        all_bullets: list[ResumeBullet] = []
        scope_budget: str | None = None
        scope_team_size: int | None = None
        scope_revenue: str | None = None

        for wu in work_units:
            bullets = cls._extract_bullets(wu)
            all_bullets.extend(bullets)

            # Aggregate scope from work units (take first non-None values)
            scope = wu.get("scope", {}) or {}
            if not scope_budget:
                scope_budget = scope.get("budget_managed")
            if not scope_team_size:
                scope_team_size = scope.get("team_size")
            if not scope_revenue:
                scope_revenue = scope.get("revenue_influenced")

        return ResumeItem(
            title=position.title,
            organization=position.employer,
            location=position.location,
            start_date=cls._format_position_date(position.start_date),
            end_date=cls._format_position_date(position.end_date),
            bullets=all_bullets,
            scope_budget=scope_budget,
            scope_team_size=scope_team_size,
            scope_revenue=scope_revenue,
        )

    @classmethod
    def _build_item_from_work_unit(
        cls,
        work_unit: dict[str, Any],
    ) -> ResumeItem:
        """Build a ResumeItem from a standalone work unit.

        Used for work units without position_id (personal projects, etc.).

        Args:
            work_unit: Work Unit dictionary.

        Returns:
            ResumeItem populated from work unit data.
        """
        bullets = cls._extract_bullets(work_unit)
        scope = work_unit.get("scope", {}) or {}

        return ResumeItem(
            title=work_unit.get("title", ""),
            organization=work_unit.get("organization"),
            start_date=cls._format_date(work_unit.get("time_started")),
            end_date=cls._format_date(work_unit.get("time_ended")),
            bullets=bullets,
            scope_budget=scope.get("budget_managed"),
            scope_team_size=scope.get("team_size"),
            scope_revenue=scope.get("revenue_influenced"),
        )

    @staticmethod
    def _format_position_date(d: str | None) -> str | None:
        """Format position date (YYYY-MM) for display.

        Args:
            d: Date string in YYYY-MM format, or None.

        Returns:
            Formatted date string (YYYY) or None.
        """
        if d is None:
            return None
        # Position dates are YYYY-MM format, return just the year
        return d[:4] if len(d) >= 4 else d

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
