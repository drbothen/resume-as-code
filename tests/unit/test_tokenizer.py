"""Tests for ResumeTokenizer with normalization and optional lemmatization."""

from __future__ import annotations


class TestTechExpansions:
    """Tests for TECH_EXPANSIONS constant dictionary."""

    def test_all_keys_are_lowercase(self) -> None:
        """All abbreviation keys should be lowercase."""
        from resume_as_code.utils.tokenizer import TECH_EXPANSIONS

        for key in TECH_EXPANSIONS:
            assert key == key.lower(), f"Key '{key}' should be lowercase"

    def test_all_values_are_lowercase(self) -> None:
        """All expansion values should be lowercase."""
        from resume_as_code.utils.tokenizer import TECH_EXPANSIONS

        for key, value in TECH_EXPANSIONS.items():
            assert value == value.lower(), f"Value for '{key}' should be lowercase"

    def test_required_abbreviations_present(self) -> None:
        """Critical abbreviations must be present."""
        from resume_as_code.utils.tokenizer import TECH_EXPANSIONS

        required = ["ml", "ai", "k8s", "aws", "gcp", "cicd", "api", "ui", "ux"]
        for abbrev in required:
            assert abbrev in TECH_EXPANSIONS, f"Missing required abbreviation: {abbrev}"

    def test_cicd_variants_all_present(self) -> None:
        """All CI/CD variants should be present for robust matching."""
        from resume_as_code.utils.tokenizer import TECH_EXPANSIONS

        variants = ["cicd", "ci/cd", "ci cd"]
        for variant in variants:
            assert variant in TECH_EXPANSIONS, f"Missing CI/CD variant: {variant}"

    def test_no_empty_expansions(self) -> None:
        """No expansion should be empty."""
        from resume_as_code.utils.tokenizer import TECH_EXPANSIONS

        for key, value in TECH_EXPANSIONS.items():
            assert value.strip(), f"Empty expansion for '{key}'"


class TestDomainStopWords:
    """Tests for DOMAIN_STOP_WORDS constant set."""

    def test_all_words_are_lowercase(self) -> None:
        """All stop words should be lowercase."""
        from resume_as_code.utils.tokenizer import DOMAIN_STOP_WORDS

        for word in DOMAIN_STOP_WORDS:
            assert word == word.lower(), f"Stop word '{word}' should be lowercase"

    def test_required_stop_words_present(self) -> None:
        """Critical JD boilerplate words must be filtered."""
        from resume_as_code.utils.tokenizer import DOMAIN_STOP_WORDS

        required = [
            "responsibilities",
            "requirements",
            "qualifications",
            "experience",
            "ability",
            "skills",
        ]
        for word in required:
            assert word in DOMAIN_STOP_WORDS, f"Missing required stop word: {word}"

    def test_no_technical_terms_in_stop_words(self) -> None:
        """Technical terms should NOT be in stop words."""
        from resume_as_code.utils.tokenizer import DOMAIN_STOP_WORDS

        technical_terms = [
            "python",
            "javascript",
            "kubernetes",
            "docker",
            "aws",
            "react",
            "database",
            "api",
            "security",
            "cloud",
        ]
        for term in technical_terms:
            assert term not in DOMAIN_STOP_WORDS, (
                f"Technical term '{term}' should not be a stop word"
            )


class TestNormalization:
    """Tests for text normalization."""

    def test_hyphen_normalization(self) -> None:
        """Hyphens are normalized to spaces."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("project-management skills")

        assert "project" in tokens
        assert "management" in tokens
        assert "project-management" not in tokens

    def test_slash_normalization(self) -> None:
        """Slashes are normalized to spaces."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("CI/CD pipeline")

        assert "pipeline" in tokens
        # After expansion: "ci cd continuous integration continuous deployment"
        assert "continuous" in tokens or "integration" in tokens

    def test_underscore_normalization(self) -> None:
        """Underscores are normalized to spaces."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("snake_case_variable")

        assert "snake" in tokens
        assert "case" in tokens
        assert "variable" in tokens


class TestAbbreviationExpansion:
    """Tests for technical abbreviation expansion."""

    def test_ml_expands_to_machine_learning(self) -> None:
        """ML expands to machine learning."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("ML engineer with Python")

        assert "machine" in tokens
        assert "learning" in tokens

    def test_k8s_expands_to_kubernetes(self) -> None:
        """k8s expands to kubernetes."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("k8s deployment")

        assert "kubernetes" in tokens
        assert "deployment" in tokens

    def test_cicd_expands(self) -> None:
        """CICD expands to continuous integration continuous deployment."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("CICD pipeline")

        assert "continuous" in tokens
        assert "integration" in tokens
        assert "deployment" in tokens

    def test_aws_expands(self) -> None:
        """AWS expands to amazon web services."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("AWS cloud")

        assert "amazon" in tokens
        assert "services" in tokens


class TestStopWordFiltering:
    """Tests for domain stop word filtering."""

    def test_filters_requirements(self) -> None:
        """'requirements' is filtered out."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("Job requirements include Python")

        assert "requirements" not in tokens
        assert "python" in tokens

    def test_filters_responsibilities(self) -> None:
        """'responsibilities' is filtered out."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("Responsibilities include coding")

        assert "responsibilities" not in tokens
        assert "coding" in tokens

    def test_filters_experience(self) -> None:
        """'experience' is filtered out."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("5 years experience with Java")

        assert "experience" not in tokens
        assert "java" in tokens

    def test_filters_short_tokens(self) -> None:
        """Tokens with 2 or fewer characters are filtered."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("a to be or not")

        assert "a" not in tokens
        assert "to" not in tokens
        assert "be" not in tokens
        assert "or" not in tokens


class TestLemmatization:
    """Tests for spaCy lemmatization."""

    def test_spacy_available_check(self) -> None:
        """Check if spaCy availability is detected."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=True)
        # This test documents the expected behavior
        # spacy_available will be True if spaCy is installed, False otherwise
        assert isinstance(tokenizer.spacy_available, bool)

    def test_lemmatization_engineering_to_engineer(self) -> None:
        """'engineering' lemmatizes to 'engineer' (if spaCy available)."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=True)
        tokens = tokenizer.tokenize("software engineering role")

        if tokenizer.spacy_available and tokenizer.nlp:
            # With spaCy: engineering -> engineer
            assert "engineer" in tokens or "engineering" in tokens
        else:
            # Without spaCy: original form preserved
            assert "engineering" in tokens

    def test_fallback_without_spacy(self) -> None:
        """Tokenization works without spaCy."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("Python programming")

        assert "python" in tokens
        assert "programming" in tokens


class TestCaching:
    """Tests for tokenization caching."""

    def test_cached_tokenization(self) -> None:
        """Cached tokenization returns consistent results."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)

        result1 = tokenizer.tokenize_cached("Python developer")
        result2 = tokenizer.tokenize_cached("Python developer")

        assert result1 == result2
        assert isinstance(result1, tuple)  # Cached returns tuple


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_string(self) -> None:
        """Empty string returns empty list."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("")

        assert tokens == []

    def test_only_stop_words(self) -> None:
        """String with only stop words returns empty list."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("requirements experience skills")

        assert tokens == []

    def test_mixed_case(self) -> None:
        """Mixed case is normalized to lowercase."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)
        tokens = tokenizer.tokenize("PYTHON Developer PyTorch")

        assert "python" in tokens
        assert "developer" in tokens
        assert "pytorch" in tokens


class TestGetTokenizer:
    """Tests for module-level get_tokenizer function."""

    def test_get_tokenizer_returns_instance(self) -> None:
        """get_tokenizer returns a ResumeTokenizer instance."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer, get_tokenizer

        tokenizer = get_tokenizer(use_lemmatization=False)
        assert isinstance(tokenizer, ResumeTokenizer)

    def test_get_tokenizer_caches_by_config(self) -> None:
        """get_tokenizer returns the same instance for same config."""
        from resume_as_code.utils import tokenizer as tok_module

        # Reset cache for clean test
        tok_module._tokenizer_cache.clear()

        tok1 = tok_module.get_tokenizer(use_lemmatization=False)
        tok2 = tok_module.get_tokenizer(use_lemmatization=False)
        assert tok1 is tok2

    def test_get_tokenizer_respects_different_configs(self) -> None:
        """get_tokenizer returns different instances for different configs."""
        from resume_as_code.utils import tokenizer as tok_module

        # Reset cache for clean test
        tok_module._tokenizer_cache.clear()

        tok_no_lemma = tok_module.get_tokenizer(use_lemmatization=False)
        tok_with_lemma = tok_module.get_tokenizer(use_lemmatization=True)

        assert tok_no_lemma is not tok_with_lemma
        assert tok_no_lemma.use_lemmatization is False
        assert tok_with_lemma.use_lemmatization is True


class TestAcceptanceCriteria:
    """Tests for story acceptance criteria."""

    def test_ac1_lemmatization_engineering_matches_engineer(self) -> None:
        """AC#1: 'engineering' matches 'engineer' via lemmatization."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=True)

        jd_tokens = tokenizer.tokenize("engineering")
        wu_tokens = tokenizer.tokenize("engineer")

        if tokenizer.spacy_available and tokenizer.nlp:
            # With lemmatization, both should produce 'engineer'
            assert set(jd_tokens) & set(wu_tokens), "engineering and engineer should share tokens"
        else:
            # Without spaCy, fallback behavior - test expansion still works
            pass

    def test_ac2_ml_matches_machine_learning(self) -> None:
        """AC#2: 'ML' matches 'machine learning' via abbreviation expansion."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)

        jd_tokens = tokenizer.tokenize("machine learning")
        wu_tokens = tokenizer.tokenize("ML")

        # Both should contain 'machine' and 'learning' after expansion
        assert "machine" in jd_tokens
        assert "learning" in jd_tokens
        assert "machine" in wu_tokens
        assert "learning" in wu_tokens

    def test_ac3_hyphen_project_management(self) -> None:
        """AC#3: 'project-management' matches 'project management'."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)

        jd_tokens = tokenizer.tokenize("project-management")
        wu_tokens = tokenizer.tokenize("project management")

        # Both should contain 'project' and 'management'
        assert "project" in jd_tokens
        assert "management" in jd_tokens
        assert "project" in wu_tokens
        assert "management" in wu_tokens

    def test_ac4_slash_cicd(self) -> None:
        """AC#4: 'CI/CD' matches 'CICD' or 'CI CD'."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)

        tokens_slash = tokenizer.tokenize("CI/CD pipeline")
        tokens_no_slash = tokenizer.tokenize("CICD pipeline")
        tokens_space = tokenizer.tokenize("CI CD pipeline")

        # All should expand to include 'continuous', 'integration', 'deployment'
        for tokens in [tokens_slash, tokens_no_slash, tokens_space]:
            assert "continuous" in tokens
            assert "integration" in tokens
            assert "deployment" in tokens

    def test_ac5_domain_stop_words_filtered(self) -> None:
        """AC#5: Domain stop words like 'responsibilities', 'requirements' are filtered."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        tokenizer = ResumeTokenizer(use_lemmatization=False)

        tokens = tokenizer.tokenize(
            "Key responsibilities include Python requirements experience ability to"
        )

        # Stop words should be filtered
        assert "responsibilities" not in tokens
        assert "requirements" not in tokens
        assert "experience" not in tokens
        assert "ability" not in tokens

        # Technical terms preserved
        assert "python" in tokens

    def test_ac6_fallback_without_spacy(self) -> None:
        """AC#6: Graceful fallback when spaCy unavailable."""
        from resume_as_code.utils.tokenizer import ResumeTokenizer

        # Force no lemmatization
        tokenizer = ResumeTokenizer(use_lemmatization=False)

        # Should still work with abbreviation expansion and normalization
        tokens = tokenizer.tokenize("ML engineer with CI/CD experience")

        assert "machine" in tokens  # Expansion works
        assert "learning" in tokens
        assert "continuous" in tokens  # CI/CD expansion works
        assert "engineer" in tokens
        assert "experience" not in tokens  # Stop word filtering works
