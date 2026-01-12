"""Tests for manifest and provenance."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from resume_as_code import __version__
from resume_as_code.models.errors import RenderError, ValidationError
from resume_as_code.models.manifest import BuildManifest, WorkUnitReference
from resume_as_code.providers.manifest import ManifestProvider


@pytest.fixture
def sample_plan() -> MagicMock:
    """Create sample plan for testing."""
    plan = MagicMock()
    plan.jd_hash = "abc123def456"
    plan.jd_title = "Senior Engineer"
    plan.jd_path = "job.txt"
    plan.ranker_version = "hybrid-rrf-v1"
    plan.top_k = 8
    plan.selected_work_units = [
        MagicMock(id="wu-1", score=0.9),
        MagicMock(id="wu-2", score=0.8),
    ]
    return plan


class TestWorkUnitReference:
    """Tests for WorkUnitReference model."""

    def test_creates_reference(self) -> None:
        """Should create work unit reference."""
        ref = WorkUnitReference(id="wu-1", title="Test Unit", score=0.85)

        assert ref.id == "wu-1"
        assert ref.title == "Test Unit"
        assert ref.score == 0.85


class TestBuildManifest:
    """Tests for BuildManifest model."""

    def test_creates_from_build(self, sample_plan: MagicMock) -> None:
        """Should create manifest from build parameters."""
        work_units = [
            {"id": "wu-1", "title": "Work Unit 1"},
            {"id": "wu-2", "title": "Work Unit 2"},
        ]

        manifest = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf", "docx"],
        )

        assert manifest.jd_hash == "abc123def456"
        assert manifest.jd_title == "Senior Engineer"
        assert manifest.work_unit_count == 2
        assert len(manifest.work_units) == 2
        assert manifest.template == "modern"
        assert manifest.output_formats == ["pdf", "docx"]

    def test_content_hash_deterministic(self, sample_plan: MagicMock) -> None:
        """Same inputs should produce same content hash."""
        work_units = [{"id": "wu-1", "title": "Work Unit 1"}]

        manifest1 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )

        manifest2 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )

        assert manifest1.content_hash == manifest2.content_hash

    def test_content_hash_differs_for_different_inputs(self, sample_plan: MagicMock) -> None:
        """Different inputs should produce different content hash."""
        work_units1 = [{"id": "wu-1", "title": "Work Unit 1"}]
        work_units2 = [{"id": "wu-2", "title": "Work Unit 2"}]

        manifest1 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units1,
            template="modern",
            output_formats=["pdf"],
        )

        manifest2 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units2,
            template="modern",
            output_formats=["pdf"],
        )

        assert manifest1.content_hash != manifest2.content_hash

    def test_work_unit_scores_from_plan(self, sample_plan: MagicMock) -> None:
        """Work unit references should include scores from plan."""
        work_units = [
            {"id": "wu-1", "title": "Work Unit 1"},
            {"id": "wu-2", "title": "Work Unit 2"},
        ]

        manifest = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )

        assert manifest.work_units[0].score == 0.9
        assert manifest.work_units[1].score == 0.8

    def test_save_and_load(self, sample_plan: MagicMock, tmp_path: Path) -> None:
        """Should save and load manifest preserving data."""
        work_units = [{"id": "wu-1", "title": "Work Unit 1"}]
        manifest = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )

        path = tmp_path / "manifest.yaml"
        manifest.save(path)

        loaded = BuildManifest.load(path)
        assert loaded.jd_hash == manifest.jd_hash
        assert loaded.content_hash == manifest.content_hash
        assert loaded.work_unit_count == manifest.work_unit_count
        assert loaded.template == manifest.template

    def test_save_creates_readable_yaml(self, sample_plan: MagicMock, tmp_path: Path) -> None:
        """Saved manifest should be human-readable with header comments."""
        work_units = [{"id": "wu-1", "title": "Test"}]
        manifest = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )

        path = tmp_path / "manifest.yaml"
        manifest.save(path)

        content = path.read_text()
        assert "# Resume Build Manifest" in content
        assert "# Generated:" in content
        assert "jd_hash" in content

    def test_version_defaults(self) -> None:
        """Manifest should have sensible version defaults."""
        manifest = BuildManifest(
            jd_hash="test123",
            work_units=[],
            work_unit_count=0,
        )

        assert manifest.version == "1.0.0"
        assert manifest.resume_as_code_version == __version__

    def test_content_hash_includes_ranker_version(self, sample_plan: MagicMock) -> None:
        """Content hash should change if ranker version differs."""
        work_units = [{"id": "wu-1", "title": "Work Unit 1"}]

        manifest1 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )

        # Change ranker version
        sample_plan.ranker_version = "different-ranker-v2"
        manifest2 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )

        assert manifest1.content_hash != manifest2.content_hash

    def test_created_at_has_timezone(self) -> None:
        """Timestamp should be timezone-aware (UTC)."""
        manifest = BuildManifest(
            jd_hash="test123",
            work_units=[],
            work_unit_count=0,
        )

        assert manifest.created_at.tzinfo is not None


class TestManifestComparison:
    """Tests for manifest comparison (AC: #3, #5)."""

    def test_diff_returns_empty_for_identical_manifests(self, sample_plan: MagicMock) -> None:
        """Identical manifests should have no differences."""
        work_units = [{"id": "wu-1", "title": "Work Unit 1"}]

        manifest1 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )
        manifest2 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )

        diff = manifest1.diff(manifest2)
        assert len(diff) == 0

    def test_diff_detects_jd_hash_difference(self, sample_plan: MagicMock) -> None:
        """Should detect when JD hash differs."""
        work_units = [{"id": "wu-1", "title": "Test"}]

        manifest1 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )

        # Change JD hash
        sample_plan.jd_hash = "different_hash"
        manifest2 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )

        diff = manifest1.diff(manifest2)
        assert "jd_hash" in diff
        assert diff["jd_hash"][0] == "abc123def456"
        assert diff["jd_hash"][1] == "different_hash"

    def test_diff_detects_work_unit_differences(self, sample_plan: MagicMock) -> None:
        """Should detect when Work Units differ (AC: #3)."""
        manifest1 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=[{"id": "wu-1", "title": "Unit 1"}],
            template="modern",
            output_formats=["pdf"],
        )
        manifest2 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=[{"id": "wu-2", "title": "Unit 2"}],
            template="modern",
            output_formats=["pdf"],
        )

        diff = manifest1.diff(manifest2)
        assert "work_units" in diff
        assert "wu-1" in diff["work_units"][0]
        assert "wu-2" in diff["work_units"][1]

    def test_is_equivalent_for_same_inputs(self, sample_plan: MagicMock) -> None:
        """Same inputs should produce equivalent manifests (AC: #5)."""
        work_units = [{"id": "wu-1", "title": "Test"}]

        manifest1 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )
        manifest2 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )

        assert manifest1.is_equivalent(manifest2)

    def test_not_equivalent_for_different_inputs(self, sample_plan: MagicMock) -> None:
        """Different inputs should not be equivalent."""
        manifest1 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=[{"id": "wu-1", "title": "Unit 1"}],
            template="modern",
            output_formats=["pdf"],
        )
        manifest2 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=[{"id": "wu-2", "title": "Unit 2"}],
            template="modern",
            output_formats=["pdf"],
        )

        assert not manifest1.is_equivalent(manifest2)


class TestManifestProvider:
    """Tests for ManifestProvider."""

    def test_generates_manifest(self, sample_plan: MagicMock, tmp_path: Path) -> None:
        """Should generate manifest file."""
        provider = ManifestProvider()
        work_units = [{"id": "wu-1", "title": "Test"}]

        path = provider.generate(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
            output_path=tmp_path / "manifest.yaml",
        )

        assert path.exists()
        content = path.read_text()
        assert "jd_hash" in content
        assert "wu-1" in content

    def test_returns_path_to_generated_file(self, sample_plan: MagicMock, tmp_path: Path) -> None:
        """Should return path to the generated file."""
        provider = ManifestProvider()
        expected_path = tmp_path / "manifest.yaml"

        result = provider.generate(
            plan=sample_plan,
            work_units=[{"id": "wu-1", "title": "Test"}],
            template="modern",
            output_formats=["pdf"],
            output_path=expected_path,
        )

        assert result == expected_path


class TestManifestErrorHandling:
    """Tests for error handling in save/load operations."""

    def test_load_nonexistent_file_raises_validation_error(self, tmp_path: Path) -> None:
        """Should raise ValidationError when loading nonexistent file."""
        nonexistent = tmp_path / "does_not_exist.yaml"

        with pytest.raises(ValidationError) as exc_info:
            BuildManifest.load(nonexistent)

        assert "Failed to read manifest" in str(exc_info.value)

    def test_load_empty_file_raises_validation_error(self, tmp_path: Path) -> None:
        """Should raise ValidationError when loading empty file."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")

        with pytest.raises(ValidationError) as exc_info:
            BuildManifest.load(empty_file)

        assert "empty" in str(exc_info.value).lower()

    def test_load_invalid_yaml_raises_validation_error(self, tmp_path: Path) -> None:
        """Should raise ValidationError when loading invalid YAML."""
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text("{ invalid yaml: [")

        with pytest.raises(ValidationError) as exc_info:
            BuildManifest.load(invalid_file)

        assert "Invalid YAML" in str(exc_info.value)

    def test_save_to_readonly_raises_render_error(self, tmp_path: Path) -> None:
        """Should raise RenderError when saving to unwritable location."""
        manifest = BuildManifest(
            jd_hash="test123",
            work_units=[],
            work_unit_count=0,
        )

        # Try to save to a directory (which will fail)
        with pytest.raises(RenderError) as exc_info:
            manifest.save(tmp_path)  # tmp_path is a directory, not a file

        assert "Failed to save manifest" in str(exc_info.value)
