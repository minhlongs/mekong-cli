/**
 * Kaizen Report Generator — periodic improvement analysis.
 * Report types: quick (bottlenecks only), standard (full analytics), deep (AI-powered).
 */
import type { KaizenReport, SopAnalytics } from './types.js';
import type { KaizenAnalyzer } from './analyzer.js';
import type { KaizenRecommender } from './recommender.js';
import { ok, err } from '../types/common.js';
import type { Result } from '../types/common.js';

export class KaizenReporter {
  constructor(
    private readonly analyzer: KaizenAnalyzer,
    private readonly recommender: KaizenRecommender,
  ) {}

  /** Generate full Kaizen report */
  async generate(options: {
    depth: 'quick' | 'standard' | 'deep';
    days: number;
  }): Promise<Result<KaizenReport>> {
    try {
      const { days } = options;
      const now = new Date();
      const from = new Date(now.getTime() - days * 24 * 60 * 60 * 1000).toISOString();
      const to = now.toISOString();

      const [health, bottlenecks] = await Promise.all([
        this.analyzer.calculateHealthScore(days),
        this.analyzer.findBottlenecks(days),
      ]);

      // For quick depth: skip per-SOP analytics
      let sopAnalytics: SopAnalytics[] = [];
      if (options.depth !== 'quick') {
        // standard + deep: try to get known SOP names from bottleneck locations
        const sopNames = [...new Set(
          bottlenecks
            .filter(b => b.type === 'sop_step')
            .map(b => b.location.split('.')[0])
            .filter(Boolean),
        )];
        sopAnalytics = await Promise.all(
          sopNames.map(name => this.analyzer.analyzeSop(name, days)),
        );
      }

      const agentAnalytics = options.depth === 'quick' ? [] : [];

      const suggestions = await this.recommender.suggest({
        sopAnalytics,
        agentAnalytics,
        bottlenecks,
        budgetData: { totalSpent: 0, byModel: {} },
      });

      const report: KaizenReport = {
        period: { from, to },
        overallHealth: { score: health.score, trend: health.trend },
        sopAnalytics,
        agentAnalytics,
        bottlenecks,
        suggestions,
        comparison: {
          totalSopRuns: { current: 0, previous: 0, change: 0 },
          avgSopDuration: { current: 0, previous: 0, change: 0 },
          totalCost: { current: 0, previous: 0, change: 0 },
          overallSuccessRate: { current: health.score, previous: 0, change: 0 },
        },
      };

      return ok(report);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Render as CLI output */
  renderCli(report: KaizenReport): string {
    const lines: string[] = [];
    const trendEmoji = report.overallHealth.trend === 'improving' ? 'up'
      : report.overallHealth.trend === 'degrading' ? 'down' : 'right';

    lines.push('=== KAIZEN REPORT ===');
    lines.push(`Period: ${report.period.from.slice(0, 10)} → ${report.period.to.slice(0, 10)}`);
    lines.push('');
    lines.push(`Health Score: ${report.overallHealth.score}/100  [${trendEmoji}] ${report.overallHealth.trend}`);
    lines.push('');

    // Bottlenecks
    if (report.bottlenecks.length > 0) {
      lines.push('--- Top Bottlenecks ---');
      const top = report.bottlenecks.slice(0, 5);
      for (const bn of top) {
        const impact = bn.impact.toUpperCase().padEnd(8);
        lines.push(`  [${impact}] ${bn.location} — ${bn.metric}: ${bn.currentValue.toFixed(1)} (expected: ${bn.expectedValue})`);
      }
      lines.push('');
    }

    // Period comparison
    const c = report.comparison;
    lines.push('--- Period Comparison ---');
    lines.push(`  SOP Runs:      ${c.totalSopRuns.current} (prev: ${c.totalSopRuns.previous}, ${sign(c.totalSopRuns.change)}%)`);
    lines.push(`  Avg Duration:  ${c.avgSopDuration.current.toFixed(1)}s (prev: ${c.avgSopDuration.previous.toFixed(1)}s, ${sign(c.avgSopDuration.change)}%)`);
    lines.push(`  Total Cost:    $${c.totalCost.current.toFixed(2)} (prev: $${c.totalCost.previous.toFixed(2)}, ${sign(c.totalCost.change)}%)`);
    lines.push(`  Success Rate:  ${c.overallSuccessRate.current.toFixed(1)}% (prev: ${c.overallSuccessRate.previous.toFixed(1)}%)`);
    lines.push('');

    // Suggestions
    if (report.suggestions.length > 0) {
      lines.push('--- Top Suggestions ---');
      report.suggestions.slice(0, 5).forEach((s, i) => {
        const auto = s.autoApplicable ? ' [AUTO]' : '';
        lines.push(`  ${i + 1}. ${s.title}${auto}`);
        lines.push(`     ${s.description}`);
        const impact = s.estimatedImpact;
        if (impact.timeSaved > 0) lines.push(`     Save: ${impact.timeSaved.toFixed(0)}s/run`);
        if (impact.costSaved > 0) lines.push(`     Save: $${impact.costSaved.toFixed(2)}/run`);
      });
      lines.push('');
    }

    // SOP leaderboard
    if (report.sopAnalytics.length > 0) {
      lines.push('--- SOP Leaderboard ---');
      const sorted = [...report.sopAnalytics];
      const fastest = sorted.sort((a, b) => a.avgDuration - b.avgDuration)[0];
      const slowest = sorted.sort((a, b) => b.avgDuration - a.avgDuration)[0];
      const mostReliable = sorted.sort((a, b) => b.successRate - a.successRate)[0];
      const leastReliable = sorted.sort((a, b) => a.successRate - b.successRate)[0];
      lines.push(`  Fastest:       ${fastest?.sopName} (${fastest?.avgDuration.toFixed(1)}s avg)`);
      lines.push(`  Slowest:       ${slowest?.sopName} (${slowest?.avgDuration.toFixed(1)}s avg)`);
      lines.push(`  Most reliable: ${mostReliable?.sopName} (${mostReliable?.successRate.toFixed(0)}%)`);
      lines.push(`  Least reliable:${leastReliable?.sopName} (${leastReliable?.successRate.toFixed(0)}%)`);
      lines.push('');
    }

    return lines.join('\n');
  }

  /** Render as Markdown */
  renderMarkdown(report: KaizenReport): string {
    const lines: string[] = [];
    const trendIcon = report.overallHealth.trend === 'improving' ? '📈'
      : report.overallHealth.trend === 'degrading' ? '📉' : '➡️';

    lines.push('# Kaizen Report');
    lines.push('');
    lines.push(`**Period:** ${report.period.from.slice(0, 10)} → ${report.period.to.slice(0, 10)}`);
    lines.push('');
    lines.push(`## Overall Health: ${report.overallHealth.score}/100 ${trendIcon}`);
    lines.push('');

    if (report.bottlenecks.length > 0) {
      lines.push('## Bottlenecks');
      lines.push('');
      lines.push('| Location | Metric | Current | Expected | Impact |');
      lines.push('|----------|--------|---------|----------|--------|');
      for (const bn of report.bottlenecks.slice(0, 10)) {
        lines.push(`| ${bn.location} | ${bn.metric} | ${bn.currentValue.toFixed(1)} | ${bn.expectedValue} | **${bn.impact}** |`);
      }
      lines.push('');
    }

    if (report.suggestions.length > 0) {
      lines.push('## Improvement Suggestions');
      lines.push('');
      report.suggestions.forEach((s, i) => {
        const badge = s.autoApplicable ? ' `AUTO`' : '';
        lines.push(`### ${i + 1}. ${s.title}${badge}`);
        lines.push('');
        lines.push(s.description);
        lines.push('');
        lines.push(`- **Target:** ${s.target}`);
        lines.push(`- **Evidence:** ${s.evidence}`);
        if (s.estimatedImpact.timeSaved > 0) {
          lines.push(`- **Time saved:** ${s.estimatedImpact.timeSaved.toFixed(0)}s/run`);
        }
        if (s.estimatedImpact.costSaved > 0) {
          lines.push(`- **Cost saved:** $${s.estimatedImpact.costSaved.toFixed(2)}/run`);
        }
        lines.push('');
      });
    }

    if (report.sopAnalytics.length > 0) {
      lines.push('## SOP Analytics');
      lines.push('');
      lines.push('| SOP | Runs | Success% | Avg Duration | Cost | Trend |');
      lines.push('|-----|------|----------|--------------|------|-------|');
      for (const sop of report.sopAnalytics) {
        lines.push(
          `| ${sop.sopName} | ${sop.totalRuns} | ${sop.successRate.toFixed(0)}% | ${sop.avgDuration.toFixed(1)}s | $${sop.avgCost.toFixed(3)} | ${sop.trend} |`,
        );
      }
      lines.push('');
    }

    return lines.join('\n');
  }
}

function sign(n: number): string {
  return n >= 0 ? `+${n.toFixed(1)}` : n.toFixed(1);
}
