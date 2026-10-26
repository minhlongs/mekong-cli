'use client'

import React, { useState } from 'react'
import { AgencyCard } from '@/components/ui/agency-card'
import { Globe2, Clock, User, Briefcase, Languages } from 'lucide-react'
import type { SupportedCurrency, SupportedLanguage } from '@/lib/opc-cockpit-data'
import { SERVICE_CATALOG } from '@/lib/opc-cockpit-data'

export interface ClientIntake {
  requestId: string
  clientName: string
  clientContact: string
  projectTitle: string
  estimatedHours: number
  currency: SupportedCurrency
  timezone: string
  language: SupportedLanguage
  services: string[]
  attachments: string[]
  principal: string
}

const CURRENCIES: SupportedCurrency[] = ['USD', 'VND', 'EUR']
const LANGUAGES: SupportedLanguage[] = 'en|vi'.split('|') as SupportedLanguage[]

const TIMEZONES = [
  'UTC',
  'Asia/Ho_Chi_Minh',
  'Asia/Singapore',
  'Asia/Bangkok',
  'Europe/Berlin',
  'America/New_York',
  'America/Los_Angeles',
]

interface ClientIntakeCardProps {
  value: ClientIntake
  onChange: (next: ClientIntake) => void
}

const labelStyle = 'text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-500 mb-1.5 block'
const inputStyle =
  'w-full rounded-xl border border-white/10 bg-[#06080d] px-3.5 py-2.5 text-sm text-white placeholder-neutral-600 focus:border-emerald-500/50 focus:outline-none transition-colors'

export default function ClientIntakeCard({ value, onChange }: ClientIntakeCardProps) {
  const [attachmentDraft, setAttachmentDraft] = useState('')

  const update = <K extends keyof ClientIntake>(key: K, next: ClientIntake[K]) => {
    onChange({ ...value, [key]: next })
  }

  const toggleService = (service: string) => {
    const has = value.services.includes(service)
    onChange({
      ...value,
      services: has ? value.services.filter((s) => s !== service) : [...value.services, service],
    })
  }

  const addAttachment = () => {
    const trimmed = attachmentDraft.trim()
    if (!trimmed || value.attachments.includes(trimmed)) return
    onChange({ ...value, attachments: [...value.attachments, trimmed] })
    setAttachmentDraft('')
  }

  return (
    <AgencyCard variant="glass" className="p-6">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
          <User className="w-4 h-4 text-emerald-400" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white">01 · Client Intake</h3>
          <p className="text-[11px] text-neutral-500">
            Neutral multi-currency (USD / VND / EUR), IANA timezone, bilingual EN / VI.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className={labelStyle}>Principal (Owner)</label>
          <div className="relative">
            <User className="absolute left-3 top-3 w-3.5 h-3.5 text-neutral-600" />
            <input
              className={`${inputStyle} pl-9`}
              value={value.principal}
              onChange={(e) => update('principal', e.target.value)}
              placeholder="Owner name"
            />
          </div>
        </div>

        <div>
          <label className={labelStyle}>Client Name</label>
          <input
            className={inputStyle}
            value={value.clientName}
            onChange={(e) => update('clientName', e.target.value)}
            placeholder="Client legal entity"
          />
        </div>

        <div>
          <label className={labelStyle}>Client Contact (Recipient)</label>
          <input
            className={inputStyle}
            value={value.clientContact}
            onChange={(e) => update('clientContact', e.target.value)}
            placeholder="procurement@client.invalid"
          />
        </div>

        <div>
          <label className={labelStyle}>Project Title</label>
          <input
            className={inputStyle}
            value={value.projectTitle}
            onChange={(e) => update('projectTitle', e.target.value)}
            placeholder="Scope of work"
          />
        </div>

        <div>
          <label className={labelStyle}>Estimated Hours</label>
          <input
            type="number"
            min={1}
            className={inputStyle}
            value={value.estimatedHours}
            onChange={(e) => update('estimatedHours', Math.max(1, Number(e.target.value) || 1))}
          />
        </div>

        <div>
          <label className={labelStyle}>Currency</label>
          <div className="flex gap-2">
            {CURRENCIES.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => update('currency', c)}
                className={`flex-1 rounded-lg border py-2 text-xs font-mono font-bold transition-all ${
                  value.currency === c
                    ? 'border-emerald-500/60 bg-emerald-500/10 text-emerald-300'
                    : 'border-white/10 bg-[#06080d] text-neutral-500 hover:text-white'
                }`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className={labelStyle}>IANA Timezone</label>
          <div className="relative">
            <Clock className="absolute left-3 top-3 w-3.5 h-3.5 text-neutral-600" />
            <select
              className={`${inputStyle} pl-9`}
              value={value.timezone}
              onChange={(e) => update('timezone', e.target.value)}
            >
              {TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>
                  {tz}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className={labelStyle}>Language / Jurisdiction</label>
          <div className="flex gap-2">
            {LANGUAGES.map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => update('language', lang)}
                className={`flex-1 flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs font-bold transition-all ${
                  value.language === lang
                    ? 'border-emerald-500/60 bg-emerald-500/10 text-emerald-300'
                    : 'border-white/10 bg-[#06080d] text-neutral-500 hover:text-white'
                }`}
              >
                <Languages className="w-3 h-3" />
                {lang.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-5">
        <label className={labelStyle}>Requested Services (Priced & Honest Unknown)</label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {Object.entries(SERVICE_CATALOG).map(([serviceKey, svc]) => {
            const isActive = value.services.includes(serviceKey)
            const rate = svc.rates[value.currency]
            return (
              <button
                key={serviceKey}
                type="button"
                onClick={() => toggleService(serviceKey)}
                className={`flex items-center justify-between gap-3 rounded-lg border px-3.5 py-2.5 text-left transition-all ${
                  isActive
                    ? 'border-emerald-500/60 bg-emerald-500/10'
                    : 'border-white/10 bg-[#06080d] hover:border-white/20'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <Briefcase
                    className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-emerald-400' : 'text-neutral-600'}`}
                  />
                  <span className={`text-xs truncate ${isActive ? 'text-white font-medium' : 'text-neutral-400'}`}>
                    {value.language === 'vi' ? svc.labelVi : svc.labelEn}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-neutral-500 shrink-0">
                  {rate === null
                    ? 'UNKNOWN'
                    : rate.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      <div className="mt-5">
        <label className={labelStyle}>Attachments</label>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Globe2 className="absolute left-3 top-3 w-3.5 h-3.5 text-neutral-600" />
            <input
              className={`${inputStyle} pl-9`}
              value={attachmentDraft}
              onChange={(e) => setAttachmentDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  addAttachment()
                }
              }}
              placeholder="rfp_architecture_v1.pdf"
            />
          </div>
          <button
            type="button"
            onClick={addAttachment}
            className="rounded-lg border border-white/10 bg-[#06080d] px-4 text-xs font-bold text-neutral-400 hover:text-white hover:border-white/30 transition-colors"
          >
            Add
          </button>
        </div>
        {value.attachments.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {value.attachments.map((a) => (
              <span
                key={a}
                className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-mono text-neutral-300"
              >
                {a}
                <button
                  type="button"
                  aria-label={`Remove ${a}`}
                  onClick={() => onChange({ ...value, attachments: value.attachments.filter((x) => x !== a) })}
                  className="text-neutral-500 hover:text-red-400"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>
    </AgencyCard>
  )
}
