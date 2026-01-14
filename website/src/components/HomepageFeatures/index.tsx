import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  emoji: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Work Unit Capture',
    emoji: '📝',
    description: (
      <>
        Store accomplishments as structured Work Units with Problem-Action-Result context.
        Capture achievements right when they happen, never lose track of your wins.
      </>
    ),
  },
  {
    title: 'Smart Ranking',
    emoji: '🎯',
    description: (
      <>
        BM25 + semantic matching automatically selects your most relevant Work Units
        for each job description. See exactly why each achievement was selected.
      </>
    ),
  },
  {
    title: 'Gap Analysis',
    emoji: '🔍',
    description: (
      <>
        Instantly see which required skills you've demonstrated and which ones are missing.
        Know exactly where to focus your professional development.
      </>
    ),
  },
  {
    title: 'Multiple Formats',
    emoji: '📄',
    description: (
      <>
        Generate PDF, DOCX, and JSON outputs with full provenance tracking.
        Every resume includes a manifest showing exactly what was included.
      </>
    ),
  },
  {
    title: 'Executive Templates',
    emoji: '👔',
    description: (
      <>
        Professional resume templates designed for senior and executive roles.
        Scope indicators highlight your leadership impact.
      </>
    ),
  },
  {
    title: 'Git-Native',
    emoji: '🔄',
    description: (
      <>
        All data stored as YAML files in your repository. Track changes,
        collaborate with PRs, and maintain a complete history of your career.
      </>
    ),
  },
];

function Feature({title, emoji, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <span className={styles.featureEmoji} role="img" aria-label={title}>
          {emoji}
        </span>
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <Heading as="h2" className="text--center margin-bottom--lg">
          Key Features
        </Heading>
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
