"""Certification matcher service for JD requirements analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass

from resume_as_code.models.certification import Certification


@dataclass(frozen=True)
class CertificationMatchResult:
    """Result of matching user certifications against JD requirements.

    Attributes:
        matched: User certifications that match JD requirements.
        gaps: JD certification requirements user doesn't have.
        additional: User certifications not mentioned in JD.
        match_percentage: Percentage of JD requirements met (0-100).
    """

    matched: list[str]
    gaps: list[str]
    additional: list[str]
    match_percentage: int


class CertificationMatcher:
    """Match user certifications against JD requirements.

    Extracts certification mentions from job descriptions and compares
    against user's certifications to identify matches, gaps, and additional
    credentials.
    """

    # Common certification patterns (case-insensitive)
    CERT_PATTERNS: list[str] = [
        # Security certifications
        r"\b(CISSP)\b",
        r"\b(CISM)\b",
        r"\b(CISA)\b",
        r"\b(CEH)\b",
        r"\b(OSCP)\b",
        r"\b(GICSP)\b",
        r"\b(GSEC)\b",
        r"\b(GCIH)\b",
        r"\b(GPEN)\b",
        r"\b(Security\+)\b",
        r"\b(CompTIA\s+Security\+)\b",
        # AWS certifications
        r"\b(AWS\s+Solutions?\s+Architect)(?:\s*-\s*(?:Associate|Professional))?\b",
        r"\b(AWS\s+Developer)(?:\s*-\s*(?:Associate|Professional))?\b",
        r"\b(AWS\s+SysOps)(?:\s*-\s*(?:Administrator|Associate))?\b",
        r"\b(AWS\s+DevOps)(?:\s*-\s*(?:Engineer|Professional))?\b",
        r"\b(AWS\s+Certified\s+Solutions?\s+Architect)\b",
        r"\b(AWS\s+Certified\s+Developer)\b",
        # Kubernetes certifications
        r"\b(CKA)\b",
        r"\b(CKAD)\b",
        r"\b(CKS)\b",
        # Project management / Agile
        r"\b(PMP)\b",
        r"\b(CAPM)\b",
        r"\b(CSM)\b",
        r"\b(PSM)\b",
        r"\b(SAFe)\b",
        # Cisco certifications
        r"\b(CCNA)\b",
        r"\b(CCNP)\b",
        r"\b(CCIE)\b",
        # Azure certifications
        r"\b(Azure\s+Administrator)(?:\s*-\s*(?:Associate))?\b",
        r"\b(Azure\s+Developer)(?:\s*-\s*(?:Associate))?\b",
        r"\b(Azure\s+Solutions?\s+Architect)(?:\s*-\s*(?:Expert))?\b",
        # GCP certifications
        r"\b(GCP\s+Professional)(?:\s+(?:Cloud\s+)?(?:Architect|Engineer))?\b",
        r"\b(GCP\s+Associate)(?:\s+(?:Cloud\s+)?(?:Engineer))?\b",
        r"\b(Google\s+Cloud\s+(?:Professional|Associate))\b",
    ]

    def extract_jd_requirements(self, jd_text: str) -> list[str]:
        """Extract certification names mentioned in JD.

        Args:
            jd_text: Raw job description text.

        Returns:
            List of certification names found in the JD.
        """
        found_certs: set[str] = set()

        for pattern in self.CERT_PATTERNS:
            matches = re.finditer(pattern, jd_text, re.IGNORECASE)
            for match in matches:
                # Normalize the certification name
                cert_name = self._normalize_cert_name(match.group(0))
                if cert_name:
                    found_certs.add(cert_name)

        return sorted(found_certs)

    def match_certifications(
        self,
        user_certs: list[Certification],
        jd_certs: list[str],
    ) -> CertificationMatchResult:
        """Compare user certifications to JD requirements.

        Args:
            user_certs: List of user's Certification objects.
            jd_certs: List of certification names from JD.

        Returns:
            CertificationMatchResult with matched, gaps, additional, and percentage.
        """
        # Normalize user cert names for comparison
        user_cert_names = {self._normalize_cert_name(c.name): c.name for c in user_certs}
        user_cert_normalized = set(user_cert_names.keys())

        # Normalize JD cert names
        jd_cert_normalized = {self._normalize_cert_name(c): c for c in jd_certs}
        jd_cert_set = set(jd_cert_normalized.keys())

        # Find matches (intersection)
        matched_normalized = user_cert_normalized & jd_cert_set
        matched = [user_cert_names.get(n, jd_cert_normalized.get(n, n)) for n in matched_normalized]

        # Find gaps (JD certs user doesn't have)
        gaps_normalized = jd_cert_set - user_cert_normalized
        gaps = [jd_cert_normalized.get(n, n) for n in gaps_normalized]

        # Find additional (user certs not in JD)
        additional_normalized = user_cert_normalized - jd_cert_set
        additional = [user_cert_names.get(n, n) for n in additional_normalized]

        # Calculate match percentage (no requirements = 100% match)
        match_percentage = 100 if not jd_certs else round(len(matched) / len(jd_certs) * 100)

        return CertificationMatchResult(
            matched=sorted(matched),
            gaps=sorted(gaps),
            additional=sorted(additional),
            match_percentage=match_percentage,
        )

    def _normalize_cert_name(self, name: str) -> str:
        """Normalize certification name for comparison.

        Args:
            name: Raw certification name.

        Returns:
            Normalized certification name (uppercase, trimmed).
        """
        if not name:
            return ""

        # Remove extra whitespace and uppercase
        normalized = " ".join(name.split()).upper()

        # Extract core certification name from longer strings
        # e.g., "AWS Solutions Architect - Professional" -> "AWS SOLUTIONS ARCHITECT"
        # Keep the main certification type, remove level suffixes
        normalized = re.sub(r"\s*-\s*(ASSOCIATE|PROFESSIONAL|EXPERT)\s*$", "", normalized)

        return normalized
