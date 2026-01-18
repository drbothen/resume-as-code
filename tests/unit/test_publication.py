"""Tests for Publication model."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from resume_as_code.models.publication import Publication


class TestPublicationModel:
    """Tests for Publication model."""

    def test_minimal_publication(self) -> None:
        """Should create publication with required fields."""
        pub = Publication(
            title="My Talk",
            type="conference",
            venue="DEF CON",
            date="2022-08",
        )
        assert pub.title == "My Talk"
        assert pub.type == "conference"
        assert pub.venue == "DEF CON"
        assert pub.date == "2022-08"
        assert pub.url is None
        assert pub.display is True

    def test_full_publication(self) -> None:
        """Should create publication with all fields."""
        pub = Publication(
            title="Securing Industrial Control Systems at Scale",
            type="conference",
            venue="DEF CON 30",
            date="2022-08",
            url="https://example.com/talk",
            display=True,
        )
        assert pub.title == "Securing Industrial Control Systems at Scale"
        assert pub.type == "conference"
        assert pub.venue == "DEF CON 30"
        assert pub.date == "2022-08"
        assert str(pub.url) == "https://example.com/talk"
        assert pub.display is True

    def test_date_format_validation_valid_yyyy_mm(self) -> None:
        """Should accept YYYY-MM date format."""
        pub = Publication(title="Test", type="article", venue="Blog", date="2024-06")
        assert pub.date == "2024-06"

    def test_date_format_validation_invalid(self) -> None:
        """Should reject invalid date format."""
        with pytest.raises(ValidationError):
            Publication(title="Test", type="article", venue="Blog", date="invalid")

    def test_date_format_validation_invalid_partial(self) -> None:
        """Should reject invalid partial date format."""
        with pytest.raises(ValidationError):
            Publication(title="Test", type="article", venue="Blog", date="2024")

    def test_date_format_validation_day_format_normalized(self) -> None:
        """YYYY-MM-DD format should be normalized to YYYY-MM."""
        pub = Publication(title="Test", type="article", venue="Blog", date="2024-06-15")
        assert pub.date == "2024-06"

    def test_url_validation_valid(self) -> None:
        """Should accept valid URL."""
        pub = Publication(
            title="Test",
            type="article",
            venue="Blog",
            date="2024-06",
            url="https://example.com/article/123",
        )
        assert str(pub.url) == "https://example.com/article/123"

    def test_url_validation_invalid(self) -> None:
        """Should reject invalid URL."""
        with pytest.raises(ValidationError):
            Publication(
                title="Test",
                type="article",
                venue="Blog",
                date="2024-06",
                url="not-a-url",
            )

    def test_display_default_true(self) -> None:
        """Display should default to True."""
        pub = Publication(title="Test", type="article", venue="Blog", date="2024-06")
        assert pub.display is True

    def test_display_can_be_false(self) -> None:
        """Display can be set to False."""
        pub = Publication(title="Test", type="article", venue="Blog", date="2024-06", display=False)
        assert pub.display is False


class TestPublicationType:
    """Tests for publication type validation."""

    @pytest.mark.parametrize(
        "pub_type",
        ["conference", "article", "whitepaper", "book", "podcast", "webinar"],
    )
    def test_valid_publication_types(self, pub_type: str) -> None:
        """Should accept all valid publication types."""
        pub = Publication(title="Test", type=pub_type, venue="Venue", date="2024-06")
        assert pub.type == pub_type

    def test_invalid_publication_type(self) -> None:
        """Should reject invalid publication type."""
        with pytest.raises(ValidationError):
            Publication(title="Test", type="invalid_type", venue="Venue", date="2024-06")


class TestPublicationYear:
    """Tests for year property."""

    def test_year_extraction(self) -> None:
        """Should extract year from date."""
        pub = Publication(title="Test", type="conference", venue="Venue", date="2022-08")
        assert pub.year == "2022"

    def test_year_extraction_different_dates(self) -> None:
        """Should extract year correctly for various dates."""
        pub = Publication(title="Test", type="conference", venue="Venue", date="2019-01")
        assert pub.year == "2019"


class TestPublicationIsSpeaking:
    """Tests for is_speaking property."""

    @pytest.mark.parametrize("pub_type", ["conference", "podcast", "webinar"])
    def test_speaking_types_return_true(self, pub_type: str) -> None:
        """Speaking engagement types should return True."""
        pub = Publication(title="Test", type=pub_type, venue="Venue", date="2024-06")
        assert pub.is_speaking is True

    @pytest.mark.parametrize("pub_type", ["article", "whitepaper", "book"])
    def test_written_types_return_false(self, pub_type: str) -> None:
        """Written work types should return False."""
        pub = Publication(title="Test", type=pub_type, venue="Venue", date="2024-06")
        assert pub.is_speaking is False


class TestPublicationFormatDisplay:
    """Tests for format_display method."""

    def test_format_display_conference(self) -> None:
        """Should format conference as speaking engagement (AC #3)."""
        pub = Publication(
            title="Securing Industrial Control Systems",
            type="conference",
            venue="DEF CON 30",
            date="2022-08",
        )
        display = pub.format_display()
        # AC #3: Speaking format "Venue (Year) - Title"
        assert display == "DEF CON 30 (2022) - Securing Industrial Control Systems"

    def test_format_display_article(self) -> None:
        """Should format article as written work (AC #4)."""
        pub = Publication(
            title="Zero Trust Architecture Guide",
            type="article",
            venue="IEEE Security",
            date="2023-03",
        )
        display = pub.format_display()
        # AC #4: Written format "Title, Venue (Year)"
        assert display == "Zero Trust Architecture Guide, IEEE Security (2023)"

    def test_format_display_whitepaper(self) -> None:
        """Should format whitepaper as written work (AC #4)."""
        pub = Publication(
            title="Cloud Security Best Practices",
            type="whitepaper",
            venue="Company Blog",
            date="2021-06",
        )
        display = pub.format_display()
        # AC #4: Written format "Title, Venue (Year)"
        assert display == "Cloud Security Best Practices, Company Blog (2021)"

    def test_format_display_podcast(self) -> None:
        """Should format podcast as speaking engagement (AC #3)."""
        pub = Publication(
            title="Security Leadership",
            type="podcast",
            venue="Tech Talk Show",
            date="2024-01",
        )
        display = pub.format_display()
        # AC #3: Speaking format "Venue (Year) - Title"
        assert display == "Tech Talk Show (2024) - Security Leadership"

    def test_format_display_webinar(self) -> None:
        """Should format webinar as speaking engagement (AC #3)."""
        pub = Publication(
            title="Cloud Security Deep Dive",
            type="webinar",
            venue="AWS Online",
            date="2023-06",
        )
        display = pub.format_display()
        # AC #3: Speaking format "Venue (Year) - Title"
        assert display == "AWS Online (2023) - Cloud Security Deep Dive"

    def test_format_display_book(self) -> None:
        """Should format book as written work (AC #4)."""
        pub = Publication(
            title="The Art of Security",
            type="book",
            venue="O'Reilly Media",
            date="2022-11",
        )
        display = pub.format_display()
        # AC #4: Written format "Title, Venue (Year)"
        assert display == "The Art of Security, O'Reilly Media (2022)"


class TestResumeConfigPublications:
    """Tests for publications in ResumeConfig."""

    def test_publications_default_empty(self) -> None:
        """ResumeConfig should default to None for publications (Story 9.2).

        Note: Access publications via data_loader for actual usage.
        """
        from resume_as_code.models.config import ResumeConfig

        config = ResumeConfig()
        assert config.publications is None

    def test_publications_list(self) -> None:
        """ResumeConfig should accept publications list."""
        from resume_as_code.models.config import ResumeConfig

        config = ResumeConfig(
            publications=[
                Publication(title="Talk 1", type="conference", venue="Conf 1", date="2024-01"),
                Publication(title="Article 1", type="article", venue="Blog", date="2023-06"),
            ]
        )
        assert len(config.publications) == 2
        assert config.publications[0].title == "Talk 1"
        assert config.publications[1].title == "Article 1"

    def test_publications_from_dict(self) -> None:
        """ResumeConfig should parse publications from dict."""
        from resume_as_code.models.config import ResumeConfig

        config = ResumeConfig(
            publications=[
                {"title": "Talk 1", "type": "conference", "venue": "Conf 1", "date": "2024-01"},
                {"title": "Article 1", "type": "article", "venue": "Blog", "date": "2023-06"},
            ]
        )
        assert len(config.publications) == 2
        assert config.publications[0].title == "Talk 1"
        assert config.publications[1].type == "article"


class TestResumeDataPublications:
    """Tests for publications in ResumeData."""

    def test_resume_data_publications_default_empty(self) -> None:
        """ResumeData should default to empty publications list."""
        from resume_as_code.models.resume import ContactInfo, ResumeData

        data = ResumeData(contact=ContactInfo(name="Test User"))
        assert data.publications == []

    def test_resume_data_publications_list(self) -> None:
        """ResumeData should accept publications list."""
        from resume_as_code.models.resume import ContactInfo, ResumeData

        data = ResumeData(
            contact=ContactInfo(name="Test User"),
            publications=[
                Publication(title="Talk 1", type="conference", venue="Conf 1", date="2024-01"),
                Publication(title="Article 1", type="article", venue="Blog", date="2023-06"),
            ],
        )
        assert len(data.publications) == 2

    def test_get_sorted_publications_by_date(self) -> None:
        """Publications should sort by date descending."""
        from resume_as_code.models.resume import ContactInfo, ResumeData

        data = ResumeData(
            contact=ContactInfo(name="Test User"),
            publications=[
                Publication(title="Old Talk", type="conference", venue="Conf", date="2020-01"),
                Publication(title="Recent Talk", type="conference", venue="Conf", date="2024-06"),
                Publication(title="Middle Talk", type="conference", venue="Conf", date="2022-03"),
            ],
        )
        sorted_pubs = data.get_sorted_publications()
        assert sorted_pubs[0].title == "Recent Talk"
        assert sorted_pubs[1].title == "Middle Talk"
        assert sorted_pubs[2].title == "Old Talk"

    def test_get_sorted_publications_filters_display_false(self) -> None:
        """Publications with display=False should be filtered out."""
        from resume_as_code.models.resume import ContactInfo, ResumeData

        data = ResumeData(
            contact=ContactInfo(name="Test User"),
            publications=[
                Publication(
                    title="Hidden",
                    type="conference",
                    venue="Conf",
                    date="2024-01",
                    display=False,
                ),
                Publication(
                    title="Visible",
                    type="conference",
                    venue="Conf",
                    date="2023-01",
                    display=True,
                ),
            ],
        )
        sorted_pubs = data.get_sorted_publications()
        assert len(sorted_pubs) == 1
        assert sorted_pubs[0].title == "Visible"


class TestPublicationsTemplateRendering:
    """Tests for publications template rendering."""

    def test_executive_template_renders_publications(self) -> None:
        """Executive template should render publications section."""
        from resume_as_code.models.resume import ContactInfo, ResumeData
        from resume_as_code.services.template_service import TemplateService

        data = ResumeData(
            contact=ContactInfo(name="Test User"),
            publications=[
                Publication(
                    title="Securing Industrial Control Systems",
                    type="conference",
                    venue="DEF CON 30",
                    date="2022-08",
                    url="https://example.com/talk",
                ),
                Publication(
                    title="Zero Trust Architecture Guide",
                    type="article",
                    venue="IEEE Security",
                    date="2023-03",
                ),
            ],
        )

        template_service = TemplateService()
        html = template_service.render(data, template_name="executive")

        # Verify publications section renders
        assert "Publications &amp; Speaking" in html
        assert "Securing Industrial Control Systems" in html
        assert "DEF CON 30" in html
        assert "Zero Trust Architecture Guide" in html
        assert "IEEE Security" in html
        # Verify URL is clickable
        assert 'href="https://example.com/talk"' in html

        # AC #3: Speaking format "Venue (Year) - Title"
        # Conference should render as: "DEF CON 30 (2022) - Securing Industrial Control Systems"
        assert "DEF CON 30 (2022) -" in html

        # AC #4: Written format "Title, Venue (Year)"
        # Article should render as: "Zero Trust Architecture Guide, IEEE Security (2023)"
        assert "Zero Trust Architecture Guide" in html
        assert ", IEEE Security (2023)" in html

    def test_executive_template_no_publications_section_when_empty(self) -> None:
        """No publications section when no publications configured."""
        from resume_as_code.models.resume import ContactInfo, ResumeData
        from resume_as_code.services.template_service import TemplateService

        data = ResumeData(
            contact=ContactInfo(name="Test User"),
            publications=[],
        )

        template_service = TemplateService()
        html = template_service.render(data, template_name="executive")

        # Check that the section HTML element is not present
        # Note: "Publications" appears in CSS comments, so check for section tag
        assert '<section class="publications">' not in html

    def test_executive_template_hides_display_false_publications(self) -> None:
        """Publications with display=False should not appear in template."""
        from resume_as_code.models.resume import ContactInfo, ResumeData
        from resume_as_code.services.template_service import TemplateService

        data = ResumeData(
            contact=ContactInfo(name="Test User"),
            publications=[
                Publication(
                    title="Hidden Talk",
                    type="conference",
                    venue="Hidden Conf",
                    date="2024-01",
                    display=False,
                ),
            ],
        )

        template_service = TemplateService()
        html = template_service.render(data, template_name="executive")

        # No publications section should render since only one is hidden
        assert '<section class="publications">' not in html
        assert "Hidden Talk" not in html


class TestPublicationsLoadingFromConfig:
    """Tests for publications loading from config files."""

    def test_publications_load_from_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Publications should load from .resume.yaml file."""
        from resume_as_code.config import get_config, reset_config

        reset_config()
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
publications:
  - title: "Securing Industrial Control Systems at Scale"
    type: "conference"
    venue: "DEF CON 30"
    date: "2022-08"
    url: "https://example.com/talk"
  - title: "Zero Trust Architecture Implementation Guide"
    type: "whitepaper"
    venue: "Company Technical Blog"
    date: "2023-03"
"""
        )
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            assert len(config.publications) == 2
            assert config.publications[0].title == "Securing Industrial Control Systems at Scale"
            assert config.publications[0].type == "conference"
            assert config.publications[1].title == "Zero Trust Architecture Implementation Guide"
            assert config.publications[1].type == "whitepaper"

    def test_publications_empty_when_not_in_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Publications should be empty when not in config file."""
        from resume_as_code.config import get_config, reset_config

        reset_config()
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            # Story 9.2: config.publications is None when not in config
            # Use data_loader for actual access
            assert config.publications is None

    def test_publications_with_display_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Publications with display: false should load correctly."""
        from resume_as_code.config import get_config, reset_config

        reset_config()
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
publications:
  - title: "Old Talk"
    type: "conference"
    venue: "Old Conf"
    date: "2020-01"
    display: false
  - title: "New Talk"
    type: "conference"
    venue: "New Conf"
    date: "2024-01"
    display: true
"""
        )
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            assert len(config.publications) == 2
            assert config.publications[0].display is False
            assert config.publications[1].display is True


class TestPublicationTopicsAndAbstract:
    """Tests for topics and abstract fields added for JD curation (Story 8.2)."""

    def test_topics_default_empty(self) -> None:
        """Topics should default to empty list."""
        pub = Publication(title="Test", type="conference", venue="Conf", date="2024-01")
        assert pub.topics == []

    def test_topics_can_be_set(self) -> None:
        """Topics should accept a list of strings."""
        pub = Publication(
            title="Python Talk",
            type="conference",
            venue="PyCon",
            date="2024-01",
            topics=["python", "aws", "kubernetes"],
        )
        assert pub.topics == ["python", "aws", "kubernetes"]

    def test_abstract_default_none(self) -> None:
        """Abstract should default to None."""
        pub = Publication(title="Test", type="conference", venue="Conf", date="2024-01")
        assert pub.abstract is None

    def test_abstract_can_be_set(self) -> None:
        """Abstract should accept a string."""
        pub = Publication(
            title="Python Talk",
            type="conference",
            venue="PyCon",
            date="2024-01",
            abstract="A deep dive into Python best practices.",
        )
        assert pub.abstract == "A deep dive into Python best practices."


class TestPublicationGetNormalizedTopics:
    """Tests for get_normalized_topics method (Story 8.2)."""

    def test_returns_topics_without_registry(self) -> None:
        """Should return topics as-is when no registry provided."""
        pub = Publication(
            title="Test",
            type="conference",
            venue="Conf",
            date="2024-01",
            topics=["python", "K8s"],
        )
        assert pub.get_normalized_topics() == ["python", "K8s"]

    def test_normalizes_topics_with_registry(self) -> None:
        """Should normalize topics via SkillRegistry when provided."""
        from unittest.mock import MagicMock

        pub = Publication(
            title="Test",
            type="conference",
            venue="Conf",
            date="2024-01",
            topics=["k8s", "py", "AWS"],
        )

        mock_registry = MagicMock()
        mock_registry.normalize.side_effect = lambda x: {
            "k8s": "kubernetes",
            "py": "python",
            "AWS": "aws",
        }.get(x, x)

        normalized = pub.get_normalized_topics(mock_registry)
        assert normalized == ["kubernetes", "python", "aws"]

    def test_returns_empty_list_when_no_topics(self) -> None:
        """Should return empty list when no topics defined."""
        pub = Publication(title="Test", type="conference", venue="Conf", date="2024-01")
        assert pub.get_normalized_topics() == []


class TestPublicationGetTextForMatching:
    """Tests for get_text_for_matching method (Story 8.2)."""

    def test_combines_title_and_venue(self) -> None:
        """Should combine title and venue for matching."""
        pub = Publication(
            title="Kubernetes Best Practices",
            type="conference",
            venue="KubeCon 2024",
            date="2024-03",
        )
        text = pub.get_text_for_matching()
        assert "Kubernetes Best Practices" in text
        assert "KubeCon 2024" in text

    def test_includes_abstract_when_present(self) -> None:
        """Should include abstract in matching text."""
        pub = Publication(
            title="Python Talk",
            type="conference",
            venue="PyCon",
            date="2024-01",
            abstract="Deep dive into async Python and AWS Lambda patterns.",
        )
        text = pub.get_text_for_matching()
        assert "Python Talk" in text
        assert "PyCon" in text
        assert "async Python" in text
        assert "AWS Lambda" in text

    def test_excludes_abstract_when_none(self) -> None:
        """Should work without abstract."""
        pub = Publication(
            title="Security Talk",
            type="conference",
            venue="DEF CON",
            date="2024-08",
        )
        text = pub.get_text_for_matching()
        assert text == "Security Talk DEF CON"


class TestPublicationFormatDisplayWithAbstract:
    """Tests for format_display with abstract (Story 8.2)."""

    def test_format_display_without_abstract_by_default(self) -> None:
        """Should not include abstract by default."""
        pub = Publication(
            title="Python Talk",
            type="conference",
            venue="PyCon",
            date="2024-01",
            abstract="A deep dive into Python patterns.",
        )
        display = pub.format_display()
        assert "deep dive" not in display.lower()

    def test_format_display_with_abstract_when_requested(self) -> None:
        """Should include abstract when include_abstract=True."""
        pub = Publication(
            title="Python Talk",
            type="conference",
            venue="PyCon",
            date="2024-01",
            abstract="A deep dive into Python patterns.",
        )
        display = pub.format_display(include_abstract=True)
        assert "A deep dive into Python patterns." in display

    def test_format_display_with_abstract_no_abstract_set(self) -> None:
        """Should work when include_abstract=True but no abstract."""
        pub = Publication(
            title="Security Talk",
            type="conference",
            venue="DEF CON",
            date="2024-08",
        )
        display = pub.format_display(include_abstract=True)
        # Should just show normal display, no error
        assert display == "DEF CON (2024) - Security Talk"
