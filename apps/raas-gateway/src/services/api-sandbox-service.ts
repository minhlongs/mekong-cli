/**
 * API Sandbox Service — isolated test environments per tenant
 * Manages sandbox lifecycle, mock responses, and request logging
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface SandboxEnvironment {
  id: string;
  tenant_id: string;
  name: string;
  is_active: number;
  config: string;
  mock_responses: string;
  request_count: number;
  created_at: string;
}

export interface SandboxRequest {
  id: string;
  sandbox_id: string;
  method: string;
  path: string;
  request_body: string | null;
  response_body: string | null;
  status_code: number | null;
  latency_ms: number | null;
  created_at: string;
}

function newId(): string {
  return crypto.randomUUID();
}

/** Create a new sandbox environment for a tenant */
export async function createSandbox(
  db: D1Database,
  tenantId: string,
  name: string,
  config?: unknown
): Promise<SandboxEnvironment> {
  const id = newId();
  const configStr = JSON.stringify(config ?? {});
  await db.prepare(
    `INSERT INTO sandbox_environments (id, tenant_id, name, config) VALUES (?, ?, ?, ?)`
  ).bind(id, tenantId, name || 'default', configStr).run();
  return getSandbox(db, id, tenantId) as Promise<SandboxEnvironment>;
}

/** List all sandboxes for a tenant */
export async function listSandboxes(db: D1Database, tenantId: string): Promise<SandboxEnvironment[]> {
  const { results } = await db.prepare(
    `SELECT * FROM sandbox_environments WHERE tenant_id = ? ORDER BY created_at DESC`
  ).bind(tenantId).all<SandboxEnvironment>();
  return results;
}

/** Get a single sandbox (validates tenant ownership) */
export async function getSandbox(
  db: D1Database,
  sandboxId: string,
  tenantId: string
): Promise<SandboxEnvironment | null> {
  return db.prepare(
    `SELECT * FROM sandbox_environments WHERE id = ? AND tenant_id = ?`
  ).bind(sandboxId, tenantId).first<SandboxEnvironment>();
}

/** Soft-delete sandbox (set is_active = 0) */
export async function deleteSandbox(db: D1Database, sandboxId: string, tenantId: string): Promise<boolean> {
  const result = await db.prepare(
    `UPDATE sandbox_environments SET is_active = 0 WHERE id = ? AND tenant_id = ?`
  ).bind(sandboxId, tenantId).run();
  return (result.meta.changes ?? 0) > 0;
}

/** Configure a mock response for a path+method combination */
export async function setMockResponse(
  db: D1Database,
  sandboxId: string,
  path: string,
  method: string,
  statusCode: number,
  body: unknown
): Promise<void> {
  const sandbox = await db.prepare(
    `SELECT mock_responses FROM sandbox_environments WHERE id = ?`
  ).bind(sandboxId).first<{ mock_responses: string }>();
  if (!sandbox) throw new Error('Sandbox not found');

  const mocks = JSON.parse(sandbox.mock_responses || '{}');
  const key = `${method.toUpperCase()}:${path}`;
  mocks[key] = { status_code: statusCode, body };

  await db.prepare(
    `UPDATE sandbox_environments SET mock_responses = ? WHERE id = ?`
  ).bind(JSON.stringify(mocks), sandboxId).run();
}

/** Simulate an API request — returns mock or default response, logs to sandbox_requests */
export async function executeRequest(
  db: D1Database,
  sandboxId: string,
  method: string,
  path: string,
  body?: unknown
): Promise<{ status_code: number; body: unknown; latency_ms: number }> {
  const startMs = Date.now();
  const sandbox = await db.prepare(
    `SELECT mock_responses FROM sandbox_environments WHERE id = ? AND is_active = 1`
  ).bind(sandboxId).first<{ mock_responses: string }>();
  if (!sandbox) throw new Error('Sandbox not found or inactive');

  const mocks = JSON.parse(sandbox.mock_responses || '{}');
  const key = `${method.toUpperCase()}:${path}`;
  const mock = mocks[key] ?? { status_code: 200, body: { message: 'ok', sandbox: true } };

  const latency = Date.now() - startMs;

  await db.prepare(
    `INSERT INTO sandbox_requests (id, sandbox_id, method, path, request_body, response_body, status_code, latency_ms)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    newId(), sandboxId, method.toUpperCase(), path,
    body ? JSON.stringify(body) : null,
    JSON.stringify(mock.body),
    mock.status_code, latency
  ).run();

  await db.prepare(
    `UPDATE sandbox_environments SET request_count = request_count + 1 WHERE id = ?`
  ).bind(sandboxId).run();

  return { status_code: mock.status_code, body: mock.body, latency_ms: latency };
}

/** Get recent request history for a sandbox */
export async function getRequestHistory(
  db: D1Database,
  sandboxId: string,
  limit = 50
): Promise<SandboxRequest[]> {
  const { results } = await db.prepare(
    `SELECT * FROM sandbox_requests WHERE sandbox_id = ? ORDER BY created_at DESC LIMIT ?`
  ).bind(sandboxId, limit).all<SandboxRequest>();
  return results;
}

/** Delete all request logs for a sandbox */
export async function clearHistory(db: D1Database, sandboxId: string): Promise<void> {
  await db.prepare(`DELETE FROM sandbox_requests WHERE sandbox_id = ?`).bind(sandboxId).run();
}

/** Aggregate stats across all sandboxes for a tenant */
export async function getSandboxStats(
  db: D1Database,
  tenantId: string
): Promise<{ total_sandboxes: number; active_sandboxes: number; total_requests: number }> {
  const row = await db.prepare(
    `SELECT COUNT(*) as total, SUM(is_active) as active, SUM(request_count) as reqs
     FROM sandbox_environments WHERE tenant_id = ?`
  ).bind(tenantId).first<{ total: number; active: number; reqs: number }>();
  return {
    total_sandboxes: row?.total ?? 0,
    active_sandboxes: row?.active ?? 0,
    total_requests: row?.reqs ?? 0,
  };
}

/** Reset sandbox: clear mocks and request history */
export async function resetSandbox(db: D1Database, sandboxId: string): Promise<void> {
  await db.prepare(
    `UPDATE sandbox_environments SET mock_responses = '{}', request_count = 0 WHERE id = ?`
  ).bind(sandboxId).run();
  await clearHistory(db, sandboxId);
}
