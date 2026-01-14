import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

/**
 * Resume as Code Documentation Sidebar
 *
 * Structure follows AC1 from the story:
 * - Getting Started
 * - Commands
 * - Data Model
 * - Configuration
 * - API Reference
 */
const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'doc',
      id: 'getting-started',
      label: 'Getting Started',
    },
    {
      type: 'category',
      label: 'Commands',
      collapsed: false,
      items: [
        'commands/new',
        'commands/list',
        'commands/show',
        'commands/remove',
        'commands/validate',
        'commands/plan',
        'commands/build',
        'commands/config',
      ],
    },
    {
      type: 'category',
      label: 'Data Model',
      collapsed: false,
      items: [
        'data-model/work-unit',
        'data-model/position',
        'data-model/certification',
        'data-model/education',
        'data-model/profile',
      ],
    },
    {
      type: 'doc',
      id: 'configuration',
      label: 'Configuration',
    },
  ],
};

export default sidebars;
