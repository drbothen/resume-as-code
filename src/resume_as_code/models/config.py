"""Configuration models for Resume as Code."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from resume_as_code.models.board_role import BoardRole
from resume_as_code.models.certification import Certification
from resume_as_code.models.education import Education
from resume_as_code.models.publication import Publication

logger = logging.getLogger(__name__)

# Default tailored notice text (Story 7.19)
DEFAULT_TAILORED_NOTICE = (
    "This resume highlights experience most relevant to this role. "
    "Full details available upon request."
)

# Employment continuity mode type (Story 7.20)
EmploymentContinuityMode = Literal["minimum_bullet", "allow_gaps"]


class BulletsPerPositionConfig(BaseModel):
    """Bullet limits based on position age.

    Research-backed limits (2024-2025 resume studies):
    - Recent positions (0-3 years): 4-6 bullets
    - Mid positions (3-7 years): 3-4 bullets
    - Older positions (7+ years): 2-3 bullets
    """

    recent_years: int = Field(default=3, ge=1, le=10, description="Years considered 'recent'")
    recent_max: int = Field(default=6, ge=1, le=10, description="Max bullets for recent positions")
    mid_years: int = Field(default=7, ge=3, le=15, description="Years considered 'mid-career'")
    mid_max: int = Field(default=4, ge=1, le=8, description="Max bullets for mid positions")
    older_max: int = Field(default=3, ge=1, le=6, description="Max bullets for older positions")


class CurationConfig(BaseModel):
    """Configuration for content curation.

    Research-backed defaults (2024-2025 resume studies):
    - Career highlights: 3-5 optimal
    - Certifications: 3-5 most relevant
    - Board roles: 2-3 unless executive
    - Skills: 6-10 optimal (median 8-9)
    """

    career_highlights_max: int = Field(default=4, ge=1, le=10)
    certifications_max: int = Field(default=5, ge=1, le=15)
    board_roles_max: int = Field(default=3, ge=1, le=10)
    board_roles_executive_max: int = Field(default=5, ge=1, le=10)
    publications_max: int = Field(default=3, ge=1, le=10)
    skills_max: int = Field(default=10, ge=1, le=30)

    bullets_per_position: BulletsPerPositionConfig = Field(default_factory=BulletsPerPositionConfig)

    min_relevance_score: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Minimum score for inclusion (below this, item is excluded)",
    )

    # Action-level scoring (Story 7.18)
    action_scoring_enabled: bool = Field(
        default=True,
        description="Score individual action bullets against JD relevance.",
    )
    min_action_relevance_score: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Minimum score for action bullet inclusion.",
    )


class ProfileConfig(BaseModel):
    """User profile information for resume header.

    All fields are optional to support incremental configuration.
    URL fields use HttpUrl for validation.
    """

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: HttpUrl | None = None
    github: HttpUrl | None = None
    website: HttpUrl | None = None
    title: str | None = None  # Professional title/headline
    summary: str | None = None  # Executive summary template


class SkillsConfig(BaseModel):
    """Configuration for skills curation.

    Controls how skills are deduplicated, filtered, and prioritized
    for resume display.
    """

    max_display: int = Field(default=15, ge=1, le=50)
    exclude: list[str] = Field(default_factory=list)
    prioritize: list[str] = Field(default_factory=list)


class ScoringWeights(BaseModel):
    """Weights for ranking algorithm.

    BM25 vs Semantic weights control the balance in RRF fusion.
    Higher bm25_weight emphasizes keyword matching.
    Higher semantic_weight emphasizes meaning/context matching.

    Recency decay (Story 7.9) uses exponential decay to weight recent
    experience higher than older experience:

        recency_score = e^(-λ × years_ago)

    Where:
        λ = ln(2) / recency_half_life  (decay constant)
        years_ago = (today - time_ended).days / 365.25

    Example with 5-year half-life:
        Current position → 100% weight
        1 year ago → ~87% weight
        5 years ago → 50% weight
        10 years ago → 25% weight

    Final score blends relevance and recency:
        final = (1 - recency_blend) × relevance + recency_blend × recency

    Section-level semantic matching (Story 7.11):
        When use_sectioned_semantic is True, matches work unit sections
        against JD sections with configurable weights:
        - Outcome ↔ JD Requirements: 40% (most predictive of job fit)
        - Actions ↔ JD Requirements: 30% (what candidate did)
        - Skills ↔ JD Skills: 20% (technical alignment)
        - Title ↔ JD Full: 10% (role alignment)
    """

    # BM25 vs Semantic balance for RRF fusion
    bm25_weight: float = Field(default=1.0, ge=0.0, le=2.0)
    semantic_weight: float = Field(default=1.0, ge=0.0, le=2.0)

    # Field-specific BM25 weights (title/skills weighted higher per HBR 2023 research)
    title_weight: float = Field(default=2.0, ge=0.0, le=10.0)
    skills_weight: float = Field(default=1.5, ge=0.0, le=10.0)
    experience_weight: float = Field(default=1.0, ge=0.0, le=10.0)

    # Recency decay (Story 7.9)
    recency_half_life: float | None = Field(
        default=5.0,
        ge=1.0,
        le=20.0,
        description="Years for experience to decay to 50% weight. None disables decay.",
    )
    recency_blend: float = Field(
        default=0.2,
        ge=0.0,
        le=0.5,
        description="Weight of recency in final score (0.2 = 20%).",
    )

    # Section-level semantic weights (Story 7.11)
    use_sectioned_semantic: bool = Field(
        default=False,
        description="Enable section-level semantic matching (more precise but slower).",
    )
    section_outcome_weight: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Weight for outcome section in semantic scoring.",
    )
    section_actions_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for actions section in semantic scoring.",
    )
    section_skills_weight: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Weight for skills section in semantic scoring.",
    )
    section_title_weight: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Weight for title section in semantic scoring.",
    )

    # Seniority matching (Story 7.12)
    use_seniority_matching: bool = Field(
        default=True,
        description="Enable seniority level matching against JD.",
    )
    seniority_blend: float = Field(
        default=0.1,
        ge=0.0,
        le=0.3,
        description="How much seniority alignment affects final score (0.1 = 10%).",
    )

    # Impact category matching (Story 7.13)
    use_impact_matching: bool = Field(
        default=True,
        description="Enable impact category matching against role type.",
    )
    impact_blend: float = Field(
        default=0.1,
        ge=0.0,
        le=0.3,
        description="How much impact alignment affects final score (0.1 = 10%).",
    )
    quantified_boost: float = Field(
        default=1.25,
        ge=1.0,
        le=2.0,
        description="Multiplier for work units with quantified outcomes (1.25 = 25% boost).",
    )

    @model_validator(mode="after")
    def validate_section_weights_sum(self) -> ScoringWeights:
        """Validate section weights sum to ~1.0 when sectioned semantic is enabled."""
        if self.use_sectioned_semantic:
            total = (
                self.section_outcome_weight
                + self.section_actions_weight
                + self.section_skills_weight
                + self.section_title_weight
            )
            if not (0.99 <= total <= 1.01):
                msg = f"Section weights must sum to 1.0, got {total:.2f}"
                raise ValueError(msg)
        return self


class ONetConfig(BaseModel):
    """O*NET API v2.0 configuration.

    API key can be set via config file or ONET_API_KEY environment variable.
    Register at https://services.onetcenter.org/developer/signup

    Attributes:
        enabled: Enable O*NET API integration.
        api_key: O*NET API key (or set ONET_API_KEY env var).
        cache_ttl: Cache TTL in seconds (minimum 1 hour).
        timeout: API request timeout in seconds.
        retry_delay_ms: Minimum delay between retries in milliseconds.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(
        default=True,
        description="Enable O*NET API integration",
    )
    api_key: str | None = Field(
        default=None,
        description="O*NET API key (or set ONET_API_KEY env var)",
    )
    cache_ttl: int = Field(
        default=86400,  # 24 hours
        ge=3600,  # Minimum 1 hour
        description="Cache TTL in seconds",
    )
    timeout: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="API request timeout in seconds",
    )
    retry_delay_ms: int = Field(
        default=200,
        ge=200,  # O*NET documented minimum
        description="Minimum delay between retries in milliseconds",
    )

    @model_validator(mode="after")
    def resolve_env_api_key(self) -> ONetConfig:
        """Resolve API key from environment if not in config."""
        if self.api_key is None:
            self.api_key = os.environ.get("ONET_API_KEY")
        return self

    @property
    def is_configured(self) -> bool:
        """Check if API key is available and enabled."""
        return self.enabled and self.api_key is not None


class TemplateOptions(BaseModel):
    """Template rendering options (Story 8.1).

    Controls how resume templates render experience sections.
    """

    group_employer_positions: bool = Field(
        default=True,
        description="Group multiple positions at the same employer under one heading",
    )


class DocxConfig(BaseModel):
    """DOCX-specific configuration (Story 13.1).

    Allows specifying a different template for DOCX output than PDF.
    """

    template: str | None = Field(
        default=None,
        description="DOCX template name (without .docx extension).",
    )


class DataPaths(BaseModel):
    """Custom paths for separated data files (Story 9.2 + 11.2).

    Allows users to customize the location of data files instead of using
    the default locations in the project root.

    Story 11.2 adds directory mode options (*_dir fields) for sharded storage
    where each item is stored as a separate YAML file in a directory.
    """

    profile: str | None = Field(default=None, description="Path to profile.yaml")
    certifications: str | None = Field(default=None, description="Path to certifications.yaml")
    education: str | None = Field(default=None, description="Path to education.yaml")
    highlights: str | None = Field(default=None, description="Path to highlights.yaml")
    publications: str | None = Field(default=None, description="Path to publications.yaml")
    board_roles: str | None = Field(default=None, description="Path to board-roles.yaml")

    # Directory mode options (Story 11.2 / TD-005)
    certifications_dir: str | None = Field(
        default=None, description="Path to certifications directory (sharded mode)"
    )
    education_dir: str | None = Field(
        default=None, description="Path to education directory (sharded mode)"
    )
    highlights_dir: str | None = Field(
        default=None, description="Path to highlights directory (sharded mode)"
    )
    publications_dir: str | None = Field(
        default=None, description="Path to publications directory (sharded mode)"
    )
    board_roles_dir: str | None = Field(
        default=None, description="Path to board-roles directory (sharded mode)"
    )

    @model_validator(mode="after")
    def validate_no_dual_config(self) -> DataPaths:
        """Ensure both file and dir aren't specified for same resource."""
        pairs = [
            ("certifications", "certifications_dir"),
            ("education", "education_dir"),
            ("highlights", "highlights_dir"),
            ("publications", "publications_dir"),
            ("board_roles", "board_roles_dir"),
        ]
        for file_key, dir_key in pairs:
            if getattr(self, file_key) and getattr(self, dir_key):
                raise ValueError(f"Cannot specify both {file_key} and {dir_key}")
        return self


class ResumeConfig(BaseModel):
    """Complete configuration for Resume as Code."""

    # Schema version for migration tracking (Story 9.1)
    schema_version: str | None = Field(
        default=None,
        description="Schema version for tracking migrations (e.g., '2.0.0')",
    )

    # Output settings
    output_dir: Path = Field(default=Path("./dist"))
    default_format: Literal["pdf", "docx", "both"] = Field(default="both")
    default_template: str = Field(default="modern")

    # Work unit settings
    work_units_dir: Path = Field(default=Path("./work-units"))

    # Employment history settings
    positions_path: Path = Field(default=Path("./positions.yaml"))

    # Ranking settings
    scoring_weights: ScoringWeights = Field(default_factory=ScoringWeights)
    default_top_k: int = Field(default=8, ge=1, le=50)

    # Editor settings
    editor: str | None = Field(default=None)  # Falls back to $EDITOR

    # Profile information (Story 9.2: Optional for config-only mode)
    profile: ProfileConfig | None = Field(
        default=None,
        description="Profile data (use data_loader for access, supports external file)",
    )

    # Certifications (Story 9.2: Optional for config-only mode)
    certifications: list[Certification] | None = Field(
        default=None,
        description="Certifications (use data_loader for access, supports external file)",
    )

    # Education (Story 9.2: Optional for config-only mode)
    education: list[Education] | None = Field(
        default=None,
        description="Education (use data_loader for access, supports external file)",
    )

    # Skills curation
    skills: SkillsConfig = Field(default_factory=SkillsConfig)

    # Career highlights (Story 9.2: Optional for config-only mode)
    career_highlights: list[str] | None = Field(
        default=None,
        description="Career highlights (use data_loader for access, supports external file)",
    )

    # Board & Advisory Roles (Story 9.2: Optional for config-only mode)
    board_roles: list[BoardRole] | None = Field(
        default=None,
        description="Board roles (use data_loader for access, supports external file)",
    )

    # Publications & Speaking Engagements (Story 9.2: Optional for config-only mode)
    publications: list[Publication] | None = Field(
        default=None,
        description="Publications (use data_loader for access, supports external file)",
    )

    # Tailored resume notice (Story 7.19)
    tailored_notice: bool = Field(
        default=False,
        description="Show footer notice that resume is tailored for the role",
    )
    tailored_notice_text: str | None = Field(
        default=None,
        description="Custom tailored notice text (overrides default)",
    )

    # Employment continuity mode (Story 7.20)
    employment_continuity: EmploymentContinuityMode = Field(
        default="minimum_bullet",
        description="minimum_bullet: always include 1 work unit per position; "
        "allow_gaps: pure relevance filtering with gap warnings",
    )

    # Work history duration filter (Story 13.2)
    history_years: int | None = Field(
        default=None,
        ge=1,
        le=50,
        description="Limit work history to last N years (None = unlimited)",
    )

    # O*NET API configuration
    onet: ONetConfig | None = Field(default=None)

    # Content curation configuration
    curation: CurationConfig = Field(default_factory=CurationConfig)

    # Template rendering options (Story 8.1)
    template_options: TemplateOptions = Field(default_factory=TemplateOptions)

    # Custom data file paths (Story 9.2)
    data_paths: DataPaths | None = Field(
        default=None,
        description="Custom paths for separated data files",
    )

    # Custom templates directory (Story 11.3)
    templates_dir: Path | None = Field(
        default=None,
        description="Path to custom templates directory (supplements built-in templates)",
    )

    # DOCX-specific configuration (Story 13.1)
    docx: DocxConfig | None = Field(
        default=None,
        description="DOCX-specific settings (template override)",
    )

    @field_validator("career_highlights", mode="before")
    @classmethod
    def validate_career_highlights(cls, v: list[str] | None) -> list[str] | None:
        """Validate career highlights list."""
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("career_highlights must be a list")
        for i, highlight in enumerate(v):
            if not isinstance(highlight, str):
                raise ValueError(f"career_highlights[{i}] must be a string")
            if not highlight.strip():
                raise ValueError(f"career_highlights[{i}] cannot be empty")
            if len(highlight) > 150:
                raise ValueError(
                    f"career_highlights[{i}] exceeds 150 characters ({len(highlight)} chars)"
                )
        return v

    # NOTE: Career highlights warning disabled - too noisy for CLI usage
    # @model_validator(mode="after")
    # def warn_excess_highlights(self) -> ResumeConfig:
    #     """Warn if more than 4 career highlights provided."""
    #     if len(self.career_highlights) > 4:
    #         warnings.warn(
    #             f"Research suggests maximum 4 career highlights for optimal impact. "
    #             f"You have {len(self.career_highlights)}.",
    #             UserWarning,
    #             stacklevel=2,
    #         )
    #         logger.warning(
    #             "More than 4 career highlights configured. Research suggests 4 is optimal."
    #         )
    #     return self

    @field_validator("output_dir", "work_units_dir", "positions_path", mode="before")
    @classmethod
    def expand_path(cls, v: str | Path) -> Path:
        """Expand ~ and resolve path."""
        if isinstance(v, str):
            v = Path(v)
        return v.expanduser()

    @field_validator("templates_dir", mode="before")
    @classmethod
    def expand_templates_path(cls, v: str | Path | None) -> Path | None:
        """Expand ~ and resolve templates_dir path."""
        if v is None:
            return None
        if isinstance(v, str):
            v = Path(v)
        return v.expanduser()


class ConfigSource(BaseModel):
    """Tracks the source of each config value."""

    value: str | int | float | bool | dict[str, object] | list[object] | None
    source: Literal["default", "user", "project", "env", "cli"]
    path: str | None = None  # File path if from file
