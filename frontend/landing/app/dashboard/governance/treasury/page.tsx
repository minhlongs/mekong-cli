'use client'

import { useState, useEffect } from 'react'

interface TreasuryData {
  balance: number
  currency: string
  total_in: number
  total_out: number
  recent_transactions: { id: string; amount: number; description: string; date: string }[]
}

export default function TreasuryPage() {
  const [treasury, setTreasury] = useState<TreasuryData | null>(null)

  useEffect(() => {
    fetch('/api/v1/governance/treasury')
      .then(r => r.json())
      .then(d => setTreasury(d))
      .catch(() => setTreasury({ balance: 0, currency: 'USD', total_in: 0, total_out: 0, recent_transactions: [] }))
  }, [])

  if (!treasury) return <div className="p-8 text-center">Loading treasury...</div>

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">💰 Community Treasury</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gradient-to-br from-blue-500 to-blue-700 text-white rounded-xl p-6 shadow-lg">
          <h3 className="text-sm font-medium opacity-80">Current Balance</h3>
          <p className="text-4xl font-bold mt-2">${treasury.balance.toLocaleString()}</p>
          <p className="text-sm mt-1 opacity-70">{treasury.currency}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Inflow</h3>
          <p className="text-2xl font-bold mt-2 text-green-600">+${treasury.total_in.toLocaleString()}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Outflow</h3>
          <p className="text-2xl font-bold mt-2 text-red-500">-${treasury.total_out.toLocaleString()}</p>
        </div>
      </div>

      <h2 className="text-xl font-semibold mb-4">Recent Transactions</h2>
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {treasury.recent_transactions.map(t => (
              <tr key={t.id}>
                <td className="px-6 py-4">{t.description}</td>
                <td className={`px-6 py-4 font-medium ${t.amount >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                  {t.amount >= 0 ? '+' : ''}{t.amount.toLocaleString()} {treasury.currency}
                </td>
                <td className="px-6 py-4 text-gray-500">{new Date(t.date).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl text-sm">
        <p className="font-medium mb-1">💡 Treasury Governance</p>
        <p className="text-gray-600 dark:text-gray-400">
          All treasury spending requires governance vote (Layer 2: 75% QV supermajority for large amounts,
          Layer 3: simple majority for operational expenses).
        </p>
      </div>
    </div>
  )
}
