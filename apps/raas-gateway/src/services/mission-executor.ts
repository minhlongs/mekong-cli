/**
 * Mission Executor — processes queued missions using CF Workers AI
 */

import type { Env } from '../index';
import { LlmRouter } from './llm-router';
import { MissionNotifier } from './mission-notifier';

const MAX_MISSIONS_PER_RUN = 5;

export class MissionExecutor {
  constructor(private env: Env) {}

  /**
   * Process queued missions (called by scheduled handler)
   */
  async processQueue(): Promise<{ processed: number; failed: number }> {
    let processed = 0;
    let failed = 0;

    // Fetch queued missions — higher tier score first, then oldest within same tier
    const queued = await this.env.DB.prepare(
      `SELECT m.id, m.tenant_id, m.goal, m.complexity, m.credits_cost
       FROM missions m
       JOIN tenants t ON m.tenant_id = t.id
       WHERE m.status = 'queued'
       ORDER BY
         CASE t.tier
           WHEN 'enterprise' THEN 100
           WHEN 'master' THEN 80
           WHEN 'agency' THEN 60
           WHEN 'pro' THEN 40
           WHEN 'starter' THEN 20
           ELSE 10
         END DESC,
         m.created_at ASC
       LIMIT ?`
    )
      .bind(MAX_MISSIONS_PER_RUN)
      .all<{ id: string; tenant_id: string; goal: string; complexity: string; credits_cost: number }>();

    for (const mission of queued.results) {
      try {
        await this.executeMission(mission);
        processed++;
      } catch (error) {
        failed++;
        const err = error as Error;
        await this.failMission(mission.id, err.message);
        console.error(`[Executor] Mission ${mission.id} failed:`, err.message);
      }
    }

    return { processed, failed };
  }

  /**
   * Execute a single mission via Workers AI, with retry + auto-refund on double failure
   */
  private async executeMission(mission: {
    id: string; tenant_id: string; goal: string; complexity: string; credits_cost: number;
  }): Promise<void> {
    const now = new Date().toISOString();

    // Update status to executing
    await this.env.DB.prepare(
      "UPDATE missions SET status = 'executing', started_at = ? WHERE id = ?"
    ).bind(now, mission.id).run();

    // Get model preference stored on this mission
    const modelRow = await this.env.DB.prepare('SELECT model FROM missions WHERE id = ?')
      .bind(mission.id).first<{ model: string }>();

    const router = new LlmRouter(this.env.AI);
    const notifier = new MissionNotifier(this.env);

    // Attempt AI call via router (handles internal fallback chain)
    let llmResult: Awaited<ReturnType<LlmRouter['execute']>>;
    try {
      llmResult = await router.execute({
        goal: mission.goal,
        complexity: mission.complexity,
        modelPreference: modelRow?.model || 'auto',
      });
    } catch (_firstError) {
      try {
        // Retry with simplified goal to reduce complexity-related failures
        console.warn(`[Executor] Mission ${mission.id} retrying with simplified goal`);
        llmResult = await router.execute({
          goal: `Simple version: ${mission.goal}`,
          complexity: 'simple',
          modelPreference: 'fast',
        });
        console.warn(`[Executor] Mission ${mission.id} succeeded on retry`);
      } catch (retryError) {
        // Both attempts failed — refund credits and mark failed
        await this.refundCredits(mission.tenant_id, mission.credits_cost, mission.id);
        await this.env.DB.prepare(
          "UPDATE missions SET status = 'failed', error_message = ?, completed_at = datetime('now') WHERE id = ?"
        ).bind(`AI execution failed after retry. ${mission.credits_cost} MCU refunded.`, mission.id).run();
        console.error(`[Executor] Mission ${mission.id} failed after retry, credits refunded:`, (retryError as Error).message);
        return;
      }
    }

    const { result, model: modelUsed, latencyMs } = llmResult;

    // Update mission as completed with result and routing metadata
    const completedAt = new Date().toISOString();
    await this.env.DB.prepare(
      `UPDATE missions SET status = 'completed', completed_at = ?, result = ?,
       metadata = ? WHERE id = ?`
    )
      .bind(
        completedAt,
        result,
        JSON.stringify({ executor: 'workers-ai', model: modelUsed, latencyMs }),
        mission.id
      )
      .run();

    // Notify Telegram user if they have chat_id
    await notifier.notifyTelegram(mission.tenant_id, mission.id, result);

    // Fire webhook callback with retry if configured
    const callbackUrl = await notifier.getCallbackUrl(mission.id);
    if (callbackUrl) {
      const delivered = await notifier.deliverWebhook(callbackUrl, {
        event: 'mission.completed',
        mission_id: mission.id,
        tenant_id: mission.tenant_id,
        status: 'completed',
        result,
        completed_at: completedAt,
      });
      if (delivered) {
        console.log(`[Executor] Webhook delivered to ${callbackUrl} for mission ${mission.id}`);
      } else {
        console.error(`[Executor] Webhook delivery failed after all retries: ${callbackUrl} mission ${mission.id}`);
      }
    }
  }

  /**
   * Refund credits to tenant and record the transaction
   */
  private async refundCredits(tenantId: string, amount: number, missionId: string): Promise<void> {
    await this.env.DB.prepare(
      'UPDATE tenants SET balance = balance + ?, total_spent = total_spent - ? WHERE id = ?'
    ).bind(amount, amount, tenantId).run();

    await this.env.DB.prepare(
      `INSERT INTO credit_transactions (id, tenant_id, amount, type, description, metadata, created_at)
       VALUES (?, ?, ?, 'refund', ?, '{}', datetime('now'))`
    ).bind(crypto.randomUUID(), tenantId, amount, `Auto-refund: mission ${missionId} failed`).run();
  }

  /**
   * Mark mission as failed
   */
  private async failMission(missionId: string, errorMessage: string): Promise<void> {
    await this.env.DB.prepare(
      "UPDATE missions SET status = 'failed', completed_at = ?, error_message = ? WHERE id = ?"
    )
      .bind(new Date().toISOString(), errorMessage.slice(0, 500), missionId)
      .run();
  }



}
