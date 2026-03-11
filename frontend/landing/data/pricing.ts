// Single source of truth for pricing tiers, FAQs, and credit tiers.
// Pricing model: Starter $49 / Pro $149 / Enterprise $499 (MCU credits)
// Free tier = CLI is open-source, use with own LLM key (BYOK). No $0 tier.

export interface PricingTier {
  name: string
  price: string
  period: string
  desc: string
  cta: string
  ctaHref: string
  highlight: boolean
  badge?: string
  features: string[]
}

export const TIERS: PricingTier[] = [
  {
    name: 'Starter',
    price: '$49',
    period: '/month',
    desc: 'For solo founders and developers getting started.',
    cta: 'Start Starter',
    ctaHref: 'https://polar.sh/mekong-cli/checkout?product=starter',
    highlight: false,
    badge: undefined,
    features: [
      '200 credits / month',
      'Simple tasks (1 credit)',
      'Core CLI commands',
      'Plan-Execute-Verify engine',
      'Email support',
    ],
  },
  {
    name: 'Pro',
    price: '$149',
    period: '/month',
    desc: 'For teams shipping production code at scale.',
    cta: 'Start Pro',
    ctaHref: 'https://polar.sh/mekong-cli/checkout?product=pro',
    highlight: true,
    badge: 'Most popular',
    features: [
      '1,000 credits / month',
      'All complexity levels (1-5 credits)',
      'Tôm Hùm autonomous daemon',
      'BYOK LLM — OpenRouter / Ollama / Direct API',
      'Priority support (24h)',
      'All skills included',
    ],
  },
  {
    name: 'Enterprise',
    price: '$499',
    period: '/month',
    desc: 'Unlimited AI power for serious engineering teams.',
    cta: 'Contact Enterprise',
    ctaHref: 'https://polar.sh/mekong-cli/checkout?product=enterprise',
    highlight: false,
    badge: undefined,
    features: [
      'Unlimited credits',
      'Custom AI agents',
      'SLA 99.9% uptime',
      'Dedicated onboarding',
      'White-label options',
      'Priority support 24/7',
    ],
  },
]

export interface CreditTier {
  complexity: string
  commands: string
  color: string
}

export const CREDIT_TIERS: CreditTier[] = [
  { complexity: 'Simple (1 credit)', commands: '/status, /help, /plan', color: 'text-green-400' },
  { complexity: 'Standard (3 credits)', commands: '/cook, /fix, /review, /sales', color: 'text-blue-400' },
  { complexity: 'Complex (5 credits)', commands: '/deploy, /cap-table, /negotiate, IPO commands', color: 'text-purple-400' },
]

export interface FAQ {
  q: string
  a: string
}

export const FAQS: FAQ[] = [
  {
    q: 'What is an MCU?',
    a: 'MCU = Mekong Credit Unit. 1 MCU = 1 agent task execution. Pricing is based on task complexity.',
  },
  {
    q: 'What happens when I run out of credits?',
    a: 'The API returns HTTP 402 (Payment Required). You can buy more credits or upgrade your plan anytime.',
  },
  {
    q: 'Can I cancel anytime?',
    a: 'Cancel anytime, no fees. No long-term commitment, no hidden charges.',
  },
  {
    q: 'Can Enterprise be customized?',
    a: 'Yes. Enterprise plan supports custom agents, white-label, and dedicated SLA. Contact us for a quote tailored to your team.',
  },
]
