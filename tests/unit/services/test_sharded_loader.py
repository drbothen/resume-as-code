"""Tests for ShardedLoader service (Story 11.2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_as_code.models.certification import Certification
from resume_as_code.services.sharded_loader import ShardedLoader


class TestShardedLoaderLoadAll:
    """Test ShardedLoader.load_all() method."""

    def test_load_empty_directory(self, tmp_path: Path) -> None:
        """load_all should return empty list for empty directory."""
        loader = ShardedLoader(tmp_path, Certification)
        items = loader.load_all()
        assert items == []

    def test_load_nonexistent_directory(self, tmp_path: Path) -> None:
        """load_all should return empty list for nonexistent directory."""
        loader = ShardedLoader(tmp_path / "nonexistent", Certification)
        items = loader.load_all()
        assert items == []

    def test_load_single_file(self, tmp_path: Path) -> None:
        """load_all should load a single YAML file."""
        cert_file = tmp_path / "cert-2023-06-aws.yaml"
        cert_file.write_text("""
name: "AWS Solutions Architect"
issuer: "Amazon Web Services"
date: "2023-06"
""")
        loader = ShardedLoader(tmp_path, Certification)
        items = loader.load_all()
        assert len(items) == 1
        assert items[0].name == "AWS Solutions Architect"
        assert items[0].issuer == "Amazon Web Services"

    def test_load_multiple_files_sorted(self, tmp_path: Path) -> None:
        """load_all should load files sorted alphabetically."""
        (tmp_path / "cert-2023-06-zulu.yaml").write_text('name: "Zulu Cert"\n')
        (tmp_path / "cert-2022-01-alpha.yaml").write_text('name: "Alpha Cert"\n')
        (tmp_path / "cert-2023-01-beta.yaml").write_text('name: "Beta Cert"\n')

        loader = ShardedLoader(tmp_path, Certification)
        items = loader.load_all()

        assert len(items) == 3
        assert items[0].name == "Alpha Cert"
        assert items[1].name == "Beta Cert"
        assert items[2].name == "Zulu Cert"

    def test_skip_hidden_files(self, tmp_path: Path) -> None:
        """load_all should skip hidden files (starting with dot)."""
        (tmp_path / ".hidden.yaml").write_text('name: "Hidden Cert"\n')
        (tmp_path / "cert-2023-06-visible.yaml").write_text('name: "Visible Cert"\n')

        loader = ShardedLoader(tmp_path, Certification)
        items = loader.load_all()

        assert len(items) == 1
        assert items[0].name == "Visible Cert"

    def test_skip_non_yaml_files(self, tmp_path: Path) -> None:
        """load_all should skip non-YAML files."""
        (tmp_path / "cert.txt").write_text('name: "Not YAML"\n')
        (tmp_path / "cert-2023-06-valid.yaml").write_text('name: "Valid Cert"\n')

        loader = ShardedLoader(tmp_path, Certification)
        items = loader.load_all()

        assert len(items) == 1
        assert items[0].name == "Valid Cert"

    def test_invalid_yaml_raises_error(self, tmp_path: Path) -> None:
        """load_all should raise ValidationError for invalid YAML."""
        (tmp_path / "cert-invalid.yaml").write_text("name: 123\n")  # name must be string

        loader = ShardedLoader(tmp_path, Certification)
        # Certification requires name to be string, but 123 is int
        # Actually, Pydantic coerces 123 to "123", so let's use a truly invalid case
        (tmp_path / "cert-invalid.yaml").write_text("invalid: [unclosed\n")

        from resume_as_code.models.errors import ValidationError

        with pytest.raises(ValidationError):
            loader.load_all()

    def test_tracks_source_file(self, tmp_path: Path) -> None:
        """load_all should track source file path on each item."""
        cert_file = tmp_path / "cert-2023-06-aws.yaml"
        cert_file.write_text('name: "AWS Cert"\n')

        loader = ShardedLoader(tmp_path, Certification)
        items = loader.load_all()

        assert len(items) == 1
        assert items[0]._source_file == cert_file


class TestShardedLoaderSave:
    """Test ShardedLoader.save() method."""

    def test_save_new_item(self, tmp_path: Path) -> None:
        """save should write new item to directory."""
        loader = ShardedLoader(tmp_path, Certification)
        cert = Certification(name="New Cert", issuer="Test Issuer", date="2023-06")

        saved_path = loader.save(cert, "cert-2023-06-new-cert")
        assert saved_path.exists()
        assert saved_path.name == "cert-2023-06-new-cert.yaml"

        # Verify content
        content = saved_path.read_text()
        assert "New Cert" in content
        assert "Test Issuer" in content

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        """save should create directory if it doesn't exist."""
        dir_path = tmp_path / "new_dir"
        assert not dir_path.exists()

        loader = ShardedLoader(dir_path, Certification)
        cert = Certification(name="New Cert")

        loader.save(cert, "cert-2023-06-new-cert")
        assert dir_path.exists()

    def test_save_overwrites_existing(self, tmp_path: Path) -> None:
        """save should overwrite existing file with same ID."""
        loader = ShardedLoader(tmp_path, Certification)
        cert1 = Certification(name="Original Cert")
        cert2 = Certification(name="Updated Cert")

        loader.save(cert1, "cert-id")
        loader.save(cert2, "cert-id")

        items = loader.load_all()
        assert len(items) == 1
        assert items[0].name == "Updated Cert"


class TestShardedLoaderRemove:
    """Test ShardedLoader.remove() method."""

    def test_remove_existing_item(self, tmp_path: Path) -> None:
        """remove should delete file for existing item."""
        cert_file = tmp_path / "cert-2023-06-test.yaml"
        cert_file.write_text('name: "Test Cert"\n')

        loader = ShardedLoader(tmp_path, Certification)
        result = loader.remove("cert-2023-06-test")

        assert result is True
        assert not cert_file.exists()

    def test_remove_nonexistent_item(self, tmp_path: Path) -> None:
        """remove should return False for nonexistent item."""
        loader = ShardedLoader(tmp_path, Certification)
        result = loader.remove("nonexistent-id")

        assert result is False


class TestShardedLoaderIdGeneration:
    """Test ShardedLoader ID generation helpers."""

    def test_generate_certification_id(self, tmp_path: Path) -> None:
        """generate_id should create cert-YYYY-MM-slug for certifications."""
        loader = ShardedLoader(tmp_path, Certification)
        cert = Certification(name="AWS Solutions Architect", date="2023-06")

        generated_id = loader.generate_id(cert)
        assert generated_id == "cert-2023-06-aws-solutions-architect"

    def test_generate_certification_id_without_date(self, tmp_path: Path) -> None:
        """generate_id should handle certifications without date."""
        loader = ShardedLoader(tmp_path, Certification)
        cert = Certification(name="Legacy Cert")

        generated_id = loader.generate_id(cert)
        # Should still produce a usable ID
        assert generated_id.startswith("cert-")
        assert "legacy-cert" in generated_id
