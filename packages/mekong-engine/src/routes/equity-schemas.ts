import { z } from 'zod'

export const createEntitySchema = z.object({
  name: z.string().min(1, 'name is required').max(200, 'name must be ≤200 chars'),
  entity_type: z.string().optional(),
  total_shares: z.number().int().positive('total_shares must be positive').optional(),
  jurisdiction: z.string().max(100, 'jurisdiction must be ≤100 chars').optional(),
})

export const createGrantSchema = z.object({
  entity_id: z.string().uuid('entity_id must be a valid UUID'),
  stakeholder_id: z.string().uuid('stakeholder_id must be a valid UUID'),
  share_class_id: z.string().uuid('share_class_id must be a valid UUID'),
  shares: z.number().int().positive('shares must be positive'),
  price_per_share: z.number().nonnegative('price_per_share must be non-negative').optional(),
  grant_type: z.string().optional(),
  vesting_months: z.number().int().nonnegative('vesting_months must be non-negative').optional(),
  cliff_months: z.number().int().nonnegative('cliff_months must be non-negative').optional(),
})

export const createSafeSchema = z.object({
  entity_id: z.string().uuid('entity_id must be a valid UUID'),
  investor_stakeholder_id: z.string().uuid('investor_stakeholder_id must be a valid UUID'),
  principal_amount: z.number().positive('principal_amount must be positive'),
  valuation_cap: z.number().positive('valuation_cap must be positive').optional(),
  discount_rate: z.number().min(0).max(1, 'discount_rate must be between 0 and 1').optional(),
})

export const convertSafeSchema = z.object({
  price_per_share: z.number().positive('price_per_share must be positive'),
  share_class_id: z.string().uuid('share_class_id must be a valid UUID'),
})

export type CreateEntityBody = z.infer<typeof createEntitySchema>
export type CreateGrantBody = z.infer<typeof createGrantSchema>
export type CreateSafeBody = z.infer<typeof createSafeSchema>
export type ConvertSafeBody = z.infer<typeof convertSafeSchema>

export type EquityEntity = {
  id: string
  tenant_id: string
  name: string
  entity_type: string
  total_authorized_shares: number
  jurisdiction: string
  created_at: string
}

export type EquityGrant = {
  id: string
  entity_id: string
  stakeholder_id: string
  share_class_id: string
  grant_type: string
  shares: number
  price_per_share: number
  vesting_months: number
  cliff_months: number
  vesting_start_date: string
  effective_date: string
}

export type SafeNote = {
  id: string
  entity_id: string
  investor_stakeholder_id: string
  principal_amount: number
  valuation_cap: number | null
  discount_rate: number
  status: string
  conversion_date: string | null
  converted_shares: number | null
  display_name: string
}

export type CapTableHolder = {
  stakeholder_id: string
  display_name: string
  role: string
  share_class: string
  total_granted: number
  total_cancelled: number
}

export function computeVestingSchedule(grants: EquityGrant[], now: Date = new Date()) {
  return grants.map((g: EquityGrant) => {
    if (!g.vesting_months || g.vesting_months === 0) {
      return { ...g, vested_shares: g.shares, vested_pct: 100 }
    }
    const start = new Date(g.vesting_start_date || g.effective_date)
    const monthsElapsed = Math.max(0, (now.getTime() - start.getTime()) / (30.44 * 24 * 60 * 60 * 1000))
    if (monthsElapsed < (g.cliff_months || 0)) {
      return { ...g, vested_shares: 0, vested_pct: 0 }
    }
    const vestedPct = Math.min(100, (monthsElapsed / g.vesting_months) * 100)
    return {
      ...g,
      vested_shares: Math.floor((g.shares * vestedPct) / 100),
      vested_pct: Math.round(vestedPct),
    }
  })
}
