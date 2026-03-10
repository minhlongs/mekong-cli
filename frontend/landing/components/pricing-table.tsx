const TIERS = [
  {
    name: 'Thử nghiệm',
    price: '$0',
    period: '/tháng',
    desc: '5 credits miễn phí để trải nghiệm. Không cần thẻ tín dụng.',
    cta: 'Bắt đầu miễn phí',
    ctaHref: 'https://polar.sh/mekong-cli/checkout?product=free',
    highlight: false,
    badge: undefined,
    features: [
      '5 credits miễn phí',
      'Tasks đơn giản (1 credit)',
      'Core CLI commands',
      'Plan → Execute → Verify engine',
      'Hỗ trợ cộng đồng',
    ],
  },
  {
    name: 'Chuyên nghiệp',
    price: '$49',
    period: '/tháng',
    desc: '200 credits/tháng. Tất cả loại task, ưu tiên xử lý.',
    cta: 'Đăng ký ngay',
    ctaHref: 'https://polar.sh/mekong-cli/checkout?product=pro',
    highlight: true,
    badge: 'Phổ biến nhất',
    features: [
      '200 credits / tháng',
      'Tất cả loại task (1-5 credits)',
      'Ưu tiên xử lý (hàng đầu queue)',
      'Self-healing pipeline',
      'Webhook integrations',
      'Audit trail đầy đủ',
    ],
  },
  {
    name: 'Doanh nghiệp',
    price: 'Liên hệ',
    period: '',
    desc: 'Credits không giới hạn, custom agents, tự host trên hạ tầng riêng.',
    cta: 'Liên hệ tư vấn',
    ctaHref: 'mailto:hello@agencyos.network',
    highlight: false,
    badge: undefined,
    features: [
      'Credits không giới hạn',
      'Custom agents theo yêu cầu',
      'Self-hosted deployment',
      'SLA đảm bảo uptime',
      'Hỗ trợ kỹ thuật riêng',
      'Audit bảo mật & compliance',
    ],
  },
]

export default function PricingTable() {
  return (
    <section id="pricing" className="px-6 py-20">
      <div className="mx-auto max-w-5xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Bảng giá credits,{' '}
            <span className="gradient-text">không phí ẩn</span>
          </h2>
          <p className="text-slate-400">
            Trả theo kết quả thực tế. Huỷ bất kỳ lúc nào.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-3">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`relative flex flex-col rounded-2xl p-7 ${
                tier.highlight
                  ? 'glass-highlight'
                  : 'glass-card'
              }`}
            >
              {tier.badge && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-blue-600 to-cyan-600 px-4 py-1 text-xs font-semibold text-white whitespace-nowrap">
                  {tier.badge}
                </div>
              )}

              <div className="mb-5">
                <h3 className="mb-1 text-lg font-bold text-white">{tier.name}</h3>
                <div className="mb-2 flex items-end gap-1">
                  <span className="text-4xl font-extrabold text-white">{tier.price}</span>
                  {tier.period && (
                    <span className="mb-1 text-slate-400">{tier.period}</span>
                  )}
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

        <p className="mt-8 text-center text-xs text-slate-600">
          MCU = Mekong Credit Unit. 1 credit ≈ 1 agent task execution.
          Giá tính bằng USD. Huỷ bất kỳ lúc nào.
        </p>
      </div>
    </section>
  )
}
