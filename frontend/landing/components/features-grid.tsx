const FEATURES = [
  {
    icon: '⚙️',
    title: 'Plan-Execute-Verify',
    desc: 'Mọi task qua 3 bước: lên kế hoạch, thực thi, kiểm tra. Tự rollback nếu thất bại.',
  },
  {
    icon: '🏯',
    title: 'Kim Tự Tháp 5 Tầng',
    desc: 'Founder → Business → Product → Engineering → Ops. Commands cascade tự động.',
  },
  {
    icon: '🤖',
    title: '105 AI Agents',
    desc: '18 hubs chuyên biệt. Mỗi agent chuyên một việc. Orchestrator phối hợp.',
  },
  {
    icon: '🔑',
    title: 'RaaS License',
    desc: 'Xây AI agency riêng. Gate features bằng API key. Tính tiền bằng MCU.',
  },
  {
    icon: '🌊',
    title: 'Antigravity Proxy',
    desc: 'Route LLM calls qua proxy thông minh. Tự failover khi rate limit.',
  },
  {
    icon: '🔌',
    title: '464 Skills',
    desc: 'Từ fundraise đến deploy. Auto-activate theo context. Fork và tùy biến.',
  },
]

export default function FeaturesGrid() {
  return (
    <section id="features" className="px-6 py-20">
      <div className="mx-auto max-w-5xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Mọi thứ bạn cần để ship{' '}
            <span className="gradient-text">nhanh hơn 10x</span>
          </h2>
          <p className="text-slate-400">
            Binh Pháp strategy gặp AI tooling hiện đại. Tôn Tử sẽ đồng ý.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-2xl glass-card p-6">
              <div className="mb-3 text-3xl">{f.icon}</div>
              <h3 className="mb-2 font-semibold text-white">{f.title}</h3>
              <p className="text-sm leading-relaxed text-slate-400">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
