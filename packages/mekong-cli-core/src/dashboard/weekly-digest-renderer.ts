/** Weekly digest Markdown, CLI renderers, and data loader helpers */
import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import chalk from 'chalk';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { CrmStore } from '../crm/store.js';
import type { CrmSummary } from '../crm/types.js';
import type { WeeklyDigest } from './types.js';

export interface SopWeeklyMetrics {
  runsTotal?: number;
  successRate?: number;
  avgDuration?: number;
  topSOPs?: Array<{ name: string; runs: number; avgTime: number }>;
  agentTokensUsed?: number;
  agentCostTotal?: number;
}

export async function loadSopWeeklyMetrics(sopMetricsPath: string): Promise<SopWeeklyMetrics> {
  if (!existsSync(sopMetricsPath)) return {};
  try {
    const raw = await readFile(sopMetricsPath, 'utf-8');
    return JSON.parse(raw) as SopWeeklyMetrics;
  } catch {
    return {};
  }
}

export async function buildWeeklyCrmSummary(
  crm: CrmStore,
  from: string,
  to: string,
): Promise<Result<CrmSummary>> {
  try {
    const [leadsResult, customersResult, ticketsResult] = await Promise.all([
      crm.getAll('leads'),
      crm.getAll('customers'),
      crm.getAll('tickets'),
    ]);
    if (!leadsResult.ok) return err(leadsResult.error);
    if (!customersResult.ok) return err(customersResult.error);
    if (!ticketsResult.ok) return err(ticketsResult.error);

    const leads = leadsResult.value;
    const customers = customersResult.value;
    const tickets = ticketsResult.value;

    const newLeads = leads.filter((l) => l.createdAt >= from && l.createdAt <= to);
    const activeCustomers = customers.filter((c) => c.status === 'active');
    const churnedThisMonth = customers.filter(
      (c) => c.churnedAt && c.churnedAt >= from && c.churnedAt <= to,
    );
    const openTickets = tickets.filter((t) => t.status === 'open' || t.status === 'in_progress');
    const resolvedTickets = tickets.filter((t) => t.resolvedAt);
    const avgResolutionMs =
      resolvedTickets.length > 0
        ? resolvedTickets.reduce(
            (sum, t) => sum + (new Date(t.resolvedAt!).getTime() - new Date(t.createdAt).getTime()),
            0,
          ) / resolvedTickets.length
        : 0;

    return ok({
      totalLeads: leads.length,
      newLeadsThisWeek: newLeads.length,
      totalCustomers: customers.length,
      activeCustomers: activeCustomers.length,
      churnedThisMonth: churnedThisMonth.length,
      openTickets: openTickets.length,
      avgResolutionTimeHours: Math.round((avgResolutionMs / 3_600_000) * 10) / 10,
      pipeline: [],
      mrr: activeCustomers.reduce((s, c) => s + c.mrr, 0),
      mrrGrowthPercent: 0,
    });
  } catch (e) {
    return err(e instanceof Error ? e : new Error(String(e)));
  }
}

export function renderWeeklyDigestMarkdown(digest: WeeklyDigest): string {
  const arrow = (n: number) => (n >= 0 ? `+${n.toFixed(1)}%` : `${n.toFixed(1)}%`);
  return [
    `# Weekly Business Digest — ${digest.week}`,
    `**Period:** ${digest.period.from} → ${digest.period.to}`,
    '',
    '## Financial Summary',
    `| Metric | Value | vs Last Week |`,
    `|--------|-------|--------------|`,
    `| Revenue | $${digest.financial.revenue.total.toFixed(2)} | ${arrow(digest.comparison.revenueVsLastWeek)} |`,
    `| Expenses | $${digest.financial.expenses.total.toFixed(2)} | ${arrow(digest.comparison.expensesVsLastWeek)} |`,
    `| MRR | $${digest.financial.revenue.mrr.toFixed(2)} | — |`,
    `| Profit Margin | ${digest.financial.profit.margin.toFixed(1)}% | — |`,
    `| Runway | ${digest.financial.runway.months} months | — |`,
    '',
    '## CRM',
    `| Metric | Value |`,
    `|--------|-------|`,
    `| Active Customers | ${digest.crm.activeCustomers} |`,
    `| Open Tickets | ${digest.crm.openTickets} |`,
    `| Avg Resolution | ${digest.crm.avgResolutionTimeHours.toFixed(1)}h |`,
    '',
    '## Operations',
    `- SOP runs: **${digest.operations.sopRunsTotal}** (${digest.operations.sopSuccessRate.toFixed(1)}% success)`,
    `- Avg SOP duration: ${digest.operations.avgSopDuration.toFixed(0)}s`,
    `- Agent tokens: ${digest.operations.agentTokensUsed.toLocaleString()}`,
    `- Agent cost: $${digest.operations.agentCostTotal.toFixed(2)}`,
    '',
    '## Highlights',
    ...digest.highlights.map((h) => `- ${h}`),
    '',
    '## Recommendations',
    ...digest.recommendations.map((r) => `- ${r}`),
    '',
  ].join('\n');
}

export function renderWeeklyDigestCli(digest: WeeklyDigest): string {
  const arrow = (n: number) =>
    n >= 0 ? chalk.green(`+${n.toFixed(1)}%`) : chalk.red(`${n.toFixed(1)}%`);
  const lines: string[] = [];
  lines.push(chalk.bold.cyan(`\n  WEEKLY DIGEST — ${digest.week}`));
  lines.push(chalk.gray(`  ${digest.period.from} → ${digest.period.to}`));
  lines.push(chalk.gray('  ' + '─'.repeat(48)));

  lines.push(chalk.bold('\n  FINANCIAL'));
  lines.push(`    Revenue:  ${chalk.white('$' + digest.financial.revenue.total.toFixed(2))} ${arrow(digest.comparison.revenueVsLastWeek)}`);
  lines.push(`    Expenses: ${chalk.white('$' + digest.financial.expenses.total.toFixed(2))} ${arrow(digest.comparison.expensesVsLastWeek)}`);
  lines.push(`    MRR:      ${chalk.white('$' + digest.financial.revenue.mrr.toFixed(2))}`);
  lines.push(`    Margin:   ${chalk.white(digest.financial.profit.margin.toFixed(1) + '%')}`);

  lines.push(chalk.bold('\n  CRM'));
  lines.push(`    Customers: ${chalk.white(String(digest.crm.activeCustomers))} active ${arrow(digest.comparison.customersVsLastWeek)}`);
  lines.push(`    Tickets:   ${chalk.white(String(digest.crm.openTickets))} open`);

  if (digest.highlights.length > 0) {
    lines.push(chalk.bold('\n  HIGHLIGHTS'));
    for (const h of digest.highlights) {
      lines.push(chalk.white(`    • ${h}`));
    }
  }

  if (digest.recommendations.length > 0) {
    lines.push(chalk.bold('\n  RECOMMENDATIONS'));
    for (const r of digest.recommendations) {
      lines.push(chalk.yellow(`    → ${r}`));
    }
  }

  lines.push('');
  return lines.join('\n');
}
