/**
 * Multi-Region Config Service — region-aware routing config and data residency per tenant
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface RegionConfig {
  id: string;
  tenant_id: string;
  primary_region: string;
  allowed_regions: string;
  data_residency: string;
  routing_strategy: string;
  failover_regions: string;
  is_active: number;
  created_at: string;
  updated_at: string;
}

export interface RegionEndpoint {
  id: string;
  region_code: string;
  region_name: string;
  base_url: string;
  status: string;
  latency_ms: number | null;
  last_health_at: string | null;
  created_at: string;
}

function newId(): string {
  return crypto.randomUUID();
}

/** Upsert region config for a tenant */
export async function setRegionConfig(
  db: D1Database,
  tenantId: string,
  config: { primary_region?: string; data_residency?: string; routing_strategy?: string; allowed_regions?: string[]; failover_regions?: string[] }
): Promise<RegionConfig> {
  const existing = await db.prepare(
    `SELECT id FROM region_configs WHERE tenant_id = ?`
  ).bind(tenantId).first<{ id: string }>();

  if (existing) {
    const fields: string[] = ['updated_at = datetime(\'now\')'];
    const vals: unknown[] = [];
    if (config.primary_region !== undefined) { fields.push('primary_region = ?'); vals.push(config.primary_region); }
    if (config.data_residency !== undefined) { fields.push('data_residency = ?'); vals.push(config.data_residency); }
    if (config.routing_strategy !== undefined) { fields.push('routing_strategy = ?'); vals.push(config.routing_strategy); }
    if (config.allowed_regions !== undefined) { fields.push('allowed_regions = ?'); vals.push(JSON.stringify(config.allowed_regions)); }
    if (config.failover_regions !== undefined) { fields.push('failover_regions = ?'); vals.push(JSON.stringify(config.failover_regions)); }
    vals.push(tenantId);
    await db.prepare(`UPDATE region_configs SET ${fields.join(', ')} WHERE tenant_id = ?`).bind(...vals).run();
  } else {
    const id = newId();
    await db.prepare(
      `INSERT INTO region_configs (id, tenant_id, primary_region, data_residency, routing_strategy, allowed_regions, failover_regions)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      id, tenantId,
      config.primary_region ?? 'auto',
      config.data_residency ?? 'none',
      config.routing_strategy ?? 'latency',
      JSON.stringify(config.allowed_regions ?? ['us', 'eu', 'ap']),
      JSON.stringify(config.failover_regions ?? [])
    ).run();
  }
  return getRegionConfig(db, tenantId) as Promise<RegionConfig>;
}

/** Get tenant region config */
export async function getRegionConfig(db: D1Database, tenantId: string): Promise<RegionConfig | null> {
  return db.prepare(`SELECT * FROM region_configs WHERE tenant_id = ?`).bind(tenantId).first<RegionConfig>();
}

/** List all available region endpoints */
export async function listAvailableRegions(db: D1Database): Promise<RegionEndpoint[]> {
  const { results } = await db.prepare(`SELECT * FROM region_endpoints ORDER BY region_code`).all<RegionEndpoint>();
  return results;
}

/** Add a new region endpoint */
export async function addRegionEndpoint(
  db: D1Database, regionCode: string, regionName: string, baseUrl: string
): Promise<RegionEndpoint> {
  const id = newId();
  await db.prepare(
    `INSERT INTO region_endpoints (id, region_code, region_name, base_url) VALUES (?, ?, ?, ?)
     ON CONFLICT(region_code) DO UPDATE SET region_name = excluded.region_name, base_url = excluded.base_url`
  ).bind(id, regionCode, regionName, baseUrl).run();
  return db.prepare(`SELECT * FROM region_endpoints WHERE region_code = ?`).bind(regionCode).first<RegionEndpoint>() as Promise<RegionEndpoint>;
}

/** Update health status for a region */
export async function updateRegionHealth(
  db: D1Database, regionCode: string, status: string, latencyMs?: number
): Promise<void> {
  await db.prepare(
    `UPDATE region_endpoints SET status = ?, latency_ms = ?, last_health_at = datetime('now') WHERE region_code = ?`
  ).bind(status, latencyMs ?? null, regionCode).run();
}

/** Determine optimal region for tenant based on routing_strategy */
export async function getOptimalRegion(db: D1Database, tenantId: string): Promise<RegionEndpoint | null> {
  const config = await getRegionConfig(db, tenantId);
  const strategy = config?.routing_strategy ?? 'latency';

  if (strategy === 'geo' && config?.primary_region && config.primary_region !== 'auto') {
    const region = await db.prepare(`SELECT * FROM region_endpoints WHERE region_code = ? AND status = 'active'`)
      .bind(config.primary_region).first<RegionEndpoint>();
    if (region) return region;
  }

  if (strategy === 'failover' && config?.failover_regions) {
    const codes: string[] = JSON.parse(config.failover_regions);
    for (const code of codes) {
      const region = await db.prepare(`SELECT * FROM region_endpoints WHERE region_code = ? AND status = 'active'`)
        .bind(code).first<RegionEndpoint>();
      if (region) return region;
    }
  }

  // Default: latency — pick lowest latency active region
  return db.prepare(
    `SELECT * FROM region_endpoints WHERE status = 'active' ORDER BY latency_ms ASC NULLS LAST LIMIT 1`
  ).first<RegionEndpoint>();
}

/** Get all regions with status and latency */
export async function getRegionStatus(db: D1Database): Promise<RegionEndpoint[]> {
  const { results } = await db.prepare(
    `SELECT * FROM region_endpoints ORDER BY status, latency_ms ASC`
  ).all<RegionEndpoint>();
  return results;
}

/** Set data residency constraint for a tenant */
export async function setDataResidency(db: D1Database, tenantId: string, residency: string): Promise<RegionConfig> {
  return setRegionConfig(db, tenantId, { data_residency: residency });
}

/** Seed default regions (us-east, eu-west, ap-southeast) */
export async function seedDefaultRegions(db: D1Database): Promise<void> {
  const defaults = [
    { code: 'us-east', name: 'US East', url: 'https://us-east.raas-gateway.workers.dev' },
    { code: 'eu-west', name: 'EU West', url: 'https://eu-west.raas-gateway.workers.dev' },
    { code: 'ap-southeast', name: 'Asia Pacific', url: 'https://ap-southeast.raas-gateway.workers.dev' },
  ];
  for (const r of defaults) {
    await addRegionEndpoint(db, r.code, r.name, r.url);
  }
}

/** Aggregate stats: tenant count per primary_region + avg latency per region */
export async function getRegionStats(db: D1Database): Promise<{ region: string; tenant_count: number; avg_latency: number | null }[]> {
  const { results } = await db.prepare(
    `SELECT primary_region as region, COUNT(*) as tenant_count FROM region_configs WHERE is_active = 1 GROUP BY primary_region`
  ).all<{ region: string; tenant_count: number }>();

  const { results: latencyRows } = await db.prepare(
    `SELECT region_code as region, AVG(latency_ms) as avg_latency FROM region_endpoints GROUP BY region_code`
  ).all<{ region: string; avg_latency: number | null }>();

  const latencyMap = Object.fromEntries(latencyRows.map(r => [r.region, r.avg_latency]));
  return results.map(r => ({ ...r, avg_latency: latencyMap[r.region] ?? null }));
}
