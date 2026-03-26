export interface NavItem {
  label: string;
  href: string;
  description: string;
  icon: string;
}

export interface NavGroup {
  group: string;
  items: NavItem[];
}

export const NAV_ITEMS: NavItem[] = [
  {
    label: 'Quickstart',
    href: '/docs/guides/quickstart',
    description: 'Install and run your first command in 5 minutes',
    icon: '⚡',
  },
  {
    label: 'Commands',
    href: '/docs/guides/commands',
    description: 'Full CLI command reference by layer',
    icon: '📋',
  },
  {
    label: 'License',
    href: '/docs/guides/license',
    description: 'License tiers, activation, and purchasing',
    icon: '🔑',
  },
  {
    label: 'RaaS',
    href: '/docs/guides/raas',
    description: 'Register tenant, API keys, and credit management',
    icon: '💳',
  },
  {
    label: 'SoloOS',
    href: '/docs/guides/solo-os',
    description: 'Start your AI company with 8 departments',
    icon: '🏢',
  },
  {
    label: 'VC Ready',
    href: '/docs/guides/vc-ready',
    description: 'Pitch generation, cap table, and compliance',
    icon: '📈',
  },
  {
    label: 'CLI Adapters',
    href: '/docs/guides/cli-adapters',
    description: 'Multi-provider routing, failover, and swarm',
    icon: '🤖',
  },
  {
    label: 'Architecture',
    href: '/docs/guides/architecture',
    description: 'PEV engine, API gateway, Workers, multi-tenant metering',
    icon: '🏗️',
  },
  {
    label: 'All Commands',
    href: '/docs/guides/all-commands',
    description: '135 commands across 20 roles — studio to worker',
    icon: '⚡',
  },
  {
    label: 'Skills Catalog',
    href: '/docs/guides/skills-catalog',
    description: '540 AI skills organized by category',
    icon: '🧩',
  },
];

export const NAV_GROUPS: NavGroup[] = [
  {
    group: 'Getting Started',
    items: NAV_ITEMS.slice(0, 2),
  },
  {
    group: 'Monetization',
    items: NAV_ITEMS.slice(2, 4),
  },
  {
    group: 'Business',
    items: NAV_ITEMS.slice(4, 6),
  },
  {
    group: 'Infrastructure',
    items: NAV_ITEMS.slice(6, 8),
  },
  {
    group: 'Reference',
    items: NAV_ITEMS.slice(8, 10),
  },
];
