/**
 * Onboarding V2 Admin Functions — completion rate + dropoff analysis
 * Used by admin-only routes; separated to keep service file under 200 lines.
 */

import type { D1Database } from '@cloudflare/workers-types';

/** Admin: % of tenants who completed onboarding */
export async function getCompletionRate(
  db: D1Database,
): Promise<{ total: number; completed: number; rate_pct: number }> {
  const total =
    (await db.prepare('SELECT COUNT(*) as n FROM onboarding_flows').first<{ n: number }>())?.n ?? 0;
  const completed =
    (
      await db
        .prepare(`SELECT COUNT(*) as n FROM onboarding_flows WHERE status = 'completed'`)
        .first<{ n: number }>()
    )?.n ?? 0;
  return { total, completed, rate_pct: total ? Math.round((completed / total) * 100) : 0 };
}

/** Admin: steps with highest skip counts — proxy for abandonment */
export async function getDropoffAnalysis(
  db: D1Database,
): Promise<{ step: string; skips: number; total_flows: number; dropoff_pct: number }[]> {
  const total =
    (await db.prepare('SELECT COUNT(*) as n FROM onboarding_flows').first<{ n: number }>())?.n ?? 1;

  const { results } = await db
    .prepare(
      `SELECT step, COUNT(*) as skips FROM onboarding_events
       WHERE action = 'skipped' GROUP BY step ORDER BY skips DESC`,
    )
    .all<{ step: string; skips: number }>();

  return results.map((r) => ({
    step: r.step,
    skips: r.skips,
    total_flows: total,
    dropoff_pct: Math.round((r.skips / total) * 100),
  }));
}
