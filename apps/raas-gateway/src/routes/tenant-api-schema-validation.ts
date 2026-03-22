/**
 * Tenant API Schema Validation Routes
 * Mount at: /v1/schema-validation
 *
 * GET  /schemas          — list schemas (auth)
 * POST /schemas          — create schema (auth)
 * GET  /violations       — list violations (auth)
 * GET  /admin/overview   — cross-tenant stats (X-Admin-Key)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiSchemaValidationService as svc } from '../services/tenant-api-schema-validation-service';

const app = new Hono<{ Bindings: Env }>();

// GET /schemas — list all schema definitions for the authenticated tenant
app.get('/schemas', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await svc.listSchemas(c.env.DB, tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to list schemas' }, 500);
  }
});

// POST /schemas — create a new schema definition for the authenticated tenant
// Body: { schema_name, endpoint_pattern, request_schema?, response_schema?, enabled? }
app.post('/schemas', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({})) as {
      schema_name?: string;
      endpoint_pattern?: string;
      request_schema?: string;
      response_schema?: string;
      enabled?: boolean;
    };

    if (!body.schema_name?.trim()) {
      return c.json({ error: 'schema_name is required' }, 400);
    }
    if (!body.endpoint_pattern?.trim()) {
      return c.json({ error: 'endpoint_pattern is required' }, 400);
    }

    const result = await svc.createSchema(c.env.DB, tenantId, {
      schema_name: body.schema_name.trim(),
      endpoint_pattern: body.endpoint_pattern.trim(),
      request_schema: body.request_schema,
      response_schema: body.response_schema,
      enabled: body.enabled,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch {
    return c.json({ error: 'Failed to create schema' }, 500);
  }
});

// GET /violations — recent violations for the authenticated tenant
// Query: schema_id? (filter by specific schema)
app.get('/violations', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const schemaId = c.req.query('schema_id') ?? undefined;
    const result = await svc.getViolations(c.env.DB, tenantId, schemaId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to fetch violations' }, 500);
  }
});

// GET /admin/overview — cross-tenant aggregate stats (X-Admin-Key required)
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const result = await svc.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to fetch admin overview' }, 500);
  }
});

export { app as tenantApiSchemaValidation };
