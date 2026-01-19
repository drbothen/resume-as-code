"""Unit tests for Resume data models."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

from resume_as_code.models.certification import Certification
from resume_as_code.models.config import SkillsConfig
from resume_as_code.models.education import Education
from resume_as_code.models.resume import (
    ContactInfo,
    EmployerGroup,
    ResumeBullet,
    ResumeData,
    ResumeItem,
    ResumeSection,
    group_positions_by_employer,
    normalize_employer,
)
from resume_as_code.models.skill_entry import SkillEntry
from resume_as_code.services.skill_registry import SkillRegistry


class TestContactInfo:
    """Tests for ContactInfo model."""

    def test_contact_info_required_fields(self) -> None:
        """ContactInfo requires name field."""
        contact = ContactInfo(name="John Doe")
        assert contact.name == "John Doe"
        assert contact.email is None
        assert contact.phone is None

    def test_contact_info_all_fields(self) -> None:
        """ContactInfo accepts all optional fields."""
        contact = ContactInfo(
            name="Jane Doe",
            email="jane@example.com",
            phone="555-1234",
            location="San Francisco, CA",
            linkedin="https://linkedin.com/in/janedoe",
            github="https://github.com/janedoe",
            website="https://janedoe.com",
        )
        assert contact.name == "Jane Doe"
        assert contact.email == "jane@example.com"
        assert contact.phone == "555-1234"
        assert contact.location == "San Francisco, CA"
        assert contact.linkedin == "https://linkedin.com/in/janedoe"
        assert contact.github == "https://github.com/janedoe"
        assert contact.website == "https://janedoe.com"


class TestResumeBullet:
    """Tests for ResumeBullet model."""

    def test_bullet_text_only(self) -> None:
        """ResumeBullet can have just text."""
        bullet = ResumeBullet(text="Led team of 5 engineers")
        assert bullet.text == "Led team of 5 engineers"
        assert bullet.metrics is None

    def test_bullet_with_metrics(self) -> None:
        """ResumeBullet can include metrics."""
        bullet = ResumeBullet(
            text="Reduced deployment time",
            metrics="from 2 hours to 15 minutes",
        )
        assert bullet.text == "Reduced deployment time"
        assert bullet.metrics == "from 2 hours to 15 minutes"


class TestResumeItem:
    """Tests for ResumeItem model."""

    def test_item_minimal(self) -> None:
        """ResumeItem requires only title."""
        item = ResumeItem(title="Software Engineer")
        assert item.title == "Software Engineer"
        assert item.organization is None
        assert item.bullets == []

    def test_item_full(self) -> None:
        """ResumeItem accepts all optional fields."""
        item = ResumeItem(
            title="Senior Engineer",
            organization="Acme Corp",
            location="Remote",
            start_date="Jan 2023",
            end_date="Present",
            bullets=[
                ResumeBullet(text="Built scalable systems"),
                ResumeBullet(text="Mentored junior engineers"),
            ],
            scope_line="P&L: $50M ARR | Team: 8 | Budget: $1.5M",
        )
        assert item.title == "Senior Engineer"
        assert item.organization == "Acme Corp"
        assert len(item.bullets) == 2
        assert item.scope_line == "P&L: $50M ARR | Team: 8 | Budget: $1.5M"


class TestResumeSection:
    """Tests for ResumeSection model."""

    def test_section_with_items(self) -> None:
        """ResumeSection groups items under a title."""
        section = ResumeSection(
            title="Experience",
            items=[
                ResumeItem(title="Engineer", organization="Company A"),
                ResumeItem(title="Developer", organization="Company B"),
            ],
        )
        assert section.title == "Experience"
        assert len(section.items) == 2


class TestResumeData:
    """Tests for ResumeData model."""

    def test_resume_data_minimal(self) -> None:
        """ResumeData requires contact info."""
        contact = ContactInfo(name="Test User")
        resume = ResumeData(contact=contact)
        assert resume.contact.name == "Test User"
        assert resume.summary is None
        assert resume.sections == []
        assert resume.skills == []

    def test_resume_data_full(self) -> None:
        """ResumeData accepts all fields."""
        contact = ContactInfo(name="Jane Doe", email="jane@test.com")
        resume = ResumeData(
            contact=contact,
            summary="Experienced software engineer with 10+ years.",
            sections=[
                ResumeSection(
                    title="Experience",
                    items=[ResumeItem(title="Tech Lead", organization="BigCo")],
                )
            ],
            skills=["Python", "AWS", "Kubernetes"],
            education=[
                Education(
                    degree="BS Computer Science",
                    institution="State University",
                    graduation_year="2014",
                )
            ],
        )
        assert resume.summary is not None
        assert len(resume.sections) == 1
        assert len(resume.skills) == 3
        assert len(resume.education) == 1


class TestResumeDataFromWorkUnits:
    """Tests for ResumeData.from_work_units() factory method."""

    def test_from_work_units_transforms_to_resume_format(self) -> None:
        """Work Units are transformed into resume-ready format."""
        work_units = [
            {
                "id": "wu-2024-01-01-test-project",
                "title": "Led API Migration Project",
                "organization": "TechCorp",
                "time_started": date(2023, 6, 1),
                "time_ended": date(2024, 1, 15),
                "actions": [
                    "Designed new REST API architecture",
                    "Coordinated cross-team migration",
                ],
                "outcome": {
                    "result": "Successfully migrated 500+ endpoints",
                    "quantified_impact": "Reduced API response time by 40%",
                },
                "tags": ["python", "api"],
                "skills_demonstrated": ["leadership", "architecture"],
            }
        ]
        contact = ContactInfo(name="Test Developer")

        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
            summary="Senior engineer with API expertise.",
        )

        assert resume.contact.name == "Test Developer"
        assert resume.summary == "Senior engineer with API expertise."
        assert len(resume.sections) == 1

        # Check Experience section was created
        exp_section = resume.sections[0]
        assert exp_section.title == "Experience"
        assert len(exp_section.items) == 1

        # Check Work Unit was transformed to ResumeItem
        item = exp_section.items[0]
        assert item.title == "Led API Migration Project"
        assert item.organization == "TechCorp"

        # Check bullets were extracted from outcome
        assert len(item.bullets) >= 1
        assert item.bullets[0].text == "Successfully migrated 500+ endpoints"

        # Check skills were extracted
        assert "python" in resume.skills
        assert "api" in resume.skills
        assert "leadership" in resume.skills

    def test_from_work_units_ignores_deprecated_scope(self) -> None:
        """WorkUnit.scope is deprecated - scope comes from Position only.

        Story 7.2: Standalone work units (without position_id) have no scope_line.
        Scope fields on work units are ignored for resume rendering.

        Note: No deprecation warning expected here because work_units are raw dicts,
        not WorkUnit model instances. The warning only fires on WorkUnit() instantiation.
        """
        work_units = [
            {
                "id": "wu-2024-01-01-exec-project",
                "title": "VP Engineering Initiatives",
                "organization": "EnterpriseCo",
                "actions": ["Directed engineering strategy"],
                "outcome": {"result": "Achieved targets"},
                "scope": {
                    "budget_managed": "$5M",
                    "team_size": 25,
                    "revenue_influenced": "$100M ARR",
                },
                "tags": [],
                "skills_demonstrated": [],
            }
        ]
        contact = ContactInfo(name="Executive")

        resume = ResumeData.from_work_units(work_units, contact)

        # Standalone work unit without position_id has no scope_line
        # (WorkUnit.scope is deprecated and ignored for rendering)
        item = resume.sections[0].items[0]
        assert item.scope_line is None

    def test_from_work_units_formats_dates(self) -> None:
        """Dates are formatted for display."""
        work_units = [
            {
                "id": "wu-2024-01-01-date-test",
                "title": "Date Format Test",
                "time_started": date(2023, 3, 15),
                "time_ended": date(2024, 6, 1),
                "actions": ["Did work"],
                "outcome": {"result": "Completed"},
                "tags": [],
                "skills_demonstrated": [],
            }
        ]
        contact = ContactInfo(name="Test")

        resume = ResumeData.from_work_units(work_units, contact)

        item = resume.sections[0].items[0]
        assert item.start_date == "Mar 2023"
        assert item.end_date == "Jun 2024"

    def test_from_work_units_handles_empty_list(self) -> None:
        """Empty Work Units list produces empty sections."""
        contact = ContactInfo(name="Empty Test")

        resume = ResumeData.from_work_units([], contact)

        assert len(resume.sections) == 1
        assert resume.sections[0].title == "Experience"
        assert resume.sections[0].items == []

    def test_from_work_units_limits_action_bullets(self) -> None:
        """Actions are limited to 3 per Work Unit."""
        work_units = [
            {
                "id": "wu-2024-01-01-many-actions",
                "title": "Many Actions Test",
                "actions": [
                    "First action performed",
                    "Second action performed",
                    "Third action performed",
                    "Fourth action performed",
                    "Fifth action performed",
                ],
                "outcome": {"result": "All completed"},
                "tags": [],
                "skills_demonstrated": [],
            }
        ]
        contact = ContactInfo(name="Test")

        resume = ResumeData.from_work_units(work_units, contact)

        item = resume.sections[0].items[0]
        # 1 outcome bullet + max 3 action bullets = 4 total
        assert len(item.bullets) <= 4


class TestResumeDataDateFormatting:
    """Tests for date formatting helper."""

    def test_format_date_with_date_object(self) -> None:
        """Date objects are formatted as 'Mon YYYY'."""
        result = ResumeData._format_date(date(2023, 11, 15))
        assert result == "Nov 2023"

    def test_format_date_with_string(self) -> None:
        """String dates keep YYYY-MM format."""
        result = ResumeData._format_date("2023-11-15")
        assert result == "2023-11"

    def test_format_date_with_none(self) -> None:
        """None returns None."""
        result = ResumeData._format_date(None)
        assert result is None


class TestResumeDataCertifications:
    """Tests for certifications in ResumeData."""

    def test_certifications_default_empty(self) -> None:
        """ResumeData should default to empty certifications list."""
        contact = ContactInfo(name="Test User")
        resume = ResumeData(contact=contact)
        assert resume.certifications == []

    def test_certifications_with_list(self) -> None:
        """ResumeData should accept certifications list."""
        contact = ContactInfo(name="Test User")
        certs = [
            Certification(name="AWS SAP", issuer="Amazon Web Services"),
            Certification(name="CISSP", issuer="ISC2"),
        ]
        resume = ResumeData(contact=contact, certifications=certs)
        assert len(resume.certifications) == 2
        assert resume.certifications[0].name == "AWS SAP"
        assert resume.certifications[1].name == "CISSP"

    def test_certifications_empty_list_graceful(self) -> None:
        """Empty certifications list should be handled gracefully."""
        contact = ContactInfo(name="Test User")
        resume = ResumeData(contact=contact, certifications=[])
        assert resume.certifications == []
        # Should not cause errors when iterating
        assert list(resume.certifications) == []

    def test_certifications_with_full_fields(self) -> None:
        """ResumeData should store full certification data."""
        contact = ContactInfo(name="Test User")
        cert = Certification(
            name="AWS Solutions Architect - Professional",
            issuer="Amazon Web Services",
            date="2024-06",
            expires="2027-06",
            credential_id="ABC123",
            url="https://aws.amazon.com/verify/ABC123",
        )
        resume = ResumeData(contact=contact, certifications=[cert])
        assert resume.certifications[0].date == "2024-06"
        assert resume.certifications[0].expires == "2027-06"

    def test_get_active_certifications(self) -> None:
        """Should filter to only active/displayable certifications."""
        contact = ContactInfo(name="Test User")
        certs = [
            Certification(name="Active Cert", display=True),
            Certification(name="Hidden Cert", display=False),
            Certification(name="Expired Cert", expires="2020-01", display=True),
        ]
        resume = ResumeData(contact=contact, certifications=certs)
        active = resume.get_active_certifications()
        # Should return certs where display=True and not expired
        assert len(active) == 1
        assert active[0].name == "Active Cert"

    def test_get_active_certifications_includes_expires_soon(self) -> None:
        """Expiring soon certs should still be active."""
        contact = ContactInfo(name="Test User")
        certs = [
            Certification(name="Expiring Soon", expires="2099-01", display=True),
        ]
        resume = ResumeData(contact=contact, certifications=certs)
        active = resume.get_active_certifications()
        assert len(active) == 1

    def test_get_active_certifications_empty_list(self) -> None:
        """Empty certifications should return empty active list."""
        contact = ContactInfo(name="Test User")
        resume = ResumeData(contact=contact, certifications=[])
        active = resume.get_active_certifications()
        assert active == []


class TestResumeDataSkillsCuration:
    """Tests for skills curation integration in ResumeData.from_work_units() (AC #1, #2, #3).

    Note: These tests mock the registry to test curation logic in isolation.
    Registry integration is tested separately in TestResumeDataSkillsRegistryIntegration.
    """

    def test_from_work_units_with_skills_config_deduplicates(self) -> None:
        """Skills should be deduplicated case-insensitively when skills_config provided."""
        work_units = [
            {
                "id": "wu-1",
                "title": "Test",
                "tags": ["MySkill", "myskill", "OtherSkill", "otherskill"],
                "skills_demonstrated": [],
                "actions": [],
                "outcome": {"result": "Done"},
            }
        ]
        contact = ContactInfo(name="Test")
        skills_config = SkillsConfig()

        # Use empty registry to test deduplication logic without normalization
        with patch.object(SkillRegistry, "load_default", return_value=SkillRegistry([])):
            resume = ResumeData.from_work_units(
                work_units=work_units,
                contact=contact,
                skills_config=skills_config,
            )

        # Should have 2 skills (MySkill and OtherSkill) not 4
        assert len(resume.skills) == 2
        lower_skills = [s.lower() for s in resume.skills]
        assert lower_skills.count("myskill") == 1
        assert lower_skills.count("otherskill") == 1

    def test_from_work_units_with_skills_config_respects_max_display(self) -> None:
        """Skills should be limited to max_display when skills_config provided."""
        work_units = [
            {
                "id": "wu-1",
                "title": "Test",
                "tags": [f"Skill{i}" for i in range(20)],  # 20 skills
                "skills_demonstrated": [],
                "actions": [],
                "outcome": {"result": "Done"},
            }
        ]
        contact = ContactInfo(name="Test")
        skills_config = SkillsConfig(max_display=5)

        with patch.object(SkillRegistry, "load_default", return_value=SkillRegistry([])):
            resume = ResumeData.from_work_units(
                work_units=work_units,
                contact=contact,
                skills_config=skills_config,
            )

        assert len(resume.skills) == 5

    def test_from_work_units_with_skills_config_respects_exclude(self) -> None:
        """Excluded skills should not appear when skills_config provided."""
        work_units = [
            {
                "id": "wu-1",
                "title": "Test",
                "tags": ["SkillA", "ExcludeMe", "SkillB", "AlsoExclude"],
                "skills_demonstrated": [],
                "actions": [],
                "outcome": {"result": "Done"},
            }
        ]
        contact = ContactInfo(name="Test")
        skills_config = SkillsConfig(exclude=["ExcludeMe", "AlsoExclude"])

        with patch.object(SkillRegistry, "load_default", return_value=SkillRegistry([])):
            resume = ResumeData.from_work_units(
                work_units=work_units,
                contact=contact,
                skills_config=skills_config,
            )

        assert "ExcludeMe" not in resume.skills
        assert "AlsoExclude" not in resume.skills
        assert "SkillA" in resume.skills
        assert "SkillB" in resume.skills

    def test_from_work_units_with_jd_keywords_prioritizes_matches(self) -> None:
        """JD-matching skills should be prioritized when jd_keywords provided."""
        work_units = [
            {
                "id": "wu-1",
                "title": "Test",
                "tags": ["Alpha", "Beta", "Gamma", "Delta"],
                "skills_demonstrated": [],
                "actions": [],
                "outcome": {"result": "Done"},
            }
        ]
        contact = ContactInfo(name="Test")
        skills_config = SkillsConfig(max_display=3)

        with patch.object(SkillRegistry, "load_default", return_value=SkillRegistry([])):
            resume = ResumeData.from_work_units(
                work_units=work_units,
                contact=contact,
                skills_config=skills_config,
                jd_keywords={"gamma", "delta"},
            )

        # Gamma and Delta should be in the top 3 (JD matches prioritized)
        lower_skills = [s.lower() for s in resume.skills]
        assert "gamma" in lower_skills
        assert "delta" in lower_skills

    def test_from_work_units_extracts_from_tags_and_skills_demonstrated(self) -> None:
        """Skills should be extracted from both tags and skills_demonstrated."""
        work_units = [
            {
                "id": "wu-1",
                "title": "Test",
                "tags": ["SkillFromTag1", "SkillFromTag2"],
                "skills_demonstrated": ["SkillDemo1", "SkillDemo2"],
                "actions": [],
                "outcome": {"result": "Done"},
            }
        ]
        contact = ContactInfo(name="Test")
        skills_config = SkillsConfig()

        with patch.object(SkillRegistry, "load_default", return_value=SkillRegistry([])):
            resume = ResumeData.from_work_units(
                work_units=work_units,
                contact=contact,
                skills_config=skills_config,
            )

        assert len(resume.skills) == 4
        assert "SkillFromTag1" in resume.skills
        assert "SkillFromTag2" in resume.skills
        assert "SkillDemo1" in resume.skills
        assert "SkillDemo2" in resume.skills

    def test_from_work_units_without_skills_config_uses_old_behavior(self) -> None:
        """Without skills_config, old alphabetical sorting should be used."""
        work_units = [
            {
                "id": "wu-1",
                "title": "Test",
                "tags": ["Zulu", "Alpha", "Mike"],
                "skills_demonstrated": [],
                "actions": [],
                "outcome": {"result": "Done"},
            }
        ]
        contact = ContactInfo(name="Test")

        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
        )

        # Without skills_config, should be alphabetically sorted
        assert resume.skills == ["Alpha", "Mike", "Zulu"]


class TestResumeDataPositionGrouping:
    """Tests for position-based grouping of work units."""

    def test_from_work_units_without_positions_uses_standalone(self) -> None:
        """Without positions, work units should be treated as standalone entries."""
        work_units = [
            {
                "id": "wu-1",
                "title": "Built API service",
                "actions": ["Designed REST API"],
                "outcome": {"result": "Reduced latency by 50%"},
            }
        ]
        contact = ContactInfo(name="Test")

        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
            positions_path=None,
        )

        assert len(resume.sections) == 1
        assert resume.sections[0].title == "Experience"
        assert len(resume.sections[0].items) == 1
        assert resume.sections[0].items[0].title == "Built API service"

    def test_from_work_units_with_positions_groups_by_position(self, tmp_path: Path) -> None:
        """Work units should be grouped by position_id."""

        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-techcorp-senior:
    employer: "TechCorp Industries"
    title: "Senior Engineer"
    location: "Austin, TX"
    start_date: "2022-01"
""")
        work_units = [
            {
                "id": "wu-1",
                "title": "Built API service",
                "position_id": "pos-techcorp-senior",
                "actions": ["Designed REST API"],
                "outcome": {"result": "Reduced latency by 50%"},
            },
            {
                "id": "wu-2",
                "title": "Improved performance",
                "position_id": "pos-techcorp-senior",
                "actions": ["Optimized queries"],
                "outcome": {"result": "10x faster"},
            },
        ]
        contact = ContactInfo(name="Test")

        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
            positions_path=positions_file,
        )

        # Should have one item with both work units' bullets
        assert len(resume.sections[0].items) == 1
        item = resume.sections[0].items[0]
        assert item.title == "Senior Engineer"
        assert item.organization == "TechCorp Industries"
        assert item.location == "Austin, TX"
        assert item.start_date == "2022"
        assert len(item.bullets) >= 2  # At least one bullet per work unit

    def test_from_work_units_with_mixed_positions(self, tmp_path: Path) -> None:
        """Work units with and without positions should both render."""

        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-techcorp:
    employer: "TechCorp"
    title: "Engineer"
    start_date: "2022-01"
""")
        work_units = [
            {
                "id": "wu-1",
                "title": "Project at TechCorp",
                "position_id": "pos-techcorp",
                "actions": ["Built feature"],
                "outcome": {"result": "Success"},
            },
            {
                "id": "wu-2",
                "title": "Open source contribution",
                "actions": ["Fixed bug"],
                "outcome": {"result": "Merged PR"},
            },
        ]
        contact = ContactInfo(name="Test")

        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
            positions_path=positions_file,
        )

        # Should have two items: one position-based, one standalone
        assert len(resume.sections[0].items) == 2

    def test_from_work_units_sorts_by_date_descending(self, tmp_path: Path) -> None:
        """Experience items should be sorted by date (most recent first)."""

        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-old:
    employer: "OldCorp"
    title: "Junior"
    start_date: "2018-01"
    end_date: "2019-12"
  pos-new:
    employer: "NewCorp"
    title: "Senior"
    start_date: "2022-01"
""")
        work_units = [
            {
                "id": "wu-old",
                "title": "Old work",
                "position_id": "pos-old",
                "actions": ["Did stuff"],
                "outcome": {"result": "Done"},
            },
            {
                "id": "wu-new",
                "title": "New work",
                "position_id": "pos-new",
                "actions": ["Did stuff"],
                "outcome": {"result": "Done"},
            },
        ]
        contact = ContactInfo(name="Test")

        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
            positions_path=positions_file,
        )

        items = resume.sections[0].items
        assert len(items) == 2
        # Most recent first
        assert items[0].organization == "NewCorp"
        assert items[1].organization == "OldCorp"

    def test_from_work_units_invalid_position_id_fallback(self, tmp_path: Path) -> None:
        """Work units with invalid position_id should be treated as standalone."""

        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-valid:
    employer: "ValidCorp"
    title: "Engineer"
    start_date: "2022-01"
""")
        work_units = [
            {
                "id": "wu-1",
                "title": "Work with invalid position",
                "position_id": "pos-nonexistent",  # Invalid reference
                "actions": ["Did work"],
                "outcome": {"result": "Done"},
            },
        ]
        contact = ContactInfo(name="Test")

        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
            positions_path=positions_file,
        )

        # Should fall back to standalone entry
        assert len(resume.sections[0].items) == 1
        assert resume.sections[0].items[0].title == "Work with invalid position"


class TestResumeDataSkillsRegistryIntegration:
    """Tests for SkillRegistry integration in ResumeData.from_work_units() (Story 7.4)."""

    def test_from_work_units_normalizes_skills_via_registry(self) -> None:
        """Skills should be normalized to canonical names via registry (AC #1)."""
        # Create a registry with known aliases
        registry = SkillRegistry(
            [
                SkillEntry(canonical="Kubernetes", aliases=["k8s", "kube"]),
                SkillEntry(canonical="TypeScript", aliases=["ts"]),
            ]
        )

        work_units = [
            {
                "id": "wu-1",
                "title": "Test",
                "tags": ["k8s", "ts", "Python"],  # k8s and ts are aliases
                "skills_demonstrated": [],
                "actions": [],
                "outcome": {"result": "Done"},
            }
        ]
        contact = ContactInfo(name="Test")
        skills_config = SkillsConfig()

        # Mock load_default to return our test registry
        with patch.object(SkillRegistry, "load_default", return_value=registry):
            resume = ResumeData.from_work_units(
                work_units=work_units,
                contact=contact,
                skills_config=skills_config,
            )

        # Should have canonical names, not aliases
        assert "Kubernetes" in resume.skills
        assert "TypeScript" in resume.skills
        assert "Python" in resume.skills
        # Aliases should not appear
        assert "k8s" not in resume.skills
        assert "ts" not in resume.skills

    def test_from_work_units_deduplicates_via_registry_normalization(self) -> None:
        """Multiple aliases for same skill should dedupe to one entry (AC #5)."""
        registry = SkillRegistry(
            [
                SkillEntry(canonical="Kubernetes", aliases=["k8s", "kube"]),
            ]
        )

        work_units = [
            {
                "id": "wu-1",
                "title": "Test",
                "tags": ["k8s", "kube", "Kubernetes"],  # All same skill
                "skills_demonstrated": [],
                "actions": [],
                "outcome": {"result": "Done"},
            }
        ]
        contact = ContactInfo(name="Test")
        skills_config = SkillsConfig()

        with patch.object(SkillRegistry, "load_default", return_value=registry):
            resume = ResumeData.from_work_units(
                work_units=work_units,
                contact=contact,
                skills_config=skills_config,
            )

        # Should have only one Kubernetes entry
        assert resume.skills.count("Kubernetes") == 1
        assert len(resume.skills) == 1

    def test_from_work_units_jd_matching_via_alias_expansion(self) -> None:
        """JD keywords should match via alias expansion (AC #6)."""
        registry = SkillRegistry(
            [
                SkillEntry(canonical="Kubernetes", aliases=["k8s", "kube"]),
                SkillEntry(canonical="Python", aliases=["py", "python3"]),
            ]
        )

        work_units = [
            {
                "id": "wu-1",
                "title": "Test",
                "tags": ["k8s", "Ruby", "Java"],  # k8s is alias for Kubernetes
                "skills_demonstrated": [],
                "actions": [],
                "outcome": {"result": "Done"},
            }
        ]
        contact = ContactInfo(name="Test")
        skills_config = SkillsConfig(max_display=2)

        # JD mentions "Kubernetes" canonical name
        with patch.object(SkillRegistry, "load_default", return_value=registry):
            resume = ResumeData.from_work_units(
                work_units=work_units,
                contact=contact,
                skills_config=skills_config,
                jd_keywords={"Kubernetes"},  # JD has canonical name
            )

        # Kubernetes should be prioritized even though work unit has "k8s"
        assert "Kubernetes" in resume.skills
        assert resume.skills[0] == "Kubernetes"  # Should be first

    def test_from_work_units_unknown_skills_passthrough(self) -> None:
        """Unknown skills should pass through unchanged (AC #4)."""
        registry = SkillRegistry(
            [
                SkillEntry(canonical="Kubernetes", aliases=["k8s"]),
            ]
        )

        work_units = [
            {
                "id": "wu-1",
                "title": "Test",
                "tags": ["k8s", "CustomFramework", "MyTool"],
                "skills_demonstrated": [],
                "actions": [],
                "outcome": {"result": "Done"},
            }
        ]
        contact = ContactInfo(name="Test")
        skills_config = SkillsConfig()

        with patch.object(SkillRegistry, "load_default", return_value=registry):
            resume = ResumeData.from_work_units(
                work_units=work_units,
                contact=contact,
                skills_config=skills_config,
            )

        # Known alias normalized, unknown pass through
        assert "Kubernetes" in resume.skills
        assert "CustomFramework" in resume.skills
        assert "MyTool" in resume.skills

    def test_from_work_units_loads_default_registry(self) -> None:
        """from_work_units should load the default registry when skills_config provided."""
        work_units = [
            {
                "id": "wu-1",
                "title": "Test",
                "tags": ["Python"],
                "skills_demonstrated": [],
                "actions": [],
                "outcome": {"result": "Done"},
            }
        ]
        contact = ContactInfo(name="Test")
        skills_config = SkillsConfig()

        # Verify load_with_onet is called (Story 7.17)
        with patch.object(SkillRegistry, "load_with_onet") as mock_load:
            mock_load.return_value = SkillRegistry([])
            ResumeData.from_work_units(
                work_units=work_units,
                contact=contact,
                skills_config=skills_config,
            )
            mock_load.assert_called_once()


class TestResumeDataActionScoring:
    """Tests for action-level scoring in ResumeData.from_work_units() (Story 7.18)."""

    def test_action_scoring_disabled_uses_legacy_behavior(self, tmp_path: Path) -> None:
        """When action_scoring_enabled=False, all bullets extracted without scoring."""
        from resume_as_code.models.config import CurationConfig
        from resume_as_code.models.job_description import JobDescription

        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-test:
    employer: "TestCorp"
    title: "Engineer"
    start_date: "2024-01"
""")
        work_units = [
            {
                "id": "wu-2024-01-01-test-one",
                "title": "Test Work Unit One",
                "position_id": "pos-test",
                "problem": {"statement": "This is a test problem statement for unit one"},
                "actions": ["Action one performed", "Action two performed"],
                "outcome": {"result": "Completed with success"},
                "tags": [],
                "skills_demonstrated": [],
            }
        ]
        contact = ContactInfo(name="Test")
        curation_config = CurationConfig(action_scoring_enabled=False)
        jd = JobDescription(
            title="Test Job",
            company="TestCo",
            raw_text="Test JD text looking for Python developer",
            skills=["Python"],
            keywords=["Python"],
        )

        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
            positions_path=positions_file,
            curation_config=curation_config,
            jd=jd,
        )

        # Should have all bullets (1 outcome + 2 actions = 3)
        item = resume.sections[0].items[0]
        assert len(item.bullets) == 3

    def test_action_scoring_without_jd_uses_legacy_behavior(self, tmp_path: Path) -> None:
        """When JD not provided, all bullets extracted without scoring."""
        from resume_as_code.models.config import CurationConfig

        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-test:
    employer: "TestCorp"
    title: "Engineer"
    start_date: "2024-01"
""")
        work_units = [
            {
                "id": "wu-2024-01-01-test-one",
                "title": "Test Work Unit One",
                "position_id": "pos-test",
                "problem": {"statement": "This is a test problem statement for unit one"},
                "actions": ["Action one performed", "Action two performed"],
                "outcome": {"result": "Completed with success"},
                "tags": [],
                "skills_demonstrated": [],
            }
        ]
        contact = ContactInfo(name="Test")
        curation_config = CurationConfig(action_scoring_enabled=True)

        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
            positions_path=positions_file,
            curation_config=curation_config,
            jd=None,  # No JD provided
        )

        # Should have all bullets (1 outcome + 2 actions = 3)
        item = resume.sections[0].items[0]
        assert len(item.bullets) == 3

    def test_action_scoring_enabled_curates_bullets(self, tmp_path: Path) -> None:
        """When action_scoring_enabled=True and JD provided, bullets are curated by relevance.

        This is an integration test that uses the real ContentCurator to verify
        the full action scoring flow works end-to-end.
        """
        from resume_as_code.models.config import CurationConfig
        from resume_as_code.models.job_description import JobDescription

        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "4.0.0"
archetype: minimal
positions:
  pos-test:
    employer: "TestCorp"
    title: "Engineer"
    start_date: "2024-01"
""")
        work_units = [
            {
                "id": "wu-2024-01-01-test-one",
                "title": "Test Work Unit One",
                "position_id": "pos-test",
                "problem": {"statement": "This is a test problem statement for unit one"},
                "actions": [
                    "Built Python microservice with Flask reducing API latency by 50%",
                    "Organized team meetings and wrote documentation for internal wiki",
                ],
                "outcome": {"result": "Deployed scalable Python Flask application to production"},
                "tags": [],
                "skills_demonstrated": [],
            }
        ]
        contact = ContactInfo(name="Test")
        curation_config = CurationConfig(
            action_scoring_enabled=True,
            min_action_relevance_score=0.0,  # Low threshold to ensure bullets pass
        )
        jd = JobDescription(
            title="Python Developer",
            company="TestCo",
            raw_text="Looking for a Python developer with Flask microservice experience",
            skills=["Python", "Flask"],
            keywords=["Python", "Flask", "microservice", "API", "scalable"],
        )

        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
            positions_path=positions_file,
            curation_config=curation_config,
            jd=jd,
        )

        # Should have curated bullets (actual count depends on scoring)
        item = resume.sections[0].items[0]
        # Verify that action scoring was used (bullets should be ResumeBullet instances)
        assert len(item.bullets) > 0
        assert all(hasattr(b, "text") for b in item.bullets)
        # The Python/Flask related bullets should score higher than meeting/wiki bullet

    def test_action_scoring_standalone_work_units_use_legacy(self) -> None:
        """Standalone work units (no position_id) use legacy bullet extraction."""
        from resume_as_code.models.config import CurationConfig
        from resume_as_code.models.job_description import JobDescription

        work_units = [
            {
                "id": "wu-2024-01-01-standalone",
                "title": "Open Source Contribution",
                "actions": ["Fixed bug in library", "Added documentation"],
                "outcome": {"result": "PR merged upstream"},
                "tags": [],
                "skills_demonstrated": [],
            }
        ]
        contact = ContactInfo(name="Test")
        curation_config = CurationConfig(action_scoring_enabled=True)
        jd = JobDescription(
            title="Developer",
            company="TestCo",
            raw_text="Looking for Python developer",
            skills=["Python"],
            keywords=["Python"],
        )

        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
            positions_path=None,  # No positions file
            curation_config=curation_config,
            jd=jd,
        )

        # Standalone work units don't use action scoring
        item = resume.sections[0].items[0]
        assert len(item.bullets) == 3  # 1 outcome + 2 actions


class TestNormalizeEmployer:
    """Tests for normalize_employer() function (Story 8.1 AC #2)."""

    def test_normalize_employer_lowercase(self) -> None:
        """Employer names should be normalized to lowercase."""
        assert normalize_employer("TechCorp") == "techcorp"
        assert normalize_employer("ACME INC") == "acme"

    def test_normalize_employer_strips_whitespace(self) -> None:
        """Leading and trailing whitespace should be stripped."""
        assert normalize_employer("  TechCorp  ") == "techcorp"
        assert normalize_employer("\tAcme\n") == "acme"

    def test_normalize_employer_ampersand_to_and(self) -> None:
        """Ampersand should be normalized to 'and'."""
        assert normalize_employer("Burns & McDonnell") == "burns and mcdonnell"
        assert normalize_employer("Burns&McDonnell") == "burns and mcdonnell"

    def test_normalize_employer_removes_inc_suffix(self) -> None:
        """Common corporate suffixes should be removed."""
        assert normalize_employer("TechCorp, Inc.") == "techcorp"
        assert normalize_employer("TechCorp Inc") == "techcorp"
        assert normalize_employer("TechCorp Inc.") == "techcorp"

    def test_normalize_employer_removes_llc_suffix(self) -> None:
        """LLC suffix should be removed."""
        assert normalize_employer("TechCorp, LLC") == "techcorp"
        assert normalize_employer("TechCorp LLC") == "techcorp"

    def test_normalize_employer_removes_corp_suffix(self) -> None:
        """Corp suffix should be removed."""
        assert normalize_employer("TechCorp, Corp") == "techcorp"
        assert normalize_employer("TechCorp Corp") == "techcorp"

    def test_normalize_employer_case_insensitive_matching(self) -> None:
        """Same employer with different cases should normalize to same value."""
        assert normalize_employer("Burns & McDonnell") == normalize_employer("BURNS & MCDONNELL")
        assert normalize_employer("TechCorp Industries") == normalize_employer(
            "techcorp industries"
        )

    def test_normalize_employer_preserves_core_name(self) -> None:
        """Core employer name should be preserved after normalization."""
        assert normalize_employer("Acme Corporation") == "acme corporation"
        assert normalize_employer("Big Tech Company") == "big tech company"


class TestEmployerGroup:
    """Tests for EmployerGroup dataclass (Story 8.1 AC #1, #3)."""

    def test_employer_group_basic_properties(self) -> None:
        """EmployerGroup should store basic employer info."""
        group = EmployerGroup(
            employer="TechCorp Industries",
            location="Austin, TX",
            total_start_date="2020-01",
            total_end_date="2024-06",
            positions=[],
        )
        assert group.employer == "TechCorp Industries"
        assert group.location == "Austin, TX"
        assert group.total_start_date == "2020-01"
        assert group.total_end_date == "2024-06"

    def test_employer_group_is_multi_position_single(self) -> None:
        """is_multi_position should be False for single position."""
        group = EmployerGroup(
            employer="TechCorp",
            location=None,
            total_start_date="2022-01",
            total_end_date=None,
            positions=[
                ResumeItem(title="Engineer", organization="TechCorp"),
            ],
        )
        assert group.is_multi_position is False

    def test_employer_group_is_multi_position_multiple(self) -> None:
        """is_multi_position should be True for multiple positions."""
        group = EmployerGroup(
            employer="TechCorp",
            location=None,
            total_start_date="2020-01",
            total_end_date=None,
            positions=[
                ResumeItem(title="Senior Engineer", organization="TechCorp"),
                ResumeItem(title="Engineer", organization="TechCorp"),
            ],
        )
        assert group.is_multi_position is True

    def test_employer_group_tenure_display_with_end_date(self) -> None:
        """tenure_display should format date range with end date."""
        group = EmployerGroup(
            employer="TechCorp",
            location=None,
            total_start_date="2020",
            total_end_date="2024",
            positions=[],
        )
        assert group.tenure_display == "2020 - 2024"

    def test_employer_group_tenure_display_current(self) -> None:
        """tenure_display should show 'Present' for current positions."""
        group = EmployerGroup(
            employer="TechCorp",
            location=None,
            total_start_date="2020",
            total_end_date=None,
            positions=[],
        )
        assert group.tenure_display == "2020 - Present"


class TestGroupPositionsByEmployer:
    """Tests for group_positions_by_employer() function (Story 8.1 AC #1, #2, #3, #5)."""

    def test_group_single_position_employer(self) -> None:
        """Single position per employer should create single-position group."""
        items = [
            ResumeItem(
                title="Engineer",
                organization="TechCorp",
                location="Austin, TX",
                start_date="2022",
                end_date=None,
                bullets=[ResumeBullet(text="Built features")],
            ),
        ]

        groups = group_positions_by_employer(items)

        assert len(groups) == 1
        assert groups[0].employer == "TechCorp"
        assert groups[0].is_multi_position is False
        assert len(groups[0].positions) == 1

    def test_group_multi_position_employer(self) -> None:
        """Multiple positions at same employer should be grouped."""
        items = [
            ResumeItem(
                title="Senior Engineer",
                organization="TechCorp",
                location="Austin, TX",
                start_date="2023",
                end_date=None,
            ),
            ResumeItem(
                title="Engineer",
                organization="TechCorp",
                location="Austin, TX",
                start_date="2020",
                end_date="2023",
            ),
        ]

        groups = group_positions_by_employer(items)

        assert len(groups) == 1
        assert groups[0].employer == "TechCorp"
        assert groups[0].is_multi_position is True
        assert len(groups[0].positions) == 2

    def test_group_employer_name_normalization(self) -> None:
        """Employer name variations should be grouped together."""
        items = [
            ResumeItem(
                title="Senior Engineer",
                organization="Burns & McDonnell",
                start_date="2023",
            ),
            ResumeItem(
                title="Engineer",
                organization="Burns and McDonnell",
                start_date="2020",
                end_date="2023",
            ),
        ]

        groups = group_positions_by_employer(items)

        # Should be grouped together despite "&" vs "and"
        assert len(groups) == 1
        assert groups[0].is_multi_position is True

    def test_group_preserves_original_employer_name(self) -> None:
        """Group should use the employer name from most recent position."""
        items = [
            ResumeItem(
                title="Senior Engineer",
                organization="Burns & McDonnell",  # Most recent
                start_date="2023",
            ),
            ResumeItem(
                title="Engineer",
                organization="Burns and McDonnell",  # Older
                start_date="2020",
                end_date="2023",
            ),
        ]

        groups = group_positions_by_employer(items)

        # Should use name from most recent position
        assert groups[0].employer == "Burns & McDonnell"

    def test_group_calculates_total_tenure(self) -> None:
        """Group should calculate tenure from earliest start to latest end."""
        items = [
            ResumeItem(
                title="Senior Engineer",
                organization="TechCorp",
                start_date="2023",
                end_date=None,  # Current
            ),
            ResumeItem(
                title="Engineer",
                organization="TechCorp",
                start_date="2020",
                end_date="2023",
            ),
        ]

        groups = group_positions_by_employer(items)

        assert groups[0].total_start_date == "2020"
        assert groups[0].total_end_date is None  # Still current

    def test_group_positions_reverse_chronological(self) -> None:
        """Positions within group should be sorted most recent first."""
        items = [
            ResumeItem(
                title="Engineer",
                organization="TechCorp",
                start_date="2020",
                end_date="2022",
            ),
            ResumeItem(
                title="Senior Engineer",
                organization="TechCorp",
                start_date="2022",
                end_date=None,
            ),
        ]

        groups = group_positions_by_employer(items)

        # Most recent first within group
        assert groups[0].positions[0].title == "Senior Engineer"
        assert groups[0].positions[1].title == "Engineer"

    def test_group_mixed_employers(self) -> None:
        """Mix of single and multi-position employers should work correctly."""
        items = [
            ResumeItem(
                title="Senior Engineer",
                organization="TechCorp",
                start_date="2023",
            ),
            ResumeItem(
                title="Engineer",
                organization="TechCorp",
                start_date="2020",
                end_date="2023",
            ),
            ResumeItem(
                title="Developer",
                organization="StartupCo",
                start_date="2018",
                end_date="2020",
            ),
        ]

        groups = group_positions_by_employer(items)

        assert len(groups) == 2
        # TechCorp should be multi-position
        techcorp = next(g for g in groups if g.employer == "TechCorp")
        assert techcorp.is_multi_position is True
        # StartupCo should be single-position
        startup = next(g for g in groups if g.employer == "StartupCo")
        assert startup.is_multi_position is False

    def test_group_empty_items(self) -> None:
        """Empty items list should return empty groups list."""
        groups = group_positions_by_employer([])
        assert groups == []

    def test_group_uses_location_from_most_recent(self) -> None:
        """Group should use location from most recent position."""
        items = [
            ResumeItem(
                title="Senior Engineer",
                organization="TechCorp",
                location="New York, NY",  # Most recent
                start_date="2023",
            ),
            ResumeItem(
                title="Engineer",
                organization="TechCorp",
                location="Austin, TX",  # Older
                start_date="2020",
                end_date="2023",
            ),
        ]

        groups = group_positions_by_employer(items)

        # Should use location from most recent position
        assert groups[0].location == "New York, NY"

    def test_group_handles_none_organization(self) -> None:
        """Items without organization should each be their own group."""
        items = [
            ResumeItem(
                title="Freelance Project",
                organization=None,
                start_date="2022",
            ),
            ResumeItem(
                title="Open Source",
                organization=None,
                start_date="2021",
            ),
        ]

        groups = group_positions_by_employer(items)

        # Each item without org is its own group
        assert len(groups) == 2

    def test_group_orders_by_most_recent_position(self) -> None:
        """Groups should be ordered by most recent position date."""
        items = [
            ResumeItem(
                title="Developer",
                organization="OldCorp",
                start_date="2015",
                end_date="2018",
            ),
            ResumeItem(
                title="Senior Engineer",
                organization="NewCorp",
                start_date="2022",
            ),
            ResumeItem(
                title="Engineer",
                organization="MidCorp",
                start_date="2018",
                end_date="2022",
            ),
        ]

        groups = group_positions_by_employer(items)

        # Groups should be ordered most recent first
        assert groups[0].employer == "NewCorp"
        assert groups[1].employer == "MidCorp"
        assert groups[2].employer == "OldCorp"

    def test_group_handles_none_start_dates(self) -> None:
        """Positions with None start_date should be handled gracefully (Issue #3 fix)."""
        items = [
            ResumeItem(
                title="Project Alpha",
                organization="TechCorp",
                start_date=None,  # No start date
            ),
            ResumeItem(
                title="Project Beta",
                organization="TechCorp",
                start_date=None,  # No start date
            ),
            ResumeItem(
                title="Regular Role",
                organization="TechCorp",
                start_date="2022",
            ),
        ]

        groups = group_positions_by_employer(items)

        # Should still group correctly
        assert len(groups) == 1
        assert groups[0].employer == "TechCorp"
        assert len(groups[0].positions) == 3
        # Regular Role with date should be first (most recent)
        assert groups[0].positions[0].title == "Regular Role"

    def test_group_all_positions_none_start_dates(self) -> None:
        """All positions with None start_date should still group."""
        items = [
            ResumeItem(
                title="Alpha",
                organization="TechCorp",
                start_date=None,
            ),
            ResumeItem(
                title="Beta",
                organization="TechCorp",
                start_date=None,
            ),
        ]

        groups = group_positions_by_employer(items)

        # Should group together
        assert len(groups) == 1
        assert groups[0].employer == "TechCorp"
        assert len(groups[0].positions) == 2
        # Total tenure should use empty string as fallback
        assert groups[0].total_start_date == ""
