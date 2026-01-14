import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <p className={styles.heroDescription}>
          Store your career accomplishments as structured data. Generate tailored resumes on demand.
          Never maintain multiple resume versions again.
        </p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/getting-started">
            Get Started
          </Link>
          <Link
            className="button button--outline button--secondary button--lg"
            to="https://github.com/jmagady/resume">
            View on GitHub
          </Link>
        </div>
      </div>
    </header>
  );
}

function HowItWorks(): ReactNode {
  return (
    <section className={styles.howItWorks}>
      <div className="container">
        <Heading as="h2" className="text--center margin-bottom--lg">
          How It Works
        </Heading>
        <div className="row">
          <div className={clsx('col col--4', styles.step)}>
            <div className={styles.stepNumber}>1</div>
            <Heading as="h3">Capture</Heading>
            <p>
              Record accomplishments as Work Units right after they happen.
              Each Work Unit captures the problem, your actions, and the result.
            </p>
          </div>
          <div className={clsx('col col--4', styles.step)}>
            <div className={styles.stepNumber}>2</div>
            <Heading as="h3">Plan</Heading>
            <p>
              Run <code>resume plan</code> with a job description.
              Smart ranking selects your most relevant achievements.
            </p>
          </div>
          <div className={clsx('col col--4', styles.step)}>
            <div className={styles.stepNumber}>3</div>
            <Heading as="h3">Generate</Heading>
            <p>
              Build a tailored PDF or DOCX resume.
              Full provenance tracking shows exactly what was included and why.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function CodeExample(): ReactNode {
  return (
    <section className={styles.codeExample}>
      <div className="container">
        <div className="row">
          <div className="col col--6">
            <Heading as="h2">Simple CLI Interface</Heading>
            <p>
              Resume as Code provides an intuitive command-line interface
              designed for both humans and AI agents.
            </p>
            <ul className={styles.featureList}>
              <li>Interactive mode for guided data entry</li>
              <li>Pipe-separated format for scripting</li>
              <li>JSON output for programmatic access</li>
              <li>Comprehensive validation with actionable feedback</li>
            </ul>
          </div>
          <div className="col col--6">
            <pre className={styles.codeBlock}>
{`# Create a position
resume new position "TechCorp|Senior Engineer|2022-01|"

# Capture an accomplishment
resume new work-unit \\
  --position-id pos-techcorp-senior-engineer \\
  --title "Reduced deployment time by 80%"

# Generate resume for a job
resume plan --jd job-description.txt
resume build`}
            </pre>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title="Git-native resume generation"
      description="Treat your career data as structured, queryable truth. Store accomplishments as Work Units, generate tailored resumes on demand.">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        <HowItWorks />
        <CodeExample />
      </main>
    </Layout>
  );
}
