/**
 * AI Mission Router — intelligent model selection for missions
 * Uses OpenClaw Model Registry to auto-select optimal model per mission requirements
 */

import { OpenClawModelRegistry } from './openclaw-model-registry';
import type { ModelInfo, ModelRequirements } from './openclaw-model-registry';

const registry = new OpenClawModelRegistry();

export interface MissionInput {
  goal: string;
  complexity: 'simple' | 'standard' | 'complex';
  capabilities?: string[];
  budget?: 'low' | 'medium' | 'high';
}

export interface ModelStats {
  modelId: string;
  provider: string;
  usageCount: number;
  avgLatencyMs: number;
  totalTokens: number;
  costEstimate: number;
}

/** Map complexity level to required capabilities */
function complexityToCapabilities(complexity: MissionInput['complexity']): string[] {
  const map: Record<MissionInput['complexity'], string[]> = {
    simple: ['chat'],
    standard: ['chat', 'code'],
    complex: ['code', 'reasoning'],
  };
  return map[complexity];
}

/** Map budget tier to max cost per million tokens (input) */
function budgetToMaxCost(budget: MissionInput['budget']): number | undefined {
  if (!budget) return undefined;
  const map: Record<NonNullable<MissionInput['budget']>, number> = {
    low: 0.5,
    medium: 2,
    high: 10,
  };
  return map[budget];
}

/**
 * Select optimal model for a given mission.
 * Falls back to cheapest available model if no match found.
 */
export function selectModelForMission(mission: MissionInput): ModelInfo {
  const requiredCaps = mission.capabilities ?? complexityToCapabilities(mission.complexity);
  const maxCost = budgetToMaxCost(mission.budget);

  // Try each required capability — use the first that yields a result
  for (const capability of requiredCaps) {
    const requirements: ModelRequirements = { capability, maxCost };
    const model = registry.selectOptimal(requirements);
    if (model) return model;
  }

  // Fallback: cheapest available regardless of capability
  const allModels = registry.listModels();
  const available = allModels
    .filter(m => m.status === 'available')
    .sort((a, b) => a.costPerMToken.input - b.costPerMToken.input);

  if (!available.length) {
    throw new Error('No available models in registry');
  }
  return available[0];
}

/**
 * Record model usage for a mission in D1 database.
 */
export async function trackModelUsage(
  missionId: string,
  modelId: string,
  tokens: number,
  latencyMs: number,
  db: any,
  tenantId?: string
): Promise<void> {
  const model = registry.getModel(modelId);
  if (!model) return;

  const costEstimate = (tokens / 1_000_000) * model.costPerMToken.input;
  const id = crypto.randomUUID();

  try {
    await db
      .prepare(
        `INSERT INTO mission_model_usage
         (id, mission_id, tenant_id, model_id, provider, tokens_used, latency_ms, cost_estimate)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, missionId, tenantId ?? null, modelId, model.provider, tokens, latencyMs, costEstimate)
      .run();
  } catch (err) {
    // Non-fatal — log and continue
    console.error('[ai-mission-router] trackModelUsage failed:', err);
  }
}

/**
 * Aggregated model usage stats for the last N days.
 */
export async function getModelStats(db: any, days = 30): Promise<ModelStats[]> {
  try {
    const since = new Date(Date.now() - days * 86_400_000).toISOString();
    const result = await db
      .prepare(
        `SELECT
           model_id,
           provider,
           COUNT(*) as usage_count,
           AVG(latency_ms) as avg_latency_ms,
           SUM(tokens_used) as total_tokens,
           SUM(cost_estimate) as cost_estimate
         FROM mission_model_usage
         WHERE created_at >= ?
         GROUP BY model_id, provider
         ORDER BY usage_count DESC`
      )
      .bind(since)
      .all();

    return (result.results ?? []).map((row: any) => ({
      modelId: row.model_id,
      provider: row.provider,
      usageCount: row.usage_count,
      avgLatencyMs: Math.round(row.avg_latency_ms ?? 0),
      totalTokens: row.total_tokens ?? 0,
      costEstimate: Number((row.cost_estimate ?? 0).toFixed(6)),
    }));
  } catch (err) {
    console.error('[ai-mission-router] getModelStats failed:', err);
    return [];
  }
}

/**
 * Personalized model recommendation based on tenant's usage history.
 * Returns the model they use most successfully, or cheapest if no history.
 */
export async function getModelRecommendation(tenantId: string, db: any): Promise<ModelInfo> {
  try {
    const result = await db
      .prepare(
        `SELECT model_id, COUNT(*) as cnt
         FROM mission_model_usage
         WHERE tenant_id = ? AND status = 'success'
         GROUP BY model_id
         ORDER BY cnt DESC
         LIMIT 1`
      )
      .bind(tenantId)
      .first();

    if (result?.model_id) {
      const model = registry.getModel(result.model_id);
      if (model && model.status === 'available') return model;
    }
  } catch (err) {
    console.error('[ai-mission-router] getModelRecommendation failed:', err);
  }

  // Default: cheapest available
  return selectModelForMission({ goal: '', complexity: 'simple', budget: 'low' });
}
