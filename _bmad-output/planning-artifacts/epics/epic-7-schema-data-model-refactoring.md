# Epic 7: Schema & Data Model Refactoring

**Goal:** Eliminate technical debt in schema/model layer, establish single source of truth, and enable O*NET skill standardization

**User Outcome:** Users benefit from consistent validation, normalized skill names across ATS systems, and reliable position references in work units

**Technical Debt Analysis (2026-01-14):**
This epic addresses schema inconsistencies identified during deep codebase analysis:
- JSON schemas drift from Pydantic models (manual sync prone to errors)
- Three incompatible Scope models (PositionScope, WorkUnit.scope, ResumeItem.scope_*)
- Date handling varies across models (strings, dates, nullable patterns)
- Skills scattered across 4 places with no normalization
- Position references lack integrity enforcement
- Evidence model requires URL even for local-only artifacts

**Priority:** P1-P3 (foundational to advanced integration)
**Total Points:** 29

---

## Story 7.1: JSON Schema Auto-Generation

As a **developer**,
I want **JSON schemas to be auto-generated from Pydantic models**,
So that **schemas never drift from implementation and documentation stays accurate**.

**Story Points:** 3
**Priority:** P1 (foundational)

**Acceptance Criteria:**

**Given** the Pydantic models in `src/resume_as_code/models/`
**When** I run the pre-commit hooks
**Then** JSON schemas are regenerated in `schemas/` directory

**Given** a Pydantic model changes (new field, type change, validation)
**When** I commit the change
**Then** the corresponding JSON schema is updated automatically
**And** the commit includes both the model change and schema update

**Given** I run `uv run python scripts/generate_schemas.py`
**When** it completes
**Then** all schemas in `schemas/` are regenerated
**And** `$id` URLs follow pattern `https://resume-as-code.dev/schemas/{name}.schema.json`

**Given** a generated schema
**When** I inspect it
**Then** it includes:
- `$schema: "https://json-schema.org/draft/2020-12/schema"`
- Proper `$defs` for nested models
- `description` from docstrings
- All validation constraints (minLength, pattern, enum, etc.)

**Technical Notes:**
```python
# scripts/generate_schemas.py
from pydantic import TypeAdapter
from resume_as_code.models.work_unit import WorkUnit
from resume_as_code.models.position import Position
from resume_as_code.models.config import ResumeConfig

MODELS = {
    "work-unit": WorkUnit,
    "positions": Position,
    "config": ResumeConfig,
}

for name, model in MODELS.items():
    adapter = TypeAdapter(model)
    schema = adapter.json_schema(mode="serialization")
    schema["$id"] = f"https://resume-as-code.dev/schemas/{name}.schema.json"
    # Write to schemas/{name}.schema.json
```

**Files to Create/Modify:**
- Create: `scripts/generate_schemas.py`
- Modify: `.pre-commit-config.yaml` (add schema generation hook)
- Delete: Manual schema maintenance workflow

**Definition of Done:**
- [ ] Schema generation script exists and runs without errors
- [ ] Pre-commit hook triggers schema regeneration
- [ ] All existing tests pass with new schemas
- [ ] Generated schemas validate against JSON Schema 2020-12

---

## Story 7.2: Unified Scope Model

As a **resume builder**,
I want **a single Scope model used consistently across positions and work units**,
So that **executive metrics are reliable and don't conflict between data sources**.

**Story Points:** 5
**Priority:** P1 (foundational)

**Acceptance Criteria:**

**Given** a position with scope data
**When** I create work units for that position
**Then** I don't need to duplicate scope in work units
**And** scope from position is used for resume rendering

**Given** the unified Scope model
**When** I inspect its fields
**Then** it contains:
- `revenue: str | None` - Revenue impact (e.g., "$500M")
- `team_size: int | None` - Total team/org size
- `direct_reports: int | None` - Direct reports count
- `budget: str | None` - Budget managed
- `pl_responsibility: str | None` - P&L responsibility
- `geography: str | None` - Geographic reach
- `customers: str | None` - Customer scope

**Given** existing work units with legacy scope fields
**When** validation runs
**Then** a deprecation warning is logged (not an error)
**And** legacy fields are mapped to unified model internally

**Given** ResumeItem renders a position
**When** scope data exists
**Then** scope_line is formatted consistently using unified model

**Technical Notes:**
```python
# src/resume_as_code/models/scope.py (new file)
from pydantic import BaseModel, ConfigDict

class Scope(BaseModel):
    """Unified scope model for positions and work units."""
    model_config = ConfigDict(extra="forbid")
    
    revenue: str | None = None
    team_size: int | None = None
    direct_reports: int | None = None
    budget: str | None = None
    pl_responsibility: str | None = None
    geography: str | None = None
    customers: str | None = None
```

**Migration:**
- Position.scope already uses PositionScope → rename to Scope
- WorkUnit.scope uses different fields → deprecate, migrate to position-level scope
- ResumeItem.scope_* fields → derive from Position.scope only

**Files to Create/Modify:**
- Create: `src/resume_as_code/models/scope.py`
- Modify: `src/resume_as_code/models/position.py` (use unified Scope)
- Modify: `src/resume_as_code/models/work_unit.py` (deprecate scope)
- Modify: `src/resume_as_code/models/resume.py` (use Position.scope)
- Modify: `src/resume_as_code/services/position_service.py` (update format_scope_line)

**Definition of Done:**
- [ ] Single Scope class defined in models/scope.py
- [ ] Position uses unified Scope
- [ ] Work unit scope deprecated with warning
- [ ] ResumeItem scope fields derived from Position.scope
- [ ] All tests pass

---

## Story 7.3: Standardized Date Types

As a **developer**,
I want **consistent date handling with reusable annotated types**,
So that **date validation is centralized and dates display consistently**.

**Story Points:** 3
**Priority:** P2

**Acceptance Criteria:**

**Given** a YearMonth field (e.g., "2024-01")
**When** I set it with various formats
**Then** it normalizes to YYYY-MM string
**And** invalid formats raise ValidationError

**Given** a Year field (e.g., "2024" or 2024)
**When** I set it with string or integer
**Then** it normalizes to 4-digit string
**And** invalid formats raise ValidationError

**Given** Position.start_date and Position.end_date
**When** I inspect their types
**Then** they use `YearMonth` annotated type
**And** validation is automatic (no custom validators needed)

**Given** Education.graduation_year
**When** I inspect its type
**Then** it uses `Year` annotated type

**Technical Notes:**
```python
# src/resume_as_code/models/types.py (new file)
import re
from typing import Annotated
from pydantic import BeforeValidator

def normalize_year_month(v: str | None) -> str | None:
    if v is None:
        return None
    if not re.match(r"^\d{4}-\d{2}$", str(v)):
        raise ValueError("Date must be in YYYY-MM format")
    return str(v)

def normalize_year(v: str | int | None) -> str | None:
    if v is None:
        return None
    year_str = str(v)
    if not re.match(r"^\d{4}$", year_str):
        raise ValueError("Year must be 4-digit format (YYYY)")
    return year_str

YearMonth = Annotated[str, BeforeValidator(normalize_year_month)]
Year = Annotated[str, BeforeValidator(normalize_year)]
```

**Files to Create/Modify:**
- Create: `src/resume_as_code/models/types.py`
- Modify: `src/resume_as_code/models/position.py` (use YearMonth)
- Modify: `src/resume_as_code/models/education.py` (use Year)
- Modify: `src/resume_as_code/models/certification.py` (use YearMonth for date fields)

**Definition of Done:**
- [ ] types.py with YearMonth and Year annotated types
- [ ] Position uses YearMonth for start_date/end_date
- [ ] Remove duplicate date validators from models
- [ ] All date fields validate consistently

---

## Story 7.4: Skills Registry & Normalization

As a **job seeker**,
I want **my skills normalized to standard names with aliases**,
So that **ATS systems recognize my skills regardless of how I typed them**.

**Story Points:** 5
**Priority:** P2

**Acceptance Criteria:**

**Given** I enter skill "k8s" in a work unit
**When** the resume renders
**Then** it displays "Kubernetes" (canonical name)
**And** original alias is preserved for search matching

**Given** the skills registry
**When** I inspect it
**Then** each skill has:
- `canonical: str` - Display name
- `aliases: list[str]` - Alternative spellings/abbreviations
- `category: str | None` - Optional category
- `onet_code: str | None` - O*NET mapping (if available)

**Given** I call `SkillRegistry.normalize("typescript")`
**When** it returns
**Then** I get `"TypeScript"` (proper casing)

**Given** I call `SkillRegistry.normalize("unknown-skill")`
**When** it returns
**Then** I get the original string back (passthrough)

**Given** skills are extracted from work units
**When** curated for resume
**Then** duplicates are removed by canonical name
**And** both aliases and canonical names match JD keywords

**Technical Notes:**
```python
# src/resume_as_code/services/skill_registry.py
from pydantic import BaseModel

class SkillEntry(BaseModel):
    canonical: str
    aliases: list[str] = []
    category: str | None = None
    onet_code: str | None = None

class SkillRegistry:
    def __init__(self, entries: list[SkillEntry]):
        self._by_alias: dict[str, SkillEntry] = {}
        for entry in entries:
            self._by_alias[entry.canonical.lower()] = entry
            for alias in entry.aliases:
                self._by_alias[alias.lower()] = entry
    
    def normalize(self, skill: str) -> str:
        entry = self._by_alias.get(skill.lower())
        return entry.canonical if entry else skill
    
    @classmethod
    def load_default(cls) -> "SkillRegistry":
        # Load from data/skills.yaml
        ...
```

**Files to Create/Modify:**
- Create: `src/resume_as_code/services/skill_registry.py`
- Create: `data/skills.yaml` (initial registry with ~50 common tech skills)
- Modify: `src/resume_as_code/services/skill_curator.py` (integrate registry)
- Modify: `src/resume_as_code/models/resume.py` (normalize during extraction)

**Definition of Done:**
- [ ] SkillRegistry class with normalize() method
- [ ] Initial skills.yaml with 50+ common tech skills
- [ ] SkillCurator uses registry for normalization
- [ ] Aliases counted for JD matching
- [ ] Unit tests for normalization

---

## Story 7.5: O*NET API Integration

As a **job seeker**,
I want **my skills mapped to O*NET standardized competencies**,
So that **my resume uses industry-recognized skill terminology**.

**Story Points:** 8
**Priority:** P3 (advanced integration)

**Dependencies:** Story 7.4 (Skills Registry)

**Acceptance Criteria:**

**Given** O*NET credentials in config or environment
**When** I run skill normalization
**Then** unmapped skills are looked up via O*NET API
**And** matches are cached locally

**Given** I call `ONetService.search_skills("python programming")`
**When** the API returns
**Then** I get O*NET skill codes and titles
**And** response is cached for 24 hours

**Given** no O*NET credentials configured
**When** skill normalization runs
**Then** it falls back to local registry only
**And** no errors are raised

**Given** O*NET API rate limit is hit
**When** making requests
**Then** exponential backoff is applied
**And** graceful degradation to local registry

**Given** a successful O*NET lookup
**When** the skill is added to registry
**Then** onet_code is populated
**And** skill is persisted for future use

**Technical Notes:**
```python
# src/resume_as_code/services/onet_service.py
import httpx
from functools import lru_cache

class ONetService:
    BASE_URL = "https://services.onetcenter.org/ws"
    
    def __init__(self, username: str, password: str):
        self._auth = (username, password)
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            auth=self._auth,
            headers={"Accept": "application/json"},
        )
    
    @lru_cache(maxsize=1000)
    def search_skills(self, keyword: str) -> list[dict]:
        resp = self._client.get("/online/search", params={
            "keyword": keyword,
            "start": 1,
            "end": 10,
        })
        resp.raise_for_status()
        return resp.json().get("occupation", [])
```

**Configuration:**
```yaml
# .resume.yaml
onet:
  username: ${ONET_USERNAME}  # from environment
  password: ${ONET_PASSWORD}
  cache_ttl: 86400  # 24 hours
```

**Files to Create/Modify:**
- Create: `src/resume_as_code/services/onet_service.py`
- Modify: `src/resume_as_code/models/config.py` (add ONetConfig)
- Modify: `src/resume_as_code/services/skill_registry.py` (integrate O*NET lookup)
- Create: `tests/unit/services/test_onet_service.py`

**Definition of Done:**
- [ ] ONetService with search_skills() method
- [ ] Config supports ONET credentials (env vars)
- [ ] Caching with configurable TTL
- [ ] Graceful fallback when API unavailable
- [ ] Rate limiting with backoff
- [ ] Integration tests (mocked API)

---

## Story 7.6: Position Reference Integrity

As a **developer**,
I want **work unit position_id references validated at load time**,
So that **invalid references are caught early, not during resume generation**.

**Story Points:** 2
**Priority:** P2

**Acceptance Criteria:**

**Given** a work unit with `position_id: pos-nonexistent`
**When** I run `resume validate --check-positions`
**Then** validation fails with error message
**And** error includes the invalid position_id and suggestions

**Given** a work unit without position_id
**When** validation runs
**Then** it passes (position_id is optional for standalone projects)

**Given** WorkUnitLoader loads work units
**When** positions are available
**Then** each position_id is validated against positions.yaml
**And** Position objects are attached to WorkUnit for efficient access

**Given** I call `work_unit.position`
**When** position_id is valid
**Then** I get the Position object directly
**And** no separate lookup is needed

**Technical Notes:**
```python
# Modify WorkUnit model
class WorkUnit(BaseModel):
    position_id: str | None = None
    _position: Position | None = PrivateAttr(default=None)
    
    @property
    def position(self) -> Position | None:
        return self._position
    
    def attach_position(self, position: Position) -> None:
        if self.position_id and position.id != self.position_id:
            raise ValueError(f"Position ID mismatch")
        self._position = position

# In WorkUnitLoader
def load_with_positions(self, positions: dict[str, Position]) -> list[WorkUnit]:
    work_units = self.load_all()
    for wu in work_units:
        if wu.position_id:
            if wu.position_id not in positions:
                raise ValidationError(f"Invalid position_id: {wu.position_id}")
            wu.attach_position(positions[wu.position_id])
    return work_units
```

**Files to Modify:**
- Modify: `src/resume_as_code/models/work_unit.py` (add position attachment)
- Modify: `src/resume_as_code/services/work_unit_loader.py` (validate references)
- Modify: `src/resume_as_code/commands/validate.py` (integrate position check)

**Definition of Done:**
- [ ] WorkUnit has position property
- [ ] Loader validates position_id references
- [ ] `--check-positions` flag works
- [ ] Clear error messages for invalid references

---

## Story 7.7: Evidence Model Enhancement

As a **job seeker**,
I want **to store evidence without requiring URLs**,
So that **I can reference local artifacts, file hashes, and descriptions**.

**Story Points:** 3
**Priority:** P3

**Acceptance Criteria:**

**Given** evidence with only description (no URL)
**When** I create a work unit
**Then** validation passes
**And** evidence is stored with type "narrative"

**Given** evidence with a URL
**When** I create a work unit
**Then** validation passes
**And** evidence type is inferred (github, metrics, etc.)

**Given** evidence with file hash
**When** I create a work unit
**Then** it stores hash and optional local path
**And** can be verified later

**Given** evidence types
**When** I inspect the discriminated union
**Then** supported types are:
- `link` - External URL (any http/https)
- `github` - GitHub PR/commit/repo
- `metrics` - Dashboard/analytics URL
- `narrative` - Text description only
- `artifact` - Local file with hash

**Technical Notes:**
```python
# Enhanced Evidence model with discriminated union
from typing import Literal
from pydantic import BaseModel, HttpUrl

class LinkEvidence(BaseModel):
    type: Literal["link"] = "link"
    url: HttpUrl
    description: str | None = None

class GitHubEvidence(BaseModel):
    type: Literal["github"] = "github"
    url: HttpUrl  # Must be github.com
    description: str | None = None

class MetricsEvidence(BaseModel):
    type: Literal["metrics"] = "metrics"
    url: HttpUrl
    description: str | None = None

class NarrativeEvidence(BaseModel):
    type: Literal["narrative"] = "narrative"
    description: str

class ArtifactEvidence(BaseModel):
    type: Literal["artifact"] = "artifact"
    path: str | None = None
    sha256: str | None = None
    description: str | None = None

Evidence = LinkEvidence | GitHubEvidence | MetricsEvidence | NarrativeEvidence | ArtifactEvidence
```

**Files to Modify:**
- Modify: `src/resume_as_code/models/work_unit.py` (enhance Evidence)
- Modify: `schemas/work-unit.schema.json` (auto-generated)
- Create: `tests/unit/models/test_evidence.py`

**Definition of Done:**
- [ ] Evidence uses discriminated union
- [ ] Narrative type allows description-only
- [ ] Artifact type supports file hash
- [ ] Schema auto-generated with oneOf
- [ ] Backward compatible with existing data

---

## Story 7.8: Field-Weighted BM25 Scoring

As a **job seeker**,
I want **my job titles and skills weighted higher than general experience text**,
So that **resumes with matching titles rank higher than those with incidental keyword matches**.

**Story Points:** 3
**Priority:** P1 (high ROI - uses existing config)

**Research Basis:** Harvard Business Review 2023 study shows field-weighted matching improves hire quality by 27%. Industry standard is 2-4x boost for job titles.

**Acceptance Criteria:**

**Given** `scoring_weights.title_weight` is set to 2.0 in config
**When** a work unit title matches JD keywords
**Then** that match contributes 2x to the BM25 score vs body text matches

**Given** `scoring_weights.skills_weight` is set to 1.5 in config
**When** work unit skills/tags match JD skills
**Then** that match contributes 1.5x to the BM25 score

**Given** default config (all weights = 1.0)
**When** ranking runs
**Then** behavior is unchanged from current implementation

**Given** I run `resume plan --jd job.txt`
**When** results display
**Then** match_reasons indicate which field matched (title, skills, experience)

**Technical Notes:**
```python
# Modify ranker.py to use field-specific BM25 scoring
def _bm25_rank_weighted(self, jd: JobDescription, work_units: list[WorkUnit]) -> list[int]:
    """BM25 with field-specific weighting."""
    weights = self.config.scoring_weights
    
    # Create separate corpora for each field
    title_corpus = [wu.title.lower().split() for wu in work_units]
    skills_corpus = [' '.join(wu.tags + [s.name for s in wu.skills_demonstrated]).lower().split() for wu in work_units]
    body_corpus = [extract_work_unit_text(wu).lower().split() for wu in work_units]
    
    # Score each field separately
    title_scores = BM25Okapi(title_corpus).get_scores(jd_tokens)
    skills_scores = BM25Okapi(skills_corpus).get_scores(jd_tokens)
    body_scores = BM25Okapi(body_corpus).get_scores(jd_tokens)
    
    # Weighted combination
    combined = (
        weights.title_weight * title_scores +
        weights.skills_weight * skills_scores +
        weights.experience_weight * body_scores
    )
    return combined
```

**Files to Modify:**
- Modify: `src/resume_as_code/services/ranker.py` (implement field weighting)
- Modify: `src/resume_as_code/utils/work_unit_text.py` (add field extraction helpers)

**Definition of Done:**
- [ ] title_weight, skills_weight, experience_weight are used in BM25 scoring
- [ ] Default weights (1.0) produce identical results to current behavior
- [ ] Match reasons indicate which field matched
- [ ] Unit tests for field weighting

---

## Story 7.9: Recency Decay for Work Units

As a **job seeker**,
I want **my recent work experience weighted higher than older experience**,
So that **my current skills and relevance are properly reflected in rankings**.

**Story Points:** 3
**Priority:** P2

**Research Basis:** Eightfold AI uses "recent skill vector similarity" as distinct signal. Exponential decay with configurable half-life is industry standard.

**Acceptance Criteria:**

**Given** a work unit with `time_ended: 2024-01` (1 year ago)
**When** ranking against a JD with `recency_half_life: 5` years
**Then** the work unit receives ~87% recency weight

**Given** a work unit with `time_ended: 2019-01` (5 years ago)
**When** ranking with 5-year half-life
**Then** the work unit receives ~50% recency weight

**Given** a work unit with `time_ended: null` (current position)
**When** ranking runs
**Then** the work unit receives 100% recency weight

**Given** recency decay is disabled (`recency_half_life: null`)
**When** ranking runs
**Then** all work units weighted equally (current behavior)

**Given** the final score calculation
**When** combining relevance and recency
**Then** formula is: `final = (0.8 × relevance) + (0.2 × recency_decay)` (configurable)

**Technical Notes:**
```python
# Add to config.py
class ScoringWeights(BaseModel):
    # ... existing fields ...
    recency_half_life: float | None = Field(
        default=5.0, 
        ge=1.0, 
        le=20.0,
        description="Years for experience to decay to 50% weight. None disables decay."
    )
    recency_blend: float = Field(
        default=0.2,
        ge=0.0,
        le=0.5,
        description="How much recency affects final score (0.2 = 20%)"
    )

# Add to ranker.py
import math
from datetime import date

def _calculate_recency_score(self, work_unit: WorkUnit) -> float:
    """Calculate recency decay score for a work unit."""
    if self.config.scoring_weights.recency_half_life is None:
        return 1.0
    
    end_date = work_unit.time_ended or date.today()
    years_ago = (date.today() - end_date).days / 365.25
    
    half_life = self.config.scoring_weights.recency_half_life
    decay_constant = math.log(2) / half_life
    
    return math.exp(-decay_constant * years_ago)
```

**Files to Modify:**
- Modify: `src/resume_as_code/models/config.py` (add recency config)
- Modify: `src/resume_as_code/services/ranker.py` (apply recency decay)
- Modify: `schemas/config.schema.json` (auto-generated)

**Definition of Done:**
- [ ] Recency decay applied to work unit scores
- [ ] Configurable half-life (default 5 years)
- [ ] Current positions get 100% weight
- [ ] Can be disabled via config
- [ ] Unit tests for decay formula

---

## Story 7.10: Improved BM25 Tokenization

As a **job seeker**,
I want **"engineering" to match "engineer" and "ML" to match "machine learning"**,
So that **keyword matching is more intelligent and less brittle**.

**Story Points:** 5
**Priority:** P2

**Research Basis:** Current `.lower().split()` misses stemming, compound terms, and abbreviations. Industry systems use lemmatization and domain-specific normalization.

**Acceptance Criteria:**

**Given** a JD containing "engineering"
**When** matching against work unit with "engineer"
**Then** they match (lemmatization)

**Given** a JD containing "machine learning"
**When** matching against work unit with "ML"
**Then** they match (abbreviation expansion)

**Given** a JD containing "project-management"
**When** matching against work unit with "project management"
**Then** they match (hyphen normalization)

**Given** a JD containing "CI/CD pipeline"
**When** matching against work unit with "CICD" or "CI CD"
**Then** they match (slash normalization)

**Given** tokenization runs
**When** processing text
**Then** domain stop words are filtered ("responsibilities", "requirements", "experience", "ability to")

**Technical Notes:**
```python
# src/resume_as_code/utils/tokenizer.py (new file)
import re
from functools import lru_cache

# Technical abbreviation mappings
TECH_EXPANSIONS = {
    "ml": "machine learning",
    "ai": "artificial intelligence", 
    "k8s": "kubernetes",
    "js": "javascript",
    "ts": "typescript",
    "cicd": "continuous integration continuous deployment",
    "ci/cd": "continuous integration continuous deployment",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
}

DOMAIN_STOP_WORDS = {
    "responsibilities", "requirements", "experience", "ability", 
    "strong", "excellent", "preferred", "required", "including",
    "work", "working", "team", "role", "position",
}

class ResumeTokenizer:
    def __init__(self, use_lemmatization: bool = True):
        self.use_lemmatization = use_lemmatization
        self._nlp = None  # Lazy load spaCy
    
    @property
    def nlp(self):
        if self._nlp is None and self.use_lemmatization:
            import spacy
            self._nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
        return self._nlp
    
    def tokenize(self, text: str) -> list[str]:
        # Normalize hyphens and slashes
        text = re.sub(r'[-/]', ' ', text.lower())
        
        # Expand abbreviations
        for abbrev, expansion in TECH_EXPANSIONS.items():
            text = re.sub(rf'\b{abbrev}\b', expansion, text)
        
        # Lemmatize if enabled
        if self.use_lemmatization and self.nlp:
            doc = self.nlp(text)
            tokens = [token.lemma_ for token in doc if token.is_alpha]
        else:
            tokens = text.split()
        
        # Filter stop words
        tokens = [t for t in tokens if t not in DOMAIN_STOP_WORDS and len(t) > 2]
        
        return tokens
```

**Files to Create/Modify:**
- Create: `src/resume_as_code/utils/tokenizer.py`
- Modify: `src/resume_as_code/services/ranker.py` (use new tokenizer)
- Modify: `pyproject.toml` (add spacy dependency, optional)

**Definition of Done:**
- [ ] Lemmatization reduces "engineering" → "engineer"
- [ ] Technical abbreviations expanded
- [ ] Hyphen/slash normalization
- [ ] Domain stop words filtered
- [ ] Optional spaCy dependency (graceful fallback)
- [ ] Unit tests for tokenization

---

## Story 7.11: Section-Level Semantic Embeddings

As a **job seeker**,
I want **my skills section matched against JD requirements and my outcomes matched against JD responsibilities**,
So that **semantic matching is more precise and relevant**.

**Story Points:** 8
**Priority:** P3 (complex but high value)

**Research Basis:** Pinecone research shows section-level embeddings reduce noise and improve precision. Full-document embedding dilutes significance of individual sections.

**Acceptance Criteria:**

**Given** a work unit with distinct sections (problem, actions, outcome, skills)
**When** embedding for semantic search
**Then** each section is embedded separately

**Given** section embeddings are computed
**When** matching against JD
**Then** work unit skills embed against JD skills section
**And** work unit outcomes embed against JD requirements section

**Given** section-level similarity scores
**When** aggregating to final score
**Then** weighted formula applies:
- Requirements match: 40%
- Experience match: 30%
- Skills match: 20%
- Education match: 10%

**Given** a work unit with strong skills match but weak experience match
**When** ranking
**Then** the weighted aggregate reflects partial relevance

**Given** embedding cache exists
**When** section embeddings are computed
**Then** each section is cached separately with section identifier

**Technical Notes:**
```python
# Modify embedder.py
class SectionEmbedding(BaseModel):
    """Embedding for a specific section of a work unit."""
    section: Literal["title", "problem", "actions", "outcome", "skills"]
    embedding: list[float]

def embed_work_unit_sections(self, work_unit: WorkUnit) -> dict[str, list[float]]:
    """Generate separate embeddings for each work unit section."""
    sections = {
        "title": work_unit.title,
        "problem": f"{work_unit.problem.statement} {work_unit.problem.context or ''}",
        "actions": " ".join(work_unit.actions),
        "outcome": f"{work_unit.outcome.result} {work_unit.outcome.quantified_impact or ''}",
        "skills": " ".join([s.name for s in work_unit.skills_demonstrated] + work_unit.tags),
    }
    
    return {
        section: self.embed_query(text)
        for section, text in sections.items()
        if text.strip()
    }

# Modify ranker.py
def _semantic_rank_sectioned(
    self, 
    jd: JobDescription, 
    work_units: list[WorkUnit]
) -> list[float]:
    """Semantic ranking with section-level matching."""
    weights = {
        "requirements": 0.4,
        "skills": 0.2,
        "experience": 0.3,
        "general": 0.1,
    }
    
    # Embed JD sections
    jd_requirements_emb = self.embedder.embed_passage(jd.requirements_text)
    jd_skills_emb = self.embedder.embed_passage(" ".join(jd.skills))
    
    scores = []
    for wu in work_units:
        wu_sections = self.embedder.embed_work_unit_sections(wu)
        
        # Cross-section matching
        req_score = cosine_sim(wu_sections.get("outcome", []), jd_requirements_emb)
        skill_score = cosine_sim(wu_sections.get("skills", []), jd_skills_emb)
        exp_score = cosine_sim(wu_sections.get("actions", []), jd_requirements_emb)
        
        # Weighted aggregate
        final = (
            weights["requirements"] * req_score +
            weights["skills"] * skill_score +
            weights["experience"] * exp_score
        )
        scores.append(final)
    
    return scores
```

**Files to Modify:**
- Modify: `src/resume_as_code/services/embedder.py` (section embedding)
- Modify: `src/resume_as_code/services/ranker.py` (sectioned semantic ranking)
- Modify: `src/resume_as_code/services/embedding_cache.py` (section-aware caching)
- Modify: `src/resume_as_code/models/config.py` (section weights config)

**Definition of Done:**
- [ ] Work units embedded as multiple section vectors
- [ ] JD embedded as requirements + skills sections
- [ ] Cross-section matching implemented
- [ ] Weighted aggregation to final score
- [ ] Section-aware embedding cache
- [ ] Unit tests for section matching

---

## Story 7.12: Seniority Level Matching

As a **job seeker**,
I want **my career level matched against the job's seniority requirements**,
So that **I'm not ranked for roles significantly above or below my experience**.

**Story Points:** 5
**Priority:** P3

**Research Basis:** LinkedIn and Eightfold use title embeddings and career trajectory to predict seniority fit. JD already has `experience_level` detected.

**Acceptance Criteria:**

**Given** a work unit with optional `seniority_level` field
**When** I set it to "senior"
**Then** it's stored and used for matching

**Given** a work unit without `seniority_level`
**When** ranking runs
**Then** seniority is inferred from position title and scope

**Given** JD with `experience_level: SENIOR`
**When** matching work units
**Then** work units with senior-level indicators score higher

**Given** a candidate with mostly mid-level work units
**When** matching against principal-level JD
**Then** seniority mismatch reduces overall score (configurable penalty)

**Given** seniority matching is disabled
**When** ranking runs
**Then** behavior unchanged (backward compatible)

**Technical Notes:**
```python
# Add to work_unit.py
from typing import Literal

SeniorityLevel = Literal["entry", "mid", "senior", "staff", "principal", "executive"]

class WorkUnit(BaseModel):
    # ... existing fields ...
    seniority_level: SeniorityLevel | None = Field(
        default=None,
        description="Optional seniority level for explicit matching"
    )

# Add seniority inference service
# src/resume_as_code/services/seniority_inference.py
TITLE_SENIORITY_PATTERNS = {
    "executive": ["cto", "ceo", "cfo", "vp ", "vice president", "chief"],
    "principal": ["principal", "distinguished", "fellow"],
    "staff": ["staff", "architect"],
    "senior": ["senior", "sr.", "sr ", "lead"],
    "mid": ["ii", "iii", "developer", "engineer"],
    "entry": ["junior", "jr.", "jr ", "associate", "intern"],
}

def infer_seniority(work_unit: WorkUnit, position: Position | None) -> SeniorityLevel:
    """Infer seniority from work unit title, position, and scope."""
    if work_unit.seniority_level:
        return work_unit.seniority_level
    
    title = (position.title if position else work_unit.title).lower()
    
    for level, patterns in TITLE_SENIORITY_PATTERNS.items():
        if any(p in title for p in patterns):
            return level
    
    # Check scope for executive indicators
    if position and position.scope:
        if position.scope.pl_responsibility or position.scope.revenue:
            return "executive"
        if position.scope.team_size and position.scope.team_size > 50:
            return "staff"
    
    return "mid"  # Default
```

**Schema Addition:**
```yaml
# Work unit seniority_level field
seniority_level:
  type: string
  enum: ["entry", "mid", "senior", "staff", "principal", "executive"]
  description: "Optional seniority level for explicit matching"
```

**Files to Create/Modify:**
- Modify: `src/resume_as_code/models/work_unit.py` (add seniority_level)
- Create: `src/resume_as_code/services/seniority_inference.py`
- Modify: `src/resume_as_code/services/ranker.py` (seniority scoring)
- Modify: `schemas/work-unit.schema.json` (auto-generated)

**Definition of Done:**
- [ ] Optional seniority_level field on WorkUnit
- [ ] Seniority inference from title patterns
- [ ] Seniority matching against JD.experience_level
- [ ] Configurable mismatch penalty
- [ ] Backward compatible when field not set

---

## Story 7.13: Impact Category Classification

As a **job seeker**,
I want **my achievements categorized by impact type and matched against role expectations**,
So that **my financial achievements rank higher for sales roles and my operational achievements rank higher for engineering roles**.

**Story Points:** 5
**Priority:** P3 (innovative - no existing research)

**Research Basis:** Novel enhancement based on resume best practices. Quantified impacts (with numbers) should weight higher than qualitative claims.

**Acceptance Criteria:**

**Given** a work unit outcome with financial metrics ("$500K revenue")
**When** impact classification runs
**Then** it's tagged as `financial` impact

**Given** a work unit outcome with operational metrics ("reduced latency 40%")
**When** impact classification runs
**Then** it's tagged as `operational` impact

**Given** JD for a sales role
**When** role type is inferred
**Then** `financial` and `customer` impacts are prioritized

**Given** JD for an engineering role
**When** role type is inferred
**Then** `operational` and `technical` impacts are prioritized

**Given** a work unit with quantified impact ("saved $2M annually")
**When** scoring
**Then** it receives boost over qualitative claims ("improved efficiency")

**Given** impact category matching
**When** generating match_reasons
**Then** reasons include impact alignment ("Financial impact aligns with Sales role")

**Technical Notes:**
```python
# src/resume_as_code/services/impact_classifier.py
from typing import Literal
import re

ImpactCategory = Literal["financial", "operational", "talent", "customer", "organizational", "technical"]

# Pattern-based classification
IMPACT_PATTERNS = {
    "financial": [
        r"\$[\d,]+[KMB]?",  # Dollar amounts
        r"revenue", r"cost sav", r"roi", r"profit", r"budget",
    ],
    "operational": [
        r"\d+%\s*(reduc|improv|increas|faster|efficiency)",
        r"automat", r"streamlin", r"optimiz", r"latency", r"uptime",
    ],
    "talent": [
        r"hired?\s+\d+", r"mentor", r"team\s+of\s+\d+", r"retention",
        r"onboard", r"train", r"coach",
    ],
    "customer": [
        r"nps", r"csat", r"customer\s+satisfaction", r"user\s+growth",
        r"churn", r"acquisition", r"retention",
    ],
    "organizational": [
        r"transform", r"culture", r"strategy", r"restructur",
        r"merger", r"acquisition", r"initiative",
    ],
    "technical": [
        r"architect", r"design", r"implement", r"deploy", r"scale",
        r"migration", r"infrastructure",
    ],
}

# Role type to expected impacts
ROLE_IMPACT_PRIORITY = {
    "sales": ["financial", "customer"],
    "engineering": ["operational", "technical"],
    "product": ["customer", "operational"],
    "hr": ["talent", "organizational"],
    "executive": ["organizational", "financial"],
    "marketing": ["customer", "financial"],
}

def classify_impact(outcome_text: str) -> list[tuple[ImpactCategory, float]]:
    """Classify outcome text into impact categories with confidence."""
    results = []
    text = outcome_text.lower()
    
    for category, patterns in IMPACT_PATTERNS.items():
        matches = sum(1 for p in patterns if re.search(p, text))
        if matches > 0:
            confidence = min(1.0, matches * 0.3)
            results.append((category, confidence))
    
    return sorted(results, key=lambda x: -x[1])

def has_quantified_impact(outcome_text: str) -> bool:
    """Check if outcome contains quantified metrics."""
    return bool(re.search(r'\d+[%$KMB]|\$[\d,]+|\d+x', outcome_text))
```

**Scoring Integration:**
```python
def _impact_alignment_score(
    self, 
    work_unit: WorkUnit, 
    jd: JobDescription
) -> float:
    """Score work unit impact alignment with role type."""
    outcome_text = f"{work_unit.outcome.result} {work_unit.outcome.quantified_impact or ''}"
    
    # Classify work unit impacts
    wu_impacts = classify_impact(outcome_text)
    
    # Infer role type from JD title
    role_type = infer_role_type(jd.title)
    expected_impacts = ROLE_IMPACT_PRIORITY.get(role_type, [])
    
    # Score alignment
    alignment_score = 0.0
    for impact, confidence in wu_impacts:
        if impact in expected_impacts:
            alignment_score += confidence * (1.0 if impact == expected_impacts[0] else 0.5)
    
    # Boost for quantified impacts
    if has_quantified_impact(outcome_text):
        alignment_score *= 1.25
    
    return min(1.0, alignment_score)
```

**Files to Create/Modify:**
- Create: `src/resume_as_code/services/impact_classifier.py`
- Modify: `src/resume_as_code/services/ranker.py` (integrate impact scoring)
- Modify: `src/resume_as_code/models/work_unit.py` (optional impact_category field)

**Definition of Done:**
- [ ] Impact classification from outcome text
- [ ] Role type inference from JD title
- [ ] Impact alignment scoring
- [ ] Quantified impact boost (25%)
- [ ] Match reasons include impact alignment
- [ ] Unit tests for classification patterns

---

## Story 7.14: JD-Relevant Content Curation

As a **job seeker**,
I want **my career highlights, certifications, and other sections intelligently selected based on JD relevance**,
So that **I can maintain a comprehensive profile while the algorithm surfaces the most appropriate items for each application**.

**Story Points:** 5
**Priority:** P2

**Research Basis:** (2024-2025 resume research, 18.4M resumes analyzed)

Cognitive load research confirms working memory limit of 5-7 items before fatigue:
- **Career highlights/Summary**: 3-5 bullet points maximum (research: 2-4 sentences)
- **Bullets per position**: 4-6 recent roles, 2-3 older positions
- **Skills**: 6-10 optimal (median 8-9), up to 12-15 mid-career, 15-20 senior
- **Certifications**: 3-5 most relevant to JD
- **Board roles**: 2-3 unless executive-level position

Key insight: Only 10% of resumes include quantified results despite 78% of recruiters citing this as top differentiator. Prioritizing quantified achievements provides massive competitive advantage.

**Acceptance Criteria:**

**Given** I have 8 career highlights configured
**When** generating a resume for a specific JD
**Then** the 4 most JD-relevant highlights are selected
**And** selection is based on keyword/semantic matching against JD

**Given** I have 10 certifications configured
**When** generating a resume for a JD requiring "AWS" and "Kubernetes"
**Then** AWS and Kubernetes certifications rank highest
**And** output limited to configured max (default 5)

**Given** I have 6 board roles configured
**When** generating a resume for a non-executive role
**Then** 2-3 most relevant board roles are selected
**And** executive roles show more board experience

**Given** the curation algorithm runs
**When** selecting items
**Then** each item is scored against JD using:
- Keyword overlap (BM25-style)
- Semantic similarity (embedding)
- Recency (more recent = higher score)

**Given** `resume plan --jd job.txt` runs
**When** displaying results
**Then** shows which highlights/certs/roles were selected
**And** shows relevance scores for transparency

**Given** I want to force-include specific items
**When** I set `priority: always` on an item
**Then** it's always included regardless of JD relevance

**Given** a position from 2 years ago with 8 work unit bullets
**When** generating resume output
**Then** only the 4-6 most JD-relevant bullets are selected

**Given** a position from 7 years ago with 6 work unit bullets
**When** generating resume output
**Then** only the 2-3 most JD-relevant bullets are selected
**And** recency decay is applied (older positions get fewer bullets)

**Given** work units with quantified outcomes ("saved $2M", "40% faster")
**When** selecting bullets
**Then** quantified achievements are boosted 25% in scoring
**And** they are prioritized for inclusion

**Technical Notes:**
```python
# src/resume_as_code/services/content_curator.py
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass
class CurationResult(Generic[T]):
    """Result of content curation."""
    selected: list[T]
    excluded: list[T]
    scores: dict[str, float]  # item_id -> relevance score

# Research-backed limits (2024-2025 resume studies)
SECTION_LIMITS = {
    "career_highlights": 4,       # Research: 3-5 optimal
    "certifications": 5,          # Research: 3-5 most relevant
    "board_roles": 3,             # 2-3 unless executive role
    "publications": 3,            # Keep focused
    "skills": 10,                 # Research: 6-10 optimal (median 8-9)
}

# Bullets per position based on recency
BULLETS_PER_POSITION = {
    "recent": (4, 6),    # 0-3 years: 4-6 bullets
    "mid": (3, 4),       # 3-7 years: 3-4 bullets
    "older": (2, 3),     # 7+ years: 2-3 bullets
}

class ContentCurator:
    """Curates resume content based on JD relevance."""
    
    def __init__(
        self,
        embedder: EmbeddingService,
        limits: dict[str, int] | None = None,
    ):
        self.embedder = embedder
        self.limits = limits or SECTION_LIMITS
    
    def curate_highlights(
        self,
        highlights: list[str],
        jd: JobDescription,
        max_count: int | None = None,
    ) -> CurationResult[str]:
        """Select most JD-relevant career highlights."""
        max_count = max_count or self.limits["career_highlights"]
        
        # Score each highlight
        jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)
        scores = {}
        
        for i, highlight in enumerate(highlights):
            highlight_emb = self.embedder.embed_query(highlight)
            semantic_score = cosine_similarity(highlight_emb, jd_embedding)
            
            # Keyword overlap bonus
            keyword_score = self._keyword_overlap(highlight, jd.keywords)
            
            # Combined score
            scores[f"highlight_{i}"] = (0.6 * semantic_score) + (0.4 * keyword_score)
        
        # Sort and select top N
        ranked = sorted(
            enumerate(highlights),
            key=lambda x: scores[f"highlight_{x[0]}"],
            reverse=True,
        )
        
        selected = [h for _, h in ranked[:max_count]]
        excluded = [h for _, h in ranked[max_count:]]
        
        return CurationResult(
            selected=selected,
            excluded=excluded,
            scores=scores,
        )
    
    def curate_certifications(
        self,
        certifications: list[Certification],
        jd: JobDescription,
        max_count: int | None = None,
    ) -> CurationResult[Certification]:
        """Select most JD-relevant certifications."""
        max_count = max_count or self.limits["certifications"]
        
        # Priority items always included
        always_include = [c for c in certifications if getattr(c, "priority", None) == "always"]
        candidates = [c for c in certifications if c not in always_include]
        
        # Score candidates
        scores = {}
        jd_skills = set(s.lower() for s in jd.skills)
        
        for cert in candidates:
            # Direct skill match (cert name contains JD skill)
            skill_match = sum(
                1 for skill in jd_skills 
                if skill in cert.name.lower() or skill in (cert.issuer or "").lower()
            )
            
            # Semantic similarity
            cert_text = f"{cert.name} {cert.issuer or ''}"
            cert_emb = self.embedder.embed_query(cert_text)
            jd_emb = self.embedder.embed_passage(jd.text_for_ranking)
            semantic_score = cosine_similarity(cert_emb, jd_emb)
            
            # Recency bonus (active certs score higher)
            recency_bonus = 1.0 if cert.get_status() == "active" else 0.5
            
            scores[cert.name] = (skill_match * 0.5) + (semantic_score * 0.3) + (recency_bonus * 0.2)
        
        # Rank and select
        ranked = sorted(candidates, key=lambda c: scores[c.name], reverse=True)
        remaining_slots = max(0, max_count - len(always_include))
        
        selected = always_include + ranked[:remaining_slots]
        excluded = ranked[remaining_slots:]
        
        return CurationResult(selected=selected, excluded=excluded, scores=scores)

    def curate_position_bullets(
        self,
        position: Position,
        work_units: list[WorkUnit],
        jd: JobDescription,
    ) -> CurationResult[WorkUnit]:
        """Select most JD-relevant work units for a position, respecting recency limits."""
        from datetime import date

        # Determine position age and bullet limits
        years_ago = self._position_age_years(position)
        if years_ago <= 3:
            min_bullets, max_bullets = BULLETS_PER_POSITION["recent"]
        elif years_ago <= 7:
            min_bullets, max_bullets = BULLETS_PER_POSITION["mid"]
        else:
            min_bullets, max_bullets = BULLETS_PER_POSITION["older"]

        # Score each work unit
        jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)
        scores = {}

        for wu in work_units:
            wu_text = extract_work_unit_text(wu)
            wu_emb = self.embedder.embed_query(wu_text)
            semantic_score = cosine_similarity(wu_emb, jd_embedding)

            # Boost for quantified outcomes
            quantified_boost = 1.25 if has_quantified_impact(wu.outcome) else 1.0

            scores[wu.id] = semantic_score * quantified_boost

        # Rank and select within limits
        ranked = sorted(work_units, key=lambda wu: scores[wu.id], reverse=True)
        selected = ranked[:max_bullets]
        excluded = ranked[max_bullets:]

        return CurationResult(selected=selected, excluded=excluded, scores=scores)

def has_quantified_impact(outcome) -> bool:
    """Check if outcome contains quantified metrics."""
    import re
    text = f"{outcome.result} {outcome.quantified_impact or ''}"
    return bool(re.search(r'\d+[%$KMB]|\$[\d,]+|\d+x|\d+\s*(hours?|days?|weeks?)', text))
```

**Config Extension:**
```yaml
# .resume.yaml
curation:
  career_highlights:
    max_display: 4          # Research: 3-5 optimal
    min_relevance: 0.3      # Minimum score to include
  certifications:
    max_display: 5          # Research: 3-5 most relevant
    min_relevance: 0.2
  board_roles:
    max_display: 3
    executive_max: 5        # More for executive roles
  publications:
    max_display: 3
  skills:
    max_display: 10         # Research: 6-10 optimal (median 8-9)
  bullets_per_position:
    recent_years: 3         # 0-3 years ago
    recent_max: 6           # 4-6 bullets
    mid_years: 7            # 3-7 years ago
    mid_max: 4              # 3-4 bullets
    older_max: 3            # 7+ years: 2-3 bullets
  quantified_boost: 1.25    # 25% boost for quantified achievements
```

**Model Enhancement:**
```python
# Add priority field to relevant models
class Certification(BaseModel):
    # ... existing fields ...
    priority: Literal["always", "normal", "low"] | None = Field(
        default=None,
        description="Priority for curation: 'always' forces inclusion"
    )

class BoardRole(BaseModel):
    # ... existing fields ...
    priority: Literal["always", "normal", "low"] | None = None
```

**Files to Create/Modify:**
- Create: `src/resume_as_code/services/content_curator.py`
- Modify: `src/resume_as_code/models/config.py` (add CurationConfig)
- Modify: `src/resume_as_code/models/certification.py` (add priority field)
- Modify: `src/resume_as_code/models/board_role.py` (add priority field)
- Modify: `src/resume_as_code/commands/plan.py` (integrate curation)
- Modify: `src/resume_as_code/models/resume.py` (use curated content)

**Definition of Done:**
- [ ] ContentCurator service with curate_* methods
- [ ] Career highlights curation (max 4)
- [ ] Certification curation with skill matching
- [ ] Board role curation (context-aware limits)
- [ ] Position bullets curation based on recency (4-6 recent, 3-4 mid, 2-3 older)
- [ ] Quantified achievement boost (25% for metrics-backed outcomes)
- [ ] Priority field for force-inclusion
- [ ] Plan command shows curation decisions
- [ ] Configurable limits via .resume.yaml
- [ ] Unit tests for curation logic

---

## Story 7.15: Comprehensive Algorithm Documentation

As a **developer or future maintainer**,
I want **complete documentation of the matching algorithm, its components, configuration options, and tuning guidance**,
So that **I can understand, debug, tune, and extend the algorithm with confidence**.

**Story Points:** 3
**Priority:** P1 (should be done alongside or after algorithm implementation)

**Acceptance Criteria:**

**Given** I am a new developer joining the project
**When** I read the algorithm documentation
**Then** I understand the complete matching pipeline end-to-end
**And** I can trace how a work unit score is calculated

**Given** the documentation exists
**When** I look for algorithm details
**Then** I find:
- Architecture overview with data flow diagram
- Each scoring component explained (BM25, Semantic, RRF)
- All configuration parameters with defaults and valid ranges
- Mathematical formulas with worked examples
- Tuning guide with recommended starting points

**Given** I want to tune the algorithm for a specific use case
**When** I consult the tuning guide
**Then** I find concrete recommendations for:
- Executive vs IC resumes
- Technical vs non-technical roles
- Career changers vs domain experts
- Entry-level vs senior positions

**Given** the algorithm changes in the future
**When** developers update the code
**Then** documentation includes a changelog section
**And** version compatibility notes

**Documentation Structure:**

```markdown
# docs/algorithm/README.md - Algorithm Documentation

# Table of Contents
1. Overview & Architecture
2. Matching Pipeline
3. Scoring Components
4. Content Curation
5. Configuration Reference
6. Tuning Guide
7. Troubleshooting
8. Changelog

# 1. Overview & Architecture

## Purpose
The Resume-as-Code matching algorithm selects and ranks Work Units
based on relevance to a target Job Description (JD). It combines
lexical matching (BM25) with semantic understanding (embeddings)
using Reciprocal Rank Fusion (RRF).

## High-Level Flow
```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Job         │───▶│ JD Parser    │───▶│ JobDescription  │
│ Description │    │              │    │ (structured)    │
└─────────────┘    └──────────────┘    └────────┬────────┘
                                                │
┌─────────────┐    ┌──────────────┐             │
│ Work Units  │───▶│ WU Loader    │─────────────┼─────────┐
│ (YAML)      │    │              │             │         │
└─────────────┘    └──────────────┘             ▼         ▼
                                       ┌─────────────────────────┐
                                       │   Hybrid Ranker         │
                                       │ ┌─────────┐ ┌─────────┐ │
                                       │ │ BM25    │ │Semantic │ │
                                       │ │ Scorer  │ │ Scorer  │ │
                                       │ └────┬────┘ └────┬────┘ │
                                       │      │           │      │
                                       │      ▼           ▼      │
                                       │   ┌─────────────────┐   │
                                       │   │   RRF Fusion    │   │
                                       │   └────────┬────────┘   │
                                       └────────────┼────────────┘
                                                    │
                                       ┌────────────▼────────────┐
                                       │   Recency Decay         │
                                       │   Field Weights         │
                                       │   Quantified Boost      │
                                       └────────────┬────────────┘
                                                    │
                                       ┌────────────▼────────────┐
                                       │   Content Curator       │
                                       │   (Section Limits)      │
                                       └────────────┬────────────┘
                                                    ▼
                                       ┌─────────────────────────┐
                                       │   Ranked Work Units     │
                                       │   + Curated Sections    │
                                       └─────────────────────────┘
```

# 2. Matching Pipeline

## Step 1: JD Parsing
Extracts structured data from job description text:
- `title`: Job title for seniority matching
- `skills`: Required/preferred skills (explicit + inferred)
- `experience_level`: junior/mid/senior/staff/principal/executive
- `keywords`: Important terms for BM25 matching
- `text_for_ranking`: Concatenated text for embedding

## Step 2: Work Unit Loading
Loads all Work Units from `work-units/*.yaml`:
- Validates against schema
- Enriches with position data (employer, dates)
- Extracts searchable text fields

## Step 3: Hybrid Scoring
Each Work Unit receives two independent scores:

### BM25 Score (Lexical)
Term frequency-inverse document frequency scoring:
```
BM25(wu, jd) = Σ IDF(term) × (tf × (k1 + 1)) / (tf + k1 × (1 - b + b × |D|/avgdl))

Where:
- k1 = 1.5 (term frequency saturation)
- b = 0.75 (length normalization)
- tf = term frequency in work unit
- |D| = work unit length
- avgdl = average document length
```

**Field Weights** (Story 7.8):
```python
FIELD_WEIGHTS = {
    "title": 3.0,        # Job title matches weighted heavily
    "skills": 2.0,       # Skill matches important
    "outcome": 1.5,      # Results matter
    "actions": 1.0,      # Base weight
    "problem": 1.0,      # Context
}
```

### Semantic Score
Cosine similarity between embeddings:
```
semantic(wu, jd) = cos(embed(wu.text), embed(jd.text_for_ranking))

Where:
- embed() = sentence-transformers model (all-MiniLM-L6-v2 default)
- cos() = cosine similarity [-1, 1] normalized to [0, 1]
```

**Section-Level Embeddings** (Story 7.11):
```python