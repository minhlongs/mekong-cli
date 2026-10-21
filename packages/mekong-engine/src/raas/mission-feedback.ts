import type { D1Database } from '@cloudflare/workers-types'
import { getMission } from './missions'

export interface MissionFeedbackRecord {
  mission_id: string
  tenant_id: string
  rating: number
  comment: string | null
  within_48h: boolean
  submitted_at: string
}

export interface PilotPartnerKpi {
  tenant_id: string
  missions_total: number
  missions_completed: number
  missions_failed: number
  feedback_submitted: number
  meets_weekly_target: boolean
}

export interface PilotKpiSummary {
  targets: {
    max_partners: number
    missions_per_partner_per_week: number
    feedback_sla_hours: number
  }
  totals: {
    redeemed_partners: number
    missions_submitted: number
    missions_completed: number
    missions_failed: number
    feedback_count: number
    feedback_within_48h_count: number
    feedback_within_48h_rate: number
    average_rating: number | null
  }
  partners: PilotPartnerKpi[]
}

const FORTY_EIGHT_HOURS_MS = 48 * 60 * 60 * 1000
const WEEKLY_MISSION_TARGET = 5

export async function ensureMissionFeedbackTable(db: D1Database): Promise<void> {
  await db
    .exec(
      `CREATE TABLE IF NOT EXISTS mission_feedback (mission_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, rating INTEGER NOT NULL, comment TEXT, within_48h INTEGER NOT NULL DEFAULT 1, submitted_at TEXT NOT NULL DEFAULT (datetime('now')))`,
    )
    .catch(() => {})
}

export async function submitMissionFeedback(
  db: D1Database,
  tenantId: string,
  missionId: string,
  rating: number,
  comment?: string,
): Promise<MissionFeedbackRecord | null> {
  await ensureMissionFeedbackTable(db)
  const mission = await getMission(db, missionId, tenantId)
  if (!mission) return null

  const now = new Date()
  const nowIso = now.toISOString()
  const anchorTime = new Date(mission.completed_at ?? mission.created_at).getTime()
  const elapsedMs = Number.isFinite(anchorTime) ? Math.max(0, now.getTime() - anchorTime) : 0
  const within48h = elapsedMs <= FORTY_EIGHT_HOURS_MS ? 1 : 0
  const normalizedComment = comment?.trim() ? comment.trim().slice(0, 1000) : null

  await db
    .prepare(
      'INSERT OR REPLACE INTO mission_feedback (mission_id, tenant_id, rating, comment, within_48h, submitted_at) VALUES (?, ?, ?, ?, ?, ?)',
    )
    .bind(missionId, tenantId, rating, normalizedComment, within48h, nowIso)
    .run()

  return {
    mission_id: missionId,
    tenant_id: tenantId,
    rating,
    comment: normalizedComment,
    within_48h: within48h === 1,
    submitted_at: nowIso,
  }
}

export async function getPilotKpiSummary(
  db: D1Database,
  maxPartners = 5,
): Promise<PilotKpiSummary> {
  await ensureMissionFeedbackTable(db)
  const missionsRes = await db
    .prepare('SELECT id, tenant_id, status FROM missions')
    .all<{ id: string; tenant_id: string; status: string }>()
  const feedbackRes = await db
    .prepare('SELECT mission_id, tenant_id, rating, within_48h FROM mission_feedback')
    .all<{ mission_id: string; tenant_id: string; rating: number; within_48h: number }>()
  const invitesRes = await db
    .prepare("SELECT redeemed_by_tenant_id FROM pilot_invites WHERE status = 'redeemed'")
    .all<{ redeemed_by_tenant_id: string | null }>()
    .catch(() => ({ results: [] as { redeemed_by_tenant_id: string | null }[] }))

  const missions = missionsRes.results ?? []
  const feedbacks = feedbackRes.results ?? []
  const partnerIds = new Set<string>()
  for (const inv of invitesRes.results ?? []) {
    if (inv.redeemed_by_tenant_id) partnerIds.add(inv.redeemed_by_tenant_id)
  }
  for (const m of missions) partnerIds.add(m.tenant_id)

  const partners: PilotPartnerKpi[] = Array.from(partnerIds).map((tenantId) => {
    const tMissions = missions.filter((m) => m.tenant_id === tenantId)
    const tFeedback = feedbacks.filter((f) => f.tenant_id === tenantId)
    return {
      tenant_id: tenantId,
      missions_total: tMissions.length,
      missions_completed: tMissions.filter((m) => m.status === 'completed').length,
      missions_failed: tMissions.filter((m) => m.status === 'failed').length,
      feedback_submitted: tFeedback.length,
      meets_weekly_target: tMissions.length >= WEEKLY_MISSION_TARGET,
    }
  })

  const within48hCount = feedbacks.filter((f) => Number(f.within_48h) === 1).length
  const avgRating = feedbacks.length
    ? Number((feedbacks.reduce((acc, f) => acc + Number(f.rating), 0) / feedbacks.length).toFixed(2))
    : null

  return {
    targets: {
      max_partners: maxPartners,
      missions_per_partner_per_week: WEEKLY_MISSION_TARGET,
      feedback_sla_hours: 48,
    },
    totals: {
      redeemed_partners: partnerIds.size,
      missions_submitted: missions.length,
      missions_completed: missions.filter((m) => m.status === 'completed').length,
      missions_failed: missions.filter((m) => m.status === 'failed').length,
      feedback_count: feedbacks.length,
      feedback_within_48h_count: within48hCount,
      feedback_within_48h_rate: feedbacks.length ? Number((within48hCount / feedbacks.length).toFixed(2)) : 1,
      average_rating: avgRating,
    },
    partners,
  }
}
