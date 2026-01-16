"""Unit tests for SkillEntry model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from resume_as_code.models.skill_entry import SkillEntry


class TestSkillEntryBasic:
    """Test basic SkillEntry creation and validation."""

    def test_skill_entry_minimal(self) -> None:
        """SkillEntry requires only canonical name."""
        entry = SkillEntry(canonical="Python")
        assert entry.canonical == "Python"
        assert entry.aliases == []
        assert entry.category is None
        assert entry.onet_code is None

    def test_skill_entry_with_all_fields(self) -> None:
        """SkillEntry accepts all optional fields."""
        entry = SkillEntry(
            canonical="Kubernetes",
            aliases=["k8s", "kube"],
            category="devops",
            onet_code="2.A.2.b",
        )
        assert entry.canonical == "Kubernetes"
        assert entry.aliases == ["k8s", "kube"]
        assert entry.category == "devops"
        assert entry.onet_code == "2.A.2.b"


class TestSkillEntryCanonicalValidation:
    """Test canonical name validation."""

    def test_empty_canonical_rejected(self) -> None:
        """Empty canonical name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SkillEntry(canonical="")
        assert "cannot be empty" in str(exc_info.value).lower()

    def test_whitespace_only_canonical_rejected(self) -> None:
        """Whitespace-only canonical name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SkillEntry(canonical="   ")
        assert "cannot be empty" in str(exc_info.value).lower()

    def test_canonical_strips_whitespace(self) -> None:
        """Canonical name is stripped of leading/trailing whitespace."""
        entry = SkillEntry(canonical="  Python  ")
        assert entry.canonical == "Python"


class TestSkillEntryAliasValidation:
    """Test alias validation and normalization."""

    def test_aliases_normalized_lowercase(self) -> None:
        """Aliases are normalized to lowercase."""
        entry = SkillEntry(
            canonical="Kubernetes",
            aliases=["K8s", "KUBE", "Kube"],
        )
        assert entry.aliases == ["k8s", "kube", "kube"]

    def test_aliases_stripped(self) -> None:
        """Aliases have whitespace stripped."""
        entry = SkillEntry(
            canonical="TypeScript",
            aliases=["  ts  ", " TS "],
        )
        assert entry.aliases == ["ts", "ts"]

    def test_empty_aliases_filtered(self) -> None:
        """Empty aliases are removed."""
        entry = SkillEntry(
            canonical="Python",
            aliases=["py", "", "  ", "python3"],
        )
        assert entry.aliases == ["py", "python3"]

    def test_aliases_default_empty_list(self) -> None:
        """Aliases default to empty list."""
        entry = SkillEntry(canonical="Python")
        assert entry.aliases == []


class TestSkillEntryExtraFields:
    """Test that extra fields are forbidden."""

    def test_extra_fields_forbidden(self) -> None:
        """Extra fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SkillEntry(canonical="Python", unknown_field="value")  # type: ignore[call-arg]
        assert "extra" in str(exc_info.value).lower()
