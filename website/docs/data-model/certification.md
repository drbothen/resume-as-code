---
id: certification
title: Certification
sidebar_position: 3
---

# Certification Schema

Certifications are professional credentials with optional expiration tracking.

## Schema

```yaml
# Required fields
name: string        # Certification name
issuer: string      # Issuing organization

# Optional fields
date: string        # Date obtained (YYYY-MM)
expires: string     # Expiration date (YYYY-MM)
credential_id: string  # Credential ID number
url: string         # Verification URL
```

## Example

```yaml
# certifications.yaml
- name: AWS Solutions Architect Professional
  issuer: Amazon Web Services
  date: "2024-01"
  expires: "2027-01"
  credential_id: "ABC123XYZ"
  url: "https://aws.amazon.com/verification/..."

- name: Certified Kubernetes Administrator (CKA)
  issuer: The Linux Foundation
  date: "2023-06"
  expires: "2026-06"

- name: CISSP
  issuer: ISC2
  date: "2022-03"
  expires: "2025-03"
```

## Status Tracking

The `resume list certifications` command shows expiration status:

| Status | Meaning |
|--------|---------|
| **Active** | Valid certification |
| **Expires Soon** | Expires within 90 days |
| **Expired** | Past expiration date |

```
Certifications (3 total)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name                              Issuer   Expires     Status
AWS Solutions Architect Pro       AWS      2027-01     Active
CKA                               CNCF     2026-06     Active
CISSP                             ISC2     2025-03     Expires Soon
```

## Resume Rendering

Certifications appear in a dedicated section:

```
CERTIFICATIONS

AWS Solutions Architect Professional (AWS, 2024)
Certified Kubernetes Administrator - CKA (CNCF, 2023)
CISSP (ISC2, 2022)
```

Expired certifications are excluded by default.
