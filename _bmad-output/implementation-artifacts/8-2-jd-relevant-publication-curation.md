# Story 8.2: JD-Relevant Publication Curation

Status: done

## Story

As a **technical leader with many publications and speaking engagements**,
I want **publications to be filtered by JD relevance during resume generation**,
So that **my resume shows only the most relevant thought leadership for the target role instead of a complete list that dilutes impact**.

## Acceptance Criteria

1. **Given** Publication model **When** creating a publication **Then** `topics: list[str]` and `abstract: str | None` fields are available **And** topics integrate with SkillRegistry for normalization

2. **Given** publications configured in `.resume.yaml` **When** running `resume build` with a JD **Then** publications are scored against JD relevance **And** only top N are included on the resume

3. **Given** a publication **When** scoring against JD **Then** scoring uses:
   - 40% semantic similarity (abstract + title + venue vs JD)
   - 40% topic overlap with JD skills/keywords (normalized via SkillRegistry)
   - 20% recency bonus (recent publications preferred)

4. **Given** publication scoring **When** a publication scores below `min_relevance_score` threshold **Then** publication is excluded regardless of limit

5. **Given** publications on the resume **When** rendering **Then** publications are sorted by relevance score descending (not by date)

6. **Given** no JD is provided (e.g., `resume build` without `--jd`) **When** generating resume **Then** fallback to date-sorted display (existing behavior)

7. **Given** configuration **When** `curation.publications_max` is set **Then** limit is respected **And** default is 3

8. **Given** `resume new publication` command **When** creating publication **Then** user can specify topics and abstract

## Tasks / Subtasks

- [x] Task 1: Enhance Publication model with topics and abstract (AC: #1)
  - [x] 1.1 Add `topics: list[str] = Field(default_factory=list)` to Publication model
  - [x] 1.2 Add `abstract: str | None = Field(default=None, max_length=500)` to Publication model
  - [x] 1.3 Add `get_normalized_topics()` method that uses SkillRegistry
  - [x] 1.4 Update Publication.format_display() to optionally include abstract preview

- [x] Task 2: Update publication CLI commands (AC: #8)
  - [x] 2.1 Add `--topic` (repeatable) flag to `resume new publication`
  - [x] 2.2 Add `--abstract` flag to `resume new publication`
  - [x] 2.3 Update interactive prompts to ask for topics and abstract
  - [x] 2.4 Update pipe-separated format: `"Title|Type|Venue|Date|URL|Topics|Abstract"`
  - [x] 2.5 Update `resume show publication` to display topics and abstract

- [x] Task 3: Update PublicationService for new fields (AC: #1)
  - [x] 3.1 Update save_publication() to persist topics and abstract
  - [x] 3.2 Update load_publications() to parse topics and abstract
  - [x] 3.3 Handle backward compatibility (existing publications without new fields)

- [x] Task 4: Add `curate_publications()` method to ContentCurator (AC: #2, #3, #4)
  - [x] 4.1 Add method signature matching existing curation patterns
  - [x] 4.2 Implement scoring: 40% semantic + 40% topic overlap + 20% recency
  - [x] 4.3 Use SkillRegistry to normalize topics before matching
  - [x] 4.4 Apply `min_relevance_score` threshold filter
  - [x] 4.5 Return CurationResult[Publication] with scores and reason

- [x] Task 5: Wire curation into build command (AC: #2, #5, #6)
  - [x] 5.1 Update build command to call curate_publications when JD provided
  - [x] 5.2 Pass curated publications to ResumeData instead of all publications
  - [x] 5.3 Preserve date-sorted fallback when no JD provided

- [x] Task 6: Update ResumeData to use curated publications (AC: #5)
  - [x] 6.1 Add `publications_curated: bool = False` flag to ResumeData
  - [x] 6.2 Modify `get_sorted_publications()` to preserve order when curated

- [x] Task 7: Add unit tests (AC: #1-7)
  - [x] 7.1 Test Publication model with topics and abstract
  - [x] 7.2 Test get_normalized_topics() with SkillRegistry
  - [x] 7.3 Test publication scoring formula (40/40/20 split)
  - [x] 7.4 Test threshold filtering
  - [x] 7.5 Test limit enforcement
  - [x] 7.6 Test no-JD fallback behavior

- [x] Task 8: Add integration tests (AC: #2, #6, #8)
  - [x] 8.1 Test `resume new publication` with topics and abstract
  - [x] 8.2 Test build with JD shows curated publications
  - [x] 8.3 Test build without JD shows all publications

## Dev Notes

### Project Context Reference

**CRITICAL**: Read `_bmad-output/project-context.md` before implementing. Key rules:
- Use `model_validator(mode='after')` not deprecated `@validator`
- Never use `print()` - use Rich console from `utils/console.py`
- Run `ruff check src tests --fix && ruff format src tests && mypy src --strict` before completing

### Architecture Constraints

1. **SkillRegistry Integration**: Topics must normalize via existing SkillRegistry:
   ```python
   from resume_as_code.services.skill_registry import SkillRegistry
   registry = SkillRegistry.load()
   normalized = registry.normalize(topic)  # "k8s" → "Kubernetes"
   ```

2. **ContentCurator Pattern**: Follow existing curation methods in `services/content_curator.py`:
   - `curate_highlights()` - 60% semantic, 40% keyword
   - `curate_certifications()` - 50% skill match, 30% semantic, 20% recency
   - `curate_board_roles()` - 70% semantic, 30% recency

3. **CurationConfig Integration**: Use existing `publications_max` field (default: 3)

4. **Build Command Flow**:
   ```
   build command → load publications → curate_publications(pubs, jd, registry) → ResumeData
   ```

### Critical Implementation Details

#### Publication Model Enhancement (Task 1)

Update `src/resume_as_code/models/publication.py`:

```python
class Publication(BaseModel):
    """Publication or speaking engagement record."""

    title: str
    type: PublicationType
    venue: str
    date: YearMonth
    url: HttpUrl | None = None
    display: bool = Field(default=True)
    # New fields for JD-relevant curation
    topics: list[str] = Field(default_factory=list, description="Topic tags for matching (normalized via SkillRegistry)")
    abstract: str | None = Field(default=None, description="Brief description for semantic matching")

    def get_normalized_topics(self, registry: SkillRegistry | None = None) -> list[str]:
        """Get topics normalized via SkillRegistry.

        Args:
            registry: Optional SkillRegistry for normalization.
                     If None, returns topics as-is.

        Returns:
            List of normalized topic strings.
        """
        if registry is None:
            return self.topics
        return [registry.normalize(topic) for topic in self.topics]

    def get_text_for_matching(self) -> str:
        """Get combined text for semantic matching.

        Returns:
            Combined title + venue + abstract for embedding.
        """
        parts = [self.title, self.venue]
        if self.abstract:
            parts.append(self.abstract)
        return " ".join(parts)
```

#### CLI Update (Task 2)

Update `resume new publication` in `commands/new.py`:

```python
# Add flags
@click.option("--topic", "-t", multiple=True, help="Topic tag (repeatable)")
@click.option("--abstract", "-a", help="Brief description of the publication")

# Pipe-separated format update (backward compatible)
# Old: "Title|Type|Venue|Date|URL"
# New: "Title|Type|Venue|Date|URL|Topics|Abstract"
# Topics as comma-separated: "kubernetes,security,devops"
```

#### curate_publications() Method (Task 4)

Add to `src/resume_as_code/services/content_curator.py`:

```python
def curate_publications(
    self,
    publications: list[Publication],
    jd: JobDescription,
    registry: SkillRegistry | None = None,
    max_count: int | None = None,
) -> CurationResult[Publication]:
    """Select most JD-relevant publications.

    Scoring formula:
    - 40% semantic similarity (abstract + title + venue vs JD)
    - 40% topic overlap with JD skills/keywords (normalized)
    - 20% recency bonus (publications in last 3 years preferred)

    Args:
        publications: All publications to consider.
        jd: Job description for matching.
        registry: SkillRegistry for topic normalization.
        max_count: Override default limit.

    Returns:
        CurationResult with selected/excluded publications and scores.
    """
    if not publications:
        return CurationResult(selected=[], excluded=[], reason="No publications configured")

    max_count = max_count or self.limits["publications"]

    # Pre-compute JD data
    jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)
    jd_skills_normalized = {
        (registry.normalize(s) if registry else s).lower()
        for s in jd.skills
    }
    jd_keywords = {kw.lower() for kw in jd.keywords}
    jd_match_terms = jd_skills_normalized | jd_keywords

    scores: dict[str, float] = {}
    today = date.today()

    for pub in publications:
        # Semantic similarity (40% weight) - use abstract + title + venue
        pub_text = pub.get_text_for_matching()
        pub_emb = self.embedder.embed_query(pub_text)
        semantic_score = self._cosine_similarity(pub_emb, jd_embedding)

        # Topic overlap (40% weight) - normalized via SkillRegistry
        normalized_topics = pub.get_normalized_topics(registry)
        topic_matches = sum(
            1 for topic in normalized_topics
            if topic.lower() in jd_match_terms
        )
        # Normalize: 2+ matches = 1.0
        topic_score = min(1.0, topic_matches / 2) if normalized_topics else 0.0

        # Recency bonus (20% weight) - publications in last 3 years preferred
        pub_year = int(pub.date[:4])
        years_ago = today.year - pub_year
        recency_score = 1.0 if years_ago <= 3 else max(0.5, 1.0 - (years_ago - 3) * 0.1)

        scores[pub.title] = (0.4 * semantic_score) + (0.4 * topic_score) + (0.2 * recency_score)

    # Rank by score descending
    ranked = sorted(publications, key=lambda p: scores.get(p.title, 0), reverse=True)

    # Filter by minimum relevance score
    qualified = [p for p in ranked if scores.get(p.title, 0) >= self.min_relevance_score]
    below_threshold = [p for p in ranked if scores.get(p.title, 0) < self.min_relevance_score]

    selected = qualified[:max_count]
    excluded = qualified[max_count:] + below_threshold

    return CurationResult(
        selected=selected,
        excluded=excluded,
        scores=scores,
        reason=f"Selected top {len(selected)} of {len(publications)} publications by JD relevance",
    )
```

#### ResumeData Integration (Task 6)

In `models/resume.py`:

```python
class ResumeData(BaseModel):
    # ... existing fields ...
    publications_curated: bool = Field(default=False, description="True when publications are pre-sorted by relevance")

    def get_sorted_publications(self) -> list[Publication]:
        """Get publications sorted for display.

        When publications_curated is True, preserves current order (relevance-sorted).
        Otherwise sorts by date descending.

        Returns:
            List of displayable publications.
        """
        displayable = [pub for pub in self.publications if pub.display]

        if self.publications_curated:
            return displayable

        # Default: sort by date descending
        return sorted(displayable, key=lambda pub: pub.date, reverse=True)
```

### Files to Modify

| File | Changes |
|------|---------|
| `src/resume_as_code/models/publication.py` | Add `topics`, `abstract`, `get_normalized_topics()`, `get_text_for_matching()` |
| `src/resume_as_code/services/publication_service.py` | Handle new fields in save/load |
| `src/resume_as_code/commands/new.py` | Add `--topic`, `--abstract` flags to publication command |
| `src/resume_as_code/commands/show.py` | Display topics and abstract in `show publication` |
| `src/resume_as_code/services/content_curator.py` | Add `curate_publications()` method |
| `src/resume_as_code/commands/build.py` | Call curation when JD provided |
| `src/resume_as_code/models/resume.py` | Add `publications_curated` flag, update `get_sorted_publications()` |
| `tests/unit/test_publication.py` | Test new fields and methods |
| `tests/unit/test_content_curator.py` | Add publication curation tests |
| `tests/test_cli.py` | Add integration tests |

### Existing Code Patterns to Follow

1. **SkillRegistry usage** - See `services/skill_registry.py` for normalization pattern
2. **Curation pattern** - See `curate_certifications()` in `content_curator.py:184-257`
3. **CLI repeatable options** - See `--skill` and `--tag` in work unit creation
4. **Pipe-separated parsing** - See position and certification parsing in `commands/new.py`

### Backward Compatibility

Publications without `topics` or `abstract` fields must still work:
- Default `topics` to empty list
- Default `abstract` to None
- Curation falls back to title+venue semantic matching when no topics/abstract

### Testing Requirements

1. **Unit tests** (`tests/unit/test_publication.py`):
   - `test_publication_with_topics_and_abstract`
   - `test_get_normalized_topics_with_registry`
   - `test_get_normalized_topics_without_registry`
   - `test_get_text_for_matching`

2. **Unit tests** (`tests/unit/test_content_curator.py`):
   - `test_curate_publications_empty_list`
   - `test_curate_publications_scoring_formula`
   - `test_curate_publications_topic_matching`
   - `test_curate_publications_threshold_filter`
   - `test_curate_publications_max_limit`
   - `test_curate_publications_recency_bonus`
   - `test_curate_publications_no_topics_fallback`

3. **Integration tests** (`tests/test_cli.py`):
   - `test_new_publication_with_topics`
   - `test_new_publication_with_abstract`
   - `test_build_with_jd_curates_publications`
   - `test_build_without_jd_shows_all_publications`

### Definition of Done

- [x] Publication model has `topics: list[str]` and `abstract: str | None` fields
- [x] `get_normalized_topics()` integrates with SkillRegistry
- [x] `resume new publication` accepts `--topic` (repeatable) and `--abstract`
- [x] Pipe-separated format supports topics and abstract
- [x] `curate_publications()` method added to ContentCurator
- [x] Scoring formula: 40% semantic + 40% topic overlap + 20% recency
- [x] Topics normalized via SkillRegistry before matching
- [x] `min_relevance_score` threshold applied
- [x] `curation.publications_max` limit respected (default: 3)
- [x] Build with JD uses curated publications (relevance-sorted)
- [x] Build without JD uses all publications (date-sorted)
- [x] Backward compatible with publications missing new fields
- [x] Unit tests for model, curation, CLI
- [x] Integration tests for build command
- [x] All tests pass: `uv run pytest`
- [x] Type check passes: `uv run mypy src --strict`
- [x] Linting passes: `uv run ruff check src tests --fix && uv run ruff format src tests`

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **Initial Implementation** (commit 49e5013): Added topics and abstract fields to Publication model, CLI support, and curate_publications() method in ContentCurator

2. **Code Review Remediation** (commit c7a09a9): Fixed 8 issues from adversarial code review:
   - ISSUE 1 (HIGH): Implemented missing Task 6 - Added `publications_curated` flag to ResumeData, updated `get_sorted_publications()` to preserve relevance order
   - ISSUE 2 (HIGH): Enhanced integration tests with assertions for curation output
   - ISSUE 3 (MEDIUM): Fixed score key collisions using MD5 hash-based `_publication_key()` method
   - ISSUE 4 (MEDIUM): Fixed legacy data handling - redistributed topic weight to 80% semantic + 20% recency when no topics
   - ISSUE 5 (MEDIUM): Added embedding error handling with fallback to topic-based scoring
   - ISSUE 6 (MEDIUM): Added unit tests for fallback behavior, marked slow tests with `@pytest.mark.slow`
   - ISSUE 7 (LOW): Added defensive date parsing with try/except
   - ISSUE 8 (LOW): Added `max_length=500` to abstract field

3. **Test Results**: 2112 unit tests passed, 6 integration tests passed, mypy strict mode passed, ruff passed

### File List

| File | Changes |
|------|---------|
| `src/resume_as_code/models/publication.py` | Added `topics`, `abstract` (with max_length=500), `get_normalized_topics()`, `get_text_for_matching()` |
| `src/resume_as_code/models/resume.py` | Added `publications_curated` flag, updated `get_sorted_publications()` |
| `src/resume_as_code/services/content_curator.py` | Added `curate_publications()`, `_publication_key()`, embedding fallback, defensive date parsing |
| `src/resume_as_code/commands/new.py` | Added `--topic`, `--abstract` flags to publication command |
| `src/resume_as_code/commands/show.py` | Display topics and abstract in `show publication` |
| `src/resume_as_code/commands/build.py` | Call curation when JD provided, set `publications_curated=True` |
| `schemas/config.schema.json` | Auto-updated for new fields |
| `schemas/publications.schema.json` | Auto-updated for abstract max_length |
| `tests/unit/test_publication.py` | Tests for new fields and methods |
| `tests/unit/test_content_curator.py` | Publication curation tests including fallback scenarios |
| `tests/integration/test_publication_curation.py` | Integration tests for CLI and build
