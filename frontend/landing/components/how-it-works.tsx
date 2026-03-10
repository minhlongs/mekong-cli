const STEPS = [
  {
    emoji: '📝',
    number: '01',
    title: 'Mô tả mục tiêu',
    desc: 'Nhập mục tiêu bằng tiếng Việt. Ví dụ: "Tạo landing page cho quán cà phê".',
  },
  {
    emoji: '💳',
    number: '02',
    title: 'Trả credits',
    desc: '3 credits = task trung bình (~$15). Chỉ trừ sau khi giao hàng thành công.',
  },
  {
    emoji: '🦞',
    number: '03',
    title: 'AI thực thi',
    desc: 'Plan → Execute → Verify hoàn toàn tự động. Tôm Hùm agent tự sửa lỗi nếu gặp sự cố.',
  },
  {
    emoji: '✅',
    number: '04',
    title: 'Nhận kết quả',
    desc: 'File + link sẵn sàng trong 15 phút. Audit trail đầy đủ từng bước thực thi.',
  },
]

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="px-6 py-20">
      <div className="mx-auto max-w-5xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Cách hoạt động{' '}
            <span className="gradient-text">4 bước</span>
          </h2>
          <p className="text-slate-400">
            Từ mục tiêu đến kết quả được kiểm chứng — không cần setup, không cần chờ đợi.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step) => (
            <div key={step.number} className="relative rounded-2xl glass-card p-6 text-center">
              <div className="mb-3 text-4xl">{step.emoji}</div>
              <div className="mb-2 font-mono text-xs tracking-widest text-cyan-400">
                BƯỚC {step.number}
              </div>
              <h3 className="mb-2 font-semibold text-white">{step.title}</h3>
              <p className="text-sm leading-relaxed text-slate-400">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
