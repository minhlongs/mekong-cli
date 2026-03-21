/**
 * Onboarding V2 — autoSeedDefaults
 * Seeds: notification preferences, retention policy, SLO error budget
 * Separated to keep onboarding-v2-service.ts under 200 lines.
 */

import type { D1Database } from '@cloudflare/workers-types';
import { logEvent } from './onboarding-v2-helpers';

/** Seed default notification prefs, retention policies, SLOs for a new tenant */
export async function autoSeedDefaults(
  db: D1Database,
  tenantId: string,
): Promise<{ seeded: string[] }> {
  const seeded: string[] = [];

  // Default notification preferences (email on mission complete)
  const prefExists = await db
    .prepare('SELECT 1 FROM notification_preferences WHERE tenant_id = ?')
    .bind(tenantId)
    .first();
  if (!prefExists) {
    await db
      .prepare(
        `INSERT OR IGNORE INTO notification_preferences
         (id, tenant_id, channel, event_type, enabled, created_at)
         VALUES (?, ?, 'email', 'mission_complete', 1, datetime('now'))`,
      )
      .bind(crypto.randomUUID(), tenantId)
      .run();
    seeded.push('notification_preferences');
  }

  // Default retention policy (90 days for missions)
  const retentionExists = await db
    .prepare(`SELECT 1 FROM retention_policies WHERE tenant_id = ? AND data_type = 'missions'`)
    .bind(tenantId)
    .first();
  if (!retentionExists) {
    await db
      .prepare(
        `INSERT OR IGNORE INTO retention_policies
         (id, tenant_id, data_type, retention_days, auto_purge, archive_before_purge, is_active, created_at, updated_at)
         VALUES (?, ?, 'missions', 90, 0, 0, 1, datetime('now'), datetime('now'))`,
      )
      .bind(crypto.randomUUID(), tenantId)
      .run();
    seeded.push('retention_policy');
  }

  // Default SLO — 99% uptime over 30-day window
  const sloExists = await db
    .prepare(`SELECT 1 FROM error_budgets WHERE tenant_id = ? LIMIT 1`)
    .bind(tenantId)
    .first();
  if (!sloExists) {
    await db
      .prepare(
        `INSERT OR IGNORE INTO error_budgets
         (id, tenant_id, service_name, slo_target, window_days, created_at)
         VALUES (?, ?, 'api', 99.0, 30, datetime('now'))`,
      )
      .bind(crypto.randomUUID(), tenantId)
      .run();
    seeded.push('slo');
  }

  await logEvent(db, tenantId, 'system', 'defaults_seeded', { seeded });
  return { seeded };
}
