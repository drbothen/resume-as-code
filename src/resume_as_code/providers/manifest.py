"""Manifest provider for build provenance."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from resume_as_code.models.manifest import BuildManifest

if TYPE_CHECKING:
    from resume_as_code.models.plan import SavedPlan


class ManifestProvider:
    """Provider for generating build manifests."""

    def generate(
        self,
        plan: SavedPlan,
        work_units: list[dict[str, Any]],
        template: str,
        output_formats: list[str],
        output_path: Path,
    ) -> Path:
        """Generate and save manifest.

        Args:
            plan: The SavedPlan used for the build.
            work_units: Work Units included in the build.
            template: Template name used.
            output_formats: Formats generated.
            output_path: Path to save manifest.

        Returns:
            Path to generated manifest file.
        """
        manifest = BuildManifest.from_build(
            plan=plan,
            work_units=work_units,
            template=template,
            output_formats=output_formats,
        )

        manifest.save(output_path)
        return output_path
