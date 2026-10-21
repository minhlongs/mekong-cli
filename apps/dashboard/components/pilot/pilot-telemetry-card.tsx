'use client'

import React, { useState } from 'react'
import { CheckCircle2, Clock, ShieldCheck, Star, Users } from 'lucide-react'
import { AgencyCard } from '@/components/ui/agency-card'
import { SyntheticMetricBadge } from '@/components/ui/synthetic-data-banner'

interface PartnerRow {
  label: string
  missionsCompleted: number
  weeklyTarget: number
  feedbackSlaMet: boolean
  rating: number
}

const INITIAL_PARTNERS: PartnerRow[] = [
  { label: 'Partner #1 (Saigon Tax Advisory — Synthetic)', missionsCompleted: 6, weeklyTarget: 5, feedbackSlaMet: true, rating: 5 },
  { label: 'Partner #2 (Delta Logistics — Synthetic)', missionsCompleted: 5, weeklyTarget: 5, feedbackSlaMet: true, rating: 5 },
  { label: 'Partner #3 (Mekong Retail OA — Synthetic)', missionsCompleted: 5, weeklyTarget: 5, feedbackSlaMet: true, rating: 4 },
  { label: 'Partner #4 (CanTho Agro Export — Synthetic)', missionsCompleted: 5, weeklyTarget: 5, feedbackSlaMet: true, rating: 5 },
  { label: 'Partner #5 (Studio Sophia Demo — Synthetic)', missionsCompleted: 5, weeklyTarget: 5, feedbackSlaMet: true, rating: 5 },
]

export function PilotTelemetryCard() {
  const [selectedRating, setSelectedRating] = useState<number>(5)
  const [feedbackComment, setFeedbackComment] = useState<string>('')
  const [submittedNotice, setSubmittedNotice] = useState<string | null>(null)

  const handlePreviewFeedback = (e: React.FormEvent) => {
    e.preventDefault()
    setSubmittedNotice(
      `Recorded ${selectedRating}/5 synthetic pilot rating (within 48h SLA window)${feedbackComment.trim() ? `: "${feedbackComment.trim()}"` : '.'}`,
    )
    setFeedbackComment('')
  }

  return (
    <AgencyCard variant="glass-pro" className="p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-bold text-white">
            Invited Pilot Cohort Telemetry (5 Partners · 5 Missions/Wk · 48h Feedback SLA)
          </h3>
        </div>
        <SyntheticMetricBadge label="Synthetic Cohort" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="rounded-lg bg-white/5 border border-white/10 p-3">
          <div className="flex items-center gap-1.5 text-xs text-neutral-400">
            <Users className="w-3.5 h-3.5 text-blue-400" />
            <span>Invited Partners</span>
          </div>
          <p className="text-lg font-bold text-white mt-1">5 / 5 Active</p>
          <p className="text-[11px] text-emerald-400">100% meeting 5 missions/wk target</p>
        </div>

        <div className="rounded-lg bg-white/5 border border-white/10 p-3">
          <div className="flex items-center gap-1.5 text-xs text-neutral-400">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>LLM-Only Queue Missions</span>
          </div>
          <p className="text-lg font-bold text-white mt-1">26 / 27 Completed</p>
          <p className="text-[11px] text-neutral-400">96.3% completion · 1 auto-refunded</p>
        </div>

        <div className="rounded-lg bg-white/5 border border-white/10 p-3">
          <div className="flex items-center gap-1.5 text-xs text-neutral-400">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>48-Hour Feedback SLA</span>
          </div>
          <p className="text-lg font-bold text-white mt-1">100% Within 48h</p>
          <p className="text-[11px] text-amber-300">Avg partner rating: 4.8 / 5.0</p>
        </div>
      </div>

      <div className="space-y-1.5">
        {INITIAL_PARTNERS.map((partner) => (
          <div
            key={partner.label}
            className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-white/[0.03] px-3 py-2 text-xs"
          >
            <span className="text-neutral-200 font-medium">{partner.label}</span>
            <div className="flex items-center gap-3">
              <span className="text-emerald-400">
                {partner.missionsCompleted}/{partner.weeklyTarget} missions/wk
              </span>
              <span className="text-amber-300">{partner.rating}.0 ★</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300">
                {partner.feedbackSlaMet ? '< 48h SLA' : 'Pending'}
              </span>
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handlePreviewFeedback} className="pt-2 border-t border-white/10 space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-xs text-neutral-300 font-medium">
            Partner 48h Mission Feedback Preview (Synthetic Demo)
          </span>
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => setSelectedRating(star)}
                className={`p-1 rounded transition-colors ${
                  star <= selectedRating ? 'text-amber-400' : 'text-neutral-600'
                }`}
                aria-label={`Rate ${star} stars`}
              >
                <Star className="w-3.5 h-3.5 fill-current" />
              </button>
            ))}
          </div>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={feedbackComment}
            onChange={(e) => setFeedbackComment(e.target.value)}
            placeholder="Share synthetic mission feedback (POST /v1/tasks/:id/feedback)..."
            className="flex-1 rounded-md bg-black/30 border border-white/10 px-2.5 py-1.5 text-xs text-white placeholder:text-neutral-500"
          />
          <button
            type="submit"
            className="rounded-md bg-emerald-600 hover:bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-white transition-colors"
          >
            Submit Feedback
          </button>
        </div>
        {submittedNotice && (
          <p className="text-[11px] text-emerald-300">{submittedNotice}</p>
        )}
      </form>
    </AgencyCard>
  )
}
