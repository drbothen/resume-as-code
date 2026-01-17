# Troubleshooting

This guide helps diagnose and fix common issues with the matching algorithm.

## Common Issues

### 1. Wrong Work Units Selected

**Symptoms:**
- Irrelevant work units appear in top results
- Highly relevant work units are excluded

**Causes & Solutions:**

| Cause | Diagnosis | Solution |
|-------|-----------|----------|
| Weak work unit content | Title/outcome don't match JD concepts | Improve work unit titles with JD keywords |
| Missing skills/tags | Skills field empty or wrong | Add relevant tags to work units |
| Keyword mismatch | JD uses different terms | Tokenizer expands abbreviations; add synonyms to tags |
| Semantic mismatch | Conceptually different | Use sectioned semantic matching |

**Debugging:**

```bash
# Run with verbose output
resume plan --jd job-description.txt --verbose

# Check match reasons in output
# Look for "Title match:", "Skills match:", "Experience match:"
```

### 2. Old Experience Ranked Too Low

**Symptoms:**
- Relevant older positions don't appear
- Too much emphasis on recent, less relevant work

**Causes & Solutions:**

| Cause | Diagnosis | Solution |
|-------|-----------|----------|
| Recency decay too aggressive | Half-life too short | Increase `recency_half_life` to 7-10 |
| Recency blend too high | Too much weight on recency | Reduce `recency_blend` to 0.10-0.15 |

**Configuration:**

```yaml
scoring_weights:
  recency_half_life: 10.0  # Experience from 10 years ago = 50% weight
  recency_blend: 0.10      # Only 10% of score from recency
```

### 3. Seniority Mismatches

**Symptoms:**
- "Seniority mismatch" in match reasons
- Executive experience ranked low for director role
- Entry-level work ranked low for senior role

**Causes & Solutions:**

| Cause | Diagnosis | Solution |
|-------|-----------|----------|
| Incorrect level inference | Title doesn't indicate level | Add `seniority_level` to work unit |
| Asymmetric penalties | Overqualified/underqualified | Adjust seniority_blend or disable |
| Career changer | Different level in new field | Disable seniority matching |

**Override seniority on work unit:**

```yaml
# work-units/example.yaml
id: wu-2024-01-15-example
title: "Led team of 10 engineers"
seniority_level: lead  # Explicit override
```

**Disable seniority matching:**

```yaml
scoring_weights:
  use_seniority_matching: false
```

### 4. Skills Not Matching

**Symptoms:**
- "Skills match: none" in match reasons
- Known matching skills not detected

**Causes & Solutions:**

| Cause | Diagnosis | Solution |
|-------|-----------|----------|
| Abbreviation mismatch | JD says "K8s", WU says "Kubernetes" | Tokenizer handles this automatically |
| Missing tags | Skills not in tags field | Add skills to work unit tags |
| Case sensitivity | Upper/lower case mismatch | Tokenizer normalizes; check tags |

**Verify tokenization:**

```python
# Python debug
from resume_as_code.utils.tokenizer import get_tokenizer

tokenizer = get_tokenizer(use_lemmatization=False)
print(tokenizer.tokenize("ML and K8s engineer"))
# Output: ['ml', 'machine', 'learning', 'k8s', 'kubernetes', 'engineer']
```

### 5. Certifications/Highlights Not Selected

**Symptoms:**
- Relevant certifications excluded
- Career highlights not appearing

**Causes & Solutions:**

| Cause | Diagnosis | Solution |
|-------|-----------|----------|
| Below relevance threshold | Score < 0.2 | Lower `min_relevance_score` |
| Section limit reached | Too many items | Increase section max limit |
| Priority not set | Should always include | Add `priority: always` to item |

**Lower threshold:**

```yaml
curation:
  min_relevance_score: 0.15  # Include more items
```

**Always include an item:**

```yaml
certifications:
  - name: "AWS Solutions Architect"
    priority: always  # Always included regardless of score
```

### 6. Too Few Results

**Symptoms:**
- Plan shows fewer work units than expected
- Many items excluded

**Causes & Solutions:**

| Cause | Diagnosis | Solution |
|-------|-----------|----------|
| High threshold | min_relevance_score too high | Lower to 0.15 |
| Low default_top_k | Only returning few results | Increase default_top_k |
| Strict curation limits | Section limits too low | Increase limits |

**Configuration:**

```yaml
default_top_k: 12  # Return more results

curation:
  min_relevance_score: 0.15
  bullets_per_position:
    recent_max: 8  # Allow more bullets
```

---

## Debugging Techniques

### Verbose Mode

```bash
resume plan --jd job-description.txt --verbose
```

Shows:
- JD parsing results (title, skills, keywords)
- Work unit scores and rankings
- Match reasons per work unit
- Curation decisions

### Check JD Parsing

Verify the JD parser extracted correct information:

```bash
resume plan --jd job-description.txt --json | jq '.data.jd'
```

> **Note:** `jq` is optional. You can also pipe to `python -m json.tool` for basic formatting, or copy the JSON output to an online viewer.

Look for:
- `title`: Is it correct?
- `skills`: Are key skills listed?
- `keywords`: Are important terms captured?
- `experience_level`: Is seniority correct?

### Score Breakdown

For detailed score analysis, you can check the ranking output:

```bash
resume plan --jd job-description.txt --json | jq '.data.results[] | {id, score, bm25_rank, semantic_rank, match_reasons}'
```

### Embedding Cache Issues

If semantic matching seems off, try clearing the embedding cache:

```bash
rm -rf .resume_cache/embeddings.db
resume plan --jd job-description.txt
```

---

## Logging Configuration

Enable debug logging for detailed algorithm tracing:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or configure specific loggers
logging.getLogger("resume_as_code.services.ranker").setLevel(logging.DEBUG)
logging.getLogger("resume_as_code.services.embedder").setLevel(logging.DEBUG)
```

---

## Performance Issues

### Slow First Run

**Cause:** Embedding model download and loading.

**Solution:** First run downloads the model (~1GB). Subsequent runs use cached model.

### Slow Embedding Generation

**Cause:** Large number of work units or long text.

**Solution:**
- Enable embedding cache: `cache_enabled: true`
- Use smaller embedding model (not recommended)
- Reduce work unit text length

### Memory Issues

**Cause:** Large embedding model in memory.

**Solution:**
- Close other applications
- Use environment variable to limit model size:
  ```bash
  export SENTENCE_TRANSFORMERS_HOME=/tmp/models
  ```

---

## Error Messages

### "Embedding model not found"

**Cause:** Model not downloaded or incorrect path.

**Solution:**
```bash
# Force re-download
rm -rf ~/.cache/huggingface/hub/models--intfloat--multilingual-e5-large-instruct
resume plan --jd job-description.txt
```

### "spaCy model not found"

**Cause:** Lemmatization enabled but spaCy model not installed.

**Solution:**
```bash
# Install spaCy model
uv run python -m spacy download en_core_web_sm

# Or disable lemmatization (default behavior)
# Tokenizer automatically falls back to non-lemmatized mode
```

### "Invalid scoring weights configuration"

**Cause:** Section weights don't sum to 1.0.

**Solution:**
```yaml
scoring_weights:
  use_sectioned_semantic: true
  section_outcome_weight: 0.4   # Must sum to 1.0
  section_actions_weight: 0.3
  section_skills_weight: 0.2
  section_title_weight: 0.1
```

### "Position not found: {id}"

**Cause:** Work unit references non-existent position.

**Solution:**
```bash
# Validate position references
resume validate --check-positions
```

---

## Getting Help

If issues persist after trying these solutions:

1. Check if the issue is reproducible with minimal configuration
2. Gather verbose output and configuration
3. File an issue at the project repository

Include:
- Configuration file (`.resume.yaml`)
- Sample JD (anonymized if needed)
- Sample work unit that's misbehaving
- Verbose output from `resume plan --verbose`
