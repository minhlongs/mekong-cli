/**
 * Tenant API Schema Validation routes
 * Mount at: /v1/schema-validation
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiSchemaValidationService as svc } from '../services/tenant-api-schema-validation-service';

export const tenantApiSchemaValidation = new Hono<{ Bindings: Env }>();

// All non-admin routes require tenant auth
tenantApiSchemaValidation.use('/rules', auth());
tenantApiSchemaValidation.use('/violations', auth());

/**
 * GET /v1/schema-validation/rules — List schema rules for the authenticated tenant
 */
tenantApiSchemaValidation.get('/rules', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const rules = await svc.listRules(c.env.DB, tenantId);
    return c.json({ success: true, data: rules });
  } catch (err) {
    console.error('[schemaValidation GET /rules]', err);
    return c.json({ success: false, error: 'Failed to list schema rules' }, 500);
  }
});

/**
 * POST /v1/schema-validation/rules — Create a new schema rule for the authenticated tenant
 * Body: { endpoint_pattern, schema_json, validation_mode? }
 */
tenantApiSchemaValidation.post('/rules', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();

    if (!body.endpoint_pattern || !body.schema_json) {
      return c.json({ success: false, error: 'endpoint_pattern and schema_json are required' }, 400);
    }

    const rule = await svc.createRule(c.env.DB, {
      id: crypto.randomUUID(),
      tenant_id: tenantId,
      endpoint_pattern: body.endpoint_pattern,
      schema_json: typeof body.schema_json === 'string'
        ? body.schema_json
        : JSON.stringify(body.schema_json),
      validation_mode: body.validation_mode,
    });
    return c.json({ success: true, data: rule }, 201);
  } catch (err) {
    console.error('[schemaValidation POST /rules]', err);
    return c.json({ success: false, error: 'Failed to create schema rule' }, 500);
  }
});

/**
 * GET /v1/schema-validation/violations — Recent violations for the authenticated tenant
 * Query param: limit (default 50, max 200)
 */
tenantApiSchemaValidation.get('/violations', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = parseInt(c.req.query('limit') ?? '50', 10) || 50;
    const violations = await svc.getViolations(c.env.DB, tenantId, limit);
    return c.json({ success: true, data: violations });
  } catch (err) {
    console.error('[schemaValidation GET /violations]', err);
    return c.json({ success: false, error: 'Failed to fetch violations' }, 500);
  }
});

/**
 * GET /v1/schema-validation/admin/overview — Cross-tenant rule + violation summary
 * Requires X-Admin-Key header
 */
tenantApiSchemaValidation.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
      return c.json({ success: false, error: 'Forbidden' }, 403);
    }
    const overview = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch (err) {
    console.error('[schemaValidation GET /admin/overview]', err);
    return c.json({ success: false, error: 'Failed to fetch admin overview' }, 500);
  }
});
