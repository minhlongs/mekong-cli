export interface Feature {
  icon: string;
  title: string;
  description: string;
  tag: string;
}

export const FEATURES: Feature[] = [
  {
    icon: '🏢',
    title: 'SoloOS',
    description: '8-department AI company. Sales, Marketing, Finance, HR, Product, Engineering, Ops, and Legal — all autonomous.',
    tag: 'Core',
  },
  {
    icon: '💳',
    title: 'RaaS',
    description: 'License + credit metering out of the box. Monetize any CLI or API with Polar.sh webhooks and MCU billing.',
    tag: 'Monetize',
  },
  {
    icon: '🤖',
    title: 'Multi-CLI',
    description: 'CC CLI + Gemini + Qwen + any OpenAI-compatible provider. Automatic failover and swarm routing.',
    tag: 'AI',
  },
  {
    icon: '🧬',
    title: 'AGI Evolution',
    description: 'Self-improving codebase. The engine audits itself, proposes refactors, and ships improvements autonomously.',
    tag: 'Advanced',
  },
  {
    icon: '📈',
    title: 'VC Ready',
    description: 'Pitch deck generation, cap table management, data room, compliance reports, and exit strategy planning.',
    tag: 'Founder',
  },
  {
    icon: '🔑',
    title: 'License SDK',
    description: 'Monetize any repo. Drop-in license gate with seat management, usage quotas, and audit trail.',
    tag: 'SDK',
  },
];
