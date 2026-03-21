/**
 * Health check endpoints — simple liveness and deep dependency checks
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';

const VERSION = '5.0.0';
const startTime = Date.now();

export const health = new Hono<{ Bindings: Env }>();

// Simple liveness check
health.get('/', (c) => {
  return json({
    status: 'healthy',
    version: VERSION,
    uptime: Date.now() - startTime,
    timestamp: new Date().toISOString(),
    environment: c.env.ENVIRONMENT,
  });
});

// Readiness check — verifies DB connection only
health.get('/ready', async (c) => {
  try {
    await c.env.DB.prepare('SELECT 1').first();
    return json({ status: 'ready', checks: { database: 'ok' } });
  } catch (error) {
    return json(
      { status: 'not_ready', checks: { database: 'error' } },
      { status: 503 }
    );
  }
});

// Liveness probe
health.get('/live', (c) => {
  return json({ status: 'alive' });
});

// Deep health check — tests DB, KV, and AI binding
health.get('/deep', async (c) => {
  const checks: Record<string, { status: string; latencyMs?: number; error?: string }> = {};
  const start = Date.now();

  // DB check
  try {
    const dbStart = Date.now();
    await c.env.DB.prepare('SELECT 1').first();
    checks.database = { status: 'ok', latencyMs: Date.now() - dbStart };
  } catch (e: any) {
    checks.database = { status: 'error', error: e.message };
  }

  // KV check — write and read back
  try {
    const kvStart = Date.now();
    await c.env.RATE_LIMIT_KV.put('health-check', 'ok', { expirationTtl: 60 });
    const val = await c.env.RATE_LIMIT_KV.get('health-check');
    checks.kv = {
      status: val === 'ok' ? 'ok' : 'degraded',
      latencyMs: Date.now() - kvStart,
    };
  } catch (e: any) {
    checks.kv = { status: 'error', error: e.message };
  }

  // AI binding check — minimal inference call
  try {
    const aiStart = Date.now();
    await c.env.AI.run('@cf/meta/llama-3.1-8b-instruct' as any, {
      messages: [{ role: 'user', content: 'Say ok' }],
      max_tokens: 5,
    });
    checks.ai = { status: 'ok', latencyMs: Date.now() - aiStart };
  } catch (e: any) {
    checks.ai = { status: 'error', error: e.message };
  }

  const allOk = Object.values(checks).every((ch) => ch.status === 'ok');

  return json(
    {
      status: allOk ? 'healthy' : 'degraded',
      totalLatencyMs: Date.now() - start,
      checks,
      timestamp: new Date().toISOString(),
      version: VERSION,
    },
    { status: allOk ? 200 : 503 }
  );
});
