# Epic 8: Resume Template Enhancements

**Goal:** Improve resume template rendering for better visual presentation and professional formatting

**User Outcome:** Users get professionally formatted resumes that follow industry best practices for grouping related content, particularly for candidates with multiple roles at the same employer

**Priority:** P2
**Total Points:** 5 (initial)

---

## Story 8.1: Employer-Grouped Position Rendering

As a **job seeker with multiple roles at the same company**,
I want **positions at the same employer to be nested under a single employer heading**,
So that **my resume shows career progression within a company rather than appearing as separate unrelated jobs**.

**Story Points:** 5
**Priority:** P2

**Problem Statement:**
When a candidate has held multiple positions at the same employer (e.g., promotions, role changes), the current template renders each position as a completely separate entry with the employer name repeated. This:
- Wastes valuable resume space
- Fails to show career progression
- Makes it harder for recruiters to see internal promotions
- Looks unprofessional compared to industry-standard resume formats

**Example - Current (Incorrect) Rendering:**
```
Burns & McDonnell - Cybersecurity Practice Lead (2018-2020)
• Achievement 1
• Achievement 2

Burns & McDonnell - Senior Security Consultant (2016-2018)
• Achievement 3
• Achievement 4

Burns & McDonnell - Security Consultant (2015-2016)
• Achievement 5
```

**Example - Desired Rendering:**
```
Burns & McDonnell (2015-2020)

  Cybersecurity Practice Lead (2018-2020)
  • Achievement 1
  • Achievement 2

  Senior Security Consultant (2016-2018)
  • Achievement 3
  • Achievement 4

  Security Consultant (2015-2016)
  • Achievement 5
```

**Acceptance Criteria:**

**Given** a resume with multiple positions at the same employer
**When** rendering to PDF or DOCX
**Then** positions are grouped under a single employer heading
**And** the employer's total tenure is shown (earliest start to latest end)
**And** each role is listed with its own dates and bullets

**Given** positions at the same employer
**When** grouping positions
**Then** employer matching is case-insensitive
**And** minor variations are normalized (e.g., "Burns & McDonnell" vs "Burns and McDonnell")

**Given** a grouped employer section
**When** rendering
**Then** roles are listed in reverse chronological order (most recent first)
**And** each role's title and dates are clearly visible
**And** bullets for each role are indented under that role

**Given** positions with scope data (team size, budget, etc.)
**When** rendering a grouped employer section
**Then** scope data is shown at the role level, not employer level

**Given** a mix of single-position and multi-position employers
**When** rendering the resume
**Then** single-position employers render normally (employer + title on one line)
**And** multi-position employers use the grouped format

**Given** the template configuration
**When** `group_employer_positions: false` is set
**Then** original separate rendering is used (backward compatible)

**Technical Notes:**
```python
# src/resume_as_code/models/resume.py

from dataclasses import dataclass, field
from typing import Literal

@dataclass
class EmployerGroup:
    """Group of positions at the same employer."""
    employer: str
    location: str | None
    total_start_date: str  # Earliest position start
    total_end_date: str | None  # Latest position end (None = current)
    positions: list[ResumeItem]  # Ordered by date (most recent first)

    @property
    def is_multi_position(self) -> bool:
        """True if employer has multiple positions."""
        return len(self.positions) > 1

    @property
    def tenure_display(self) -> str:
        """Format total tenure for display."""
        end = self.total_end_date or "Present"
        return f"{self.total_start_date} - {end}"


def group_positions_by_employer(items: list[ResumeItem]) -> list[EmployerGroup]:
    """Group resume items by normalized employer name.

    Args:
        items: List of ResumeItem, each representing a position.

    Returns:
        List of EmployerGroup, maintaining overall chronological order.
    """
    from collections import defaultdict

    # Normalize employer names for grouping
    def normalize_employer(name: str) -> str:
        # Lowercase, normalize ampersands, strip common suffixes
        normalized = name.lower()
        normalized = normalized.replace(" & ", " and ")
        normalized = normalized.replace("&", " and ")
        # Remove common suffixes like Inc, LLC, Corp
        for suffix in [", inc", ", llc", ", corp", " inc", " llc", " corp"]:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
        return normalized.strip()

    # Group by normalized employer
    employer_groups: dict[str, list[ResumeItem]] = defaultdict(list)
    employer_canonical: dict[str, str] = {}  # normalized -> original (first seen)

    for item in items:
        key = normalize_employer(item.employer)
        employer_groups[key].append(item)
        if key not in employer_canonical:
            employer_canonical[key] = item.employer

    # Build EmployerGroup objects
    result: list[EmployerGroup] = []

    for key, positions in employer_groups.items():
        # Sort positions by date (most recent first)
        positions.sort(key=lambda p: p.start_date or "", reverse=True)

        # Calculate total tenure
        start_dates = [p.start_date for p in positions if p.start_date]
        end_dates = [p.end_date for p in positions if p.end_date]

        total_start = min(start_dates) if start_dates else ""
        # If any position has no end_date, the group is current
        has_current = any(p.end_date is None for p in positions)
        total_end = None if has_current else (max(end_dates) if end_dates else None)

        result.append(EmployerGroup(
            employer=employer_canonical[key],
            location=positions[0].location if positions else None,
            total_start_date=total_start,
            total_end_date=total_end,
            positions=positions,
        ))

    # Sort groups by most recent position's start date
    result.sort(key=lambda g: g.positions[0].start_date or "", reverse=True)

    return result
```

**Template Changes:**
```html
{# templates/modern.html - Updated experience section #}
{% for group in employer_groups %}
  {% if group.is_multi_position %}
    {# Multi-position employer - grouped format #}
    <div class="employer-group">
      <div class="employer-header">
        <h3 class="employer-name">{{ group.employer }}</h3>
        <span class="employer-tenure">{{ group.tenure_display }}</span>
        {% if group.location %}
          <span class="employer-location">{{ group.location }}</span>
        {% endif %}
      </div>

      {% for position in group.positions %}
        <div class="position-entry nested">
          <div class="position-header">
            <h4 class="position-title">{{ position.title }}</h4>
            <span class="position-dates">{{ position.date_range }}</span>
          </div>
          {% if position.scope_line %}
            <div class="scope-line">{{ position.scope_line }}</div>
          {% endif %}
          <ul class="bullets">
            {% for bullet in position.bullets %}
              <li>{{ bullet.text }}</li>
            {% endfor %}
          </ul>
        </div>
      {% endfor %}
    </div>
  {% else %}
    {# Single-position employer - standard format #}
    {% set position = group.positions[0] %}
    <div class="position-entry">
      <div class="position-header">
        <h3>{{ group.employer }}</h3>
        <span class="position-title">{{ position.title }}</span>
        <span class="position-dates">{{ position.date_range }}</span>
        {% if position.location %}
          <span class="position-location">{{ position.location }}</span>
        {% endif %}
      </div>
      {% if position.scope_line %}
        <div class="scope-line">{{ position.scope_line }}</div>
      {% endif %}
      <ul class="bullets">
        {% for bullet in position.bullets %}
          <li>{{ bullet.text }}</li>
        {% endfor %}
      </ul>
    </div>
  {% endif %}
{% endfor %}
```

**CSS Additions:**
```css
/* Employer group styling */
.employer-group {
    margin-bottom: 1.5em;
}

.employer-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    border-bottom: 1px solid #ccc;
    padding-bottom: 0.25em;
    margin-bottom: 0.5em;
}

.employer-name {
    font-weight: bold;
    font-size: 1.1em;
}

.employer-tenure {
    font-style: italic;
    color: #666;
}

.position-entry.nested {
    margin-left: 1em;
    padding-left: 1em;
    border-left: 2px solid #e0e0e0;
    margin-bottom: 1em;
}

.position-entry.nested .position-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
}

.position-entry.nested .position-title {
    font-weight: 600;
    font-size: 1em;
}

.position-entry.nested .position-dates {
    font-size: 0.9em;
    color: #666;
}
```

**Config Extension:**
```yaml
# .resume.yaml
template_options:
  group_employer_positions: true  # Default: true (enable grouping)
```

**Files to Create/Modify:**
- Modify: `src/resume_as_code/models/resume.py` (add EmployerGroup, grouping logic)
- Modify: `src/resume_as_code/templates/modern.html` (grouped rendering)
- Modify: `src/resume_as_code/templates/modern.css` (nested position styling)
- Modify: `src/resume_as_code/templates/cto.html` (grouped rendering)
- Modify: `src/resume_as_code/templates/cto-results.html` (grouped rendering)
- Modify: `src/resume_as_code/models/config.py` (add template_options.group_employer_positions)
- Modify: `src/resume_as_code/services/template_service.py` (pass grouped data to templates)

**Definition of Done:**
- [ ] EmployerGroup dataclass with grouping logic
- [ ] Employer name normalization (case, ampersands, suffixes)
- [ ] Positions sorted by date within each group
- [ ] Total tenure calculated per employer group
- [ ] Template renders grouped format for multi-position employers
- [ ] Template renders standard format for single-position employers
- [ ] `group_employer_positions` config option (default: true)
- [ ] Setting `group_employer_positions: false` uses original rendering
- [ ] All template variants updated (modern, cto, cto-results)
- [ ] CSS styling for nested positions
- [ ] Unit tests for employer grouping logic
- [ ] Integration tests for grouped rendering

---
