/**
 * Sales Pipeline Routes — admin-only CRM API for leads, deals, and forecasting
 * All endpoints require X-Admin-Key header
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import * as svc from '../services/sales-pipeline-service';

export const salesPipeline = new Hono<{ Bindings: Env }>();

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  const key = c.req.header('X-Admin-Key');
  return Boolean(c.env.ADMIN_API_KEY && key === c.env.ADMIN_API_KEY);
}

function unauthorized(): Response {
  return json({ error: 'Unauthorized' }, { status: 401 });
}

// POST /admin/sales/leads — create lead
salesPipeline.post('/leads', async (c) => {
  if (!isAdmin(c)) return unauthorized();
  try {
    const body = await c.req.json<{ company_name?: string } & Record<string, unknown>>();
    if (!body.company_name) return json({ error: 'company_name required' }, { status: 400 });
    const lead = await svc.createLead(c.env.DB, body as Parameters<typeof svc.createLead>[1]);
    return json({ lead }, { status: 201 });
  } catch (e) {
    return json({ error: String(e) }, { status: 500 });
  }
});

// GET /admin/sales/leads — list leads with optional filters
salesPipeline.get('/leads', async (c) => {
  if (!isAdmin(c)) return unauthorized();
  try {
    const stage = c.req.query('stage');
    const source = c.req.query('source');
    const minScore = c.req.query('min_score');
    const filters: svc.LeadFilters = {};
    if (stage) filters.stage = stage;
    if (source) filters.source = source;
    if (minScore) filters.min_score = parseInt(minScore, 10);
    const leads = await svc.listLeads(c.env.DB, filters);
    return json({ leads, total: leads.length });
  } catch (e) {
    return json({ error: String(e) }, { status: 500 });
  }
});

// GET /admin/sales/leads/:id — get lead details + activities
salesPipeline.get('/leads/:id', async (c) => {
  if (!isAdmin(c)) return unauthorized();
  try {
    const id = c.req.param('id');
    const leads = await svc.listLeads(c.env.DB);
    const lead = leads.find((l) => l.id === id);
    if (!lead) return json({ error: 'Lead not found' }, { status: 404 });
    const activities = await svc.getActivities(c.env.DB, id);
    return json({ lead, activities });
  } catch (e) {
    return json({ error: String(e) }, { status: 500 });
  }
});

// PUT /admin/sales/leads/:id/stage — update lead stage
salesPipeline.put('/leads/:id/stage', async (c) => {
  if (!isAdmin(c)) return unauthorized();
  try {
    const id = c.req.param('id');
    const body = await c.req.json<{ stage?: string; notes?: string }>();
    if (!body.stage) return json({ error: 'stage required' }, { status: 400 });
    const lead = await svc.updateStage(c.env.DB, id, body.stage, body.notes);
    return json({ lead });
  } catch (e) {
    const msg = String(e);
    return json({ error: msg }, { status: msg.includes('not found') ? 404 : 500 });
  }
});

// PUT /admin/sales/leads/:id — update lead details
salesPipeline.put('/leads/:id', async (c) => {
  if (!isAdmin(c)) return unauthorized();
  try {
    const id = c.req.param('id');
    const body = await c.req.json<Partial<svc.SalesLead>>();
    const lead = await svc.updateLead(c.env.DB, id, body);
    return json({ lead });
  } catch (e) {
    const msg = String(e);
    return json({ error: msg }, { status: msg.includes('not found') ? 404 : 500 });
  }
});

// GET /admin/sales/pipeline — pipeline view grouped by stage
salesPipeline.get('/pipeline', async (c) => {
  if (!isAdmin(c)) return unauthorized();
  try {
    const pipeline = await svc.getPipeline(c.env.DB);
    return json({ pipeline });
  } catch (e) {
    return json({ error: String(e) }, { status: 500 });
  }
});

// GET /admin/sales/forecast — weighted revenue forecast
salesPipeline.get('/forecast', async (c) => {
  if (!isAdmin(c)) return unauthorized();
  try {
    const forecast = await svc.getForecast(c.env.DB);
    return json({ forecast });
  } catch (e) {
    return json({ error: String(e) }, { status: 500 });
  }
});

// POST /admin/sales/leads/:id/activities — add activity to lead
salesPipeline.post('/leads/:id/activities', async (c) => {
  if (!isAdmin(c)) return unauthorized();
  try {
    const id = c.req.param('id');
    const body = await c.req.json<{ activity_type?: string; description?: string; outcome?: string }>();
    if (!body.activity_type) return json({ error: 'activity_type required' }, { status: 400 });
    const activity = await svc.addActivity(c.env.DB, id, body as { activity_type: string; description?: string; outcome?: string });
    return json({ activity }, { status: 201 });
  } catch (e) {
    const msg = String(e);
    return json({ error: msg }, { status: msg.includes('not found') ? 404 : 500 });
  }
});
