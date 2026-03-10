import { SERVICES } from '@/data/services'

const CATEGORY_LABELS = {
  business: 'Kinh doanh',
  tech: 'Kỹ thuật',
  marketing: 'Marketing',
}

const CATEGORY_COLORS = {
  business: 'text-amber-400 border-amber-400/30 bg-amber-400/10',
  tech: 'text-cyan-400 border-cyan-400/30 bg-cyan-400/10',
  marketing: 'text-emerald-400 border-emerald-400/30 bg-emerald-400/10',
}

export default function ServiceCards() {
  return (
    <section id="services" className="px-6 py-20">
      <div className="mx-auto max-w-5xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Dịch vụ{' '}
            <span className="gradient-text">đóng gói sẵn</span>
          </h2>
          <p className="text-slate-400">
            Chọn dịch vụ, trả credits, nhận kết quả. Không setup, không chờ đợi.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {SERVICES.map((service) => (
            <div key={service.id} className="flex flex-col rounded-2xl glass-card p-6">
              <div className="mb-3">
                <span
                  className={`inline-block rounded-full border px-2.5 py-0.5 text-xs font-semibold ${CATEGORY_COLORS[service.category]}`}
                >
                  {CATEGORY_LABELS[service.category]}
                </span>
              </div>

              <h3 className="mb-2 font-semibold text-white">{service.title}</h3>
              <p className="mb-4 flex-1 text-sm leading-relaxed text-slate-400">
                {service.description}
              </p>

              <div className="flex items-center justify-between border-t border-slate-800 pt-4">
                <div className="text-sm font-medium text-cyan-400">
                  {service.credits} credits
                  <span className="ml-1 text-slate-500">(~${service.priceUsd})</span>
                </div>
                <div className="text-xs text-slate-500">
                  ⏱ {service.durationMin} phút
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
