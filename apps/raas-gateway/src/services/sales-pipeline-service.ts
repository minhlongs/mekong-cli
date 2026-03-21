/**
 * Sales Pipeline Service — CRM lead management, scoring, forecasting
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface SalesLead {
  id: string;
  company_name: string;
  contact_name?: string;
  contact_email?: string;
  stage: string;
  source: string;
  score: number;
  estimated_arr: number;
  notes?: string;
  assigned_to?: string;
  next_action?: string;
  next_action_date?: string;
  converted_tenant_id?: string;
  lost_reason?: string;
  created_at: string;
  updated_at: string;
}

export interface SalesActivity {
  id: string;
  lead_id: string;
  activity_type: string;
  description?: string;
  outcome?: string;
  created_at: string;
}

export interface LeadFilters {
  stage?: string;
  source?: string;
  min_score?: number;
}

const STAGE_WEIGHTS: Record<string, number> = {
  prospect: 0.10,
  qualified: 0.25,
  demo: 0.50,
  proposal: 0.70,
  negotiation: 0.90,
  closed_won: 1.0,
  closed_lost: 0,
};

export async function createLead(db: D1Database, data: Partial<SalesLead> & { company_name: string }): Promise<SalesLead> {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();

  await db.prepare(`
    INSERT INTO sales_leads
      (id, company_name, contact_name, contact_email, stage, source, score, estimated_arr, notes, assigned_to, next_action, next_action_date, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    id, data.company_name, data.contact_name ?? null, data.contact_email ?? null,
    data.stage ?? 'prospect', data.source ?? 'inbound',
    data.estimated_arr ?? 0, data.notes ?? null, data.assigned_to ?? null,
    data.next_action ?? null, data.next_action_date ?? null, now, now
  ).run();

  const lead = await db.prepare('SELECT * FROM sales_leads WHERE id = ?').bind(id).first<SalesLead>();
  if (!lead) throw new Error('Failed to create lead');
  return scoreLead(db, id);
}

export async function updateStage(db: D1Database, leadId: string, newStage: string, notes?: string): Promise<SalesLead> {
  const now = new Date().toISOString();
  const lead = await db.prepare('SELECT * FROM sales_leads WHERE id = ?').bind(leadId).first<SalesLead>();
  if (!lead) throw new Error('Lead not found');

  await db.prepare(`UPDATE sales_leads SET stage = ?, updated_at = ? WHERE id = ?`)
    .bind(newStage, now, leadId).run();
  await db.prepare(`
    INSERT INTO sales_activities (id, lead_id, activity_type, description, created_at)
    VALUES (?, ?, 'stage_change', ?, ?)
  `).bind(crypto.randomUUID(), leadId, `Stage changed: ${lead.stage} → ${newStage}${notes ? '. ' + notes : ''}`, now).run();

  const updated = await db.prepare('SELECT * FROM sales_leads WHERE id = ?').bind(leadId).first<SalesLead>();
  return updated!;
}

export async function scoreLead(db: D1Database, leadId: string): Promise<SalesLead> {
  const lead = await db.prepare('SELECT * FROM sales_leads WHERE id = ?').bind(leadId).first<SalesLead>();
  if (!lead) throw new Error('Lead not found');

  let score = 0;
  if (lead.contact_email) score += 20;
  if (lead.company_name) score += 20;
  if (lead.source === 'referral') score += 30;
  if (lead.estimated_arr > 1000) score += 20;
  if (lead.next_action) score += 10;

  await db.prepare('UPDATE sales_leads SET score = ?, updated_at = ? WHERE id = ?')
    .bind(score, new Date().toISOString(), leadId).run();

  return { ...lead, score };
}

export async function getPipeline(db: D1Database): Promise<Record<string, { count: number; total_arr: number; leads: SalesLead[] }>> {
  const leads = await db.prepare('SELECT * FROM sales_leads ORDER BY score DESC').all<SalesLead>();
  const pipeline: Record<string, { count: number; total_arr: number; leads: SalesLead[] }> = {};

  for (const stage of Object.keys(STAGE_WEIGHTS)) {
    pipeline[stage] = { count: 0, total_arr: 0, leads: [] };
  }

  for (const lead of leads.results) {
    const s = pipeline[lead.stage];
    if (s) {
      s.count++;
      s.total_arr += lead.estimated_arr ?? 0;
      s.leads.push(lead);
    }
  }

  return pipeline;
}

export async function getForecast(db: D1Database): Promise<{ total_pipeline: number; weighted_forecast: number; by_stage: Record<string, { arr: number; weighted: number }> }> {
  const leads = await db.prepare(
    `SELECT stage, COALESCE(SUM(estimated_arr), 0) as total_arr FROM sales_leads WHERE stage NOT IN ('closed_lost') GROUP BY stage`
  ).all<{ stage: string; total_arr: number }>();

  let totalPipeline = 0;
  let weightedForecast = 0;
  const byStage: Record<string, { arr: number; weighted: number }> = {};

  for (const row of leads.results) {
    const weight = STAGE_WEIGHTS[row.stage] ?? 0;
    const weighted = row.total_arr * weight;
    totalPipeline += row.total_arr;
    weightedForecast += weighted;
    byStage[row.stage] = { arr: row.total_arr, weighted };
  }

  return { total_pipeline: totalPipeline, weighted_forecast: weightedForecast, by_stage: byStage };
}

export async function getActivities(db: D1Database, leadId: string): Promise<SalesActivity[]> {
  const result = await db.prepare(
    'SELECT * FROM sales_activities WHERE lead_id = ? ORDER BY created_at DESC'
  ).bind(leadId).all<SalesActivity>();
  return result.results;
}

export async function listLeads(db: D1Database, filters?: LeadFilters): Promise<SalesLead[]> {
  let query = 'SELECT * FROM sales_leads WHERE 1=1';
  const params: (string | number)[] = [];

  if (filters?.stage) { query += ' AND stage = ?'; params.push(filters.stage); }
  if (filters?.source) { query += ' AND source = ?'; params.push(filters.source); }
  if (filters?.min_score !== undefined) { query += ' AND score >= ?'; params.push(filters.min_score); }

  query += ' ORDER BY score DESC, created_at DESC';

  const result = await db.prepare(query).bind(...params).all<SalesLead>();
  return result.results;
}

export async function updateLead(db: D1Database, leadId: string, data: Partial<SalesLead>): Promise<SalesLead> {
  const lead = await db.prepare('SELECT * FROM sales_leads WHERE id = ?').bind(leadId).first<SalesLead>();
  if (!lead) throw new Error('Lead not found');

  const now = new Date().toISOString();
  const fields = ['company_name', 'contact_name', 'contact_email', 'source', 'estimated_arr', 'notes', 'assigned_to', 'next_action', 'next_action_date', 'lost_reason', 'converted_tenant_id'] as const;
  const setClauses: string[] = ['updated_at = ?'];
  const values: unknown[] = [now];

  for (const field of fields) {
    if (field in data) { setClauses.push(`${field} = ?`); values.push(data[field] ?? null); }
  }

  values.push(leadId);
  await db.prepare(`UPDATE sales_leads SET ${setClauses.join(', ')} WHERE id = ?`).bind(...values).run();

  return scoreLead(db, leadId);
}

export async function addActivity(db: D1Database, leadId: string, data: { activity_type: string; description?: string; outcome?: string }): Promise<SalesActivity> {
  const lead = await db.prepare('SELECT id FROM sales_leads WHERE id = ?').bind(leadId).first();
  if (!lead) throw new Error('Lead not found');

  const id = crypto.randomUUID();
  const now = new Date().toISOString();

  await db.prepare(`
    INSERT INTO sales_activities (id, lead_id, activity_type, description, outcome, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `).bind(id, leadId, data.activity_type, data.description ?? null, data.outcome ?? null, now).run();

  return { id, lead_id: leadId, activity_type: data.activity_type, description: data.description, outcome: data.outcome, created_at: now };
}
