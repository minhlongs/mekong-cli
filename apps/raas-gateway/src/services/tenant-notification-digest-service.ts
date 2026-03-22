/**
 * Tenant Notification Digest Service
 * Manage per-tenant digest configs and delivery records.
 *
 * listConfigs      — list digest configs for a tenant
 * createConfig     — create a new digest config
 * getDeliveries    — list delivery records for a tenant
 * getAdminOverview — cross-tenant digest stats (admin only)
 */

interface DigestConfig {
  id: string;
  tenant_id: string;
  digest_frequency: string;
  channels_json: string;
  include_types: string;
  is_active: number;
  created_at: string;
  updated_at: string;
}

interface DigestDelivery {
  id: string;
  tenant_id: string;
  config_id: string;
  items_count: number;
  delivery_status: string;
  delivered_at: string | null;
  created_at: string;
}

/** List all digest configs for a tenant, newest first */
async function listConfigs(db: any, tenantId: string): Promise<DigestConfig[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM notification_digest_configs WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return (result.results ?? []) as DigestConfig[];
  } catch (err) {
    throw new Error(`listConfigs failed: ${(err as Error).message}`);
  }
}

/** Create a new digest config for a tenant */
async function createConfig(
  db: any,
  tenantId: string,
  data: {
    digest_frequency?: string;
    channels_json?: string;
    include_types?: string;
  }
): Promise<DigestConfig> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const digest_frequency = data.digest_frequency ?? 'daily';
    const channels_json = data.channels_json ?? '["email"]';
    const include_types = data.include_types ?? 'all';

    await db
      .prepare(
        `INSERT INTO notification_digest_configs
           (id, tenant_id, digest_frequency, channels_json, include_types, is_active, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, 1, ?, ?)`
      )
      .bind(id, tenantId, digest_frequency, channels_json, include_types, now, now)
      .run();

    return { id, tenant_id: tenantId, digest_frequency, channels_json, include_types, is_active: 1, created_at: now, updated_at: now };
  } catch (err) {
    throw new Error(`createConfig failed: ${(err as Error).message}`);
  }
}

/** List delivery records for a tenant, newest first */
async function getDeliveries(db: any, tenantId: string): Promise<DigestDelivery[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM notification_digest_deliveries WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return (result.results ?? []) as DigestDelivery[];
  } catch (err) {
    throw new Error(`getDeliveries failed: ${(err as Error).message}`);
  }
}

/** Admin overview — aggregate digest stats across all tenants */
async function getAdminOverview(db: any): Promise<{
  total_configs: number;
  active_configs: number;
  total_deliveries: number;
  tenants_with_configs: number;
}> {
  try {
    const [configs, deliveries, tenants] = await Promise.all([
      db.prepare('SELECT COUNT(*) as total, SUM(is_active) as active FROM notification_digest_configs').first(),
      db.prepare('SELECT COUNT(*) as total FROM notification_digest_deliveries').first(),
      db.prepare('SELECT COUNT(DISTINCT tenant_id) as total FROM notification_digest_configs').first(),
    ]);
    return {
      total_configs: Number(configs?.total ?? 0),
      active_configs: Number(configs?.active ?? 0),
      total_deliveries: Number(deliveries?.total ?? 0),
      tenants_with_configs: Number(tenants?.total ?? 0),
    };
  } catch (err) {
    throw new Error(`getAdminOverview failed: ${(err as Error).message}`);
  }
}

export const tenantNotificationDigestService = { listConfigs, createConfig, getDeliveries, getAdminOverview };
