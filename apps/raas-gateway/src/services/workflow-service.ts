/**
 * Workflow Service — CRUD and execution for custom workflow DAGs
 */

import type { D1Database } from '@cloudflare/workers-types';

export type StepType = 'mission' | 'condition' | 'delay' | 'webhook' | 'notification';
export type TriggerType = 'manual' | 'event' | 'schedule' | 'webhook';
export type WorkflowStatus = 'draft' | 'active' | 'paused' | 'archived';
export type ExecutionStatus = 'running' | 'completed' | 'failed' | 'cancelled';

export interface WorkflowStep {
  name: string;
  type: StepType;
  config: Record<string, unknown>;
  onSuccess?: string;
  onFailure?: string;
}

export interface Workflow {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  steps: WorkflowStep[];
  trigger_type: TriggerType;
  trigger_config: Record<string, unknown>;
  status: WorkflowStatus;
  created_at: string;
  updated_at: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  tenant_id: string;
  status: ExecutionStatus;
  current_step: number;
  step_results: unknown[];
  input_data: Record<string, unknown>;
  output_data?: string;
  started_at: string;
  completed_at?: string;
  error?: string;
}

interface CreateWorkflowInput {
  name: string;
  description?: string;
  steps?: WorkflowStep[];
  triggerType?: TriggerType;
  triggerConfig?: Record<string, unknown>;
}

interface UpdateWorkflowInput {
  name?: string;
  description?: string;
  steps?: WorkflowStep[];
  status?: WorkflowStatus;
  triggerType?: TriggerType;
  triggerConfig?: Record<string, unknown>;
}

interface ListExecutionsInput {
  workflowId?: string;
  status?: ExecutionStatus;
  limit?: number;
}

// --- Workflow CRUD ---

export async function createWorkflow(
  db: D1Database,
  tenantId: string,
  input: CreateWorkflowInput
): Promise<Workflow> {
  const id = crypto.randomUUID();
  const steps = JSON.stringify(input.steps ?? []);
  const triggerConfig = JSON.stringify(input.triggerConfig ?? {});
  const triggerType = input.triggerType ?? 'manual';

  await db.prepare(
    `INSERT INTO workflows (id, tenant_id, name, description, steps, trigger_type, trigger_config)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).bind(id, tenantId, input.name, input.description ?? null, steps, triggerType, triggerConfig).run();

  return getWorkflow(db, tenantId, id) as Promise<Workflow>;
}

export async function getWorkflows(
  db: D1Database,
  tenantId: string,
  filters: { status?: WorkflowStatus } = {}
): Promise<Workflow[]> {
  let query = 'SELECT * FROM workflows WHERE tenant_id = ?';
  const bindings: unknown[] = [tenantId];

  if (filters.status) {
    query += ' AND status = ?';
    bindings.push(filters.status);
  }
  query += ' ORDER BY created_at DESC';

  const result = await db.prepare(query).bind(...bindings).all<Record<string, unknown>>();
  return result.results.map(parseWorkflow);
}

export async function getWorkflow(
  db: D1Database,
  tenantId: string,
  workflowId: string
): Promise<Workflow | null> {
  const row = await db.prepare(
    'SELECT * FROM workflows WHERE id = ? AND tenant_id = ?'
  ).bind(workflowId, tenantId).first<Record<string, unknown>>();

  return row ? parseWorkflow(row) : null;
}

export async function updateWorkflow(
  db: D1Database,
  tenantId: string,
  workflowId: string,
  updates: UpdateWorkflowInput
): Promise<Workflow | null> {
  const sets: string[] = ['updated_at = datetime(\'now\')'];
  const bindings: unknown[] = [];

  if (updates.name !== undefined) { sets.push('name = ?'); bindings.push(updates.name); }
  if (updates.description !== undefined) { sets.push('description = ?'); bindings.push(updates.description); }
  if (updates.steps !== undefined) { sets.push('steps = ?'); bindings.push(JSON.stringify(updates.steps)); }
  if (updates.status !== undefined) { sets.push('status = ?'); bindings.push(updates.status); }
  if (updates.triggerType !== undefined) { sets.push('trigger_type = ?'); bindings.push(updates.triggerType); }
  if (updates.triggerConfig !== undefined) { sets.push('trigger_config = ?'); bindings.push(JSON.stringify(updates.triggerConfig)); }

  if (sets.length === 1) return getWorkflow(db, tenantId, workflowId);

  bindings.push(workflowId, tenantId);
  await db.prepare(
    `UPDATE workflows SET ${sets.join(', ')} WHERE id = ? AND tenant_id = ?`
  ).bind(...bindings).run();

  return getWorkflow(db, tenantId, workflowId);
}

export async function deleteWorkflow(
  db: D1Database,
  tenantId: string,
  workflowId: string
): Promise<boolean> {
  const result = await db.prepare(
    'DELETE FROM workflows WHERE id = ? AND tenant_id = ?'
  ).bind(workflowId, tenantId).run();

  return (result.meta?.changes ?? 0) > 0;
}

// --- Executions ---

export async function executeWorkflow(
  db: D1Database,
  tenantId: string,
  workflowId: string,
  inputData: Record<string, unknown> = {}
): Promise<WorkflowExecution | null> {
  const workflow = await getWorkflow(db, tenantId, workflowId);
  if (!workflow) return null;

  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO workflow_executions (id, workflow_id, tenant_id, input_data)
     VALUES (?, ?, ?, ?)`
  ).bind(id, workflowId, tenantId, JSON.stringify(inputData)).run();

  return getExecution(db, tenantId, id);
}

export async function getExecution(
  db: D1Database,
  tenantId: string,
  executionId: string
): Promise<WorkflowExecution | null> {
  const row = await db.prepare(
    'SELECT * FROM workflow_executions WHERE id = ? AND tenant_id = ?'
  ).bind(executionId, tenantId).first<Record<string, unknown>>();

  return row ? parseExecution(row) : null;
}

export async function listExecutions(
  db: D1Database,
  tenantId: string,
  filters: ListExecutionsInput = {}
): Promise<WorkflowExecution[]> {
  let query = 'SELECT * FROM workflow_executions WHERE tenant_id = ?';
  const bindings: unknown[] = [tenantId];

  if (filters.workflowId) { query += ' AND workflow_id = ?'; bindings.push(filters.workflowId); }
  if (filters.status) { query += ' AND status = ?'; bindings.push(filters.status); }
  query += ' ORDER BY started_at DESC LIMIT ?';
  bindings.push(filters.limit ?? 50);

  const result = await db.prepare(query).bind(...bindings).all<Record<string, unknown>>();
  return result.results.map(parseExecution);
}

export async function cancelExecution(
  db: D1Database,
  tenantId: string,
  executionId: string
): Promise<WorkflowExecution | null> {
  await db.prepare(
    `UPDATE workflow_executions SET status = 'cancelled', completed_at = datetime('now')
     WHERE id = ? AND tenant_id = ? AND status = 'running'`
  ).bind(executionId, tenantId).run();

  return getExecution(db, tenantId, executionId);
}

export async function getWorkflowStats(
  db: D1Database,
  tenantId: string
): Promise<Record<string, unknown>> {
  const [wfCounts, execCounts, recentExecs] = await Promise.all([
    db.prepare(
      'SELECT status, COUNT(*) as count FROM workflows WHERE tenant_id = ? GROUP BY status'
    ).bind(tenantId).all<{ status: string; count: number }>(),
    db.prepare(
      'SELECT status, COUNT(*) as count FROM workflow_executions WHERE tenant_id = ? GROUP BY status'
    ).bind(tenantId).all<{ status: string; count: number }>(),
    db.prepare(
      'SELECT * FROM workflow_executions WHERE tenant_id = ? ORDER BY started_at DESC LIMIT 5'
    ).bind(tenantId).all<Record<string, unknown>>(),
  ]);

  const execByStatus: Record<string, number> = {};
  for (const row of execCounts.results) execByStatus[row.status] = row.count;

  const total = Object.values(execByStatus).reduce((a, b) => a + b, 0);
  const completed = execByStatus['completed'] ?? 0;
  const successRate = total > 0 ? Math.round((completed / total) * 100) : 0;

  return {
    workflows: Object.fromEntries(wfCounts.results.map(r => [r.status, r.count])),
    executions: execByStatus,
    successRate,
    recentExecutions: recentExecs.results.map(parseExecution),
  };
}

// --- Parsers ---

function parseWorkflow(row: Record<string, unknown>): Workflow {
  return {
    ...row,
    steps: JSON.parse(row.steps as string ?? '[]'),
    trigger_config: JSON.parse(row.trigger_config as string ?? '{}'),
  } as Workflow;
}

function parseExecution(row: Record<string, unknown>): WorkflowExecution {
  return {
    ...row,
    step_results: JSON.parse(row.step_results as string ?? '[]'),
    input_data: JSON.parse(row.input_data as string ?? '{}'),
  } as WorkflowExecution;
}
