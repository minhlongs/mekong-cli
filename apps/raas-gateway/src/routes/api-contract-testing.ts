/**
 * API Contract Testing routes — full CRUD + validation + breaking changes + compliance
 * All endpoints protected by X-Admin-Key header middleware
 */

import { Hono } from 'hono';
import { apiContractTestingService as svc } from '../services/api-contract-testing-service';

const app = new Hono<{
  Bindings: {
    DB: any;
    RATE_LIMIT_KV: any;
    SESSION_KV: any;
    AI: any;
    JWT_SECRET=REDACTED: string;
    POLAR_WEBHOOK_SECRET: string;
    TELEGRAM_BOT_TOKEN: string;
    ENVIRONMENT: string;
    LOG_LEVEL: string;
    ADMIN_API_KEY: string;
  };
}>();

// Admin auth middleware — all routes require X-Admin-Key
app.use('*', async (c, next) => {
  if (!c.env.ADMIN_API_KEY || c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /contracts — list with optional ?status and ?api_path filters
app.get('/contracts', async (c) => {
  const status = c.req.query('status');
  const api_path = c.req.query('api_path');
  const result = await svc.listContracts(c.env.DB, { status, api_path });
  return c.json(result);
});

// POST /contracts — create new contract
app.post('/contracts', async (c) => {
  const body = await c.req.json();
  if (!body.name || !body.api_path) {
    return c.json({ error: 'name and api_path are required' }, 400);
  }
  const contract = await svc.createContract(c.env.DB, body);
  return c.json(contract, 201);
});

// GET /contracts/:id — single contract
app.get('/contracts/:id', async (c) => {
  const contract = await svc.getContract(c.env.DB, c.req.param('id'));
  if (!contract) return c.json({ error: 'Not found' }, 404);
  return c.json(contract);
});

// PUT /contracts/:id — update contract, detects breaking changes
app.put('/contracts/:id', async (c) => {
  const body = await c.req.json();
  const contract = await svc.updateContract(c.env.DB, c.req.param('id'), body);
  if (!contract) return c.json({ error: 'Not found' }, 404);
  return c.json(contract);
});

// DELETE /contracts/:id — remove contract
app.delete('/contracts/:id', async (c) => {
  const contract = await svc.getContract(c.env.DB, c.req.param('id'));
  if (!contract) return c.json({ error: 'Not found' }, 404);
  const result = await svc.deleteContract(c.env.DB, c.req.param('id'));
  return c.json(result);
});

// POST /contracts/:id/validate — run schema validation
app.post('/contracts/:id/validate', async (c) => {
  const result = await svc.validateContract(c.env.DB, c.req.param('id'));
  if (!result) return c.json({ error: 'Not found' }, 404);
  return c.json(result);
});

// GET /contracts/:id/validations — list validation history
app.get('/contracts/:id/validations', async (c) => {
  const contract = await svc.getContract(c.env.DB, c.req.param('id'));
  if (!contract) return c.json({ error: 'Not found' }, 404);
  const result = await svc.listValidations(c.env.DB, c.req.param('id'));
  return c.json(result);
});

// GET /breaking-changes — list with optional ?severity and ?acknowledged filters
app.get('/breaking-changes', async (c) => {
  const severity = c.req.query('severity');
  const acknowledged = c.req.query('acknowledged');
  const result = await svc.listBreakingChanges(c.env.DB, { severity, acknowledged });
  return c.json(result);
});

// POST /breaking-changes/:id/acknowledge — mark breaking change as acknowledged
app.post('/breaking-changes/:id/acknowledge', async (c) => {
  const result = await svc.acknowledgeBreakingChange(c.env.DB, c.req.param('id'));
  if (!result) return c.json({ error: 'Not found' }, 404);
  return c.json(result);
});

// GET /compliance — overall contract health report
app.get('/compliance', async (c) => {
  const report = await svc.getComplianceReport(c.env.DB);
  return c.json(report);
});

// GET /dashboard — admin overview counts and compliance rate
app.get('/dashboard', async (c) => {
  const overview = await svc.getAdminOverview(c.env.DB);
  return c.json(overview);
});

export { app as apiContractTesting };
