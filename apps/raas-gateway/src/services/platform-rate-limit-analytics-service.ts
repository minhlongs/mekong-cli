/**
 * Platform Rate Limit Analytics Service — event recording, abuse detection, throttle history
 *
 * Functions: recordEvent, getEvents, listAbuse, createAbuse, resolveAbuse,
 *            getThrottleHistory, recordThrottleSnapshot, getTopThrottled,
 *            getTenantRateLimitStats, getAdminOverview
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface RateLimitEvent {
  id: string;
  tenant_id: string;
  endpoint: string;
  ip_address?: string;
  action: string;
  remaining?: number;
  limit_value?: number;
  window_seconds?: number;
  created_at: string;
}

export interface AbuseDetection {
  id: string;
  tenant_id?: string;
  ip_address: string;
  detection_type: string;
  severity: string;
  details_json: string;
  resolved: number;
  detected_at: string;
  resolved_at?: string;
}

export interface ThrottleHistory {
  id: string;
  tenant_id: string;
  period: string;
  total_requests: number;
  throttled_requests: number;
  unique_ips: number;
  top_endpoints_json: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Events
// ---------------------------------------------------------------------------

export async function recordEvent(
  db: any,
  data: Omit<RateLimitEvent, 'id' | 'created_at'>
): Promise<void> {
  await db
    .prepare(
      `INSERT INTO rate_limit_events
         (id, tenant_id, endpoint, ip_address, action, remaining, limit_value, window_seconds)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
    )
    .bind(
      crypto.randomUUID(),
      data.tenant_id,
      data.endpoint,
      data.ip_address ?? null,
      data.action ?? 'throttled',
      data.remaining ?? null,
      data.limit_value ?? null,
      data.window_seconds ?? null
    )
    .run();
}

export async function getEvents(
  db: any,
  tenantId: string,
  filters?: { endpoint?: string; action?: string; limit?: number }
): Promise<RateLimitEvent[]> {
  const limit = Math.min(filters?.limit ?? 50, 200);
  const conditions: string[] = ['tenant_id = ?'];
  const binds: unknown[] = [tenantId];

  if (filters?.endpoint) { conditions.push('endpoint = ?'); binds.push(filters.endpoint); }
  if (filters?.action)   { conditions.push('action = ?');   binds.push(filters.action); }

  const { results } = await db
    .prepare(
      `SELECT * FROM rate_limit_events WHERE ${conditions.join(' AND ')}
       ORDER BY created_at DESC LIMIT ?`
    )
    .bind(...binds, limit)
    .all();
  return (results as RateLimitEvent[]);
}

// ---------------------------------------------------------------------------
// Abuse detections
// ---------------------------------------------------------------------------

export async function listAbuse(
  db: any,
  filters?: { ip_address?: string; detection_type?: string; severity?: string; resolved?: number }
): Promise<AbuseDetection[]> {
  const conditions: string[] = ['1=1'];
  const binds: unknown[] = [];

  if (filters?.ip_address)     { conditions.push('ip_address = ?');     binds.push(filters.ip_address); }
  if (filters?.detection_type) { conditions.push('detection_type = ?'); binds.push(filters.detection_type); }
  if (filters?.severity)       { conditions.push('severity = ?');       binds.push(filters.severity); }
  if (filters?.resolved !== undefined) { conditions.push('resolved = ?'); binds.push(filters.resolved); }

  const { results } = await db
    .prepare(`SELECT * FROM abuse_detections WHERE ${conditions.join(' AND ')} ORDER BY detected_at DESC LIMIT 100`)
    .bind(...binds)
    .all();
  return (results as AbuseDetection[]);
}

export async function createAbuse(
  db: any,
  data: Omit<AbuseDetection, 'id' | 'resolved' | 'detected_at' | 'resolved_at'>
): Promise<string> {
  const id = crypto.randomUUID();
  await db
    .prepare(
      `INSERT INTO abuse_detections
         (id, tenant_id, ip_address, detection_type, severity, details_json)
       VALUES (?, ?, ?, ?, ?, ?)`
    )
    .bind(
      id,
      data.tenant_id ?? null,
      data.ip_address,
      data.detection_type ?? 'brute_force',
      data.severity ?? 'medium',
      data.details_json ?? '{}'
    )
    .run();
  return id;
}

export async function resolveAbuse(db: any, id: string): Promise<void> {
  await db
    .prepare(
      `UPDATE abuse_detections SET resolved = 1, resolved_at = CURRENT_TIMESTAMP WHERE id = ?`
    )
    .bind(id)
    .run();
}

// ---------------------------------------------------------------------------
// Throttle history
// ---------------------------------------------------------------------------

export async function getThrottleHistory(db: any, tenantId: string): Promise<ThrottleHistory[]> {
  const { results } = await db
    .prepare('SELECT * FROM throttle_history WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 90')
    .bind(tenantId)
    .all();
  return (results as ThrottleHistory[]);
}

export async function recordThrottleSnapshot(
  db: any,
  tenantId: string,
  data: Omit<ThrottleHistory, 'id' | 'tenant_id' | 'created_at'>
): Promise<void> {
  await db
    .prepare(
      `INSERT INTO throttle_history
         (id, tenant_id, period, total_requests, throttled_requests, unique_ips, top_endpoints_json)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    )
    .bind(
      crypto.randomUUID(),
      tenantId,
      data.period,
      data.total_requests ?? 0,
      data.throttled_requests ?? 0,
      data.unique_ips ?? 0,
      data.top_endpoints_json ?? '[]'
    )
    .run();
}

// ---------------------------------------------------------------------------
// Aggregates
// ---------------------------------------------------------------------------

export async function getTopThrottled(
  db: any
): Promise<{ endpoint: string; throttle_count: number }[]> {
  const { results } = await db
    .prepare(
      `SELECT endpoint, COUNT(*) as throttle_count FROM rate_limit_events
       WHERE action = 'throttled' GROUP BY endpoint ORDER BY throttle_count DESC LIMIT 20`
    )
    .all();
  return (results as { endpoint: string; throttle_count: number }[]);
}

export async function getTenantRateLimitStats(
  db: any,
  tenantId: string
): Promise<{ total_events: number; throttled: number; throttle_rate: number; latest_event: string | null }> {
  const row = await db
    .prepare(
      `SELECT
         COUNT(*) as total_events,
         SUM(CASE WHEN action = 'throttled' THEN 1 ELSE 0 END) as throttled,
         MAX(created_at) as latest_event
       FROM rate_limit_events WHERE tenant_id = ?`
    )
    .bind(tenantId)
    .first() as { total_events: number; throttled: number; latest_event: string | null } | null;
  const total = row?.total_events ?? 0;
  const throttled = row?.throttled ?? 0;
  return {
    total_events: total,
    throttled,
    throttle_rate: total > 0 ? Math.round((throttled / total) * 10000) / 100 : 0,
    latest_event: row?.latest_event ?? null,
  };
}

export async function getAdminOverview(db: any): Promise<{
  total_events: number;
  total_throttled: number;
  open_abuse_detections: number;
  top_abusive_ips: { ip_address: string; count: number }[];
}> {
  const [eventsRow, abuseRow, topIps] = await Promise.all([
    db
      .prepare(
        `SELECT COUNT(*) as total_events,
                SUM(CASE WHEN action = 'throttled' THEN 1 ELSE 0 END) as total_throttled
         FROM rate_limit_events`
      )
      .first() as Promise<{ total_events: number; total_throttled: number } | null>,
    db
      .prepare(`SELECT COUNT(*) as open_count FROM abuse_detections WHERE resolved = 0`)
      .first() as Promise<{ open_count: number } | null>,
    db
      .prepare(
        `SELECT ip_address, COUNT(*) as count FROM rate_limit_events
         WHERE ip_address IS NOT NULL GROUP BY ip_address ORDER BY count DESC LIMIT 10`
      )
      .all() as Promise<{ results: { ip_address: string; count: number }[] }>,
  ]);
  return {
    total_events: eventsRow?.total_events ?? 0,
    total_throttled: eventsRow?.total_throttled ?? 0,
    open_abuse_detections: abuseRow?.open_count ?? 0,
    top_abusive_ips: topIps.results,
  };
}

export const platformRateLimitAnalyticsService = {
  recordEvent,
  getEvents,
  listAbuse,
  createAbuse,
  resolveAbuse,
  getThrottleHistory,
  recordThrottleSnapshot,
  getTopThrottled,
  getTenantRateLimitStats,
  getAdminOverview,
};
