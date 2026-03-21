/**
 * Customer Portal Service — overview, usage, and account settings
 */

// D1Database provided by @cloudflare/workers-types (ambient)

/** Aggregate dashboard data for tenant portal overview */
export async function getPortalOverview(db: D1Database, tenantId: string) {
  const [tenant, missionCount, apiKeys, subscription, recentActivity] = await Promise.all([
    db.prepare(
      `SELECT id, name, email, tier, credits FROM tenants WHERE id = ?`
    ).bind(tenantId).first<{ id: string; name: string; email: string; tier: string; credits: number }>(),
    db.prepare(
      `SELECT COUNT(*) as count FROM missions WHERE tenant_id = ?`
    ).bind(tenantId).first<{ count: number }>(),
    db.prepare(
      `SELECT COUNT(*) as count FROM api_keys WHERE tenant_id = ? AND status = 'active'`
    ).bind(tenantId).first<{ count: number }>(),
    db.prepare(
      `SELECT status FROM subscriptions WHERE tenant_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1`
    ).bind(tenantId).first<{ status: string }>(),
    db.prepare(
      `SELECT action, details, created_at FROM portal_activity WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 5`
    ).bind(tenantId).all(),
  ]);

  if (!tenant) throw new Error('Tenant not found');

  return {
    id: tenant.id,
    name: tenant.name,
    email: tenant.email,
    tier: tenant.tier,
    credit_balance: tenant.credits,
    total_missions: missionCount?.count ?? 0,
    active_api_keys: apiKeys?.count ?? 0,
    subscription_status: subscription?.status ?? 'inactive',
    recent_activity: recentActivity.results ?? [],
  };
}

/** Usage stats grouped by period (day/week/month) */
export async function getUsageSummary(
  db: D1Database,
  tenantId: string,
  opts: { period?: string } = {}
) {
  const validPeriods: Record<string, string> = { day: '-1 day', week: '-7 days', month: '-30 days' };
  const period = (opts.period && validPeriods[opts.period]) ? opts.period : 'month';
  const since = validPeriods[period];

  const [missions, apiCalls, credits] = await Promise.all([
    db.prepare(
      `SELECT DATE(created_at) as date, COUNT(*) as count
       FROM missions WHERE tenant_id = ? AND created_at > datetime('now', ?)
       GROUP BY DATE(created_at) ORDER BY date DESC`
    ).bind(tenantId, since).all(),
    db.prepare(
      `SELECT COUNT(*) as count FROM usage_logs WHERE tenant_id = ? AND created_at > datetime('now', ?)`
    ).bind(tenantId, since).first<{ count: number }>(),
    db.prepare(
      `SELECT SUM(ABS(amount)) as consumed FROM credit_transactions
       WHERE tenant_id = ? AND amount < 0 AND created_at > datetime('now', ?)`
    ).bind(tenantId, since).first<{ consumed: number | null }>(),
  ]);

  return {
    period,
    missions_by_day: missions.results ?? [],
    api_calls: apiCalls?.count ?? 0,
    credits_consumed: credits?.consumed ?? 0,
  };
}

/** Account settings from tenants table */
export async function getAccountSettings(db: D1Database, tenantId: string) {
  const tenant = await db.prepare(
    `SELECT id, name, email, tier, telegram_chat_id, created_at, updated_at FROM tenants WHERE id = ?`
  ).bind(tenantId).first<{
    id: string;
    name: string;
    email: string;
    tier: string;
    telegram_chat_id: string | null;
    created_at: string;
    updated_at: string;
  }>();

  if (!tenant) throw new Error('Tenant not found');
  return tenant;
}
