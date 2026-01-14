---
id: validate
title: validate
sidebar_position: 5
---

# resume validate

Validate your resume data against schemas and quality standards.

## Usage

```bash
# Validate all work units
resume validate

# Validate specific path
resume validate work-units/wu-2024-01-15-deployment.yaml

# With content quality checks
resume validate --content-quality

# With content density checks
resume validate --content-density

# Validate position references
resume validate --check-positions
```

## Options

| Flag | Description |
|------|-------------|
| `--content-quality` | Check for weak verbs, quantification issues |
| `--content-density` | Check bullet point length optimization |
| `--check-positions` | Validate position_id references exist |

## Validation Checks

### Schema Validation

Ensures all YAML files conform to their schemas:

- Required fields present
- Correct data types
- Valid date formats
- Proper ID formats

### Content Quality (--content-quality)

Checks for resume writing best practices:

- **Weak verbs**: Flags "helped", "worked on", "assisted"
- **Quantification**: Suggests adding metrics to vague statements
- **Action verbs**: Recommends stronger action verbs

### Content Density (--content-density)

Checks bullet point optimization:

- Too short (< 50 chars): May lack impact
- Too long (> 200 chars): May not fit resume
- Optimal range: 80-150 characters

### Position References (--check-positions)

Validates that all `position_id` references in work units point to existing positions.

## Output

### Success

```
✓ Validated 12 work units
✓ Validated 3 positions
✓ Validated 2 certifications
✓ All position references valid
```

### With Issues

```
✗ work-units/wu-2024-01-15-test.yaml
  Line 5: Missing required field 'title'
  Line 12: Weak verb detected: "helped"

✗ work-units/wu-2024-02-10-project.yaml
  Line 8: position_id 'pos-invalid' not found in positions.yaml

Found 3 errors in 2 files
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All validations pass |
| 3 | Validation errors found |
