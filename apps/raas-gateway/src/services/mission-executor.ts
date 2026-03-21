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

    // Fetch queued missions (oldest first)
    const queued = await this.env.DB.prepare(
      `SELECT id, tenant_id, goal, complexity, credits_cost
       FROM missions WHERE status = 'queued'
       ORDER BY created_at ASC LIMIT ?`
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
   * Execute a single mission via Workers AI
   */
  private async executeMission(mission: {
    id: string; tenant_id: string; goal: string; complexity: string;
  }): Promise<void> {
    const now = new Date().toISOString();

    // Update status to executing
    await this.env.DB.prepare(
      "UPDATE missions SET status = 'executing', started_at = ? WHERE id = ?"
    ).bind(now, mission.id).run();

    // Build prompt based on complexity
    const systemPrompt = this.buildSystemPrompt(mission.complexity);

    // Call Workers AI
    let result: string;
    try {
      const aiResponse = await this.env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: mission.goal },
        ],
        max_tokens: this.getMaxTokens(mission.complexity),
      }) as { response?: string };

      result = aiResponse?.response || 'No response generated';
    } catch (aiError) {
      // Fallback: generate a structured plan without AI
      result = this.generateFallbackPlan(mission.goal, mission.complexity);
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
        JSON.stringify({ executor: 'workers-ai', model: 'llama-3.1-8b-instruct' }),
        mission.id
      )
      .run();

    // Fire webhook callback if configured
    const callbackUrl = await this.getCallbackUrl(mission.id);
    if (callbackUrl) {
      await this.fireCallback(callbackUrl, {
        event: 'mission.completed',
        mission_id: mission.id,
        tenant_id: mission.tenant_id,
        status: 'completed',
        result,
        completed_at: completedAt,
      });
    }
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
   * Fire webhook callback (best-effort, no retry)
   */
  private async fireCallback(url: string, payload: Record<string, unknown>): Promise<void> {
    try {
      await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch (error) {
      console.error(`[Executor] Callback to ${url} failed:`, error);
    }
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
