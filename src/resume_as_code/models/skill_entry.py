"""SkillEntry model for skill registry normalization."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SkillEntry(BaseModel):
    """A skill in the registry with canonical name and aliases.

    Used by SkillRegistry to normalize skill names for consistent
    resume rendering and improved ATS matching.
    """

    model_config = ConfigDict(extra="forbid")

    canonical: str = Field(description="Display name (e.g., 'Kubernetes')")
    aliases: list[str] = Field(
        default_factory=list,
        description="Alternative names (e.g., ['k8s', 'kube'])",
    )
    category: str | None = Field(
        default=None,
        description="Skill category (e.g., 'cloud', 'language', 'framework')",
    )
    onet_code: str | None = Field(
        default=None,
        description="O*NET element ID for standardization",
    )

    @field_validator("canonical", mode="before")
    @classmethod
    def validate_canonical(cls, v: str) -> str:
        """Ensure canonical name is non-empty after stripping whitespace."""
        if not isinstance(v, str):
            v = str(v)
        stripped = v.strip()
        if not stripped:
            raise ValueError("Canonical name cannot be empty")
        return stripped

    @field_validator("aliases", mode="before")
    @classmethod
    def validate_aliases(cls, v: list[str]) -> list[str]:
        """Normalize aliases to lowercase, strip whitespace, remove empty."""
        if v is None:
            return []
        result: list[str] = []
        for alias in v:
            if alias:
                stripped = alias.strip().lower()
                if stripped:
                    result.append(stripped)
        return result
