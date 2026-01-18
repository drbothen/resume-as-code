"""Template service for resume rendering."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, select_autoescape

from resume_as_code.models.resume import ResumeData, group_positions_by_employer

if TYPE_CHECKING:
    from resume_as_code.models.config import ResumeConfig


class TemplateService:
    """Service for rendering resumes with Jinja2 templates."""

    def __init__(self, templates_dir: Path | None = None) -> None:
        """Initialize template service.

        Args:
            templates_dir: Path to templates directory. If None, uses
                the default templates directory in the package.
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "templates"

        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def list_templates(self) -> list[str]:
        """List available template names.

        Returns names of all HTML templates in the templates directory,
        excluding partials (files starting with underscore).

        Returns:
            Sorted list of template names (without .html extension).
        """
        templates: list[str] = []
        if not self.templates_dir.exists():
            return templates

        for path in self.templates_dir.glob("*.html"):
            if not path.name.startswith("_"):  # Skip partials
                templates.append(path.stem)
        return sorted(templates)

    def render(
        self,
        resume: ResumeData,
        template_name: str = "modern",
        config: ResumeConfig | None = None,
    ) -> str:
        """Render resume to HTML.

        Args:
            resume: ResumeData instance to render.
            template_name: Name of template (without .html extension).
            config: Optional ResumeConfig to control rendering options.

        Returns:
            Rendered HTML string.

        Raises:
            jinja2.TemplateNotFound: If template doesn't exist.
        """
        template = self.env.get_template(f"{template_name}.html")
        css = self.get_css(template_name)

        # Compute employer groups if enabled (Story 8.1)
        employer_groups = None
        group_enabled = config is None or config.template_options.group_employer_positions
        if group_enabled:
            experience_section = next((s for s in resume.sections if s.title == "Experience"), None)
            if experience_section:
                employer_groups = group_positions_by_employer(experience_section.items)

        return template.render(resume=resume, css=css, employer_groups=employer_groups)

    # Template inheritance map for CSS loading (Story 6.17: CTO template)
    # Child templates that extend a parent should inherit parent CSS
    # Chain is followed recursively: cto-results → cto → executive
    _css_inheritance: dict[str, str] = {
        "cto": "executive",
        "cto-results": "cto",
    }

    def get_css(self, template_name: str = "modern") -> str:
        """Get CSS for a template, including inherited base styles.

        For templates that extend another template (e.g., cto extends executive),
        the parent CSS is loaded first, then the child's CSS additions are appended.
        Inheritance is followed recursively, so cto-results → cto → executive
        will load executive.css, then cto.css, then cto-results.css.

        This ensures AC #7: templates share the same CSS base styling.

        Args:
            template_name: Name of template (without .css extension).

        Returns:
            CSS content (base + template-specific), or empty string if no CSS exists.
        """
        css_parts: list[str] = []

        # Build inheritance chain by following parent links recursively
        chain: list[str] = []
        current = template_name
        while current in self._css_inheritance:
            parent = self._css_inheritance[current]
            chain.append(parent)
            current = parent

        # Load CSS in order from root parent to current template
        for ancestor in reversed(chain):
            ancestor_css_path = self.templates_dir / f"{ancestor}.css"
            if ancestor_css_path.exists():
                css_parts.append(ancestor_css_path.read_text())

        # Load template-specific CSS
        css_path = self.templates_dir / f"{template_name}.css"
        if css_path.exists():
            css_parts.append(css_path.read_text())

        return "\n".join(css_parts)
