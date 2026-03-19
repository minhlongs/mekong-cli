import { z } from 'zod'

// Mirrors Python: src/raas/tenant.py
export const TenantSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  api_key_hash: z.string(),
  tier: z.enum(['free', 'pro', 'enterprise']).default('free'),
  created_at: z.string(),
})

// Mirrors Python: src/raas/credits.py
export const CreditEntrySchema = z.object({
  id: z.number().int(),
  tenant_id: z.string().uuid(),
  amount: z.number().int(),
  reason: z.string().default(''),
  created_at: z.string(),
})

// Mirrors Python: src/raas/missions.py
export const MissionStatusSchema = z.enum([
  'pending',
  'planning',
  'executing',
  'verifying',
  'completed',
  'failed',
])

export const MissionSchema = z.object({
  id: z.string().uuid(),
  tenant_id: z.string().uuid(),
  goal: z.string().min(1),
  status: MissionStatusSchema.default('pending'),
  credits_used: z.number().int().default(0),
  total_steps: z.number().int().default(0),
  completed_steps: z.number().int().default(0),
  result: z.string().nullable().optional(),
  created_at: z.string(),
  completed_at: z.string().nullable().optional(),
})

// Credit tiers from README
export const CREDIT_TIERS = {
  simple: 1,
  standard: 3,
  complex: 5,
} as const

// BYOK — tenant LLM settings
export const LLMProviderSchema = z.enum(['openai', 'google', 'anthropic', 'custom', 'workers-ai'])

export const TenantSettingsSchema = z.object({
  tenant_id: z.string().uuid(),
  llm_provider: LLMProviderSchema.default('workers-ai'),
  llm_api_key_encrypted: z.string().nullable().optional(),
  llm_base_url: z.string().nullable().optional(),
  llm_model: z.string().nullable().optional(),
  updated_at: z.string(),
})

export type Tenant = z.infer<typeof TenantSchema>
export type CreditEntry = z.infer<typeof CreditEntrySchema>
export type MissionStatus = z.infer<typeof MissionStatusSchema>
export type Mission = z.infer<typeof MissionSchema>
export type LLMProvider = z.infer<typeof LLMProviderSchema>
export type TenantSettings = z.infer<typeof TenantSettingsSchema>

// ═══════════════════════════════════════════════════════════════
// BINH PHÁP VC STUDIO — Governance Types
// ═══════════════════════════════════════════════════════════════

export const StakeholderRoleSchema = z.enum([
  'owner', 'admin', 'operator', 'vc_partner', 'founder',
  'expert', 'developer', 'customer', 'community',
])

export const ProposalTypeSchema = z.enum([
  'feature', 'strategic', 'constitutional', 'treasury', 'equity',
])

export const ProposalStatusSchema = z.enum([
  'draft', 'discussion', 'voting', 'approved', 'rejected', 'implemented',
])

export const VotingMechanismSchema = z.enum([
  'quadratic', 'simple_majority', 'supermajority',
])

export const ReputationDimensionSchema = z.enum([
  'code', 'mentorship', 'governance', 'expertise', 'community', 'general',
])

export const TerrainSchema = z.enum([
  'tan_dia', 'khinh_dia', 'tranh_dia', 'giao_dia',
  'trung_dia', 'vi_dia', 'tu_dia', 'unknown',
])

export const StakeholderSchema = z.object({
  id: z.string(),
  tenant_id: z.string(),
  display_name: z.string(),
  email: z.string().nullable().optional(),
  role: StakeholderRoleSchema,
  governance_level: z.number().int().min(1).max(6).default(6),
  voice_credits_monthly: z.number().int().default(10),
  reputation_score: z.number().int().default(0),
  created_at: z.string(),
})

export const ProposalSchema = z.object({
  id: z.string(),
  tenant_id: z.string(),
  author_id: z.string(),
  title: z.string(),
  body: z.string(),
  proposal_type: ProposalTypeSchema,
  voting_mechanism: VotingMechanismSchema,
  status: ProposalStatusSchema,
  quorum_pct: z.number().default(0.10),
  voice_credits_pool: z.number().int().default(0),
  voting_starts_at: z.string().nullable().optional(),
  voting_ends_at: z.string().nullable().optional(),
  created_at: z.string(),
})

export const NguSuScoreSchema = z.object({
  id: z.string(),
  tenant_id: z.string(),
  entity_name: z.string(),
  dao_score: z.number().min(0).max(5),
  thien_score: z.number().min(0).max(5),
  dia_score: z.number().min(0).max(5),
  tuong_score: z.number().min(0).max(5),
  phap_score: z.number().min(0).max(5),
  overall_score: z.number().optional(),
  terrain: TerrainSchema.default('unknown'),
  scored_at: z.string(),
})

// Voice credits for QV: governance_level → monthly credits
export const GOVERNANCE_VOICE_CREDITS: Record<string, number> = {
  owner: 10,      // ít nhất (servant)
  admin: 15,
  operator: 20,
  vc_partner: 30,
  founder: 40,
  expert: 50,
  developer: 60,
  customer: 80,
  community: 100,  // nhiều nhất (tam giác ngược)
}

export type Stakeholder = z.infer<typeof StakeholderSchema>
export type Proposal = z.infer<typeof ProposalSchema>
export type NguSuScore = z.infer<typeof NguSuScoreSchema>
export type StakeholderRole = z.infer<typeof StakeholderRoleSchema>
export type ProposalType = z.infer<typeof ProposalTypeSchema>
export type ReputationDimension = z.infer<typeof ReputationDimensionSchema>
export type Terrain = z.infer<typeof TerrainSchema>
