"""Integration tests for template rendering with real templates."""

from __future__ import annotations

from datetime import date

from resume_as_code.models.resume import (
    ContactInfo,
    ResumeBullet,
    ResumeData,
    ResumeItem,
    ResumeSection,
)
from resume_as_code.services.template_service import TemplateService


class TestEndToEndWorkUnitToHTML:
    """End-to-end tests: Work Unit dicts -> ResumeData -> HTML."""

    def test_work_units_to_html_modern_template(self) -> None:
        """Full pipeline: Work Unit dicts transform to rendered HTML."""
        # Simulate Work Units as they'd come from YAML files
        work_units = [
            {
                "id": "wu-2024-01-15-api-migration",
                "title": "Senior Software Engineer",
                "organization": "TechCorp Inc",
                "time_started": date(2022, 3, 1),
                "time_ended": date(2024, 1, 15),
                "actions": [
                    "Led migration of 200+ REST endpoints to GraphQL",
                    "Implemented caching layer reducing latency by 60%",
                    "Mentored team of 4 junior engineers",
                ],
                "outcome": {
                    "result": "Delivered new API platform serving 10M requests/day",
                    "quantified_impact": "40% reduction in p99 latency",
                },
                "tags": ["python", "graphql", "redis"],
                "skills_demonstrated": [
                    {"name": "API Design", "level": "expert"},
                    "Technical Leadership",
                ],
                "scope": {
                    "budget_managed": "$500K",
                    "team_size": 5,
                },
            },
            {
                "id": "wu-2022-02-28-startup",
                "title": "Full Stack Developer",
                "organization": "StartupXYZ",
                "time_started": date(2020, 6, 1),
                "time_ended": date(2022, 2, 28),
                "actions": [
                    "Built customer-facing dashboard from scratch",
                    "Integrated third-party payment processing",
                ],
                "outcome": {
                    "result": "Launched MVP that acquired 1000 paying customers",
                },
                "tags": ["react", "typescript", "postgres"],
                "skills_demonstrated": ["Full Stack Development"],
            },
        ]

        contact = ContactInfo(
            name="Jane Developer",
            email="jane@example.com",
            phone="555-0123",
            location="San Francisco, CA",
            linkedin="https://linkedin.com/in/janedev",
        )

        # Transform Work Units to ResumeData
        resume = ResumeData.from_work_units(
            work_units=work_units,
            contact=contact,
            summary="Senior engineer with 5+ years building scalable systems.",
        )

        # Render to HTML
        service = TemplateService()
        html = service.render(resume, "modern")

        # Verify contact info rendered
        assert "Jane Developer" in html
        assert "jane@example.com" in html
        assert "San Francisco, CA" in html

        # Verify summary rendered
        assert "Senior engineer with 5+ years" in html

        # Verify Work Unit data transformed and rendered
        assert "Senior Software Engineer" in html
        assert "TechCorp Inc" in html
        assert "Mar 2022" in html  # Formatted date
        assert "Delivered new API platform" in html  # Outcome bullet

        # Verify skills extracted and rendered
        assert "python" in html
        assert "graphql" in html
        assert "API Design" in html

    def test_work_units_to_html_executive_template_with_scope(self) -> None:
        """Executive template renders scope indicators from Work Units."""
        work_units = [
            {
                "id": "wu-2024-01-01-vp-eng",
                "title": "VP of Engineering",
                "organization": "Enterprise Corp",
                "time_started": date(2021, 1, 1),
                "time_ended": None,
                "actions": ["Directed engineering strategy"],
                "outcome": {
                    "result": "Scaled engineering organization",
                    "quantified_impact": "from 20 to 80 engineers",
                },
                "tags": [],
                "skills_demonstrated": [],
                "scope": {
                    "budget_managed": "$10M",
                    "team_size": 80,
                    "revenue_influenced": "$50M ARR",
                },
            }
        ]

        contact = ContactInfo(name="Executive Leader")
        resume = ResumeData.from_work_units(work_units, contact)

        service = TemplateService()
        html = service.render(resume, "executive")

        # Verify scope indicators rendered
        assert "Budget:" in html
        assert "$10M" in html
        assert "Team:" in html
        assert "80 people" in html
        assert "Revenue:" in html
        assert "$50M ARR" in html

    def test_work_units_to_html_ats_safe_template(self) -> None:
        """ATS-safe template renders Work Unit data with standard formatting."""
        work_units = [
            {
                "id": "wu-2024-01-01-test",
                "title": "Software Engineer",
                "organization": "Tech Company",
                "time_started": "2023-01-15",
                "time_ended": "2024-06-30",
                "actions": ["Developed features", "Fixed bugs"],
                "outcome": {"result": "Improved system reliability"},
                "tags": ["java", "spring"],
                "skills_demonstrated": ["Backend Development"],
            }
        ]

        contact = ContactInfo(
            name="Test Candidate",
            email="test@example.com",
            phone="555-9999",
        )
        resume = ResumeData.from_work_units(work_units, contact)

        service = TemplateService()
        html = service.render(resume, "ats-safe")

        # Verify ATS-friendly uppercase headers
        assert "EXPERIENCE" in html
        assert "SKILLS" in html

        # Verify content rendered
        assert "Software Engineer" in html
        assert "Tech Company" in html
        assert "java | spring" in html or "java" in html  # Skills as pipe-separated


class TestATSSafeTemplateIntegration:
    """Integration tests for ATS-safe template rendering."""

    def test_ats_safe_template_exists(self) -> None:
        """ATS-safe template is discovered by template service."""
        service = TemplateService()
        templates = service.list_templates()
        assert "ats-safe" in templates

    def test_ats_safe_template_uses_standard_section_headers(self) -> None:
        """ATS-safe template uses standard uppercase section headers."""
        service = TemplateService()
        contact = ContactInfo(name="Test Candidate")
        resume = ResumeData(
            contact=contact,
            summary="Experienced professional.",
            sections=[
                ResumeSection(title="Experience", items=[]),
            ],
            skills=["Python", "SQL"],
        )

        html = service.render(resume, "ats-safe")

        # Standard ATS-recognizable headers in uppercase
        assert "PROFESSIONAL SUMMARY" in html
        assert "SKILLS" in html
        assert "EXPERIENCE" in html

    def test_ats_safe_template_single_column_layout(self) -> None:
        """ATS-safe template uses simple single-column structure."""
        service = TemplateService()

        # ATS-safe CSS should not use flex or grid layouts
        css = service.get_css("ats-safe")
        assert "flex" not in css, "ATS-safe CSS should not use flexbox"
        assert "grid" not in css, "ATS-safe CSS should not use CSS grid"

    def test_ats_safe_template_renders_contact_inline(self) -> None:
        """ATS-safe template renders contact info on single line with separators."""
        service = TemplateService()
        contact = ContactInfo(
            name="Test Candidate",
            email="test@example.com",
            phone="555-1234",
            location="New York, NY",
        )
        resume = ResumeData(contact=contact)

        html = service.render(resume, "ats-safe")

        assert "test@example.com" in html
        assert "555-1234" in html
        assert "New York, NY" in html
        # Contact items separated by pipe
        assert "|" in html

    def test_ats_safe_template_renders_skills_inline(self) -> None:
        """ATS-safe template renders skills as pipe-separated list."""
        service = TemplateService()
        contact = ContactInfo(name="Test Candidate")
        resume = ResumeData(
            contact=contact,
            skills=["Python", "JavaScript", "SQL"],
        )

        html = service.render(resume, "ats-safe")

        # Skills should be separated by pipes for ATS parsing
        assert "Python | JavaScript | SQL" in html

    def test_ats_safe_css_minimal_formatting(self) -> None:
        """ATS-safe CSS has minimal decorative elements."""
        service = TemplateService()
        css = service.get_css("ats-safe")

        assert len(css) > 0
        # Uses standard system fonts
        assert "Arial" in css
        # No complex layouts
        assert "flex" not in css
        assert "grid" not in css

    def test_ats_safe_template_valid_html_structure(self) -> None:
        """ATS-safe template produces valid HTML structure."""
        service = TemplateService()
        contact = ContactInfo(name="Test Candidate")
        resume = ResumeData(contact=contact)

        html = service.render(resume, "ats-safe")

        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html


class TestExecutiveTemplateIntegration:
    """Integration tests for executive template rendering."""

    def test_executive_template_exists(self) -> None:
        """Executive template is discovered by template service."""
        service = TemplateService()
        templates = service.list_templates()
        assert "executive" in templates

    def test_executive_template_renders_scope_indicators(self) -> None:
        """Executive template renders scope indicators (budget, team, revenue)."""
        service = TemplateService()
        contact = ContactInfo(name="Executive Leader")
        resume = ResumeData(
            contact=contact,
            sections=[
                ResumeSection(
                    title="Experience",
                    items=[
                        ResumeItem(
                            title="VP of Engineering",
                            organization="Enterprise Corp",
                            scope_budget="$5M",
                            scope_team_size=25,
                            scope_revenue="$100M ARR",
                            bullets=[
                                ResumeBullet(text="Led digital transformation"),
                            ],
                        )
                    ],
                )
            ],
        )

        html = service.render(resume, "executive")

        # Verify scope indicators are rendered
        assert "Budget:" in html
        assert "$5M" in html
        assert "Team:" in html
        assert "25 people" in html
        assert "Revenue:" in html
        assert "$100M ARR" in html

    def test_executive_template_executive_summary_section(self) -> None:
        """Executive template renders Executive Summary section."""
        service = TemplateService()
        contact = ContactInfo(name="Executive Leader")
        resume = ResumeData(
            contact=contact,
            summary="Transformational technology executive with 20+ years.",
        )

        html = service.render(resume, "executive")

        assert "Executive Summary" in html
        assert "Transformational technology executive" in html

    def test_executive_template_renders_metrics_inline(self) -> None:
        """Executive template renders metrics inline with achievement text."""
        service = TemplateService()
        contact = ContactInfo(name="Executive Leader")
        resume = ResumeData(
            contact=contact,
            sections=[
                ResumeSection(
                    title="Experience",
                    items=[
                        ResumeItem(
                            title="CTO",
                            bullets=[
                                ResumeBullet(
                                    text="Scaled engineering organization",
                                    metrics="from 50 to 200 engineers in 18 months",
                                ),
                            ],
                        )
                    ],
                )
            ],
        )

        html = service.render(resume, "executive")

        assert "Scaled engineering organization" in html
        assert "from 50 to 200 engineers" in html

    def test_executive_template_core_competencies(self) -> None:
        """Executive template renders skills as Core Competencies."""
        service = TemplateService()
        contact = ContactInfo(name="Executive Leader")
        resume = ResumeData(
            contact=contact,
            skills=["Strategic Planning", "Team Leadership", "Digital Transformation"],
        )

        html = service.render(resume, "executive")

        assert "Core Competencies" in html
        assert "Strategic Planning" in html
        assert "Team Leadership" in html

    def test_executive_css_has_scope_styling(self) -> None:
        """Executive CSS includes scope indicator styling."""
        service = TemplateService()
        css = service.get_css("executive")

        assert ".scope-indicators" in css
        assert ".scope-item" in css
        assert ".scope-label" in css
        assert ".scope-value" in css

    def test_executive_template_valid_html_structure(self) -> None:
        """Executive template produces valid HTML structure."""
        service = TemplateService()
        contact = ContactInfo(name="Executive Leader")
        resume = ResumeData(contact=contact)

        html = service.render(resume, "executive")

        assert "<!DOCTYPE html>" in html
        assert "Executive Resume" in html


class TestModernTemplateIntegration:
    """Integration tests for modern template rendering."""

    def test_modern_template_exists(self) -> None:
        """Modern template is discovered by template service."""
        service = TemplateService()
        templates = service.list_templates()
        assert "modern" in templates

    def test_modern_template_renders_contact_info(self) -> None:
        """Modern template renders contact information."""
        service = TemplateService()
        contact = ContactInfo(
            name="Jane Developer",
            email="jane@example.com",
            phone="555-1234",
            location="San Francisco, CA",
        )
        resume = ResumeData(contact=contact)

        html = service.render(resume, "modern")

        assert "Jane Developer" in html
        assert "jane@example.com" in html
        assert "555-1234" in html
        assert "San Francisco, CA" in html

    def test_modern_template_renders_links(self) -> None:
        """Modern template renders social links."""
        service = TemplateService()
        contact = ContactInfo(
            name="Jane Developer",
            linkedin="https://linkedin.com/in/janedev",
            github="https://github.com/janedev",
            website="https://janedev.com",
        )
        resume = ResumeData(contact=contact)

        html = service.render(resume, "modern")

        assert "linkedin.com/in/janedev" in html
        assert "github.com/janedev" in html
        assert "janedev.com" in html

    def test_modern_template_renders_summary(self) -> None:
        """Modern template renders professional summary."""
        service = TemplateService()
        contact = ContactInfo(name="Jane Developer")
        resume = ResumeData(
            contact=contact,
            summary="Experienced software engineer with 10+ years of Python expertise.",
        )

        html = service.render(resume, "modern")

        assert "Summary" in html
        assert "Experienced software engineer" in html

    def test_modern_template_renders_experience_section(self) -> None:
        """Modern template renders experience section with bullets."""
        service = TemplateService()
        contact = ContactInfo(name="Jane Developer")
        resume = ResumeData(
            contact=contact,
            sections=[
                ResumeSection(
                    title="Experience",
                    items=[
                        ResumeItem(
                            title="Senior Engineer",
                            organization="TechCorp",
                            location="Remote",
                            start_date="Jan 2022",
                            end_date="Present",
                            bullets=[
                                ResumeBullet(
                                    text="Led platform migration to Kubernetes",
                                    metrics="reduced deployment time by 75%",
                                ),
                                ResumeBullet(text="Mentored 5 junior engineers"),
                            ],
                        )
                    ],
                )
            ],
        )

        html = service.render(resume, "modern")

        assert "Experience" in html
        assert "Senior Engineer" in html
        assert "TechCorp" in html
        assert "Remote" in html
        assert "Jan 2022" in html
        assert "Present" in html
        assert "Led platform migration to Kubernetes" in html
        assert "reduced deployment time by 75%" in html
        assert "Mentored 5 junior engineers" in html

    def test_modern_template_renders_education(self) -> None:
        """Modern template renders education section."""
        service = TemplateService()
        contact = ContactInfo(name="Jane Developer")
        resume = ResumeData(
            contact=contact,
            education=[
                ResumeItem(
                    title="BS Computer Science",
                    organization="State University",
                    start_date="2010",
                    end_date="2014",
                )
            ],
        )

        html = service.render(resume, "modern")

        assert "Education" in html
        assert "BS Computer Science" in html
        assert "State University" in html
        assert "2014" in html

    def test_modern_template_renders_skills(self) -> None:
        """Modern template renders skills list."""
        service = TemplateService()
        contact = ContactInfo(name="Jane Developer")
        resume = ResumeData(
            contact=contact,
            skills=["Python", "TypeScript", "Kubernetes", "AWS", "PostgreSQL"],
        )

        html = service.render(resume, "modern")

        assert "Skills" in html
        assert "Python" in html
        assert "TypeScript" in html
        assert "Kubernetes" in html

    def test_modern_template_valid_html_structure(self) -> None:
        """Modern template produces valid HTML structure."""
        service = TemplateService()
        contact = ContactInfo(name="Jane Developer")
        resume = ResumeData(contact=contact)

        html = service.render(resume, "modern")

        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "<head>" in html
        assert "</head>" in html
        assert "<body>" in html
        assert "</body>" in html
        assert "<title>" in html

    def test_modern_css_exists(self) -> None:
        """Modern CSS file exists and has content."""
        service = TemplateService()
        css = service.get_css("modern")

        assert len(css) > 0
        assert "@page" in css  # Page setup for printing
        assert "font-family" in css
        assert "@media print" in css  # Print-friendly styles

    def test_modern_template_escapes_html_special_chars(self) -> None:
        """Modern template escapes HTML special characters."""
        service = TemplateService()
        contact = ContactInfo(name="Test <script>alert('xss')</script>")
        resume = ResumeData(contact=contact)

        html = service.render(resume, "modern")

        # Script tag should be escaped
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
