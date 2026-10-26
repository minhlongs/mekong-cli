'use client'

import React, { useEffect, useState } from 'react'
import { AgencyCard } from '@/components/ui/agency-card'
import { AgencyButton } from '@/components/ui/agency-button'
import { Key, ShieldCheck, CheckCircle2 } from 'lucide-react'
import { activateLicenseKey, getLicenseStatus, type LicenseStatusResponse } from '@/lib/agentops-api'

const OPEN_CORE_PHASES = [
  {
    phase: 'PHASE_1_SPLIT_AND_HYGIENE',
    title: 'Phase 1: Codebase Split & Secret Hygiene',
    steps: [
      { num: 1, slug: 'git-history-secret-purge' },
      { num: 2, slug: 'oss-vs-ee-directory-split' },
      { num: 3, slug: 'gitignore-quarantine-lock' },
      { num: 4, slug: 'env-example-byok-template' },
      { num: 5, slug: 'mit-license-and-sbom' },
    ],
  },
  {
    phase: 'PHASE_2_PLUGIN_AND_SEAMS',
    title: 'Phase 2: Core Boundary & Plugin Seams',
    steps: [
      { num: 6, slug: 'capability-bus-interfaces' },
      { num: 7, slug: 'byok-local-adapters' },
      { num: 8, slug: 'cloud-bridge-webhooks' },
      { num: 9, slug: 'local-sandbox-runtime' },
      { num: 10, slug: 'versioned-openapi-sdk' },
    ],
  },
  {
    phase: 'PHASE_3_CLOUD_CONTROL_PLANE',
    title: 'Phase 3: Cloud Control Plane & Auth',
    steps: [
      { num: 11, slug: 'jwt-license-gate' },
      { num: '11b', slug: 'signed-raas-license-key' },
      { num: '11c', slug: 'resolve-polar-checkout-path' },
      { num: 12, slug: 'mcu-credit-metering' },
      { num: 13, slug: 'tiered-rate-limiting' },
      { num: 14, slug: 'managed-worker-queues' },
      { num: 15, slug: 'encrypted-key-vault' },
    ],
  },
  {
    phase: 'PHASE_4_ENTERPRISE_MONETIZATION',
    title: 'Phase 4: Enterprise Security & Billing',
    steps: [
      { num: 16, slug: 'multi-tenant-rbac-isolation' },
      { num: 17, slug: 'compliance-audit-ledger' },
      { num: 18, slug: 'always-on-cloud-daemon' },
      { num: 19, slug: 'strategy-recipe-marketplace' },
      { num: 20, slug: 'payment-webhook-activation' },
    ],
  },
  {
    phase: 'PHASE_5_PLG_GROWTH_AND_GOVERNANCE',
    title: 'Phase 5: PLG Growth & CI Governance',
    steps: [
      { num: 21, slug: 'sixty-second-quickstart' },
      { num: 22, slug: 'cli-to-cloud-upsell-prompt' },
      { num: 23, slug: 'ci-leak-and-loc-gate' },
      { num: 24, slug: 'public-benchmark-trust-badge' },
      { num: 25, slug: 'cla-and-trademark-policy' },
    ],
  },
]

export default function SettingsPage() {
  const [licenseKeyInput, setLicenseKeyInput] = useState('')
  const [licenseStatus, setLicenseStatus] = useState<LicenseStatusResponse | null>(null)
  const [feedback, setFeedback] = useState<string>('')
  const [isLoading, setIsLoading] = useState<boolean>(false)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = window.localStorage.getItem('RAAS_LICENSE_KEY')
      if (stored) {
        setLicenseKeyInput(stored)
        getLicenseStatus(stored).then((status) => {
          if (status) setLicenseStatus(status)
        })
      }
    }
  }, [])

  const handleActivate = async () => {
    if (!licenseKeyInput.trim()) {
      setFeedback('Vui lòng nhập RAAS_LICENSE_KEY.')
      return
    }
    setIsLoading(true)
    setFeedback('Đang xác thực chữ ký số HMAC-SHA256...')
    const result = await activateLicenseKey(licenseKeyInput.trim())
    setIsLoading(false)
    if (result && result.active) {
      setLicenseStatus(result)
      setFeedback(`Kích hoạt thành công gói ${result.tier} (Tenant: ${result.tenant_id})!`)
      if (typeof window !== 'undefined') {
        window.localStorage.setItem('RAAS_LICENSE_KEY', licenseKeyInput.trim())
      }
    } else {
      setFeedback('Chữ ký bản quyền không hợp lệ hoặc đã hết hạn.')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Cài Đặt Hệ Thống &amp; Bản Quyền (License &amp; Open-Core)</h2>
          <p className="text-neutral-400">
            Quản lý khóa bản quyền RaaS, định ngạch MCU credits và tiến trình kiến trúc 25 bước.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <AgencyCard variant="glass-pro" className="lg:col-span-1 space-y-4">
          <div className="flex items-center gap-2 text-white font-semibold">
            <Key className="w-5 h-5 text-emerald-400" />
            <span>Kích Hoạt RAAS_LICENSE_KEY</span>
          </div>
          <p className="text-xs text-neutral-400">
            Nhập token HMAC-SHA256 định dạng <code>MEKONG-RAAS-v1.&lt;payload&gt;.&lt;signature&gt;</code> được cấp sau khi thanh toán VietQR / NOWPayments.
          </p>

          <div className="space-y-2">
            <input
              type="text"
              placeholder="MEKONG-RAAS-v1.ey..."
              value={licenseKeyInput}
              onChange={(e) => setLicenseKeyInput(e.target.value)}
              className="w-full bg-neutral-900/60 border border-white/10 rounded-lg px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-emerald-500"
            />
            <AgencyButton
              variant="secondary"
              onClick={handleActivate}
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? 'Đang xác thực...' : 'Kích Hoạt Bản Quyền'}
            </AgencyButton>
          </div>

          {feedback && (
            <div className="text-xs p-3 rounded-lg bg-white/5 border border-white/10 text-neutral-300">
              {feedback}
            </div>
          )}

          {licenseStatus && (
            <div className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 space-y-2 text-xs">
              <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
                <ShieldCheck className="w-4 h-4" />
                <span>Trạng thái: Hoạt động ({licenseStatus.tier})</span>
              </div>
              <div className="text-neutral-300">Tenant: <span className="font-mono text-white">{licenseStatus.tenant_id}</span></div>
              <div className="text-neutral-300">MCU Balance: <span className="font-mono text-emerald-300">{licenseStatus.mcu_balance.toLocaleString()} credits</span></div>
            </div>
          )}
        </AgencyCard>

        <AgencyCard variant="glass-pro" className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white">Tiến Trình Kiến Trúc 25 Bước Open-Core (100.0% READY)</h3>
            <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 font-mono">
              PUBLIC_GITHUB_SAAS_READY
            </span>
          </div>
          <div className="space-y-3 mt-2">
            {OPEN_CORE_PHASES.map((phase) => (
              <div key={phase.phase} className="p-3 rounded-lg border border-white/5 bg-white/5 space-y-2">
                <div className="text-xs font-semibold text-white/90">{phase.title} ({phase.phase})</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {phase.steps.map((st) => (
                    <div key={String(st.num)} className="flex items-center gap-2 text-xs text-neutral-300">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      <span className="font-mono text-neutral-500">#{st.num}</span>
                      <span className="truncate font-mono">{st.slug}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </AgencyCard>
      </div>
    </div>
  )
}
