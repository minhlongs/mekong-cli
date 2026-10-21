/**
 * Mission Outbox & Cloudflare Queue Producer/Consumer (LLM-only pilot, 3 retries, DLQ + one-time refund)
 */

import type { D1Database, MessageBatch, Queue } from '@cloudflare/workers-types'
import type { Bindings } from '../index'
import type { Recipe, RecipeStep } from '../types/recipe'
import { RecipeOrchestrator } from '../core/recipe-orchestrator'
import { getMission, updateMissionStatus } from './missions'
import { refundMissionCreditsOnce } from './credits'
import { isPilotModeEnabled } from './invite-codes'

export interface MissionQueuePayload {
  mission_id: string
  tenant_id: string
  goal: string
  credits_cost: number
  steps?: RecipeStep[]
  enqueued_at: string
}

export interface MissionConsumerOutcome {
  status: 'completed' | 'failed' | 'retrying' | 'not_found'
  idempotentSkip: boolean
  shouldRetry: boolean
  refunded: boolean
}

export async function ensureMissionOutboxTable(db: D1Database): Promise<void> {
  await db
    .exec(`CREATE TABLE IF NOT EXISTS mission_outbox (id TEXT PRIMARY KEY, mission_id TEXT NOT NULL UNIQUE, tenant_id TEXT NOT NULL, payload_json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now')), updated_at TEXT NOT NULL DEFAULT (datetime('now')))`)
    .catch(() => {})
}

export async function enqueueMissionOutbox(
  db: D1Database,
  queue: Queue<MissionQueuePayload> | undefined,
  payload: MissionQueuePayload,
): Promise<{ outboxId: string; status: 'pending' | 'published' }> {
  await ensureMissionOutboxTable(db)
  const outboxId = crypto.randomUUID()
  const now = new Date().toISOString()

  await db
    .prepare('INSERT OR REPLACE INTO mission_outbox (id, mission_id, tenant_id, payload_json, status, attempts, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 0, ?, ?)')
    .bind(outboxId, payload.mission_id, payload.tenant_id, JSON.stringify(payload), 'pending', now, now)
    .run()

  if (queue) {
    try {
      await queue.send(payload)
      await db.prepare("UPDATE mission_outbox SET status = 'published', updated_at = ? WHERE mission_id = ?").bind(new Date().toISOString(), payload.mission_id).run()
      return { outboxId, status: 'published' }
    } catch {
      return { outboxId, status: 'pending' }
    }
  }
  return { outboxId, status: 'pending' }
}

export async function republishPendingOutbox(
  db: D1Database,
  queue: Queue<MissionQueuePayload> | undefined,
  limit = 10,
): Promise<number> {
  if (!queue) return 0
  await ensureMissionOutboxTable(db)
  const { results } = await db
    .prepare("SELECT mission_id, payload_json FROM mission_outbox WHERE status = 'pending' ORDER BY created_at ASC LIMIT ?")
    .bind(limit)
    .all<{ mission_id: string; payload_json: string }>()
  let count = 0
  for (const row of results ?? []) {
    try {
      await queue.send(JSON.parse(row.payload_json) as MissionQueuePayload)
      await db.prepare("UPDATE mission_outbox SET status = 'published', updated_at = ? WHERE mission_id = ?").bind(new Date().toISOString(), row.mission_id).run()
      count++
    } catch { /* retry next sweep */ }
  }
  return count
}

async function markTerminalFailureAndRefund(
  db: D1Database,
  payload: MissionQueuePayload,
  attempts: number,
  resultJson: string,
  errSummary: string,
  reasonPrefix: string,
): Promise<MissionConsumerOutcome> {
  await updateMissionStatus(db, payload.mission_id, 'failed', resultJson)
  await db.prepare("UPDATE mission_outbox SET status = 'dlq', attempts = ?, last_error = ?, updated_at = ? WHERE mission_id = ?").bind(attempts, errSummary, new Date().toISOString(), payload.mission_id).run()
  const refund = await refundMissionCreditsOnce(db, payload.tenant_id, payload.mission_id, payload.credits_cost, `${reasonPrefix} ${payload.mission_id}`)
  return { status: 'failed', idempotentSkip: false, shouldRetry: false, refunded: refund.refunded }
}

export async function processMissionQueueMessage(
  db: D1Database,
  env: Bindings,
  payload: MissionQueuePayload,
  opts: { attempts?: number; maxRetries?: number; isDlq?: boolean } = {},
): Promise<MissionConsumerOutcome> {
  await ensureMissionOutboxTable(db)
  const attempts = opts.attempts ?? 1
  const maxRetries = opts.maxRetries ?? 3
  const isDlq = opts.isDlq ?? false
  const llmOnly = isPilotModeEnabled(env.PILOT_MODE)

  const mission = await getMission(db, payload.mission_id, payload.tenant_id)
  if (!mission) return { status: 'not_found', idempotentSkip: true, shouldRetry: false, refunded: false }

  if (mission.status === 'completed' || mission.status === 'failed') {
    if (mission.status === 'failed') {
      await refundMissionCreditsOnce(db, payload.tenant_id, payload.mission_id, payload.credits_cost, 'refund: terminal failed mission')
    }
    return { status: mission.status, idempotentSkip: true, shouldRetry: false, refunded: false }
  }

  if (isDlq) {
    const dlqJson = JSON.stringify({
      status: 'failed',
      error: 'DEAD_LETTER_QUEUE_EXHAUSTED',
      message: 'Mission exhausted maximum queue delivery retries and moved to DLQ',
    })
    return markTerminalFailureAndRefund(db, payload, attempts, dlqJson, 'DLQ exhausted', 'refund: DLQ mission')
  }

  try {
    await updateMissionStatus(db, payload.mission_id, 'planning')
    const orchestrator = new RecipeOrchestrator({
      ai: env.AI,
      llmApiKey: env.LLM_API_KEY,
      llmBaseUrl: env.LLM_BASE_URL,
      model: env.DEFAULT_LLM_MODEL,
      strictVerification: true,
      llmOnly,
    })

    await updateMissionStatus(db, payload.mission_id, 'executing')
    const orchResult = payload.steps?.length
      ? await orchestrator.runRecipe({ name: payload.goal.slice(0, 50), description: payload.goal, tags: ['pilot'], steps: payload.steps } satisfies Recipe)
      : await orchestrator.runFromGoal(payload.goal)

    await updateMissionStatus(db, payload.mission_id, 'verifying')

    if (orchResult.status === 'success') {
      const now = new Date().toISOString()
      const compRes = await db
        .prepare("UPDATE missions SET status = ?, total_steps = ?, completed_steps = ?, result = ?, completed_at = ? WHERE id = ? AND status NOT IN ('completed', 'failed')")
        .bind('completed', orchResult.total_steps, orchResult.completed_steps, JSON.stringify(orchResult), now, payload.mission_id)
        .run()
      const updated = ((compRes as { meta?: { changes?: number } })?.meta?.changes ?? 1) > 0
      if (!updated) return { status: 'failed', idempotentSkip: true, shouldRetry: false, refunded: false }
      await db
        .prepare("UPDATE mission_outbox SET status = 'processed', attempts = ?, updated_at = ? WHERE mission_id = ?")
        .bind(attempts, now, payload.mission_id)
        .run()
      return { status: 'completed', idempotentSkip: false, shouldRetry: false, refunded: false }
    }

    const rejectedByPolicy = orchResult.errors.some((e) => e.includes('PILOT_STEP_MODE_REJECTED'))
    const errSummary = orchResult.errors.join('; ') || 'Verification failed'
    if (rejectedByPolicy || attempts >= maxRetries) {
      return markTerminalFailureAndRefund(db, payload, attempts, JSON.stringify(orchResult), errSummary, 'refund: failed mission')
    }

    await db
      .prepare('UPDATE mission_outbox SET attempts = ?, last_error = ?, updated_at = ? WHERE mission_id = ?')
      .bind(attempts, errSummary, new Date().toISOString(), payload.mission_id)
      .run()
    return { status: 'retrying', idempotentSkip: false, shouldRetry: true, refunded: false }
  } catch (err) {
    const errMsg = err instanceof Error ? err.message : String(err)
    if (attempts >= maxRetries) {
      return markTerminalFailureAndRefund(db, payload, attempts, JSON.stringify({ status: 'failed', errors: [errMsg] }), errMsg, 'refund: failed mission')
    }

    await db
      .prepare('UPDATE mission_outbox SET attempts = ?, last_error = ?, updated_at = ? WHERE mission_id = ?')
      .bind(attempts, errMsg, new Date().toISOString(), payload.mission_id)
      .run()
    return { status: 'retrying', idempotentSkip: false, shouldRetry: true, refunded: false }
  }
}

export async function handleMissionQueueBatch(batch: MessageBatch<MissionQueuePayload>, env: Bindings): Promise<void> {
  if (!env.DB) return
  const isDlq = batch.queue.includes('dlq')
  for (const msg of batch.messages) {
    const outcome = await processMissionQueueMessage(env.DB, env, msg.body, { attempts: msg.attempts, maxRetries: 3, isDlq })
    if (outcome.shouldRetry) msg.retry()
    else msg.ack()
  }
}
