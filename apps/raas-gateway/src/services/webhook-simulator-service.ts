/**
 * Webhook Simulator Service — test delivery, inspect payloads, simulate scenarios
 * Supports mock delivery, test endpoints, retry, and stats
 */

import type { SimulationRow, TestEndpointRow, DeliveryResult } from './webhook-simulator-types';
export type { SimulationRow, TestEndpointRow } from './webhook-simulator-types';

// ── Sample payload generator ───────────────────────────────────────────────

/** Generate a realistic sample payload for common event types */
export function generateSamplePayload(eventType: string): Record<string, unknown> {
  const ts = new Date().toISOString();
  const samples: Record<string, Record<string, unknown>> = {
    'mission.created': {
      event: 'mission.created', timestamp: ts,
      data: { id: 'msn_demo123', title: 'Sample Mission', status: 'pending', tenant_id: 'tenant_demo' },
    },
    'mission.completed': {
      event: 'mission.completed', timestamp: ts,
      data: { id: 'msn_demo123', title: 'Sample Mission', status: 'completed', duration_ms: 1200 },
    },
    'payment.received': {
      event: 'payment.received', timestamp: ts,
      data: { id: 'pay_demo456', amount: 4900, currency: 'usd', tenant_id: 'tenant_demo' },
    },
    'tenant.updated': {
      event: 'tenant.updated', timestamp: ts,
      data: { id: 'tenant_demo', name: 'Acme Corp', plan: 'pro', updated_fields: ['name'] },
    },
  };
  return samples[eventType] ?? { event: eventType, timestamp: ts, data: {} };
}

// ── Delivery ───────────────────────────────────────────────────────────────

/** Attempt webhook delivery via HTTP POST */
async function attemptDelivery(targetUrl: string, payload: Record<string, unknown>): Promise<DeliveryResult> {
  const start = Date.now();
  try {
    const res = await fetch(targetUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Webhook-Source': 'raas-simulator' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(5000),
    });
    const body = await res.text().catch(() => '');
    return { code: res.status, body: body.substring(0, 500), latency: Date.now() - start };
  } catch {
    return { code: 0, body: 'delivery_failed', latency: Date.now() - start };
  }
}

// ── Simulation CRUD ────────────────────────────────────────────────────────

/** Create simulation record, attempt delivery, update result */
export async function simulateWebhook(
  db: D1Database, tenantId: string, targetUrl: string,
  eventType: string, payload: Record<string, unknown>,
): Promise<SimulationRow> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO webhook_simulations (id,tenant_id,target_url,event_type,payload,status)
     VALUES (?,?,?,?,?,'pending')`
  ).bind(id, tenantId, targetUrl, eventType, JSON.stringify(payload)).run();

  const result = await attemptDelivery(targetUrl, payload);
  const status = result.code >= 200 && result.code < 300 ? 'success' : 'failed';
  await db.prepare(
    `UPDATE webhook_simulations
     SET status=?,response_code=?,response_body=?,latency_ms=?,completed_at=datetime('now')
     WHERE id=?`
  ).bind(status, result.code || null, result.body, result.latency, id).run();

  return db.prepare('SELECT * FROM webhook_simulations WHERE id=?').bind(id).first<SimulationRow>() as Promise<SimulationRow>;
}

/** List recent simulations for a tenant */
export async function listSimulations(db: D1Database, tenantId: string, limit = 20): Promise<SimulationRow[]> {
  const { results } = await db.prepare(
    'SELECT * FROM webhook_simulations WHERE tenant_id=? ORDER BY created_at DESC LIMIT ?'
  ).bind(tenantId, limit).all<SimulationRow>();
  return results;
}

/** Get single simulation scoped to tenant */
export async function getSimulation(db: D1Database, simId: string, tenantId: string): Promise<SimulationRow | null> {
  return db.prepare('SELECT * FROM webhook_simulations WHERE id=? AND tenant_id=?')
    .bind(simId, tenantId).first<SimulationRow>();
}

/** Retry a simulation — re-attempt delivery and increment retry_count */
export async function retrySimulation(db: D1Database, simId: string, tenantId: string): Promise<SimulationRow | null> {
  const sim = await getSimulation(db, simId, tenantId);
  if (!sim) return null;
  const payload = JSON.parse(sim.payload) as Record<string, unknown>;
  const result = await attemptDelivery(sim.target_url, payload);
  const status = result.code >= 200 && result.code < 300 ? 'success' : 'failed';
  await db.prepare(
    `UPDATE webhook_simulations
     SET status=?,response_code=?,response_body=?,latency_ms=?,retry_count=retry_count+1,completed_at=datetime('now')
     WHERE id=?`
  ).bind(status, result.code || null, result.body, result.latency, simId).run();
  return getSimulation(db, simId, tenantId);
}

// ── Test endpoints ─────────────────────────────────────────────────────────

/** Create a captive test endpoint for this tenant */
export async function createTestEndpoint(db: D1Database, tenantId: string): Promise<TestEndpointRow> {
  const id = crypto.randomUUID();
  await db.prepare(
    'INSERT INTO webhook_test_endpoints (id,tenant_id,endpoint_path) VALUES (?,?,?)'
  ).bind(id, tenantId, `/test-hooks/${id}`).run();
  return db.prepare('SELECT * FROM webhook_test_endpoints WHERE id=?').bind(id).first<TestEndpointRow>() as Promise<TestEndpointRow>;
}

/** List all test endpoints for a tenant */
export async function listTestEndpoints(db: D1Database, tenantId: string): Promise<TestEndpointRow[]> {
  const { results } = await db.prepare(
    'SELECT * FROM webhook_test_endpoints WHERE tenant_id=? ORDER BY created_at DESC'
  ).bind(tenantId).all<TestEndpointRow>();
  return results;
}

/** Get endpoint detail including last_payload */
export async function getEndpointPayloads(db: D1Database, endpointId: string, tenantId: string): Promise<TestEndpointRow | null> {
  return db.prepare('SELECT * FROM webhook_test_endpoints WHERE id=? AND tenant_id=?')
    .bind(endpointId, tenantId).first<TestEndpointRow>();
}

/** Delete a test endpoint */
export async function deleteTestEndpoint(db: D1Database, endpointId: string, tenantId: string): Promise<boolean> {
  const res = await db.prepare('DELETE FROM webhook_test_endpoints WHERE id=? AND tenant_id=?')
    .bind(endpointId, tenantId).run();
  return (res.meta?.changes ?? 0) > 0;
}

// ── Stats ──────────────────────────────────────────────────────────────────

/** Aggregate simulation stats for a tenant */
export async function getSimulationStats(db: D1Database, tenantId: string) {
  const row = await db.prepare(
    `SELECT COUNT(*) as total,
       SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success,
       SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
       AVG(latency_ms) as avg_latency_ms
     FROM webhook_simulations WHERE tenant_id=?`
  ).bind(tenantId).first<{ total: number; success: number; failed: number; avg_latency_ms: number }>();
  const total = row?.total ?? 0;
  const success = row?.success ?? 0;
  return {
    total, success,
    failed: row?.failed ?? 0,
    success_rate: total > 0 ? Math.round((success / total) * 100) : 0,
    avg_latency_ms: Math.round(row?.avg_latency_ms ?? 0),
  };
}
