"""Unit tests for Resume data models."""

from __future__ import annotations

from datetime import date

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
                ResumeItem(
                    title="BS Computer Science",
                    organization="State University",
                    start_date="2010",
                    end_date="2014",
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
