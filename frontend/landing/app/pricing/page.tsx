import SiteNav from '@/components/site-nav'

const TIERS = [
  {
    name: 'Starter',
    price: '$49',
    period: '/tháng',
    desc: 'Dành cho solo founder và developer mới bắt đầu.',
    cta: 'Bắt đầu Starter',
    ctaHref: 'https://polar.sh/mekong-cli/checkout?product=starter',
    highlight: false,
    badge: undefined as string | undefined,
    features: [
      '100 credits / tháng',
      'Task đơn giản (1 credit)',
      'Core CLI commands',
      'Plan-Execute-Verify engine',
      'Email support',
    ],
  },
  {
    name: 'Pro',
    price: '$149',
    period: '/tháng',
    desc: 'Cho team ship production code ở quy mô lớn.',
    cta: 'Bắt đầu Pro',
    ctaHref: 'https://polar.sh/mekong-cli/checkout?product=pro',
    highlight: true,
    badge: 'Phổ biến nhất',
    features: [
      '1,000 credits / tháng',
      'Tất cả mức độ phức tạp (1-5 credits)',
      'Tôm Hùm daemon tự động',
      'Antigravity Proxy access',
      'Priority support (24h)',
      'Tất cả 464 skills',
    ],
  },
  {
    name: 'Enterprise',
    price: '$499',
    period: '/tháng',
    desc: 'Unlimited AI power cho engineering team nghiêm túc.',
    cta: 'Liên hệ Enterprise',
    ctaHref: 'https://polar.sh/mekong-cli/checkout?product=enterprise',
    highlight: false,
    badge: undefined as string | undefined,
    features: [
      'Unlimited credits',
      'Custom AI agents',
      'SLA 99.9% uptime',
      'Dedicated onboarding',
      'White-label options',
      'Hỗ trợ ưu tiên 24/7',
    ],
  },
]

const CREDIT_TIERS = [
  { complexity: 'Simple (1 credit)', commands: '/status, /help, /plan', color: 'text-green-400' },
  { complexity: 'Standard (3 credits)', commands: '/cook, /fix, /review, /sales', color: 'text-blue-400' },
  { complexity: 'Complex (5 credits)', commands: '/deploy, /cap-table, /negotiate, IPO commands', color: 'text-purple-400' },
]

const FAQS = [
  {
    q: 'MCU là gì?',
    a: 'MCU = Mekong Credit Unit. 1 MCU = 1 agent task execution. Giá tính theo mức độ phức tạp của task.',
  },
  {
    q: 'Hết credit thì sao?',
    a: 'API trả HTTP 402 (Payment Required). Bạn có thể mua thêm credit hoặc upgrade lên plan cao hơn bất cứ lúc nào.',
  },
  {
    q: 'Huỷ được không?',
    a: 'Huỷ bất cứ lúc nào, không phí. Không cam kết dài hạn, không phí ẩn.',
  },
  {
    q: 'Enterprise tùy chỉnh được không?',
    a: 'Có. Enterprise plan hỗ trợ custom agents, white-label, và SLA riêng. Liên hệ để nhận quote phù hợp với team của bạn.',
  },
]

export default function PricingPage() {
  return (
    <main className="min-h-screen bg-slate-950">
      <SiteNav />

      {/* Hero */}
      <section className="px-6 pb-8 pt-12 text-center">
        <div className="mx-auto max-w-2xl">
          <h1 className="mb-4 text-4xl font-extrabold text-white sm:text-5xl">
            Bảng giá —{' '}
            <span className="gradient-text">Trả theo credit, không phí ẩn</span>
          </h1>
          <p className="text-lg text-slate-400">
            Scale khi cần. Hủy bất kỳ lúc nào. Không cam kết dài hạn.
          </p>
        </div>
      </section>

      {/* Pricing tiers */}
      <section className="px-6 pb-16">
        <div className="mx-auto max-w-5xl">
          <div className="grid gap-6 sm:grid-cols-3">
            {TIERS.map((tier) => (
              <div
                key={tier.name}
                className={`relative flex flex-col rounded-2xl p-7 ${
                  tier.highlight ? 'glass-highlight' : 'glass-card'
                }`}
              >
                {tier.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-blue-600 to-cyan-600 px-4 py-1 text-xs font-semibold text-white whitespace-nowrap">
                    {tier.badge}
                  </div>
                )}

                <div className="mb-5">
                  <h2 className="mb-1 text-lg font-bold text-white">{tier.name}</h2>
                  <div className="mb-2 flex items-end gap-1">
                    <span className="text-4xl font-extrabold text-white">{tier.price}</span>
                    <span className="mb-1 text-slate-400">{tier.period}</span>
                  </div>
                  <p className="text-sm text-slate-400">{tier.desc}</p>
                </div>

                <ul className="mb-7 flex-1 space-y-3">
                  {tier.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm text-slate-300">
                      <span className="mt-0.5 text-cyan-400">✓</span>
                      {f}
                    </li>
                  ))}
                </ul>

                <a
                  href={tier.ctaHref}
                  className={`block rounded-xl py-3 text-center font-semibold transition-opacity hover:opacity-90 ${
                    tier.highlight
                      ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white'
                      : 'border border-slate-700 text-slate-300 hover:border-slate-500 hover:text-white'
                  }`}
                >
                  {tier.cta}
                </a>
              </div>
            ))}
          </div>

          <p className="mt-6 text-center text-xs text-slate-600">
            Giá tính bằng USD. Hủy bất kỳ lúc nào.
          </p>
        </div>
      </section>

      {/* Credit explanation */}
      <section className="px-6 pb-16">
        <div className="mx-auto max-w-3xl">
          <div className="glass-card rounded-2xl p-8">
            <h2 className="mb-6 text-xl font-bold text-white">Cách tính credit</h2>
            <div className="space-y-4">
              {CREDIT_TIERS.map((ct) => (
                <div key={ct.complexity} className="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-6">
                  <span className={`shrink-0 font-semibold ${ct.color} text-sm w-44`}>
                    {ct.complexity}
                  </span>
                  <span className="font-mono text-xs text-slate-400">{ct.commands}</span>
                </div>
              ))}
            </div>
            <p className="mt-6 text-xs text-slate-500">
              Free commands (0 credit): <span className="font-mono text-slate-400">/status, /help, /founder/ARCHITECTURE, /raas</span>
            </p>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="px-6 pb-20">
        <div className="mx-auto max-w-3xl">
          <h2 className="mb-8 text-center text-2xl font-bold text-white">
            Câu hỏi thường gặp
          </h2>
          <div className="space-y-4">
            {FAQS.map((faq) => (
              <div key={faq.q} className="glass-card rounded-xl p-6">
                <h3 className="mb-2 font-semibold text-white">{faq.q}</h3>
                <p className="text-sm text-slate-400">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  )
}
