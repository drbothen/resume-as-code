"""Tests for Evidence model enhancements (Story 7.7).

Tests new evidence types: NarrativeEvidence, LinkEvidence
Tests enhanced ArtifactEvidence with optional URL and hash support
"""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from resume_as_code.models.work_unit import (
    ArtifactEvidence,
    Evidence,
    EvidenceType,
    LinkEvidence,
    NarrativeEvidence,
)


class TestNarrativeEvidence:
    """Tests for NarrativeEvidence model."""

    def test_valid_narrative_minimal(self) -> None:
        """Narrative evidence with only description."""
        evidence = NarrativeEvidence(
            description="Received positive feedback from VP of Engineering"
        )
        assert evidence.type == "narrative"
        assert evidence.source is None

    def test_valid_narrative_full(self) -> None:
        """Narrative evidence with all fields."""
        evidence = NarrativeEvidence(
            description="Led team to achieve 99.9% uptime for Q4 2024",
            source="Quarterly review",
            date_recorded="2024-12-15",
        )
        assert evidence.source == "Quarterly review"
        assert evidence.date_recorded is not None

    def test_narrative_requires_description(self) -> None:
        """Description is required for narrative evidence."""
        with pytest.raises(ValidationError, match="description"):
            NarrativeEvidence()  # type: ignore[call-arg]

    def test_narrative_description_min_length(self) -> None:
        """Description must be at least 10 characters."""
        with pytest.raises(ValidationError, match="String should have at least 10"):
            NarrativeEvidence(description="Too short")

    def test_narrative_type_literal(self) -> None:
        """Type field should always be 'narrative'."""
        evidence = NarrativeEvidence(description="Internal achievement documented")
        assert evidence.type == "narrative"

    def test_narrative_rejects_extra_fields(self) -> None:
        """NarrativeEvidence should reject extra fields."""
        with pytest.raises(ValidationError, match="extra_forbidden"):
            NarrativeEvidence(
                description="Valid description here",
                unknown_field="not allowed",  # type: ignore[call-arg]
            )


class TestLinkEvidence:
    """Tests for LinkEvidence model."""

    def test_valid_link_minimal(self) -> None:
        """Link evidence with only URL."""
        evidence = LinkEvidence(url="https://example.com/article")
        assert evidence.type == "link"
        assert evidence.title is None

    def test_valid_link_full(self) -> None:
        """Link evidence with all fields."""
        evidence = LinkEvidence(
            url="https://medium.com/@user/article-title",
            title="My Published Article",
            description="Article about microservices patterns",
        )
        assert evidence.title == "My Published Article"

    def test_link_requires_url(self) -> None:
        """URL is required for link evidence."""
        with pytest.raises(ValidationError, match="url"):
            LinkEvidence()  # type: ignore[call-arg]

    def test_link_invalid_url_raises_error(self) -> None:
        """Invalid URL should raise ValidationError."""
        with pytest.raises(ValidationError):
            LinkEvidence(url="not-a-valid-url")

    def test_link_type_literal(self) -> None:
        """Type field should always be 'link'."""
        evidence = LinkEvidence(url="https://example.com")
        assert evidence.type == "link"

    def test_link_rejects_extra_fields(self) -> None:
        """LinkEvidence should reject extra fields."""
        with pytest.raises(ValidationError, match="extra_forbidden"):
            LinkEvidence(
                url="https://example.com",
                unknown_field="not allowed",  # type: ignore[call-arg]
            )


class TestArtifactEvidenceEnhanced:
    """Tests for enhanced ArtifactEvidence model."""

    def test_artifact_with_url_only(self) -> None:
        """Artifact evidence with URL only (backward compatible)."""
        evidence = ArtifactEvidence(url="https://pypi.org/project/mypackage")
        assert evidence.type == "artifact"
        assert evidence.sha256 is None

    def test_artifact_with_local_path_only(self) -> None:
        """Artifact evidence with local path only."""
        evidence = ArtifactEvidence(
            local_path="artifacts/report.pdf",
            artifact_type="pdf",
        )
        assert evidence.local_path == "artifacts/report.pdf"
        assert evidence.url is None

    def test_artifact_with_sha256_only(self) -> None:
        """Artifact evidence with SHA-256 hash only."""
        sha = "a" * 64  # Valid SHA-256 hex string
        evidence = ArtifactEvidence(
            sha256=sha,
            description="Deployment package",
        )
        assert evidence.sha256 == sha

    def test_artifact_with_all_references(self) -> None:
        """Artifact evidence with URL, path, and hash."""
        evidence = ArtifactEvidence(
            url="https://releases.example.com/v1.0.0.tar.gz",
            local_path="releases/v1.0.0.tar.gz",
            sha256="b" * 64,
            artifact_type="tarball",
        )
        assert evidence.url is not None
        assert evidence.local_path is not None

    def test_artifact_requires_at_least_one_reference(self) -> None:
        """Must provide at least one of url, local_path, or sha256."""
        with pytest.raises(ValidationError, match="at least one"):
            ArtifactEvidence(description="Missing all references")

    def test_artifact_sha256_format_validation(self) -> None:
        """SHA-256 must be valid 64-character hex string."""
        with pytest.raises(ValidationError, match="String should match pattern"):
            ArtifactEvidence(sha256="invalid-hash")

        with pytest.raises(ValidationError, match="String should match pattern"):
            ArtifactEvidence(sha256="abc123")  # Too short

    def test_artifact_sha256_uppercase_valid(self) -> None:
        """SHA-256 can be uppercase hex."""
        sha = "A" * 64
        evidence = ArtifactEvidence(sha256=sha)
        assert evidence.sha256 == sha

    def test_artifact_local_path_rejects_unix_absolute(self) -> None:
        """Unix absolute paths starting with / should be rejected."""
        with pytest.raises(ValidationError, match="relative to project root"):
            ArtifactEvidence(local_path="/etc/passwd")

    def test_artifact_local_path_rejects_home_directory(self) -> None:
        """Home directory paths starting with ~ should be rejected."""
        with pytest.raises(ValidationError, match="relative to project root"):
            ArtifactEvidence(local_path="~/Documents/artifact.pdf")

    def test_artifact_local_path_rejects_windows_absolute(self) -> None:
        """Windows absolute paths with drive letters should be rejected."""
        with pytest.raises(ValidationError, match="relative to project root"):
            ArtifactEvidence(local_path="C:\\Users\\artifact.pdf")

        with pytest.raises(ValidationError, match="relative to project root"):
            ArtifactEvidence(local_path="D:/Documents/artifact.pdf")

    def test_artifact_local_path_accepts_relative(self) -> None:
        """Relative paths should be accepted."""
        evidence = ArtifactEvidence(local_path="artifacts/report.pdf")
        assert evidence.local_path == "artifacts/report.pdf"

        # Paths with .. are allowed (caller responsibility to resolve)
        evidence2 = ArtifactEvidence(local_path="../sibling/file.txt")
        assert evidence2.local_path == "../sibling/file.txt"

        # Current directory paths
        evidence3 = ArtifactEvidence(local_path="./file.txt")
        assert evidence3.local_path == "./file.txt"


class TestEvidenceDiscriminatedUnion:
    """Tests for Evidence discriminated union."""

    def test_narrative_in_union(self) -> None:
        """Narrative evidence works in union."""
        adapter = TypeAdapter(Evidence)
        data = {"type": "narrative", "description": "Internal achievement documented"}
        evidence = adapter.validate_python(data)
        assert isinstance(evidence, NarrativeEvidence)

    def test_link_in_union(self) -> None:
        """Link evidence works in union."""
        adapter = TypeAdapter(Evidence)
        data = {"type": "link", "url": "https://example.com"}
        evidence = adapter.validate_python(data)
        assert isinstance(evidence, LinkEvidence)

    def test_artifact_without_url_in_union(self) -> None:
        """Enhanced artifact evidence works in union."""
        adapter = TypeAdapter(Evidence)
        data = {
            "type": "artifact",
            "local_path": "artifacts/build.log",
            "description": "Build log",
        }
        evidence = adapter.validate_python(data)
        assert isinstance(evidence, ArtifactEvidence)
        assert evidence.url is None

    def test_all_evidence_types_in_union(self) -> None:
        """All evidence types should be parseable via the union."""
        adapter = TypeAdapter(Evidence)

        # git_repo
        git = adapter.validate_python({"type": "git_repo", "url": "https://github.com/org/repo"})
        assert git.type == "git_repo"

        # metrics
        metrics = adapter.validate_python({"type": "metrics", "url": "https://grafana.example.com"})
        assert metrics.type == "metrics"

        # document
        doc = adapter.validate_python({"type": "document", "url": "https://docs.example.com"})
        assert doc.type == "document"

        # artifact
        artifact = adapter.validate_python({"type": "artifact", "local_path": "file.txt"})
        assert artifact.type == "artifact"

        # link
        link = adapter.validate_python({"type": "link", "url": "https://example.com"})
        assert link.type == "link"

        # narrative
        narrative = adapter.validate_python(
            {"type": "narrative", "description": "Internal achievement"}
        )
        assert narrative.type == "narrative"

        # other
        other = adapter.validate_python({"type": "other", "url": "https://example.com/other"})
        assert other.type == "other"


class TestEvidenceTypeEnum:
    """Tests for EvidenceType enum values."""

    def test_evidence_type_includes_link(self) -> None:
        """EvidenceType enum should include LINK."""
        assert EvidenceType.LINK.value == "link"

    def test_evidence_type_includes_narrative(self) -> None:
        """EvidenceType enum should include NARRATIVE."""
        assert EvidenceType.NARRATIVE.value == "narrative"

    def test_all_evidence_types_defined(self) -> None:
        """All required evidence types should be defined."""
        expected = {"git_repo", "metrics", "document", "artifact", "link", "narrative", "other"}
        actual = {e.value for e in EvidenceType}
        assert expected == actual


class TestEvidenceIntegrationWithWorkUnit:
    """Integration tests for Evidence types with WorkUnit model."""

    def test_work_unit_with_narrative_evidence(self) -> None:
        """WorkUnit accepts narrative evidence."""
        from resume_as_code.models.work_unit import Outcome, Problem, WorkUnit, WorkUnitArchetype

        wu = WorkUnit(
            id="wu-2024-03-15-internal-achievement",
            title="Led internal cost optimization initiative",
            problem=Problem(statement="Cloud costs exceeded budget by 40%"),
            actions=["Analyzed costs", "Implemented savings"],
            outcome=Outcome(result="Reduced costs by 35%"),
            archetype=WorkUnitArchetype.OPTIMIZATION,
            evidence=[
                NarrativeEvidence(
                    description="Recognized in company all-hands for cost savings",
                    source="CEO presentation Q3 2024",
                )
            ],
        )
        assert len(wu.evidence) == 1
        assert wu.evidence[0].type == "narrative"

    def test_work_unit_with_link_evidence(self) -> None:
        """WorkUnit accepts link evidence."""
        from resume_as_code.models.work_unit import Outcome, Problem, WorkUnit, WorkUnitArchetype

        wu = WorkUnit(
            id="wu-2024-03-15-blog-post",
            title="Published technical blog post on microservices",
            problem=Problem(statement="Team needed microservices guidance"),
            actions=["Researched patterns", "Wrote blog post"],
            outcome=Outcome(result="Post read by 10K+ developers"),
            archetype=WorkUnitArchetype.STRATEGIC,
            evidence=[
                LinkEvidence(
                    url="https://medium.com/@user/microservices-patterns",
                    title="Microservices Patterns Guide",
                )
            ],
        )
        assert len(wu.evidence) == 1
        assert wu.evidence[0].type == "link"

    def test_work_unit_with_artifact_local_path(self) -> None:
        """WorkUnit accepts artifact evidence with local path only."""
        from resume_as_code.models.work_unit import Outcome, Problem, WorkUnit, WorkUnitArchetype

        wu = WorkUnit(
            id="wu-2024-03-15-local-artifact",
            title="Created internal deployment package",
            problem=Problem(statement="Deployment process was manual"),
            actions=["Built automation scripts"],
            outcome=Outcome(result="Automated 80% of deployments"),
            archetype=WorkUnitArchetype.GREENFIELD,
            evidence=[
                ArtifactEvidence(
                    local_path="artifacts/deploy-package.tar.gz",
                    sha256="a" * 64,
                    artifact_type="tarball",
                )
            ],
        )
        assert len(wu.evidence) == 1
        assert wu.evidence[0].url is None
        assert wu.evidence[0].local_path == "artifacts/deploy-package.tar.gz"

    def test_work_unit_with_mixed_evidence_types(self) -> None:
        """WorkUnit accepts multiple evidence types."""
        from resume_as_code.models.work_unit import (
            GitRepoEvidence,
            Outcome,
            Problem,
            WorkUnit,
            WorkUnitArchetype,
        )

        wu = WorkUnit(
            id="wu-2024-03-15-mixed-evidence",
            title="Open source contribution with recognition",
            problem=Problem(statement="Project needed security improvements"),
            actions=["Implemented security fixes", "Received recognition"],
            outcome=Outcome(result="Security vulnerabilities reduced by 90%"),
            archetype=WorkUnitArchetype.OPTIMIZATION,
            evidence=[
                GitRepoEvidence(url="https://github.com/org/project"),
                NarrativeEvidence(description="Featured in project newsletter"),
                LinkEvidence(url="https://blog.example.com/security-update"),
                ArtifactEvidence(sha256="b" * 64, description="Security audit report"),
            ],
        )
        assert len(wu.evidence) == 4
        evidence_types = [e.type for e in wu.evidence]
        assert evidence_types == ["git_repo", "narrative", "link", "artifact"]


class TestBackwardCompatibility:
    """Tests ensuring backward compatibility with existing evidence usage."""

    def test_artifact_evidence_with_url_only_still_works(self) -> None:
        """Existing code using ArtifactEvidence(url=...) should still work."""
        evidence = ArtifactEvidence(url="https://pypi.org/project/mypackage/1.0.0")
        assert evidence.url is not None
        assert evidence.local_path is None
        assert evidence.sha256 is None

    def test_existing_yaml_artifact_structure_validates(self) -> None:
        """YAML structure with url-only artifact should validate."""
        adapter = TypeAdapter(Evidence)
        data = {
            "type": "artifact",
            "url": "https://pypi.org/project/mypackage",
            "artifact_type": "wheel",
            "description": "Python package",
        }
        evidence = adapter.validate_python(data)
        assert isinstance(evidence, ArtifactEvidence)
        assert evidence.url is not None
