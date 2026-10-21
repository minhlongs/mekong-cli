/** Weekly business summary with LLM-generated insights */
import { format, startOfWeek, endOfWeek, subWeeks, getISOWeek, getYear } from 'date-fns';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { RevenueTracker } from '../finance/revenue.js';
import type { CrmStore } from '../crm/store.js';
import type { LlmRouter } from '../llm/router.js';
import type { WeeklyDigest } from './types.js';
import {
  renderWeeklyDigestMarkdown,
  renderWeeklyDigestCli,
  loadSopWeeklyMetrics,
  buildWeeklyCrmSummary,
} from './weekly-digest-renderer.js';

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
          buildWeeklyCrmSummary(this.crm, from, to),
          loadSopWeeklyMetrics(this.sopMetricsPath),
        ]);

      if (!financialResult.ok) return err(financialResult.error);
      if (!prevFinancialResult.ok) return err(prevFinancialResult.error);
      if (!crmSummaryResult.ok) return err(crmSummaryResult.error);

      const financial = financialResult.value;
      const prevFinancial = prevFinancialResult.value;
      const crmSummary = crmSummaryResult.value;

      const pctChange = (curr: number, prev: number) =>
        prev > 0 ? Math.round(((curr - prev) / prev) * 10000) / 100 : 0;

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
          revenueVsLastWeek: pctChange(financial.revenue.total, prevFinancial.revenue.total),
          expensesVsLastWeek: pctChange(financial.expenses.total, prevFinancial.expenses.total),
          customersVsLastWeek: pctChange(financial.customers.total, prevFinancial.customers.total),
          ticketsVsLastWeek: 0,
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
      if (!jsonMatch) return ok({ highlights: [], recommendations: [] });
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
    return renderWeeklyDigestMarkdown(digest);
  }

  renderCli(digest: WeeklyDigest): string {
    return renderWeeklyDigestCli(digest);
  }
}
