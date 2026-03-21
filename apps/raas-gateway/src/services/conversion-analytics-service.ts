/**
 * Conversion Analytics Service — funnel tracking, cohort analysis, source attribution
 * Funnel: page_view → signup_start → signup_complete → first_mission → first_payment → subscription_active
 */

import type { D1Database } from '@cloudflare/workers-types';

export const FUNNEL_STAGES = [
  'page_view',
  'signup_start',
  'signup_complete',
  'first_mission',
  'first_payment',
  'subscription_active',
] as const;

export type FunnelStage = typeof FUNNEL_STAGES[number];

export interface ConversionEvent {
  tenant_id?: string;
  event_type: FunnelStage;
  event_data?: Record<string, unknown>;
  session_id?: string;
  source?: string;
}

export interface FunnelStep {
  stage: FunnelStage;
  count: number;
  dropoff_rate: number;
}

export interface ConversionRates {
  signup_to_mission: number;
  mission_to_payment: number;
  payment_to_subscription: number;
  overall: number;
}

export interface CohortData {
  cohort_period: string;
  tenant_count: number;
  retention: number[];
}

export interface SourceData {
  source: string;
  signups: number;
  conversions: number;
  conversion_rate: number;
}

/**
 * Insert a conversion event into the DB
 */
export async function trackEvent(db: D1Database, event: ConversionEvent): Promise<void> {
  await db
    .prepare(
      `INSERT INTO conversion_events (tenant_id, event_type, event_data, session_id, source)
       VALUES (?, ?, ?, ?, ?)`
    )
    .bind(
      event.tenant_id ?? null,
      event.event_type,
      JSON.stringify(event.event_data ?? {}),
      event.session_id ?? null,
      event.source ?? null
    )
    .run();
}

/**
 * Count distinct sessions/tenants at each funnel stage
 */
export async function getFunnel(
  db: D1Database,
  opts: { days: number; source?: string }
): Promise<FunnelStep[]> {
  const since = new Date(Date.now() - opts.days * 86400000).toISOString();

  const counts: Record<string, number> = {};

  for (const stage of FUNNEL_STAGES) {
    const sourceClause = opts.source ? `AND source = '${opts.source.replace(/'/g, "''")}'` : '';
    const row = await db
      .prepare(
        `SELECT COUNT(DISTINCT COALESCE(session_id, CAST(id AS TEXT))) as cnt
         FROM conversion_events
         WHERE event_type = ? AND created_at >= ? ${sourceClause}`
      )
      .bind(stage, since)
      .first<{ cnt: number }>();
    counts[stage] = row?.cnt ?? 0;
  }

  const topCount = counts['page_view'] || 1;
  return FUNNEL_STAGES.map((stage, idx) => {
    const prevCount = idx === 0 ? topCount : counts[FUNNEL_STAGES[idx - 1]] || 1;
    const count = counts[stage] ?? 0;
    const dropoff_rate = idx === 0 ? 0 : parseFloat(((1 - count / prevCount) * 100).toFixed(1));
    return { stage, count, dropoff_rate };
  });
}

/**
 * Calculate step-over-step conversion rates
 */
export async function getConversionRates(
  db: D1Database,
  opts: { days: number; source?: string }
): Promise<ConversionRates> {
  const steps = await getFunnel(db, opts);
  const byStage = Object.fromEntries(steps.map((s) => [s.stage, s.count]));

  const safe = (a: number, b: number) => (b > 0 ? parseFloat(((a / b) * 100).toFixed(1)) : 0);

  return {
    signup_to_mission: safe(byStage['first_mission'], byStage['signup_complete']),
    mission_to_payment: safe(byStage['first_payment'], byStage['first_mission']),
    payment_to_subscription: safe(byStage['subscription_active'], byStage['first_payment']),
    overall: safe(byStage['subscription_active'], byStage['page_view']),
  };
}

/**
 * Group tenants by signup week/month, track retention (missions created) over time
 */
export async function getCohortAnalysis(
  db: D1Database,
  opts: { period: 'week' | 'month'; cohorts: number }
): Promise<CohortData[]> {
  const fmtStr = opts.period === 'week' ? '%Y-W%W' : '%Y-%m';

  // Get cohorts: tenants grouped by signup period
  const cohortRows = await db
    .prepare(
      `SELECT strftime('${fmtStr}', created_at) as cohort_period,
              COUNT(DISTINCT tenant_id) as tenant_count
       FROM conversion_events
       WHERE event_type = 'signup_complete' AND tenant_id IS NOT NULL
       GROUP BY cohort_period
       ORDER BY cohort_period DESC
       LIMIT ?`
    )
    .bind(opts.cohorts)
    .all<{ cohort_period: string; tenant_count: number }>();

  const results: CohortData[] = [];

  for (const cohort of cohortRows.results) {
    // Count how many from this cohort had missions in each subsequent period
    const retentionRows = await db
      .prepare(
        `SELECT COUNT(DISTINCT m.tenant_id) as active
         FROM missions m
         WHERE m.tenant_id IN (
           SELECT DISTINCT tenant_id FROM conversion_events
           WHERE event_type = 'signup_complete'
             AND tenant_id IS NOT NULL
             AND strftime('${fmtStr}', created_at) = ?
         )
         AND strftime('${fmtStr}', m.created_at) >= ?`
      )
      .bind(cohort.cohort_period, cohort.cohort_period)
      .first<{ active: number }>();

    results.push({
      cohort_period: cohort.cohort_period,
      tenant_count: cohort.tenant_count,
      retention: [retentionRows?.active ?? 0],
    });
  }

  return results;
}

/**
 * Group events by source, count signups + conversions
 */
export async function getTopSources(
  db: D1Database,
  opts: { days: number; limit: number }
): Promise<SourceData[]> {
  const since = new Date(Date.now() - opts.days * 86400000).toISOString();

  const rows = await db
    .prepare(
      `SELECT
         COALESCE(source, 'direct') as source,
         COUNT(DISTINCT CASE WHEN event_type = 'signup_complete' THEN session_id END) as signups,
         COUNT(DISTINCT CASE WHEN event_type = 'subscription_active' THEN session_id END) as conversions
       FROM conversion_events
       WHERE created_at >= ?
       GROUP BY source
       ORDER BY signups DESC
       LIMIT ?`
    )
    .bind(since, opts.limit)
    .all<{ source: string; signups: number; conversions: number }>();

  return rows.results.map((r) => ({
    source: r.source,
    signups: r.signups,
    conversions: r.conversions,
    conversion_rate: r.signups > 0 ? parseFloat(((r.conversions / r.signups) * 100).toFixed(1)) : 0,
  }));
}
