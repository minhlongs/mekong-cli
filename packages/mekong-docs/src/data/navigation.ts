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
    href: '/guides/quickstart',
    description: 'Install and run your first command in 5 minutes',
    icon: '⚡',
  },
  {
    label: 'Commands',
    href: '/guides/commands',
    description: 'Full CLI command reference by layer',
    icon: '📋',
  },
  {
    label: 'License',
    href: '/guides/license',
    description: 'License tiers, activation, and purchasing',
    icon: '🔑',
  },
  {
    label: 'RaaS',
    href: '/guides/raas',
    description: 'Register tenant, API keys, and credit management',
    icon: '💳',
  },
  {
    label: 'SoloOS',
    href: '/guides/solo-os',
    description: 'Start your AI company with 8 departments',
    icon: '🏢',
  },
  {
    label: 'VC Ready',
    href: '/guides/vc-ready',
    description: 'Pitch generation, cap table, and compliance',
    icon: '📈',
  },
  {
    label: 'CLI Adapters',
    href: '/guides/cli-adapters',
    description: 'Multi-provider routing, failover, and swarm',
    icon: '🤖',
  },
  {
    label: 'Architecture',
    href: '/guides/architecture',
    description: 'PEV engine, API gateway, Workers, multi-tenant metering',
    icon: '🏗️',
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
];
