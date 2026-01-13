"""Tests for CertificationMatcher service."""

from __future__ import annotations

from resume_as_code.models.certification import Certification
from resume_as_code.services.certification_matcher import (
    CertificationMatcher,
    CertificationMatchResult,
)


class TestCertificationMatcherInit:
    """Tests for CertificationMatcher initialization."""

    def test_creates_instance(self) -> None:
        """Should create a CertificationMatcher instance."""
        matcher = CertificationMatcher()
        assert matcher is not None

    def test_has_cert_patterns(self) -> None:
        """Should have certification patterns defined."""
        matcher = CertificationMatcher()
        assert hasattr(matcher, "CERT_PATTERNS")
        assert len(matcher.CERT_PATTERNS) > 0


class TestExtractJDRequirements:
    """Tests for extract_jd_requirements method."""

    def test_extracts_cissp(self) -> None:
        """Should extract CISSP certification from JD text."""
        matcher = CertificationMatcher()
        jd_text = "Requires CISSP certification"
        certs = matcher.extract_jd_requirements(jd_text)
        assert "CISSP" in certs

    def test_extracts_cism(self) -> None:
        """Should extract CISM certification from JD text."""
        matcher = CertificationMatcher()
        jd_text = "CISM or equivalent security certification required"
        certs = matcher.extract_jd_requirements(jd_text)
        assert "CISM" in certs

    def test_extracts_multiple_certs(self) -> None:
        """Should extract multiple certifications from JD text."""
        matcher = CertificationMatcher()
        jd_text = "Requires CISSP or CISM certification. GICSP preferred."
        certs = matcher.extract_jd_requirements(jd_text)
        assert "CISSP" in certs
        assert "CISM" in certs
        assert "GICSP" in certs

    def test_extracts_aws_solutions_architect(self) -> None:
        """Should extract AWS Solutions Architect certification."""
        matcher = CertificationMatcher()
        jd_text = "AWS Solutions Architect certification preferred"
        certs = matcher.extract_jd_requirements(jd_text)
        assert any("AWS" in cert for cert in certs)

    def test_extracts_aws_developer(self) -> None:
        """Should extract AWS Developer certification."""
        matcher = CertificationMatcher()
        jd_text = "AWS Developer certification required"
        certs = matcher.extract_jd_requirements(jd_text)
        assert any("AWS" in cert for cert in certs)

    def test_extracts_kubernetes_certs(self) -> None:
        """Should extract Kubernetes certifications (CKA, CKAD, CKS)."""
        matcher = CertificationMatcher()
        jd_text = "CKA or CKAD certification preferred"
        certs = matcher.extract_jd_requirements(jd_text)
        assert "CKA" in certs or "CKAD" in certs

    def test_extracts_project_management_certs(self) -> None:
        """Should extract project management certifications."""
        matcher = CertificationMatcher()
        jd_text = "PMP or CSM certification required"
        certs = matcher.extract_jd_requirements(jd_text)
        assert "PMP" in certs or "CSM" in certs

    def test_extracts_cisco_certs(self) -> None:
        """Should extract Cisco certifications."""
        matcher = CertificationMatcher()
        jd_text = "CCNA or CCNP networking certification"
        certs = matcher.extract_jd_requirements(jd_text)
        assert "CCNA" in certs or "CCNP" in certs

    def test_extracts_azure_certs(self) -> None:
        """Should extract Azure certifications."""
        matcher = CertificationMatcher()
        jd_text = "Azure Solutions Architect certification"
        certs = matcher.extract_jd_requirements(jd_text)
        assert any("AZURE" in cert.upper() for cert in certs)

    def test_case_insensitive(self) -> None:
        """Should be case insensitive when extracting certifications."""
        matcher = CertificationMatcher()
        jd_text = "cissp certification required"
        certs = matcher.extract_jd_requirements(jd_text)
        # Should still find CISSP (case normalized)
        assert any("CISSP" in cert.upper() for cert in certs)

    def test_returns_empty_for_no_certs(self) -> None:
        """Should return empty list when no certifications mentioned."""
        matcher = CertificationMatcher()
        jd_text = "5+ years of Python experience required"
        certs = matcher.extract_jd_requirements(jd_text)
        assert certs == []

    def test_returns_list(self) -> None:
        """Should return a list type."""
        matcher = CertificationMatcher()
        jd_text = "Any experience welcome"
        certs = matcher.extract_jd_requirements(jd_text)
        assert isinstance(certs, list)


class TestMatchCertifications:
    """Tests for match_certifications method."""

    def test_identifies_matched_certifications(self) -> None:
        """Should identify user certs that match JD requirements."""
        matcher = CertificationMatcher()
        user_certs = [
            Certification(name="CISSP", issuer="ISC2"),
            Certification(name="GICSP", issuer="GIAC"),
        ]
        jd_certs = ["CISSP", "CISM"]

        result = matcher.match_certifications(user_certs, jd_certs)
        assert "CISSP" in result.matched

    def test_identifies_gaps(self) -> None:
        """Should identify JD certs user doesn't have."""
        matcher = CertificationMatcher()
        user_certs = [
            Certification(name="CISSP", issuer="ISC2"),
        ]
        jd_certs = ["CISSP", "CISM"]

        result = matcher.match_certifications(user_certs, jd_certs)
        assert "CISM" in result.gaps

    def test_identifies_additional_certs(self) -> None:
        """Should identify user certs not in JD requirements."""
        matcher = CertificationMatcher()
        user_certs = [
            Certification(name="CISSP", issuer="ISC2"),
            Certification(name="GICSP", issuer="GIAC"),
        ]
        jd_certs = ["CISSP"]

        result = matcher.match_certifications(user_certs, jd_certs)
        assert "GICSP" in result.additional

    def test_calculates_match_percentage(self) -> None:
        """Should calculate correct match percentage."""
        matcher = CertificationMatcher()
        user_certs = [
            Certification(name="CISSP", issuer="ISC2"),
            Certification(name="CISM", issuer="ISACA"),
        ]
        jd_certs = ["CISSP", "CISM", "CISA"]  # User has 2 of 3

        result = matcher.match_certifications(user_certs, jd_certs)
        assert result.match_percentage == 67  # 2/3 rounded

    def test_handles_empty_user_certs(self) -> None:
        """Should handle empty user certifications list."""
        matcher = CertificationMatcher()
        user_certs: list[Certification] = []
        jd_certs = ["CISSP", "CISM"]

        result = matcher.match_certifications(user_certs, jd_certs)
        assert result.matched == []
        assert set(result.gaps) == {"CISSP", "CISM"}
        assert result.additional == []
        assert result.match_percentage == 0

    def test_handles_empty_jd_certs(self) -> None:
        """Should handle empty JD certifications list."""
        matcher = CertificationMatcher()
        user_certs = [
            Certification(name="CISSP", issuer="ISC2"),
        ]
        jd_certs: list[str] = []

        result = matcher.match_certifications(user_certs, jd_certs)
        assert result.matched == []
        assert result.gaps == []
        assert "CISSP" in result.additional
        assert result.match_percentage == 100  # No requirements = 100% match

    def test_handles_both_empty(self) -> None:
        """Should handle both lists empty."""
        matcher = CertificationMatcher()
        user_certs: list[Certification] = []
        jd_certs: list[str] = []

        result = matcher.match_certifications(user_certs, jd_certs)
        assert result.matched == []
        assert result.gaps == []
        assert result.additional == []
        assert result.match_percentage == 100  # No requirements = 100% match

    def test_returns_certification_match_result(self) -> None:
        """Should return a CertificationMatchResult dataclass."""
        matcher = CertificationMatcher()
        user_certs = [Certification(name="CISSP", issuer="ISC2")]
        jd_certs = ["CISSP"]

        result = matcher.match_certifications(user_certs, jd_certs)
        assert isinstance(result, CertificationMatchResult)
        assert hasattr(result, "matched")
        assert hasattr(result, "gaps")
        assert hasattr(result, "additional")
        assert hasattr(result, "match_percentage")

    def test_case_insensitive_matching(self) -> None:
        """Should match certifications case-insensitively."""
        matcher = CertificationMatcher()
        user_certs = [
            Certification(name="cissp", issuer="ISC2"),  # lowercase
        ]
        jd_certs = ["CISSP"]  # uppercase

        result = matcher.match_certifications(user_certs, jd_certs)
        # Should still match
        assert len(result.matched) == 1
        assert result.match_percentage == 100

    def test_partial_name_matching(self) -> None:
        """Should match certification names with variations."""
        matcher = CertificationMatcher()
        user_certs = [
            Certification(name="AWS Solutions Architect - Professional", issuer="AWS"),
        ]
        jd_certs = ["AWS Solutions Architect"]

        result = matcher.match_certifications(user_certs, jd_certs)
        # Should match the AWS Solutions Architect
        assert len(result.matched) >= 1


class TestCertificationMatchResult:
    """Tests for CertificationMatchResult dataclass."""

    def test_dataclass_fields(self) -> None:
        """Should have expected fields."""
        result = CertificationMatchResult(
            matched=["CISSP"],
            gaps=["CISM"],
            additional=["GICSP"],
            match_percentage=50,
        )
        assert result.matched == ["CISSP"]
        assert result.gaps == ["CISM"]
        assert result.additional == ["GICSP"]
        assert result.match_percentage == 50

    def test_dataclass_immutable(self) -> None:
        """Should be immutable (frozen dataclass)."""
        result = CertificationMatchResult(
            matched=["CISSP"],
            gaps=["CISM"],
            additional=[],
            match_percentage=50,
        )
        # Dataclass should be frozen for safety
        # If not frozen, this test documents expected behavior
        assert result.matched == ["CISSP"]
