/** Weekly business summary with LLM-generated insights */
import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { format, startOfWeek, endOfWeek, subWeeks, getISOWeek, getYear } from 'date-fns';
import chalk from 'chalk';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { RevenueTracker } from '../finance/revenue.js';
import type { CrmStore } from '../crm/store.js';
import type { LlmRouter } from '../llm/router.js';
import type { WeeklyDigest } from './types.js';
import type { CrmSummary } from '../crm/types.js';

interface SopWeeklyMetrics {
  runsTotal?: number;
  successRate?: number;
  avgDuration?: number;
  topSOPs?: Array<{ name: string; runs: number; avgTime: number }>;
  agentTokensUsed?: number;
  agentCostTotal?: number;
}

export class WeeklyDigestGenerator {
  constructor(
    private revenue: RevenueTracker,
    private crm: CrmStore,
    private llm: LlmRouter,
    private sopMetricsPath: string,
  ) {}

  async generate(referenceDate: Date = new Date()): Promise<Result<WeeklyDigest>> {
    try {
      const weekStart = startOfWeek(referenceDate, { weekStartsOn: 1 });
      const weekEnd = endOfWeek(referenceDate, { weekStartsOn: 1 });
      const prevStart = startOfWeek(subWeeks(referenceDate, 1), { weekStartsOn: 1 });
      const prevEnd = endOfWeek(subWeeks(referenceDate, 1), { weekStartsOn: 1 });

      const from = format(weekStart, 'yyyy-MM-dd');
      const to = format(weekEnd, 'yyyy-MM-dd');
      const prevFrom = format(prevStart, 'yyyy-MM-dd');
      const prevTo = format(prevEnd, 'yyyy-MM-dd');

      const weekLabel = `${getYear(weekStart)}-W${String(getISOWeek(weekStart)).padStart(2, '0')}`;

      const [financialResult, prevFinancialResult, crmSummaryResult, sopMetrics] =
        await Promise.all([
          this.revenue.generateSummary(from, to),
          this.revenue.generateSummary(prevFrom, prevTo),
          this.buildCrmSummary(from, to, prevFrom, prevTo),
          this.loadSopMetrics(),
        ]);

      if (!financialResult.ok) return err(financialResult.error);
      if (!prevFinancialResult.ok) return err(prevFinancialResult.error);
      if (!crmSummaryResult.ok) return err(crmSummaryResult.error);

      const financial = financialResult.value;
      const prevFinancial = prevFinancialResult.value;
      const crmSummary = crmSummaryResult.value;

      const revenueVsLastWeek =
        prevFinancial.revenue.total > 0
          ? ((financial.revenue.total - prevFinancial.revenue.total) /
              prevFinancial.revenue.total) *
            100
          : 0;
      const expensesVsLastWeek =
        prevFinancial.expenses.total > 0
          ? ((financial.expenses.total - prevFinancial.expenses.total) /
              prevFinancial.expenses.total) *
            100
          : 0;
      const customersVsLastWeek =
        prevFinancial.customers.total > 0
          ? ((financial.customers.total - prevFinancial.customers.total) /
              prevFinancial.customers.total) *
            100
          : 0;
      const ticketsVsLastWeek = 0; // requires storing previous ticket count

      const digestData: Omit<WeeklyDigest, 'highlights' | 'recommendations'> = {
        week: weekLabel,
        period: { from, to },
        financial,
        crm: crmSummary,
        operations: {
          sopRunsTotal: sopMetrics.runsTotal ?? 0,
          sopSuccessRate: sopMetrics.successRate ?? 0,
          avgSopDuration: sopMetrics.avgDuration ?? 0,
          topSOPs: sopMetrics.topSOPs ?? [],
          agentTokensUsed: sopMetrics.agentTokensUsed ?? 0,
          agentCostTotal: sopMetrics.agentCostTotal ?? 0,
        },
        comparison: {
          revenueVsLastWeek: Math.round(revenueVsLastWeek * 100) / 100,
          expensesVsLastWeek: Math.round(expensesVsLastWeek * 100) / 100,
          customersVsLastWeek: Math.round(customersVsLastWeek * 100) / 100,
          ticketsVsLastWeek,
        },
      };

      const insightsResult = await this.generateInsights(digestData);

      return ok({
        ...digestData,
        highlights: insightsResult.ok ? insightsResult.value.highlights : [],
        recommendations: insightsResult.ok ? insightsResult.value.recommendations : [],
      });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async generateInsights(
    data: Omit<WeeklyDigest, 'highlights' | 'recommendations'>,
  ): Promise<Result<{ highlights: string[]; recommendations: string[] }>> {
    try {
      const prompt = `You are a business analyst. Analyze this weekly business data and provide:
1. 3-5 key highlights (what happened, notable metrics)
2. 2-3 actionable recommendations

Weekly data:
- Revenue: $${data.financial.revenue.total.toFixed(2)} (${data.comparison.revenueVsLastWeek >= 0 ? '+' : ''}${data.comparison.revenueVsLastWeek.toFixed(1)}% vs last week)
- Expenses: $${data.financial.expenses.total.toFixed(2)} (${data.comparison.expensesVsLastWeek >= 0 ? '+' : ''}${data.comparison.expensesVsLastWeek.toFixed(1)}% vs last week)
- MRR: $${data.financial.revenue.mrr.toFixed(2)}
- Profit margin: ${data.financial.profit.margin.toFixed(1)}%
- Active customers: ${data.crm.activeCustomers}
- New customers: ${data.crm.totalCustomers} total (${data.comparison.customersVsLastWeek >= 0 ? '+' : ''}${data.comparison.customersVsLastWeek.toFixed(1)}% vs last week)
- Open tickets: ${data.crm.openTickets}
- SOP runs: ${data.operations.sopRunsTotal} (${data.operations.sopSuccessRate.toFixed(1)}% success)

Respond as JSON: {"highlights": ["..."], "recommendations": ["..."]}`;

      const response = await this.llm.chat({
        messages: [{ role: 'user', content: prompt }],
        maxTokens: 512,
        temperature: 0.3,
      });

      const jsonMatch = response.content.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        return ok({ highlights: [], recommendations: [] });
      }
      const parsed = JSON.parse(jsonMatch[0]) as {
        highlights?: string[];
        recommendations?: string[];
      };
      return ok({
        highlights: parsed.highlights ?? [],
        recommendations: parsed.recommendations ?? [],
      });
    } catch {
      return ok({ highlights: [], recommendations: [] });
    }
  }

  renderMarkdown(digest: WeeklyDigest): string {
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

  renderCli(digest: WeeklyDigest): string {
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

  private async buildCrmSummary(
    from: string,
    to: string,
    _prevFrom: string,
    _prevTo: string,
  ): Promise<Result<CrmSummary>> {
    try {
      const [leadsResult, customersResult, ticketsResult] = await Promise.all([
        this.crm.getAll('leads'),
        this.crm.getAll('customers'),
        this.crm.getAll('tickets'),
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
      const openTickets = tickets.filter(
        (t) => t.status === 'open' || t.status === 'in_progress',
      );
      const resolvedTickets = tickets.filter((t) => t.resolvedAt);
      const avgResolutionMs =
        resolvedTickets.length > 0
          ? resolvedTickets.reduce((sum, t) => {
              const ms =
                new Date(t.resolvedAt!).getTime() - new Date(t.createdAt).getTime();
              return sum + ms;
            }, 0) / resolvedTickets.length
          : 0;
      const avgResolutionHours = avgResolutionMs / (1000 * 60 * 60);
      const mrr = activeCustomers.reduce((s, c) => s + c.mrr, 0);

      return ok({
        totalLeads: leads.length,
        newLeadsThisWeek: newLeads.length,
        totalCustomers: customers.length,
        activeCustomers: activeCustomers.length,
        churnedThisMonth: churnedThisMonth.length,
        openTickets: openTickets.length,
        avgResolutionTimeHours: Math.round(avgResolutionHours * 10) / 10,
        pipeline: [],
        mrr,
        mrrGrowthPercent: 0,
      });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  private async loadSopMetrics(): Promise<SopWeeklyMetrics> {
    if (!existsSync(this.sopMetricsPath)) return {};
    try {
      const raw = await readFile(this.sopMetricsPath, 'utf-8');
      return JSON.parse(raw) as SopWeeklyMetrics;
    } catch {
      return {};
    }
  }
}
