'use client'

import React, { useEffect, useState } from 'react'
import { AgencyCard } from '@/components/ui/agency-card'
import { DollarSign, ArrowUpRight, CreditCard, Wallet, QrCode } from 'lucide-react'
import { getPricingCatalog, getLicenseStatus, type PricingTierInfo } from '@/lib/agentops-api'

const CANONICAL_TIERS: Record<string, PricingTierInfo> = {
  basic: { usd: 199, vnd: 4975000, mcu: 1500 },
  premium: { usd: 399, vnd: 9975000, mcu: 4000 },
  enterprise: { usd: 799, vnd: 19975000, mcu: 10000 },
  master: { usd: 4999, vnd: 124975000, mcu: 100000 },
}

export default function RevenuePage() {
  const [tiers, setTiers] = useState<Record<string, PricingTierInfo>>(CANONICAL_TIERS)
  const [rails, setRails] = useState<string[]>(['vietqr', 'nowpayments'])
  const [activeTier, setActiveTier] = useState<string>('FREE')
  const [mcuBalance, setMcuBalance] = useState<number>(0)

  useEffect(() => {
    getPricingCatalog().then((catalog) => {
      if (catalog?.tiers) setTiers(catalog.tiers)
      if (catalog?.rails) setRails(catalog.rails)
    })
    const storedKey = typeof window !== 'undefined' ? window.localStorage.getItem('RAAS_LICENSE_KEY') ?? undefined : undefined
    getLicenseStatus(storedKey).then((status) => {
      if (status?.active) {
        setActiveTier(status.tier)
        setMcuBalance(status.mcu_balance)
      }
    })
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Doanh Thu &amp; Bảng Giá Cổng Thanh Toán Dual-Rail (RaaS Gateway)</h2>
          <p className="text-neutral-400">
            Cổng thanh toán thực qua VietQR Napas 247 và NOWPayments USDT (Polar.sh: HTTP 410 Gone).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <AgencyCard variant="neon" className="relative">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-neutral-400 text-sm">Gói Bản Quyền Đang Kích Hoạt</p>
              <h3 className="text-3xl font-bold text-white mt-2">{activeTier}</h3>
            </div>
            <div className="p-2 bg-emerald-500/10 rounded-lg">
              <DollarSign className="w-6 h-6 text-emerald-400" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm text-emerald-400">
            <ArrowUpRight className="w-4 h-4 mr-1" />
            <span>Số dư MCU: {mcuBalance.toLocaleString()} MCU</span>
          </div>
        </AgencyCard>

        <AgencyCard variant="glass-pro">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-neutral-400 text-sm">Kênh Thanh Toán Hoạt Động</p>
              <h3 className="text-2xl font-bold text-white mt-2 uppercase">{rails.join(' + ')}</h3>
            </div>
            <div className="p-2 bg-emerald-500/10 rounded-lg">
              <QrCode className="w-6 h-6 text-emerald-400" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm text-emerald-400">
            <span>Napas 247 VND &amp; USDT IPN tức thời</span>
          </div>
        </AgencyCard>

        <AgencyCard variant="glass-pro">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-neutral-400 text-sm">Trạng Thái Cổng Thanh Toán</p>
              <h3 className="text-xl font-bold text-emerald-400 mt-2">Dual-Rail Active</h3>
            </div>
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <Wallet className="w-6 h-6 text-blue-400" />
            </div>
          </div>
          <div className="mt-4 text-xs text-neutral-400">
            VietQR + NOWPayments: Hoạt động | Polar: HTTP 410 Gone
          </div>
        </AgencyCard>
      </div>

      <AgencyCard variant="glass">
        <h3 className="text-lg font-bold text-white mb-4">Biểu Phí Niêm Yết Chính Thức (COMMERCIAL_TIERS)</h3>
        <div className="space-y-3">
          {Object.entries(tiers).map(([tierKey, info]) => (
            <div
              key={tierKey}
              className="flex items-center justify-between p-3.5 hover:bg-white/5 rounded-xl transition-colors border border-white/5"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-neutral-800 flex items-center justify-center">
                  <CreditCard className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-white font-semibold uppercase">{tierKey}</span>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-white/10 text-emerald-300">
                      {info.mcu.toLocaleString()} MCU
                    </span>
                  </div>
                  <p className="text-xs text-neutral-400 mt-0.5">
                    Dual-Rail: VietQR Napas 247 / NOWPayments USDT
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-emerald-400 font-bold">${info.usd.toLocaleString()}</div>
                <div className="text-xs text-neutral-400">{info.vnd.toLocaleString()} VND</div>
              </div>
            </div>
          ))}
        </div>
      </AgencyCard>
    </div>
  )
}
