import type {ReactNode} from 'react';
import clsx from 'clsx';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import Link from '@docusaurus/Link';
import styles from './features.module.css';

type Feature = {
  title: string;
  emoji: string;
  description: string;
  details: string[];
  link?: string;
};

const features: Feature[] = [
  {
    title: 'Work Unit Capture',
    emoji: '📝',
    description: 'Store accomplishments as structured data with full context.',
    details: [
      'Problem-Action-Result (PAR) framework for complete stories',
      'Skills automatically extracted and categorized',
      'Evidence links for supporting artifacts',
      'Archetype templates for common achievement types',
    ],
    link: '/docs/data-model/work-unit',
  },
  {
    title: 'Smart Ranking',
    emoji: '🎯',
    description: 'AI-powered selection of your most relevant achievements.',
    details: [
      'BM25 keyword matching for precision',
      'Semantic similarity using sentence transformers',
      'Configurable scoring weights',
      'Transparent scoring explanations',
    ],
    link: '/docs/commands/plan',
  },
  {
    title: 'Gap Analysis',
    emoji: '🔍',
    description: 'See exactly what skills you have and what you\'re missing.',
    details: [
      'Automatic JD requirement extraction',
      'Skill coverage visualization',
      'Identified gaps with recommendations',
      'Career development insights',
    ],
    link: '/docs/commands/plan',
  },
  {
    title: 'Multiple Output Formats',
    emoji: '📄',
    description: 'Generate professional documents in any format you need.',
    details: [
      'PDF with beautiful typesetting (WeasyPrint)',
      'DOCX for ATS compatibility',
      'JSON for programmatic access',
      'HTML for web viewing',
    ],
    link: '/docs/commands/build',
  },
  {
    title: 'Executive Templates',
    emoji: '👔',
    description: 'Professional templates designed for senior roles.',
    details: [
      'Scope indicators (revenue, team size, budget)',
      'Career highlights section',
      'Board & advisory roles support',
      'Publications & speaking engagements',
    ],
    link: '/docs/getting-started',
  },
  {
    title: 'Git-Native',
    emoji: '🔄',
    description: 'All data lives in version-controlled YAML files.',
    details: [
      'Full history of career changes',
      'Collaborate via pull requests',
      'Branch for resume experiments',
      'CI/CD for automated builds',
    ],
  },
  {
    title: 'AI-Ready',
    emoji: '🤖',
    description: 'Structured data designed for LLM assistance.',
    details: [
      'JSON output for programmatic parsing',
      'Pipe-separated format for scripting',
      'Clear schemas for validation',
      'Context-rich error messages',
    ],
  },
  {
    title: 'Provenance Tracking',
    emoji: '📋',
    description: 'Know exactly what went into every resume.',
    details: [
      'Manifest with included Work Units',
      'Selection scores and reasoning',
      'Build timestamp and inputs hash',
      'Reproducible generation',
    ],
    link: '/docs/commands/build',
  },
];

function FeatureCard({title, emoji, description, details, link}: Feature): ReactNode {
  return (
    <div className={clsx('col col--6', styles.featureCol)}>
      <div className={styles.featureCard}>
        <div className={styles.featureHeader}>
          <span className={styles.featureEmoji}>{emoji}</span>
          <Heading as="h3">{title}</Heading>
        </div>
        <p className={styles.featureDescription}>{description}</p>
        <ul className={styles.featureDetails}>
          {details.map((detail, idx) => (
            <li key={idx}>{detail}</li>
          ))}
        </ul>
        {link && (
          <Link className={styles.featureLink} to={link}>
            Learn more →
          </Link>
        )}
      </div>
    </div>
  );
}

export default function Features(): ReactNode {
  return (
    <Layout
      title="Features"
      description="Explore the features of Resume as Code - Work Unit capture, smart ranking, gap analysis, and more.">
      <main className={styles.featuresPage}>
        <div className="container">
          <div className={styles.header}>
            <Heading as="h1">Features</Heading>
            <p className={styles.subtitle}>
              Everything you need to treat your career data as structured, queryable truth.
            </p>
          </div>
          <div className="row">
            {features.map((feature, idx) => (
              <FeatureCard key={idx} {...feature} />
            ))}
          </div>
        </div>
      </main>
    </Layout>
  );
}
