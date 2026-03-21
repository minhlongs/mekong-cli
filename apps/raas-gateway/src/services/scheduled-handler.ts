/**
 * Scheduled Handler — orchestrates all periodic background tasks.
 * Invoked by the Cloudflare Workers `scheduled` event.
 */

import { RecurringMissionService } from './recurring-mission-service';
import { WebhookRetryService } from './webhook-retry-service';
import { TenantHealthService } from './tenant-health-service';

interface TaskResult {
  task: string;
  status: 'ok' | 'error' | 'skipped';
  error?: string;
}

export async function handleScheduled(env: { DB: D1Database; RATE_LIMIT_KV: KVNamespace }): Promise<void> {
  const results: TaskResult[] = [];

  // 1. Process recurring missions
  try {
    const recurring = new RecurringMissionService();
    const processed = await recurring.processDue(env.DB);
    results.push({ task: 'recurring_missions', status: 'ok', ...processed });
  } catch (err) {
    results.push({
      task: 'recurring_missions',
      status: 'error',
      error: err instanceof Error ? err.message : 'unknown',
    });
  }

  // 2. Process webhook retries
  try {
    const retrier = new WebhookRetryService();
    await retrier.processRetries(env.DB, env.RATE_LIMIT_KV);
    results.push({ task: 'webhook_retries', status: 'ok' });
  } catch (err) {
    results.push({
      task: 'webhook_retries',
      status: 'error',
      error: err instanceof Error ? err.message : 'unknown',
    });
  }

  // 3. Auto-calculate tenant health scores (hourly — only run if minute < 5)
  try {
    const now = new Date();
    if (now.getMinutes() < 5) {
      const health = new TenantHealthService();
      const tenants = await env.DB
        .prepare('SELECT DISTINCT tenant_id FROM tenants WHERE status = ?')
        .bind('active')
        .all();
      for (const t of (tenants.results || [])) {
        await health.calculateScore(env.DB, t.tenant_id as string);
      }
      results.push({ task: 'tenant_health', status: 'ok' });
    } else {
      results.push({ task: 'tenant_health', status: 'skipped' });
    }
  } catch (err) {
    results.push({
      task: 'tenant_health',
      status: 'error',
      error: err instanceof Error ? err.message : 'unknown',
    });
  }

  console.log('[scheduled]', JSON.stringify(results));
}
