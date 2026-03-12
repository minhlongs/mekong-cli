/**
 * Report Generator — CLI tables + Markdown export for analytics bundle.
 * Phase 5 of v0.8 Analytics.
 */
import type { AnalyticsBundle, ROIMetrics, AgentPerformance, RevenueReport, GrowthIndicator } from './types.js';

export class ReportGenerator {
  /** Full Markdown report from analytics bundle */
  toMarkdown(bundle: AnalyticsBundle): string {
    const { roi, agents, revenue, growth } = bundle;
    const now = new Date().toISOString().slice(0, 10);

    return [
      `# Mekong Analytics Report — ${roi.period.label}`,
      `_Generated: ${now}_`,
      '',
      '---',
      '',
      '## ROI Summary',
      '',
      `| Metric | Value |`,
      `|--------|-------|`,
      `| ROI % | ${roi.roiPercent >= 0 ? '+' : ''}${roi.roiPercent.toFixed(1)}% |`,
      `| Net Value | $${roi.netValue.toFixed(2)} |`,
      `| Time Saved | ${roi.timeSavedHours.toFixed(1)}h → $${roi.timeSavedValue.toFixed(2)} |`,
      `| Revenue Generated | $${roi.revenueGenerated.toFixed(2)} |`,
      `| Total Cost | $${roi.totalCost.toFixed(6)} |`,
      '',
      '---',
      '',
      '## Agent Leaderboard',
      '',
      `| Agent | AGI Score | Success% | Resilience |`,
      `|-------|-----------|----------|------------|`,
      ...agents.map((a) =>
        `| ${a.agentName} | ${a.agiScore} | ${(a.successRate * 100).toFixed(0)}% | ${(a.errorRecoveryRate * 100).toFixed(0)}% |`,
      ),
      '',
      '---',
      '',
      '## Revenue Breakdown',
      '',
      `| Metric | Value |`,
      `|--------|-------|`,
      `| MRR | $${revenue.mrr.toFixed(2)} |`,
      `| ARR | $${revenue.arr.toFixed(2)} |`,
      `| ARPU | $${revenue.arpu.toFixed(2)} |`,
      `| Active Customers | ${revenue.activeCustomers} |`,
      '',
      '**Tier Distribution:**',
      '',
      `| Tier | Count |`,
      `|------|-------|`,
      `| Free | ${revenue.tierDistribution.free} |`,
      `| Starter | ${revenue.tierDistribution.starter} |`,
      `| Pro | ${revenue.tierDistribution.pro} |`,
      `| Enterprise | ${revenue.tierDistribution.enterprise} |`,
      '',
      '---',
      '',
      '## Growth Trends',
      '',
      `| Metric | Value |`,
      `|--------|-------|`,
      `| MoM Growth | ${growth.momGrowthPercent >= 0 ? '+' : ''}${growth.momGrowthPercent.toFixed(1)}% |`,
      `| WoW Growth | ${growth.wowGrowthPercent >= 0 ? '+' : ''}${growth.wowGrowthPercent.toFixed(1)}% |`,
      `| Churn Rate | ${(growth.churnRate * 100).toFixed(2)}% |`,
      `| Expansion Revenue | $${growth.expansionRevenue.toFixed(2)} |`,
      `| NRR | ${growth.nrrPercent.toFixed(1)}% |`,
      `| New Customers | ${growth.newCustomers} |`,
      `| Churned | ${growth.churnedCustomers} |`,
      '',
      '---',
      '',
      '_ROIaaS DNA Phase 5 Complete — Mekong CLI v0.8_',
      '',
    ].join('\n');
  }

  /** CLI summary (all sections combined) */
  toCliSummary(bundle: AnalyticsBundle): string {
    return [
      this.roiSection(bundle.roi),
      this.agentSection(bundle.agents),
      this.revenueSection(bundle.revenue),
      this.growthSection(bundle.growth),
    ].join('');
  }

  roiSection(roi: ROIMetrics): string {
    const sign = roi.roiPercent >= 0 ? '+' : '';
    return [
      `\n── ROI Summary (${roi.period.label}) ──────────────────────\n`,
      `  ROI              : ${sign}${roi.roiPercent.toFixed(1)}%`,
      `  Net Value        : $${roi.netValue.toFixed(2)}`,
      `  Time Saved       : ${roi.timeSavedHours.toFixed(1)}h @ $${roi.hourlyRate}/hr`,
      `  Revenue          : $${roi.revenueGenerated.toFixed(2)}`,
      `  Cost             : $${roi.totalCost.toFixed(6)}`,
      '',
    ].join('\n');
  }

  agentSection(agents: AgentPerformance[]): string {
    if (agents.length === 0) return '\n── Agent Leaderboard ─── (no data)\n\n';
    const rows = agents.map((a) =>
      `  ${a.agentName.padEnd(22)}${String(a.agiScore).padStart(5)}  ${(a.successRate * 100).toFixed(0).padStart(7)}%  ${(a.errorRecoveryRate * 100).toFixed(0).padStart(9)}%`,
    );
    return [
      '\n── Agent Leaderboard ────────────────────────────\n',
      `  ${'Agent'.padEnd(22)}${'Score'.padStart(5)}  ${'Success'.padStart(8)}  ${'Resilience'.padStart(10)}`,
      '  ' + '─'.repeat(50),
      ...rows,
      '',
    ].join('\n');
  }

  revenueSection(revenue: RevenueReport): string {
    return [
      `\n── Revenue (${revenue.period.label}) ───────────────────────\n`,
      `  MRR              : $${revenue.mrr.toFixed(2)}`,
      `  ARR              : $${revenue.arr.toFixed(2)}`,
      `  ARPU             : $${revenue.arpu.toFixed(2)}`,
      `  Active Customers : ${revenue.activeCustomers}`,
      '',
    ].join('\n');
  }

  growthSection(growth: GrowthIndicator): string {
    const sign = (n: number) => (n >= 0 ? '+' : '');
    return [
      `\n── Growth Trends (${growth.period.label}) ──────────────────\n`,
      `  MoM Growth       : ${sign(growth.momGrowthPercent)}${growth.momGrowthPercent.toFixed(1)}%`,
      `  WoW Growth       : ${sign(growth.wowGrowthPercent)}${growth.wowGrowthPercent.toFixed(1)}%`,
      `  Churn Rate       : ${(growth.churnRate * 100).toFixed(2)}%`,
      `  NRR              : ${growth.nrrPercent.toFixed(1)}%`,
      `  New Customers    : ${growth.newCustomers}`,
      '',
    ].join('\n');
  }
}
