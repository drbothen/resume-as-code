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
**Total Points:** 34

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
See Story 7.11 for implementation details.

**Definition of Done:**
- [ ] docs/algorithm/README.md created with complete algorithm documentation
- [ ] Architecture diagram with data flow
- [ ] All scoring components explained with formulas
- [ ] Configuration reference with defaults and ranges
- [ ] Tuning guide for different resume types
- [ ] Changelog section for version tracking

---

## Story 7.18: Score Actions Against JD

As a **job seeker**,
I want **action bullets within work units scored against JD relevance**,
So that **only the most relevant actions are included, keeping executive resumes concise while maximizing impact**.

**Story Points:** 5
**Priority:** P2

**Problem Statement:**
Currently, work units render up to 4 bullets per position (1 result + 3 actions). For executive templates like CTO, this creates overly long resumes (4+ pages instead of 2). While the `cto-results` template shows only results, some actions ARE relevant and should be included.

**Research Basis:**
- Executive resumes should be 2 pages maximum (Harvard Business Review 2023)
- Actions that directly match JD requirements provide supporting evidence for results
- 78% of recruiters cite quantified results as top differentiator (2024 resume research)

**Acceptance Criteria:**

**Given** a work unit with 5+ actions
**When** building a resume against a JD
**Then** only the 1-2 most JD-relevant actions are included
**And** irrelevant actions are excluded

**Given** an action containing JD keywords ("Kubernetes", "CI/CD")
**When** scoring actions
**Then** that action scores higher than actions without keyword matches

**Given** an action with quantified impact ("reduced build time 40%")
**When** scoring actions
**Then** that action receives a 25% scoring boost

**Given** configuration `max_actions_per_wu: 2`
**When** building resume
**Then** at most 2 action bullets are included per work unit
**And** the result bullet is always included (not counted against limit)

**Given** all actions in a work unit score below threshold (0.2)
**When** building resume
**Then** only the result bullet is shown (no action bullets)

**Given** configuration `action_scoring_enabled: false`
**When** building resume
**Then** original behavior is used (first N actions, no scoring)
**And** no JD-based filtering is applied

**Given** default configuration (action_scoring_enabled not set)
**When** building resume with a JD
**Then** action scoring is enabled by default

**Given** `resume plan --jd job.txt --show-actions`
**When** displaying results
**Then** shows which actions were selected/excluded per work unit
**And** shows relevance scores for each action

**Technical Notes:**
```python
# src/resume_as_code/services/action_scorer.py
from dataclasses import dataclass

@dataclass
class ScoredAction:
    """Action with JD relevance score."""
    text: str
    score: float
    match_reasons: list[str]

class ActionScorer:
    """Score work unit actions against JD for relevance."""

    def __init__(self, embedder: EmbeddingService):
        self.embedder = embedder

    def score_actions(
        self,
        actions: list[str],
        jd: JobDescription,
        max_actions: int = 2,
        min_score: float = 0.2,
    ) -> list[ScoredAction]:
        """Score and select most relevant actions.

        Args:
            actions: List of action bullet texts.
            jd: Target job description.
            max_actions: Maximum actions to include.
            min_score: Minimum score threshold.

        Returns:
            List of scored actions, sorted by relevance.
        """
        jd_embedding = self.embedder.embed_passage(jd.text_for_ranking)
        jd_keywords = set(k.lower() for k in jd.keywords)

        scored = []
        for action in actions:
            # Semantic similarity
            action_emb = self.embedder.embed_query(action)
            semantic_score = cosine_similarity(action_emb, jd_embedding)

            # Keyword overlap
            action_lower = action.lower()
            keyword_matches = [k for k in jd_keywords if k in action_lower]
            keyword_score = min(1.0, len(keyword_matches) * 0.3)

            # Quantified impact boost
            quantified_boost = 1.25 if has_quantified_impact(action) else 1.0

            # Combined score
            score = ((0.6 * semantic_score) + (0.4 * keyword_score)) * quantified_boost

            scored.append(ScoredAction(
                text=action,
                score=score,
                match_reasons=[f"keyword: {k}" for k in keyword_matches],
            ))

        # Filter by threshold and limit
        filtered = [a for a in scored if a.score >= min_score]
        filtered.sort(key=lambda a: a.score, reverse=True)

        return filtered[:max_actions]

def has_quantified_impact(text: str) -> bool:
    """Check if text contains quantified metrics."""
    import re
    return bool(re.search(r'\d+[%$KMB]|\$[\d,]+|\d+x|\d+\s*(hours?|days?|weeks?)', text))
```

**Integration with _extract_bullets:**
```python
# Modify resume.py _extract_bullets to optionally score actions
@staticmethod
def _extract_bullets(
    work_unit: dict[str, Any],
    jd: JobDescription | None = None,
    action_scorer: ActionScorer | None = None,
    max_actions: int = 3,
) -> list[ResumeBullet]:
    """Extract bullets with optional JD-based action filtering."""
    bullets: list[ResumeBullet] = []

    # Main outcome as primary bullet (always included)
    outcome = work_unit.get("outcome", {}) or {}
    if result := outcome.get("result"):
        bullets.append(ResumeBullet(text=result, metrics=outcome.get("quantified_impact")))

    # Actions - scored if JD available, otherwise first N
    actions = work_unit.get("actions", [])

    if jd and action_scorer:
        scored_actions = action_scorer.score_actions(actions, jd, max_actions=max_actions)
        for scored in scored_actions:
            bullets.append(ResumeBullet(text=scored.text))
    else:
        # Fallback: first N actions
        for action in actions[:max_actions]:
            bullets.append(ResumeBullet(text=action))

    return bullets
```

**Config Extension:**
```yaml
# .resume.yaml
curation:
  action_scoring_enabled: true    # Enable JD-based action scoring (default: true)
  max_actions_per_work_unit: 2    # Default for executive templates
  action_min_score: 0.2           # Minimum relevance threshold
  action_quantified_boost: 1.25   # Boost for quantified actions
```

**Disabling Action Scoring:**
```yaml
# To use original behavior (first N actions, no JD scoring):
curation:
  action_scoring_enabled: false
  max_actions_per_work_unit: 3    # Takes first 3 actions per work unit
```

**Files to Create/Modify:**
- Create: `src/resume_as_code/services/action_scorer.py`
- Modify: `src/resume_as_code/models/resume.py` (_extract_bullets with scoring)
- Modify: `src/resume_as_code/models/config.py` (add action curation config)
- Modify: `src/resume_as_code/commands/plan.py` (--show-actions flag)
- Modify: `src/resume_as_code/commands/build.py` (integrate action scoring)

**Definition of Done:**
- [ ] ActionScorer service with score_actions() method
- [ ] Actions scored using semantic + keyword matching
- [ ] Quantified action boost (25%)
- [ ] Configurable max_actions and min_score
- [ ] `action_scoring_enabled` config option (default: true)
- [ ] Setting `action_scoring_enabled: false` reverts to original behavior
- [ ] _extract_bullets integrates action scoring when JD available
- [ ] plan command shows action selection with --show-actions
- [ ] Unit tests for action scoring (enabled and disabled modes)
- [ ] Executive templates use action scoring by default

---

## Story 7.19: Tailored Resume Notice

As a **job seeker**,
I want **an optional footer notice indicating this resume is tailored for the role**,
So that **recruiters understand relevant details were prioritized and can request my full history**.

**Story Points:** 2
**Priority:** P3

**Problem Statement:**
When resumes are tailored for specific JDs, some experience is intentionally omitted or condensed. Recruiters may wonder about gaps or want more details. A subtle footer notice sets expectations and invites further conversation.

**Research Basis:**
- Executive resume best practice: communicate that content is curated
- Opens door for "tell me more" conversations in interviews
- Professional way to acknowledge tailoring without appearing incomplete

**Acceptance Criteria:**

**Given** configuration `tailored_notice: true` in .resume.yaml
**When** building a resume
**Then** a footer notice appears on the last page
**And** the notice reads: "This resume highlights experience most relevant to this role. Full details available upon request."

**Given** CLI flag `--tailored-notice`
**When** building a resume
**Then** the footer notice is included regardless of config setting

**Given** CLI flag `--no-tailored-notice`
**When** building a resume
**Then** the footer notice is excluded regardless of config setting

**Given** neither config nor CLI flag is set
**When** building a resume
**Then** no footer notice is included (opt-in by default)

**Given** configuration `tailored_notice_text: "Custom message here"`
**When** building a resume
**Then** the custom text is used instead of the default

**Given** the footer notice is enabled
**When** viewing the rendered PDF
**Then** the notice appears as subtle text at the bottom of the last page
**And** it uses smaller font (8-9pt) and muted color
**And** it does not interfere with main resume content

**Technical Notes:**
```python
# src/resume_as_code/models/config.py
class ResumeConfig(BaseModel):
    # ... existing fields ...
    tailored_notice: bool = Field(
        default=False,
        description="Show footer notice that resume is tailored"
    )
    tailored_notice_text: str | None = Field(
        default=None,
        description="Custom tailored notice text (overrides default)"
    )

DEFAULT_TAILORED_NOTICE = (
    "This resume highlights experience most relevant to this role. "
    "Full details available upon request."
)
```

**CLI Integration:**
```python
# src/resume_as_code/commands/build.py
@click.option(
    "--tailored-notice/--no-tailored-notice",
    default=None,
    help="Include/exclude tailored resume footer notice"
)
def build(tailored_notice: bool | None, ...):
    # CLI flag overrides config
    if tailored_notice is not None:
        config.tailored_notice = tailored_notice
```

**Template Integration:**
```html
{# Add to base of all templates before </body> #}
{% if tailored_notice %}
<footer class="tailored-notice">
    {{ tailored_notice_text }}
</footer>
{% endif %}
```

**CSS Styling:**
```css
.tailored-notice {
    position: running(tailored-footer);
    font-size: 8pt;
    color: #666;
    text-align: center;
    font-style: italic;
    margin-top: 2em;
    padding-top: 0.5em;
    border-top: 1px solid #ddd;
}

@page :last {
    @bottom-center {
        content: element(tailored-footer);
    }
}
```

**Config Extension:**
```yaml
# .resume.yaml
tailored_notice: true
tailored_notice_text: "Tailored resume. Complete history available on request."
```

**Files to Create/Modify:**
- Modify: `src/resume_as_code/models/config.py` (add tailored_notice fields)
- Modify: `src/resume_as_code/commands/build.py` (add CLI flag)
- Modify: `src/resume_as_code/services/template_service.py` (pass notice to templates)
- Modify: All template HTML files (add conditional footer)
- Modify: All template CSS files (add footer styling)

**Definition of Done:**
- [ ] `tailored_notice` config option (default: false)
- [ ] `tailored_notice_text` config option for custom text
- [ ] `--tailored-notice` / `--no-tailored-notice` CLI flags
- [ ] CLI flags override config settings
- [ ] Footer renders on last page of all templates
- [ ] Subtle styling (small font, muted color)
- [ ] Unit tests for config and CLI integration
- [ ] CLAUDE.md updated with new CLI option

---

## Story 7.20: Employment Continuity & Gap Detection

As a **job seeker**,
I want **my resume to maintain employment timeline continuity when work units are filtered by relevance**,
So that **tailored resumes don't appear to have unexplained employment gaps**.

**Story Points:** 3
**Priority:** P2

**Problem Statement:**
When filtering work units by JD relevance, entire positions may be excluded if none of their work units score highly enough. This creates apparent employment gaps that raise red flags for recruiters, even though the candidate was continuously employed.

**Research Basis:**
- Employment gaps >3 months trigger ATS/recruiter scrutiny
- Timeline continuity is a basic resume hygiene requirement
- Tailoring should curate content, not create false narratives

**Acceptance Criteria:**

**Given** configuration `employment_continuity: minimum_bullet` (default)
**When** filtering work units by JD relevance
**Then** at least one work unit is included from each position
**And** the highest-scoring work unit is selected even if below threshold

**Given** configuration `employment_continuity: allow_gaps`
**When** filtering work units by JD relevance
**Then** pure relevance filtering is applied
**And** positions with no relevant work units are excluded

**Given** `employment_continuity: allow_gaps` is set
**When** running `resume plan --jd job.txt`
**Then** gap detection analyzes the resulting timeline
**And** gaps >3 months are reported with warnings

**Given** a gap is detected during `plan`
**When** displaying results
**Then** warning shows: "⚠️ Employment Gap Detected"
**And** shows which position(s) would be omitted
**And** shows gap duration between positions
**And** suggests using `--no-allow-gaps` to force minimum inclusion

**Given** CLI flag `--allow-gaps`
**When** building a resume
**Then** `employment_continuity: allow_gaps` behavior is used
**And** gap detection warnings are shown

**Given** CLI flag `--no-allow-gaps`
**When** building a resume
**Then** `employment_continuity: minimum_bullet` behavior is used
**And** at least one bullet per position is guaranteed

**Given** `--show-excluded` flag is used with detected gaps
**When** displaying excluded work units
**Then** excluded work units that would cause gaps are flagged
**And** shows "⚠️ Excluding this creates X-month gap"

**Technical Notes:**
```python
# src/resume_as_code/services/employment_continuity.py
from dataclasses import dataclass
from datetime import date
from typing import Literal

EmploymentContinuityMode = Literal["minimum_bullet", "allow_gaps"]

@dataclass
class EmploymentGap:
    """Detected gap in employment timeline."""
    start_date: date
    end_date: date
    duration_months: int
    missing_position_id: str
    missing_employer: str

class EmploymentContinuityService:
    """Ensure employment timeline continuity in tailored resumes."""

    def __init__(self, mode: EmploymentContinuityMode = "minimum_bullet"):
        self.mode = mode

    def ensure_continuity(
        self,
        positions: list[Position],
        selected_work_units: list[WorkUnit],
        all_work_units: list[WorkUnit],
    ) -> list[WorkUnit]:
        """Ensure at least one work unit per position if mode is minimum_bullet.

        Args:
            positions: All positions in timeline.
            selected_work_units: Work units selected by relevance scoring.
            all_work_units: All available work units.

        Returns:
            Updated list of work units with continuity guaranteed.
        """
        if self.mode == "allow_gaps":
            return selected_work_units

        # Find positions with no selected work units
        selected_position_ids = {wu.position_id for wu in selected_work_units if wu.position_id}

        result = list(selected_work_units)

        for position in positions:
            if position.id not in selected_position_ids:
                # Find highest-scoring work unit for this position
                position_wus = [wu for wu in all_work_units if wu.position_id == position.id]
                if position_wus:
                    # Select the one with highest score (if scores available) or first
                    best_wu = max(position_wus, key=lambda wu: getattr(wu, '_relevance_score', 0))
                    result.append(best_wu)

        return result

    def detect_gaps(
        self,
        positions: list[Position],
        selected_work_units: list[WorkUnit],
        min_gap_months: int = 3,
    ) -> list[EmploymentGap]:
        """Detect employment gaps in the filtered resume.

        Args:
            positions: All positions in timeline.
            selected_work_units: Work units selected for resume.
            min_gap_months: Minimum gap duration to report.

        Returns:
            List of detected employment gaps.
        """
        # Get positions that have work units in the selection
        included_position_ids = {wu.position_id for wu in selected_work_units if wu.position_id}
        included_positions = [p for p in positions if p.id in included_position_ids]
        excluded_positions = [p for p in positions if p.id not in included_position_ids]

        if not excluded_positions:
            return []

        gaps = []

        # Sort all positions by start date
        all_sorted = sorted(positions, key=lambda p: p.start_date or "")

        for excluded in excluded_positions:
            # Find the gap this exclusion creates
            exc_start = self._parse_date(excluded.start_date)
            exc_end = self._parse_date(excluded.end_date) or date.today()

            # Check if there's a gap before and after this position
            gap_months = self._calculate_gap_months(exc_start, exc_end)

            if gap_months >= min_gap_months:
                gaps.append(EmploymentGap(
                    start_date=exc_start,
                    end_date=exc_end,
                    duration_months=gap_months,
                    missing_position_id=excluded.id,
                    missing_employer=excluded.employer,
                ))

        return gaps

    def format_gap_warning(self, gaps: list[EmploymentGap]) -> str:
        """Format gap warnings for display."""
        if not gaps:
            return ""

        lines = ["⚠️  Employment Gap Detected"]
        for gap in gaps:
            lines.append(f"    Missing: {gap.missing_employer} ({gap.start_date} to {gap.end_date})")
            lines.append(f"    Gap: {gap.duration_months} months")
        lines.append("")
        lines.append("    Suggestion: Using --no-allow-gaps will include 1 bullet from each position")

        return "\n".join(lines)
```

**Config Extension:**
```yaml
# .resume.yaml
employment_continuity: minimum_bullet  # Options: minimum_bullet | allow_gaps
# minimum_bullet (default): Always include at least 1 work unit per position
# allow_gaps: Pure relevance filtering, but warns about detected gaps
```

**CLI Integration:**
```python
# src/resume_as_code/commands/build.py
@click.option(
    "--allow-gaps/--no-allow-gaps",
    default=None,
    help="Allow/prevent employment gaps in tailored resume"
)
def build(allow_gaps: bool | None, ...):
    # CLI flag overrides config
    if allow_gaps is not None:
        mode = "allow_gaps" if allow_gaps else "minimum_bullet"
        config.employment_continuity = mode
```

**Integration with plan command:**
```python
# src/resume_as_code/commands/plan.py
def display_plan(plan: ResumePlan, config: ResumeConfig, show_excluded: bool):
    # ... existing display logic ...

    # Gap detection (always runs when allow_gaps mode)
    if config.employment_continuity == "allow_gaps":
        continuity_svc = EmploymentContinuityService(mode="allow_gaps")
        gaps = continuity_svc.detect_gaps(
            positions=all_positions,
            selected_work_units=plan.selected_work_units,
        )

        if gaps:
            console.print(continuity_svc.format_gap_warning(gaps), style="yellow")
```

**Files to Create/Modify:**
- Create: `src/resume_as_code/services/employment_continuity.py`
- Modify: `src/resume_as_code/models/config.py` (add employment_continuity field)
- Modify: `src/resume_as_code/commands/plan.py` (add gap detection display)
- Modify: `src/resume_as_code/commands/build.py` (add --allow-gaps flag)
- Modify: `src/resume_as_code/services/ranker.py` (integrate continuity service)

**Definition of Done:**
- [ ] `employment_continuity` config option (default: minimum_bullet)
- [ ] EmploymentContinuityService with ensure_continuity() method
- [ ] Gap detection with configurable minimum (default 3 months)
- [ ] `--allow-gaps` / `--no-allow-gaps` CLI flags
- [ ] CLI flags override config settings
- [ ] Gap warnings displayed during `plan` command
- [ ] `--show-excluded` flags work units that would cause gaps
- [ ] Unit tests for continuity and gap detection
- [ ] CLAUDE.md updated with new CLI option

---

## Story 7.21: Resume Init Command

As a **new user**,
I want **a `resume init` command to scaffold my project with sensible defaults**,
So that **I can quickly start capturing work units without manually creating config files**.

**Story Points:** 3
**Priority:** P2

**Acceptance Criteria:**

**Given** I run `resume init` in a directory without `.resume.yaml`
**When** the command completes
**Then** `.resume.yaml` is created with default configuration
**And** `work-units/` directory is created
**And** `positions.yaml` is created with empty list

**Given** I run `resume init` interactively
**When** prompts appear
**Then** I can enter my name, email, phone, location, LinkedIn, GitHub, website
**And** these are saved to `profile` section in `.resume.yaml`

**Given** I run `resume init --non-interactive`
**When** the command completes
**Then** files are created with placeholder values
**And** no prompts are displayed

**Given** `.resume.yaml` already exists in the directory
**When** I run `resume init`
**Then** command fails with exit code 1
**And** error message says: "Project already initialized. Use --force to reinitialize."

**Given** `.resume.yaml` exists and I run `resume init --force`
**When** prompted for confirmation
**Then** existing config is backed up to `.resume.yaml.bak`
**And** new config is created

**Given** I run `resume init`
**When** the command completes successfully
**Then** a success message shows what was created
**And** suggests next steps: `resume new position` and `resume new work-unit`

**Files to Create/Modify:**
- Create: `src/resume_as_code/commands/init.py`
- Modify: `src/resume_as_code/cli.py` (add init command)

**Definition of Done:**
- [ ] `resume init` command creates .resume.yaml, work-units/, positions.yaml
- [ ] Interactive mode prompts for profile info
- [ ] `--non-interactive` flag uses defaults without prompts
- [ ] Error if .resume.yaml exists (exit code 1)
- [ ] `--force` flag backs up and reinitializes
- [ ] Success output with next steps
- [ ] CLAUDE.md updated with new command
- [ ] Unit tests for all modes