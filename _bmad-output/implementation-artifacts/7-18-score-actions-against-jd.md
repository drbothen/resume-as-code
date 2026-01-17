# Story 7.18: Score Actions Against JD

Status: complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **job seeker**,
I want **individual action bullets scored against JD relevance**,
So that **my resume shows only the most impactful, JD-aligned achievements per position**.

## Acceptance Criteria

1. **Given** a position has many work units with action bullets
   **When** `ContentCurator.curate_position_bullets()` runs
   **Then** individual action bullets are scored against JD using semantic similarity + keyword matching

2. **Given** action-level scoring is enabled
   **When** an action is evaluated
   **Then** it receives a composite score:
   - 60% semantic similarity to JD requirements
   - 30% keyword overlap with JD extracted keywords
   - 10% quantified impact boost if action contains metrics

3. **Given** a position has 12 total action bullets but only 6 bullet slots (based on recency)
   **When** curation runs
   **Then** the 6 highest-scoring actions are selected (regardless of which work unit they came from)

4. **Given** action scoring is enabled (config: `curation.action_scoring_enabled = true`)
   **When** scoring is disabled
   **Then** falls back to existing behavior (whole work unit scoring)

5. **Given** an action's score is below minimum threshold (config: `curation.min_action_relevance_score`)
   **When** curation runs
   **Then** the action is excluded even if slots remain

## Tasks / Subtasks

- [x] Task 1: Add action scoring configuration (AC: #4)
  - [x] 1.1 Add `action_scoring_enabled: bool = True` to `CurationConfig`
  - [x] 1.2 Add `min_action_relevance_score: float = 0.25` to `CurationConfig`
  - [x] 1.3 Add unit tests for new config fields

- [x] Task 2: Implement action scoring method (AC: #2)
  - [x] 2.1 Add `ContentCurator.score_action(action: str, jd: JobDescription) -> float`
  - [x] 2.2 Implement semantic similarity component (60% weight)
  - [x] 2.3 Implement keyword overlap component (30% weight)
  - [x] 2.4 Implement quantified boost detection (10% weight)
  - [x] 2.5 Add unit tests for score_action with various inputs

- [x] Task 3: Extend curate_position_bullets for action-level selection (AC: #1, #3)
  - [x] 3.1 Extract all actions from all work units for position
  - [x] 3.2 Score each action individually via `score_action()`
  - [x] 3.3 Rank actions by score, select top N based on bullet limits
  - [x] 3.4 Return `CurationResult` with selected/excluded actions
  - [x] 3.5 Add integration test: 12 actions → 6 selected by score

- [x] Task 4: Apply minimum threshold filter (AC: #5)
  - [x] 4.1 Filter out actions below `min_action_relevance_score`
  - [x] 4.2 Log excluded count at DEBUG level
  - [x] 4.3 Add unit test for threshold filtering

- [x] Task 5: Wire into resume build flow
  - [x] 5.1 Update `ResumeData._extract_bullets()` to accept curated action list
  - [x] 5.2 Ensure position grouping still works with action-level curation
  - [x] 5.3 Add integration test: end-to-end build with action scoring

- [x] Task 6: Quality checks
  - [x] 6.1 Run `ruff check src tests --fix`
  - [x] 6.2 Run `ruff format src tests`
  - [x] 6.3 Run `mypy src --strict` (zero errors)
  - [x] 6.4 Run full test suite

## Dev Notes

### Current State Analysis

**What exists:**
- `ContentCurator` in `services/content_curator.py` (Story 7.14)
  - `curate_position_bullets()` scores **work units** as a whole
  - Uses `_extract_work_unit_text()` for semantic matching
  - Returns `CurationResult[WorkUnit]`
- `ResumeData._extract_bullets()` in `models/resume.py`
  - Extracts outcome.result + first 3 actions from work unit
  - No scoring — returns all bullets

**Gap:**
- No individual action-level scoring
- Bullets are limited by count, not relevance
- All actions from a work unit are included or excluded together

### Implementation Pattern

**New Configuration:**
```python
# models/config.py - CurationConfig
class CurationConfig(BaseModel):
    # ... existing fields ...

    action_scoring_enabled: bool = Field(
        default=True,
        description="Score individual action bullets against JD relevance.",
    )
    min_action_relevance_score: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Minimum score for action bullet inclusion.",
    )
```

**Action Scoring Method:**
```python
# services/content_curator.py

def score_action(
    self,
    action: str,
    jd: JobDescription,
    jd_embedding: NDArray[np.float32] | None = None,
) -> float:
    """Score individual action bullet against JD relevance.

    Args:
        action: Action bullet text.
        jd: Job description for matching.
        jd_embedding: Pre-computed JD embedding (optional, for batch efficiency).

    Returns:
        Relevance score between 0.0 and 1.0.
    """
    if jd_embedding is None:
        jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)

    # Semantic similarity (60% weight)
    action_emb = self.embedder.embed_query(action)
    semantic_score = self._cosine_similarity(action_emb, jd_embedding)

    # Keyword overlap (30% weight)
    jd_keywords = {kw.lower() for kw in jd.keywords}
    keyword_score = self._keyword_overlap(action, jd_keywords)

    # Quantified boost (10% weight) - binary: 1.0 if quantified, 0.0 if not
    quantified_score = 1.0 if self._has_quantified_text(action) else 0.0

    return (0.6 * semantic_score) + (0.3 * keyword_score) + (0.1 * quantified_score)
```

**Extended curate_position_bullets:**
```python
def curate_position_bullets(
    self,
    position: Position,
    work_units: list[WorkUnit],
    jd: JobDescription,
) -> CurationResult[str]:  # NOTE: Returns str (action text), not WorkUnit
    """Select most JD-relevant action bullets for a position.

    When action_scoring_enabled is True, scores individual actions.
    Otherwise falls back to work-unit-level selection.
    """
    if not self.action_scoring_enabled:
        # Existing behavior: score whole work units
        return self._curate_work_units(position, work_units, jd)

    # Determine bullet limits
    years_ago = self._position_age_years(position)
    bullet_config = self._get_bullet_config(years_ago)
    max_bullets = int(bullet_config["max"])

    # Pre-compute JD embedding for efficiency
    jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)

    # Extract all action bullets from all work units
    all_actions: list[tuple[str, str]] = []  # (action_text, work_unit_id)
    for wu in work_units:
        # Include outcome.result as primary bullet
        if wu.outcome.result:
            all_actions.append((wu.outcome.result, wu.id))
        # Include actions
        for action in wu.actions:
            all_actions.append((action, wu.id))

    # Score each action
    scores: dict[str, float] = {}
    for action_text, wu_id in all_actions:
        key = f"{wu_id}:{action_text[:50]}"  # Unique key
        scores[key] = self.score_action(action_text, jd, jd_embedding)

    # Filter by minimum threshold
    min_score = self.min_action_relevance_score
    qualified = [(a, k) for a, k in zip(
        [t[0] for t in all_actions],
        [f"{t[1]}:{t[0][:50]}" for t in all_actions]
    ) if scores.get(k, 0) >= min_score]

    # Rank by score
    qualified.sort(key=lambda x: scores.get(x[1], 0), reverse=True)

    # Select top N
    selected = [a for a, _ in qualified[:max_bullets]]
    excluded = [a for a, _ in qualified[max_bullets:]]

    return CurationResult(
        selected=selected,
        excluded=excluded,
        scores=scores,
        reason=f"Selected {len(selected)} of {len(all_actions)} actions by JD relevance",
    )
```

**Quantified Text Detection:**
```python
def _has_quantified_text(self, text: str) -> bool:
    """Check if text contains quantified metrics."""
    patterns = [
        r"\d+%",              # Percentages: 40%, 100%
        r"\$[\d,]+[KMB]?",    # Dollar amounts: $50K, $1M
        r"\d+x\b",            # Multipliers: 3x, 10x
        r"\d+\s*(?:hours?|days?|weeks?|months?)",  # Time: 2 hours
        r"\d+\s*(?:users?|customers?|clients?)",   # People: 500 users
        r"\d+\s*(?:teams?|engineers?|developers?)",  # Teams: 5 engineers
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)
```

### Integration with Resume Build

The `ResumeData._extract_bullets()` method currently extracts bullets without curation. Two approaches:

**Option A (Recommended): Inject curated actions during build**
- Pass curated action list from build.py
- `_build_item_from_position()` receives pre-curated bullets
- Minimal changes to existing flow

**Option B: Call ContentCurator from resume.py**
- Add JD parameter to `from_work_units()`
- Call `ContentCurator.curate_position_bullets()` in the model
- More self-contained but adds JD dependency to model layer

### Dependencies

- **Depends on:** Story 7.14 (ContentCurator exists)
- **Blocked by:** None

### Testing Strategy

```python
# tests/unit/test_content_curator.py

class TestScoreAction:
    def test_score_action_high_relevance(self, curator, mock_jd):
        """Action matching JD keywords scores high."""
        action = "Led Kubernetes migration reducing deployment time 80%"
        # JD has: Kubernetes, deployment, DevOps
        score = curator.score_action(action, mock_jd)
        assert score >= 0.6

    def test_score_action_low_relevance(self, curator, mock_jd):
        """Unrelated action scores low."""
        action = "Organized team building events"
        score = curator.score_action(action, mock_jd)
        assert score < 0.3

    def test_score_action_quantified_boost(self, curator, mock_jd):
        """Quantified actions get boost."""
        base = "Improved system performance"
        quantified = "Improved system performance by 40%"

        base_score = curator.score_action(base, mock_jd)
        quant_score = curator.score_action(quantified, mock_jd)

        assert quant_score > base_score


class TestCuratePositionBulletsActionLevel:
    def test_selects_top_actions_across_work_units(self, curator, position, work_units, jd):
        """Top actions selected regardless of source work unit."""
        # 3 work units, each with 4 actions = 12 total
        # Position is recent (0-3 years) = 6 bullet limit
        result = curator.curate_position_bullets(position, work_units, jd)

        assert len(result.selected) == 6
        assert len(result.excluded) == 6

    def test_filters_below_threshold(self, curator, position, work_units, jd):
        """Actions below min_action_relevance_score are excluded."""
        curator.min_action_relevance_score = 0.5
        result = curator.curate_position_bullets(position, work_units, jd)

        # Verify all selected meet threshold
        for action in result.selected:
            key = [k for k in result.scores if action[:50] in k][0]
            assert result.scores[key] >= 0.5
```

### Project Context Rules

From `project-context.md`:
- Run `ruff check` and `mypy --strict` before completing
- Use Rich console for CLI output, never `print()`
- Type hints required on all public functions
- Use `|` union syntax (Python 3.10+)
- Exception handling: catch specific exceptions

### References

- [Depends: Story 7.14 - JD-Relevant Content Curation]
- [Source: src/resume_as_code/services/content_curator.py]
- [Source: src/resume_as_code/models/resume.py - _extract_bullets method]
- [Source: src/resume_as_code/models/config.py - CurationConfig]
- [Epic: epic-7-schema-data-model-refactoring.md - Story 7.18]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Code review session 2026-01-17: Validated all 5 ACs implemented, 168 tests passing
- Quality checks: mypy --strict (0 errors), ruff check (all passed)
- Fixed test isolation for ONET_API_KEY environment variable (pre-existing issue)

### Completion Notes List

- Implemented `curate_action_bullets()` method (renamed from spec's `curate_position_bullets` for clarity)
- Used cleaner key format `{wu_id}:{source_type}` instead of spec's `{wu_id}:{text[:50]}`
- Integration via dedicated `_curate_bullets_for_position()` method in resume.py
- Story-related tests: TestScoreAction (8), TestCurateActionBullets (6), TestHasQuantifiedText (6), TestCurationConfig action fields (6), TestResumeDataActionScoring (4) = 30 tests
- Fixed 2 pre-existing test failures (test isolation for ONET_API_KEY env var)

### File List

**Modified:**
- `src/resume_as_code/models/config.py` - Added `action_scoring_enabled`, `min_action_relevance_score` to CurationConfig
- `src/resume_as_code/services/content_curator.py` - Added `score_action()`, `curate_action_bullets()`, `_has_quantified_text()`
- `src/resume_as_code/models/resume.py` - Added `_curate_bullets_for_position()`, updated `_build_item_from_position()`
- `src/resume_as_code/commands/build.py` - Added `_get_jd_for_scoring()`, pass JD to `from_work_units()`
- `tests/unit/test_content_curator.py` - Added `TestScoreAction`, `TestCurateActionBullets`, `TestHasQuantifiedText`
- `tests/unit/test_config_models.py` - Added `TestCurationConfig` action scoring tests, fixed test isolation for ONET_API_KEY
- `tests/unit/test_resume_model.py` - Added `TestResumeDataActionScoring` integration tests
