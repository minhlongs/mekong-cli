import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'

export type GovernanceVariables = { tenant: Tenant }
export type GovernanceEnv = { Bindings: Bindings; Variables: GovernanceVariables }

export type DbResult<T = unknown> = { results?: T[] }

export type StakeholderRow = {
  id: string
  tenant_id: string
  display_name: string
  email: string | null
  role: string
  governance_level: number
  voice_credits_monthly: number
  reputation_score: number
  created_at: string
  updated_at: string
}

export const GOVERNANCE_ROLE_LEVELS: Record<string, number> = {
  owner: 1,
  admin: 2,
  operator: 3,
  vc_partner: 4,
  founder: 5,
  expert: 5,
  developer: 6,
  customer: 6,
  community: 6,
}

export const stakeholderSchema = z.object({
  display_name: z.string().min(1, 'Display name is required'),
  email: z.string().email().optional().or(z.literal('')),
  role: z.enum([
    'owner', 'admin', 'operator', 'vc_partner',
    'founder', 'expert', 'developer', 'customer', 'community'
  ]).optional(),
})

export const proposalSchema = z.object({
  author_id: z.string().uuid('Invalid author_id format'),
  title: z.string().min(1, 'Title is required'),
  body: z.string().min(1, 'Body is required'),
  proposal_type: z.enum(['feature', 'strategic', 'constitutional', 'treasury', 'equity']).optional(),
  voting_mechanism: z.enum(['quadratic', 'simple_majority', 'supermajority']).optional(),
  voting_days: z.number().int().positive().max(30).optional(),
})

export const voteSchema = z.object({
  proposal_id: z.string().uuid('Invalid proposal_id format'),
  stakeholder_id: z.string().uuid('Invalid stakeholder_id format'),
  voice_credits: z.number().int().positive('Voice credits must be positive'),
  direction: z.enum(['for', 'against', 'abstain']).optional(),
})

export const reputationSchema = z.object({
  stakeholder_id: z.string().uuid('Invalid stakeholder_id format'),
  dimension: z.enum(['code', 'mentorship', 'governance', 'expertise', 'community', 'general']).optional(),
  points: z.number().int().min(-100).max(100),
  reason: z.string().min(1, 'Reason is required'),
})

export const nguSuSchema = z.object({
  entity_name: z.string().min(1, 'Entity name is required'),
  dao: z.number().min(0).max(5),
  thien: z.number().min(0).max(5),
  dia: z.number().min(0).max(5),
  tuong: z.number().min(0).max(5),
  phap: z.number().min(0).max(5),
  terrain: z.string().optional(),
  notes: z.string().optional(),
})

export function classifyNguSuTerrain(overall: number, requestedTerrain?: string): string {
  const terrain = requestedTerrain || 'unknown'
  if (terrain !== 'unknown') return terrain
  if (overall < 1.5) return 'tu_dia'
  if (overall < 2.5) return 'vi_dia'
  if (overall < 3.5) return 'tranh_dia'
  return 'giao_dia'
}
