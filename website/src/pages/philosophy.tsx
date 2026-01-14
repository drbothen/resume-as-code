import type {ReactNode} from 'react';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import styles from './philosophy.module.css';

function ProblemSection(): ReactNode {
  return (
    <section className={styles.section}>
      <Heading as="h2">The Problem with Traditional Resumes</Heading>
      <p className={styles.lead}>
        Traditional resume management is document-centric, creating chaos and duplication.
      </p>
      <div className={styles.codeExample}>
        <pre>
{`Resume_v1.docx
Resume_v2_tech.docx
Resume_v2_tech_final.docx
Resume_v2_tech_final_FINAL.docx
Resume_for_Google.docx
Resume_for_Amazon.docx
...`}
        </pre>
      </div>
      <div className={styles.problemGrid}>
        <div className={styles.problemCard}>
          <Heading as="h3">No Single Source of Truth</Heading>
          <p>
            Accomplishments exist in dozens of slightly different documents.
            Which version has that metric you calculated? Was it 40% or 47%?
          </p>
        </div>
        <div className={styles.problemCard}>
          <Heading as="h3">Duplicate Effort</Heading>
          <p>
            Every job application means opening a document, copying bullets,
            rewording, reformatting, and hoping you didn't forget something.
          </p>
        </div>
        <div className={styles.problemCard}>
          <Heading as="h3">No Version Control</Heading>
          <p>
            Documents get renamed, overwritten, and lost. No history,
            no diffs, no collaboration without "Resume_v2_Josh_edits.docx" chaos.
          </p>
        </div>
        <div className={styles.problemCard}>
          <Heading as="h3">Lost Accomplishments</Heading>
          <p>
            That achievement from three jobs ago might be in one version but not another.
            Over time, your best work gets buried in the document graveyard.
          </p>
        </div>
      </div>
    </section>
  );
}

function SolutionSection(): ReactNode {
  return (
    <section className={styles.section}>
      <Heading as="h2">The Resume as Code Solution</Heading>
      <p className={styles.lead}>
        Resume as Code inverts the traditional model: data is truth, resumes are generated.
      </p>
      <table className={styles.comparisonTable}>
        <thead>
          <tr>
            <th>Traditional</th>
            <th>Resume as Code</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Documents are the source of truth</td>
            <td><strong>Data</strong> is the source of truth</td>
          </tr>
          <tr>
            <td>Resumes are edited</td>
            <td>Resumes are <strong>generated</strong></td>
          </tr>
          <tr>
            <td>Each application starts from scratch</td>
            <td>Each application is a <strong>query</strong></td>
          </tr>
          <tr>
            <td>Accomplishments scattered</td>
            <td>Accomplishments <strong>centralized</strong></td>
          </tr>
          <tr>
            <td>No history</td>
            <td><strong>Git-native</strong> history</td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}

function CoreConceptsSection(): ReactNode {
  return (
    <section className={styles.section}>
      <Heading as="h2">Core Concepts</Heading>

      <div className={styles.concept}>
        <Heading as="h3">Work Units: The Atomic Unit</Heading>
        <p>
          The Work Unit is the fundamental building block — not jobs (too coarse)
          and not bullet points (too fine). Each Work Unit is a complete accomplishment:
        </p>
        <ul>
          <li>What <strong>problem</strong> existed</li>
          <li>What <strong>actions</strong> you took</li>
          <li>What <strong>results</strong> you achieved</li>
          <li>What <strong>skills</strong> you demonstrated</li>
          <li>What <strong>metrics</strong> prove the impact</li>
        </ul>
      </div>

      <div className={styles.concept}>
        <Heading as="h3">The PAR Framework</Heading>
        <p>
          Every Work Unit follows the <strong>Problem-Action-Result</strong> framework,
          ensuring every accomplishment tells a complete story:
        </p>
        <div className={styles.parGrid}>
          <div className={styles.parCard}>
            <span className={styles.parLabel}>Problem</span>
            <span className={styles.parQuestion}>What challenge did you face?</span>
            <span className={styles.parExample}>"Manual deployments took 4 hours"</span>
          </div>
          <div className={styles.parCard}>
            <span className={styles.parLabel}>Action</span>
            <span className={styles.parQuestion}>What did you do?</span>
            <span className={styles.parExample}>"Built CI/CD pipeline with GitHub Actions"</span>
          </div>
          <div className={styles.parCard}>
            <span className={styles.parLabel}>Result</span>
            <span className={styles.parQuestion}>What was the outcome?</span>
            <span className={styles.parExample}>"Reduced deployment time by 80%"</span>
          </div>
        </div>
      </div>

      <div className={styles.concept}>
        <Heading as="h3">Resumes as Queries</Heading>
        <p>
          Here's the key insight: <strong>Your capability graph is fixed</strong> — what you've done doesn't change.
          Your Work Units are immutable facts about your past.
        </p>
        <p>
          <strong>Each job description is a query</strong> against that graph.
          Different jobs want different subsets of your experience.
        </p>
        <div className={styles.codeExample}>
          <pre>
{`# This is a query against your capability graph
resume plan --jd senior-platform-engineer.txt

# Output shows matches with relevance scores:
Selected Work Units:
✓ [0.87] wu-2024-06-15-cicd-pipeline
✓ [0.82] wu-2024-03-22-security-audit
✓ [0.75] wu-2023-11-08-team-scaling`}
          </pre>
        </div>
        <p>
          You're not editing a document — you're selecting from a pre-existing pool of accomplishments.
        </p>
      </div>
    </section>
  );
}

function BenefitsSection(): ReactNode {
  return (
    <section className={styles.section}>
      <Heading as="h2">Benefits</Heading>
      <div className={styles.benefitsGrid}>
        <div className={styles.benefitCard}>
          <span className={styles.benefitNumber}>1</span>
          <Heading as="h3">Never Lose an Accomplishment</Heading>
          <p>
            Every Work Unit is a permanent record. Even if you don't include it
            in a particular resume, it exists in your repository. Years later,
            you can still find that metric or project description.
          </p>
        </div>
        <div className={styles.benefitCard}>
          <span className={styles.benefitNumber}>2</span>
          <Heading as="h3">Consistent Quality</Heading>
          <p>
            Schema validation ensures every Work Unit meets minimum standards.
            You can't create a half-baked bullet point — the system enforces completeness.
          </p>
        </div>
        <div className={styles.benefitCard}>
          <span className={styles.benefitNumber}>3</span>
          <Heading as="h3">Targeted Applications</Heading>
          <p>
            The ranking algorithm finds Work Units that match each job description.
            You're not guessing what to include — the relevance is calculated.
          </p>
        </div>
        <div className={styles.benefitCard}>
          <span className={styles.benefitNumber}>4</span>
          <Heading as="h3">Full Audit Trail</Heading>
          <p>
            The manifest shows exactly what was included in each generated resume.
            You can always explain why something was or wasn't included.
          </p>
        </div>
        <div className={styles.benefitCard}>
          <span className={styles.benefitNumber}>5</span>
          <Heading as="h3">AI-Ready</Heading>
          <p>
            Structured data is machine-readable. AI assistants can suggest improvements,
            help draft new Work Units, identify gaps, and generate cover letters.
          </p>
        </div>
      </div>
    </section>
  );
}

export default function Philosophy(): ReactNode {
  return (
    <Layout
      title="Philosophy"
      description="The Resume as Code philosophy - treating career data as structured, queryable truth rather than prose to be rewritten.">
      <main className={styles.philosophyPage}>
        <div className="container">
          <div className={styles.header}>
            <Heading as="h1">The Resume as Code Philosophy</Heading>
            <p className={styles.subtitle}>
              Treating career data as <strong>structured, queryable truth</strong> rather
              than prose to be rewritten for each application.
            </p>
          </div>
          <ProblemSection />
          <SolutionSection />
          <CoreConceptsSection />
          <BenefitsSection />
        </div>
      </main>
    </Layout>
  );
}
