// Admin Tenant Management Service — notes, tags, and risk scoring for tenants
import type { D1Database } from '@cloudflare/workers-types';

// --- Notes ---

/** Add a note to a tenant */
export async function addNote(
  db: D1Database,
  tenantId: string,
  author: string,
  content: string,
  noteType = 'general',
  isPinned = false
): Promise<unknown> {
  return db.prepare(
    `INSERT INTO tenant_notes (tenant_id, author, content, note_type, is_pinned)
     VALUES (?, ?, ?, ?, ?) RETURNING *`
  ).bind(tenantId, author, content, noteType, isPinned ? 1 : 0).first();
}

/** List notes for a tenant, pinned first then newest */
export async function listNotes(
  db: D1Database,
  tenantId: string,
  noteType?: string
): Promise<unknown[]> {
  const conditions = ['tenant_id = ?'];
  const binds: unknown[] = [tenantId];

  if (noteType) { conditions.push('note_type = ?'); binds.push(noteType); }

  const where = conditions.join(' AND ');
  const rows = await db.prepare(
    `SELECT * FROM tenant_notes WHERE ${where} ORDER BY is_pinned DESC, created_at DESC`
  ).bind(...binds).all();
  return rows.results;
}

/** Delete a note by ID (must belong to tenant) */
export async function deleteNote(
  db: D1Database,
  tenantId: string,
  noteId: string
): Promise<boolean> {
  const r = await db.prepare(
    `DELETE FROM tenant_notes WHERE id = ? AND tenant_id = ?`
  ).bind(noteId, tenantId).run();
  return (r.meta?.changes ?? 0) > 0;
}

// --- Tags ---

/** Add a tag to a tenant (idempotent via UNIQUE index) */
export async function addTag(
  db: D1Database,
  tenantId: string,
  tag: string,
  color = '#6366f1'
): Promise<unknown> {
  return db.prepare(
    `INSERT INTO tenant_tags (tenant_id, tag, color)
     VALUES (?, ?, ?)
     ON CONFLICT(tenant_id, tag) DO UPDATE SET color = excluded.color
     RETURNING *`
  ).bind(tenantId, tag.toLowerCase().trim(), color).first();
}

/** List all tags for a tenant */
export async function listTags(db: D1Database, tenantId: string): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM tenant_tags WHERE tenant_id = ? ORDER BY tag ASC`
  ).bind(tenantId).all();
  return rows.results;
}

/** Remove a tag by ID (must belong to tenant) */
export async function removeTag(
  db: D1Database,
  tenantId: string,
  tagId: string
): Promise<boolean> {
  const r = await db.prepare(
    `DELETE FROM tenant_tags WHERE id = ? AND tenant_id = ?`
  ).bind(tagId, tenantId).run();
  return (r.meta?.changes ?? 0) > 0;
}

// --- Risk Scores ---

interface RiskFactors {
  daysSinceLastActivity?: number;
  missedPayments?: number;
  apiErrorRate?: number;
  requestVolumeDrop?: number;
}

/** Compute risk scores from tenant activity signals */
export async function calculateRiskScore(
  db: D1Database,
  tenantId: string
): Promise<unknown> {
  // Pull basic tenant signals from existing tables
  const [tenant, recentUsage] = await Promise.all([
    db.prepare(`SELECT * FROM tenants WHERE id = ?`).bind(tenantId).first<Record<string, unknown>>(),
    db.prepare(
      `SELECT COUNT(*) as calls, SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as errors
       FROM api_usage_logs WHERE tenant_id = ? AND created_at >= datetime('now', '-30 days')`
    ).bind(tenantId).first<{ calls: number; errors: number }>(),
  ]);

  if (!tenant) throw new Error('Tenant not found');

  const calls = recentUsage?.calls ?? 0;
  const errors = recentUsage?.errors ?? 0;
  const apiErrorRate = calls > 0 ? (errors / calls) * 100 : 0;

  // Heuristic scoring (0-100, higher churn_risk = worse)
  const churnRisk = Math.min(100, apiErrorRate * 2 + (calls === 0 ? 40 : 0));
  const healthScore = Math.max(0, 100 - churnRisk);
  const engagementScore = Math.min(100, calls > 0 ? Math.min(100, calls / 10) : 10);
  const paymentReliability = 100; // extend with billing table when available

  const factors: RiskFactors = { apiErrorRate: Math.round(apiErrorRate * 10) / 10 };

  await db.prepare(
    `INSERT INTO tenant_risk_scores
       (tenant_id, churn_risk, health_score, engagement_score, payment_reliability, last_calculated_at, factors)
     VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
     ON CONFLICT(tenant_id) DO UPDATE SET
       churn_risk = excluded.churn_risk,
       health_score = excluded.health_score,
       engagement_score = excluded.engagement_score,
       payment_reliability = excluded.payment_reliability,
       last_calculated_at = excluded.last_calculated_at,
       factors = excluded.factors,
       updated_at = datetime('now')`
  ).bind(tenantId, churnRisk, healthScore, engagementScore, paymentReliability, JSON.stringify(factors)).run();

  return db.prepare(`SELECT * FROM tenant_risk_scores WHERE tenant_id = ?`).bind(tenantId).first();
}

/** Get existing risk score for a tenant */
export async function getRiskScore(db: D1Database, tenantId: string): Promise<unknown | null> {
  return db.prepare(`SELECT * FROM tenant_risk_scores WHERE tenant_id = ?`).bind(tenantId).first();
}

/** List tenants with churn_risk above threshold, ordered by highest risk first */
export async function listAtRiskTenants(
  db: D1Database,
  threshold = 50,
  limit = 50
): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT trs.*, t.name as tenant_name, t.plan as tenant_plan
     FROM tenant_risk_scores trs
     LEFT JOIN tenants t ON t.id = trs.tenant_id
     WHERE trs.churn_risk >= ?
     ORDER BY trs.churn_risk DESC
     LIMIT ?`
  ).bind(threshold, Math.min(limit, 200)).all();
  return rows.results;
}

/** Admin dashboard: counts, at-risk summary, tag cloud */
export async function getAdminTenantDashboard(db: D1Database): Promise<unknown> {
  const [totalNotes, pinnedNotes, totalTags, atRisk, avgHealth] = await Promise.all([
    db.prepare(`SELECT COUNT(*) as count FROM tenant_notes`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM tenant_notes WHERE is_pinned = 1`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM tenant_tags`).first<{ count: number }>(),
    db.prepare(
      `SELECT COUNT(*) as count FROM tenant_risk_scores WHERE churn_risk >= 50`
    ).first<{ count: number }>(),
    db.prepare(
      `SELECT AVG(health_score) as avg FROM tenant_risk_scores`
    ).first<{ avg: number }>(),
  ]);

  return {
    notes: { total: totalNotes?.count ?? 0, pinned: pinnedNotes?.count ?? 0 },
    tags: { total: totalTags?.count ?? 0 },
    risk: { atRiskCount: atRisk?.count ?? 0, avgHealthScore: Math.round((avgHealth?.avg ?? 100) * 10) / 10 },
  };
}
