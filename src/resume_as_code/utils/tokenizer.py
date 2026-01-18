"""Resume-specific tokenization with normalization and optional lemmatization."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # spaCy types if needed


# Technical abbreviation mappings (bidirectional expansion)
TECH_EXPANSIONS: dict[str, str] = {
    # AI/ML
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "llm": "large language model",
    "genai": "generative artificial intelligence",
    # Infrastructure
    "k8s": "kubernetes",
    "infra": "infrastructure",
    "vpc": "virtual private cloud",
    "cdn": "content delivery network",
    "dns": "domain name system",
    # Languages/Frameworks
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "rb": "ruby",
    "fe": "frontend",
    "be": "backend",
    # CI/CD variants
    "cicd": "continuous integration continuous deployment",
    "ci/cd": "continuous integration continuous deployment",
    "ci cd": "continuous integration continuous deployment",
    # Cloud providers
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "az": "azure",
    # Databases
    "db": "database",
    "sql": "structured query language",
    "nosql": "not only sql",
    "orm": "object relational mapping",
    "rds": "relational database service",
    # APIs/Architecture
    "api": "application programming interface",
    "rest": "representational state transfer",
    "graphql": "graph query language",
    "grpc": "google remote procedure call",
    "mvc": "model view controller",
    "soa": "service oriented architecture",
    # UX/UI
    "ui": "user interface",
    "ux": "user experience",
    # DevOps/SRE
    "devops": "development operations",
    "sre": "site reliability engineering",
    "qa": "quality assurance",
    "tdd": "test driven development",
    "bdd": "behavior driven development",
    # Tools/SDKs
    "sdk": "software development kit",
    "cli": "command line interface",
    "ide": "integrated development environment",
    # Cloud services
    "saas": "software as a service",
    "paas": "platform as a service",
    "iaas": "infrastructure as a service",
    # Security
    "sso": "single sign on",
    "mfa": "multi factor authentication",
    "rbac": "role based access control",
    "iam": "identity access management",
    # Agile/Management
    "agile": "agile methodology",
    "scrum": "scrum framework",
    "kanban": "kanban methodology",
    "okr": "objectives key results",
    "kpi": "key performance indicator",
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
    # Common filler
    "include",
    "job",
    "key",
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
                import spacy  # type: ignore[import-not-found,unused-ignore]

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
        for token in doc:
            # Skip non-alphabetic tokens (punctuation, numbers)
            if not token.is_alpha:
                continue
            # Use lemma (base form)
            lemma = token.lemma_.lower()
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
            if t not in DOMAIN_STOP_WORDS and len(t) > 2  # Skip very short tokens
        ]

    def tokenize_cached(self, text: str) -> tuple[str, ...]:
        """Tokenize with caching (returns tuple for hashability).

        Use this for repeated tokenization of the same text.
        Uses module-level cache to avoid memory leaks from method caching.
        """
        return _tokenize_cached(self, text)


# Module-level cache function (avoids memory leak from lru_cache on methods)
# Cache key is (text, use_lemmatization) since those determine output
@lru_cache(maxsize=1000)
def _tokenize_cached_impl(text: str, use_lemmatization: bool) -> tuple[str, ...]:
    """Cache tokenization results at module level."""
    tokenizer = ResumeTokenizer(use_lemmatization=use_lemmatization)
    return tuple(tokenizer.tokenize(text))


def _tokenize_cached(tokenizer: ResumeTokenizer, text: str) -> tuple[str, ...]:
    """Wrapper that extracts cache key from tokenizer instance."""
    return _tokenize_cached_impl(text, tokenizer.use_lemmatization)


# Module-level cache for tokenizer instances (keyed by config)
_tokenizer_cache: dict[bool, ResumeTokenizer] = {}


def get_tokenizer(use_lemmatization: bool = True) -> ResumeTokenizer:
    """Get or create tokenizer instance for the given configuration.

    Uses a cache to reuse tokenizer instances with the same configuration,
    avoiding repeated spaCy model loading while respecting different configs.

    Args:
        use_lemmatization: Whether to use spaCy lemmatization.

    Returns:
        ResumeTokenizer instance configured as requested.
    """
    if use_lemmatization not in _tokenizer_cache:
        _tokenizer_cache[use_lemmatization] = ResumeTokenizer(use_lemmatization=use_lemmatization)
    return _tokenizer_cache[use_lemmatization]
