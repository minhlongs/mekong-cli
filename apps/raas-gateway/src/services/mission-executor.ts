/**
 * Mission Executor — processes queued missions using CF Workers AI
 */

import type { Env } from '../index';

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

    // Get model preference
    const modelRow = await this.env.DB.prepare('SELECT model FROM missions WHERE id = ?')
      .bind(mission.id).first<{ model: string }>();
    const modelId = this.resolveModel(modelRow?.model || 'auto');

    // Attempt AI call, retry once with simplified prompt on failure
    let result: string;
    try {
      result = await this.callAI(mission.goal, mission.complexity, modelId);
    } catch (_firstError) {
      try {
        // Retry with simplified goal to reduce complexity-related failures
        result = await this.callAI(`Simple version: ${mission.goal}`, 'simple', modelId);
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

    // Update mission as completed with result
    const completedAt = new Date().toISOString();
    await this.env.DB.prepare(
      `UPDATE missions SET status = 'completed', completed_at = ?, result = ?,
       metadata = ? WHERE id = ?`
    )
      .bind(
        completedAt,
        result,
        JSON.stringify({ executor: 'workers-ai', model: modelId }),
        mission.id
      )
      .run();

    // Notify Telegram user if they have chat_id
    await this.notifyTelegram(mission.tenant_id, mission.id, result);

    // Fire webhook callback with retry if configured
    const callbackUrl = await this.getCallbackUrl(mission.id);
    if (callbackUrl) {
      const delivered = await this.deliverWebhook(callbackUrl, {
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
   * Call Workers AI and return the response text (throws on failure)
   */
  private async callAI(goal: string, complexity: string, modelId: string): Promise<string> {
    const systemPrompt = this.buildSystemPrompt(complexity);
    const aiResponse = await this.env.AI.run(modelId as any, {
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: goal },
      ],
      max_tokens: this.getMaxTokens(complexity),
    }) as { response?: string };
    return aiResponse?.response || 'No response generated';
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

  /**
   * Send Telegram notification when mission completes
   */
  private async notifyTelegram(tenantId: string, missionId: string, result: string): Promise<void> {
    const botToken = (this.env as any).TELEGRAM_BOT_TOKEN;
    if (!botToken) return;

    const tenant = await this.env.DB.prepare(
      'SELECT telegram_chat_id FROM tenants WHERE id = ?'
    ).bind(tenantId).first<{ telegram_chat_id: string }>();

    if (!tenant?.telegram_chat_id) return;

    const text = `Mission ${missionId.slice(0, 8)}... completed!\n\n${result.slice(0, 3500)}`;
    try {
      await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: parseInt(tenant.telegram_chat_id), text }),
      });
    } catch (error) {
      console.error('[Executor] Telegram notify failed:', error);
    }
  }

  /**
   * Get callback URL from mission metadata
   */
  private async getCallbackUrl(missionId: string): Promise<string | null> {
    const row = await this.env.DB.prepare(
      'SELECT metadata FROM missions WHERE id = ?'
    ).bind(missionId).first<{ metadata: string }>();

    if (!row?.metadata) return null;
    try {
      const meta = JSON.parse(row.metadata);
      return meta.callback_url || null;
    } catch { return null; }
  }

  /**
   * Deliver webhook with exponential backoff retry (immediate, 1s, 5s)
   * Returns true if delivered, false if all retries exhausted
   */
  private async deliverWebhook(url: string, payload: unknown, maxRetries = 3): Promise<boolean> {
    const delays = [0, 1000, 5000];

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      if (attempt > 0) {
        await new Promise(r => setTimeout(r, delays[attempt] || 5000));
      }

      try {
        const resp = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Webhook-Attempt': String(attempt + 1) },
          body: JSON.stringify(payload),
        });

        // 2xx or 4xx = stop retrying (4xx won't fix itself on retry)
        if (resp.ok || resp.status < 500) return true;
      } catch {
        // Network error — will retry
      }
    }

    return false;
  }

  /**
   * Resolve model name to Workers AI model ID
   */
  private resolveModel(model: string): string {
    const models: Record<string, string> = {
      'auto': '@cf/meta/llama-3.1-8b-instruct',
      'fast': '@cf/meta/llama-3.1-8b-instruct',
      'balanced': '@cf/meta/llama-3.1-8b-instruct',
      'premium': '@cf/meta/llama-3.3-70b-instruct-fp8-fast',
    };
    return models[model] || models.auto;
  }

  /**
   * Build system prompt based on complexity
   */
  private buildSystemPrompt(complexity: string): string {
    const base = 'You are Mekong CLI, an AI business operations assistant. ';
    switch (complexity) {
      case 'simple':
        return base + 'Give a brief, actionable answer in 2-3 paragraphs.';
      case 'complex':
        return base + 'Provide a comprehensive plan with steps, code examples, and considerations. Be thorough.';
      default:
        return base + 'Provide a clear, structured response with actionable steps.';
    }
  }

  /**
   * Max tokens based on complexity
   */
  private getMaxTokens(complexity: string): number {
    switch (complexity) {
      case 'simple': return 512;
      case 'complex': return 2048;
      default: return 1024;
    }
  }

  /**
   * Fallback plan when AI is unavailable
   */
  private generateFallbackPlan(goal: string, complexity: string): string {
    return [
      `## Mission Plan: ${goal}`,
      '',
      '### Steps',
      '1. Analyze requirements from the goal description',
      '2. Break down into actionable subtasks',
      '3. Execute each subtask sequentially',
      '4. Verify results against the original goal',
      '',
      `*Complexity: ${complexity} | Generated by Mekong CLI fallback planner*`,
      '*For full AI-powered execution, ensure Workers AI binding is configured.*',
    ].join('\n');
  }
}
