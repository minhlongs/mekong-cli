const FEATURES = [
  {
    icon: '🧠',
    title: 'Plan → Execute → Verify',
    desc: 'AI tự lập kế hoạch, phân rã thành tasks, thực thi từng bước và tự kiểm tra chất lượng kết quả.',
  },
  {
    icon: '🔄',
    title: 'Self-Healing Pipeline',
    desc: 'Nếu bước nào lỗi, AI tự phát hiện nguyên nhân gốc rễ và sửa — không cần can thiệp thủ công.',
  },
  {
    icon: '🔓',
    title: 'Open Source 100%',
    desc: 'MIT License. Fork về chạy riêng, tuỳ chỉnh agents, không bị vendor lock-in bao giờ.',
  },
  {
    icon: '💳',
    title: 'Trả theo kết quả',
    desc: '1 credit task đơn giản, 3 credits task trung bình, 5 credits task phức tạp. Chỉ trả khi thành công.',
  },
  {
    icon: '🏯',
    title: '5 tầng doanh nghiệp',
    desc: 'Founder → Business → Product → Engineering → Ops. Mỗi tầng có agents chuyên biệt sẵn sàng.',
  },
  {
    icon: '🌊',
    title: 'Cascade tự động',
    desc: 'Kế hoạch cấp cao tự động phân rã thành tasks song song. Nhiều agents chạy đồng thời.',
  },
]

export default function FeaturesGrid() {
  return (
    <section id="features" className="px-6 py-20">
      <div className="mx-auto max-w-5xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Tại sao chọn{' '}
            <span className="gradient-text">AgencyOS RaaS?</span>
          </h2>
          <p className="text-slate-400">
            Infrastructure tự trị cho AI agents — open-source core, tính tiền theo kết quả thực tế.
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
