"""Template service for resume rendering."""

from __future__ import annotations

from difflib import get_close_matches
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape

from resume_as_code.models.errors import RenderError
from resume_as_code.models.resume import ResumeData, group_positions_by_employer

if TYPE_CHECKING:
    from resume_as_code.models.config import ResumeConfig


class TemplateService:
    """Service for rendering resumes with Jinja2 templates."""

    def __init__(
        self,
        templates_dir: Path | None = None,
        custom_templates_dir: Path | None = None,
        builtin_templates_dir: Path | None = None,
    ) -> None:
        """Initialize template service.

        Args:
            templates_dir: Path to templates directory (backwards compatibility).
                If provided alone, used as builtin_templates_dir.
            custom_templates_dir: Path to custom templates directory.
                Templates here take precedence over builtin templates.
            builtin_templates_dir: Path to builtin templates directory.
                If None, uses the default templates directory in the package.

        The template search order is: custom_templates_dir, then builtin_templates_dir.
        This allows custom templates to override or supplement builtin templates (Story 11.3).
        """
        # Handle backwards compatibility: templates_dir alone = builtin only
        if templates_dir is not None and builtin_templates_dir is None:
            builtin_templates_dir = templates_dir

        if builtin_templates_dir is None:
            builtin_templates_dir = Path(__file__).parent.parent / "templates"

        self.builtin_templates_dir = builtin_templates_dir
        self.custom_templates_dir = custom_templates_dir

        # Backwards compatibility: keep templates_dir pointing to builtin
        self.templates_dir = builtin_templates_dir

        # Build loader list: custom first (higher priority), then builtin
        loader_paths: list[str] = []
        if custom_templates_dir and custom_templates_dir.exists():
            loader_paths.append(str(custom_templates_dir))
        loader_paths.append(str(builtin_templates_dir))

        self.env = Environment(
            loader=FileSystemLoader(loader_paths),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def list_templates(self) -> list[str]:
        """List available template names from all directories.

        Returns names of all HTML templates in both custom and builtin directories,
        excluding partials (files starting with underscore). Templates are
        deduplicated (custom templates can override builtin templates).

        Returns:
            Sorted list of template names (without .html extension).
        """
        templates: set[str] = set()

        # Add custom templates first (if directory exists)
        if self.custom_templates_dir and self.custom_templates_dir.exists():
            for path in self.custom_templates_dir.glob("*.html"):
                if not path.name.startswith("_"):  # Skip partials
                    templates.add(path.stem)

        # Add builtin templates
        if self.builtin_templates_dir.exists():
            for path in self.builtin_templates_dir.glob("*.html"):
                if not path.name.startswith("_"):  # Skip partials
                    templates.add(path.stem)

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
            RenderError: If template doesn't exist (with helpful suggestions).
        """
        try:
            template = self.env.get_template(f"{template_name}.html")
        except TemplateNotFound:
            # Provide helpful error message with available templates (Story 11.3 AC: #5)
            available = self.list_templates()
            suggestion_parts: list[str] = []

            # Check for close match (typo detection)
            close_matches = get_close_matches(template_name, available, n=1, cutoff=0.6)
            if close_matches:
                suggestion_parts.append(f"Did you mean '{close_matches[0]}'?")

            # List all available templates
            suggestion_parts.append(f"Available templates: {', '.join(available)}")

            raise RenderError(
                message=f"Template '{template_name}' not found",
                suggestion=" ".join(suggestion_parts),
            ) from None

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
    #
    # NOTE: Custom templates (Story 11.3) that extend builtin templates via
    # Jinja2 {% extends %} get HTML inheritance automatically, but CSS inheritance
    # requires registration here. Custom templates not in this map will only load
    # their own CSS file (if present) without inheriting parent CSS styles.
    # To add CSS inheritance for custom templates, extend this dict programmatically
    # or copy the parent CSS into your custom template's CSS file.
    _css_inheritance: dict[str, str] = {
        "cto": "executive",
        "cto-results": "cto",
    }

    def _find_css(self, name: str) -> Path | None:
        """Find CSS file in custom or builtin directory.

        Checks custom directory first (if configured), then falls back to builtin.
        This allows custom CSS to override builtin CSS for the same template name.

        Args:
            name: Template name (without .css extension).

        Returns:
            Path to CSS file if found, None otherwise.
        """
        # Custom directory first
        if self.custom_templates_dir and self.custom_templates_dir.exists():
            custom_css = self.custom_templates_dir / f"{name}.css"
            if custom_css.exists():
                return custom_css
        # Builtin fallback
        builtin_css = self.builtin_templates_dir / f"{name}.css"
        if builtin_css.exists():
            return builtin_css
        return None

    def get_css(self, template_name: str = "modern") -> str:
        """Get CSS for a template, including inherited base styles.

        For templates that extend another template (e.g., cto extends executive),
        the parent CSS is loaded first, then the child's CSS additions are appended.
        Inheritance is followed recursively, so cto-results → cto → executive
        will load executive.css, then cto.css, then cto-results.css.

        CSS is loaded from custom directory first, then builtin directory.
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
            css_path = self._find_css(ancestor)
            if css_path:
                css_parts.append(css_path.read_text())

        # Load template-specific CSS
        css_path = self._find_css(template_name)
        if css_path:
            css_parts.append(css_path.read_text())

        return "\n".join(css_parts)
