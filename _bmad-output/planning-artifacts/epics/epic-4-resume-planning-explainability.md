# Epic 4: Resume Planning & Explainability

**Goal:** Users can run `resume plan` and see exactly what will be included/excluded with reasons (Journey 2: "The Plan")

**FRs Covered:** FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19

---

## Story 4.1: Job Description Parser

As a **developer**,
I want **to extract structured information from job descriptions**,
So that **the ranking algorithm has clean data to work with**.

**Acceptance Criteria:**

**Given** a plain text job description file
**When** the parser processes it
**Then** it extracts a list of skills/technologies mentioned
**And** it extracts key requirements and responsibilities
**And** it identifies experience level indicators (senior, staff, lead, etc.)

**Given** a JD with varied formatting (bullets, paragraphs, sections)
**When** the parser processes it
**Then** it handles all formats gracefully
**And** extracts meaningful content regardless of structure

**Given** a JD file path
**When** I pass it to the parser
**Then** the file is read and parsed
**And** a `JobDescription` model is returned with extracted data

**Given** the parser extracts skills
**When** I inspect the output
**Then** skills are normalized (e.g., "Python 3" → "python", "K8s" → "kubernetes")

**Technical Notes:**
- Create `models/job_description.py` with Pydantic model
- Create parsing logic in `services/planner.py`
- Use simple keyword extraction (no ML required for MVP)
- Store raw text plus extracted structured data

---

## Story 4.1.5: Embedding Service & Cache *(Enabling Story)* (Research-Validated 2026-01-10)

As a **system**,
I want **an embedding service with intelligent caching and model versioning**,
So that **semantic search is fast and embeddings remain valid across model updates**.

> **Note:** This is an enabling story that provides infrastructure for Story 4.2 (BM25 Ranking Engine). It does not deliver direct user value but is required for semantic ranking.

**Acceptance Criteria:**

**Given** the embedding service is initialized
**When** I load the model
**Then** the model hash is computed from weights for cache key generation
**And** the hash is stored for all subsequent cache operations

**Given** I request embeddings for text
**When** the text exists in cache with matching model hash
**Then** the cached embedding is returned without recomputation
**And** retrieval completes in <10ms

**Given** I request embeddings for text
**When** the cache miss occurs or model hash differs
**Then** the embedding is computed fresh
**And** the result is stored in cache with current model hash

**Given** the embedding model is updated
**When** I request embeddings for previously cached text
**Then** the old cached embedding is ignored (model hash mismatch)
**And** a fresh embedding is computed and cached

**Given** I run `resume cache clear`
**When** the command completes
**Then** embeddings with stale model hashes are removed
**And** a count of cleared entries is displayed

**Given** the embedding service generates embeddings (Research-Validated 2026-01-10)
**When** I inspect the cache key format
**Then** it uses: `SHA256(model_hash + "::" + normalized_text)`
**And** normalized_text is lowercased and stripped

**Given** the cache storage format (Research-Validated 2026-01-10)
**When** I inspect stored embeddings
**Then** they use SQLite for indexing
**And** pickle for serialization
**And** gzip for compression (40-60% size reduction)

**Technical Notes:**
- Create `services/embedder.py` with EmbeddingService class
- **Model Hash Computation:**
  ```python
  def compute_model_hash(model):
      hasher = hashlib.sha256()
      for name in sorted(model.state_dict().keys()):
          param = model.state_dict()[name]
          hasher.update(param.cpu().numpy().tobytes())
      return hasher.hexdigest()[:16]
  ```
- **Cache Key Generation:**
  ```python
  cache_key = SHA256(f"{model_hash}::{text.strip().lower()}")
  ```
- **SQLite Schema:**
  ```sql
  CREATE TABLE embeddings (
      cache_key TEXT PRIMARY KEY,
      model_hash TEXT NOT NULL,
      embedding BLOB NOT NULL,  -- gzip(pickle(numpy_array))
      timestamp REAL NOT NULL
  );
  CREATE INDEX idx_model_hash ON embeddings(model_hash);
  ```
- Cache location: `.resume-cache/{model_name}/cache.db`
- **Model Selection:**
  - Primary: `intfloat/multilingual-e5-large-instruct` (1024-dim, 560M params)
  - Fallback: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, 22M params)
- **Instruction Prefixes (CRITICAL):**
  - Passages (JDs): `"passage: {text}"`
  - Queries (Work Units): `"query: {text}"`

---

## Story 4.2: BM25 Ranking Engine

As a **system**,
I want **to rank Work Units by relevance to a job description**,
So that **the most relevant accomplishments are selected for the resume**.

**Acceptance Criteria:**

**Given** a set of Work Units and a parsed job description
**When** the ranker processes them
**Then** each Work Unit receives a relevance score (0.0 to 1.0)
**And** Work Units are returned sorted by score (highest first)

**Given** a Work Unit with exact keyword matches to the JD
**When** ranking occurs
**Then** it scores higher than Work Units with partial or no matches

**Given** a Work Unit's title, problem, actions, and outcome fields
**When** the ranker processes it
**Then** all text fields contribute to the relevance score

**Given** the ranking completes
**When** I inspect the results
**Then** each Work Unit has a `match_reasons` list explaining why it ranked where it did

**Given** a typical job description and 15+ Work Units
**When** ranking runs
**Then** it completes within 3 seconds (NFR1)

**Given** the hybrid ranking system uses RRF fusion (Research-Validated 2026-01-10)
**When** BM25 and semantic results are combined
**Then** RRF formula is applied: `RRF_Score(d) = Σ (1 / (k + rank_i(d)))`
**And** k=60 is used as the default parameter
**And** top_k * 2 results are retrieved from each method before fusion
**And** ties are broken deterministically by document ID

**Given** the embedding model requires instruction prefixes (Research-Validated 2026-01-10)
**When** Work Units are encoded for similarity
**Then** they use the `"query: "` prefix
**And** job descriptions use the `"passage: "` prefix
**And** the e5-large-instruct model is loaded with these prefixes applied

**Technical Notes:**
- Create `services/ranker.py` with hybrid BM25 + semantic ranking
- Use `rank-bm25` library for lexical matching
- Use `sentence-transformers` with `multilingual-e5-large-instruct` model for semantic similarity
- Combine scores using Reciprocal Rank Fusion (RRF) with k=60 per Architecture
- **RRF Implementation (Research-Validated 2026-01-10):**
  - Retrieve `top_k * 2` from each method before fusion
  - Apply RRF: `score = 1/(k + rank_bm25) + 1/(k + rank_semantic)`
  - Sort by RRF score descending, then by doc_id for deterministic tie-breaking
- **Embedding Prefixes (CRITICAL):**
  - Job descriptions: `"passage: {text}"`
  - Work Units: `"query: {text}"`
- Build corpus from Work Unit text fields
- Return scores normalized to 0.0-1.0 range

---

## Story 4.3: Plan Command & Selection Display

As a **user**,
I want **to run `resume plan` and see which Work Units will be included**,
So that **I know exactly what my resume will contain before generating it**.

**Acceptance Criteria:**

**Given** I run `resume plan --jd senior-engineer.txt`
**When** the command executes
**Then** I see a "SELECTED" section with Work Units that will be included
**And** each selected Work Unit shows: ID, title, relevance score, match reasons

**Given** the plan displays selected Work Units
**When** I review the output
**Then** Work Units are ordered by relevance score (highest first)
**And** scores are displayed as percentages (e.g., "87% match")

**Given** I run `resume plan --jd file.txt --top 5`
**When** the command executes
**Then** only the top 5 Work Units are selected

**Given** no `--top` flag is provided
**When** the plan runs
**Then** a sensible default is used (e.g., top 8 or score threshold)

**Given** I run the plan command
**When** output is displayed
**Then** Rich formatting makes selections easy to scan
**And** match reasons are indented under each Work Unit

**Given** I run `resume plan --jd file.txt` (Research-Validated 2026-01-10)
**When** the plan displays content analysis
**Then** I see total word count with optimal range comparison
**And** I see estimated page count
**And** I see average bullets per role (optimal: 4-6)
**And** I see average characters per bullet (optimal: 100-160)

**Given** I run `resume plan --jd file.txt` (Research-Validated 2026-01-10)
**When** the plan displays keyword analysis
**Then** I see keyword density percentage (optimal: 2-3%)
**And** I see keyword coverage percentage (optimal: 60-80%)
**And** I see list of missing high-priority JD keywords
**And** I see keyword placement analysis (which sections contain key terms)

**Given** the plan identifies keyword issues (Research-Validated 2026-01-10)
**When** keyword coverage is below 60%
**Then** missing keywords are highlighted with JD occurrence count
**And** suggestions for Work Unit sections to add keywords are provided

**Technical Notes:**
- Create `commands/plan.py` with Click command
- Wire together JD parser, ranker, and display
- Add `--top N` flag for selection count
- Consider `--threshold 0.5` for score-based cutoff
- **Content Analysis Output (Research-Validated 2026-01-10):**
  ```
  📊 Content Analysis:
     Total Word Count: 742 (optimal: 800-1,200 for 2-page)
     Estimated Pages: 1.8
     Avg Bullets/Role: 5.2 (optimal: 4-6)
     Avg Chars/Bullet: 148 (optimal: 100-160)
  ```
- **Keyword Analysis Output (Research-Validated 2026-01-10):**
  ```
  🔑 Keyword Analysis:
     Density: 2.4% (optimal: 2-3%)
     Coverage: 73% (15/20 JD keywords found)

     Missing High-Priority Keywords:
     - "Kubernetes" (mentioned 3x in JD)
     - "CI/CD" (mentioned 2x in JD)
  ```

---

## Story 4.4: Exclusion Reasoning

As a **user**,
I want **to see which Work Units were excluded and why**,
So that **I trust the system isn't hiding relevant experience**.

**Acceptance Criteria:**

**Given** I run `resume plan --jd file.txt`
**When** the command executes
**Then** I see an "EXCLUDED" section after the selected Work Units
**And** each excluded Work Unit shows: ID, title, and exclusion reason

**Given** a Work Unit is excluded due to low relevance
**When** the exclusion is displayed
**Then** the reason states "Low relevance score (23%)" or similar

**Given** a Work Unit is excluded due to being outside top N
**When** the exclusion is displayed
**Then** the reason states "Below selection threshold" with its score shown

**Given** I run `resume plan --jd file.txt --show-excluded`
**When** the command executes
**Then** the excluded section is shown (it may be hidden by default)

**Given** exclusions are displayed
**When** I review them
**Then** I can identify Work Units that might need terminology updates
**And** I understand why the system made its choices

**Technical Notes:**
- Extend `commands/plan.py` to show exclusions
- Add `--show-excluded` flag (default: show top 5 exclusions)
- Format exclusion reasons clearly
- This builds trust through transparency

---

## Story 4.5: Skill Coverage & Gap Analysis

As a **user considering a job**,
I want **to see which JD requirements I cover and where I have gaps**,
So that **I can honestly assess my fit for the role**.

**Acceptance Criteria:**

**Given** I run `resume plan --jd file.txt`
**When** the command executes
**Then** I see a "COVERAGE" section showing skills/requirements from the JD
**And** each requirement shows: covered (✓), weak (△), or gap (✗)

**Given** a JD requirement is strongly matched by selected Work Units
**When** coverage is displayed
**Then** it shows ✓ with the matching Work Unit IDs

**Given** a JD requirement has partial matches
**When** coverage is displayed
**Then** it shows △ with "Weak signal" and relevant Work Unit IDs

**Given** a JD requirement has no matches in any Work Units
**When** coverage is displayed
**Then** it shows ✗ as a gap
**And** no judgment is implied (just factual reporting)

**Given** I run `resume plan --jd file.txt --json`
**When** the command executes
**Then** coverage data is included in the JSON output
**And** gaps are clearly enumerated

**Technical Notes:**
- Extract requirements from JD during parsing
- Cross-reference with Work Unit skills/tags
- Display as a coverage matrix or list
- This is the "Do I belong in this room?" feature from Journey 2

---

## Story 4.6: Plan Persistence

As a **user**,
I want **to save my plan and reload it later**,
So that **I can review, modify, and use it for resume generation**.

**Acceptance Criteria:**

**Given** I run `resume plan --jd file.txt --output plan.yaml`
**When** the command completes
**Then** the plan is saved to `plan.yaml`
**And** the file contains: JD hash, selected Work Units, scores, timestamp

**Given** a saved plan file exists
**When** I run `resume plan --load plan.yaml`
**Then** the plan is displayed without re-running ranking

**Given** I modify a Work Unit after saving a plan
**When** I re-run `resume plan --jd file.txt`
**Then** new rankings reflect the modifications
**And** the original plan file is unchanged

**Given** I run `resume build --plan plan.yaml`
**When** the build executes
**Then** it uses the selections from the saved plan (Epic 5)

**Given** a plan is saved
**When** I inspect the YAML file
**Then** it is human-readable and could be manually edited if needed

**Technical Notes:**
- Define plan file schema in `models/resume.py`
- Include JD hash for change detection
- Store Work Unit IDs and scores
- Enable `resume build` to consume plan files (Story 5.x)

---

**FR17 (Proposed Rewrites) Note:** This feature requires LLM integration which is marked as "hooks only" for MVP per Architecture. Recommend deferring to post-MVP or implementing as a stub that shows "Rewrite suggestions require LLM configuration."

---
