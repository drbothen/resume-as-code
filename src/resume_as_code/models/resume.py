"""Resume data models for output generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from resume_as_code.models.board_role import BoardRole
from resume_as_code.models.certification import Certification
from resume_as_code.models.education import Education
from resume_as_code.models.publication import Publication

if TYPE_CHECKING:
    from resume_as_code.models.config import CurationConfig, ONetConfig, SkillsConfig
    from resume_as_code.models.job_description import JobDescription
    from resume_as_code.models.position import Position


def normalize_employer(name: str) -> str:
    """Normalize employer name for grouping comparison.

    Handles case-insensitivity, ampersand variations, and common suffixes
    to ensure consistent grouping of employer positions.

    Args:
        name: Employer name to normalize.

    Returns:
        Normalized employer name for comparison.
    """
    normalized = name.lower().strip()
    # Normalize ampersand variations
    normalized = normalized.replace(" & ", " and ")
    normalized = normalized.replace("&", " and ")
    # Remove common corporate suffixes
    for suffix in [", inc.", ", inc", " inc.", " inc", ", llc", " llc", ", corp", " corp"]:
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
    return normalized.strip()


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

    # Executive scope - formatted line derived from Position.scope
    # Individual scope_* fields removed in Story 7.2 - use scope_line only
    scope_line: str | None = None


@dataclass
class EmployerGroup:
    """Group of positions at the same employer (Story 8.1).

    Used to render multiple positions at the same employer under
    a single employer heading with grouped tenure display.
    """

    employer: str
    location: str | None
    total_start_date: str
    total_end_date: str | None  # None = current position
    positions: list[ResumeItem] = field(default_factory=list)

    @property
    def is_multi_position(self) -> bool:
        """Check if this group has multiple positions."""
        return len(self.positions) > 1

    @property
    def tenure_display(self) -> str:
        """Format total tenure as 'start - end' or 'start - Present'."""
        end = self.total_end_date or "Present"
        return f"{self.total_start_date} - {end}"


def group_positions_by_employer(items: list[ResumeItem]) -> list[EmployerGroup]:
    """Group resume items by normalized employer name.

    Groups positions at the same employer (handling name variations)
    and calculates total tenure for each employer group.

    Args:
        items: List of ResumeItem objects to group.

    Returns:
        List of EmployerGroup objects, ordered by most recent position date.
    """
    if not items:
        return []

    # Group items by normalized employer name
    groups_by_key: dict[str, list[ResumeItem]] = {}
    for item in items:
        # Items without organization get unique keys
        if item.organization is None:
            key = f"__none__{id(item)}"
        else:
            key = normalize_employer(item.organization)

        if key not in groups_by_key:
            groups_by_key[key] = []
        groups_by_key[key].append(item)

    # Build EmployerGroup objects
    employer_groups: list[EmployerGroup] = []
    for group_items in groups_by_key.values():
        # Sort positions within group by start_date descending (most recent first)
        sorted_positions = sorted(
            group_items,
            key=lambda x: x.start_date or "",
            reverse=True,
        )

        # Use most recent position for employer name and location
        most_recent = sorted_positions[0]
        employer = most_recent.organization or most_recent.title
        location = most_recent.location

        # Calculate total tenure (earliest start to latest end)
        start_dates = [p.start_date for p in sorted_positions if p.start_date]
        end_dates = [p.end_date for p in sorted_positions]

        total_start = min(start_dates) if start_dates else ""
        # If any position has no end_date (current), total_end is None
        if None in end_dates:
            total_end = None
        else:
            non_none_dates = [d for d in end_dates if d]
            total_end = max(non_none_dates) if non_none_dates else None

        employer_groups.append(
            EmployerGroup(
                employer=employer,
                location=location,
                total_start_date=total_start,
                total_end_date=total_end,
                positions=sorted_positions,
            )
        )

    # Sort groups by most recent position date (descending)
    employer_groups.sort(
        key=lambda g: g.positions[0].start_date or "" if g.positions else "",
        reverse=True,
    )

    return employer_groups


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
    board_roles: list[BoardRole] = Field(default_factory=list)
    publications: list[Publication] = Field(default_factory=list)
    # Flag indicating publications are pre-sorted by JD relevance (Story 8.2 Task 6)
    publications_curated: bool = Field(
        default=False,
        description="True when publications are pre-sorted by relevance score",
    )
    # Footer notice for tailored resumes (Story 7.19)
    tailored_notice_text: str | None = None

    def get_active_certifications(self) -> list[Certification]:
        """Get certifications that should be displayed on resume.

        Returns certifications where display=True and not expired.

        Returns:
            List of active, displayable certifications.
        """
        return [
            cert for cert in self.certifications if cert.display and cert.get_status() != "expired"
        ]

    def get_sorted_board_roles(self) -> list[BoardRole]:
        """Get board roles sorted for display.

        Sorting priority:
        1. Directors first (higher governance level)
        2. Then by start_date descending (most recent first)

        Only returns roles where display=True.

        Returns:
            List of displayable board roles sorted by type and date.
        """
        displayable = [role for role in self.board_roles if role.display]

        # Define type priority: director=0, advisory=1, committee=2
        type_priority = {"director": 0, "advisory": 1, "committee": 2}

        return sorted(
            displayable,
            key=lambda role: (type_priority.get(role.type, 1), -(int(role.start_date[:4]))),
        )

    def get_sorted_publications(self) -> list[Publication]:
        """Get publications sorted for display.

        When publications_curated is True (JD provided), preserves current order
        which is already sorted by relevance score descending. (Story 8.2 AC #5)

        When publications_curated is False (no JD), sorts by date descending
        (most recent first) as fallback behavior. (Story 8.2 AC #6)

        Only returns publications where display=True.

        Returns:
            List of displayable publications in appropriate order.
        """
        displayable = [pub for pub in self.publications if pub.display]

        if self.publications_curated:
            # Preserve relevance-sorted order from curation
            return displayable

        # Default: sort by date descending (most recent first)
        return sorted(displayable, key=lambda pub: pub.date, reverse=True)

    @classmethod
    def from_work_units(
        cls,
        work_units: list[dict[str, Any]],
        contact: ContactInfo,
        summary: str | None = None,
        skills_config: SkillsConfig | None = None,
        jd_keywords: set[str] | None = None,
        positions_path: Path | None = None,
        onet_config: ONetConfig | None = None,
        curation_config: CurationConfig | None = None,
        jd: JobDescription | None = None,
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
            onet_config: Optional O*NET configuration for skill discovery.
            curation_config: Optional curation configuration for action scoring.
            jd: Optional job description for action-level scoring (Story 7.18).

        Returns:
            ResumeData instance ready for rendering.
        """
        # Build experience items with position grouping if positions available
        experience_items = cls._build_experience_items(
            work_units, positions_path, curation_config, jd
        )

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
            from resume_as_code.services.skill_registry import SkillRegistry

            # Load registry with O*NET support if configured (Story 7.17)
            registry = SkillRegistry.load_with_onet(onet_config)

            curator = SkillCurator(
                max_count=skills_config.max_display,
                exclude=skills_config.exclude,
                prioritize=skills_config.prioritize,
                registry=registry,
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
        curation_config: CurationConfig | None = None,
        jd: JobDescription | None = None,
    ) -> list[ResumeItem]:
        """Build experience items from work units, grouped by position.

        Groups work units by position_id when positions are available,
        otherwise falls back to treating each work unit as standalone entry.

        When action scoring is enabled (curation_config.action_scoring_enabled=True)
        and a JD is provided, uses ContentCurator.curate_action_bullets to select
        the most JD-relevant action bullets for each position. (Story 7.18)

        Args:
            work_units: List of Work Unit dictionaries.
            positions_path: Optional path to positions.yaml file.
            curation_config: Optional curation configuration for action scoring.
            jd: Optional job description for action-level scoring.

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
                item = cls._build_item_from_position(pos, pos_work_units, curation_config, jd)
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
        curation_config: CurationConfig | None = None,
        jd: JobDescription | None = None,
    ) -> ResumeItem:
        """Build a ResumeItem from a position with work unit bullets.

        When action scoring is enabled and a JD is provided, uses
        ContentCurator.curate_action_bullets to select the most relevant
        action bullets for this position. (Story 7.18)

        Args:
            position: Position model instance.
            work_units: List of Work Unit dictionaries for this position.
            curation_config: Optional curation configuration for action scoring.
            jd: Optional job description for action-level scoring.

        Returns:
            ResumeItem populated from position and work unit data.
        """
        from resume_as_code.services.position_service import format_scope_line

        # Check if action scoring should be used (Story 7.18)
        use_action_scoring = (
            curation_config is not None
            and jd is not None
            and curation_config.action_scoring_enabled
        )

        if use_action_scoring:
            # Use action-level curation for bullet selection
            # Assertions for type narrowing (mypy)
            assert curation_config is not None
            assert jd is not None
            all_bullets = cls._curate_bullets_for_position(
                position, work_units, curation_config, jd
            )
        else:
            # Fallback: collect all bullets from work units without scoring
            all_bullets = []
            for wu in work_units:
                bullets = cls._extract_bullets(wu)
                all_bullets.extend(bullets)

        # Scope line derived from Position.scope only (Story 7.2 - unified model)
        # WorkUnit.scope is deprecated and ignored for resume rendering
        scope_line = format_scope_line(position)

        return ResumeItem(
            title=position.title,
            organization=position.employer,
            location=position.location,
            start_date=cls._format_position_date(position.start_date),
            end_date=cls._format_position_date(position.end_date),
            bullets=all_bullets,
            scope_line=scope_line,
        )

    @classmethod
    def _build_item_from_work_unit(
        cls,
        work_unit: dict[str, Any],
    ) -> ResumeItem:
        """Build a ResumeItem from a standalone work unit.

        Used for work units without position_id (personal projects, etc.).
        Note: WorkUnit.scope is deprecated - standalone work units have no scope_line.

        Args:
            work_unit: Work Unit dictionary.

        Returns:
            ResumeItem populated from work unit data.
        """
        bullets = cls._extract_bullets(work_unit)

        return ResumeItem(
            title=work_unit.get("title", ""),
            organization=work_unit.get("organization"),
            start_date=cls._format_date(work_unit.get("time_started")),
            end_date=cls._format_date(work_unit.get("time_ended")),
            bullets=bullets,
        )

    @classmethod
    def _curate_bullets_for_position(
        cls,
        position: Position,
        work_units: list[dict[str, Any]],
        curation_config: CurationConfig,
        jd: JobDescription,
    ) -> list[ResumeBullet]:
        """Curate bullets for a position using action-level scoring.

        Uses ContentCurator.curate_action_bullets to select the most
        JD-relevant actions from all work units for this position. (Story 7.18)

        Args:
            position: Position model instance.
            work_units: List of Work Unit dictionaries for this position.
            curation_config: Curation configuration for action scoring.
            jd: Job description for scoring actions.

        Returns:
            List of ResumeBullet objects containing curated actions.
        """
        from resume_as_code.models.work_unit import WorkUnit
        from resume_as_code.services.content_curator import ContentCurator
        from resume_as_code.services.embedder import EmbeddingService

        # Convert dicts to WorkUnit models
        wu_models: list[WorkUnit] = []
        for wu_dict in work_units:
            try:
                wu_model = WorkUnit.model_validate(wu_dict)
                wu_models.append(wu_model)
            except Exception:
                # Skip invalid work units - they'll be excluded from curation
                continue

        if not wu_models:
            # Fallback to legacy extraction if no valid models
            all_bullets: list[ResumeBullet] = []
            for wu in work_units:
                all_bullets.extend(cls._extract_bullets(wu))
            return all_bullets

        # Create curator with embedder and config
        embedder = EmbeddingService()
        curator = ContentCurator(embedder=embedder, config=curation_config)

        # Curate actions based on JD relevance
        result = curator.curate_action_bullets(position, wu_models, jd)

        # Convert selected action strings to ResumeBullet objects
        # Preserve quantified_impact from work unit outcomes as metrics
        return [
            ResumeBullet(text=action, metrics=result.metrics.get(action))
            for action in result.selected
        ]

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
