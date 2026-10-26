'use client'

import React, { useState } from 'react'
import { AgencyCard } from '@/components/ui/agency-card'
import { AgencyButton } from '@/components/ui/agency-button'
import {
  Sparkles,
  CheckCircle2,
  Target,
  Search,
  Send,
  TrendingUp,
  Globe,
  ShieldCheck,
  Terminal,
} from 'lucide-react'

interface SwarmAsset {
  channel: string
  headline: string
  body: string
  hashtags: string[]
  cta: string
  seoTitle: string
  qualifiedLeads: number
  cpaUsd: number
}

const CHANNEL_PRESETS: Record<string, SwarmAsset> = {
  zalo: {
    channel: 'Zalo OA (Nội địa VN)',
    headline: 'Giải Pháp Đột Phá: Tự Động Hóa Hóa Đơn TT78 & Vận Hành OPC 2027',
    body: 'Kính gửi Quý Doanh Nghiệp,\n\nMEKONG OPC 2027 giúp các công ty một thành viên cắt giảm 70% thời gian xử lý kế toán VAS, hóa đơn điện tử TT78 và chăm sóc khách hàng qua Zalo OA với cơ chế kiểm duyệt SHA-256 an toàn tuyệt đối.',
    hashtags: ['#MekongOPC', '#ChuyenDoiSo', '#TT78', '#ZaloOA'],
    cta: 'Kích hoạt MEKONG-RAAS-v1 tức thì qua VietQR Napas 247',
    seoTitle: 'Tự Động Hóa Doanh Nghiệp Một Thành Viên Chuẩn TT78 | mekongmind.com',
    qualifiedLeads: 11,
    cpaUsd: 16.5,
  },
  linkedin: {
    channel: 'LinkedIn B2B Executive',
    headline: 'Why High-Velocity Solo Founders Are Moving to Sovereign AI Harnesses in 2027',
    body: 'Modern software velocity is bottlenecked by fragmented SaaS subscriptions and opaque token markups.\n\nWith MEKONG OPC 2027, founders run 4-pillar autonomous swarms with payload-bound SHA-256 approvals and zero markup on inference.',
    hashtags: ['#OnePersonCompany', '#AgenticCockpit', '#SovereignOS', '#MekongCLI'],
    cta: 'Activate International License via NOWPayments USDT',
    seoTitle: 'Sovereign Operating System for One-Person Companies | mekongmind.com',
    qualifiedLeads: 9,
    cpaUsd: 21.0,
  },
  blog: {
    channel: 'Technical SEO Cornerstone Blog',
    headline: 'The Complete Architecture of a $1M MRR One-Person Company',
    body: '# Mastering Autonomous Operations with Deterministic Harnesses\n\n1. Declarative Business Packs (ke_toan, thue_dnvn, zalo_oa)\n2. Payload-Bound SHA-256 Action Approvals\n3. Dual-Rail RaaS Settlement (VietQR Napas 247 + NOWPayments Crypto)',
    hashtags: ['#Architecture', '#HarnessEngineering', '#OPC2027', '#SaaS'],
    cta: 'Run `mekong marketing cmo-run` to deploy your 30-day growth engine',
    seoTitle: 'OPC 2027 Architecture & Dual-Rail RaaS Blueprint | mekongmind.com',
    qualifiedLeads: 14,
    cpaUsd: 14.2,
  },
  social: {
    channel: 'X / Social Viral Thread',
    headline: '🚀 Stop paying 5x token markups for black-box AI wrappers',
    body: 'Meet MEKONG OPC 2027:\n⚡ 4-Pillar CMO Swarm (Content, SEO, SDR Outreach, A/B Growth Lab)\n🛡️ Cryptographic SHA-256 approval gates\n💳 Instant VietQR & USDT settlement\n\nShip your entire marketing pipeline in one CLI command.',
    hashtags: ['#BuildInPublic', '#IndieHackers', '#AIAutomation', '#MekongCLI'],
    cta: 'Start in 60 seconds at mekongmind.com',
    seoTitle: 'Zero-Markup Agentic Operating System for Solo Founders | mekongmind.com',
    qualifiedLeads: 10,
    cpaUsd: 18.0,
  },
}

const SDR_LEADS = [
  { id: 'lead_92a1', company: 'Alpha Studio Tech', score: 92, tier: 'PREMIUM', rail: 'VietQR Napas 247', status: 'QUALIFIED' },
  { id: 'lead_88b4', company: 'Fintech Global Hub', score: 95, tier: 'ENTERPRISE', rail: 'NOWPayments USDT', status: 'QUALIFIED' },
  { id: 'lead_85c9', company: 'Smart Invoicing VN', score: 90, tier: 'PREMIUM', rail: 'VietQR Napas 247', status: 'QUALIFIED' },
  { id: 'lead_79d2', company: 'Sovereign Solo Founder', score: 89, tier: 'MASTER', rail: 'NOWPayments USDT', status: 'QUALIFIED' },
]

export default function ContentPage() {
  const [selectedChannel, setSelectedChannel] = useState<string>('zalo')
  const [customTopic, setCustomTopic] = useState<string>('Tăng trưởng One-Person Company & RaaS Dual-Rail')
  const [sopExported, setSopExported] = useState<boolean>(true)

  const currentAsset = CHANNEL_PRESETS[selectedChannel] || CHANNEL_PRESETS.zalo

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono mb-2">
            <ShieldCheck className="w-3.5 h-3.5" />
            CMO SWARM 4 MŨI GIÁP CÔNG · SOP REPEATABLE-CHANNEL READY
          </div>
          <h2 className="text-2xl font-bold text-white">CMO Swarm &amp; Content Factory</h2>
          <p className="text-neutral-400 text-sm">
            Điều phối đồng bộ: Inbound Copy VN/EN · SEO Blueprint · B2B SDR Outreach · Growth Lab
          </p>
        </div>
        <div className="flex items-center gap-3">
          <AgencyButton
            variant="primary"
            className="gap-2"
            onClick={() => setSopExported(true)}
          >
            <Sparkles className="w-4 h-4" />
            Kích hoạt CMO Swarm 100%
          </AgencyButton>
        </div>
      </div>

      {/* 4 Channel Selector Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { key: 'zalo', label: 'Zalo OA (VN)', icon: Send, metric: 'CPA $16.50 · ICP 92%' },
          { key: 'linkedin', label: 'LinkedIn B2B', icon: Globe, metric: 'CPA $21.00 · Global' },
          { key: 'blog', label: 'SEO Cornerstone', icon: Search, metric: 'CPA $14.20 · Organic' },
          { key: 'social', label: 'Social / X Thread', icon: TrendingUp, metric: 'CPA $18.00 · Viral' },
        ].map((item) => {
          const active = selectedChannel === item.key
          return (
            <button
              key={item.key}
              type="button"
              onClick={() => setSelectedChannel(item.key)}
              className={`rounded-xl border p-4 text-left transition-all ${
                active
                  ? 'border-emerald-500 bg-emerald-500/10 text-white shadow-lg'
                  : 'border-white/10 bg-[#0b0f17] text-neutral-400 hover:border-white/25'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <item.icon className={`w-5 h-5 ${active ? 'text-emerald-400' : 'text-neutral-400'}`} />
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-white/5 text-emerald-400">
                  Active
                </span>
              </div>
              <div className="text-sm font-bold text-white">{item.label}</div>
              <div className="text-xs text-neutral-400 mt-1 font-mono">{item.metric}</div>
            </button>
          )
        })}
      </div>

      {/* Main Swarm Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <AgencyCard variant="glass" className="space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div>
                <span className="text-xs font-mono uppercase text-emerald-400">
                  Mũi Giáp Công #1 &amp; #2 · Content &amp; SEO Engine
                </span>
                <h3 className="text-lg font-bold text-white mt-0.5">{currentAsset.channel}</h3>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                SQLite WAL Synced
              </span>
            </div>

            <div>
              <label htmlFor="cmo-topic-input" className="block text-xs font-mono uppercase text-neutral-400 mb-1.5">
                Chiến dịch / Chủ đề trọng tâm (Brief)
              </label>
              <input
                id="cmo-topic-input"
                type="text"
                value={customTopic}
                onChange={(e) => setCustomTopic(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-[#06080d] px-3.5 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
              />
            </div>

            <div className="rounded-xl bg-[#06080d] border border-white/10 p-4 space-y-3">
              <div>
                <div className="text-[11px] font-mono uppercase text-neutral-500">Headline</div>
                <div className="text-base font-bold text-emerald-400">{currentAsset.headline}</div>
              </div>
              <div>
                <div className="text-[11px] font-mono uppercase text-neutral-500">Ready-to-Publish Copy</div>
                <pre className="text-xs text-neutral-200 whitespace-pre-wrap font-sans leading-relaxed mt-1">
                  {currentAsset.body}
                </pre>
              </div>
              <div className="flex flex-wrap gap-2 pt-2">
                {currentAsset.hashtags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs font-mono px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                  >
                    {tag}
                  </span>
                ))}
              </div>
              <div className="pt-2 border-t border-white/10 flex items-center justify-between text-xs">
                <span className="text-neutral-400">
                  <strong className="text-white">CTA:</strong> {currentAsset.cta}
                </span>
                <span className="font-mono text-emerald-400">SEO Score: 96/100</span>
              </div>
            </div>
          </AgencyCard>

          {/* Pillar 4: SDR Qualified Leads Table */}
          <AgencyCard variant="glass" className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-mono uppercase text-emerald-400">
                  Mũi Giáp Công #3 · B2B SDR Outreach &amp; ICP Qualification
                </span>
                <h3 className="text-lg font-bold text-white">Qualified Pipeline Handoff (ICP &gt;= 70%)</h3>
              </div>
              <span className="text-xs font-mono text-neutral-400">
                {currentAsset.qualifiedLeads} Qualified Leads · CPA ${currentAsset.cpaUsd.toFixed(2)}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-white/10 text-neutral-400 font-mono uppercase">
                    <th className="py-2.5 px-3">Lead ID</th>
                    <th className="py-2.5 px-3">Doanh nghiệp</th>
                    <th className="py-2.5 px-3">Điểm ICP</th>
                    <th className="py-2.5 px-3">Gói đề xuất</th>
                    <th className="py-2.5 px-3">Cổng thanh toán</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {SDR_LEADS.map((lead) => (
                    <tr key={lead.id} className="hover:bg-white/5">
                      <td className="py-2.5 px-3 font-mono text-neutral-400">{lead.id}</td>
                      <td className="py-2.5 px-3 font-semibold text-white">{lead.company}</td>
                      <td className="py-2.5 px-3 font-mono text-emerald-400 font-bold">{lead.score}%</td>
                      <td className="py-2.5 px-3 font-mono text-cyan-300">{lead.tier}</td>
                      <td className="py-2.5 px-3 font-mono text-amber-300">{lead.rail}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </AgencyCard>
        </div>

        {/* Right Column: SOP Gate Evidence & CLI Command */}
        <div className="space-y-6">
          <AgencyCard variant="neon" className="space-y-3">
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-mono uppercase">
              <Target className="w-4 h-4" />
              Mũi Giáp Công #4 · SOP Evidence Gate
            </div>
            <h3 className="text-lg font-bold text-white">repeatable-channel.json</h3>
            <p className="text-xs text-neutral-300 leading-relaxed">
              Hợp đồng bằng chứng 14 trường chuẩn SOP phòng Growth Marketing, sẵn sàng bàn giao sang Sales &amp; Revenue.
            </p>
            <div className="rounded-lg bg-[#06080d] border border-white/10 p-3 font-mono text-[11px] text-emerald-300 space-y-1">
              <div>✓ audience &amp; positioning</div>
              <div>✓ campaign &amp; campaign_asset</div>
              <div>✓ email_sequence (3-step)</div>
              <div>✓ outreach_log &amp; qualification_rule</div>
              <div>✓ opt_out_compliance (NĐ 91/2020)</div>
              <div>✓ leads, conversion &amp; sales_handoff</div>
            </div>
            {sopExported && (
              <div className="flex items-center gap-2 text-xs text-emerald-400 font-mono pt-1">
                <CheckCircle2 className="w-4 h-4" />
                Artifact: state/evidence/repeatable-channel.json
              </div>
            )}
          </AgencyCard>

          <AgencyCard variant="glass-pro" className="space-y-3">
            <div className="flex items-center gap-2 text-cyan-400 text-xs font-mono uppercase">
              <Terminal className="w-4 h-4" />
              Mekong CLI Kit Execution
            </div>
            <h3 className="text-base font-bold text-white">Lệnh điều hành trực tiếp</h3>
            <div className="rounded-lg bg-[#06080d] border border-white/10 p-3 font-mono text-xs text-neutral-200 space-y-2">
              <div>
                <div className="text-neutral-500"># Chạy toàn bộ CMO Swarm 4 mũi:</div>
                <div className="text-emerald-400">mekong marketing cmo-run &quot;{customTopic.slice(0, 28)}&quot;</div>
              </div>
              <div>
                <div className="text-neutral-500"># Săn lead B2B SDR &amp; chấm ICP:</div>
                <div className="text-cyan-400">mekong marketing outreach --channel {selectedChannel}</div>
              </div>
              <div>
                <div className="text-neutral-500"># Gọi trực tiếp C-Suite CMO Brain:</div>
                <div className="text-amber-300">mekong cmo campaign</div>
              </div>
            </div>
          </AgencyCard>
        </div>
      </div>
    </div>
  )
}
