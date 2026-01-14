---
id: config
title: config
sidebar_position: 8
---

# resume config

Display and manage configuration settings.

## Usage

```bash
# Show current configuration
resume config

# Show specific section
resume config --section profile

# Validate configuration
resume config --validate

# JSON output
resume --json config
```

## Output

```
Resume as Code Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Profile:
├── Name: John Doe
├── Email: john@example.com
├── Phone: +1-555-123-4567
├── Location: San Francisco, CA
├── LinkedIn: linkedin.com/in/johndoe
└── GitHub: github.com/johndoe

Output Settings:
├── Directory: dist
├── Formats: pdf, docx
└── Template: modern

Selection Settings:
├── Min Score: 0.3
├── Max Units: 15
└── Skill Weight: 0.4

Files:
├── Config: .resume.yaml
├── Positions: positions.yaml (3 entries)
├── Work Units: work-units/ (12 files)
├── Certifications: certifications.yaml (2 entries)
└── Education: education.yaml (1 entry)
```

## Options

| Flag | Description |
|------|-------------|
| `--section NAME` | Show specific section |
| `--validate` | Validate configuration files |

## Configuration Sources

Configuration is loaded from (in order of precedence):

1. Environment variables (`RESUME_*`)
2. Project config (`.resume.yaml`)
3. User config (`~/.config/resume-as-code/config.yaml`)
4. Default values

## JSON Output

```json
{
  "format_version": "1.0.0",
  "status": "success",
  "command": "config",
  "data": {
    "profile": {
      "name": "John Doe",
      "email": "john@example.com"
    },
    "output": {
      "directory": "dist",
      "formats": ["pdf", "docx"]
    }
  }
}
```
