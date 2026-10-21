import type { Hono } from 'hono'
import type { Tenant } from '../types/raas'
import { payloadSizeLimit } from '../raas/payload-limiter'
import { handleAsync, handleDb } from '../types/error'
import {
  type DbResult,
  type GovernanceEnv,
  proposalSchema,
  voteSchema,
} from './governance-schemas'

export function registerProposalAndVoteRoutes(app: Hono<GovernanceEnv>): void {
  // Create proposal
  app.post('/proposals', payloadSizeLimit(), handleAsync(async (c) => {
    const tenant = c.get('tenant') as Tenant

    const parsed = proposalSchema.safeParse(await c.req.json().catch(() => ({})))
    if (!parsed.success) {
      const errors = parsed.error.errors.map(e => ({ field: e.path.join('.'), message: e.message }))
      return c.json({ error: 'Validation failed', code: 'VALIDATION_ERROR', details: errors }, 400)
    }

    // Constitutional proposals need supermajority (75%)
    const proposalType = parsed.data.proposal_type || 'feature'
    const mechanism = proposalType === 'constitutional' ? 'supermajority' : (parsed.data.voting_mechanism || 'quadratic')
    const quorum = proposalType === 'constitutional' ? 0.75 : 0.10

    const now = new Date()
    const votingDays = parsed.data.voting_days || 7
    const votingEnd = new Date(now.getTime() + votingDays * 24 * 60 * 60 * 1000)

    const id = crypto.randomUUID()
    await handleDb(
      () => c.env.DB!.prepare(
        `INSERT INTO proposals (id, tenant_id, author_id, title, body, proposal_type, voting_mechanism, status, quorum_pct, voting_starts_at, voting_ends_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, 'voting', ?, ?, ?)`
      ).bind(id, tenant.id, parsed.data.author_id, parsed.data.title, parsed.data.body, proposalType, mechanism, quorum,
        now.toISOString(), votingEnd.toISOString()).run(),
      'DATABASE_ERROR',
      'Failed to create proposal'
    )

    return c.json({
      id,
      proposal_type: proposalType,
      mechanism,
      quorum,
      voting_ends_at: votingEnd.toISOString(),
      message: 'Proposal created successfully'
    }, 201)
  }))

  // List proposals
  app.get('/proposals', handleAsync(async (c) => {
    const tenant = c.get('tenant') as Tenant
    const status = c.req.query('status')
    const limit = Math.min(Number(c.req.query('limit') ?? 50), 200)

    const query = status
      ? 'SELECT * FROM proposals WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC LIMIT ?'
      : 'SELECT * FROM proposals WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?'
    const params = status ? [tenant.id, status, limit] : [tenant.id, limit]
    const rowsResult = await handleDb(
      async () => {
        const r = await c.env.DB!.prepare(query).bind(...params).all()
        return r as DbResult
      },
      'DATABASE_ERROR',
      'Failed to fetch proposals'
    )

    const proposals = []
    for (const p of rowsResult.results || []) {
      const pTyped = p as { id: string }
      const voteStatsResult = await handleDb(
        async () => {
          const r = await c.env.DB!.prepare(
            `SELECT direction, COUNT(*) as count, SUM(votes_cast) as total_votes
           FROM votes WHERE proposal_id = ? GROUP BY direction`
          ).bind(pTyped.id).all()
          return r as unknown as DbResult
        },
        'DATABASE_ERROR',
        'Failed to fetch vote stats'
      )
      proposals.push({ ...(p as object), vote_stats: voteStatsResult.results || [] })
    }

    return c.json({ proposals })
  }))

  // Cast vote: cost = credits², votes = √credits
  app.post('/vote', payloadSizeLimit(), handleAsync(async (c) => {
    const tenant = c.get('tenant') as Tenant

    const parsed = voteSchema.safeParse(await c.req.json().catch(() => ({})))
    if (!parsed.success) {
      const errors = parsed.error.errors.map(e => ({ field: e.path.join('.'), message: e.message }))
      return c.json({ error: 'Validation failed', code: 'VALIDATION_ERROR', details: errors }, 400)
    }

    const proposal = await handleDb(
      () => c.env.DB!.prepare(
        'SELECT * FROM proposals WHERE id = ? AND tenant_id = ? AND status = ?'
      ).bind(parsed.data.proposal_id, tenant.id, 'voting').first(),
      'DATABASE_ERROR',
      'Failed to fetch proposal'
    )
    if (!proposal) return c.json({ error: 'Proposal not found or not in voting state', code: 'NOT_FOUND' }, 404)

    const proposalWithDeadline = proposal as { voting_ends_at?: string }
    if (proposalWithDeadline.voting_ends_at && new Date(proposalWithDeadline.voting_ends_at) < new Date()) {
      return c.json({ error: 'Voting period has ended', code: 'VOTING_CLOSED' }, 400)
    }

    const stakeholder = await handleDb(
      () => c.env.DB!.prepare(
        'SELECT * FROM stakeholders WHERE id = ? AND tenant_id = ?'
      ).bind(parsed.data.stakeholder_id, tenant.id).first(),
      'DATABASE_ERROR',
      'Failed to fetch stakeholder'
    )
    if (!stakeholder) return c.json({ error: 'Stakeholder not found', code: 'NOT_FOUND' }, 404)

    const creditsSpent = Math.abs(parsed.data.voice_credits)
    const votesCast = Math.sqrt(creditsSpent)
    const direction = parsed.data.direction || 'for'

    const id = crypto.randomUUID()
    try {
      await handleDb(
        () => c.env.DB!.prepare(
          'INSERT INTO votes (id, proposal_id, stakeholder_id, voice_credits_spent, votes_cast, direction) VALUES (?, ?, ?, ?, ?, ?)'
        ).bind(id, parsed.data.proposal_id, parsed.data.stakeholder_id, creditsSpent, votesCast, direction).run(),
        'DATABASE_ERROR',
        'Failed to cast vote'
      )
    } catch (error: unknown) {
      if ((error as Error).message?.includes('UNIQUE')) {
        return c.json({ error: 'Already voted on this proposal', code: 'CONFLICT' }, 409)
      }
      throw error
    }

    await handleDb(
      () => c.env.DB!.prepare(
        'UPDATE proposals SET voice_credits_pool = voice_credits_pool + ? WHERE id = ?'
      ).bind(creditsSpent, parsed.data.proposal_id).run(),
      'DATABASE_ERROR',
      'Failed to update proposal voice credits'
    )

    return c.json({
      vote_id: id,
      credits_spent: creditsSpent,
      votes_cast: votesCast.toFixed(2),
      direction,
      message: `QV: ${creditsSpent} credits → ${votesCast.toFixed(2)} votes`
    }, 201)
  }))
}
