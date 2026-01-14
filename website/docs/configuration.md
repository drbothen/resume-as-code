---
id: configuration
title: Configuration
sidebar_position: 4
---

# Configuration

Resume as Code uses a layered configuration system with sensible defaults.

## Configuration Files

### Project Configuration (`.resume.yaml`)

Located in your project root, this file contains project-specific settings:

```yaml
# .resume.yaml
schema_version: "1.0.0"

# Profile information
profile:
  name: "Your Name"
  email: "you@example.com"
  phone: "+1-555-123-4567"
  location: "San Francisco, CA"
  linkedin: "linkedin.com/in/yourprofile"
  github: "github.com/yourusername"

# Output settings
output:
  directory: "dist"
  formats:
    - pdf
    - docx
  template: "modern"

# Selection tuning
selection:
  min_relevance_score: 0.3
  max_work_units: 15
  skill_weight: 0.4
```

### User Configuration

Global settings at `~/.config/resume-as-code/config.yaml`:

```yaml
# User-level defaults
default_template: "executive"
default_output_dir: "~/resumes"
```

## Configuration Options

### Profile Section

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Your full name |
| `email` | string | Contact email |
| `phone` | string | Phone number (E.164 format preferred) |
| `location` | string | City, State/Country |
| `linkedin` | string | LinkedIn profile URL |
| `github` | string | GitHub profile URL |
| `website` | string | Personal website URL |

### Output Section

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `directory` | string | `dist` | Output directory |
| `formats` | list | `[pdf, docx]` | Output formats |
| `template` | string | `modern` | Template name |

### Selection Section

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `min_relevance_score` | float | `0.3` | Minimum BM25 score |
| `max_work_units` | int | `15` | Maximum units to include |
| `skill_weight` | float | `0.4` | Weight for skill matching |

## Environment Variables

Override any configuration with environment variables:

```bash
RESUME_OUTPUT_DIR=/custom/path resume build --jd job.txt
RESUME_TEMPLATE=executive resume build --jd job.txt
```

## Template Selection

Available templates:

| Template | Best For |
|----------|----------|
| `modern` | General professional use |
| `executive` | Senior/C-level positions |
| `ats-safe` | Applicant tracking systems |
| `academic` | Research/academic positions |

```bash
# Use a specific template
resume build --jd job.txt --template executive
```

## Validation

Check your configuration:

```bash
# Validate config file
resume config --validate

# Show current configuration
resume config
```
