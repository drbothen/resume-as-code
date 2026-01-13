"""Unit tests for Resume data models."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from resume_as_code.models.certification import Certification
from resume_as_code.models.config import SkillsConfig
from resume_as_code.models.education import Education
from resume_as_code.models.resume import (
    ContactInfo,
    ResumeBullet,
    ResumeData,
    ResumeItem,
    ResumeSection,
)


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
            scope_budget="$1.5M",
            scope_team_size=8,
            scope_revenue="$50M ARR",
        )
        assert item.title == "Senior Engineer"
        assert item.organization == "Acme Corp"
        assert len(item.bullets) == 2
        assert item.scope_budget == "$1.5M"
        assert item.scope_team_size == 8


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
                    year="2014",
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

    def test_from_work_units_extracts_scope_fields(self) -> None:
        """Executive scope fields are preserved."""
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

        item = resume.sections[0].items[0]
        assert item.scope_budget == "$5M"
        assert item.scope_team_size == 25
        assert item.scope_revenue == "$100M ARR"

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
    """Tests for skills curation integration in ResumeData.from_work_units() (AC #1, #2, #3)."""

    def test_from_work_units_with_skills_config_deduplicates(self) -> None:
        """Skills should be deduplicated case-insensitively when skills_config provided."""
        work_units = [
            {
                "id": "wu-1",
                "title": "Test",
                "tags": ["AWS", "aws", "Python", "python"],
                "skills_demonstrated": [],
                "actions": [],
                "outcome": {"result": "Done"},
            }
        ]
        contact = ContactInfo(name="Test")
        skills_config = SkillsConfig()

        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
            skills_config=skills_config,
        )

        # Should have 2 skills (AWS and Python) not 4
        assert len(resume.skills) == 2
        lower_skills = [s.lower() for s in resume.skills]
        assert lower_skills.count("aws") == 1
        assert lower_skills.count("python") == 1

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
                "tags": ["Python", "PHP", "JavaScript", "jQuery"],
                "skills_demonstrated": [],
                "actions": [],
                "outcome": {"result": "Done"},
            }
        ]
        contact = ContactInfo(name="Test")
        skills_config = SkillsConfig(exclude=["PHP", "jQuery"])

        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
            skills_config=skills_config,
        )

        assert "PHP" not in resume.skills
        assert "jQuery" not in resume.skills
        assert "Python" in resume.skills
        assert "JavaScript" in resume.skills

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
                "tags": ["Python", "AWS"],
                "skills_demonstrated": ["Leadership", "Architecture"],
                "actions": [],
                "outcome": {"result": "Done"},
            }
        ]
        contact = ContactInfo(name="Test")
        skills_config = SkillsConfig()

        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
            skills_config=skills_config,
        )

        assert len(resume.skills) == 4
        lower_skills = [s.lower() for s in resume.skills]
        assert "python" in lower_skills
        assert "aws" in lower_skills
        assert "leadership" in lower_skills
        assert "architecture" in lower_skills

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

    def test_from_work_units_with_positions_groups_by_position(
        self, tmp_path: Path
    ) -> None:
        """Work units should be grouped by position_id."""

        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "1.0.0"
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

    def test_from_work_units_with_mixed_positions(
        self, tmp_path: Path
    ) -> None:
        """Work units with and without positions should both render."""

        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "1.0.0"
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

    def test_from_work_units_sorts_by_date_descending(
        self, tmp_path: Path
    ) -> None:
        """Experience items should be sorted by date (most recent first)."""

        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "1.0.0"
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

    def test_from_work_units_invalid_position_id_fallback(
        self, tmp_path: Path
    ) -> None:
        """Work units with invalid position_id should be treated as standalone."""

        positions_file = tmp_path / "positions.yaml"
        positions_file.write_text("""
schema_version: "1.0.0"
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
