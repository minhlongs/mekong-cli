import { z } from 'zod'

export const createProfileSchema = z.object({
  stakeholder_id: z.string().uuid('stakeholder_id must be a valid UUID'),
  skills: z.array(z.string()).optional(),
  industries: z.array(z.string()).optional(),
  availability: z.string().optional().default('available'),
  hourly_rate_usd: z.number().positive('hourly_rate_usd must be positive').optional(),
  bio: z.string().optional(),
})

export const createRequestSchema = z.object({
  requester_id: z.string().uuid('requester_id must be a valid UUID'),
  request_type: z.enum(['expert_needed', 'cofounder_needed', 'mentor_needed', 'vc_intro']),
  skills_needed: z.array(z.string()).optional(),
  industry: z.string().optional(),
  description: z.string().optional(),
  budget_usd: z.number().positive('budget_usd must be positive').optional(),
})

export const updateMatchSchema = z.object({
  status: z.enum(['accepted', 'rejected', 'completed']),
})

export type CreateProfileBody = z.infer<typeof createProfileSchema>
export type CreateRequestBody = z.infer<typeof createRequestSchema>
export type UpdateMatchBody = z.infer<typeof updateMatchSchema>

export type CandidateProfileRow = {
  stakeholder_id: string
  skills: string
  industries: string
  reputation_score: number
}

export type ProposedMatch = {
  match_id: string
  stakeholder_id: string
  score: number
  reasons: string[]
}

export function evaluateCandidateProfile(
  profile: CandidateProfileRow,
  skillsNeeded: string[],
  industry?: string
): { totalScore: number; reasons: string[] } | null {
  const profileSkills: string[] = JSON.parse((profile.skills as string) || '[]')
  const profileIndustries: string[] = JSON.parse((profile.industries as string) || '[]')

  let skillScore = 0
  if (skillsNeeded.length > 0 && profileSkills.length > 0) {
    const overlap = skillsNeeded.filter(s =>
      profileSkills.some(ps => ps.toLowerCase() === s.toLowerCase())
    ).length
    skillScore = overlap / skillsNeeded.length
  } else if (skillsNeeded.length === 0) {
    skillScore = 1
  }

  const industryBonus = industry && profileIndustries.some(
    i => i.toLowerCase() === industry.toLowerCase()
  ) ? 0.1 : 0

  const reputationScore = Math.min(((profile.reputation_score as number) || 0) / 1000, 1)

  const totalScore = (skillScore + industryBonus) * 0.6 + reputationScore * 0.4
  if (totalScore < 0.1) return null

  const reasons: string[] = []
  if (skillScore > 0) reasons.push(`skill_overlap:${(skillScore * 100).toFixed(0)}%`)
  if (industryBonus > 0) reasons.push('industry_match')
  if (reputationScore > 0.3) reasons.push(`reputation:${(reputationScore * 100).toFixed(0)}`)

  return { totalScore, reasons }
}
