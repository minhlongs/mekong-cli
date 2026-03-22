/**
 * Tenant Audit Policies routes — policy CRUD, violation tracking, and admin overview
 * Mount at: /v1/audit-policies
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createPolicy,
  listPolicies,
  getPolicy,
  updatePolicy,
  deletePolicy,
  listViolations,
  resolveViolation,
  getAdminPolicyOverview,
} from '../services/tenant-audit-policies-service';

export const tenantAuditPolicies = new Hono<{ Bindings: Env }>();

/**
 * GET /policies — list all audit policies for the authenticated tenant
 */
tenantAuditPolicies.get('/policies', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const policies = await listPolicies(c.env.DB, tenantId);
    return json({ policies });
  } catch {
    return json({ error: 'Failed to fetch audit policies' }, { status: 500 });
  }
});

/**
 * POST /policies — create a new audit policy
 * Body: { policy_name, event_types?, retention_days?, log_level?, include_request_body?,
 *         include_response_body?, export_enabled?, export_destination?, export_config? }
 */
tenantAuditPolicies.post('/policies', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { policy_name } = body;
  if (!policy_name || typeof policy_name !== 'string') {
    return json({ error: 'policy_name is required' }, { status: 400 });
  }

  const validLogLevels = ['minimal', 'standard', 'verbose'];
  if (body.log_level && !validLogLevels.includes(String(body.log_level))) {
    return json({ error: `log_level must be one of: ${validLogLevels.join(', ')}` }, { status: 400 });
  }

  const validDestinations = ['s3', 'webhook', 'email'];
  if (body.export_destination && !validDestinations.includes(String(body.export_destination))) {
    return json({ error: `export_destination must be one of: ${validDestinations.join(', ')}` }, { status: 400 });
  }

  try {
    const policy = await createPolicy(c.env.DB, tenantId, {
      policyName: policy_name,
      eventTypes: Array.isArray(body.event_types) ? body.event_types as string[] : undefined,
      retentionDays: body.retention_days ? Number(body.retention_days) : undefined,
      logLevel: body.log_level ? String(body.log_level) : undefined,
      includeRequestBody: Boolean(body.include_request_body),
      includeResponseBody: Boolean(body.include_response_body),
      exportEnabled: Boolean(body.export_enabled),
      exportDestination: body.export_destination ? String(body.export_destination) : undefined,
      exportConfig: body.export_config as Record<string, unknown> | undefined,
    });
    return json({ policy }, { status: 201 });
  } catch {
    return json({ error: 'Failed to create audit policy' }, { status: 500 });
  }
});

/**
 * GET /policies/:policyId — get a single audit policy
 */
tenantAuditPolicies.get('/policies/:policyId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const policyId = c.req.param('policyId');
  try {
    const policy = await getPolicy(c.env.DB, tenantId, policyId);
    if (!policy) return json({ error: 'Audit policy not found' }, { status: 404 });
    return json({ policy });
  } catch {
    return json({ error: 'Failed to fetch audit policy' }, { status: 500 });
  }
});

/**
 * PUT /policies/:policyId — update an audit policy (partial)
 * Body: any updatable fields
 */
tenantAuditPolicies.put('/policies/:policyId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const policyId = c.req.param('policyId');
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const validLogLevels = ['minimal', 'standard', 'verbose'];
  if (body.log_level && !validLogLevels.includes(String(body.log_level))) {
    return json({ error: `log_level must be one of: ${validLogLevels.join(', ')}` }, { status: 400 });
  }

  try {
    const policy = await updatePolicy(c.env.DB, tenantId, policyId, {
      policyName: body.policy_name ? String(body.policy_name) : undefined,
      eventTypes: Array.isArray(body.event_types) ? body.event_types as string[] : undefined,
      retentionDays: body.retention_days !== undefined ? Number(body.retention_days) : undefined,
      logLevel: body.log_level ? String(body.log_level) : undefined,
      includeRequestBody: body.include_request_body !== undefined ? Boolean(body.include_request_body) : undefined,
      includeResponseBody: body.include_response_body !== undefined ? Boolean(body.include_response_body) : undefined,
      exportEnabled: body.export_enabled !== undefined ? Boolean(body.export_enabled) : undefined,
      exportDestination: 'export_destination' in body ? (body.export_destination ? String(body.export_destination) : null) : undefined,
      exportConfig: body.export_config as Record<string, unknown> | undefined,
      isActive: body.is_active !== undefined ? Boolean(body.is_active) : undefined,
    });
    if (!policy) return json({ error: 'Audit policy not found' }, { status: 404 });
    return json({ policy });
  } catch {
    return json({ error: 'Failed to update audit policy' }, { status: 500 });
  }
});

/**
 * DELETE /policies/:policyId — delete an audit policy
 */
tenantAuditPolicies.delete('/policies/:policyId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const policyId = c.req.param('policyId');
  try {
    const deleted = await deletePolicy(c.env.DB, tenantId, policyId);
    if (!deleted) return json({ error: 'Audit policy not found' }, { status: 404 });
    return json({ success: true });
  } catch {
    return json({ error: 'Failed to delete audit policy' }, { status: 500 });
  }
});

/**
 * GET /violations — list violations for the authenticated tenant
 * Query: resolved (boolean), severity (info|warning|critical), limit (default 50)
 */
tenantAuditPolicies.get('/violations', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const resolvedParam = c.req.query('resolved');
  const severity = c.req.query('severity');
  const limit = Math.min(parseInt(c.req.query('limit') ?? '50', 10) || 50, 200);

  const resolved = resolvedParam !== undefined ? resolvedParam === 'true' : undefined;

  const validSeverities = ['info', 'warning', 'critical'];
  if (severity && !validSeverities.includes(severity)) {
    return json({ error: `severity must be one of: ${validSeverities.join(', ')}` }, { status: 400 });
  }

  try {
    const violations = await listViolations(c.env.DB, tenantId, { resolved, severity, limit });
    return json({ violations });
  } catch {
    return json({ error: 'Failed to fetch violations' }, { status: 500 });
  }
});

/**
 * POST /violations/:violationId/resolve — mark a violation as resolved
 */
tenantAuditPolicies.post('/violations/:violationId/resolve', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const violationId = c.req.param('violationId');
  try {
    const violation = await resolveViolation(c.env.DB, tenantId, violationId);
    if (!violation) return json({ error: 'Violation not found' }, { status: 404 });
    return json({ violation });
  } catch {
    return json({ error: 'Failed to resolve violation' }, { status: 500 });
  }
});

/**
 * GET /admin/overview — admin: policy and violation summary across all tenants
 * Requires X-Admin-Key header
 */
tenantAuditPolicies.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) return json({ error: 'Forbidden' }, { status: 403 });

  try {
    const overview = await getAdminPolicyOverview(c.env.DB);
    return json({ overview });
  } catch {
    return json({ error: 'Failed to fetch admin overview' }, { status: 500 });
  }
});
