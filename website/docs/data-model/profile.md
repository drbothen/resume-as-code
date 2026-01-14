---
id: profile
title: Profile
sidebar_position: 5
---

# Profile Schema

The profile contains your personal and contact information, stored in `.resume.yaml`.

## Schema

```yaml
profile:
  # Required
  name: string        # Full name

  # Optional
  email: string       # Email address
  phone: string       # Phone number
  location: string    # City, State/Country
  linkedin: string    # LinkedIn URL
  github: string      # GitHub URL
  website: string     # Personal website
  summary: string     # Professional summary
```

## Example

```yaml
# .resume.yaml
profile:
  name: "Jane Smith"
  email: "jane@example.com"
  phone: "+1-555-123-4567"
  location: "San Francisco, CA"
  linkedin: "linkedin.com/in/janesmith"
  github: "github.com/janesmith"
  website: "janesmith.dev"
  summary: >
    Senior software engineer with 8+ years experience
    building scalable distributed systems. Passionate
    about developer experience and infrastructure automation.
```

## Resume Header

Profile data renders as the resume header:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                         JANE SMITH
              Senior Software Engineer

  jane@example.com | +1-555-123-4567 | San Francisco, CA
  linkedin.com/in/janesmith | github.com/janesmith
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Summary

The `summary` field is optional and template-dependent:

- **Modern template**: Shows summary below header
- **Executive template**: Shows summary prominently
- **ATS-safe template**: Includes in plain text

Keep summaries to 2-3 sentences highlighting key differentiators.
