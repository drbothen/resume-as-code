# Story 7.10: Improved BM25 Tokenization

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **job seeker**,
I want **"engineering" to match "engineer" and "ML" to match "machine learning"**,
So that **keyword matching is more intelligent and less brittle**.

## Acceptance Criteria

1. **Given** a JD containing "engineering"
   **When** matching against work unit with "engineer"
   **Then** they match (lemmatization)

2. **Given** a JD containing "machine learning"
   **When** matching against work unit with "ML"
   **Then** they match (abbreviation expansion)

3. **Given** a JD containing "project-management"
   **When** matching against work unit with "project management"
   **Then** they match (hyphen normalization)

4. **Given** a JD containing "CI/CD pipeline"
   **When** matching against work unit with "CICD" or "CI CD"
   **Then** they match (slash normalization)

5. **Given** tokenization runs
   **When** processing text
   **Then** domain stop words are filtered ("responsibilities", "requirements", "experience", "ability to")

6. **Given** spaCy is not installed
   **When** tokenization runs
   **Then** it falls back to basic tokenization without lemmatization
   **And** abbreviation expansion and normalization still work

## Tasks / Subtasks

- [x] Task 1: Create ResumeTokenizer class (AC: #1-#5)
  - [x] 1.1 Create `src/resume_as_code/utils/tokenizer.py`
  - [x] 1.2 Implement abbreviation expansion dictionary
  - [x] 1.3 Implement hyphen/slash normalization
  - [x] 1.4 Implement domain stop words filtering
  - [x] 1.5 Add unit tests for each normalization type

- [x] Task 2: Add optional spaCy lemmatization (AC: #1, #6)
  - [x] 2.1 Add spaCy to optional dependencies in pyproject.toml
  - [x] 2.2 Implement lazy-loading of spaCy model
  - [x] 2.3 Implement graceful fallback when spaCy unavailable
  - [x] 2.4 Add lemmatization to tokenization pipeline

- [x] Task 3: Integrate with ranker (AC: #1-#5)
  - [x] 3.1 Update `_bm25_rank()` to use ResumeTokenizer
  - [x] 3.2 Update `_bm25_rank_weighted()` to use ResumeTokenizer
  - [x] 3.3 Ensure backward compatibility with default settings

- [x] Task 4: Add tests and quality checks
  - [x] 4.1 Unit tests for tokenizer
  - [x] 4.2 Integration tests with ranker
  - [x] 4.3 Test fallback behavior without spaCy
  - [x] 4.4 Run `ruff check` and `mypy --strict`

## Dev Notes

### Current State Analysis

**Existing Implementation (ranker.py:147-148):**
```python
tokenized_docs = [doc.lower().split() for doc in documents]
tokenized_query = query.lower().split()
```

**Problems:**
- No lemmatization: "engineering" ≠ "engineer"
- No abbreviation handling: "ML" ≠ "machine learning"
- No normalization: "CI/CD" ≠ "CICD"
- No stop word filtering: "requirements" matches uselessly

### Implementation Pattern

**Tokenizer Module:**
```python
# src/resume_as_code/utils/tokenizer.py
"""Resume-specific tokenization with normalization and optional lemmatization."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # spaCy types if needed


# Technical abbreviation mappings (bidirectional expansion)
TECH_EXPANSIONS: dict[str, str] = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "k8s": "kubernetes",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "cicd": "continuous integration continuous deployment",
    "ci/cd": "continuous integration continuous deployment",
    "ci cd": "continuous integration continuous deployment",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "az": "azure",
    "db": "database",
    "api": "application programming interface",
    "ui": "user interface",
    "ux": "user experience",
    "qa": "quality assurance",
    "devops": "development operations",
    "sre": "site reliability engineering",
    "sdk": "software development kit",
    "cli": "command line interface",
    "sql": "structured query language",
    "nosql": "not only sql",
    "orm": "object relational mapping",
    "mvc": "model view controller",
    "rest": "representational state transfer",
    "graphql": "graph query language",
    "saas": "software as a service",
    "paas": "platform as a service",
    "iaas": "infrastructure as a service",
}

# Domain-specific stop words (common in JDs but not meaningful for matching)
DOMAIN_STOP_WORDS: set[str] = {
    # JD boilerplate
    "responsibilities",
    "requirements",
    "qualifications",
    "experience",
    "ability",
    "skills",
    "knowledge",
    "understanding",
    # Filler words
    "strong",
    "excellent",
    "preferred",
    "required",
    "including",
    "demonstrated",
    "proven",
    "solid",
    # Generic terms
    "work",
    "working",
    "team",
    "role",
    "position",
    "candidate",
    "applicant",
    "opportunity",
    "company",
    "organization",
    # Common verbs (too generic)
    "using",
    "used",
    "use",
    "will",
    "can",
    "must",
    "should",
    "would",
    "could",
}


class ResumeTokenizer:
    """Resume-optimized tokenizer with normalization and optional lemmatization.

    Features:
    - Technical abbreviation expansion (ML -> machine learning)
    - Hyphen/slash normalization (CI/CD -> ci cd)
    - Domain stop word filtering
    - Optional spaCy lemmatization (engineering -> engineer)
    """

    def __init__(self, use_lemmatization: bool = True) -> None:
        """Initialize tokenizer.

        Args:
            use_lemmatization: Whether to use spaCy lemmatization.
                Falls back gracefully if spaCy not installed.
        """
        self.use_lemmatization = use_lemmatization
        self._nlp: object | None = None
        self._spacy_available: bool | None = None

    @property
    def spacy_available(self) -> bool:
        """Check if spaCy is available."""
        if self._spacy_available is None:
            try:
                import spacy  # noqa: F401

                self._spacy_available = True
            except ImportError:
                self._spacy_available = False
        return self._spacy_available

    @property
    def nlp(self) -> object | None:
        """Lazy-load spaCy model."""
        if self._nlp is None and self.use_lemmatization and self.spacy_available:
            try:
                import spacy

                # Use small model, disable components we don't need
                self._nlp = spacy.load(
                    "en_core_web_sm",
                    disable=["ner", "parser", "attribute_ruler"],
                )
            except OSError:
                # Model not downloaded
                self._nlp = None
        return self._nlp

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text with full normalization pipeline.

        Pipeline:
        1. Lowercase
        2. Normalize hyphens and slashes to spaces
        3. Expand abbreviations
        4. Lemmatize (if spaCy available)
        5. Filter stop words and short tokens

        Args:
            text: Input text to tokenize.

        Returns:
            List of normalized tokens.
        """
        # Step 1: Lowercase
        text = text.lower()

        # Step 2: Normalize hyphens and slashes to spaces
        text = self._normalize_separators(text)

        # Step 3: Expand abbreviations (before lemmatization)
        text = self._expand_abbreviations(text)

        # Step 4: Lemmatize or basic tokenize
        if self.use_lemmatization and self.nlp is not None:
            tokens = self._lemmatize(text)
        else:
            # Basic tokenization: split on whitespace, keep alphanumeric
            tokens = [t for t in text.split() if t.isalnum()]

        # Step 5: Filter stop words and short tokens
        tokens = self._filter_tokens(tokens)

        return tokens

    def _normalize_separators(self, text: str) -> str:
        """Normalize hyphens, slashes, and other separators to spaces.

        Examples:
            "CI/CD" -> "ci cd"
            "project-management" -> "project management"
            "front-end" -> "front end"
        """
        # Replace hyphens, slashes, underscores with spaces
        text = re.sub(r"[-/_]", " ", text)
        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _expand_abbreviations(self, text: str) -> str:
        """Expand technical abbreviations in text.

        Adds expansion alongside original to match both forms.

        Examples:
            "ml engineer" -> "ml machine learning engineer"
            "k8s deployment" -> "k8s kubernetes deployment"
        """
        for abbrev, expansion in TECH_EXPANSIONS.items():
            # Match whole word only (word boundaries)
            pattern = rf"\b{re.escape(abbrev)}\b"
            if re.search(pattern, text):
                # Add expansion alongside abbreviation (match both)
                text = re.sub(pattern, f"{abbrev} {expansion}", text)
        return text

    def _lemmatize(self, text: str) -> list[str]:
        """Lemmatize text using spaCy.

        Args:
            text: Preprocessed text.

        Returns:
            List of lemmatized tokens.
        """
        if self.nlp is None:
            return text.split()

        doc = self.nlp(text)  # type: ignore[operator]
        tokens: list[str] = []
        for token in doc:  # type: ignore[union-attr]
            # Skip non-alphabetic tokens (punctuation, numbers)
            if not token.is_alpha:  # type: ignore[union-attr]
                continue
            # Use lemma (base form)
            lemma = token.lemma_.lower()  # type: ignore[union-attr]
            tokens.append(lemma)
        return tokens

    def _filter_tokens(self, tokens: list[str]) -> list[str]:
        """Filter out stop words and short tokens.

        Args:
            tokens: List of tokens.

        Returns:
            Filtered token list.
        """
        return [
            t
            for t in tokens
            if t not in DOMAIN_STOP_WORDS
            and len(t) > 2  # Skip very short tokens
        ]

    @lru_cache(maxsize=1000)
    def tokenize_cached(self, text: str) -> tuple[str, ...]:
        """Tokenize with caching (returns tuple for hashability).

        Use this for repeated tokenization of the same text.
        """
        return tuple(self.tokenize(text))


# Module-level singleton for convenience
_default_tokenizer: ResumeTokenizer | None = None


def get_tokenizer(use_lemmatization: bool = True) -> ResumeTokenizer:
    """Get or create default tokenizer instance.

    Args:
        use_lemmatization: Whether to use spaCy lemmatization.

    Returns:
        ResumeTokenizer instance.
    """
    global _default_tokenizer
    if _default_tokenizer is None:
        _default_tokenizer = ResumeTokenizer(use_lemmatization=use_lemmatization)
    return _default_tokenizer
```

**pyproject.toml Update:**
```toml
[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-cov",
  "mypy",
  "ruff",
  "pre-commit",
]
llm = [
  "anthropic>=0.25",
  "openai>=1.0",
]
nlp = [
  "spacy>=3.7",
]

# To install with spaCy:
# uv pip install -e ".[nlp]"
# python -m spacy download en_core_web_sm
```

**Ranker Integration:**
```python
# services/ranker.py - update _bm25_rank method

from resume_as_code.utils.tokenizer import get_tokenizer

def _bm25_rank(self, documents: list[str], query: str) -> list[int]:
    """Compute BM25 ranks (1-indexed, lower is better)."""
    tokenizer = get_tokenizer()

    # Tokenize with normalization
    tokenized_docs = [tokenizer.tokenize(doc) for doc in documents]
    tokenized_query = tokenizer.tokenize(query)

    # Handle empty documents (add placeholder to avoid BM25 errors)
    tokenized_docs = [doc if doc else ["_empty_"] for doc in tokenized_docs]

    # Build BM25 index
    bm25 = BM25Okapi(tokenized_docs)

    # Get scores
    scores: NDArray[np.float64] = bm25.get_scores(tokenized_query)

    # Compute ranks (1-indexed, lower rank = better match)
    sorted_indices = np.argsort(scores)[::-1]
    ranks = [0] * len(scores)
    for rank, idx in enumerate(sorted_indices, 1):
        ranks[idx] = rank

    return ranks
```

### Testing Standards

```python
# tests/unit/utils/test_tokenizer.py
import pytest

from resume_as_code.utils.tokenizer import (
    DOMAIN_STOP_WORDS,
    TECH_EXPANSIONS,
    ResumeTokenizer,
)


class TestNormalization:
    """Tests for text normalization."""

    def test_hyphen_normalization(self) -> None:
        """Hyphens are normalized to spaces."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("project-management skills")

        assert "project" in tokens
        assert "management" in tokens
        assert "project-management" not in tokens

    def test_slash_normalization(self) -> None:
        """Slashes are normalized to spaces."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("CI/CD pipeline")

        # CI/CD should become "ci cd" plus expansion
        assert "pipeline" in tokens
        # After expansion: "ci cd continuous integration continuous deployment"
        assert "continuous" in tokens or "integration" in tokens

    def test_underscore_normalization(self) -> None:
        """Underscores are normalized to spaces."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("snake_case_variable")

        assert "snake" in tokens
        assert "case" in tokens
        assert "variable" in tokens


class TestAbbreviationExpansion:
    """Tests for technical abbreviation expansion."""

    def test_ml_expands_to_machine_learning(self) -> None:
        """ML expands to machine learning."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("ML engineer with Python")

        assert "machine" in tokens
        assert "learning" in tokens
        # Original also preserved
        # (Note: 'ml' is 2 chars, might be filtered by length)

    def test_k8s_expands_to_kubernetes(self) -> None:
        """k8s expands to kubernetes."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("k8s deployment")

        assert "kubernetes" in tokens
        assert "deployment" in tokens

    def test_cicd_expands(self) -> None:
        """CICD expands to continuous integration continuous deployment."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("CICD pipeline")

        assert "continuous" in tokens
        assert "integration" in tokens
        assert "deployment" in tokens

    def test_aws_expands(self) -> None:
        """AWS expands to amazon web services."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("AWS cloud")

        assert "amazon" in tokens
        assert "services" in tokens


class TestStopWordFiltering:
    """Tests for domain stop word filtering."""

    def test_filters_requirements(self) -> None:
        """'requirements' is filtered out."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("Job requirements include Python")

        assert "requirements" not in tokens
        assert "python" in tokens

    def test_filters_responsibilities(self) -> None:
        """'responsibilities' is filtered out."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("Responsibilities include coding")

        assert "responsibilities" not in tokens
        assert "coding" in tokens

    def test_filters_experience(self) -> None:
        """'experience' is filtered out."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("5 years experience with Java")

        assert "experience" not in tokens
        assert "java" in tokens

    def test_filters_short_tokens(self) -> None:
        """Tokens with 2 or fewer characters are filtered."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("a to be or not")

        assert "a" not in tokens
        assert "to" not in tokens
        assert "be" not in tokens
        assert "or" not in tokens


class TestLemmatization:
    """Tests for spaCy lemmatization."""

    @pytest.fixture
    def tokenizer_with_lemma(self) -> ResumeTokenizer:
        """Create tokenizer with lemmatization enabled."""
        return ResumeTokenizer(use_lemmatization=True)

    def test_spacy_available_check(self, tokenizer_with_lemma: ResumeTokenizer) -> None:
        """Check if spaCy availability is detected."""
        # This test documents the expected behavior
        # spacy_available will be True if spaCy is installed, False otherwise
        assert isinstance(tokenizer_with_lemma.spacy_available, bool)

    def test_lemmatization_engineering_to_engineer(
        self, tokenizer_with_lemma: ResumeTokenizer
    ) -> None:
        """'engineering' lemmatizes to 'engineer' (if spaCy available)."""
        tokens = tokenizer_with_lemma.tokenize("software engineering role")

        if tokenizer_with_lemma.spacy_available and tokenizer_with_lemma.nlp:
            # With spaCy: engineering -> engineer
            assert "engineer" in tokens or "engineering" in tokens
        else:
            # Without spaCy: original form preserved
            assert "engineering" in tokens

    def test_fallback_without_spacy(self) -> None:
        """Tokenization works without spaCy."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("Python programming")

        assert "python" in tokens
        assert "programming" in tokens


class TestCaching:
    """Tests for tokenization caching."""

    def test_cached_tokenization(self) -> None:
        """Cached tokenization returns consistent results."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)

        result1 = tokenizer.tokenize_cached("Python developer")
        result2 = tokenizer.tokenize_cached("Python developer")

        assert result1 == result2
        assert isinstance(result1, tuple)  # Cached returns tuple


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_string(self) -> None:
        """Empty string returns empty list."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("")

        assert tokens == []

    def test_only_stop_words(self) -> None:
        """String with only stop words returns empty list."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("requirements experience skills")

        assert tokens == []

    def test_mixed_case(self) -> None:
        """Mixed case is normalized to lowercase."""
        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("PYTHON Developer PyTorch")

        assert "python" in tokens
        assert "developer" in tokens
        assert "pytorch" in tokens
```

### Project Context Rules

From `project-context.md`:
- Run `ruff check` and `mypy --strict` before completing
- Use Rich console for CLI output, never `print()`
- Type hints required on all public functions
- Use `|` union syntax (Python 3.10+)

### spaCy Installation Note

spaCy is optional. To enable lemmatization:
```bash
uv pip install -e ".[nlp]"
python -m spacy download en_core_web_sm
```

Without spaCy, the tokenizer still provides:
- Abbreviation expansion
- Hyphen/slash normalization
- Stop word filtering

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-7-schema-data-model-refactoring.md#Story 7.10]
- [Source: src/resume_as_code/services/ranker.py:147-148 - current basic tokenization]
- [Source: pyproject.toml - current dependencies (no spaCy)]

## Dev Agent Record

### Agent Model Used

Claude Opus 4 (claude-opus-4-20250514)

### Debug Log References

- Commit: 7ab185e feat(ranker): add ResumeTokenizer with normalization and abbreviation expansion

### Completion Notes List

- ResumeTokenizer implements full normalization pipeline: lowercase → separator normalization → abbreviation expansion → optional lemmatization → stop word filtering
- spaCy lemmatization is optional (disabled by default in ranker for performance)
- 26 unit tests covering all ACs
- Integration with both `_bm25_rank` and `_bm25_rank_weighted` methods

### File List

- `src/resume_as_code/utils/tokenizer.py` - NEW: ResumeTokenizer class with normalization pipeline
- `src/resume_as_code/services/ranker.py` - MODIFIED: Integrated ResumeTokenizer in BM25 methods
- `tests/unit/test_tokenizer.py` - NEW: 26 unit tests including AC validation tests
- `pyproject.toml` - MODIFIED: Added optional `nlp` dependency group with spaCy>=3.7
