import type {ReactNode} from 'react';
import {useState} from 'react';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import CodeBlock from '@theme/CodeBlock';
import styles from './demo.module.css';

// Sample Work Units for the Plan Simulator
const sampleWorkUnits = [
  {
    id: 'wu-2024-01-cicd',
    title: 'Reduced deployment time by 80%',
    skills: ['CI/CD', 'GitHub Actions', 'Kubernetes', 'DevOps'],
    score: 0,
  },
  {
    id: 'wu-2024-02-security',
    title: 'Led SOC2 compliance initiative',
    skills: ['Security', 'Compliance', 'Risk Management', 'AWS'],
    score: 0,
  },
  {
    id: 'wu-2023-08-perf',
    title: 'Optimized API response time by 60%',
    skills: ['Performance', 'PostgreSQL', 'Redis', 'Python'],
    score: 0,
  },
  {
    id: 'wu-2023-06-team',
    title: 'Scaled engineering team from 5 to 15',
    skills: ['Leadership', 'Hiring', 'Mentoring', 'Team Building'],
    score: 0,
  },
  {
    id: 'wu-2023-03-arch',
    title: 'Designed microservices architecture',
    skills: ['Architecture', 'Microservices', 'Docker', 'AWS'],
    score: 0,
  },
];

function WorkUnitBuilder(): ReactNode {
  const [title, setTitle] = useState('');
  const [problem, setProblem] = useState('');
  const [actions, setActions] = useState('');
  const [result, setResult] = useState('');
  const [skills, setSkills] = useState('');
  const [copied, setCopied] = useState(false);

  const today = new Date().toISOString().slice(0, 10);
  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 30) || 'example';

  const yaml = `id: wu-${today}-${slug}
title: "${title || 'Your accomplishment title'}"

par:
  problem: >
    ${problem || 'Describe the challenge or context'}
  actions:
${actions.split('\n').filter(a => a.trim()).map(a => `    - "${a.trim()}"`).join('\n') || '    - "What you did"'}
  result: >
    ${result || 'The measurable outcome'}

skills_demonstrated:
${skills.split(',').filter(s => s.trim()).map(s => `  - "${s.trim()}"`).join('\n') || '  - "Skill"'}
`;

  const handleCopy = () => {
    navigator.clipboard.writeText(yaml);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={styles.demoSection}>
      <Heading as="h2">Work Unit Builder</Heading>
      <p className={styles.demoDescription}>
        Create a Work Unit interactively and see the YAML output in real-time.
      </p>
      <div className={styles.demoContainer}>
        <div className={styles.formSection}>
          <div className={styles.formField}>
            <label>Title (headline of your accomplishment)</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Reduced deployment time by 80%"
            />
          </div>
          <div className={styles.formField}>
            <label>Problem (the challenge or context)</label>
            <textarea
              value={problem}
              onChange={(e) => setProblem(e.target.value)}
              placeholder="Manual deployments took 4 hours and caused frequent outages"
            />
          </div>
          <div className={styles.formField}>
            <label>Actions (one per line)</label>
            <textarea
              value={actions}
              onChange={(e) => setActions(e.target.value)}
              placeholder="Designed CI/CD pipeline&#10;Implemented blue-green deployment&#10;Added automated rollback"
            />
          </div>
          <div className={styles.formField}>
            <label>Result (measurable outcome)</label>
            <textarea
              value={result}
              onChange={(e) => setResult(e.target.value)}
              placeholder="Deployments now take 48 minutes with zero-downtime releases"
            />
          </div>
          <div className={styles.formField}>
            <label>Skills (comma-separated)</label>
            <input
              type="text"
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
              placeholder="CI/CD, GitHub Actions, Kubernetes"
            />
          </div>
        </div>
        <div className={styles.previewSection}>
          <div className={styles.previewHeader}>
            <span>YAML Output</span>
            <button
              className={`${styles.copyButton} ${copied ? styles.copied : ''}`}
              onClick={handleCopy}
            >
              {copied ? '✓ Copied!' : 'Copy YAML'}
            </button>
          </div>
          <CodeBlock language="yaml">{yaml}</CodeBlock>
        </div>
      </div>
    </div>
  );
}

function PlanSimulator(): ReactNode {
  const [jdText, setJdText] = useState('');
  const [results, setResults] = useState<typeof sampleWorkUnits | null>(null);

  const runPlan = () => {
    const jdLower = jdText.toLowerCase();
    const scored = sampleWorkUnits.map((wu) => {
      let score = 0;
      wu.skills.forEach((skill) => {
        if (jdLower.includes(skill.toLowerCase())) {
          score += 0.2;
        }
      });
      if (jdLower.includes(wu.title.toLowerCase().slice(0, 20))) {
        score += 0.3;
      }
      // Add some randomness for demo
      score = Math.min(0.95, score + Math.random() * 0.2);
      return { ...wu, score: Math.round(score * 100) / 100 };
    });

    scored.sort((a, b) => b.score - a.score);
    setResults(scored);
  };

  return (
    <div className={styles.demoSection}>
      <Heading as="h2">Plan Simulator</Heading>
      <p className={styles.demoDescription}>
        Paste a job description and see how Work Units get ranked for relevance.
      </p>
      <div className={styles.demoContainer}>
        <div className={styles.formSection}>
          <div className={styles.formField}>
            <label>Job Description</label>
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste a job description here... Try including keywords like CI/CD, Kubernetes, Security, AWS, Leadership, etc."
              rows={8}
            />
          </div>
          <button className={styles.runButton} onClick={runPlan}>
            Run Plan
          </button>
        </div>
        <div className={styles.resultsSection}>
          <div className={styles.resultsHeader}>Ranked Work Units</div>
          {results ? (
            <div className={styles.resultsList}>
              {results.map((wu, idx) => (
                <div
                  key={wu.id}
                  className={`${styles.resultItem} ${idx < 3 ? styles.selected : styles.excluded}`}
                >
                  <span className={styles.resultScore}>{wu.score.toFixed(2)}</span>
                  <div className={styles.resultContent}>
                    <span className={styles.resultTitle}>{wu.title}</span>
                    <span className={styles.resultSkills}>{wu.skills.join(', ')}</span>
                  </div>
                  <span className={styles.resultStatus}>
                    {idx < 3 ? '✓ Selected' : '○ Excluded'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.resultsPlaceholder}>
              Enter a job description and click "Run Plan" to see ranked results.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function OutputPreview(): ReactNode {
  const [template, setTemplate] = useState('modern');

  return (
    <div className={styles.demoSection}>
      <Heading as="h2">Output Preview</Heading>
      <p className={styles.demoDescription}>
        See how Work Units render to resume bullets in different templates.
      </p>
      <div className={styles.templateSelector}>
        <button
          className={`${styles.templateButton} ${template === 'modern' ? styles.active : ''}`}
          onClick={() => setTemplate('modern')}
        >
          Modern
        </button>
        <button
          className={`${styles.templateButton} ${template === 'executive' ? styles.active : ''}`}
          onClick={() => setTemplate('executive')}
        >
          Executive
        </button>
        <button
          className={`${styles.templateButton} ${template === 'ats' ? styles.active : ''}`}
          onClick={() => setTemplate('ats')}
        >
          ATS-Safe
        </button>
      </div>
      <div className={styles.resumePreview}>
        <div className={styles.resumeHeader}>
          <h3>JANE SMITH</h3>
          <p>Senior Platform Engineer</p>
          <p className={styles.contact}>
            jane@example.com | San Francisco, CA | linkedin.com/in/janesmith
          </p>
        </div>
        <div className={styles.resumeSection}>
          <h4>PROFESSIONAL EXPERIENCE</h4>
          <div className={styles.job}>
            <div className={styles.jobHeader}>
              <strong>TechCorp Industries</strong>
              <span>Senior Platform Engineer</span>
              <span>2022 - Present</span>
            </div>
            <ul className={styles.bullets}>
              <li>
                {template === 'executive' && <strong>Infrastructure Excellence: </strong>}
                Reduced deployment time by 80% (4 hours → 48 minutes) by designing
                CI/CD pipeline with GitHub Actions and implementing blue-green deployment
                strategy
              </li>
              <li>
                {template === 'executive' && <strong>Security Leadership: </strong>}
                Led SOC2 compliance initiative, achieving certification in 6 months
                and establishing security-first culture across engineering team
              </li>
              <li>
                {template === 'executive' && <strong>Performance Optimization: </strong>}
                Optimized API response time by 60% through database indexing,
                query optimization, and Redis caching layer implementation
              </li>
            </ul>
          </div>
        </div>
        <div className={styles.templateNote}>
          Template: {template.charAt(0).toUpperCase() + template.slice(1)}
          {template === 'executive' && ' (includes bold category prefixes)'}
          {template === 'ats' && ' (plain text formatting for ATS compatibility)'}
        </div>
      </div>
    </div>
  );
}

export default function Demo(): ReactNode {
  return (
    <Layout
      title="Demo"
      description="Try Resume as Code interactively - build Work Units, simulate planning, and preview output.">
      <main className={styles.demoPage}>
        <div className="container">
          <div className={styles.header}>
            <Heading as="h1">Interactive Demo</Heading>
            <p className={styles.subtitle}>
              Experience Resume as Code without installing anything.
              Try the Work Unit builder, plan simulator, and output preview.
            </p>
          </div>
          <WorkUnitBuilder />
          <PlanSimulator />
          <OutputPreview />
        </div>
      </main>
    </Layout>
  );
}
