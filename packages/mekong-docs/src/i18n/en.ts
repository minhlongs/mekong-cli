export const en = {
  nav: {
    home: 'Home',
    guides: 'Guides',
    pricing: 'Pricing',
    github: 'GitHub',
  },
  hero: {
    title: 'OpenClaw — AGI CLI for Solo Founders',
    subtitle: 'Run your entire company from the terminal. 16+ packages. 1 person. 0 employees.',
    cta_install: 'Install',
    cta_guides: 'Read Guides',
    cta_copy: 'Copy',
    cta_copied: 'Copied!',
  },
  features: {
    title: 'Everything you need to run a company',
    subtitle: 'From idea to exit — without hiring a single employee.',
  },
  terminal: {
    title: 'See it in action',
    subtitle: 'One command. Infinite leverage.',
  },
  install: {
    title: 'Get started in 30 seconds',
    step1: 'Install the CLI',
    step2: 'Initialize your company',
    step3: 'Run your first mission',
  },
  footer: {
    tagline: '16+ packages. 1 person. 0 employees.',
    copyright: 'OpenClaw',
  },
  pricing: {
    title: 'Simple, transparent pricing',
    subtitle: 'Pick the product that fits your stack.',
    free: 'Free',
    starter: 'Starter',
    pro: 'Pro',
    enterprise: 'Enterprise',
    per_month: '/mo',
    buy: 'Buy on Polar',
    contact: 'Contact Sales',
    get_started: 'Get Started',
  },
  guides: {
    title: 'Guides',
    subtitle: 'Everything you need to master OpenClaw.',
    read_more: 'Read guide →',
  },
} as const;

export type Translations = typeof en;
