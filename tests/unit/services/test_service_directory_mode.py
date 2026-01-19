"""Unit tests for service directory mode operations (Story 11.2).

Tests save and remove operations for all services when using directory mode:
- CertificationService
- PublicationService
- EducationService
- BoardRoleService
- HighlightService
"""

from __future__ import annotations

from pathlib import Path

from resume_as_code.models.board_role import BoardRole
from resume_as_code.models.certification import Certification
from resume_as_code.models.education import Education
from resume_as_code.models.publication import Publication
from resume_as_code.services.board_role_service import BoardRoleService
from resume_as_code.services.certification_service import CertificationService
from resume_as_code.services.education_service import EducationService
from resume_as_code.services.highlight_service import HighlightService
from resume_as_code.services.publication_service import PublicationService


class TestCertificationServiceDirectoryMode:
    """Tests for CertificationService directory mode operations."""

    def test_save_certification_creates_file_in_directory(self, tmp_path: Path) -> None:
        """save_certification should create individual file in directory mode."""
        # Setup: Create directory structure
        cert_dir = tmp_path / "certifications"
        cert_dir.mkdir()
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        service = CertificationService(config_path=tmp_path / ".resume.yaml")
        cert = Certification(name="AWS Solutions Architect", issuer="AWS", date="2023-06")

        result = service.save_certification(cert)

        # Should return path to saved file
        assert result is not None
        assert result.exists()
        assert "cert-" in result.name
        assert "aws" in result.name.lower()

    def test_save_certification_content_is_valid(self, tmp_path: Path) -> None:
        """Saved certification file should contain valid YAML data."""
        cert_dir = tmp_path / "certifications"
        cert_dir.mkdir()
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        service = CertificationService(config_path=tmp_path / ".resume.yaml")
        cert = Certification(name="CISSP", issuer="ISC2", date="2022-11")

        result = service.save_certification(cert)

        content = result.read_text()
        assert "CISSP" in content
        assert "ISC2" in content
        assert "2022-11" in content

    def test_remove_certification_deletes_file(self, tmp_path: Path) -> None:
        """remove_certification should delete file in directory mode."""
        cert_dir = tmp_path / "certifications"
        cert_dir.mkdir()
        cert_file = cert_dir / "cert-2023-06-aws.yaml"
        cert_file.write_text('name: "AWS Cert"\nissuer: "AWS"\ndate: "2023-06"\n')
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        service = CertificationService(config_path=tmp_path / ".resume.yaml")
        result = service.remove_certification("AWS")

        assert result is True
        assert not cert_file.exists()

    def test_remove_certification_returns_false_when_not_found(self, tmp_path: Path) -> None:
        """remove_certification should return False when cert not found."""
        cert_dir = tmp_path / "certifications"
        cert_dir.mkdir()
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        service = CertificationService(config_path=tmp_path / ".resume.yaml")
        result = service.remove_certification("NonExistent")

        assert result is False


class TestPublicationServiceDirectoryMode:
    """Tests for PublicationService directory mode operations."""

    def test_save_publication_creates_file_in_directory(self, tmp_path: Path) -> None:
        """save_publication should create individual file in directory mode."""
        pub_dir = tmp_path / "publications"
        pub_dir.mkdir()
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        service = PublicationService(config_path=tmp_path / ".resume.yaml")
        pub = Publication(
            title="Zero Trust Architecture",
            type="conference",
            venue="RSA Conference",
            date="2023-06",
        )

        result = service.save_publication(pub)

        assert result is not None
        assert result.exists()
        assert "pub-" in result.name

    def test_remove_publication_deletes_file(self, tmp_path: Path) -> None:
        """remove_publication should delete file in directory mode."""
        pub_dir = tmp_path / "publications"
        pub_dir.mkdir()
        pub_file = pub_dir / "pub-2023-06-zero-trust.yaml"
        pub_file.write_text(
            'title: "Zero Trust"\ntype: conference\nvenue: "RSA"\ndate: "2023-06"\n'
        )
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        service = PublicationService(config_path=tmp_path / ".resume.yaml")
        result = service.remove_publication("Zero Trust")

        assert result is True
        assert not pub_file.exists()


class TestEducationServiceDirectoryMode:
    """Tests for EducationService directory mode operations."""

    def test_save_education_creates_file_in_directory(self, tmp_path: Path) -> None:
        """save_education should create individual file in directory mode."""
        edu_dir = tmp_path / "education"
        edu_dir.mkdir()
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        service = EducationService(config_path=tmp_path / ".resume.yaml")
        edu = Education(
            degree="Bachelor of Science in Computer Science",
            institution="MIT",
            graduation_year="2015",
        )

        result = service.save_education(edu)

        assert result is not None
        assert result.exists()
        assert "edu-" in result.name

    def test_remove_education_deletes_file(self, tmp_path: Path) -> None:
        """remove_education should delete file in directory mode."""
        edu_dir = tmp_path / "education"
        edu_dir.mkdir()
        edu_file = edu_dir / "edu-2015-mit.yaml"
        edu_file.write_text('degree: "BS Computer Science"\ninstitution: "MIT"\n')
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        service = EducationService(config_path=tmp_path / ".resume.yaml")
        result = service.remove_education("BS Computer Science")

        assert result is True
        assert not edu_file.exists()


class TestBoardRoleServiceDirectoryMode:
    """Tests for BoardRoleService directory mode operations."""

    def test_save_board_role_creates_file_in_directory(self, tmp_path: Path) -> None:
        """save_board_role should create individual file in directory mode."""
        br_dir = tmp_path / "board-roles"
        br_dir.mkdir()
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        service = BoardRoleService(config_path=tmp_path / ".resume.yaml")
        board_role = BoardRole(
            organization="CyberShield Ventures",
            role="Technical Advisor",
            type="advisory",
            start_date="2022-03",
        )

        result = service.save_board_role(board_role)

        assert result is not None
        assert result.exists()
        assert "board-" in result.name

    def test_remove_board_role_deletes_file(self, tmp_path: Path) -> None:
        """remove_board_role should delete file in directory mode."""
        br_dir = tmp_path / "board-roles"
        br_dir.mkdir()
        br_file = br_dir / "board-2022-03-cybershield.yaml"
        br_file.write_text(
            'organization: "CyberShield"\nrole: "Advisor"\ntype: advisory\nstart_date: "2022-03"\n'
        )
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        service = BoardRoleService(config_path=tmp_path / ".resume.yaml")
        result = service.remove_board_role("CyberShield")

        assert result is True
        assert not br_file.exists()


class TestHighlightServiceDirectoryMode:
    """Tests for HighlightService directory mode operations."""

    def test_save_highlight_creates_file_in_directory(self, tmp_path: Path) -> None:
        """save_highlight should create individual file in directory mode."""
        hl_dir = tmp_path / "highlights"
        hl_dir.mkdir()
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        service = HighlightService(config_path=tmp_path / ".resume.yaml")
        highlight = "Led digital transformation generating $50M revenue"

        result = service.save_highlight(highlight)

        assert result is not None
        assert result.exists()
        assert "hl-" in result.name

    def test_save_highlight_content_has_text_field(self, tmp_path: Path) -> None:
        """Saved highlight file should have 'text' field."""
        hl_dir = tmp_path / "highlights"
        hl_dir.mkdir()
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        service = HighlightService(config_path=tmp_path / ".resume.yaml")
        highlight = "Managed $50M budget"

        result = service.save_highlight(highlight)

        content = result.read_text()
        assert "text:" in content
        assert "Managed $50M budget" in content

    def test_remove_highlight_deletes_file(self, tmp_path: Path) -> None:
        """remove_highlight should delete file at given index."""
        hl_dir = tmp_path / "highlights"
        hl_dir.mkdir()
        (hl_dir / "hl-001-first.yaml").write_text('text: "First highlight"\n')
        (hl_dir / "hl-002-second.yaml").write_text('text: "Second highlight"\n')
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        service = HighlightService(config_path=tmp_path / ".resume.yaml")
        result = service.remove_highlight(0)

        assert result is True
        assert not (hl_dir / "hl-001-first.yaml").exists()
        assert (hl_dir / "hl-002-second.yaml").exists()

    def test_remove_highlight_returns_false_for_invalid_index(self, tmp_path: Path) -> None:
        """remove_highlight should return False for out-of-bounds index."""
        hl_dir = tmp_path / "highlights"
        hl_dir.mkdir()
        (hl_dir / "hl-001-test.yaml").write_text('text: "Test"\n')
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        service = HighlightService(config_path=tmp_path / ".resume.yaml")
        result = service.remove_highlight(5)

        assert result is False


class TestSourceTrackedProtocol:
    """Tests for SourceTracked protocol usage."""

    def test_loaded_items_have_source_file_attribute(self, tmp_path: Path) -> None:
        """Items loaded via directory mode should have _source_file attribute."""
        from resume_as_code.services.sharded_loader import ShardedLoader, SourceTracked

        cert_dir = tmp_path / "certifications"
        cert_dir.mkdir()
        cert_file = cert_dir / "cert-2023-06-test.yaml"
        cert_file.write_text('name: "Test Cert"\nissuer: "Test"\n')

        loader = ShardedLoader(cert_dir, Certification)
        items = loader.load_all()

        assert len(items) == 1
        # Check protocol conformance
        assert isinstance(items[0], SourceTracked)
        assert items[0]._source_file == cert_file

    def test_source_tracked_protocol_is_runtime_checkable(self, tmp_path: Path) -> None:
        """SourceTracked protocol should be runtime checkable."""
        from resume_as_code.services.sharded_loader import ShardedLoader, SourceTracked

        cert_dir = tmp_path / "certifications"
        cert_dir.mkdir()
        (cert_dir / "cert-test.yaml").write_text('name: "Cert"\n')

        loader = ShardedLoader(cert_dir, Certification)
        items = loader.load_all()

        # This should work without AttributeError
        for item in items:
            if isinstance(item, SourceTracked):
                assert item._source_file.name == "cert-test.yaml"
