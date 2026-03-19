import type { D1Database } from '@cloudflare/workers-types'

export interface TerrainMetrics {
  runway_months: number       // Cash runway
  monthly_customers: number   // Active customers
  competition_intensity: number // 0-10 scale
  company_age_months: number  // How long in market
  mrr_usd?: number            // Monthly recurring revenue
}

export interface TerrainResult {
  terrain: string
  terrain_vn: string
  description: string
  recommended_actions: string[]
  score: number
}

// 7 terrains from Cửu Địa (Nine Terrains) adapted for startups
export function classifyTerrain(metrics: TerrainMetrics): TerrainResult {
  const { runway_months, monthly_customers, competition_intensity, company_age_months } = metrics

  // Tử Địa — Death ground: < 2mo runway or zero customers after 12mo
  if (runway_months < 2 || (monthly_customers === 0 && company_age_months > 12)) {
    return {
      terrain: 'tu_dia',
      terrain_vn: 'Tử Địa',
      description: 'Death ground — fight or die. No retreat possible.',
      recommended_actions: [
        'Freeze all non-essential spending immediately',
        'Emergency fundraise or revenue sprint',
        'Escalate all decisions to human founders',
        'Pivot or dissolve within 60 days',
      ],
      score: 1,
    }
  }

  // Vi Địa — Hemmed-in: 2-4mo runway, high competition
  if (runway_months < 4 && competition_intensity > 7) {
    return {
      terrain: 'vi_dia',
      terrain_vn: 'Vi Địa',
      description: 'Hemmed-in — surrounded, must act decisively.',
      recommended_actions: [
        'Focus on one winning customer segment',
        'Cut costs to extend runway to 6 months',
        'Negotiate emergency bridge financing',
      ],
      score: 2,
    }
  }

  // Tranh Địa — Contentious: heavy competition, early stage
  if (competition_intensity > 7 && company_age_months < 24) {
    return {
      terrain: 'tranh_dia',
      terrain_vn: 'Tranh Địa',
      description: 'Contentious ground — high competition, do not fight head-on.',
      recommended_actions: [
        'Find underserved niche within market',
        'Differentiate on service quality over features',
        'Build moat through proprietary data or relationships',
      ],
      score: 3,
    }
  }

  // Khinh Địa — Light: new market, few customers, early
  if (monthly_customers < 10 && company_age_months < 12) {
    return {
      terrain: 'khinh_dia',
      terrain_vn: 'Khinh Địa',
      description: 'Light ground — just entered, do not halt here.',
      recommended_actions: [
        'Move fast, iterate weekly on product',
        'Do not over-optimize — find product-market fit first',
        'Talk to 10 customers this week',
      ],
      score: 4,
    }
  }

  // Giao Địa — Intersecting: moderate growth, multiple stakeholders
  if (monthly_customers >= 10 && monthly_customers < 100 && runway_months >= 6) {
    return {
      terrain: 'giao_dia',
      terrain_vn: 'Giao Địa',
      description: 'Intersecting ground — multiple paths, build alliances.',
      recommended_actions: [
        'Partner with complementary businesses',
        'Build referral and channel programs',
        'Standardize processes for scale',
      ],
      score: 6,
    }
  }

  // Trọng Địa — Heavy: established, strong position
  if (monthly_customers >= 100 && runway_months >= 12) {
    return {
      terrain: 'trong_dia',
      terrain_vn: 'Trọng Địa',
      description: 'Heavy ground — deep in enemy territory, well established.',
      recommended_actions: [
        'Expand into adjacent markets',
        'Invest in team and infrastructure',
        'Plan Series A or profitability path',
      ],
      score: 8,
    }
  }

  // Tán Địa — Dispersive: default stable state
  return {
    terrain: 'tan_dia',
    terrain_vn: 'Tán Địa',
    description: 'Dispersive ground — home territory, consolidate before advancing.',
    recommended_actions: [
      'Build strong foundations before expansion',
      'Focus on retention over acquisition',
      'Document processes and build culture',
    ],
    score: 5,
  }
}

// Auto-gather metrics from D1 and classify
export async function autoClassifyFromDB(db: D1Database, tenantId: string): Promise<TerrainResult & { metrics: TerrainMetrics }> {
  // Runway: net cash from ledger (months = balance / avg monthly burn)
  const ledger = await db
    .prepare(
      `SELECT
        SUM(CASE WHEN entry_type = 'credit' THEN amount ELSE 0 END) -
        SUM(CASE WHEN entry_type = 'debit' THEN amount ELSE 0 END) as net_balance,
        SUM(CASE WHEN entry_type = 'debit' AND created_at >= datetime('now', '-30 days') THEN amount ELSE 0 END) as monthly_burn
       FROM ledger_entries WHERE tenant_id = ?`
    )
    .bind(tenantId)
    .first<{ net_balance: number; monthly_burn: number }>()

  const balance = ledger?.net_balance || 0
  const monthlyBurn = ledger?.monthly_burn || 1
  const runway_months = monthlyBurn > 0 ? Math.floor(balance / monthlyBurn) : 24

  // Customer count from CRM contacts with type 'customer'
  const contacts = await db
    .prepare(
      "SELECT COUNT(*) as count FROM crm_contacts WHERE tenant_id = ? AND lifecycle_stage = 'customer'"
    )
    .bind(tenantId)
    .first<{ count: number }>()
  const monthly_customers = contacts?.count || 0

  // Company age from tenant created_at
  const tenant = await db
    .prepare('SELECT created_at FROM tenants WHERE id = ?')
    .bind(tenantId)
    .first<{ created_at: string }>()
  const createdAt = tenant?.created_at ? new Date(tenant.created_at) : new Date()
  const company_age_months = Math.floor((Date.now() - createdAt.getTime()) / (1000 * 60 * 60 * 24 * 30))

  // Competition intensity from latest ngu_su score (dia = terrain/competition proxy)
  const nguSu = await db
    .prepare('SELECT dia_score FROM ngu_su_scores WHERE tenant_id = ? ORDER BY scored_at DESC LIMIT 1')
    .bind(tenantId)
    .first<{ dia_score: number }>()
  const competition_intensity = nguSu ? (nguSu.dia_score / 5) * 10 : 5

  const metrics: TerrainMetrics = {
    runway_months: Math.max(0, runway_months),
    monthly_customers,
    competition_intensity,
    company_age_months,
  }

  const result = classifyTerrain(metrics)
  return { ...result, metrics }
}
