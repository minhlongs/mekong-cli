/**
 * Tenant IP Geolocation Service — lookup, geo-fencing rules, access control, analytics
 * Used by tenant-ip-geolocation route (auth + admin protected)
 */

type DB = any;

interface GeoRuleData {
  rule_type?: string;
  country_codes_json?: string;
  description?: string;
  enabled?: number;
}

/** Get cached geolocation for an IP, null if not cached */
async function getCachedLookup(db: DB, ip: string) {
  return db.prepare('SELECT * FROM ip_geolocation_cache WHERE ip_address = ?').bind(ip).first();
}

/** Lookup IP geolocation — returns cache hit or minimal record with ip only */
async function lookupIp(db: DB, ip: string) {
  const cached = await getCachedLookup(db, ip);
  if (cached) return { ...cached, source: 'cache' };

  // Store minimal record — real geo data would come from an external provider
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db
    .prepare(
      `INSERT INTO ip_geolocation_cache (id, ip_address, cached_at)
       VALUES (?, ?, ?)
       ON CONFLICT(ip_address) DO UPDATE SET cached_at = excluded.cached_at`
    )
    .bind(id, ip, now)
    .run();

  return { id, ip_address: ip, cached_at: now, source: 'new' };
}

/** List all geo-fencing rules for a tenant */
async function listGeoRules(db: DB, tenantId: string) {
  const { results } = await db
    .prepare('SELECT * FROM geo_fencing_rules WHERE tenant_id = ? ORDER BY created_at DESC')
    .bind(tenantId)
    .all();
  return { rules: results, total: results.length };
}

/** Create a new geo-fencing rule for a tenant */
async function createGeoRule(db: DB, tenantId: string, data: GeoRuleData) {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db
    .prepare(
      `INSERT INTO geo_fencing_rules (id, tenant_id, rule_type, country_codes_json, description, enabled, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    )
    .bind(
      id,
      tenantId,
      data.rule_type ?? 'allow',
      data.country_codes_json ?? '[]',
      data.description ?? null,
      data.enabled ?? 1,
      now
    )
    .run();
  return db.prepare('SELECT * FROM geo_fencing_rules WHERE id = ?').bind(id).first();
}

/** Update an existing geo-fencing rule (tenant-scoped) */
async function updateGeoRule(db: DB, tenantId: string, id: string, data: GeoRuleData) {
  const existing = await db
    .prepare('SELECT * FROM geo_fencing_rules WHERE id = ? AND tenant_id = ?')
    .bind(id, tenantId)
    .first();
  if (!existing) return null;

  const rule_type = data.rule_type ?? existing.rule_type;
  const country_codes_json = data.country_codes_json ?? existing.country_codes_json;
  const description = data.description ?? existing.description;
  const enabled = data.enabled ?? existing.enabled;

  await db
    .prepare(
      `UPDATE geo_fencing_rules
       SET rule_type = ?, country_codes_json = ?, description = ?, enabled = ?
       WHERE id = ? AND tenant_id = ?`
    )
    .bind(rule_type, country_codes_json, description, enabled, id, tenantId)
    .run();
  return db.prepare('SELECT * FROM geo_fencing_rules WHERE id = ?').bind(id).first();
}

/** Delete a geo-fencing rule (tenant-scoped) */
async function deleteGeoRule(db: DB, tenantId: string, id: string) {
  const existing = await db
    .prepare('SELECT id FROM geo_fencing_rules WHERE id = ? AND tenant_id = ?')
    .bind(id, tenantId)
    .first();
  if (!existing) return false;
  await db.prepare('DELETE FROM geo_fencing_rules WHERE id = ? AND tenant_id = ?').bind(id, tenantId).run();
  return true;
}

/** Check if an IP/country is allowed under tenant geo-fencing rules; logs result */
async function checkAccess(db: DB, tenantId: string, ip: string, countryCode: string) {
  const { results: rules } = await db
    .prepare(
      'SELECT * FROM geo_fencing_rules WHERE tenant_id = ? AND enabled = 1 ORDER BY created_at ASC'
    )
    .bind(tenantId)
    .all();

  let action = 'allowed';
  let matchedRuleId: string | null = null;

  for (const rule of rules) {
    let codes: string[] = [];
    try { codes = JSON.parse(rule.country_codes_json || '[]'); } catch { codes = []; }
    if (codes.includes(countryCode)) {
      action = rule.rule_type === 'deny' ? 'denied' : 'allowed';
      matchedRuleId = rule.id;
      break;
    }
  }

  await db
    .prepare(
      `INSERT INTO geo_access_logs (id, tenant_id, ip_address, country_code, action, rule_id, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    )
    .bind(crypto.randomUUID(), tenantId, ip, countryCode, action, matchedRuleId, new Date().toISOString())
    .run();

  return { ip, country_code: countryCode, action, rule_id: matchedRuleId };
}

/** Get recent access logs for a tenant */
async function getAccessLogs(db: DB, tenantId: string) {
  const { results } = await db
    .prepare(
      'SELECT * FROM geo_access_logs WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 100'
    )
    .bind(tenantId)
    .all();
  return { logs: results, total: results.length };
}

/** Analytics: access summary by country and action for a tenant */
async function getGeoAnalytics(db: DB, tenantId: string) {
  const [byCountry, byAction] = await Promise.all([
    db
      .prepare(
        `SELECT country_code, COUNT(*) as count FROM geo_access_logs WHERE tenant_id = ? GROUP BY country_code ORDER BY count DESC LIMIT 20`
      )
      .bind(tenantId)
      .all(),
    db
      .prepare(
        `SELECT action, COUNT(*) as count FROM geo_access_logs WHERE tenant_id = ? GROUP BY action`
      )
      .bind(tenantId)
      .all(),
  ]);
  return { by_country: byCountry.results, by_action: byAction.results };
}

/** Admin overview: top IPs, rule counts, total logs across all tenants */
async function getAdminOverview(db: DB) {
  const [totalLogs, totalRules, topCountries] = await Promise.all([
    db.prepare('SELECT COUNT(*) as total FROM geo_access_logs').first(),
    db.prepare('SELECT COUNT(*) as total FROM geo_fencing_rules').first(),
    db
      .prepare(
        `SELECT country_code, COUNT(*) as count FROM geo_access_logs GROUP BY country_code ORDER BY count DESC LIMIT 10`
      )
      .all(),
  ]);
  return {
    total_logs: totalLogs?.total ?? 0,
    total_rules: totalRules?.total ?? 0,
    top_countries: topCountries.results,
  };
}

export const tenantIpGeolocationService = {
  lookupIp,
  getCachedLookup,
  listGeoRules,
  createGeoRule,
  updateGeoRule,
  deleteGeoRule,
  checkAccess,
  getAccessLogs,
  getGeoAnalytics,
  getAdminOverview,
};
