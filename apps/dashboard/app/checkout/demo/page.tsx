'use client'

import { useEffect, useState } from 'react'
import {
  createDualRailCheckout,
  getCheckoutStatus,
  type DualRailCheckoutResponse,
} from '@/lib/agentops-api'

interface TierPlan {
  id: 'BASIC' | 'PREMIUM' | 'ENTERPRISE' | 'MASTER'
  name: string
  priceUsd: number
  priceVnd: string
  billing: 'monthly' | 'annual'
  description: string
  mcuQuota: string
}

const TIER_PLANS: TierPlan[] = [
  {
    id: 'BASIC',
    name: 'Mekong Cloud BASIC',
    priceUsd: 199,
    priceVnd: '4,975,000 VND',
    billing: 'monthly',
    description: 'Hosted Control Plane + 1,500 MCU/tháng',
    mcuQuota: '1,500 MCU',
  },
  {
    id: 'PREMIUM',
    name: 'Mekong Cloud PREMIUM',
    priceUsd: 399,
    priceVnd: '9,975,000 VND',
    billing: 'monthly',
    description: 'Multi-Agent Swarm + 4,000 MCU/tháng',
    mcuQuota: '4,000 MCU',
  },
  {
    id: 'ENTERPRISE',
    name: 'Mekong Cloud ENTERPRISE',
    priceUsd: 799,
    priceVnd: '19,975,000 VND',
    billing: 'monthly',
    description: 'RBAC Multi-Tenant + 10,000 MCU/tháng',
    mcuQuota: '10,000 MCU',
  },
  {
    id: 'MASTER',
    name: 'Mekong Enterprise MASTER',
    priceUsd: 4999,
    priceVnd: '124,975,000 VND',
    billing: 'annual',
    description: 'White-label Portal + Audit Vault + 100,000 MCU',
    mcuQuota: '100,000 MCU',
  },
]

export default function CheckoutDemoPage() {
  const [selectedTier, setSelectedTier] = useState<TierPlan>(TIER_PLANS[1])
  const [rail, setRail] = useState<'vietqr' | 'nowpayments'>('vietqr')
  const [checkoutSession, setCheckoutSession] = useState<DualRailCheckoutResponse | null>(null)
  const [provisionedKey, setProvisionedKey] = useState<string | null>(null)
  const [statusMessage, setStatusMessage] = useState<string>('Sẵn sàng khởi tạo phiên thanh toán Dual-Rail')
  const [isLoading, setIsLoading] = useState<boolean>(false)

  useEffect(() => {
    if (!checkoutSession?.order_id || provisionedKey) return

    const timer = setInterval(async () => {
      const status = await getCheckoutStatus(checkoutSession.order_id)
      if (status && status.status === 'paid' && status.license_key) {
        setProvisionedKey(status.license_key)
        setStatusMessage(`Đã kích hoạt tự động gói ${status.tier}!`)
        if (typeof window !== 'undefined') {
          window.localStorage.setItem('RAAS_LICENSE_KEY', status.license_key)
        }
      }
    }, 3000)

    return () => clearInterval(timer)
  }, [checkoutSession, provisionedKey])

  const handleStartCheckout = async () => {
    setIsLoading(true)
    setProvisionedKey(null)
    setStatusMessage('Đang tạo mã thanh toán Dual-Rail...')
    const res = await createDualRailCheckout({
      tier: selectedTier.id,
      rail,
      billing_period: selectedTier.billing,
    })
    setIsLoading(false)
    if (res) {
      setCheckoutSession(res)
      setStatusMessage(`Đang chờ thanh toán đơn ${res.order_id} (tự động kiểm tra mỗi 3 giây)...`)
    } else {
      setStatusMessage('Không thể kết nối cổng thanh toán Gateway (/v1/checkout).')
    }
  }

  return (
    <div className="min-h-screen bg-linear-to-b from-slate-900 to-slate-950 p-8">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-white mb-2">
            Thanh Toán Dual-Rail RaaS (VietQR Napas 247 &amp; NOWPayments USDT)
          </h1>
          <p className="text-white/60">
            Cổng thanh toán chuẩn Open-Core 25 Bước — Tự động cấp phát chữ ký HMAC-SHA256 RAAS_LICENSE_KEY
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-white mb-4">1. Chọn Gói Bản Quyền (Canonical Tiers)</h2>
            {TIER_PLANS.map((plan) => (
              <button
                key={plan.id}
                onClick={() => setSelectedTier(plan)}
                className={`w-full p-4 rounded-xl border text-left transition-all ${
                  selectedTier.id === plan.id
                    ? 'border-emerald-500 bg-emerald-500/10'
                    : 'border-white/10 bg-white/5 hover:border-white/20'
                }`}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                      {plan.id} • {plan.mcuQuota}
                    </span>
                    <h3 className="font-semibold text-white mt-1">{plan.name}</h3>
                    <p className="text-white/60 text-sm">{plan.description}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-white">${plan.priceUsd.toLocaleString()}</div>
                    <div className="text-xs text-emerald-400">{plan.priceVnd}</div>
                  </div>
                </div>
              </button>
            ))}
          </div>

          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-white mb-4">2. Chọn Kênh Thanh Toán (Dual-Rail)</h2>
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => setRail('vietqr')}
                className={`p-4 rounded-xl border text-center font-medium transition-all ${
                  rail === 'vietqr'
                    ? 'border-emerald-500 bg-emerald-500/20 text-white'
                    : 'border-white/10 bg-white/5 text-white/60'
                }`}
              >
                VietQR Napas 247 (VND)
              </button>
              <button
                onClick={() => setRail('nowpayments')}
                className={`p-4 rounded-xl border text-center font-medium transition-all ${
                  rail === 'nowpayments'
                    ? 'border-blue-500 bg-blue-500/20 text-white'
                    : 'border-white/10 bg-white/5 text-white/60'
                }`}
              >
                NOWPayments (USDT)
              </button>
            </div>

            <button
              onClick={handleStartCheckout}
              disabled={isLoading}
              className="w-full py-3 px-6 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition-colors"
            >
              {isLoading ? 'Đang khởi tạo...' : `Tạo Đơn Thanh Toán ${selectedTier.id} ($${selectedTier.priceUsd.toLocaleString()})`}
            </button>

            <div className="p-4 rounded-xl border border-white/10 bg-white/5 space-y-3">
              <div className="text-sm text-white/80">{statusMessage}</div>
              {checkoutSession && (
                <div className="space-y-2 text-xs text-white/70 border-t border-white/10 pt-3">
                  <div>Mã đơn (Order ID): <span className="font-mono text-white">{checkoutSession.order_id}</span></div>
                  <div>Kênh (Rail): <span className="font-mono uppercase text-emerald-400">{checkoutSession.rail}</span></div>
                  <div>Liên kết / QR: <span className="font-mono break-all text-blue-300">{checkoutSession.checkout_url}</span></div>
                </div>
              )}
              {provisionedKey && (
                <div className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 space-y-1">
                  <div className="text-xs font-semibold text-emerald-400">
                    RAAS_LICENSE_KEY Đã Cấp Phát Tự Động (HMAC-SHA256):
                  </div>
                  <div className="font-mono text-xs text-white break-all">{provisionedKey}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
