import type {ReactNode} from 'react';
import {useState} from 'react';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import CodeBlock from '@theme/CodeBlock';
import styles from './examples.module.css';

type Example = {
  title: string;
  description: string;
  scenario: string;
  code: string;
  output: string;
};

const examples: Example[] = [
  {
    title: 'Quick Capture: New Accomplishment',
    description: 'Capture an accomplishment right after it happens with minimal friction.',
    scenario: 'You just finished a project that reduced costs by 40%. Capture it before you forget the details.',
    code: `# Create a position if it doesn't exist
resume new position "TechCorp|Senior Engineer|2022-01|"

# Quick capture with inline position
resume new work-unit \\
  --position-id pos-techcorp-senior-engineer \\
  --title "Reduced cloud costs by 40% through infrastructure optimization"

# Or capture with full details using archetype
resume new work-unit --archetype optimization`,
    output: `✓ Created work unit: wu-2024-01-15-reduced-cloud-costs

Work Unit Details:
  ID: wu-2024-01-15-reduced-cloud-costs
  Title: Reduced cloud costs by 40% through infrastructure optimization
  Position: TechCorp - Senior Engineer

  Next steps:
  - Edit work-units/wu-2024-01-15-reduced-cloud-costs.yaml to add PAR details
  - Run \`resume validate\` to check completeness`,
  },
  {
    title: 'Generate Resume for Job Application',
    description: 'The full workflow from job description to generated resume.',
    scenario: 'You found a job posting for a Senior DevOps Engineer and want to create a tailored resume.',
    code: `# Save the job description to a file
cat > job-description.txt << 'EOF'
Senior DevOps Engineer

Requirements:
- 5+ years of experience with CI/CD pipelines
- Strong Kubernetes and container orchestration skills
- AWS or GCP cloud infrastructure experience
- Experience with Infrastructure as Code (Terraform)
- Security-minded approach to infrastructure
EOF

# Validate your work units first
resume validate --check-positions

# Plan: analyze JD and select best Work Units
resume plan --jd job-description.txt

# Build the resume
resume build --jd job-description.txt --template modern`,
    output: `Resume Plan for: Senior DevOps Engineer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Selected Work Units (6):
┌────────────────────────────────────────────────┐
│ Score  Title                                   │
├────────────────────────────────────────────────┤
│ 0.89   Led Kubernetes migration                │
│ 0.85   Reduced deployment time by 80%          │
│ 0.78   Implemented observability platform      │
│ 0.72   Built CI/CD pipeline                    │
│ 0.68   Automated infrastructure provisioning   │
│ 0.52   Led SOC2 compliance initiative          │
└────────────────────────────────────────────────┘

Skill Coverage:
✓ CI/CD (3 work units)
✓ Kubernetes (2 work units)
✓ AWS (2 work units)
✗ Terraform (0 work units) ← Gap

Building resume...
✓ Generated: dist/resume-senior-devops.pdf (142 KB)
✓ Generated: dist/resume-senior-devops.docx (48 KB)
✓ Manifest: dist/manifest.json`,
  },
  {
    title: 'Incident Response Work Unit',
    description: 'Document a crisis response accomplishment using the incident archetype.',
    scenario: 'You led the response to a critical production outage and want to capture it properly.',
    code: `# Use the incident archetype for crisis response
resume new work-unit --archetype incident

# This opens an editor with a template:
# - Incident context (what went wrong)
# - Your response actions (what you did)
# - Resolution and prevention (what changed)

# The resulting YAML looks like:
cat work-units/wu-2024-01-20-production-outage.yaml`,
    output: `id: wu-2024-01-20-production-outage
position_id: pos-techcorp-senior-engineer
title: "Resolved critical payment system outage in 23 minutes"

par:
  problem: >
    Payment processing system experienced complete failure
    during peak Black Friday traffic, blocking $2M/hour in
    transactions and generating 50+ customer escalations.
  actions:
    - Led incident response as primary on-call engineer
    - Identified root cause: database connection pool exhaustion
    - Implemented emergency connection limit increase
    - Coordinated with payments team for transaction replay
    - Drafted and communicated customer status updates
  result: >
    Restored service in 23 minutes (SLA: 1 hour). Zero
    transaction data loss through replay mechanism.
    Implemented connection pool monitoring to prevent recurrence.

skills_demonstrated:
  - Incident Response
  - Database Administration
  - Crisis Communication
  - Leadership

tags:
  - incident
  - production
  - payments`,
  },
  {
    title: 'Bulk Import from LinkedIn',
    description: 'Import positions from exported LinkedIn data.',
    scenario: 'You want to initialize your resume project with your existing job history.',
    code: `# Create positions from LinkedIn export
# Pipe-separated format: Employer|Title|Start|End

resume new position "Google|Senior Software Engineer|2020-06|2023-12"
resume new position "Meta|Software Engineer|2017-08|2020-05"
resume new position "Startup Inc|Junior Developer|2015-06|2017-07"

# Verify imports
resume list positions

# Add executive scope for senior roles
resume show position pos-google-senior-software-engineer`,
    output: `Positions (3 total)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ID                                    Employer      Title                    Period
pos-google-senior-software-engineer  Google        Senior Software Engineer  2020-06 - 2023-12
pos-meta-software-engineer           Meta          Software Engineer         2017-08 - 2020-05
pos-startup-junior-developer         Startup Inc   Junior Developer          2015-06 - 2017-07`,
  },
  {
    title: 'JSON Output for Scripting',
    description: 'Use JSON output mode for programmatic access to resume data.',
    scenario: 'You want to integrate Resume as Code with other tools or scripts.',
    code: `# Get positions as JSON
resume --json list positions | jq '.data[] | {id, employer, title}'

# Get specific work unit
resume --json show work-unit wu-2024-01-15-cicd-pipeline

# Plan with JSON output for CI/CD integration
resume --json plan --jd job.txt | jq '.data.selected_work_units'

# Check validation status
resume --json validate | jq '.status'`,
    output: `# positions output:
[
  {
    "id": "pos-google-senior-software-engineer",
    "employer": "Google",
    "title": "Senior Software Engineer"
  },
  {
    "id": "pos-meta-software-engineer",
    "employer": "Meta",
    "title": "Software Engineer"
  }
]

# validation output:
{
  "status": "success",
  "data": {
    "work_units_validated": 12,
    "positions_validated": 3,
    "errors": []
  }
}`,
  },
];

function ExampleCard({example, isOpen, onToggle}: {
  example: Example;
  isOpen: boolean;
  onToggle: () => void;
}): ReactNode {
  return (
    <div className={`${styles.exampleCard} ${isOpen ? styles.open : ''}`}>
      <button className={styles.exampleHeader} onClick={onToggle}>
        <div className={styles.exampleTitle}>
          <Heading as="h3">{example.title}</Heading>
          <p>{example.description}</p>
        </div>
        <span className={styles.expandIcon}>{isOpen ? '−' : '+'}</span>
      </button>
      {isOpen && (
        <div className={styles.exampleContent}>
          <div className={styles.scenario}>
            <strong>Scenario:</strong> {example.scenario}
          </div>
          <div className={styles.codeSection}>
            <div className={styles.codeLabel}>Commands</div>
            <CodeBlock language="bash">{example.code}</CodeBlock>
          </div>
          <div className={styles.outputSection}>
            <div className={styles.outputLabel}>Expected Output</div>
            <CodeBlock language="text">{example.output}</CodeBlock>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Examples(): ReactNode {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <Layout
      title="Examples"
      description="Real-world examples of using Resume as Code - capturing accomplishments, generating resumes, and integrating with other tools.">
      <main className={styles.examplesPage}>
        <div className="container">
          <div className={styles.header}>
            <Heading as="h1">Examples</Heading>
            <p className={styles.subtitle}>
              Real-world workflows showing Resume as Code in action.
              Click each example to see the commands and expected output.
            </p>
          </div>
          <div className={styles.examplesList}>
            {examples.map((example, idx) => (
              <ExampleCard
                key={idx}
                example={example}
                isOpen={openIndex === idx}
                onToggle={() => setOpenIndex(openIndex === idx ? null : idx)}
              />
            ))}
          </div>
        </div>
      </main>
    </Layout>
  );
}
