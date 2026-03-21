/**
 * Mission Timeline Service — track granular execution events and trace summaries
 * Supports: startTrace, addEvent, completeTrace, getTimeline, getTrace, getTenantTraces, getPerformanceStats
 */

import type { D1Database } from '@cloudflare/workers-types';

// Valid event types for mission execution tracing
export type EventType =
  | 'queued'
  | 'started'
  | 'step_begin'
  | 'step_complete'
  | 'llm_call'
  | 'tool_call'
  | 'error'
  | 'completed'
  | 'failed';

export interface TimelineEvent {
  id?: number;
  mission_id: number;
  tenant_id: string;
  event_type: EventType;
  event_data: Record<string, unknown>;
  duration_ms?: number;
  created_at?: string;
}

export interface MissionTrace {
  id?: number;
  mission_id: number;
  tenant_id: string;
  trace_id: string;
  total_duration_ms?: number;
  step_count: number;
  status: 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
}

export interface PerfStats {
  total_missions: number;
  avg_duration_ms: number;
  p95_duration_ms: number;
  success_rate: number;
  step_distribution: Record<string, number>;
}

export interface GetTenantTracesOpts {
  status?: string;
  limit?: number;
}

export class MissionTimelineService {
  /**
   * Create a new trace for a mission with a generated trace_id
   */
  async startTrace(db: D1Database, missionId: number, tenantId: string): Promise<MissionTrace> {
    const traceId = crypto.randomUUID();

    await db
      .prepare(
        `INSERT INTO mission_traces (mission_id, tenant_id, trace_id, step_count, status, started_at)
         VALUES (?, ?, ?, 0, 'running', datetime('now'))`
      )
      .bind(missionId, tenantId, traceId)
      .run();

    const row = await db
      .prepare('SELECT * FROM mission_traces WHERE mission_id = ?')
      .bind(missionId)
      .first<MissionTrace>();

    if (!row) throw new Error(`Failed to create trace for mission ${missionId}`);
    return row;
  }

  /**
   * Insert a timeline event and increment trace step_count
   */
  async addEvent(
    db: D1Database,
    missionId: number,
    tenantId: string,
    event: Omit<TimelineEvent, 'mission_id' | 'tenant_id'>
  ): Promise<void> {
    const eventDataJson = JSON.stringify(event.event_data ?? {});

    await db
      .prepare(
        `INSERT INTO mission_timeline_events (mission_id, tenant_id, event_type, event_data, duration_ms)
         VALUES (?, ?, ?, ?, ?)`
      )
      .bind(missionId, tenantId, event.event_type, eventDataJson, event.duration_ms ?? null)
      .run();

    // Increment step_count on the associated trace
    await db
      .prepare(
        `UPDATE mission_traces SET step_count = step_count + 1
         WHERE mission_id = ?`
      )
      .bind(missionId)
      .run();
  }

  /**
   * Mark trace as completed or failed, set timestamps and total_duration_ms
   */
  async completeTrace(
    db: D1Database,
    missionId: number,
    status: 'completed' | 'failed'
  ): Promise<void> {
    await db
      .prepare(
        `UPDATE mission_traces
         SET status = ?,
             completed_at = datetime('now'),
             total_duration_ms = CAST(
               (julianday(datetime('now')) - julianday(started_at)) * 86400000 AS INTEGER
             )
         WHERE mission_id = ?`
      )
      .bind(status, missionId)
      .run();
  }

  /**
   * Get all timeline events for a mission ordered by created_at
   */
  async getTimeline(
    db: D1Database,
    missionId: number,
    tenantId: string
  ): Promise<TimelineEvent[]> {
    const result = await db
      .prepare(
        `SELECT id, mission_id, tenant_id, event_type, event_data, duration_ms, created_at
         FROM mission_timeline_events
         WHERE mission_id = ? AND tenant_id = ?
         ORDER BY created_at ASC`
      )
      .bind(missionId, tenantId)
      .all<TimelineEvent & { event_data: string }>();

    // Parse JSON event_data stored as TEXT in D1
    return result.results.map((row) => ({
      ...row,
      event_data: parseJson(row.event_data, {}),
    }));
  }

  /**
   * Get trace summary for a mission
   */
  async getTrace(db: D1Database, missionId: number): Promise<MissionTrace | null> {
    return db
      .prepare('SELECT * FROM mission_traces WHERE mission_id = ?')
      .bind(missionId)
      .first<MissionTrace>();
  }

  /**
   * List traces for a tenant with optional status filter and limit
   */
  async getTenantTraces(
    db: D1Database,
    tenantId: string,
    opts: GetTenantTracesOpts = {}
  ): Promise<MissionTrace[]> {
    const limit = Math.min(opts.limit ?? 20, 100);
    let query = 'SELECT * FROM mission_traces WHERE tenant_id = ?';
    const bindings: unknown[] = [tenantId];

    if (opts.status) {
      query += ' AND status = ?';
      bindings.push(opts.status);
    }

    query += ' ORDER BY started_at DESC LIMIT ?';
    bindings.push(limit);

    const result = await db
      .prepare(query)
      .bind(...bindings)
      .all<MissionTrace>();

    return result.results;
  }

  /**
   * Compute performance stats for a tenant over the last N days
   * Returns avg duration, p95 duration, success rate, step distribution
   */
  async getPerformanceStats(
    db: D1Database,
    tenantId: string,
    days: number
  ): Promise<PerfStats> {
    const since = `datetime('now', '-${Math.max(1, days)} days')`;

    // Aggregate stats from completed/failed traces
    const stats = await db
      .prepare(
        `SELECT
           COUNT(*) as total_missions,
           AVG(total_duration_ms) as avg_duration_ms,
           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count
         FROM mission_traces
         WHERE tenant_id = ?
           AND started_at >= ${since}
           AND status IN ('completed', 'failed')`
      )
      .bind(tenantId)
      .first<{ total_missions: number; avg_duration_ms: number; completed_count: number }>();

    const total = stats?.total_missions ?? 0;
    const completed = stats?.completed_count ?? 0;
    const avgDuration = Math.round(stats?.avg_duration_ms ?? 0);
    const successRate = total > 0 ? Math.round((completed / total) * 100) / 100 : 0;

    // P95 via offset on sorted durations
    let p95 = 0;
    if (total > 0) {
      const p95Offset = Math.max(0, Math.ceil(total * 0.95) - 1);
      const p95Row = await db
        .prepare(
          `SELECT total_duration_ms FROM mission_traces
           WHERE tenant_id = ?
             AND started_at >= ${since}
             AND status IN ('completed', 'failed')
             AND total_duration_ms IS NOT NULL
           ORDER BY total_duration_ms ASC
           LIMIT 1 OFFSET ?`
        )
        .bind(tenantId, p95Offset)
        .first<{ total_duration_ms: number }>();
      p95 = p95Row?.total_duration_ms ?? 0;
    }

    // Step distribution: bucket by step_count ranges
    const stepRows = await db
      .prepare(
        `SELECT
           CASE
             WHEN step_count <= 5  THEN '1-5'
             WHEN step_count <= 10 THEN '6-10'
             WHEN step_count <= 20 THEN '11-20'
             ELSE '21+'
           END as bucket,
           COUNT(*) as cnt
         FROM mission_traces
         WHERE tenant_id = ?
           AND started_at >= ${since}
         GROUP BY bucket`
      )
      .bind(tenantId)
      .all<{ bucket: string; cnt: number }>();

    const stepDistribution: Record<string, number> = {};
    for (const row of stepRows.results) {
      stepDistribution[row.bucket] = row.cnt;
    }

    return {
      total_missions: total,
      avg_duration_ms: avgDuration,
      p95_duration_ms: p95,
      success_rate: successRate,
      step_distribution: stepDistribution,
    };
  }
}

// Safe JSON parse with fallback
function parseJson<T>(value: unknown, fallback: T): T {
  if (typeof value !== 'string') return fallback;
  try {
    return JSON.parse(value) as T;
  } catch {
    return fallback;
  }
}
