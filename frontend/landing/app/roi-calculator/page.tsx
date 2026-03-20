'use client'

import { useState } from 'react'

export default function ROICalculator() {
  const [devCost, setDevCost] = useState(150000)
  const [teamSize, setTeamSize] = useState(5)
  const [timeline, setTimeline] = useState(6)
  const [avgSalary, setAvgSalary] = useState(3000)

  const calculateROI = () => {
    // Traditional development cost
    const traditionalCost = devCost + (teamSize * avgSalary * timeline)

    // Mekong CLI cost (estimated 80% reduction)
    const mekongCost = traditionalCost * 0.2

    // Savings
    const savings = traditionalCost - mekongCost
    const savingsPercent = ((savings / traditionalCost) * 100).toFixed(1)

    // Payback period (months)
    const monthlySavings = savings / timeline
    const mekongMonthlyCost = 149 // Pro plan
    const paybackPeriod = (mekongMonthlyCost / monthlySavings).toFixed(1)

    // 3-year NPV (assuming 10% discount rate)
    const threeYearSavings = (savings * 36) / timeline
    const npv = (threeYearSavings / Math.pow(1.1, 3)).toFixed(0)

    return {
      traditionalCost,
      mekongCost,
      savings,
      savingsPercent,
      paybackPeriod,
      npv,
      monthlySavings,
    }
  }

  const roi = calculateROI()

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-900/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <nav className="flex items-center justify-between">
            <a href="/" className="text-xl font-bold text-emerald-400">
              Mekong CLI
            </a>
            <div className="flex gap-6">
              <a href="/pricing" className="text-gray-300 hover:text-white">
                Pricing
              </a>
              <a href="/dashboard" className="text-gray-300 hover:text-white">
                Dashboard
              </a>
            </div>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h1 className="text-5xl font-bold mb-6">
            ROI Calculator
          </h1>
          <p className="text-xl text-gray-400 mb-8">
            See how much you can save with Mekong CLI vs traditional development
          </p>
        </div>
      </section>

      {/* Calculator */}
      <section className="py-12">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Input Form */}
            <div className="bg-gray-800 rounded-2xl p-8 border border-gray-700">
              <h2 className="text-2xl font-bold mb-6">Your Project Details</h2>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Estimated Development Cost ($)
                  </label>
                  <input
                    type="number"
                    value={devCost}
                    onChange={(e) => setDevCost(Number(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Team Size (developers)
                  </label>
                  <input
                    type="number"
                    value={teamSize}
                    onChange={(e) => setTeamSize(Number(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Timeline (months)
                  </label>
                  <input
                    type="number"
                    value={timeline}
                    onChange={(e) => setTimeline(Number(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Avg Monthly Salary per Dev ($)
                  </label>
                  <input
                    type="number"
                    value={avgSalary}
                    onChange={(e) => setAvgSalary(Number(e.target.value))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Results */}
            <div className="bg-gradient-to-br from-emerald-900/50 to-gray-800 rounded-2xl p-8 border border-emerald-700/50">
              <h2 className="text-2xl font-bold mb-6 text-emerald-400">
                Your ROI with Mekong CLI
              </h2>

              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Traditional Cost</span>
                  <span className="text-2xl font-bold">
                    ${roi.traditionalCost.toLocaleString()}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-400">With Mekong CLI</span>
                  <span className="text-2xl font-bold text-emerald-400">
                    ${roi.mekongCost.toLocaleString()}
                  </span>
                </div>

                <div className="border-t border-gray-700 pt-6">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-gray-400">Total Savings</span>
                    <span className="text-3xl font-bold text-emerald-400">
                      ${roi.savings.toLocaleString()}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-800/50 rounded-lg p-4">
                      <div className="text-sm text-gray-400">Savings %</div>
                      <div className="text-2xl font-bold text-emerald-400">
                        {roi.savingsPercent}%
                      </div>
                    </div>
                    <div className="bg-gray-800/50 rounded-lg p-4">
                      <div className="text-sm text-gray-400">Payback Period</div>
                      <div className="text-2xl font-bold text-emerald-400">
                        {roi.paybackPeriod} months
                      </div>
                    </div>
                    <div className="bg-gray-800/50 rounded-lg p-4">
                      <div className="text-sm text-gray-400">3-Year NPV</div>
                      <div className="text-2xl font-bold text-emerald-400">
                        ${Number(roi.npv).toLocaleString()}
                      </div>
                    </div>
                    <div className="bg-gray-800/50 rounded-lg p-4">
                      <div className="text-sm text-gray-400">Monthly Savings</div>
                      <div className="text-2xl font-bold text-emerald-400">
                        ${roi.monthlySavings.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-6">
                  <a
                    href="https://polar.sh/mekong-cli/checkout?product=pro"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full bg-emerald-500 hover:bg-emerald-600 text-white text-center font-semibold py-4 rounded-lg transition-colors"
                  >
                    Start Free Trial - $149/mo
                  </a>
                  <p className="text-center text-sm text-gray-400 mt-3">
                    1,000 MCU credits/month • All 89 super commands
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 bg-gray-800/50">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">
            How We Calculate ROI
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-bold mb-2">Traditional Cost</h3>
              <p className="text-gray-400">
                Development cost + (Team size × Salary × Timeline)
              </p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-4">🚀</div>
              <h3 className="text-xl font-bold mb-2">Mekong CLI Savings</h3>
              <p className="text-gray-400">
                80% reduction in development time through AI automation
              </p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-4">💰</div>
              <h3 className="text-xl font-bold mb-2">Payback Period</h3>
              <p className="text-gray-400">
                Most customers see positive ROI in &lt; 1 month
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-700 py-8">
        <div className="max-w-6xl mx-auto px-6 text-center text-gray-400">
          <p>© 2026 Mekong CLI. MIT License. Open source.</p>
        </div>
      </footer>
    </div>
  )
}
