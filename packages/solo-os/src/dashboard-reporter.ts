/**
 * DashboardReporter — aggregates pipeline runs into daily summaries and weekly markdown reports.
 */

import type { PipelineRun, DailySummary } from './types.js';

/** Map pipeline ids to business metric categories */
const LEAD_PIPELINE_IDS = new Set(['daily-lead-scan']);
const CONTENT_PIPELINE_IDS = new Set(['content-batch']);
const SUPPORT_PIPELINE_IDS = new Set(['support-triage']);

export class DashboardReporter {
  /**
   * Aggregate a list of completed pipeline runs into a single daily summary.
   * Filters to runs completed on the summary date (YYYY-MM-DD).
   */
  generateDailySummary(runs: PipelineRun[], dailyCreditBudget = 100): DailySummary {
    const date = new Date().toISOString().split('T')[0];
    const completed = runs.filter((r) => r.status === 'completed');

    const creditsUsed = completed.reduce((sum, r) => sum + r.creditsUsed, 0);

    return {
      date,
      leadsGenerated: completed.filter((r) => LEAD_PIPELINE_IDS.has(r.pipelineId)).length,
      contentPublished: completed.filter((r) => CONTENT_PIPELINE_IDS.has(r.pipelineId)).length,
      ticketsResolved: completed.filter((r) => SUPPORT_PIPELINE_IDS.has(r.pipelineId)).length,
      creditsUsed,
      creditsRemaining: Math.max(0, dailyCreditBudget - creditsUsed),
    };
  }

  /**
   * Produce a markdown weekly report from an array of daily summaries.
   * Includes totals table and per-day breakdown.
   */
  generateWeeklyReport(summaries: DailySummary[]): string {
    if (summaries.length === 0) return '# Weekly Report\n\nNo data available.\n';

    const totals = summaries.reduce(
      (acc, s) => ({
        leadsGenerated: acc.leadsGenerated + s.leadsGenerated,
        contentPublished: acc.contentPublished + s.contentPublished,
        ticketsResolved: acc.ticketsResolved + s.ticketsResolved,
        creditsUsed: acc.creditsUsed + s.creditsUsed,
      }),
      { leadsGenerated: 0, contentPublished: 0, ticketsResolved: 0, creditsUsed: 0 },
    );

    const startDate = summaries[0].date;
    const endDate = summaries[summaries.length - 1].date;

    const rows = summaries
      .map(
        (s) =>
          `| ${s.date} | ${s.leadsGenerated} | ${s.contentPublished} | ${s.ticketsResolved} | ${s.creditsUsed} |`,
      )
      .join('\n');

    return [
      `# Weekly Report: ${startDate} — ${endDate}`,
      '',
      '## Totals',
      `- Leads generated: **${totals.leadsGenerated}**`,
      `- Content published: **${totals.contentPublished}**`,
      `- Tickets resolved: **${totals.ticketsResolved}**`,
      `- Credits used: **${totals.creditsUsed}**`,
      '',
      '## Daily Breakdown',
      '| Date | Leads | Content | Tickets | Credits |',
      '|------|-------|---------|---------|---------|',
      rows,
    ].join('\n');
  }
}
