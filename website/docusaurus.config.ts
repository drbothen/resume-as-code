import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'Resume as Code',
  tagline: 'Treat your career data as structured, queryable truth',
  favicon: 'img/favicon.ico',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  // Set the production url of your site here
  url: 'https://drbothen.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/resume-as-code/',

  // GitHub pages deployment config.
  organizationName: 'drbothen', // Usually your GitHub org/user name.
  projectName: 'resume-as-code', // Usually your repo name.
  trailingSlash: false,

  onBrokenLinks: 'throw',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang.
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  headTags: [
    {
      tagName: 'meta',
      attributes: {
        name: 'keywords',
        content: 'resume, CV, career, job search, CLI, developer tools, resume generator, work units, job application',
      },
    },
    {
      tagName: 'meta',
      attributes: {
        name: 'author',
        content: 'Joshua Magady',
      },
    },
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/drbothen/resume-as-code/tree/main/website/',
        },
        blog: false, // Disabled until we have blog content
        sitemap: {
          lastmod: 'date',
          changefreq: 'weekly',
          priority: 0.5,
          filename: 'sitemap.xml',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Social card for sharing (replace with custom image)
    image: 'img/docusaurus-social-card.jpg',
    metadata: [
      {name: 'twitter:card', content: 'summary_large_image'},
      {name: 'twitter:title', content: 'Resume as Code'},
      {name: 'twitter:description', content: 'Treat your career data as structured, queryable truth. Generate tailored resumes from your work history.'},
      {property: 'og:type', content: 'website'},
      {property: 'og:title', content: 'Resume as Code'},
      {property: 'og:description', content: 'Treat your career data as structured, queryable truth. Generate tailored resumes from your work history.'},
    ],
    colorMode: {
      defaultMode: 'light',
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Resume as Code',
      logo: {
        alt: 'Resume as Code Logo',
        src: 'img/logo.svg',
      },
      items: [
        {to: '/features', label: 'Features', position: 'left'},
        {to: '/philosophy', label: 'Philosophy', position: 'left'},
        {to: '/demo', label: 'Demo', position: 'left'},
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {to: '/examples', label: 'Examples', position: 'left'},
        {
          href: 'https://github.com/drbothen/resume-as-code',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Learn',
          items: [
            {
              label: 'Getting Started',
              to: '/docs/getting-started',
            },
            {
              label: 'Philosophy',
              to: '/philosophy',
            },
            {
              label: 'Examples',
              to: '/examples',
            },
          ],
        },
        {
          title: 'Documentation',
          items: [
            {
              label: 'Commands',
              to: '/docs/commands/new',
            },
            {
              label: 'Data Model',
              to: '/docs/data-model/work-unit',
            },
            {
              label: 'Configuration',
              to: '/docs/configuration',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/drbothen/resume-as-code',
            },
            {
              label: 'Issues',
              href: 'https://github.com/drbothen/resume-as-code/issues',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Resume as Code. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'yaml', 'python'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
