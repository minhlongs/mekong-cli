// Mission Approval Workflow Service — approval chains, delegation, escalation
import type { D1Database } from '@cloudflare/workers-types';

/** List all approval workflows for a tenant */
export async function listWorkflows(db: D1Database, tenantId: string): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM approval_workflows WHERE tenant_id = ? ORDER BY created_at DESC`
  ).bind(tenantId).all();
  return rows.results;
}

/** Create a new approval workflow with steps */
export async function createWorkflow(
  db: D1Database,
  tenantId: string,
  data: { name: string; description?: string; steps?: unknown[] }
): Promise<unknown> {
  const id = crypto.randomUUID();
  return db.prepare(
    `INSERT INTO approval_workflows (id, tenant_id, name, description, steps_json)
     VALUES (?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    id, tenantId, data.name,
    data.description ?? null,
    JSON.stringify(data.steps ?? [])
  ).first();
}

/** Get a single workflow by id scoped to tenant */
export async function getWorkflow(
  db: D1Database, tenantId: string, workflowId: string
): Promise<unknown | null> {
  return db.prepare(
    `SELECT * FROM approval_workflows WHERE id = ? AND tenant_id = ?`
  ).bind(workflowId, tenantId).first();
}

/** Update workflow name, description, steps, or active status */
export async function updateWorkflow(
  db: D1Database,
  tenantId: string,
  workflowId: string,
  data: { name?: string; description?: string; steps?: unknown[]; is_active?: boolean }
): Promise<unknown | null> {
  const sets: string[] = ["updated_at = datetime('now')"];
  const binds: unknown[] = [];

  if (data.name !== undefined) { sets.push('name = ?'); binds.push(data.name); }
  if (data.description !== undefined) { sets.push('description = ?'); binds.push(data.description); }
  if (data.steps !== undefined) { sets.push('steps_json = ?'); binds.push(JSON.stringify(data.steps)); }
  if (data.is_active !== undefined) { sets.push('is_active = ?'); binds.push(data.is_active ? 1 : 0); }

  if (sets.length === 1) return getWorkflow(db, tenantId, workflowId);
  binds.push(workflowId, tenantId);

  return db.prepare(
    `UPDATE approval_workflows SET ${sets.join(', ')} WHERE id = ? AND tenant_id = ? RETURNING *`
  ).bind(...binds).first();
}

/** Create an approval request to submit a mission through a workflow */
export async function submitForApproval(
  db: D1Database,
  tenantId: string,
  missionId: string,
  workflowId: string,
  requestedBy: string
): Promise<unknown> {
  const id = crypto.randomUUID();
  return db.prepare(
    `INSERT INTO approval_requests (id, tenant_id, workflow_id, mission_id, requested_by)
     VALUES (?, ?, ?, ?, ?) RETURNING *`
  ).bind(id, tenantId, workflowId, missionId, requestedBy).first();
}

/** Get a single approval request with its decisions */
export async function getApprovalRequest(
  db: D1Database, tenantId: string, requestId: string
): Promise<unknown | null> {
  const request = await db.prepare(
    `SELECT * FROM approval_requests WHERE id = ? AND tenant_id = ?`
  ).bind(requestId, tenantId).first();
  if (!request) return null;

  const decisions = await db.prepare(
    `SELECT * FROM approval_decisions WHERE request_id = ? ORDER BY step_index ASC, decided_at ASC`
  ).bind(requestId).all();

  return { ...(request as object), decisions: decisions.results };
}

/** Record an approval decision (approve/reject/delegate) and advance workflow state */
export async function makeDecision(
  db: D1Database,
  tenantId: string,
  requestId: string,
  approverId: string,
  decision: string,
  comment?: string
): Promise<unknown | null> {
  const request = await db.prepare(
    `SELECT * FROM approval_requests WHERE id = ? AND tenant_id = ?`
  ).bind(requestId, tenantId).first<{ current_step: number; status: string }>();
  if (!request || request.status !== 'pending') return null;

  const decisionId = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO approval_decisions (id, request_id, step_index, approver_id, decision, comment)
     VALUES (?, ?, ?, ?, ?, ?)`
  ).bind(decisionId, requestId, request.current_step, approverId, decision, comment ?? null).run();

  // Map decision to request status
  let newStatus = 'pending';
  let nextStep = request.current_step;
  if (decision === 'approve') { newStatus = 'approved'; nextStep = request.current_step + 1; }
  else if (decision === 'reject') { newStatus = 'rejected'; }
  else if (decision === 'delegate') { newStatus = 'escalated'; }

  return db.prepare(
    `UPDATE approval_requests SET status = ?, current_step = ?, updated_at = datetime('now')
     WHERE id = ? RETURNING *`
  ).bind(newStatus, nextStep, requestId).first();
}

/** List all pending approval requests for a tenant */
export async function listPendingApprovals(db: D1Database, tenantId: string): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM approval_requests WHERE tenant_id = ? AND status = 'pending'
     ORDER BY created_at ASC`
  ).bind(tenantId).all();
  return rows.results;
}

/** Admin overview: workflow and request counts across all tenants */
export async function getAdminOverview(db: D1Database): Promise<unknown> {
  const [totalWorkflows, activeWorkflows, totalRequests, pending, approved, rejected] =
    await Promise.all([
      db.prepare(`SELECT COUNT(*) as count FROM approval_workflows`).first<{ count: number }>(),
      db.prepare(`SELECT COUNT(*) as count FROM approval_workflows WHERE is_active = 1`).first<{ count: number }>(),
      db.prepare(`SELECT COUNT(*) as count FROM approval_requests`).first<{ count: number }>(),
      db.prepare(`SELECT COUNT(*) as count FROM approval_requests WHERE status = 'pending'`).first<{ count: number }>(),
      db.prepare(`SELECT COUNT(*) as count FROM approval_requests WHERE status = 'approved'`).first<{ count: number }>(),
      db.prepare(`SELECT COUNT(*) as count FROM approval_requests WHERE status = 'rejected'`).first<{ count: number }>(),
    ]);

  return {
    workflows: { total: totalWorkflows?.count ?? 0, active: activeWorkflows?.count ?? 0 },
    requests: {
      total: totalRequests?.count ?? 0,
      pending: pending?.count ?? 0,
      approved: approved?.count ?? 0,
      rejected: rejected?.count ?? 0,
    },
  };
}
