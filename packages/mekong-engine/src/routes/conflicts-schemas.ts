import { z } from 'zod'

export const validTypes = ['resource', 'equity', 'decision', 'conduct', 'constitutional'] as const
export const validSeverities = ['low', 'medium', 'high', 'critical'] as const

export const createConflictSchema = z.object({
  reporter_id: z.string().uuid('reporter_id must be a valid UUID'),
  against_id: z.string().uuid('against_id must be a valid UUID').optional(),
  conflict_type: z.enum([...validTypes] as [string, ...string[]]),
  description: z.string().min(1, 'description is required').max(2000, 'description must be ≤2000 chars'),
  severity: z.enum([...validSeverities] as [string, ...string[]]).optional().default('medium'),
})

export const escalateConflictSchema = z.object({
  reason: z.string().min(1, 'reason is required').max(1000, 'reason must be ≤1000 chars'),
  escalated_by: z.string().uuid('escalated_by must be a valid UUID').optional(),
})

export const resolveConflictSchema = z.object({
  resolution_notes: z.string().max(2000, 'resolution_notes must be ≤2000 chars').optional(),
  dismissed: z.boolean().optional().default(false),
})

export type CreateConflictBody = z.infer<typeof createConflictSchema>
export type EscalateConflictBody = z.infer<typeof escalateConflictSchema>
export type ResolveConflictBody = z.infer<typeof resolveConflictSchema>

// 5-level resolution protocol with SLA
export const RESOLUTION_LEVELS: Record<number, { name: string; sla: string; status: string }> = {
  1: { name: 'auto_resolve', sla: '1h', status: 'auto_resolved' },
  2: { name: 'agent_negotiation', sla: '4h', status: 'negotiating' },
  3: { name: 'governance_review', sla: '24h', status: 'under_review' },
  4: { name: 'human_arbitration', sla: '72h', status: 'arbitration' },
  5: { name: 'constitutional_review', sla: '14d', status: 'constitutional_review' },
}
