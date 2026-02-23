const TRANSACTIONS = [
  { id: 1, date: '2026-02-20', product: 'AgencyOS Pro', amount: '$299', status: 'Paid' },
  { id: 2, date: '2026-02-18', product: 'Starter Plan', amount: '$49', status: 'Paid' },
  { id: 3, date: '2026-02-15', product: 'AgencyOS Pro', amount: '$299', status: 'Paid' },
  { id: 4, date: '2026-02-12', product: 'Growth Plan', amount: '$149', status: 'Pending' },
  { id: 5, date: '2026-02-08', product: 'Starter Plan', amount: '$49', status: 'Refunded' },
]

const STATUS_STYLES: Record<string, string> = {
  Paid: 'bg-green-500/10 text-green-400 border border-green-500/20',
  Pending: 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20',
  Refunded: 'bg-red-500/10 text-red-400 border border-red-500/20',
}

const STATS = [
  { label: 'Total Revenue', value: '$12,450' },
  { label: 'MRR', value: '$2,100' },
  { label: 'Active Subscriptions', value: '47' },
]

export default function RevenuePage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Revenue</h1>
        <select
          className="text-sm bg-zinc-900 border border-zinc-800 text-zinc-400 rounded-md px-3 py-1.5 focus:outline-none focus:border-purple-600"
          defaultValue="30d"
        >
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
          <option value="1y">Last year</option>
        </select>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {STATS.map((stat) => (
          <div key={stat.label} className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
            <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">{stat.label}</p>
            <p className="text-2xl font-bold text-white">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Transactions table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-zinc-800">
          <h2 className="text-sm font-medium text-zinc-200">Recent Transactions</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-zinc-500 uppercase tracking-wide border-b border-zinc-800">
              <th className="px-5 py-3 text-left">Date</th>
              <th className="px-5 py-3 text-left">Product</th>
              <th className="px-5 py-3 text-left">Amount</th>
              <th className="px-5 py-3 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {TRANSACTIONS.map((tx) => (
              <tr key={tx.id} className="border-b border-zinc-800/50 last:border-0 hover:bg-zinc-800/30 transition-colors">
                <td className="px-5 py-3 text-zinc-400">{tx.date}</td>
                <td className="px-5 py-3 text-zinc-200">{tx.product}</td>
                <td className="px-5 py-3 text-zinc-200 font-medium">{tx.amount}</td>
                <td className="px-5 py-3">
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[tx.status]}`}>
                    {tx.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
