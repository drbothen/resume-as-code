---
id: education
title: Education
sidebar_position: 4
---

# Education Schema

Education entries represent degrees, diplomas, and academic achievements.

## Schema

```yaml
# Required fields
degree: string        # Degree name
institution: string   # School/university name
year: int            # Graduation year

# Optional fields
honors: string       # Honors designation
gpa: string          # GPA (if notable)
major: string        # Major/concentration
minor: string        # Minor
location: string     # Institution location
```

## Example

```yaml
# education.yaml
- degree: BS Computer Science
  institution: Massachusetts Institute of Technology
  year: 2015
  honors: Magna Cum Laude
  gpa: "3.8/4.0"
  major: Computer Science
  minor: Mathematics
  location: Cambridge, MA

- degree: MBA
  institution: Stanford Graduate School of Business
  year: 2020
  honors: Arjay Miller Scholar
```

## Resume Rendering

Education appears with relevant details:

```
EDUCATION

BS Computer Science, Massachusetts Institute of Technology (2015)
Magna Cum Laude | GPA: 3.8/4.0

MBA, Stanford Graduate School of Business (2020)
Arjay Miller Scholar
```

## Best Practices

- **Recent Graduates**: Include GPA if above 3.5
- **Experienced Professionals**: Omit GPA, focus on honors
- **Executive Resumes**: Education often moves to the end
- **Relevant Coursework**: Add to degree description if applicable
