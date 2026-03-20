import { Hono } from 'hono';
import { cors } from 'hono/cors';

interface Env {
  DB: D1Database;
  ASSETS: Fetcher;
}

export const api = new Hono<{ Bindings: Env }>();

api.use('/*', cors());

// GET /api/leads - List all leads
api.get('/leads', async (c) => {
  const { results } = await c.env.DB.prepare(
    'SELECT * FROM leads ORDER BY created_at DESC'
  ).all();
  return c.json(results);
});

// GET /api/leads/:id - Get single lead
api.get('/leads/:id', async (c) => {
  const id = c.req.param('id');
  const { results } = await c.env.DB.prepare(
    'SELECT * FROM leads WHERE id = ?'
  ).bind(id).all();

  if (!results || results.length === 0) {
    return c.json({ error: 'Lead not found' }, 404);
  }
  return c.json(results[0]);
});

// POST /api/leads - Create lead
api.post('/leads', async (c) => {
  const body = await c.req.json();
  const { company_name, contact_name, email, phone, stage, estimated_value, probability, notes } = body;

  if (!company_name) {
    return c.json({ error: 'company_name is required' }, 400);
  }

  const id = crypto.randomUUID();
  const now = new Date().toISOString();

  await c.env.DB.prepare(`
    INSERT INTO leads (id, company_name, contact_name, email, phone, stage, estimated_value, probability, notes, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    id, company_name, contact_name || null, email || null, phone || null,
    stage || 'new', estimated_value || 0, probability || 0, notes || null, now, now
  ).run();

  const { results } = await c.env.DB.prepare('SELECT * FROM leads WHERE id = ?').bind(id).all();
  return c.json(results[0], 201);
});

// PUT /api/leads/:id - Update lead
api.put('/leads/:id', async (c) => {
  const id = c.req.param('id');
  const body = await c.req.json();
  const now = new Date().toISOString();

  const fields: string[] = [];
  const values: any[] = [];

  const updatableFields = ['company_name', 'contact_name', 'email', 'phone', 'stage', 'estimated_value', 'probability', 'notes', 'last_contact_date', 'next_followup_date'];

  for (const field of updatableFields) {
    if (field in body) {
      fields.push(`${field} = ?`);
      values.push(body[field]);
    }
  }

  if (fields.length === 0) {
    return c.json({ error: 'No fields to update' }, 400);
  }

  fields.push('updated_at = ?');
  values.push(now);
  values.push(id);

  await c.env.DB.prepare(`
    UPDATE leads SET ${fields.join(', ')} WHERE id = ?
  `).bind(...values).run();

  const { results } = await c.env.DB.prepare('SELECT * FROM leads WHERE id = ?').bind(id).all();
  return c.json(results[0]);
});

// DELETE /api/leads/:id - Delete lead
api.delete('/leads/:id', async (c) => {
  const id = c.req.param('id');
  await c.env.DB.prepare('DELETE FROM leads WHERE id = ?').bind(id).run();
  return c.json({ success: true });
});

// GET /api/leads/:id/activities - Get lead activities
api.get('/leads/:id/activities', async (c) => {
  const leadId = c.req.param('id');
  const { results } = await c.env.DB.prepare(
    'SELECT * FROM activities WHERE lead_id = ? ORDER BY created_at DESC'
  ).bind(leadId).all();
  return c.json(results);
});

// POST /api/activities - Create activity
api.post('/activities', async (c) => {
  const body = await c.req.json();
  const { lead_id, activity_type, description } = body;

  if (!lead_id || !activity_type || !description) {
    return c.json({ error: 'lead_id, activity_type, and description are required' }, 400);
  }

  const id = crypto.randomUUID();
  const now = new Date().toISOString();

  await c.env.DB.prepare(`
    INSERT INTO activities (id, lead_id, activity_type, description, created_at)
    VALUES (?, ?, ?, ?, ?)
  `).bind(id, lead_id, activity_type, description, now).run();

  // Update lead's last_contact_date
  await c.env.DB.prepare(`
    UPDATE leads SET last_contact_date = ? WHERE id = ?
  `).bind(now, lead_id).run();

  const { results } = await c.env.DB.prepare('SELECT * FROM activities WHERE id = ?').bind(id).all();
  return c.json(results[0], 201);
});

// GET /api/pipeline - Get pipeline summary
api.get('/pipeline', async (c) => {
  const stages = ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost'];
  const pipeline: any[] = [];

  for (const stage of stages) {
    const { results } = await c.env.DB.prepare(`
      SELECT
        COUNT(*) as count,
        COALESCE(SUM(estimated_value), 0) as total_value,
        COALESCE(SUM(estimated_value * probability / 100), 0) as weighted_value
      FROM leads WHERE stage = ?
    `).bind(stage).all();

    pipeline.push({
      stage,
      count: results[0].count,
      total_value: results[0].total_value,
      weighted_value: results[0].weighted_value,
    });
  }

  return c.json(pipeline);
});
