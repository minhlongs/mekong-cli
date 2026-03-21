/**
 * Tenant Portal Service — self-service account, usage, billing, plan management
 */

// D1Database is provided by @cloudflare/workers-types (ambient)

/** Tier feature definitions */
const TIER_FEATURES: Record<string, { credits: number; price: number; features: string[] }> = {
  starter: { credits: 200, price: 49, features: ['5 API keys', 'Email support', '50 missions/day'] },
  pro: { credits: 1000, price: 149, features: ['20 API keys', 'Priority support', '200 missions/day', 'Webhooks'] },
  agency: { credits: 3000, price: 299, features: ['50 API keys', 'Dedicated support', '500 missions/day', 'Webhooks', 'Team members'] },
  master: { credits: 10000, price: 499, features: ['100 API keys', '24/7 support', '2000 missions/day', 'All features', 'Custom models'] },
  enterprise: { credits: -1, price: 999, features: ['Unlimited', 'SLA', 'Unlimited missions', 'All features', 'Custom models', 'SSO'] },
};

const TIER_ORDER = ['starter', 'pro', 'agency', 'master', 'enterprise'];

/** Account overview — tenant info, tier, credits, members, missions, age */
export async function getAccountOverview(db: D1Database, tenantId: string) {
  const [tenant, memberCount, activeMissions] = await Promise.all([
    db.prepare(
      `SELECT id, name, email, tier, credits, created_at FROM tenants WHERE id = ?`
    ).bind(tenantId).first<{ id: string; name: string; email: string; tier: string; credits: number; created_at: string }>(),
    db.prepare(
      `SELECT COUNT(*) as count FROM team_members WHERE tenant_id = ? AND status = 'active'`
    ).bind(tenantId).first<{ count: number }>(),
    db.prepare(
      `SELECT COUNT(*) as count FROM missions WHERE tenant_id = ? AND status IN ('queued','running')`
    ).bind(tenantId).first<{ count: number }>(),
  ]);

  if (!tenant) throw new Error('Tenant not found');

  const accountAge = Math.floor(
    (Date.now() - new Date(tenant.created_at).getTime()) / (1000 * 60 * 60 * 24)
  );

  return {
    id: tenant.id,
    name: tenant.name,
    email: tenant.email,
    tier: tenant.tier,
    credits_remaining: tenant.credits,
    member_count: memberCount?.count ?? 0,
    active_missions: activeMissions?.count ?? 0,
    account_age_days: accountAge,
  };
}

/** Usage summary grouped by period (day/week/month) */
export async function getUsageSummary(
  db: D1Database,
  tenantId: string,
  period: 'day' | 'week' | 'month' = 'month'
) {
  const intervalMap = { day: '-1 day', week: '-7 days', month: '-30 days' };
  const since = intervalMap[period];

  const [missionStats, creditStats, topModels] = await Promise.all([
    db.prepare(
      `SELECT COUNT(*) as count, AVG(latency_ms) as avg_latency
       FROM missions WHERE tenant_id = ? AND created_at > datetime('now', ?)`
    ).bind(tenantId, since).first<{ count: number; avg_latency: number | null }>(),
    db.prepare(
      `SELECT SUM(ABS(amount)) as credits_used
       FROM credit_transactions
       WHERE tenant_id = ? AND amount < 0 AND created_at > datetime('now', ?)`
    ).bind(tenantId, since).first<{ credits_used: number | null }>(),
    db.prepare(
      `SELECT model, COUNT(*) as count FROM missions
       WHERE tenant_id = ? AND model IS NOT NULL AND created_at > datetime('now', ?)
       GROUP BY model ORDER BY count DESC LIMIT 5`
    ).bind(tenantId, since).all(),
  ]);

  return {
    period,
    missions_count: missionStats?.count ?? 0,
    credits_used: creditStats?.credits_used ?? 0,
    avg_latency_ms: Math.round(missionStats?.avg_latency ?? 0),
    top_models: topModels.results ?? [],
  };
}

/** Billing history — last N invoices/credit transactions */
export async function getBillingHistory(db: D1Database, tenantId: string, limit = 20) {
  const rows = await db.prepare(
    `SELECT id, amount, type, description, created_at
     FROM credit_transactions
     WHERE tenant_id = ? AND amount > 0
     ORDER BY created_at DESC LIMIT ?`
  ).bind(tenantId, limit).all();

  return (rows.results ?? []).map((r: any) => ({
    id: r.id,
    amount: r.amount,
    type: r.type,
    description: r.description,
    date: r.created_at,
    status: 'completed',
  }));
}

/** Current plan details + available upgrades */
export async function getCurrentPlan(db: D1Database, tenantId: string) {
  const [tenant, subscription] = await Promise.all([
    db.prepare(`SELECT tier FROM tenants WHERE id = ?`).bind(tenantId).first<{ tier: string }>(),
    db.prepare(
      `SELECT current_period_end, status FROM subscriptions
       WHERE tenant_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1`
    ).bind(tenantId).first<{ current_period_end: string; status: string }>(),
  ]);

  const tier = tenant?.tier ?? 'starter';
  const tierConfig = TIER_FEATURES[tier];
  const tierIndex = TIER_ORDER.indexOf(tier);

  const upgrades = TIER_ORDER.slice(tierIndex + 1).map((t) => ({
    tier: t,
    ...TIER_FEATURES[t],
  }));

  return {
    current_tier: tier,
    credits_per_month: tierConfig?.credits ?? 200,
    price_per_month: tierConfig?.price ?? 49,
    features: tierConfig?.features ?? [],
    renewal_date: subscription?.current_period_end ?? null,
    subscription_status: subscription?.status ?? 'inactive',
    available_upgrades: upgrades,
  };
}

/** Request plan change — auto-approve upgrades, queue downgrades */
export async function requestPlanChange(
  db: D1Database,
  tenantId: string,
  newTier: string,
  reason?: string
) {
  const tenant = await db.prepare(`SELECT tier FROM tenants WHERE id = ?`)
    .bind(tenantId).first<{ tier: string }>();

  if (!tenant) throw new Error('Tenant not found');

  const currentIndex = TIER_ORDER.indexOf(tenant.tier);
  const newIndex = TIER_ORDER.indexOf(newTier);
  const isUpgrade = newIndex > currentIndex;
  const id = crypto.randomUUID();

  await db.prepare(
    `INSERT INTO plan_change_requests
     (id, tenant_id, current_tier, requested_tier, reason, status, auto_approved, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))`
  ).bind(id, tenantId, tenant.tier, newTier, reason ?? null, isUpgrade ? 'approved' : 'pending', isUpgrade ? 1 : 0).run();

  if (isUpgrade) {
    await db.prepare(
      `UPDATE tenants SET tier = ?, updated_at = datetime('now') WHERE id = ?`
    ).bind(newTier, tenantId).run();
  }

  return {
    request_id: id,
    current_tier: tenant.tier,
    requested_tier: newTier,
    status: isUpgrade ? 'approved' : 'pending',
    auto_approved: isUpgrade,
    message: isUpgrade
      ? `Upgraded to ${newTier} immediately`
      : `Downgrade to ${newTier} queued for admin review`,
  };
}

/** API keys summary — counts, last used dates */
export async function getApiKeysSummary(db: D1Database, tenantId: string) {
  const rows = await db.prepare(
    `SELECT
       SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_count,
       SUM(CASE WHEN status = 'revoked' THEN 1 ELSE 0 END) as revoked_count,
       MAX(CASE WHEN status = 'active' THEN last_used_at END) as last_active_used,
       MAX(last_used_at) as last_used_overall
     FROM api_keys WHERE tenant_id = ?`
  ).bind(tenantId).first<any>();

  return {
    active_count: rows?.active_count ?? 0,
    revoked_count: rows?.revoked_count ?? 0,
    last_active_used: rows?.last_active_used ?? null,
    last_used_overall: rows?.last_used_overall ?? null,
  };
}

/** Get notification settings for tenant */
export async function getNotificationSettings(db: D1Database, tenantId: string) {
  const row = await db.prepare(
    `SELECT billing_alerts, usage_warnings, product_updates, weekly_digest
     FROM tenant_notification_settings WHERE tenant_id = ?`
  ).bind(tenantId).first<any>();

  // Return defaults if not configured yet
  return {
    billing_alerts: row ? Boolean(row.billing_alerts) : true,
    usage_warnings: row ? Boolean(row.usage_warnings) : true,
    product_updates: row ? Boolean(row.product_updates) : true,
    weekly_digest: row ? Boolean(row.weekly_digest) : false,
  };
}

/** Update notification settings */
export async function updateNotificationSettings(
  db: D1Database,
  tenantId: string,
  settings: Record<string, boolean>
) {
  await db.prepare(
    `INSERT INTO tenant_notification_settings
     (tenant_id, billing_alerts, usage_warnings, product_updates, weekly_digest, updated_at)
     VALUES (?, ?, ?, ?, ?, datetime('now'))
     ON CONFLICT(tenant_id) DO UPDATE SET
       billing_alerts = excluded.billing_alerts,
       usage_warnings = excluded.usage_warnings,
       product_updates = excluded.product_updates,
       weekly_digest = excluded.weekly_digest,
       updated_at = excluded.updated_at`
  ).bind(
    tenantId,
    settings.billing_alerts ? 1 : 0,
    settings.usage_warnings ? 1 : 0,
    settings.product_updates ? 1 : 0,
    settings.weekly_digest ? 1 : 0,
  ).run();

  return { success: true, updated_at: new Date().toISOString() };
}
