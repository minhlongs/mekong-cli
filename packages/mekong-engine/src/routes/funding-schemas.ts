import { z } from 'zod'
import type { Bindings } from '../index'
import { handleDb } from '../types/error'

export const createRoundSchema = z.object({
  title: z.string().min(1, 'title is required').max(200, 'title must be ≤200 chars'),
  matching_pool: z.number().int().positive('matching_pool must be positive').max(10_000_000_000, 'matching_pool too large'),
  duration_days: z.number().int().positive('duration_days must be positive').max(365, 'duration_days must be ≤365').optional(),
})
export type CreateRoundInput = z.infer<typeof createRoundSchema>

export const createProjectSchema = z.object({
  round_id: z.string().uuid('round_id must be a valid UUID'),
  name: z.string().min(1, 'name is required').max(200, 'name must be ≤200 chars'),
  description: z.string().max(1000, 'description must be ≤1000 chars').optional(),
  author_id: z.string().uuid('author_id must be a valid UUID').optional(),
})
export type CreateProjectInput = z.infer<typeof createProjectSchema>

export const contributeSchema = z.object({
  project_id: z.string().uuid('project_id must be a valid UUID'),
  stakeholder_id: z.string().uuid('stakeholder_id must be a valid UUID'),
  amount: z.number().int().positive('amount must be positive').max(1_000_000_000, 'amount too large'),
})
export type ContributeInput = z.infer<typeof contributeSchema>

export type FundingRound = {
  id: string
  tenant_id: string
  title: string
  matching_pool: number
  status: 'active' | 'calculating' | 'completed'
  starts_at: string
  ends_at: string
  created_at: string
}

export type FundingProject = {
  id: string
  round_id: string
  tenant_id: string
  name: string
  description: string
  author_id: string | null
  total_contributions: number
  contributor_count: number
  matched_amount: number
  created_at: string
}

export type FundingContribution = {
  id: string
  project_id: string
  stakeholder_id: string
  amount: number
  created_at: string
}

export type QFResult = {
  id: string
  name: string
  direct: number
  qf_score: number
  contributors: number
  matched_amount: number
  total: number
}

/**
 * Ensure funding tables exist - using safe batched statements instead of .exec()
 */
export async function ensureFundingTables(db: Bindings['DB']): Promise<void> {
  if (!db) return

  const checkResult = await db
    .prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='funding_rounds'")
    .first()

  if (checkResult) return

  const batch = [
    db.prepare(`
      CREATE TABLE IF NOT EXISTS funding_rounds (
        id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, title TEXT NOT NULL,
        matching_pool INTEGER NOT NULL DEFAULT 0,
        status TEXT DEFAULT 'active' CHECK (status IN ('active','calculating','completed')),
        starts_at TEXT, ends_at TEXT, created_at TEXT DEFAULT (datetime('now'))
      )
    `),
    db.prepare(`
      CREATE TABLE IF NOT EXISTS funding_projects (
        id TEXT PRIMARY KEY, round_id TEXT NOT NULL, tenant_id TEXT NOT NULL,
        name TEXT NOT NULL, description TEXT, author_id TEXT,
        total_contributions INTEGER DEFAULT 0, contributor_count INTEGER DEFAULT 0,
        matched_amount INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
      )
    `),
    db.prepare(`
      CREATE TABLE IF NOT EXISTS funding_contributions (
        id TEXT PRIMARY KEY, project_id TEXT NOT NULL, stakeholder_id TEXT NOT NULL,
        amount INTEGER NOT NULL, created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(project_id, stakeholder_id)
      )
    `),
  ]

  await db.batch(batch)
}

export async function calculateQuadraticFunding(
  db: NonNullable<Bindings['DB']>,
  projects: FundingProject[],
  matchingPool: number
): Promise<QFResult[]> {
  const results: QFResult[] = []
  let totalQFScore = 0

  for (const project of projects) {
    const contributionsResult = await handleDb(
      async () => {
        const r = await db.prepare(
          'SELECT amount FROM funding_contributions WHERE project_id = ?'
        ).bind(project.id).all()
        return r as unknown as { results?: FundingContribution[] }
      },
      'DATABASE_ERROR',
      `Failed to fetch contributions for project ${project.id}`
    )

    const contributions = contributionsResult.results || []
    const sqrtSum = contributions.reduce((sum: number, c: FundingContribution) => sum + Math.sqrt(c.amount), 0)
    const directSum = contributions.reduce((sum: number, c: FundingContribution) => sum + c.amount, 0)
    const qfScore = Math.pow(sqrtSum, 2) - directSum

    results.push({
      id: project.id,
      name: project.name,
      direct: directSum,
      qf_score: qfScore,
      contributors: contributions.length,
      matched_amount: 0,
      total: 0,
    })
    totalQFScore += Math.max(0, qfScore)
  }

  for (const r of results) {
    r.matched_amount = totalQFScore > 0 ? Math.floor((r.qf_score / totalQFScore) * matchingPool) : 0
    r.total = r.direct + r.matched_amount

    await handleDb(
      () => db.prepare('UPDATE funding_projects SET matched_amount = ? WHERE id = ?').bind(r.matched_amount, r.id).run(),
      'DATABASE_ERROR',
      `Failed to update matched amount for project ${r.id}`
    )
  }

  return results.sort((a: QFResult, b: QFResult) => b.total - a.total)
}
