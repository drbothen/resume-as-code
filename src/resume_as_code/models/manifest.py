"""Build manifest for provenance tracking."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from resume_as_code import __version__
from resume_as_code.models.errors import RenderError, ValidationError

if TYPE_CHECKING:
    from resume_as_code.models.plan import SavedPlan

# Default ranker version - matches plan.py and ranker.py
DEFAULT_RANKER_VERSION = "hybrid-rrf-v1"


class WorkUnitReference(BaseModel):
    """Reference to a Work Unit included in the build."""

    id: str
    title: str
    score: float


class BuildManifest(BaseModel):
    """Manifest documenting what went into a resume build."""

    # Version info
    version: str = "1.0.0"
    resume_as_code_version: str = Field(
        default=__version__,
        description="Version of resume-as-code used",
    )

    # Timestamps (UTC for consistency)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # JD information
    jd_hash: str = Field(..., description="SHA256 hash of JD content")
    jd_title: str | None = None
    jd_path: str | None = None

    # Work Units included
    work_units: list[WorkUnitReference] = Field(default_factory=list)
    work_unit_count: int = 0

    # Build settings
    template: str = "modern"
    output_formats: list[str] = Field(default_factory=lambda: ["pdf", "docx"])

    # Scoring configuration
    ranker_version: str = DEFAULT_RANKER_VERSION
    top_k: int = 8

    # Content hash for determinism
    content_hash: str = Field(
        default="",
        description="Hash of inputs for reproducibility check",
    )

    @classmethod
    def from_build(
        cls,
        plan: SavedPlan,
        work_units: list[dict[str, Any]],
        template: str,
        output_formats: list[str],
    ) -> BuildManifest:
        """Create manifest from build parameters.

        Args:
            plan: The SavedPlan used for the build.
            work_units: Work Units included in the build.
            template: Template name used.
            output_formats: Formats generated.

        Returns:
            BuildManifest instance with computed content hash.
        """
        # Build work unit references with scores from plan
        plan_scores = {wu.id: wu.score for wu in plan.selected_work_units}

        wu_refs = [
            WorkUnitReference(
                id=str(wu.get("id", "")),
                title=str(wu.get("title", "")),
                score=plan_scores.get(str(wu.get("id", "")), 0.0),
            )
            for wu in work_units
        ]

        manifest = cls(
            jd_hash=plan.jd_hash,
            jd_title=plan.jd_title,
            jd_path=plan.jd_path,
            work_units=wu_refs,
            work_unit_count=len(wu_refs),
            template=template,
            output_formats=output_formats,
            ranker_version=plan.ranker_version,
            top_k=plan.top_k,
        )

        # Compute content hash
        manifest.content_hash = manifest._compute_content_hash()

        return manifest

    def _compute_content_hash(self) -> str:
        """Compute hash of content-affecting inputs.

        Returns:
            16-character hex hash of inputs that affect output content.
        """
        # Hash inputs that affect output content (excluding timestamps)
        # Include ranker_version since different algorithms may select differently
        content_parts = [
            self.jd_hash,
            self.template,
            ",".join(sorted(wu.id for wu in self.work_units)),
            str(self.top_k),
            self.ranker_version,
        ]

        combined = "|".join(content_parts)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def save(self, path: Path) -> None:
        """Save manifest to YAML file with human-readable header.

        Args:
            path: Path to save the manifest file.

        Raises:
            RenderError: If the file cannot be written.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        data = self.model_dump(mode="json")

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Resume Build Manifest\n")
                f.write(f"# Generated: {self.created_at.isoformat()}\n")
                f.write("# This file documents what went into the resume build\n\n")
                yaml.dump(data, f)
        except OSError as e:
            raise RenderError(
                message=f"Failed to save manifest: {e}",
                suggestion=f"Check that {path.parent} exists and is writable",
            ) from e

    @classmethod
    def load(cls, path: Path) -> BuildManifest:
        """Load manifest from YAML file.

        Args:
            path: Path to the manifest file.

        Returns:
            BuildManifest loaded from the file.

        Raises:
            ValidationError: If the file cannot be read or contains invalid data.
        """
        yaml = YAML()
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.load(f)
        except OSError as e:
            raise ValidationError(
                message=f"Failed to read manifest: {e}",
                path=str(path),
                suggestion="Check that the file exists and is readable",
            ) from e
        except YAMLError as e:
            raise ValidationError(
                message=f"Invalid YAML in manifest file: {e}",
                path=str(path),
                suggestion="Check the manifest file for syntax errors",
            ) from e

        if data is None:
            raise ValidationError(
                message="Manifest file is empty",
                path=str(path),
                suggestion="Regenerate the manifest by running a build",
            )

        return cls.model_validate(data)

    def diff(self, other: BuildManifest) -> dict[str, tuple[str, str]]:
        """Compare this manifest with another and return differences.

        Args:
            other: Another BuildManifest to compare against.

        Returns:
            Dictionary of field names to (self_value, other_value) tuples
            for fields that differ. Excludes timestamps.
        """
        differences: dict[str, tuple[str, str]] = {}

        # Compare content-affecting fields
        if self.jd_hash != other.jd_hash:
            differences["jd_hash"] = (self.jd_hash, other.jd_hash)

        if self.template != other.template:
            differences["template"] = (self.template, other.template)

        if self.top_k != other.top_k:
            differences["top_k"] = (str(self.top_k), str(other.top_k))

        # Compare Work Unit IDs
        self_wu_ids = {wu.id for wu in self.work_units}
        other_wu_ids = {wu.id for wu in other.work_units}

        if self_wu_ids != other_wu_ids:
            only_self = self_wu_ids - other_wu_ids
            only_other = other_wu_ids - self_wu_ids
            differences["work_units"] = (
                f"unique: {sorted(only_self)}" if only_self else "none",
                f"unique: {sorted(only_other)}" if only_other else "none",
            )

        if self.content_hash != other.content_hash:
            differences["content_hash"] = (self.content_hash, other.content_hash)

        return differences

    def is_equivalent(self, other: BuildManifest) -> bool:
        """Check if this manifest is content-equivalent to another.

        Two manifests are equivalent if they would produce the same output,
        ignoring timestamps.

        Args:
            other: Another BuildManifest to compare against.

        Returns:
            True if the manifests are content-equivalent.
        """
        return self.content_hash == other.content_hash
